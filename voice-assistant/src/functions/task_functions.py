#!/usr/bin/env python3
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger
from firebase.firestore_service import FirestoreService

from functions.google_workspace_functions import GoogleWorkspaceFunctions

class TaskFunctions:
    """Task management functions for the voice assistant"""
    
    def __init__(self):
        self.firestore = FirestoreService()

        self.google_workspace = GoogleWorkspaceFunctions()  # Google Workspace integration
        logger.info("TaskFunctions initialized with Google Workspace integration")
    
    async def create_task(self, task_name: str, due_date: str, priority: str = "medium") -> Dict[str, Any]:
        """Create a new task"""
        try:
            # Parse due date
            parsed_date = self._parse_date(due_date)
            if not parsed_date:
                return {
                    "success": False,
                    "message": f"Could not parse due date: {due_date}. Please use YYYY-MM-DD format or terms like 'tomorrow', 'next week'."
                }
            
            # Create task data
            task_data = {
                "name": task_name,
                "due_date": parsed_date.isoformat(),
                "priority": priority,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Save to Firestore
            task_id = await self.firestore.create_task(task_data)
            task_data["id"] = task_id
            
            # Sync with Google Tasks (primary integration)
            google_result = await self.google_workspace.create_google_task(
                task_name=task_name,
                due_date=parsed_date.isoformat(),
                priority=priority
            )
            
            logger.info(f"Created task: {task_name} (ID: {task_id})")
            response = {
                "success": True,
                "message": f"Task '{task_name}' created successfully for {parsed_date.strftime('%Y-%m-%d')}",
                "task_id": task_id,
                "task_data": task_data
            }
            
            # Add Google Tasks sync status to response
            if google_result.get("success"):
                response["message"] += " and synced with Google Tasks"
                response["google_tasks_synced"] = True
                response["google_task_id"] = google_result.get("task_id")
            else:
                response["google_sync_warning"] = google_result.get("message")
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return {
                "success": False,
                "message": "Failed to create task. Please try again."
            }
    
    async def list_tasks(self, status: str = "all", due_date: Optional[str] = None) -> Dict[str, Any]:
        """List tasks with optional filtering by status or due date"""
        try:
            # Build filters
            filters = {}
            if status != "all":
                filters["status"] = status
            
            # Parse due date if provided
            if due_date:
                parsed_date = self._parse_date(due_date)
                if not parsed_date:
                    return {
                        "success": False,
                        "message": f"Could not parse due date: {due_date}. Please use YYYY-MM-DD format or terms like 'tomorrow', 'next week'."
                    }
                # We'll filter tasks after fetching since we need to compare dates
            
            # Get tasks from Firestore
            tasks = await self.firestore.get_tasks(filters)
            
            # Filter by due date if provided
            if due_date and parsed_date and tasks:
                filtered_tasks = []
                for task in tasks:
                    task_due_date = datetime.fromisoformat(task["due_date"]).date()
                    if task_due_date == parsed_date.date():
                        filtered_tasks.append(task)
                tasks = filtered_tasks
            
            if not tasks:
                return {
                    "success": True,
                    "message": "No tasks found matching your criteria.",
                    "tasks": []
                }
            
            # Format task list for response
            task_list = []
            for task in tasks:
                due_date_str = datetime.fromisoformat(task["due_date"]).strftime("%Y-%m-%d")
                task_list.append(f"• {task['name']} (Due: {due_date_str}, Priority: {task['priority']})")
            
            message = f"Found {len(tasks)} task(s):\n" + "\n".join(task_list)
            
            logger.info(f"Listed {len(tasks)} tasks")
            return {
                "success": True,
                "message": message,
                "tasks": tasks
            }
            
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return {
                "success": False,
                "message": "Failed to retrieve tasks. Please try again."
            }
    
    async def update_task_status(self, task_id: str, status: str) -> Dict[str, Any]:
        """Update task status"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            
            if status == "completed":
                update_data["completed_at"] = datetime.now().isoformat()
            
            await self.firestore.update_task(task_id, update_data)
            
            logger.info(f"Updated task {task_id} status to {status}")
            return {
                "success": True,
                "message": f"Task status updated to {status}"
            }
            
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return {
                "success": False,
                "message": "Failed to update task status. Please try again."
            }
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats and relative terms"""
        date_str = date_str.lower().strip()
        now = datetime.now()
        
        # Handle relative terms
        if date_str in ["today"]:
            return now.replace(hour=23, minute=59, second=59, microsecond=0)
        elif date_str in ["tomorrow"]:
            return (now + timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=0)
        elif date_str in ["next week", "1 week"]:
            return (now + timedelta(weeks=1)).replace(hour=23, minute=59, second=59, microsecond=0)
        elif date_str in ["next month", "1 month"]:
            return (now + timedelta(days=30)).replace(hour=23, minute=59, second=59, microsecond=0)
        
        # Handle "in X days" format
        if "in " in date_str and "day" in date_str:
            try:
                days = int(date_str.split()[1])
                return (now + timedelta(days=days)).replace(hour=23, minute=59, second=59, microsecond=0)
            except (ValueError, IndexError):
                pass
        
        # Handle standard date formats
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%d/%m/%Y",
            "%d-m-%Y"
        ]
        
        for fmt in date_formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                # Set time to end of day
                return parsed.replace(hour=23, minute=59, second=59, microsecond=0)
            except ValueError:
                continue
        
        return None