#!/usr/bin/env python3
"""
Unit tests for Google OAuth Manager

These tests verify the functionality of the GoogleOAuthManager class
without requiring actual Google API calls.
"""

import asyncio
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ..google_oauth import GoogleOAuthManager
from ..credential_manager import CredentialManager


class TestGoogleOAuthManager(unittest.TestCase):
    """Test cases for GoogleOAuthManager class."""

    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret'
        })
        self.env_patcher.start()
        
        # Mock credential manager
        self.credential_manager_mock = MagicMock(spec=CredentialManager)
        
        # Create test instance with mocked dependencies
        self.oauth_manager = GoogleOAuthManager()
        self.oauth_manager.credential_manager = self.credential_manager_mock
        
        # Mock client secrets file
        self.mock_client_secrets = {
            "installed": {
                "client_id": "test-client-id",
                "project_id": "test-project",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": "test-client-secret",
                "redirect_uris": ["http://localhost:8080/callback"]
            }
        }

    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('google_auth_oauthlib.flow.Flow.from_client_secrets_file')
    async def test_get_authorization_url(self, mock_flow_from_file, mock_json_load, mock_file):
        """Test generating authorization URL."""
        # Setup mocks
        mock_json_load.return_value = self.mock_client_secrets
        
        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = ('https://test-auth-url', 'test-state')
        mock_flow_from_file.return_value = mock_flow
        
        # Call method
        auth_url = await self.oauth_manager.get_authorization_url()
        
        # Assertions
        self.assertEqual(auth_url, 'https://test-auth-url')
        mock_flow.authorization_url.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('google_auth_oauthlib.flow.Flow.from_client_secrets_file')
    async def test_handle_callback(self, mock_flow_from_file, mock_json_load, mock_file):
        """Test handling OAuth callback."""
        # Setup mocks
        mock_json_load.return_value = self.mock_client_secrets
        
        mock_flow = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.to_json.return_value = '{"token": "test-token"}'
        mock_flow.fetch_token.return_value = mock_credentials
        mock_flow_from_file.return_value = mock_flow
        
        # Call method
        result = await self.oauth_manager.handle_callback('test-code')
        
        # Assertions
        self.assertTrue(result)
        mock_flow.fetch_token.assert_called_once_with(code='test-code')
        self.credential_manager_mock.store_credentials.assert_called_once()

    async def test_is_authenticated(self):
        """Test checking authentication status."""
        # Setup mock
        self.credential_manager_mock.is_authenticated.return_value = True
        
        # Call method
        result = await self.oauth_manager.is_authenticated()
        
        # Assertions
        self.assertTrue(result)
        self.credential_manager_mock.is_authenticated.assert_called_once_with('google')

    @patch('googleapiclient.discovery.build')
    async def test_get_tasks_service(self, mock_build):
        """Test getting Tasks API service."""
        # Setup mocks
        mock_credentials = MagicMock()
        self.credential_manager_mock.load_credentials.return_value = mock_credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Call method
        result = await self.oauth_manager.get_tasks_service()
        
        # Assertions
        self.assertEqual(result, mock_service)
        mock_build.assert_called_once_with('tasks', 'v1', credentials=mock_credentials)

    @patch('googleapiclient.discovery.build')
    async def test_get_calendar_service(self, mock_build):
        """Test getting Calendar API service."""
        # Setup mocks
        mock_credentials = MagicMock()
        self.credential_manager_mock.load_credentials.return_value = mock_credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Call method
        result = await self.oauth_manager.get_calendar_service()
        
        # Assertions
        self.assertEqual(result, mock_service)
        mock_build.assert_called_once_with('calendar', 'v3', credentials=mock_credentials)

    @patch('googleapiclient.discovery.build')
    async def test_get_drive_service(self, mock_build):
        """Test getting Drive API service."""
        # Setup mocks
        mock_credentials = MagicMock()
        self.credential_manager_mock.load_credentials.return_value = mock_credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Call method
        result = await self.oauth_manager.get_drive_service()
        
        # Assertions
        self.assertEqual(result, mock_service)
        mock_build.assert_called_once_with('drive', 'v3', credentials=mock_credentials)

    @patch('googleapiclient.discovery.build')
    async def test_get_docs_service(self, mock_build):
        """Test getting Docs API service."""
        # Setup mocks
        mock_credentials = MagicMock()
        self.credential_manager_mock.load_credentials.return_value = mock_credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # Call method
        result = await self.oauth_manager.get_docs_service()
        
        # Assertions
        self.assertEqual(result, mock_service)
        mock_build.assert_called_once_with('docs', 'v1', credentials=mock_credentials)

    async def test_revoke_credentials(self):
        """Test revoking credentials."""
        # Setup mock
        self.credential_manager_mock.delete_credentials.return_value = True
        
        # Call method
        result = await self.oauth_manager.revoke_credentials()
        
        # Assertions
        self.assertTrue(result)
        self.credential_manager_mock.delete_credentials.assert_called_once_with('google')

    @patch('googleapiclient.discovery.build')
    async def test_get_user_info(self, mock_build):
        """Test getting user information."""
        # Setup mocks
        mock_credentials = MagicMock()
        self.credential_manager_mock.load_credentials.return_value = mock_credentials
        
        mock_service = MagicMock()
        mock_userinfo = MagicMock()
        mock_get = MagicMock()
        mock_execute = AsyncMock()
        mock_execute.return_value = {"email": "test@example.com", "name": "Test User"}
        
        mock_service.userinfo.return_value = mock_userinfo
        mock_userinfo.get.return_value = mock_get
        mock_get.execute = mock_execute
        
        mock_build.return_value = mock_service
        
        # Call method
        result = await self.oauth_manager.get_user_info()
        
        # Assertions
        self.assertEqual(result["email"], "test@example.com")
        self.assertEqual(result["name"], "Test User")
        mock_build.assert_called_once_with('oauth2', 'v2', credentials=mock_credentials)


class TestCredentialManager(unittest.TestCase):
    """Test cases for CredentialManager class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for credentials
        self.test_dir = Path("test_credentials")
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create test instance with test directory
        with patch('src.auth.credential_manager.CredentialManager.ensure_storage_dir'):
            with patch('src.auth.credential_manager.CredentialManager._generate_key'):
                self.credential_manager = CredentialManager(credentials_dir=self.test_dir)
                self.credential_manager._key = b'test_key_for_encryption_purposes_only=='

    def tearDown(self):
        """Clean up after tests."""
        # Remove test directory and files
        for file in self.test_dir.glob('*'):
            file.unlink()
        self.test_dir.rmdir()

    def test_ensure_storage_dir(self):
        """Test ensuring storage directory exists."""
        test_path = self.test_dir / "subdir"
        
        # Call method
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            self.credential_manager.ensure_storage_dir(test_path)
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch('keyring.set_password')
    @patch('keyring.get_password')
    def test_generate_key(self, mock_get_password, mock_set_password):
        """Test key generation and retrieval."""
        # Setup mock
        mock_get_password.return_value = None
        
        # Call method
        with patch('cryptography.fernet.Fernet.generate_key') as mock_generate:
            mock_generate.return_value = b'test_generated_key=='
            key = self.credential_manager._generate_key()
        
        # Assertions
        self.assertEqual(key, b'test_generated_key==')
        mock_set_password.assert_called_once()

    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        # Test data
        test_data = {"token": "secret-token", "refresh_token": "refresh-secret"}
        test_json = json.dumps(test_data)
        
        # Encrypt
        encrypted = self.credential_manager._encrypt(test_json)
        self.assertNotEqual(encrypted, test_json)
        
        # Decrypt
        decrypted = self.credential_manager._decrypt(encrypted)
        self.assertEqual(decrypted, test_json)
        
        # Verify original data can be recovered
        recovered_data = json.loads(decrypted)
        self.assertEqual(recovered_data, test_data)

    @patch('builtins.open', new_callable=mock_open)
    def test_store_credentials(self, mock_file):
        """Test storing credentials."""
        # Test data
        test_service = "google"
        test_credentials = {"token": "test-token"}
        
        # Call method with patch for encrypt
        with patch.object(self.credential_manager, '_encrypt', return_value=b'encrypted-data'):
            result = self.credential_manager.store_credentials(test_service, test_credentials)
        
        # Assertions
        self.assertTrue(result)
        mock_file.assert_called_once()
        mock_file().write.assert_called_once_with(b'encrypted-data')

    @patch('builtins.open', new_callable=mock_open, read_data=b'encrypted-data')
    @patch('os.path.exists')
    def test_load_credentials(self, mock_exists, mock_file):
        """Test loading credentials."""
        # Setup mocks
        mock_exists.return_value = True
        test_service = "google"
        test_credentials = {"token": "test-token"}
        
        # Call method with patch for decrypt
        with patch.object(self.credential_manager, '_decrypt', return_value=json.dumps(test_credentials)):
            result = self.credential_manager.load_credentials(test_service)
        
        # Assertions
        self.assertEqual(result, test_credentials)
        mock_file.assert_called_once()

    @patch('os.path.exists')
    @patch('os.remove')
    def test_delete_credentials(self, mock_remove, mock_exists):
        """Test deleting credentials."""
        # Setup mocks
        mock_exists.return_value = True
        test_service = "google"
        
        # Call method
        result = self.credential_manager.delete_credentials(test_service)
        
        # Assertions
        self.assertTrue(result)
        mock_remove.assert_called_once()

    @patch('os.path.exists')
    def test_is_authenticated(self, mock_exists):
        """Test checking authentication status."""
        # Setup mocks
        test_service = "google"
        
        # Test when credentials exist
        mock_exists.return_value = True
        result = self.credential_manager.is_authenticated(test_service)
        self.assertTrue(result)
        
        # Test when credentials don't exist
        mock_exists.return_value = False
        result = self.credential_manager.is_authenticated(test_service)
        self.assertFalse(result)


def run_async_test(coro):
    """Run an async test coroutine."""
    return asyncio.run(coro)


if __name__ == "__main__":
    unittest.main()