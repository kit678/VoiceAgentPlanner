#!/usr/bin/env python3
"""
Google OAuth Setup Helper

This script helps set up Google OAuth configuration for the Voice Assistant project.
It creates necessary directories, templates, and validates the setup.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
import re

def create_credentials_directory():
    """Create the credentials directory with proper .gitignore."""
    credentials_dir = Path('credentials')
    credentials_dir.mkdir(exist_ok=True)
    
    # Create .gitignore to prevent committing credentials
    gitignore_file = credentials_dir / '.gitignore'
    gitignore_content = '''# Ignore all credential files
*.json
*.key
*.pem
*.p12
'''
    
    with open(gitignore_file, 'w') as f:
        f.write(gitignore_content)
    
    print(f"✅ Created credentials directory: {credentials_dir.absolute()}")
    return credentials_dir

def create_client_secrets_template(credentials_dir: Path):
    """Create a template for the Google client secrets file."""
    template = {
        "web": {
            "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
            "project_id": "your-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uris": ["http://localhost:8080/oauth/callback"]
        }
    }
    
    template_file = credentials_dir / 'google_client_secrets_template.json'
    with open(template_file, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"✅ Created client secrets template: {template_file.absolute()}")
    return template_file

def create_env_template():
    """Create a .env template file."""
    env_template = '''# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here

# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=path/to/your/firebase-service-account-key.json

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Environment
ENVIRONMENT=development
'''
    
    env_file = Path('.env.template')
    with open(env_file, 'w') as f:
        f.write(env_template)
    
    print(f"✅ Created .env template: {env_file.absolute()}")
    return env_file

def parse_env_file(env_path: Path) -> Dict[str, str]:
    """Parse .env file and return key-value pairs."""
    env_vars = {}
    if env_path.exists():
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        except Exception as e:
            print(f"Warning: Could not parse .env file: {e}")
    return env_vars

def check_existing_setup():
    """Check if OAuth setup already exists."""
    credentials_dir = Path('credentials')
    client_secrets_file = credentials_dir / 'google_client_secrets.json'
    
    # Look for .env in project root (parent directory)
    project_root = Path('..').resolve()
    env_file = project_root / '.env'
    
    # Parse .env file to check for required variables
    env_vars = parse_env_file(env_file)
    
    status = {
        'credentials_dir': credentials_dir.exists(),
        'client_secrets': client_secrets_file.exists(),
        'env_file': env_file.exists(),
        'env_file_path': str(env_file),
        'env_vars': {
            'GOOGLE_CLIENT_ID': 'GOOGLE_CLIENT_ID' in env_vars and env_vars['GOOGLE_CLIENT_ID'] != 'your_client_id_here',
            'GOOGLE_CLIENT_SECRET': 'GOOGLE_CLIENT_SECRET' in env_vars and env_vars['GOOGLE_CLIENT_SECRET'] != 'your_client_secret_here'
        }
    }
    
    return status

def validate_client_secrets(file_path: Path) -> Dict[str, Any]:
    """Validate the client secrets file format."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        required_fields = ['client_id', 'client_secret', 'project_id']
        web_config = data.get('web', {})
        
        missing_fields = [field for field in required_fields if not web_config.get(field) or web_config.get(field).startswith('YOUR_')]
        
        return {
            'valid': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'data': data
        }
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return {
            'valid': False,
            'error': str(e),
            'missing_fields': [],
            'data': None
        }

def main():
    """Main setup function."""
    print("🚀 Google OAuth Setup Helper")
    print("=" * 40)
    
    # Check current status
    print("\n📋 Checking current setup...")
    status = check_existing_setup()
    
    # Create directories and templates
    print("\n🔧 Setting up local files...")
    credentials_dir = create_credentials_directory()
    create_client_secrets_template(credentials_dir)
    create_env_template()
    
    # Check if actual credentials exist
    client_secrets_file = credentials_dir / 'google_client_secrets.json'
    
    print("\n📊 Setup Status:")
    print(f"  Credentials directory: {'✅' if status['credentials_dir'] else '❌'}")
    print(f"  Client secrets file: {'✅' if status['client_secrets'] else '❌'}")
    print(f"  Environment file: {'✅' if status['env_file'] else '❌'} ({status['env_file_path']})")
    print(f"  GOOGLE_CLIENT_ID env var: {'✅' if status['env_vars']['GOOGLE_CLIENT_ID'] else '❌'}")
    print(f"  GOOGLE_CLIENT_SECRET env var: {'✅' if status['env_vars']['GOOGLE_CLIENT_SECRET'] else '❌'}")
    
    if client_secrets_file.exists():
        print("\n🔍 Validating client secrets file...")
        validation = validate_client_secrets(client_secrets_file)
        if validation['valid']:
            print("  ✅ Client secrets file is valid")
        else:
            print("  ❌ Client secrets file has issues:")
            if 'error' in validation:
                print(f"    Error: {validation['error']}")
            if validation['missing_fields']:
                print(f"    Missing/template fields: {', '.join(validation['missing_fields'])}")
    
    print("\n📝 Next Steps:")
    if not status['env_file']:
        print("1. Copy .env.template to project root (.env) and fill in your actual values")
        print("2. Follow the manual setup instructions in MANUAL_ACTIONS.md")
        print("3. Download your actual google_client_secrets.json from Google Cloud Console")
        print(f"4. Replace the template file: {client_secrets_file.absolute()}")
        print("5. Run this script again to validate your setup")
    elif not all(status['env_vars'].values()):
        print("1. Update your .env file with actual Google OAuth credentials")
        print("2. Download your actual google_client_secrets.json from Google Cloud Console")
        print(f"3. Replace the template file: {client_secrets_file.absolute()}")
        print("4. Run this script again to validate your setup")
    else:
        print("1. Download your actual google_client_secrets.json from Google Cloud Console")
        print(f"2. Replace the template file: {client_secrets_file.absolute()}")
        print("3. Run this script again to validate your setup")
    
    print("\n🔗 Useful Links:")
    print("  Google Cloud Console: https://console.cloud.google.com/")
    print("  OAuth Setup Guide: https://developers.google.com/identity/protocols/oauth2")

if __name__ == '__main__':
    main()