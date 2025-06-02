import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from loguru import logger
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
import sys

from auth.google_oauth import GoogleOAuthManager
from firebase.firestore_service import FirestoreService

class GoogleWorkspaceFunctions:
    """Google Workspace API integration functions for Tasks, Calendar, Drive, and Docs"""
    
    def __init__(self):
        self.oauth_manager = GoogleOAuthManager()
        self.firestore = FirestoreService()
        self._services = {}
        logger.info("GoogleWorkspaceFunctions initialized")
    
    async def _get_service(self, service_name: str):
        """Get authenticated Google API service client
        
        Args:
            service_name: Name of the service ('tasks', 'calendar', 'drive', 'docs')
            
        Returns:
            Authenticated service client
        """
        logger.info(f"=== GET SERVICE: {service_name} ===")
        
        if service_name not in self._services:
            try:
                logger.info(f"Service '{service_name}' not cached, initializing...")
                
                # Check authentication first
                logger.info("Checking OAuth authentication status...")
                is_authenticated = await self.oauth_manager.is_authenticated()
                logger.info(f"Authentication status: {is_authenticated}")
                
                if not is_authenticated:
                    logger.error("❌ User is not authenticated with Google OAuth")
                    raise Exception("User is not authenticated with Google OAuth")
                
                if service_name == 'tasks':
                    logger.info("Getting Google Tasks service...")
                    self._services[service_name] = await self.oauth_manager.get_tasks_service()
                elif service_name == 'calendar':
                    logger.info("Getting Google Calendar service...")
                    self._services[service_name] = await self.oauth_manager.get_calendar_service()
                elif service_name == 'drive':
                    logger.info("Getting Google Drive service...")
                    self._services[service_name] = await self.oauth_manager.get_drive_service()
                elif service_name == 'docs':
                    logger.info("Getting Google Docs service...")
                    self._services[service_name] = await self.oauth_manager.get_docs_service()
                else:
                    raise ValueError(f"Unknown service: {service_name}")
                    
                logger.info(f"✅ Successfully initialized {service_name} service")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {service_name} service: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
        else:
            logger.info(f"Using cached {service_name} service")
                
        return self._services[service_name]
    
    # ==================== GOOGLE TASKS INTEGRATION ====================
    
    async def create_google_task(self, task_name: str, due_date: Optional[str] = None, 
                               priority: str = "medium", list_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a task in Google Tasks
        
        Args:
            task_name: Name of the task
            due_date: Due date in ISO format (YYYY-MM-DD) or None
            priority: Priority level (high, medium, low)
            list_id: Google Tasks list ID (uses default if None)
            
        Returns:
            Dict with success status and task details
        """
        logger.info(f"=== CREATE GOOGLE TASK START ===")
        logger.info(f"Parameters: task_name='{task_name}', due_date='{due_date}', priority='{priority}', list_id='{list_id}'")
        
        try:
            logger.info("Getting Google Tasks service...")
            service = await self._get_service('tasks')
            logger.info("Google Tasks service obtained successfully")
            
            # Get default task list if none specified
            if not list_id:
                logger.info("No list_id provided, fetching default task list...")
                task_lists = service.tasklists().list().execute()
                logger.info(f"Retrieved task lists: {task_lists}")
                list_id = task_lists['items'][0]['id'] if task_lists.get('items') else None
                logger.info(f"Using default list_id: {list_id}")
                
            if not list_id:
                logger.error("No task lists found in Google Tasks")
                return {
                    "success": False,
                    "message": "No task lists found in Google Tasks"
                }
            
            # Prepare task data
            task_body = {
                'title': task_name,
                'notes': f"Priority: {priority}\nCreated by Voice Assistant"
            }
            logger.info(f"Prepared task body: {task_body}")
            
            # Add due date if provided
            if due_date:
                try:
                    # Convert to RFC 3339 format
                    due_datetime = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    task_body['due'] = due_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                    logger.info(f"Added due date to task: {task_body['due']}")
                except ValueError:
                    logger.warning(f"Invalid due date format: {due_date}")
            
            # Create task
            logger.info(f"Creating task in Google Tasks with list_id: {list_id}")
            result = service.tasks().insert(tasklist=list_id, body=task_body).execute()
            logger.info(f"Google Tasks API response: {result}")
            
            # Store in Firestore for local tracking
            task_data = {
                'google_task_id': result['id'],
                'google_list_id': list_id,
                'title': task_name,
                'priority': priority,
                'due_date': due_date,
                'status': 'needsAction',
                'created_at': datetime.now().isoformat(),
                'synced_with_google': True
            }
            
            logger.info(f"Storing task in Firestore: {task_data}")
            doc_ref = await self.firestore.add_document('tasks', task_data)
            logger.info(f"Firestore document created with ID: {doc_ref.id}")
            
            logger.info(f"✅ Successfully created Google Task: {task_name}")
            return {
                "success": True,
                "message": f"Task '{task_name}' created successfully",
                "task_id": result['id'],
                "local_id": doc_ref.id,
                "task_data": result
            }
            
        except HttpError as e:
            logger.error(f"❌ Google Tasks API error: {e}")
            logger.error(f"HTTP Error details: status={e.resp.status}, reason={e.resp.reason}")
            return {
                "success": False,
                "message": f"Google Tasks API error: {e}"
            }
        except Exception as e:
            logger.error(f"❌ Error creating Google Task: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "message": f"Error creating task: {str(e)}"
            }
    
    async def list_google_tasks(self, list_id: Optional[str] = None, 
                              status_filter: str = "all") -> Dict[str, Any]:
        """List tasks from Google Tasks
        
        Args:
            list_id: Google Tasks list ID (uses default if None)
            status_filter: Filter by status ('all', 'needsAction', 'completed')
            
        Returns:
            Dict with success status and tasks list, or a string message for TTS.
        """
        logger.info(f"=== LIST GOOGLE TASKS START ===")
        logger.info(f"Parameters: list_id='{list_id}', status_filter='{status_filter}'")
        try:
            service = await self._get_service('tasks')
            logger.info("Google Tasks service obtained successfully")
            
            # Fetch default task list if not provided
            task_lists = service.tasklists().list().execute()
            if task_lists.get('items'):
                list_id = task_lists['items'][0]['id'] 
                logger.info(f"No list_id provided, using default: {list_id}")
            else:
                logger.error("No task lists found for user.")
                return {
                    "success": False,
                    "message": "You don't have any task lists in Google Tasks."
                }
            
            # Build query parameters for the API call
            # Always fetch all tasks from the API initially, then filter locally
            api_params = {
                'tasklist': list_id,
                'showCompleted': True, # Always get completed tasks from API
                'showHidden': True,    # Always get hidden tasks from API
                'maxResults': 100      # Fetch a reasonable number for local filtering
            }
            
            logger.info(f"Fetching Google Tasks with API params: {api_params}")
            result = service.tasks().list(**api_params).execute()
            tasks = result.get('items', [])
            logger.info(f"Retrieved {len(tasks)} raw tasks from API for list_id: {list_id}")
            
            # Filter by status locally if needed
            if status_filter != "all":
                filtered_tasks = [task for task in tasks if task.get('status') == status_filter]
                logger.info(f"Filtered tasks by status '{status_filter}', count: {len(filtered_tasks)}")
            else:
                filtered_tasks = tasks # No local status filtering needed
            
            logger.info(f"Returning {len(filtered_tasks)} Google Tasks after filtering.")
            return {
                "success": True,
                "message": f"Retrieved {len(filtered_tasks)} tasks",
                "tasks": filtered_tasks,
                "count": len(filtered_tasks)
            }
            
        except HttpError as e:
            logger.error(f"Google Tasks API error in list_google_tasks: {e.content}") # Log content for more details
            return {
                "success": False,
                "message": f"Google Tasks API error: {e.resp.status} - {e.reason}"
            }
        except Exception as e:
            logger.error(f"Error listing Google Tasks: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error listing tasks: {str(e)}"
            }
    
    async def update_google_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing Google Task
        
        Args:
            task_id: Google Task ID
            updates: Dictionary of updates (title, notes, due, status)
            
        Returns:
            Dict with success status and updated task details
        """
        try:
            service = await self._get_service('tasks')
            
            # Get current task to preserve existing data
            current_task = service.tasks().get(tasklist='@default', task=task_id).execute()
            
            # Apply updates
            if 'title' in updates:
                current_task['title'] = updates['title']
            if 'notes' in updates:
                current_task['notes'] = updates['notes']
            if 'due_date' in updates and updates['due_date']:
                try:
                    due_datetime = datetime.fromisoformat(updates['due_date'].replace('Z', '+00:00'))
                    current_task['due'] = due_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                except ValueError:
                    logger.warning(f"Invalid due date format: {updates['due_date']}")
            if 'status' in updates:
                current_task['status'] = updates['status']
            
            # Update task
            result = service.tasks().update(
                tasklist='@default', 
                task=task_id, 
                body=current_task
            ).execute()
            
            # Update local Firestore record
            await self.firestore.update_document_by_field(
                'tasks', 
                'google_task_id', 
                task_id, 
                {
                    **updates,
                    'updated_at': datetime.now().isoformat(),
                    'synced_with_google': True
                }
            )
            
            logger.info(f"Updated Google Task: {task_id}")
            return {
                "success": True,
                "message": "Task updated successfully",
                "task_data": result
            }
            
        except HttpError as e:
            logger.error(f"Google Tasks API error: {e}")
            return {
                "success": False,
                "message": f"Google Tasks API error: {e}"
            }
        except Exception as e:
            logger.error(f"Error updating Google Task: {e}")
            return {
                "success": False,
                "message": f"Error updating task: {str(e)}"
            }
    
    async def complete_google_task(self, task_id: str) -> Dict[str, Any]:
        """Mark a Google Task as complete
        
        Args:
            task_id: Google Task ID
            
        Returns:
            Dict with success status
        """
        return await self.update_google_task(task_id, {'status': 'completed'})
    
    async def delete_google_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a Google Task
        
        Args:
            task_id: Google Task ID
            
        Returns:
            Dict with success status
        """
        try:
            service = await self._get_service('tasks')
            
            # Delete task
            service.tasks().delete(tasklist='@default', task=task_id).execute()
            
            # Delete from local Firestore
            await self.firestore.delete_document_by_field(
                'tasks', 
                'google_task_id', 
                task_id
            )
            
            logger.info(f"Deleted Google Task: {task_id}")
            return {
                "success": True,
                "message": "Task deleted successfully"
            }
            
        except HttpError as e:
            logger.error(f"Google Tasks API error: {e}")
            return {
                "success": False,
                "message": f"Google Tasks API error: {e}"
            }
        except Exception as e:
            logger.error(f"Error deleting Google Task: {e}")
            return {
                "success": False,
                "message": f"Error deleting task: {str(e)}"
            }
    
    # ==================== GOOGLE CALENDAR INTEGRATION ====================
    
    async def create_google_calendar_event(self, title: str, start_time: str, 
                                         end_time: str, description: str = "") -> Dict[str, Any]:
        """Create a calendar event in Google Calendar
        
        Args:
            title: Event title
            start_time: Start time in ISO format
            end_time: End time in ISO format
            description: Event description
            
        Returns:
            Dict with success status and event details
        """
        try:
            service = await self._get_service('calendar')
            
            # Prepare event data
            event_body = {
                'summary': title,
                'description': f"{description}\n\nCreated by Voice Assistant",
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'UTC'
                }
            }
            
            # Create event
            result = service.events().insert(calendarId='primary', body=event_body).execute()
            
            # Store in Firestore
            event_data = {
                'google_event_id': result['id'],
                'title': title,
                'description': description,
                'start_time': start_time,
                'end_time': end_time,
                'created_at': datetime.now().isoformat(),
                'synced_with_google': True
            }
            
            doc_ref = await self.firestore.add_document('calendar_events', event_data)
            
            logger.info(f"Created Google Calendar event: {title}")
            return {
                "success": True,
                "message": f"Event '{title}' created successfully",
                "event_id": result['id'],
                "local_id": doc_ref.id,
                "event_data": result
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return {
                "success": False,
                "message": f"Google Calendar API error: {e}"
            }
        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {e}")
            return {
                "success": False,
                "message": f"Error creating event: {str(e)}"
            }
    
    async def list_google_calendar_events(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """List calendar events from Google Calendar
        
        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format
            
        Returns:
            Dict with success status and events list
        """
        try:
            service = await self._get_service('calendar')
            
            # Get events
            result = service.events().list(
                calendarId='primary',
                timeMin=start_date,
                timeMax=end_date,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = result.get('items', [])
            
            logger.info(f"Retrieved {len(events)} Google Calendar events")
            return {
                "success": True,
                "message": f"Retrieved {len(events)} events",
                "events": events,
                "count": len(events)
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return {
                "success": False,
                "message": f"Google Calendar API error: {e}"
            }
        except Exception as e:
            logger.error(f"Error listing Google Calendar events: {e}")
            return {
                "success": False,
                "message": f"Error listing events: {str(e)}"
            }
    
    async def update_google_calendar_event(self, event_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a Google Calendar event
        
        Args:
            event_id: Google Calendar event ID
            updates: Dictionary of updates
            
        Returns:
            Dict with success status and updated event details
        """
        try:
            service = await self._get_service('calendar')
            
            # Get current event
            current_event = service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Apply updates
            if 'title' in updates:
                current_event['summary'] = updates['title']
            if 'description' in updates:
                current_event['description'] = updates['description']
            if 'start_time' in updates:
                current_event['start']['dateTime'] = updates['start_time']
            if 'end_time' in updates:
                current_event['end']['dateTime'] = updates['end_time']
            
            # Update event
            result = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=current_event
            ).execute()
            
            # Update local record
            await self.firestore.update_document_by_field(
                'calendar_events',
                'google_event_id',
                event_id,
                {
                    **updates,
                    'updated_at': datetime.now().isoformat(),
                    'synced_with_google': True
                }
            )
            
            logger.info(f"Updated Google Calendar event: {event_id}")
            return {
                "success": True,
                "message": "Event updated successfully",
                "event_data": result
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return {
                "success": False,
                "message": f"Google Calendar API error: {e}"
            }
        except Exception as e:
            logger.error(f"Error updating Google Calendar event: {e}")
            return {
                "success": False,
                "message": f"Error updating event: {str(e)}"
            }
    
    async def delete_google_calendar_event(self, event_id: str) -> Dict[str, Any]:
        """Delete a Google Calendar event
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Dict with success status
        """
        try:
            service = await self._get_service('calendar')
            
            # Delete event
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            
            # Delete from local Firestore
            await self.firestore.delete_document_by_field(
                'calendar_events',
                'google_event_id',
                event_id
            )
            
            logger.info(f"Deleted Google Calendar event: {event_id}")
            return {
                "success": True,
                "message": "Event deleted successfully"
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return {
                "success": False,
                "message": f"Google Calendar API error: {e}"
            }
        except Exception as e:
            logger.error(f"Error deleting Google Calendar event: {e}")
            return {
                "success": False,
                "message": f"Error deleting event: {str(e)}"
            }
    
    # ==================== GOOGLE DRIVE INTEGRATION ====================
    
    async def upload_to_google_drive(self, file_path: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Upload a file to Google Drive
        
        Args:
            file_path: Local file path to upload
            folder_id: Google Drive folder ID (uploads to root if None)
            
        Returns:
            Dict with success status and file details
        """
        try:
            service = await self._get_service('drive')
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "message": f"File not found: {file_path}"
                }
            
            # Prepare file metadata
            file_name = os.path.basename(file_path)
            file_metadata = {'name': file_name}
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Upload file
            from googleapiclient.http import MediaFileUpload
            media = MediaFileUpload(file_path)
            
            result = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,mimeType,createdTime'
            ).execute()
            
            # Store in Firestore
            file_data = {
                'google_file_id': result['id'],
                'name': result['name'],
                'size': result.get('size'),
                'mime_type': result.get('mimeType'),
                'folder_id': folder_id,
                'local_path': file_path,
                'uploaded_at': datetime.now().isoformat(),
                'synced_with_google': True
            }
            
            doc_ref = await self.firestore.add_document('drive_files', file_data)
            
            logger.info(f"Uploaded file to Google Drive: {file_name}")
            return {
                "success": True,
                "message": f"File '{file_name}' uploaded successfully",
                "file_id": result['id'],
                "local_id": doc_ref.id,
                "file_data": result
            }
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            return {
                "success": False,
                "message": f"Google Drive API error: {e}"
            }
        except Exception as e:
            logger.error(f"Error uploading to Google Drive: {e}")
            return {
                "success": False,
                "message": f"Error uploading file: {str(e)}"
            }
    
    async def list_google_drive_files(self, folder_id: Optional[str] = None, 
                                    file_type: Optional[str] = None) -> Dict[str, Any]:
        """List files from Google Drive
        
        Args:
            folder_id: Google Drive folder ID (lists root if None)
            file_type: MIME type filter (e.g., 'application/pdf')
            
        Returns:
            Dict with success status and files list
        """
        try:
            service = await self._get_service('drive')
            
            # Build query
            query_parts = []
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            if file_type:
                query_parts.append(f"mimeType='{file_type}'")
            
            query = ' and '.join(query_parts) if query_parts else None
            
            # Get files
            result = service.files().list(
                q=query,
                fields='files(id,name,size,mimeType,createdTime,modifiedTime)',
                orderBy='modifiedTime desc'
            ).execute()
            
            files = result.get('files', [])
            
            logger.info(f"Retrieved {len(files)} Google Drive files")
            return {
                "success": True,
                "message": f"Retrieved {len(files)} files",
                "files": files,
                "count": len(files)
            }
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            return {
                "success": False,
                "message": f"Google Drive API error: {e}"
            }
        except Exception as e:
            logger.error(f"Error listing Google Drive files: {e}")
            return {
                "success": False,
                "message": f"Error listing files: {str(e)}"
            }
    
    async def download_from_google_drive(self, file_id: str, local_path: str) -> Dict[str, Any]:
        """Download a file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            local_path: Local path to save the file
            
        Returns:
            Dict with success status
        """
        try:
            service = await self._get_service('drive')
            
            # Get file metadata
            file_metadata = service.files().get(fileId=file_id).execute()
            
            # Download file content
            request = service.files().get_media(fileId=file_id)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Save file
            with open(local_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
            
            logger.info(f"Downloaded file from Google Drive: {file_metadata['name']}")
            return {
                "success": True,
                "message": f"File '{file_metadata['name']}' downloaded successfully",
                "local_path": local_path,
                "file_name": file_metadata['name']
            }
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            return {
                "success": False,
                "message": f"Google Drive API error: {e}"
            }
        except Exception as e:
            logger.error(f"Error downloading from Google Drive: {e}")
            return {
                "success": False,
                "message": f"Error downloading file: {str(e)}"
            }
    
    async def create_google_drive_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a folder in Google Drive
        
        Args:
            folder_name: Name of the folder to create
            parent_id: Parent folder ID (creates in root if None)
            
        Returns:
            Dict with success status and folder details
        """
        try:
            service = await self._get_service('drive')
            
            # Prepare folder metadata
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                folder_metadata['parents'] = [parent_id]
            
            # Create folder
            result = service.files().create(
                body=folder_metadata,
                fields='id,name,createdTime'
            ).execute()
            
            # Store in Firestore
            folder_data = {
                'google_folder_id': result['id'],
                'name': folder_name,
                'parent_id': parent_id,
                'created_at': datetime.now().isoformat(),
                'synced_with_google': True
            }
            
            doc_ref = await self.firestore.add_document('drive_folders', folder_data)
            
            logger.info(f"Created Google Drive folder: {folder_name}")
            return {
                "success": True,
                "message": f"Folder '{folder_name}' created successfully",
                "folder_id": result['id'],
                "local_id": doc_ref.id,
                "folder_data": result
            }
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            return {
                "success": False,
                "message": f"Google Drive API error: {e}"
            }
        except Exception as e:
            logger.error(f"Error creating Google Drive folder: {e}")
            return {
                "success": False,
                "message": f"Error creating folder: {str(e)}"
            }
    
    # ==================== GOOGLE DOCS INTEGRATION ====================
    
    async def create_google_doc(self, title: str, content: str = "") -> Dict[str, Any]:
        """Create a new Google Doc
        
        Args:
            title: Document title
            content: Initial document content
            
        Returns:
            Dict with success status and document details
        """
        try:
            # Use Drive service to create the document
            drive_service = await self._get_service('drive')
            
            # Create document
            doc_metadata = {
                'name': title,
                'mimeType': 'application/vnd.google-apps.document'
            }
            
            result = drive_service.files().create(body=doc_metadata).execute()
            doc_id = result['id']
            
            # Add content if provided
            if content:
                docs_service = await self._get_service('docs')
                requests = [{
                    'insertText': {
                        'location': {'index': 1},
                        'text': content
                    }
                }]
                
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
            
            # Store in Firestore
            doc_data = {
                'google_doc_id': doc_id,
                'title': title,
                'content_preview': content[:200] if content else '',
                'created_at': datetime.now().isoformat(),
                'synced_with_google': True
            }
            
            doc_ref = await self.firestore.add_document('google_docs', doc_data)
            
            logger.info(f"Created Google Doc: {title}")
            return {
                "success": True,
                "message": f"Document '{title}' created successfully",
                "doc_id": doc_id,
                "local_id": doc_ref.id,
                "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit"
            }
            
        except HttpError as e:
            logger.error(f"Google Docs API error: {e}")
            return {
                "success": False,
                "message": f"Google Docs API error: {e}"
            }
        except Exception as e:
            logger.error(f"Error creating Google Doc: {e}")
            return {
                "success": False,
                "message": f"Error creating document: {str(e)}"
            }
    
    async def update_google_doc(self, doc_id: str, content: str) -> Dict[str, Any]:
        """Update Google Doc content
        
        Args:
            doc_id: Google Doc ID
            content: New content to append or replace
            
        Returns:
            Dict with success status
        """
        try:
            service = await self._get_service('docs')
            
            # Get current document to find end index
            doc = service.documents().get(documentId=doc_id).execute()
            doc_content = doc.get('body', {}).get('content', [])
            
            # Find the end index
            end_index = 1
            for element in doc_content:
                if 'endIndex' in element:
                    end_index = max(end_index, element['endIndex'])
            
            # Append content
            requests = [{
                'insertText': {
                    'location': {'index': end_index - 1},
                    'text': f"\n\n{content}"
                }
            }]
            
            service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            
            # Update local record
            await self.firestore.update_document_by_field(
                'google_docs',
                'google_doc_id',
                doc_id,
                {
                    'content_preview': content[:200],
                    'updated_at': datetime.now().isoformat(),
                    'synced_with_google': True
                }
            )
            
            logger.info(f"Updated Google Doc: {doc_id}")
            return {
                "success": True,
                "message": "Document updated successfully",
                "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit"
            }
            
        except HttpError as e:
            logger.error(f"Google Docs API error: {e}")
            return {
                "success": False,
                "message": f"Google Docs API error: {e}"
            }
        except Exception as e:
            logger.error(f"Error updating Google Doc: {e}")
            return {
                "success": False,
                "message": f"Error updating document: {str(e)}"
            }
    
    async def read_google_doc(self, doc_id: str) -> Dict[str, Any]:
        """Read content from a Google Doc
        
        Args:
            doc_id: Google Doc ID
            
        Returns:
            Dict with success status and document content
        """
        try:
            service = await self._get_service('docs')
            
            # Get document
            doc = service.documents().get(documentId=doc_id).execute()
            
            # Extract text content
            content = ""
            doc_content = doc.get('body', {}).get('content', [])
            
            for element in doc_content:
                if 'paragraph' in element:
                    paragraph = element['paragraph']
                    for text_run in paragraph.get('elements', []):
                        if 'textRun' in text_run:
                            content += text_run['textRun'].get('content', '')
            
            logger.info(f"Read Google Doc: {doc_id}")
            return {
                "success": True,
                "message": "Document read successfully",
                "title": doc.get('title', 'Untitled'),
                "content": content.strip(),
                "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit"
            }
            
        except HttpError as e:
            logger.error(f"Google Docs API error: {e}")
            return {
                "success": False,
                "message": f"Google Docs API error: {e}"
            }
        except Exception as e:
            logger.error(f"Error reading Google Doc: {e}")
            return {
                "success": False,
                "message": f"Error reading document: {str(e)}"
            }

# Add missing import for MediaIoBaseDownload
from googleapiclient.http import MediaIoBaseDownload