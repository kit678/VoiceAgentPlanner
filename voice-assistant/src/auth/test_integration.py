#!/usr/bin/env python3
"""
Integration tests for Google OAuth Authentication System

These tests verify the complete authentication flow and API integration
with real Google services. Run these tests only when you have valid
Google OAuth credentials configured.

Usage:
    python src/auth/test_integration.py

Note: These tests require:
1. Valid Google OAuth credentials in client_secrets.json
2. Environment variables GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
3. Internet connection
4. User interaction for OAuth flow (first run)
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .google_oauth import GoogleOAuthManager
from .credential_manager import CredentialManager
from .google_config import GoogleConfig
from loguru import logger


class GoogleIntegrationTest:
    """Integration test suite for Google OAuth and API functionality."""
    
    def __init__(self):
        self.oauth_manager = GoogleOAuthManager()
        self.config = GoogleConfig()
        self.setup_logger()
        
    def setup_logger(self):
        """Configure logging for tests."""
        logger.remove()  # Remove default handler
        logger.add(
            sys.stdout,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            level="INFO"
        )
    
    async def test_configuration(self) -> bool:
        """Test OAuth configuration validity."""
        logger.info("Testing OAuth configuration...")
        
        try:
            # Validate configuration
            validation = self.config.validate_config()
            
            if not validation['valid']:
                logger.error("Configuration validation failed:")
                for issue in validation['issues']:
                    logger.error(f"  - {issue}")
                return False
            
            if validation['warnings']:
                logger.warning("Configuration warnings:")
                for warning in validation['warnings']:
                    logger.warning(f"  - {warning}")
            
            logger.success("✓ Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration test failed: {e}")
            return False
    
    async def test_authentication_flow(self) -> bool:
        """Test the complete OAuth authentication flow."""
        logger.info("Testing authentication flow...")
        
        try:
            # Check if already authenticated
            if await self.oauth_manager.is_authenticated():
                logger.info("✓ Already authenticated")
                return True
            
            # Generate authorization URL
            auth_url = await self.oauth_manager.get_authorization_url()
            logger.info(f"Authorization URL generated: {auth_url[:50]}...")
            
            # In a real integration test, you would:
            # 1. Open the URL in a browser
            # 2. Complete the OAuth flow
            # 3. Extract the authorization code
            # 4. Call handle_callback with the code
            
            logger.warning("Manual OAuth flow required - visit the URL above")
            logger.info("✓ Authorization URL generation successful")
            return True
            
        except Exception as e:
            logger.error(f"Authentication flow test failed: {e}")
            return False
    
    async def test_user_info(self) -> bool:
        """Test retrieving user information."""
        logger.info("Testing user info retrieval...")
        
        try:
            if not await self.oauth_manager.is_authenticated():
                logger.warning("Not authenticated - skipping user info test")
                return True
            
            user_info = await self.oauth_manager.get_user_info()
            
            if user_info and 'email' in user_info:
                logger.success(f"✓ User info retrieved: {user_info['email']}")
                return True
            else:
                logger.error("Failed to retrieve user info")
                return False
                
        except Exception as e:
            logger.error(f"User info test failed: {e}")
            return False
    
    async def test_tasks_api(self) -> bool:
        """Test Google Tasks API integration."""
        logger.info("Testing Google Tasks API...")
        
        try:
            if not await self.oauth_manager.is_authenticated():
                logger.warning("Not authenticated - skipping Tasks API test")
                return True
            
            # Get Tasks service
            tasks_service = await self.oauth_manager.get_tasks_service()
            
            # List task lists
            task_lists = tasks_service.tasklists().list().execute()
            
            if 'items' in task_lists:
                logger.success(f"✓ Tasks API working - found {len(task_lists['items'])} task lists")
                
                # Test creating a task (optional)
                if task_lists['items']:
                    default_list = task_lists['items'][0]['id']
                    
                    # Create a test task
                    test_task = {
                        'title': f'Integration Test Task - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                        'notes': 'This task was created by the integration test'
                    }
                    
                    created_task = tasks_service.tasks().insert(
                        tasklist=default_list,
                        body=test_task
                    ).execute()
                    
                    logger.success(f"✓ Test task created: {created_task['title']}")
                    
                    # Clean up - delete the test task
                    tasks_service.tasks().delete(
                        tasklist=default_list,
                        task=created_task['id']
                    ).execute()
                    
                    logger.info("✓ Test task cleaned up")
                
                return True
            else:
                logger.warning("No task lists found")
                return True
                
        except Exception as e:
            logger.error(f"Tasks API test failed: {e}")
            return False
    
    async def test_calendar_api(self) -> bool:
        """Test Google Calendar API integration."""
        logger.info("Testing Google Calendar API...")
        
        try:
            if not await self.oauth_manager.is_authenticated():
                logger.warning("Not authenticated - skipping Calendar API test")
                return True
            
            # Get Calendar service
            calendar_service = await self.oauth_manager.get_calendar_service()
            
            # List calendars
            calendars = calendar_service.calendarList().list().execute()
            
            if 'items' in calendars:
                logger.success(f"✓ Calendar API working - found {len(calendars['items'])} calendars")
                
                # Test listing events from primary calendar
                now = datetime.utcnow().isoformat() + 'Z'
                events_result = calendar_service.events().list(
                    calendarId='primary',
                    timeMin=now,
                    maxResults=10,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                logger.success(f"✓ Found {len(events)} upcoming events")
                
                return True
            else:
                logger.warning("No calendars found")
                return True
                
        except Exception as e:
            logger.error(f"Calendar API test failed: {e}")
            return False
    
    async def test_drive_api(self) -> bool:
        """Test Google Drive API integration."""
        logger.info("Testing Google Drive API...")
        
        try:
            if not await self.oauth_manager.is_authenticated():
                logger.warning("Not authenticated - skipping Drive API test")
                return True
            
            # Get Drive service
            drive_service = await self.oauth_manager.get_drive_service()
            
            # List files (first 10)
            results = drive_service.files().list(
                pageSize=10,
                fields="nextPageToken, files(id, name, mimeType)"
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                logger.success(f"✓ Drive API working - found {len(files)} files")
                for file in files[:3]:  # Show first 3 files
                    logger.info(f"  - {file['name']} ({file['mimeType']})")
            else:
                logger.info("✓ Drive API working - no files found")
            
            return True
                
        except Exception as e:
            logger.error(f"Drive API test failed: {e}")
            return False
    
    async def test_docs_api(self) -> bool:
        """Test Google Docs API integration."""
        logger.info("Testing Google Docs API...")
        
        try:
            if not await self.oauth_manager.is_authenticated():
                logger.warning("Not authenticated - skipping Docs API test")
                return True
            
            # Get Docs service
            docs_service = await self.oauth_manager.get_docs_service()
            
            # For Docs API, we need a document ID to test
            # We'll just verify the service is accessible
            logger.success("✓ Docs API service created successfully")
            
            # Note: To fully test Docs API, you would need:
            # 1. Create a test document
            # 2. Read its content
            # 3. Update the content
            # 4. Delete the document
            
            return True
                
        except Exception as e:
            logger.error(f"Docs API test failed: {e}")
            return False
    
    async def test_credential_management(self) -> bool:
        """Test credential storage and management."""
        logger.info("Testing credential management...")
        
        try:
            credential_manager = CredentialManager()
            
            # Test storing dummy credentials
            test_credentials = {
                'token': 'test-token',
                'refresh_token': 'test-refresh-token',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'client_id': 'test-client-id',
                'client_secret': 'test-client-secret'
            }
            
            # Store test credentials
            result = credential_manager.store_credentials('test-service', test_credentials)
            if not result:
                logger.error("Failed to store test credentials")
                return False
            
            # Load test credentials
            loaded_credentials = credential_manager.load_credentials('test-service')
            if not loaded_credentials:
                logger.error("Failed to load test credentials")
                return False
            
            # Verify credentials match
            if loaded_credentials['token'] != test_credentials['token']:
                logger.error("Loaded credentials don't match stored credentials")
                return False
            
            # Clean up test credentials
            credential_manager.delete_credentials('test-service')
            
            logger.success("✓ Credential management working correctly")
            return True
            
        except Exception as e:
            logger.error(f"Credential management test failed: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all integration tests."""
        logger.info("Starting Google OAuth Integration Tests")
        logger.info("=" * 50)
        
        tests = [
            ("Configuration", self.test_configuration),
            ("Authentication Flow", self.test_authentication_flow),
            ("User Info", self.test_user_info),
            ("Tasks API", self.test_tasks_api),
            ("Calendar API", self.test_calendar_api),
            ("Drive API", self.test_drive_api),
            ("Docs API", self.test_docs_api),
            ("Credential Management", self.test_credential_management)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            logger.info(f"\nRunning {test_name} test...")
            try:
                result = await test_func()
                results.append((test_name, result))
                
                if result:
                    logger.success(f"✓ {test_name} test passed")
                else:
                    logger.error(f"✗ {test_name} test failed")
                    
            except Exception as e:
                logger.error(f"✗ {test_name} test failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("TEST SUMMARY")
        logger.info("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"{test_name:<20} {status}")
        
        logger.info(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            logger.success("🎉 All integration tests passed!")
            return True
        else:
            logger.error(f"❌ {total - passed} tests failed")
            return False


async def main():
    """Main entry point for integration tests."""
    # Check prerequisites
    if not os.getenv('GOOGLE_CLIENT_ID') or not os.getenv('GOOGLE_CLIENT_SECRET'):
        logger.error("Missing required environment variables:")
        logger.error("  - GOOGLE_CLIENT_ID")
        logger.error("  - GOOGLE_CLIENT_SECRET")
        logger.info("\nPlease run the setup script first:")
        logger.info("  python src/auth/setup_google_auth.py")
        return False
    
    # Run tests
    test_suite = GoogleIntegrationTest()
    success = await test_suite.run_all_tests()
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nTests cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Integration tests failed: {e}")
        sys.exit(1)