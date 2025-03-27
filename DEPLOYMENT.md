# DocuInsight AI - Deployment Guide

This guide will walk you through deploying the DocuInsight AI application on Render.

## Prerequisites

1. A [Render account](https://render.com/) (free tier is available)
2. Git installed on your computer
3. API keys for the AI providers you want to use (OpenAI, DeepSeek, etc.)
4. Stripe account for payment processing (optional for initial setup)

## Deployment Steps

### 1. Create a Git Repository

First, create a Git repository and push the application code:

```bash
# Initialize a Git repository
git init

# Add all files
git add .

# Commit the changes
git commit -m "Initial commit"

# Create a repository on GitHub/GitLab and push
git remote add origin <your-repository-url>
git push -u origin main
```

### 2. Deploy on Render

#### Option 1: Using the Render Dashboard

1. Log in to your [Render dashboard](https://dashboard.render.com/)
2. Click "New +" and select "Web Service"
3. Connect your Git repository
4. Configure the service:
   - Name: `docuinsight-ai`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Add the following environment variables:
   - `FLASK_SECRET_KEY`: Generate a random string
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `STRIPE_SECRET_KEY`: Your Stripe secret key
   - `STRIPE_PUBLISHABLE_KEY`: Your Stripe publishable key
6. Click "Create Web Service"

#### Option 2: Using render.yaml (Blueprint)

1. Push your code with the `render.yaml` file to your Git repository
2. Go to the [Render dashboard](https://dashboard.render.com/)
3. Click "New +" and select "Blueprint"
4. Connect your Git repository
5. Render will automatically detect the `render.yaml` file and set up the service
6. You'll be prompted to enter values for environment variables

### 3. Configure Environment Variables

After deployment, you'll need to set up the following environment variables in the Render dashboard:

- `FLASK_SECRET_KEY`: A secure random string for session encryption
- `OPENAI_API_KEY`: Your OpenAI API key
- `DEEPSEEK_API_KEY`: Your DeepSeek API key (optional)
- `ANTHROPIC_API_KEY`: Your Anthropic API key (optional)
- `GOOGLE_API_KEY`: Your Google API key (optional)
- `MISTRAL_API_KEY`: Your Mistral API key (optional)
- `STRIPE_SECRET_KEY`: Your Stripe secret key
- `STRIPE_PUBLISHABLE_KEY`: Your Stripe publishable key

### 4. Set Up Database (For Production)

For a production environment, you should replace the in-memory database with a persistent database:

1. Create a PostgreSQL database on Render or another provider
2. Add the database connection string as an environment variable
3. Update the application code to use the database

### 5. First-Time Setup

After deployment:

1. Visit your application URL
2. Sign up for an account (the first user will automatically be an admin)
3. Go to the Settings page to configure your AI providers and payment settings

## Local Development

To run the application locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will be available at http://localhost:5000

## Folder Structure

```
document_analysis_ai/
├── app.py                 # Main application file
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── Procfile               # Process file for Render
├── render.yaml            # Render deployment configuration
├── static/                # Static assets
│   ├── css/               # CSS stylesheets
│   ├── js/                # JavaScript files
│   └── img/               # Images and icons
├── templates/             # HTML templates
│   ├── index.html         # Landing page
│   ├── dashboard.html     # User dashboard
│   ├── login.html         # Login page
│   ├── signup.html        # Signup page
│   ├── upload.html        # Document upload
│   ├── document.html      # Document analysis view
│   ├── settings.html      # Settings page
│   ├── teams.html         # Team management
│   ├── clients.html       # Client management
│   ├── reports.html       # Reports and analytics
│   └── pricing.html       # Pricing page
└── uploads/               # Document upload directory
```

## Support

If you encounter any issues during deployment, please refer to the [Render documentation](https://render.com/docs) or contact their support team.

For application-specific questions, you can reach out to the DocuInsight AI support team.
