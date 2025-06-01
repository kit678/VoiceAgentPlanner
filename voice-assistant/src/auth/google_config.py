import os
from pathlib import Path
from typing import List, Dict, Any

class GoogleConfig:
    """
    Configuration settings for Google OAuth and API integration.
    """
    
    # OAuth 2.0 Configuration
    CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    
    # Redirect URI for OAuth flow
    REDIRECT_URI = 'http://localhost:8080/oauth/callback'
    
    # OAuth 2.0 Scopes for Google Workspace services
    SCOPES = [
        # Google Tasks
        'https://www.googleapis.com/auth/tasks',
        'https://www.googleapis.com/auth/tasks.readonly',
        
        # Google Calendar
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/calendar.readonly',
        
        # Google Drive
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.readonly',
        
        # Google Docs
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/documents.readonly',
        
        # User profile information
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
        'openid'
    ]
    
    # Minimal scopes for basic functionality
    MINIMAL_SCOPES = [
        'https://www.googleapis.com/auth/tasks',
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/userinfo.profile',
        'openid'
    ]
    
    # Service-specific scope groups
    SCOPE_GROUPS = {
        'tasks': [
            'https://www.googleapis.com/auth/tasks',
            'https://www.googleapis.com/auth/tasks.readonly'
        ],
        'calendar': [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events',
            'https://www.googleapis.com/auth/calendar.readonly'
        ],
        'drive': [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive.readonly'
        ],
        'docs': [
            'https://www.googleapis.com/auth/documents',
            'https://www.googleapis.com/auth/documents.readonly'
        ],
        'profile': [
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/userinfo.email',
            'openid'
        ]
    }
    
    # API Service Discovery URLs
    SERVICE_DISCOVERY_URLS = {
        'tasks': 'https://tasks.googleapis.com/$discovery/rest?version=v1',
        'calendar': 'https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest',
        'drive': 'https://www.googleapis.com/discovery/v1/apis/drive/v3/rest',
        'docs': 'https://docs.googleapis.com/$discovery/rest?version=v1',
        'oauth2': 'https://www.googleapis.com/discovery/v1/apis/oauth2/v2/rest'
    }
    
    # File paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    CREDENTIALS_DIR = PROJECT_ROOT / 'credentials'
    TOKEN_FILE = CREDENTIALS_DIR / 'google_token.json'
    CLIENT_SECRETS_FILE = CREDENTIALS_DIR / 'google_client_secrets.json'
    
    # OAuth server configuration
    OAUTH_SERVER_HOST = 'localhost'
    OAUTH_SERVER_PORT = 8080
    OAUTH_TIMEOUT = 300  # 5 minutes
    
    # Token refresh settings
    TOKEN_REFRESH_THRESHOLD = 300  # Refresh if expires within 5 minutes
    MAX_REFRESH_ATTEMPTS = 3
    
    # Rate limiting settings
    API_RATE_LIMITS = {
        'tasks': {
            'requests_per_second': 10,
            'requests_per_day': 50000
        },
        'calendar': {
            'requests_per_second': 10,
            'requests_per_day': 1000000
        },
        'drive': {
            'requests_per_second': 10,
            'requests_per_day': 1000000000
        },
        'docs': {
            'requests_per_second': 5,
            'requests_per_day': 300
        }
    }
    
    @classmethod
    def get_scopes_for_services(cls, services: List[str]) -> List[str]:
        """
        Get OAuth scopes for specific services.
        
        Args:
            services: List of service names (e.g., ['tasks', 'calendar'])
            
        Returns:
            List of OAuth scopes
        """
        scopes = set()
        
        # Always include profile scopes
        scopes.update(cls.SCOPE_GROUPS['profile'])
        
        # Add service-specific scopes
        for service in services:
            if service in cls.SCOPE_GROUPS:
                scopes.update(cls.SCOPE_GROUPS[service])
        
        return list(scopes)
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """
        Validate the Google configuration.
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        # Check required environment variables
        if not cls.CLIENT_ID:
            issues.append('GOOGLE_CLIENT_ID environment variable is not set')
        
        if not cls.CLIENT_SECRET:
            issues.append('GOOGLE_CLIENT_SECRET environment variable is not set')
        
        # Check credentials directory
        if not cls.CREDENTIALS_DIR.exists():
            warnings.append(f'Credentials directory does not exist: {cls.CREDENTIALS_DIR}')
        
        # Check client secrets file
        if not cls.CLIENT_SECRETS_FILE.exists():
            warnings.append(f'Client secrets file does not exist: {cls.CLIENT_SECRETS_FILE}')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    @classmethod
    def create_client_secrets_template(cls) -> Dict[str, Any]:
        """
        Create a template for the Google client secrets file.
        
        Returns:
            Dictionary template for client secrets
        """
        return {
            "web": {
                "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
                "project_id": "your-project-id",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": "YOUR_CLIENT_SECRET",
                "redirect_uris": [cls.REDIRECT_URI]
            }
        }
    
    @classmethod
    def get_service_config(cls, service_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific Google service.
        
        Args:
            service_name: Name of the service (e.g., 'tasks', 'calendar')
            
        Returns:
            Dictionary with service configuration
        """
        return {
            'name': service_name,
            'scopes': cls.SCOPE_GROUPS.get(service_name, []),
            'discovery_url': cls.SERVICE_DISCOVERY_URLS.get(service_name),
            'rate_limits': cls.API_RATE_LIMITS.get(service_name, {})
        }
    
    @classmethod
    def ensure_credentials_dir(cls) -> None:
        """
        Ensure the credentials directory exists.
        """
        cls.CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create .gitignore to prevent committing credentials
        gitignore_file = cls.CREDENTIALS_DIR / '.gitignore'
        if not gitignore_file.exists():
            with open(gitignore_file, 'w') as f:
                f.write('# Ignore all credential files\n')
                f.write('*.json\n')
                f.write('*.key\n')
                f.write('*.pem\n')
                f.write('*.p12\n')

# Environment-specific configurations
class DevelopmentConfig(GoogleConfig):
    """Development environment configuration."""
    DEBUG = True
    OAUTH_SERVER_PORT = 8080

class ProductionConfig(GoogleConfig):
    """Production environment configuration."""
    DEBUG = False
    OAUTH_SERVER_PORT = 8443  # HTTPS port
    REDIRECT_URI = 'https://your-domain.com/oauth/callback'

class TestingConfig(GoogleConfig):
    """Testing environment configuration."""
    DEBUG = True
    SCOPES = GoogleConfig.MINIMAL_SCOPES  # Use minimal scopes for testing
    OAUTH_TIMEOUT = 60  # Shorter timeout for tests

# Configuration factory
def get_config(environment: str = None) -> GoogleConfig:
    """
    Get configuration based on environment.
    
    Args:
        environment: Environment name ('development', 'production', 'testing')
        
    Returns:
        Configuration class instance
    """
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'development')
    
    config_map = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    return config_map.get(environment, DevelopmentConfig)