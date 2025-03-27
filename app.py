import os
import openai
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Mock database for users and documents (will be replaced with a real database later)
USERS_DB = {}
DOCUMENTS_DB = {}
ANALYSIS_DB = {}
TEAMS_DB = {}
CLIENTS_DB = {}
REPORTS_DB = {}
SETTINGS_DB = {
    'ai_settings': {
        'primary_provider': 'openai',
        'openai_api_key': '',
        'deepseek_api_key': '',
        'anthropic_api_key': '',
        'gemini_api_key': '',
        'mistral_api_key': '',
        'enable_fallback': True,
        'temperature': 0.2
    },
    'payment_settings': {
        'stripe_publishable_key': '',
        'stripe_secret_key': '',
        'basic_plan_price': 99,
        'professional_plan_price': 299,
        'enterprise_plan_price': 999,
        'enable_annual_discount': True,
        'annual_discount_percentage': 20
    },
    'account_settings': {
        'company_name': '',
        'company_website': ''
    },
    'notification_settings': {
        'notify_document_complete': True,
        'notify_payment_success': True,
        'notify_payment_failure': True,
        'notify_subscription_renewal': True
    }
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# AI Document Analysis Functions
def analyze_document_with_ai(text, analysis_types, provider='openai'):
    """
    Analyze document text using the specified AI provider
    
    Parameters:
    - text: The document text to analyze
    - analysis_types: List of analysis types to perform (summary, keyPoints, entities, risk)
    - provider: AI provider to use (openai, deepseek, anthropic, gemini, mistral)
    
    Returns:
    - Dictionary containing analysis results
    """
    try:
        if provider == 'openai':
            return analyze_with_openai(text, analysis_types)
        elif provider == 'deepseek':
            return analyze_with_deepseek(text, analysis_types)
        elif provider == 'anthropic':
            return analyze_with_anthropic(text, analysis_types)
        elif provider == 'gemini':
            return analyze_with_gemini(text, analysis_types)
        elif provider == 'mistral':
            return analyze_with_mistral(text, analysis_types)
        else:
            # Default to OpenAI
            return analyze_with_openai(text, analysis_types)
    except Exception as e:
        # If fallback is enabled, try the next provider
        if SETTINGS_DB['ai_settings']['enable_fallback']:
            providers = ['openai', 'deepseek', 'anthropic', 'gemini', 'mistral']
            current_index = providers.index(provider)
            
            # Try each provider in order
            for i in range(1, len(providers)):
                next_provider = providers[(current_index + i) % len(providers)]
                
                # Skip if we don't have an API key for this provider
                if not SETTINGS_DB['ai_settings'].get(f'{next_provider}_api_key'):
                    continue
                
                try:
                    return analyze_document_with_ai(text, analysis_types, next_provider)
                except:
                    continue
        
        # If we get here, all providers failed or fallback is disabled
        raise Exception(f"Document analysis failed with provider {provider}: {str(e)}")

def analyze_with_openai(text, analysis_types):
    """Analyze document using OpenAI"""
    api_key = SETTINGS_DB['ai_settings'].get('openai_api_key')
    temperature = float(SETTINGS_DB['ai_settings'].get('temperature', 0.2))
    
    if not api_key:
        # Return mock data if no API key is provided
        return get_mock_analysis_results()
    
    # Create different prompts based on analysis types
    prompts = []
    if "summary" in analysis_types:
        prompts.append("Provide a concise summary of the following document:")
    if "keyPoints" in analysis_types:
        prompts.append("Extract the key points from the following document:")
    if "entities" in analysis_types:
        prompts.append("Identify all people, organizations, and dates mentioned in the following document:")
    if "risk" in analysis_types:
        prompts.append("Assess the potential legal or financial risks in the following document:")
    
    # Combine prompts
    combined_prompt = "\n".join(prompts) + "\n\nDocument text:\n" + text
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a document analysis assistant for legal and financial professionals."},
                {"role": "user", "content": combined_prompt}
            ],
            temperature=temperature,
        )
        
        # Process response
        analysis_text = response.choices[0].message.content
        
        # Parse the response to extract different parts
        summary = ""
        key_points = []
        entities = {"people": [], "organizations": [], "dates": []}
        risk_assessment = ""
        
        # Simple parsing logic
        if "summary" in analysis_types:
            summary_section = analysis_text.split("Key points:")[0] if "Key points:" in analysis_text else analysis_text
            summary = summary_section.strip()
        
        if "keyPoints" in analysis_types:
            if "Key points:" in analysis_text:
                key_points_section = analysis_text.split("Key points:")[1].split("Entities:")[0] if "Entities:" in analysis_text else analysis_text.split("Key points:")[1]
                key_points = [point.strip().replace("- ", "") for point in key_points_section.strip().split("\n") if point.strip()]
        
        if "entities" in analysis_types:
            if "Entities:" in analysis_text:
                entities_section = analysis_text.split("Entities:")[1].split("Risk assessment:")[0] if "Risk assessment:" in analysis_text else analysis_text.split("Entities:")[1]
                
                # Extract people
                if "People:" in entities_section:
                    people_section = entities_section.split("People:")[1].split("Organizations:")[0] if "Organizations:" in entities_section else entities_section.split("People:")[1]
                    entities["people"] = [person.strip().replace("- ", "") for person in people_section.strip().split("\n") if person.strip()]
                
                # Extract organizations
                if "Organizations:" in entities_section:
                    orgs_section = entities_section.split("Organizations:")[1].split("Dates:")[0] if "Dates:" in entities_section else entities_section.split("Organizations:")[1]
                    entities["organizations"] = [org.strip().replace("- ", "") for org in orgs_section.strip().split("\n") if org.strip()]
                
                # Extract dates
                if "Dates:" in entities_section:
                    dates_section = entities_section.split("Dates:")[1]
                    entities["dates"] = [date.strip().replace("- ", "") for date in dates_section.strip().split("\n") if date.strip()]
        
        if "risk" in analysis_types:
            if "Risk assessment:" in analysis_text:
                risk_section = analysis_text.split("Risk assessment:")[1]
                risk_assessment = risk_section.strip()
        
        return {
            "summary": summary,
            "key_points": key_points,
            "entities": entities,
            "risk_assessment": risk_assessment,
            "analyzed_at": datetime.now().isoformat(),
            "provider": "openai"
        }
    except Exception as e:
        raise Exception(f"OpenAI analysis failed: {str(e)}")

def analyze_with_deepseek(text, analysis_types):
    """Analyze document using DeepSeek AI"""
    api_key = SETTINGS_DB['ai_settings'].get('deepseek_api_key')
    
    if not api_key:
        # Return mock data if no API key is provided
        return get_mock_analysis_results(provider="deepseek")
    
    # Implement DeepSeek API integration here
    # For now, return mock data
    return get_mock_analysis_results(provider="deepseek")

def analyze_with_anthropic(text, analysis_types):
    """Analyze document using Anthropic Claude"""
    api_key = SETTINGS_DB['ai_settings'].get('anthropic_api_key')
    
    if not api_key:
        # Return mock data if no API key is provided
        return get_mock_analysis_results(provider="anthropic")
    
    # Implement Anthropic API integration here
    # For now, return mock data
    return get_mock_analysis_results(provider="anthropic")

def analyze_with_gemini(text, analysis_types):
    """Analyze document using Google Gemini"""
    api_key = SETTINGS_DB['ai_settings'].get('gemini_api_key')
    
    if not api_key:
        # Return mock data if no API key is provided
        return get_mock_analysis_results(provider="gemini")
    
    # Implement Google Gemini API integration here
    # For now, return mock data
    return get_mock_analysis_results(provider="gemini")

def analyze_with_mistral(text, analysis_types):
    """Analyze document using Mistral AI"""
    api_key = SETTINGS_DB['ai_settings'].get('mistral_api_key')
    
    if not api_key:
        # Return mock data if no API key is provided
        return get_mock_analysis_results(provider="mistral")
    
    # Implement Mistral AI API integration here
    # For now, return mock data
    return get_mock_analysis_results(provider="mistral")

def get_mock_analysis_results(provider="openai"):
    """Return mock analysis results for testing"""
    return {
        "summary": "This document appears to be a contract agreement between Company A and Company B for software development services. The contract outlines the scope of work, payment terms, intellectual property rights, and confidentiality obligations. The agreement is set to begin on January 1, 2025 and continue for 12 months with possible renewal options.",
        "key_points": [
            "Company A will provide software development services to Company B",
            "Payment terms include a monthly fee of $10,000",
            "The contract duration is 12 months starting January 1, 2025",
            "Intellectual property developed during the project belongs to Company B",
            "Both parties are bound by confidentiality obligations"
        ],
        "entities": {
            "people": ["John Smith", "Jane Doe", "Robert Johnson"],
            "organizations": ["Company A", "Company B", "Legal Firm LLC"],
            "dates": ["January 1, 2025", "December 31, 2025", "March 15, 2025"]
        },
        "risk_assessment": "Low risk. The contract appears to be a standard service agreement with clear terms and conditions. However, there are a few areas that could benefit from more specific language, particularly around the acceptance criteria for deliverables and the process for handling change requests.",
        "analyzed_at": datetime.now().isoformat(),
        "provider": provider
    }

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in USERS_DB:
            flash('Email already exists')
            return redirect(url_for('signup'))
        
        user_id = str(uuid.uuid4())
        USERS_DB[email] = {
            'id': user_id,
            'email': email,
            'password': password,  # In a real app, this would be hashed
            'created_at': datetime.now().isoformat(),
            'subscription': 'free',  # Default to free tier
            'is_admin': False  # Default to regular user, not admin
        }
        
        # Make the first user an admin for testing purposes
        if len(USERS_DB) == 1:
            USERS_DB[email]['is_admin'] = True
        
        session['user_id'] = user_id
        session['email'] = email
        
        flash('Account created successfully')
        return redirect(url_for('dashboard'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email not in USERS_DB or USERS_DB[email]['password'] != password:
            flash('Invalid email or password')
            return redirect(url_for('login'))
        
        session['user_id'] = USERS_DB[email]['id']
        session['email'] = email
        
        flash('Logged in successfully')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('email', None)
    flash('Logged out successfully')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to access the dashboard')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    email = session.get('email', '')
    user_is_admin = USERS_DB.get(email, {}).get('is_admin', False)
    user_documents = [doc for doc in DOCUMENTS_DB.values() if doc['user_id'] == user_id]
    
    return render_template('dashboard.html', documents=user_documents, user_is_admin=user_is_admin)

@app.route('/upload', methods=['GET', 'POST'])
def upload_document():
    if 'user_id' not in session:
        flash('Please login to upload documents')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'document' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['document']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            document_id = str(uuid.uuid4())
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{document_id}_{filename}")
            file.save(file_path)
            
            # Get analysis types from form
            analysis_types = request.form.getlist('analysisType')
            if not analysis_types:
                analysis_types = ['summary', 'keyPoints', 'entities', 'risk']  # Default to all if none selected
            
            DOCUMENTS_DB[document_id] = {
                'id': document_id,
                'user_id': session['user_id'],
                'filename': filename,
                'file_path': file_path,
                'uploaded_at': datetime.now().isoformat(),
                'status': 'processing'  # Status: uploaded, processing, analyzed, error
            }
            
            # In a real app, we would read the file content here
            # For now, we'll just use a mock text
            document_text = "This is a sample contract between Company A and Company B..."
            
            # Process the document with AI
            try:
                # Use the primary AI provider from settings
                provider = SETTINGS_DB['ai_settings']['primary_provider']
                analysis_results = analyze_document_with_ai(document_text, analysis_types, provider)
                DOCUMENTS_DB[document_id]['status'] = 'analyzed'
                ANALYSIS_DB[document_id] = {
                    'document_id': document_id,
                    **analysis_results
                }
                flash('Document uploaded and analyzed successfully')
            except Exception as e:
                DOCUMENTS_DB[document_id]['status'] = 'error'
                flash(f'Error analyzing document: {str(e)}')
            
            return redirect(url_for('view_document', document_id=document_id))
        
        flash('File type not allowed')
        return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/document/<document_id>')
def view_document(document_id):
    if 'user_id' not in session:
        flash('Please login to view documents')
        return redirect(url_for('login'))
    
    if document_id not in DOCUMENTS_DB:
        flash('Document not found')
        return redirect(url_for('dashboard'))
    
    document = DOCUMENTS_DB[document_id]
    
    if document['user_id'] != session['user_id']:
        flash('You do not have permission to view this document')
        return redirect(url_for('dashboard'))
    
    analysis = ANALYSIS_DB.get(document_id, {})
    
    return render_template('document.html', document=document, analysis=analysis)

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/teams')
def teams():
    if 'user_id' not in session:
        flash('Please login to access teams')
        return redirect(url_for('login'))
    
    email = session.get('email', '')
    user_is_admin = USERS_DB.get(email, {}).get('is_admin', False)
    
    # Mock team data for demonstration
    teams = [
        {
            'id': '1',
            'name': 'Legal Team',
            'description': 'Team focused on contract analysis and legal document review',
            'members': [
                {'email': 'john@example.com', 'role': 'admin'},
                {'email': 'sarah@example.com', 'role': 'member'},
                {'email': 'mike@example.com', 'role': 'member'}
            ]
        },
        {
            'id': '2',
            'name': 'Finance Team',
            'description': 'Team focused on financial document analysis and reporting',
            'members': [
                {'email': 'lisa@example.com', 'role': 'admin'},
                {'email': 'david@example.com', 'role': 'member'}
            ]
        }
    ]
    
    return render_template('teams.html', teams=teams, user_is_admin=user_is_admin)

@app.route('/clients')
def clients():
    if 'user_id' not in session:
        flash('Please login to access clients')
        return redirect(url_for('login'))
    
    email = session.get('email', '')
    user_is_admin = USERS_DB.get(email, {}).get('is_admin', False)
    
    # Mock client data for demonstration
    clients = [
        {
            'id': '1',
            'name': 'Acme Corporation',
            'company': 'Acme Inc.',
            'email': 'contact@acme.com',
            'phone': '(555) 123-4567',
            'documents': ['1', '2', '3']
        },
        {
            'id': '2',
            'name': 'Global Financial Services',
            'company': 'GFS Ltd.',
            'email': 'info@gfs.com',
            'phone': '(555) 987-6543',
            'documents': ['4', '5']
        }
    ]
    
    return render_template('clients.html', clients=clients, user_is_admin=user_is_admin)

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        flash('Please login to access reports')
        return redirect(url_for('login'))
    
    email = session.get('email', '')
    user_is_admin = USERS_DB.get(email, {}).get('is_admin', False)
    
    # Mock report data for demonstration
    total_documents = 120
    analyzed_documents = 105
    avg_processing_time = 3.2
    total_clients = 15
    
    # Mock recent documents for demonstration
    recent_documents = [
        {
            'id': '1',
            'filename': 'Contract_2025_03_15.pdf',
            'client_name': 'Acme Corporation',
            'uploaded_by': 'john@example.com',
            'uploaded_at': '2025-03-15',
            'status': 'analyzed'
        },
        {
            'id': '2',
            'filename': 'Financial_Report_Q1.pdf',
            'client_name': 'Global Financial Services',
            'uploaded_by': 'lisa@example.com',
            'uploaded_at': '2025-03-18',
            'status': 'analyzed'
        },
        {
            'id': '3',
            'filename': 'Legal_Brief_Case123.pdf',
            'client_name': 'Acme Corporation',
            'uploaded_by': 'sarah@example.com',
            'uploaded_at': '2025-03-20',
            'status': 'processing'
        }
    ]
    
    return render_template('reports.html', 
                          total_documents=total_documents,
                          analyzed_documents=analyzed_documents,
                          avg_processing_time=avg_processing_time,
                          total_clients=total_clients,
                          recent_documents=recent_documents,
                          user_is_admin=user_is_admin)

@app.route('/settings/ai', methods=['POST'])
def update_ai_settings():
    if 'user_id' not in session:
        flash('Please login to update settings')
        return redirect(url_for('login'))
    
    SETTINGS_DB['ai_settings']['primary_provider'] = request.form.get('primary_ai_provider', 'openai')
    SETTINGS_DB['ai_settings']['openai_api_key'] = request.form.get('openai_api_key', '')
    SETTINGS_DB['ai_settings']['deepseek_api_key'] = request.form.get('deepseek_api_key', '')
    SETTINGS_DB['ai_settings']['anthropic_api_key'] = request.form.get('anthropic_api_key', '')
    SETTINGS_DB['ai_settings']['gemini_api_key'] = request.form.get('gemini_api_key', '')
    SETTINGS_DB['ai_settings']['mistral_api_key'] = request.form.get('mistral_api_key', '')
    SETTINGS_DB['ai_settings']['enable_fallback'] = 'enable_fallback' in request.form
    SETTINGS_DB['ai_settings']['temperature'] = request.form.get('model_temperature', '0.2')
    
    flash('AI settings updated successfully')
    return redirect(url_for('settings'))

@app.route('/settings/payment', methods=['POST'])
def update_payment_settings():
    if 'user_id' not in session:
        flash('Please login to update settings')
        return redirect(url_for('login'))
    
    SETTINGS_DB['payment_settings']['stripe_publishable_key'] = request.form.get('stripe_publishable_key', '')
    SETTINGS_DB['payment_settings']['stripe_secret_key'] = request.form.get('stripe_secret_key', '')
    SETTINGS_DB['payment_settings']['basic_plan_price'] = int(request.form.get('basic_plan_price', 99))
    SETTINGS_DB['payment_settings']['professional_plan_price'] = int(request.form.get('professional_plan_price', 299))
    SETTINGS_DB['payment_settings']['enterprise_plan_price'] = int(request.form.get('enterprise_plan_price', 999))
    SETTINGS_DB['payment_settings']['enable_annual_discount'] = 'enable_annual_discount' in request.form
    SETTINGS_DB['payment_settings']['annual_discount_percentage'] = int(request.form.get('annual_discount_percentage', 20))
    
    flash('Payment settings updated successfully')
    return redirect(url_for('settings'))

@app.route('/settings/account', methods=['POST'])
def update_account_settings():
    if 'user_id' not in session:
        flash('Please login to update settings')
        return redirect(url_for('login'))
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Update password if provided
    if current_password and new_password and confirm_password:
        email = session['email']
        if USERS_DB[email]['password'] != current_password:
            flash('Current password is incorrect')
            return redirect(url_for('settings'))
        
        if new_password != confirm_password:
            flash('New passwords do not match')
            return redirect(url_for('settings'))
        
        USERS_DB[email]['password'] = new_password
        flash('Password updated successfully')
    
    # Update company information
    SETTINGS_DB['account_settings']['company_name'] = request.form.get('company_name', '')
    SETTINGS_DB['account_settings']['company_website'] = request.form.get('company_website', '')
    
    flash('Account settings updated successfully')
    return redirect(url_for('settings'))

@app.route('/settings/notifications', methods=['POST'])
def update_notification_settings():
    if 'user_id' not in session:
        flash('Please login to update settings')
        return redirect(url_for('login'))
    
    SETTINGS_DB['notification_settings']['notify_document_complete'] = 'notify_document_complete' in request.form
    SETTINGS_DB['notification_settings']['notify_payment_success'] = 'notify_payment_success' in request.form
    SETTINGS_DB['notification_settings']['notify_payment_failure'] = 'notify_payment_failure' in request.form
    SETTINGS_DB['notification_settings']['notify_subscription_renewal'] = 'notify_subscription_renewal' in request.form
    
    flash('Notification settings updated successfully')
    return redirect(url_for('settings'))

@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    if 'user_id' not in session:
        flash('Please login to subscribe')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        plan = request.form.get('plan')
        
        # Check if Stripe keys are configured
        if not SETTINGS_DB['payment_settings']['stripe_publishable_key'] or not SETTINGS_DB['payment_settings']['stripe_secret_key']:
            flash('Payment processing is not configured. Please set up Stripe API keys in settings.')
            return redirect(url_for('settings'))
        
        # In a real app, we would process the payment here with Stripe
        # For now, we'll just update the user's subscription
        USERS_DB[session['email']]['subscription'] = plan
        
        flash(f'Successfully subscribed to {plan} plan')
        return redirect(url_for('dashboard'))
    
    plan = request.args.get('plan', 'basic')
    
    # Check if Stripe is configured
    stripe_configured = bool(SETTINGS_DB['payment_settings']['stripe_publishable_key'] and SETTINGS_DB['payment_settings']['stripe_secret_key'])
    
    return render_template('subscribe.html', 
                          plan=plan, 
                          stripe_configured=stripe_configured,
                          stripe_publishable_key=SETTINGS_DB['payment_settings']['stripe_publishable_key'],
                          payment_settings=SETTINGS_DB['payment_settings'])

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    document_id = data.get('document_id')
    
    if not document_id or document_id not in DOCUMENTS_DB:
        return jsonify({'error': 'Document not found'}), 404
    
    document = DOCUMENTS_DB[document_id]
    
    if document['user_id'] != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # In a real app, we would analyze the document here
    # For now, we'll return mock analysis results
    analysis = ANALYSIS_DB.get(document_id, {})
    
    return jsonify(analysis)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
