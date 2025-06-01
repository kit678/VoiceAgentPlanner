import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
import tempfile
from loguru import logger

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .google_oauth import GoogleOAuthManager
from .credential_manager import CredentialManager

class ElectronAuthHandler:
    """
    Handles authentication and Google API calls for the Electron application.
    This class bridges between the Electron main process and Python authentication logic.
    """
    
    def __init__(self):
        self.oauth_manager = GoogleOAuthManager()
        self.credential_manager = CredentialManager()
        self.temp_dir = Path(tempfile.gettempdir()) / "voice_assistant_electron"
        self.temp_dir.mkdir(exist_ok=True)
        
        # IPC communication files
        self.request_file = self.temp_dir / "auth_request.json"
        self.response_file = self.temp_dir / "auth_response.json"
        self.status_file = self.temp_dir / "auth_status.json"
        
        logger.info("ElectronAuthHandler initialized")
    
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle authentication and API requests from Electron main process.
        
        Args:
            request_data: Dictionary containing request type and parameters
            
        Returns:
            Dictionary containing response data
        """
        try:
            request_type = request_data.get('type')
            params = request_data.get('params', {})
            
            logger.info(f"Handling request: {request_type}")
            
            # Authentication requests
            if request_type == 'start_auth':
                return await self._handle_start_auth(params)
            elif request_type == 'check_status':
                return await self._handle_check_status(params)
            elif request_type == 'revoke_auth':
                return await self._handle_revoke_auth(params)
            
            # Google Tasks API requests
            elif request_type == 'tasks_list_tasklists':
                return await self._handle_tasks_list_tasklists(params)
            elif request_type == 'tasks_create_tasklist':
                return await self._handle_tasks_create_tasklist(params)
            elif request_type == 'tasks_list_tasks':
                return await self._handle_tasks_list_tasks(params)
            elif request_type == 'tasks_create_task':
                return await self._handle_tasks_create_task(params)
            elif request_type == 'tasks_update_task':
                return await self._handle_tasks_update_task(params)
            elif request_type == 'tasks_delete_task':
                return await self._handle_tasks_delete_task(params)
            
            # Google Calendar API requests
            elif request_type == 'calendar_list_calendars':
                return await self._handle_calendar_list_calendars(params)
            elif request_type == 'calendar_list_events':
                return await self._handle_calendar_list_events(params)
            elif request_type == 'calendar_create_event':
                return await self._handle_calendar_create_event(params)
            elif request_type == 'calendar_update_event':
                return await self._handle_calendar_update_event(params)
            elif request_type == 'calendar_delete_event':
                return await self._handle_calendar_delete_event(params)
            
            # Google Drive API requests
            elif request_type == 'drive_list_files':
                return await self._handle_drive_list_files(params)
            elif request_type == 'drive_create_file':
                return await self._handle_drive_create_file(params)
            elif request_type == 'drive_get_file':
                return await self._handle_drive_get_file(params)
            elif request_type == 'drive_update_file':
                return await self._handle_drive_update_file(params)
            elif request_type == 'drive_delete_file':
                return await self._handle_drive_delete_file(params)
            
            # Google Docs API requests
            elif request_type == 'docs_create_document':
                return await self._handle_docs_create_document(params)
            elif request_type == 'docs_get_document':
                return await self._handle_docs_get_document(params)
            elif request_type == 'docs_update_document':
                return await self._handle_docs_update_document(params)
            
            else:
                return {
                    'success': False,
                    'error': f'Unknown request type: {request_type}'
                }
                
        except Exception as e:
            logger.error(f"Error handling request {request_type}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Authentication handlers
    async def _handle_start_auth(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start Google OAuth authentication flow."""
        try:
            auth_url = await self.oauth_manager.get_authorization_url()
            
            # Open browser for authentication
            import webbrowser
            webbrowser.open(auth_url)
            
            # Wait for callback (this would be handled by the OAuth callback server)
            # For now, we'll simulate the flow
            return {
                'success': True,
                'auth_url': auth_url,
                'message': 'Authentication started. Please complete in browser.'
            }
            
        except Exception as e:
            logger.error(f"Error starting authentication: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_check_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check current authentication status."""
        try:
            is_authenticated = await self.oauth_manager.is_authenticated()
            
            if is_authenticated:
                user_info = await self.oauth_manager.get_user_info()
                return {
                    'success': True,
                    'authenticated': True,
                    'user_info': user_info
                }
            else:
                return {
                    'success': True,
                    'authenticated': False
                }
                
        except Exception as e:
            logger.error(f"Error checking auth status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_revoke_auth(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Revoke Google authentication."""
        try:
            await self.oauth_manager.revoke_credentials()
            return {
                'success': True,
                'message': 'Authentication revoked successfully'
            }
            
        except Exception as e:
            logger.error(f"Error revoking authentication: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Google Tasks API handlers
    async def _handle_tasks_list_tasklists(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List Google Tasks task lists."""
        try:
            tasks_service = await self.oauth_manager.get_tasks_service()
            result = tasks_service.tasklists().list().execute()
            
            return {
                'success': True,
                'data': result.get('items', [])
            }
            
        except Exception as e:
            logger.error(f"Error listing task lists: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_tasks_create_tasklist(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Google Tasks task list."""
        try:
            title = params.get('title', 'New Task List')
            tasks_service = await self.oauth_manager.get_tasks_service()
            
            tasklist = {
                'title': title
            }
            
            result = tasks_service.tasklists().insert(body=tasklist).execute()
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error creating task list: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_tasks_list_tasks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List tasks in a Google Tasks task list."""
        try:
            tasklist_id = params.get('taskListId', '@default')
            tasks_service = await self.oauth_manager.get_tasks_service()
            
            result = tasks_service.tasks().list(tasklist=tasklist_id).execute()
            
            return {
                'success': True,
                'data': result.get('items', [])
            }
            
        except Exception as e:
            logger.error(f"Error listing tasks: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_tasks_create_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task in Google Tasks."""
        try:
            tasklist_id = params.get('taskListId', '@default')
            task_data = params.get('task', {})
            tasks_service = await self.oauth_manager.get_tasks_service()
            
            result = tasks_service.tasks().insert(
                tasklist=tasklist_id,
                body=task_data
            ).execute()
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_tasks_update_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task in Google Tasks."""
        try:
            tasklist_id = params.get('taskListId', '@default')
            task_id = params.get('taskId')
            task_data = params.get('task', {})
            tasks_service = await self.oauth_manager.get_tasks_service()
            
            result = tasks_service.tasks().update(
                tasklist=tasklist_id,
                task=task_id,
                body=task_data
            ).execute()
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error updating task: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_tasks_delete_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a task from Google Tasks."""
        try:
            tasklist_id = params.get('taskListId', '@default')
            task_id = params.get('taskId')
            tasks_service = await self.oauth_manager.get_tasks_service()
            
            tasks_service.tasks().delete(
                tasklist=tasklist_id,
                task=task_id
            ).execute()
            
            return {
                'success': True,
                'message': 'Task deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deleting task: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Google Calendar API handlers (simplified implementations)
    async def _handle_calendar_list_calendars(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List Google Calendar calendars."""
        try:
            calendar_service = await self.oauth_manager.get_calendar_service()
            result = calendar_service.calendarList().list().execute()
            
            return {
                'success': True,
                'data': result.get('items', [])
            }
            
        except Exception as e:
            logger.error(f"Error listing calendars: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_calendar_list_events(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List events from Google Calendar."""
        try:
            calendar_id = params.get('calendarId', 'primary')
            time_min = params.get('timeMin')
            time_max = params.get('timeMax')
            calendar_service = await self.oauth_manager.get_calendar_service()
            
            result = calendar_service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return {
                'success': True,
                'data': result.get('items', [])
            }
            
        except Exception as e:
            logger.error(f"Error listing events: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_calendar_create_event(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Google Calendar event."""
        try:
            calendar_id = params.get('calendarId', 'primary')
            event_data = params.get('event', {})
            calendar_service = await self.oauth_manager.get_calendar_service()
            
            result = calendar_service.events().insert(
                calendarId=calendar_id,
                body=event_data
            ).execute()
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_calendar_update_event(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a Google Calendar event."""
        try:
            calendar_id = params.get('calendarId', 'primary')
            event_id = params.get('eventId')
            event_data = params.get('event', {})
            calendar_service = await self.oauth_manager.get_calendar_service()
            
            result = calendar_service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event_data
            ).execute()
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error updating event: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_calendar_delete_event(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a Google Calendar event."""
        try:
            calendar_id = params.get('calendarId', 'primary')
            event_id = params.get('eventId')
            calendar_service = await self.oauth_manager.get_calendar_service()
            
            calendar_service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            return {
                'success': True,
                'message': 'Event deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deleting event: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Google Drive API handlers (simplified implementations)
    async def _handle_drive_list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List files from Google Drive."""
        try:
            query = params.get('query', '')
            page_size = params.get('pageSize', 10)
            drive_service = await self.oauth_manager.get_drive_service()
            
            result = drive_service.files().list(
                q=query,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)"
            ).execute()
            
            return {
                'success': True,
                'data': result.get('files', [])
            }
            
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_drive_create_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a file in Google Drive."""
        try:
            file_metadata = params.get('fileMetadata', {})
            media = params.get('media')
            drive_service = await self.oauth_manager.get_drive_service()
            
            # This is a simplified implementation
            # In practice, you'd handle media upload properly
            result = drive_service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error creating file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_drive_get_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get file metadata from Google Drive."""
        try:
            file_id = params.get('fileId')
            drive_service = await self.oauth_manager.get_drive_service()
            
            result = drive_service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, modifiedTime, size'
            ).execute()
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error getting file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_drive_update_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a file in Google Drive."""
        try:
            file_id = params.get('fileId')
            file_metadata = params.get('fileMetadata', {})
            drive_service = await self.oauth_manager.get_drive_service()
            
            result = drive_service.files().update(
                fileId=file_id,
                body=file_metadata
            ).execute()
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error updating file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_drive_delete_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a file from Google Drive."""
        try:
            file_id = params.get('fileId')
            drive_service = await self.oauth_manager.get_drive_service()
            
            drive_service.files().delete(fileId=file_id).execute()
            
            return {
                'success': True,
                'message': 'File deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Google Docs API handlers (simplified implementations)
    async def _handle_docs_create_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Google Docs document."""
        try:
            title = params.get('title', 'Untitled Document')
            docs_service = await self.oauth_manager.get_docs_service()
            
            document = {
                'title': title
            }
            
            result = docs_service.documents().create(body=document).execute()
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_docs_get_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a Google Docs document."""
        try:
            document_id = params.get('documentId')
            docs_service = await self.oauth_manager.get_docs_service()
            
            result = docs_service.documents().get(documentId=document_id).execute()
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_docs_update_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a Google Docs document."""
        try:
            document_id = params.get('documentId')
            requests = params.get('requests', [])
            docs_service = await self.oauth_manager.get_docs_service()
            
            result = docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def start_ipc_server(self):
        """Start IPC server to handle requests from Electron."""
        async def ipc_loop():
            logger.info("Starting IPC server for Electron communication")
            
            while True:
                try:
                    # Check for new requests
                    if self.request_file.exists():
                        with open(self.request_file, 'r') as f:
                            request_data = json.load(f)
                        
                        # Process request
                        response = await self.handle_request(request_data)
                        
                        # Write response
                        with open(self.response_file, 'w') as f:
                            json.dump(response, f)
                        
                        # Clean up request file
                        self.request_file.unlink()
                        
                        logger.info(f"Processed request: {request_data.get('type')}")
                    
                    # Small delay to prevent busy waiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error in IPC loop: {str(e)}")
                    await asyncio.sleep(1)
        
        # Run the IPC loop
        asyncio.run(ipc_loop())

if __name__ == "__main__":
    # Start the Electron auth handler
    handler = ElectronAuthHandler()
    handler.start_ipc_server()