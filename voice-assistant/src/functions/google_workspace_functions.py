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
# Add missing import for MediaIoBaseDownload
from googleapiclient.http import MediaIoBaseDownload


class GoogleWorkspaceFunctions:
    """Google Workspace API integration functions for Tasks, Calendar, Drive, and Docs"""

    def __init__(self):
        self.oauth_manager = GoogleOAuthManager()
        self.firestore = FirestoreService()
        self._services: Dict[str, Any] = {}
        logger.info("GoogleWorkspaceFunctions initialized")

    # ---------------------------------------------------------------------
    #  LOW-LEVEL SERVICE HELPER
    # ---------------------------------------------------------------------
    async def _get_service(self, service_name: str):
        """
        Lazily fetch and cache an authenticated Google API service client.

        Args:
            service_name: 'tasks' | 'calendar' | 'drive' | 'docs'
        """
        logger.info(f"=== GET SERVICE: {service_name} ===")

        if service_name not in self._services:
            try:
                logger.info("Checking OAuth authentication status…")
                is_authenticated = await self.oauth_manager.is_authenticated()
                if not is_authenticated:
                    raise RuntimeError(
                        "User is not authenticated with Google OAuth"
                    )

                fetcher = {
                    "tasks": self.oauth_manager.get_tasks_service,
                    "calendar": self.oauth_manager.get_calendar_service,
                    "drive": self.oauth_manager.get_drive_service,
                    "docs": self.oauth_manager.get_docs_service,
                }.get(service_name)

                if fetcher is None:
                    raise ValueError(f"Unknown service: {service_name}")

                self._services[service_name] = await fetcher()
                logger.info(f"✅  {service_name} service initialised")

            except Exception as exc:
                logger.error(f"❌ Failed to init {service_name}: {exc!r}")
                raise
        else:
            logger.info(f"Using cached {service_name} service")

        return self._services[service_name]

    # =====================================================================
    #  GOOGLE TASKS
    # =====================================================================
    async def create_google_task(
        self,
        task_name: str,
        due_date: Optional[str] = None,
        priority: str = "medium",
        list_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a task in Google Tasks."""
        logger.info(f"=== CREATE GOOGLE TASK: {task_name} ===")
        service = await self._get_service("tasks")

        # Resolve list ID
        if not list_id:
            task_lists = service.tasklists().list().execute()
            list_id = task_lists["items"][0]["id"] if task_lists.get("items") else None
            if not list_id:
                return {
                    "success": False,
                    "message": "No task lists found in Google Tasks",
                }

        body: Dict[str, Any] = {
            "title": task_name,
            "notes": f"Priority: {priority}\nCreated by Voice Assistant",
        }
        if due_date:
            try:
                due_dt = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
                body["due"] = due_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                logger.warning("Invalid due-date format supplied; skipping")

        result = service.tasks().insert(tasklist=list_id, body=body).execute()

        # Persist locally
        doc_ref = await self.firestore.add_document(
            "tasks",
            {
                "google_task_id": result["id"],
                "google_list_id": list_id,
                "title": task_name,
                "priority": priority,
                "due_date": due_date,
                "status": "needsAction",
                "created_at": datetime.now().isoformat(),
                "synced_with_google": True,
            },
        )

        return {
            "success": True,
            "message": f"Task '{task_name}' created successfully",
            "task_id": result["id"],
            "local_id": doc_ref.id,
            "task_data": result,
        }

    async def list_google_tasks(
        self,
        list_id: Optional[str] = None,
        status_filter: str = "needsAction",
        max_results: int = 20,
    ) -> Dict[str, Any]:
        """List tasks in the requested Google Tasks list."""
        logger.info("=== LIST GOOGLE TASKS ===")
        service = await self._get_service("tasks")

        if not list_id:
            task_lists = service.tasklists().list().execute()
            if not task_lists.get("items"):
                return {
                    "success": False,
                    "message": "No task lists found for user.",
                }
            list_id = task_lists["items"][0]["id"]

        show_completed = None
        if status_filter == "completed":
            show_completed = True
        elif status_filter == "needsAction":
            show_completed = False

        tasks = (
            service.tasks()
            .list(
                tasklist=list_id,
                showCompleted=show_completed,
                showHidden=True,
                maxResults=max_results,
            )
            .execute()
            .get("items", [])
        )

        return {
            "success": True,
            "tasks": tasks,
            "message": f"Retrieved {len(tasks)} tasks",
        }

    async def update_google_task(
        self, task_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a Google Task."""
        service = await self._get_service("tasks")
        current = service.tasks().get(tasklist="@default", task=task_id).execute()

        if "title" in updates:
            current["title"] = updates["title"]
        if "notes" in updates:
            current["notes"] = updates["notes"]
        if "due_date" in updates and updates["due_date"]:
            try:
                due_dt = datetime.fromisoformat(updates["due_date"].replace("Z", "+00:00"))
                current["due"] = due_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                logger.warning("Invalid due-date while updating task")

        if "status" in updates:
            current["status"] = updates["status"]

        result = (
            service.tasks()
            .update(tasklist="@default", task=task_id, body=current)
            .execute()
        )

        await self.firestore.update_document_by_field(
            "tasks",
            "google_task_id",
            task_id,
            {**updates, "updated_at": datetime.now().isoformat(), "synced_with_google": True},
        )

        return {"success": True, "message": "Task updated", "task_data": result}

    async def complete_google_task(self, task_id: str) -> Dict[str, Any]:
        return await self.update_google_task(task_id, {"status": "completed"})

    async def delete_google_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a Google Task."""
        service = await self._get_service("tasks")
        service.tasks().delete(tasklist="@default", task=task_id).execute()
        await self.firestore.delete_document_by_field("tasks", "google_task_id", task_id)
        return {"success": True, "message": "Task deleted"}

    # =====================================================================
    #  GOOGLE CALENDAR
    # =====================================================================
    async def create_calendar_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: str = "",
        location: str = "",
    ) -> Dict[str, Any]:
        """
        Original helper kept for compatibility (summary/start_time/end_time signature).
        """
        service = await self._get_service("calendar")
        body = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": {"dateTime": start_time, "timeZone": "UTC"},
            "end": {"dateTime": end_time, "timeZone": "UTC"},
        }
        event = service.events().insert(calendarId="primary", body=body).execute()
        return {
            "success": True,
            "message": f"Event '{summary}' created",
            "event_id": event["id"],
            "event_link": event.get("htmlLink"),
            "event_data": event,
        }



    async def list_google_calendar_events(
        self, time_min: str, time_max: str, max_results: int = 10
    ) -> Dict[str, Any]:
        """
        List events between `time_min` and `time_max` (ISO 8601 or yyyy-mm-dd)
        """
        logger.info("=== LIST GOOGLE CALENDAR EVENTS ===")
        service = await self._get_service("calendar")

        # Best-effort parsing: accept full ISO or just a date.
        try:
            t_min = datetime.fromisoformat(time_min.replace("Z", "+00:00"))
            t_max = datetime.fromisoformat(time_max.replace("Z", "+00:00"))
        except ValueError:
            t_min = datetime.strptime(time_min, "%Y-%m-%d")
            t_max = datetime.strptime(time_max, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )

        events = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=t_min.isoformat() + "Z",
                timeMax=t_max.isoformat() + "Z",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
            .get("items", [])
        )

        formatted = [
            {
                "summary": ev.get("summary"),
                "start": ev["start"].get("dateTime", ev["start"].get("date")),
                "end": ev["end"].get("dateTime", ev["end"].get("date")),
                "location": ev.get("location"),
                "description": ev.get("description"),
            }
            for ev in events
        ]

        return {
            "success": True,
            "message": f"Found {len(formatted)} events",
            "events": formatted,
        }

    async def update_google_calendar_event(
        self, event_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a Google Calendar event."""
        service = await self._get_service("calendar")
        current = service.events().get(calendarId="primary", eventId=event_id).execute()

        if "title" in updates:
            current["summary"] = updates["title"]
        if "description" in updates:
            current["description"] = updates["description"]
        if "start_time" in updates:
            current["start"]["dateTime"] = updates["start_time"]
        if "end_time" in updates:
            current["end"]["dateTime"] = updates["end_time"]

        result = (
            service.events()
            .update(calendarId="primary", eventId=event_id, body=current)
            .execute()
        )

        await self.firestore.update_document_by_field(
            "calendar_events",
            "google_event_id",
            event_id,
            {
                **updates,
                "updated_at": datetime.now().isoformat(),
                "synced_with_google": True,
            },
        )

        return {"success": True, "message": "Event updated", "event_data": result}

    async def delete_google_calendar_event(self, event_id: str) -> Dict[str, Any]:
        """Delete a Google Calendar event."""
        service = await self._get_service("calendar")
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        await self.firestore.delete_document_by_field(
            "calendar_events", "google_event_id", event_id
        )
        return {"success": True, "message": "Event deleted"}

    # =====================================================================
    #  GOOGLE DRIVE
    # =====================================================================
    async def upload_to_google_drive(
        self, file_path: str, folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a local file to Google Drive."""
        service = await self._get_service("drive")

        if not os.path.exists(file_path):
            return {"success": False, "message": f"File not found: {file_path}"}

        file_name = os.path.basename(file_path)
        metadata: Dict[str, Any] = {"name": file_name}
        if folder_id:
            metadata["parents"] = [folder_id]

        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(file_path)
        result = (
            service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id,name,size,mimeType,createdTime",
            )
            .execute()
        )

        doc_ref = await self.firestore.add_document(
            "drive_files",
            {
                "google_file_id": result["id"],
                "name": result["name"],
                "size": result.get("size"),
                "mime_type": result.get("mimeType"),
                "folder_id": folder_id,
                "local_path": file_path,
                "uploaded_at": datetime.now().isoformat(),
                "synced_with_google": True,
            },
        )

        return {
            "success": True,
            "message": f"File '{file_name}' uploaded",
            "file_id": result["id"],
            "local_id": doc_ref.id,
            "file_data": result,
        }

    async def list_google_drive_files(
        self, folder_id: Optional[str] = None, file_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """List files in Google Drive (optionally filtered)."""
        service = await self._get_service("drive")

        query_parts: List[str] = []
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        if file_type:
            query_parts.append(f"mimeType='{file_type}'")

        query = " and ".join(query_parts) if query_parts else None

        files = (
            service.files()
            .list(
                q=query,
                fields="files(id,name,size,mimeType,createdTime,modifiedTime)",
                orderBy="modifiedTime desc",
            )
            .execute()
            .get("files", [])
        )

        return {
            "success": True,
            "message": f"Retrieved {len(files)} files",
            "files": files,
        }

    async def create_google_drive_folder(
        self, folder_name: str, parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a folder in Google Drive."""
        service = await self._get_service("drive")
        metadata: Dict[str, Any] = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        result = (
            service.files()
            .create(body=metadata, fields="id,name,createdTime")
            .execute()
        )

        doc_ref = await self.firestore.add_document(
            "drive_folders",
            {
                "google_folder_id": result["id"],
                "name": folder_name,
                "parent_id": parent_id,
                "created_at": datetime.now().isoformat(),
                "synced_with_google": True,
            },
        )

        return {
            "success": True,
            "message": f"Folder '{folder_name}' created",
            "folder_id": result["id"],
            "local_id": doc_ref.id,
            "folder_data": result,
        }

    # =====================================================================
    #  GOOGLE DOCS
    # =====================================================================
    async def create_google_doc(
        self, title: str, content: str = ""
    ) -> Dict[str, Any]:
        """Create a new Google Doc and (optionally) write its initial content."""
        drive = await self._get_service("drive")
        doc_meta = {"name": title, "mimeType": "application/vnd.google-apps.document"}
        doc = drive.files().create(body=doc_meta).execute()
        doc_id = doc["id"]

        if content:
            docs = await self._get_service("docs")
            docs.documents().batchUpdate(
                documentId=doc_id,
                body={
                    "requests": [
                        {
                            "insertText": {
                                "location": {"index": 1},
                                "text": content,
                            }
                        }
                    ]
                },
            ).execute()

        doc_ref = await self.firestore.add_document(
            "google_docs",
            {
                "google_doc_id": doc_id,
                "title": title,
                "content_preview": content[:200],
                "created_at": datetime.now().isoformat(),
                "synced_with_google": True,
            },
        )

        return {
            "success": True,
            "message": f"Document '{title}' created",
            "doc_id": doc_id,
            "local_id": doc_ref.id,
            "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit",
        }

    async def update_google_doc(
        self, doc_id: str, content: str
    ) -> Dict[str, Any]:
        """Append text to an existing Google Doc."""
        docs = await self._get_service("docs")
        doc = docs.documents().get(documentId=doc_id).execute()

        end_index = max(
            (el.get("endIndex", 1) for el in doc.get("body", {}).get("content", [])), default=1
        )

        docs.documents().batchUpdate(
            documentId=doc_id,
            body={
                "requests": [
                    {
                        "insertText": {
                            "location": {"index": end_index - 1},
                            "text": f"\n\n{content}",
                        }
                    }
                ]
            },
        ).execute()

        await self.firestore.update_document_by_field(
            "google_docs",
            "google_doc_id",
            doc_id,
            {
                "content_preview": content[:200],
                "updated_at": datetime.now().isoformat(),
                "synced_with_google": True,
            },
        )

        return {
            "success": True,
            "message": "Document updated",
            "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit",
        }

    async def read_google_doc(self, doc_id: str) -> Dict[str, Any]:
        """Read and return plain-text content of a Google Doc."""
        docs = await self._get_service("docs")
        doc = docs.documents().get(documentId=doc_id).execute()

        text_chunks: List[str] = []
        for el in doc.get("body", {}).get("content", []):
            for elem in el.get("paragraph", {}).get("elements", []):
                if "textRun" in elem:
                    text_chunks.append(elem["textRun"].get("content", ""))

        return {
            "success": True,
            "title": doc.get("title", "Untitled"),
            "content": "".join(text_chunks).strip(),
            "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit",
        }
