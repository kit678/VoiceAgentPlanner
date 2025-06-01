import os
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger
from firebase.firestore_service import FirestoreService
import sys

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../config'))
from zapier_config import zapier_config

class IntegrationFunctions:
    """External integration functions for Zapier webhooks"""
    
    def __init__(self):
        self.firestore = FirestoreService()
        self.config = zapier_config
        logger.info(f"IntegrationFunctions initialized with {len(self.config.get_configured_services())} configured services")
    
    async def sync_with_trello(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync task with Trello via Zapier webhook"""
        try:
            if not self.config.is_service_configured("trello"):
                logger.warning("Trello webhook URL not configured")
                return {
                    "success": False,
                    "message": "Trello integration not configured. Please update zapier_config.py"
                }
            
            # Prepare data for Trello
            trello_data = {
                "name": task_data.get("name", ""),
                "description": task_data.get("description", ""),
                "due_date": task_data.get("due_date", ""),
                "priority": task_data.get("priority", "medium"),
                "status": task_data.get("status", "pending"),
                "labels": [task_data.get("priority", "medium")],
                "list_name": "Voice Assistant Tasks"
            }
            
            # Send to Zapier webhook
            response = requests.post(
                self.config.get_webhook_url("trello"),
                json=trello_data,
                headers={'Content-Type': 'application/json'},
                timeout=self.config.request_timeout
            )
            
            if response.status_code == 200:
                # Store Trello reference in Firestore
                await self.firestore.update_task_metadata(
                    task_data.get("id"),
                    {"trello_synced": True, "trello_sync_date": datetime.now().isoformat()}
                )
                
                logger.info(f"Task synced with Trello: {task_data.get('name')}")
                return {
                    "success": True,
                    "message": "Task synced with Trello successfully",
                    "trello_response": response.json() if response.content else None
                }
            else:
                logger.error(f"Trello sync failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Trello sync failed: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error syncing with Trello: {e}")
            return {
                "success": False,
                "message": f"Trello sync error: {str(e)}"
            }
    
    async def sync_with_notion(self, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync note with Notion via Zapier webhook"""
        try:
            if not self.config.is_service_configured("notion"):
                logger.warning("Notion webhook URL not configured")
                return {
                    "success": False,
                    "message": "Notion integration not configured. Please update zapier_config.py"
                }
            
            # Prepare data for Notion
            notion_data = {
                "title": note_data.get("title", "Voice Assistant Note"),
                "content": note_data.get("content", ""),
                "category": note_data.get("category", "general"),
                "tags": note_data.get("tags", []),
                "created_date": note_data.get("created_at", datetime.now().isoformat()),
                "database_name": "Voice Assistant Notes"
            }
            
            # Send to Zapier webhook
            response = requests.post(
                self.config.get_webhook_url("notion"),
                json=notion_data,
                headers={'Content-Type': 'application/json'},
                timeout=self.config.request_timeout
            )
            
            if response.status_code == 200:
                # Store Notion reference in Firestore
                await self.firestore.update_note_metadata(
                    note_data.get("id"),
                    {"notion_synced": True, "notion_sync_date": datetime.now().isoformat()}
                )
                
                logger.info(f"Note synced with Notion: {note_data.get('title')}")
                return {
                    "success": True,
                    "message": "Note synced with Notion successfully",
                    "notion_response": response.json() if response.content else None
                }
            else:
                logger.error(f"Notion sync failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Notion sync failed: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error syncing with Notion: {e}")
            return {
                "success": False,
                "message": f"Notion sync error: {str(e)}"
            }
    
    async def create_calendar_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create calendar event via Zapier webhook"""
        try:
            if not self.config.is_service_configured("google_calendar"):
                logger.warning("Google Calendar webhook URL not configured")
                return {
                    "success": False,
                    "message": "Google Calendar integration not configured. Please update zapier_config.py"
                }
            
            # Prepare data for Google Calendar
            calendar_data = {
                "summary": event_data.get("title", "Voice Assistant Event"),
                "description": event_data.get("description", ""),
                "start_time": event_data.get("start_time", ""),
                "end_time": event_data.get("end_time", ""),
                "timezone": event_data.get("timezone", "UTC"),
                "attendees": event_data.get("attendees", []),
                "location": event_data.get("location", ""),
                "calendar_id": "primary"
            }
            
            # Send to Zapier webhook
            response = requests.post(
                self.config.get_webhook_url("google_calendar"),
                json=calendar_data,
                headers={'Content-Type': 'application/json'},
                timeout=self.config.request_timeout
            )
            
            if response.status_code == 200:
                # Store calendar reference in Firestore
                event_id = await self.firestore.create_calendar_event({
                    **event_data,
                    "google_calendar_synced": True,
                    "google_calendar_sync_date": datetime.now().isoformat()
                })
                
                logger.info(f"Calendar event created: {event_data.get('title')}")
                return {
                    "success": True,
                    "message": "Calendar event created successfully",
                    "event_id": event_id,
                    "calendar_response": response.json() if response.content else None
                }
            else:
                logger.error(f"Calendar event creation failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Calendar event creation failed: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return {
                "success": False,
                "message": f"Calendar event creation error: {str(e)}"
            }
    
    async def send_slack_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification to Slack via Zapier webhook"""
        try:
            if not self.config.is_service_configured("slack"):
                logger.warning("Slack webhook URL not configured")
                return {
                    "success": False,
                    "message": "Slack integration not configured. Please update zapier_config.py"
                }
            
            # Prepare data for Slack
            slack_data = {
                "text": notification_data.get("message", "Voice Assistant Notification"),
                "channel": notification_data.get("channel", "#general"),
                "username": "Voice Assistant",
                "icon_emoji": ":robot_face:",
                "attachments": [
                    {
                        "color": notification_data.get("color", "good"),
                        "title": notification_data.get("title", "Notification"),
                        "text": notification_data.get("details", ""),
                        "timestamp": int(datetime.now().timestamp())
                    }
                ]
            }
            
            # Send to Zapier webhook
            response = requests.post(
                self.config.get_webhook_url("slack"),
                json=slack_data,
                headers={'Content-Type': 'application/json'},
                timeout=self.config.request_timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Slack notification sent: {notification_data.get('title')}")
                return {
                    "success": True,
                    "message": "Slack notification sent successfully"
                }
            else:
                logger.error(f"Slack notification failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "message": f"Slack notification failed: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return {
                "success": False,
                "message": f"Slack notification error: {str(e)}"
            }
    
    async def sync_with_google_calendar(self, reminder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync reminder with Google Calendar via Zapier webhook"""
        try:
            # Convert reminder to calendar event format
            event_data = {
                "title": f"Reminder: {reminder_data.get('message', 'Voice Assistant Reminder')}",
                "description": reminder_data.get('description', ''),
                "start_time": reminder_data.get('reminder_time', ''),
                "end_time": reminder_data.get('reminder_time', ''),  # Same as start for reminders
                "timezone": "UTC"
            }
            
            return await self.create_calendar_event(event_data)
            
        except Exception as e:
            logger.error(f"Error syncing reminder with Google Calendar: {e}")
            return {
                "success": False,
                "message": f"Google Calendar sync error: {str(e)}"
            }
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all integrations"""
        try:
            configured_services = self.config.get_configured_services()
            
            status = {
                "trello": {
                    "configured": self.config.is_service_configured("trello"),
                    "webhook_url": self.config.get_webhook_url("trello")[:50] + "..." if self.config.is_service_configured("trello") else None
                },
                "notion": {
                    "configured": self.config.is_service_configured("notion"),
                    "webhook_url": self.config.get_webhook_url("notion")[:50] + "..." if self.config.is_service_configured("notion") else None
                },
                "google_calendar": {
                    "configured": self.config.is_service_configured("google_calendar"),
                    "webhook_url": self.config.get_webhook_url("google_calendar")[:50] + "..." if self.config.is_service_configured("google_calendar") else None
                },
                "slack": {
                    "configured": self.config.is_service_configured("slack"),
                    "webhook_url": self.config.get_webhook_url("slack")[:50] + "..." if self.config.is_service_configured("slack") else None
                }
            }
            
            return {
                "success": True,
                "integrations": status,
                "configured_count": len(configured_services),
                "config_file": "config/zapier_config.py"
            }
            
        except Exception as e:
            logger.error(f"Error getting integration status: {e}")
            return {
                "success": False,
                "message": f"Error getting integration status: {str(e)}"
            }