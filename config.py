import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configuration class for application settings
class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'rtf'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    
    # API Keys (to be set in environment variables)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
    MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY', '')
    
    # Stripe Configuration
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    
    # Default AI Provider
    DEFAULT_AI_PROVIDER = 'openai'
