import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from loguru import logger
from .credential_manager import CredentialManager

class GoogleOAuthManager:
    """Manages Google OAuth 2.0 authentication flow and API client initialization."""
    
    # Google OAuth 2.0 scopes for different services
    SCOPES = {
        'tasks': 'https://www.googleapis.com/auth/tasks',
        'calendar': 'https://www.googleapis.com/auth/calendar',
        'drive': 'https://www.googleapis.com/auth/drive.file',
        'keep': 'https://www.googleapis.com/auth/keep',  # Note: Keep API has limited availability
        'docs': 'https://www.googleapis.com/auth/documents'
    }
    
    def __init__(self, client_secrets_path: str = None):
        """Initialize OAuth manager with client secrets.
        
        Args:
            client_secrets_path: Path to Google OAuth client secrets JSON file
        """
        self.client_secrets_path = client_secrets_path or os.path.join(
            os.path.dirname(__file__), '..', '..', 'config', 'google_client_secrets.json'
        )
        self.credential_manager = CredentialManager()
        self.flow = None
        self._credentials = None
        
        # Token file paths for compatibility with main.js
        self.token_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'config', 'token.json'
        )
        self.refresh_token_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'config', 'refresh_token.json'
        )
        
    def _get_required_scopes(self, services: List[str] = None) -> List[str]:
        """Get required OAuth scopes for specified services.
        
        Args:
            services: List of service names ('tasks', 'calendar', 'drive', 'docs')
            
        Returns:
            List of OAuth scope URLs
        """
        if not services:
            # Default to all available services
            services = ['tasks', 'calendar', 'drive', 'docs']
            
        scopes = []
        for service in services:
            if service in self.SCOPES:
                scopes.append(self.SCOPES[service])
            else:
                logger.warning(f"Unknown service: {service}")
                
        return scopes
    
    def initialize_flow(self, services: List[str] = None, redirect_uri: str = 'http://localhost:8080/oauth/callback') -> str:
        """Initialize OAuth flow and return authorization URL.
        
        Args:
            services: List of Google services to request access for
            redirect_uri: OAuth redirect URI
            
        Returns:
            Authorization URL for user to visit
        """
        try:
            if not os.path.exists(self.client_secrets_path):
                raise FileNotFoundError(
                    f"Google client secrets file not found at {self.client_secrets_path}. "
                    "Please download it from Google Cloud Console and place it in the config directory."
                )
            
            scopes = self._get_required_scopes(services)
            
            self.flow = Flow.from_client_secrets_file(
                self.client_secrets_path,
                scopes=scopes,
                redirect_uri=redirect_uri
            )
            
            # Generate authorization URL
            auth_url, _ = self.flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'  # Force consent screen to get refresh token
            )
            
            logger.info(f"OAuth flow initialized for services: {services}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Failed to initialize OAuth flow: {e}")
            raise
    
    async def handle_callback(self, authorization_code: str) -> bool:
        """Handle OAuth callback and exchange code for tokens.
        
        Args:
            authorization_code: Authorization code from OAuth callback
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            if not self.flow:
                raise ValueError("OAuth flow not initialized. Call initialize_flow() first.")
            
            # Exchange authorization code for credentials
            self.flow.fetch_token(code=authorization_code)
            self._credentials = self.flow.credentials
            
            # Store credentials securely
            await self.credential_manager.store_credentials(
                'google_oauth',
                {
                    'token': self._credentials.token,
                    'refresh_token': self._credentials.refresh_token,
                    'token_uri': self._credentials.token_uri,
                    'client_id': self._credentials.client_id,
                    'client_secret': self._credentials.client_secret,
                    'scopes': self._credentials.scopes
                }
            )
            
            logger.info("Google OAuth authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"OAuth callback handling failed: {e}")
            return False
    
    async def load_credentials(self) -> Optional[Credentials]:
        """Load stored credentials and refresh if necessary.
        
        Returns:
            Google OAuth credentials if available and valid
        """
        try:
            # Load stored credentials
            cred_data = await self.credential_manager.get_credentials('google_oauth')
            if not cred_data:
                logger.info("No stored Google credentials found")
                return None
            
            # Reconstruct credentials object
            self._credentials = Credentials(
                token=cred_data.get('token'),
                refresh_token=cred_data.get('refresh_token'),
                token_uri=cred_data.get('token_uri'),
                client_id=cred_data.get('client_id'),
                client_secret=cred_data.get('client_secret'),
                scopes=cred_data.get('scopes')
            )
            
            # Refresh token if expired
            if self._credentials.expired and self._credentials.refresh_token:
                logger.info("Refreshing expired Google OAuth token")
                self._credentials.refresh(Request())
                
                # Update stored credentials with new token
                await self.credential_manager.store_credentials(
                    'google_oauth',
                    {
                        'token': self._credentials.token,
                        'refresh_token': self._credentials.refresh_token,
                        'token_uri': self._credentials.token_uri,
                        'client_id': self._credentials.client_id,
                        'client_secret': self._credentials.client_secret,
                        'scopes': self._credentials.scopes
                    }
                )
            
            return self._credentials
            
        except Exception as e:
            logger.error(f"Failed to load Google credentials: {e}")
            return None
    
    def get_api_client(self, service_name: str, version: str = None):
        """Get authenticated Google API client for specified service.
        
        Args:
            service_name: Google service name ('tasks', 'calendar', 'drive', 'docs')
            version: API version (defaults to latest stable)
            
        Returns:
            Authenticated Google API client
        """
        if not self._credentials:
            raise ValueError("No valid credentials available. Please authenticate first.")
        
        # Default API versions
        default_versions = {
            'tasks': 'v1',
            'calendar': 'v3',
            'drive': 'v3',
            'docs': 'v1'
        }
        
        api_version = version or default_versions.get(service_name, 'v1')
        
        try:
            client = build(service_name, api_version, credentials=self._credentials)
            logger.info(f"Created {service_name} API client (v{api_version})")
            return client
            
        except Exception as e:
            logger.error(f"Failed to create {service_name} API client: {e}")
            raise
    
    async def revoke_credentials(self) -> bool:
        """Revoke stored Google OAuth credentials.
        
        Returns:
            True if revocation successful
        """
        try:
            if self._credentials:
                # Revoke token with Google
                self._credentials.revoke(Request())
            
            # Remove stored credentials
            await self.credential_manager.delete_credentials('google_oauth')
            self._credentials = None
            
            logger.info("Google OAuth credentials revoked")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke Google credentials: {e}")
            return False
    
    async def get_authorization_url(self, services: List[str] = None, redirect_uri: str = 'http://localhost:8080/oauth/callback') -> str:
        """Get authorization URL for OAuth flow.
        
        Args:
            services: List of Google services to request access for (defaults to all available)
            redirect_uri: OAuth redirect URI
            
        Returns:
            Authorization URL for user to visit
        """
        if services is None:
            services = ['tasks', 'calendar', 'drive', 'docs']
        
        return self.initialize_flow(services, redirect_uri)
    
    async def is_authenticated(self) -> bool:
        """Check if user is currently authenticated with Google.
        
        Returns:
            True if valid credentials are available
        """
        # Load credentials if not already loaded
        if not self._credentials:
            await self.load_credentials()
        
        return self._credentials is not None and self._credentials.valid
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get basic user information from Google.
        
        Returns:
            User information dictionary or None if not authenticated
        """
        if not self.is_authenticated():
            return None
        
        try:
            # Use OAuth2 API to get user info
            oauth2_client = build('oauth2', 'v2', credentials=self._credentials)
            user_info = oauth2_client.userinfo().get().execute()
            
            return {
                'id': user_info.get('id'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture')
            }
            
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None
    
    async def get_tasks_service(self):
        """Get authenticated Google Tasks API service.
        
        Returns:
            Authenticated Google Tasks API client
        """
        # Ensure we have valid credentials
        if not self._credentials:
            await self.load_credentials()
        
        return self.get_api_client('tasks', 'v1')
    
    async def get_calendar_service(self):
        """Get authenticated Google Calendar API service.
        
        Returns:
            Authenticated Google Calendar API client
        """
        # Ensure we have valid credentials
        if not self._credentials:
            await self.load_credentials()
        
        return self.get_api_client('calendar', 'v3')
    
    async def get_drive_service(self):
        """Get authenticated Google Drive API service.
        
        Returns:
            Authenticated Google Drive API client
        """
        # Ensure we have valid credentials
        if not self._credentials:
            await self.load_credentials()
        
        return self.get_api_client('drive', 'v3')
    
    async def get_docs_service(self):
        """Get authenticated Google Docs API service.
        
        Returns:
            Authenticated Google Docs API client
        """
        # Ensure we have valid credentials
        if not self._credentials:
            await self.load_credentials()
        
        return self.get_api_client('docs', 'v1')