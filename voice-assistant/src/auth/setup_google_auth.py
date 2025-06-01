#!/usr/bin/env python3
"""
Google OAuth Setup Script

This script helps users set up Google OAuth authentication for the Voice Assistant.
It guides through the process of creating Google Cloud credentials and configuring
the application for Google Workspace integration.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .google_config import GoogleConfig
from loguru import logger

class GoogleAuthSetup:
    """
    Interactive setup for Google OAuth authentication.
    """
    
    def __init__(self):
        self.config = GoogleConfig()
        self.setup_logger()
    
    def setup_logger(self):
        """Configure logging for the setup process."""
        logger.remove()  # Remove default handler
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            level="INFO"
        )
    
    def print_banner(self):
        """Print setup banner."""
        print("\n" + "="*60)
        print("    VOICE ASSISTANT - GOOGLE OAUTH SETUP")
        print("="*60)
        print("\nThis script will help you set up Google OAuth authentication.")
        print("You'll need to create a Google Cloud project and OAuth credentials.\n")
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met."""
        logger.info("Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            logger.error("Python 3.8 or higher is required")
            return False
        
        # Check required packages
        try:
            import google.auth
            import google_auth_oauthlib
            import googleapiclient
        except ImportError as e:
            logger.error(f"Missing required package: {e}")
            logger.info("Please run: pip install -r requirements.txt")
            return False
        
        logger.info("✓ Prerequisites check passed")
        return True
    
    def create_directories(self):
        """Create necessary directories."""
        logger.info("Creating directories...")
        
        # Ensure credentials directory exists
        self.config.ensure_credentials_dir()
        
        logger.info(f"✓ Created credentials directory: {self.config.CREDENTIALS_DIR}")
    
    def show_google_cloud_instructions(self):
        """Show instructions for setting up Google Cloud project."""
        print("\n" + "-"*60)
        print("STEP 1: CREATE GOOGLE CLOUD PROJECT")
        print("-"*60)
        print("\n1. Go to the Google Cloud Console:")
        print("   https://console.cloud.google.com/")
        print("\n2. Create a new project or select an existing one")
        print("\n3. Enable the following APIs:")
        print("   - Google Tasks API")
        print("   - Google Calendar API")
        print("   - Google Drive API")
        print("   - Google Docs API")
        print("\n4. Go to 'APIs & Services' > 'Credentials'")
        print("\n5. Click 'Create Credentials' > 'OAuth 2.0 Client IDs'")
        print("\n6. Configure the OAuth consent screen if prompted")
        print("\n7. Choose 'Desktop application' as the application type")
        print("\n8. Add this redirect URI:")
        print(f"   {self.config.REDIRECT_URI}")
        print("\n9. Download the JSON file with your credentials")
        
        input("\nPress Enter when you have completed these steps...")
    
    def get_client_secrets_file(self) -> Path:
        """Get the path to the client secrets file."""
        print("\n" + "-"*60)
        print("STEP 2: CONFIGURE CLIENT SECRETS")
        print("-"*60)
        
        while True:
            print("\nPlease provide your Google OAuth client secrets:")
            print("\n1. Use downloaded JSON file")
            print("2. Enter credentials manually")
            print("3. Create template file")
            
            choice = input("\nChoose an option (1-3): ").strip()
            
            if choice == "1":
                return self._handle_json_file()
            elif choice == "2":
                return self._handle_manual_entry()
            elif choice == "3":
                return self._create_template_file()
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    
    def _handle_json_file(self) -> Path:
        """Handle JSON file upload."""
        while True:
            file_path = input("\nEnter the path to your downloaded JSON file: ").strip()
            file_path = Path(file_path.strip('"\'')).expanduser().resolve()
            
            if not file_path.exists():
                print(f"File not found: {file_path}")
                continue
            
            try:
                with open(file_path, 'r') as f:
                    credentials = json.load(f)
                
                # Validate the JSON structure
                if 'web' in credentials or 'installed' in credentials:
                    # Copy to credentials directory
                    target_path = self.config.CLIENT_SECRETS_FILE
                    with open(target_path, 'w') as f:
                        json.dump(credentials, f, indent=2)
                    
                    logger.info(f"✓ Client secrets saved to: {target_path}")
                    return target_path
                else:
                    print("Invalid JSON format. Please check your file.")
                    
            except json.JSONDecodeError:
                print("Invalid JSON file. Please check the file format.")
            except Exception as e:
                print(f"Error reading file: {e}")
    
    def _handle_manual_entry(self) -> Path:
        """Handle manual credential entry."""
        print("\nEnter your OAuth 2.0 credentials:")
        
        client_id = input("Client ID: ").strip()
        client_secret = input("Client Secret: ").strip()
        project_id = input("Project ID (optional): ").strip() or "voice-assistant"
        
        if not client_id or not client_secret:
            print("Client ID and Client Secret are required.")
            return self._handle_manual_entry()
        
        # Create client secrets structure
        credentials = {
            "web": {
                "client_id": client_id,
                "project_id": project_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": [self.config.REDIRECT_URI]
            }
        }
        
        # Save to file
        target_path = self.config.CLIENT_SECRETS_FILE
        with open(target_path, 'w') as f:
            json.dump(credentials, f, indent=2)
        
        logger.info(f"✓ Client secrets saved to: {target_path}")
        return target_path
    
    def _create_template_file(self) -> Path:
        """Create a template client secrets file."""
        template = self.config.create_client_secrets_template()
        target_path = self.config.CLIENT_SECRETS_FILE
        
        with open(target_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        print(f"\n✓ Template created at: {target_path}")
        print("\nPlease edit this file with your actual credentials.")
        print("Then run this setup script again.")
        
        return target_path
    
    def configure_environment(self, client_secrets_path: Path):
        """Configure environment variables."""
        print("\n" + "-"*60)
        print("STEP 3: CONFIGURE ENVIRONMENT")
        print("-"*60)
        
        # Read client secrets to get client ID and secret
        try:
            with open(client_secrets_path, 'r') as f:
                credentials = json.load(f)
            
            # Extract credentials
            if 'web' in credentials:
                client_data = credentials['web']
            elif 'installed' in credentials:
                client_data = credentials['installed']
            else:
                logger.error("Invalid client secrets format")
                return
            
            client_id = client_data.get('client_id')
            client_secret = client_data.get('client_secret')
            
            if not client_id or not client_secret:
                logger.error("Missing client_id or client_secret in credentials file")
                return
            
            # Create .env file
            env_file = self.config.PROJECT_ROOT / '.env'
            env_content = []
            
            # Read existing .env file if it exists
            if env_file.exists():
                with open(env_file, 'r') as f:
                    env_content = f.readlines()
            
            # Update or add Google credentials
            google_vars = {
                'GOOGLE_CLIENT_ID': client_id,
                'GOOGLE_CLIENT_SECRET': client_secret
            }
            
            # Remove existing Google variables
            env_content = [line for line in env_content 
                          if not any(line.startswith(f'{var}=') for var in google_vars.keys())]
            
            # Add new Google variables
            for var, value in google_vars.items():
                env_content.append(f'{var}={value}\n')
            
            # Write updated .env file
            with open(env_file, 'w') as f:
                f.writelines(env_content)
            
            logger.info(f"✓ Environment variables saved to: {env_file}")
            
        except Exception as e:
            logger.error(f"Error configuring environment: {e}")
    
    def test_authentication(self):
        """Test the authentication setup."""
        print("\n" + "-"*60)
        print("STEP 4: TEST AUTHENTICATION")
        print("-"*60)
        
        try:
            from .google_oauth import GoogleOAuthManager
            
            oauth_manager = GoogleOAuthManager()
            
            print("\nTesting OAuth configuration...")
            
            # Validate configuration
            validation = self.config.validate_config()
            if not validation['valid']:
                logger.error("Configuration validation failed:")
                for issue in validation['issues']:
                    logger.error(f"  - {issue}")
                return False
            
            if validation['warnings']:
                for warning in validation['warnings']:
                    logger.warning(f"  - {warning}")
            
            logger.info("✓ Configuration validation passed")
            
            # Test authorization URL generation
            try:
                import asyncio
                auth_url = asyncio.run(oauth_manager.get_authorization_url())
                logger.info("✓ OAuth authorization URL generated successfully")
                
                print(f"\nTo complete setup, visit this URL to authorize the application:")
                print(f"{auth_url}")
                
                return True
                
            except Exception as e:
                logger.error(f"Error generating authorization URL: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing authentication: {e}")
            return False
    
    def show_next_steps(self):
        """Show next steps after setup."""
        print("\n" + "="*60)
        print("SETUP COMPLETE!")
        print("="*60)
        
        print("\nNext steps:")
        print("\n1. Start the Voice Assistant application:")
        print("   npm start")
        print("\n2. The authentication window will open automatically")
        print("\n3. Complete the Google OAuth flow in your browser")
        print("\n4. Start using voice commands with Google Workspace!")
        
        print("\nSupported voice commands:")
        print("  - 'Create a task: Buy groceries'")
        print("  - 'Schedule meeting tomorrow at 2 PM'")
        print("  - 'Show my calendar for today'")
        print("  - 'Create a document called Meeting Notes'")
        
        print("\nFor troubleshooting, check the logs in:")
        print(f"  {self.config.PROJECT_ROOT / 'logs'}")
    
    def run_setup(self):
        """Run the complete setup process."""
        try:
            self.print_banner()
            
            if not self.check_prerequisites():
                return False
            
            self.create_directories()
            self.show_google_cloud_instructions()
            
            client_secrets_path = self.get_client_secrets_file()
            if not client_secrets_path:
                logger.error("Failed to configure client secrets")
                return False
            
            self.configure_environment(client_secrets_path)
            
            if self.test_authentication():
                self.show_next_steps()
                return True
            else:
                logger.error("Authentication test failed")
                return False
                
        except KeyboardInterrupt:
            print("\n\nSetup cancelled by user.")
            return False
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False

def main():
    """Main entry point for the setup script."""
    setup = GoogleAuthSetup()
    success = setup.run_setup()
    
    if success:
        print("\n🎉 Google OAuth setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()