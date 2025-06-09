#!/usr/bin/env python3
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from loguru import logger
from firebase.firestore_service import FirestoreService

from functions.google_workspace_functions import GoogleWorkspaceFunctions

class GoalFunctions:
    """Goal management and tracking functions for the voice assistant"""
    
    def __init__(self):
        self.firestore = FirestoreService()

        self.google_workspace = GoogleWorkspaceFunctions()  # Google Workspace integration
        logger.info("GoalFunctions initialized with Google Workspace integration")
    
    async def create_goal(self, title: str, target_date: str, description: str = "", category: str = "personal") -> Dict[str, Any]:
        """Create a new goal"""
        try:
            # Parse target date
            parsed_date = self._parse_date(target_date)
            if not parsed_date:
                return {
                    "success": False,
                    "message": f"Could not parse target date: {target_date}. Please use YYYY-MM-DD format or terms like 'next month', 'end of year'."
                }
            
            # Create goal data
            goal_data = {
                "name": title,
                "description": description,
                "category": category,
                "target_date": parsed_date.isoformat(),
                "status": "active",
                "progress_percentage": 0,
                "milestones": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Save to Firestore
            goal_id = await self.firestore.create_goal(goal_data)
            goal_data["id"] = goal_id
            
            # Create Google Doc for goal tracking (primary integration)
            doc_content = f"""# Goal: {title}

**Category:** {category}
**Target Date:** {parsed_date.strftime('%Y-%m-%d')}
**Status:** Active
**Progress:** 0%

## Description
{description}

## Progress Updates
- Goal created on {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Milestones
(To be added as progress is made)

## Notes
(Add notes and reflections here)
"""
            
            google_result = await self.google_workspace.create_google_doc(
                title=f"Goal: {title}",
                content=doc_content
            )
            
            logger.info(f"Created goal: {title} (ID: {goal_id})")
            response = {
                "success": True,
                "message": f"Goal '{title}' created successfully with target date {parsed_date.strftime('%Y-%m-%d')}",
                "goal_id": goal_id,
                "goal_data": goal_data
            }
            
            # Add Google Docs sync status to response
            if google_result.get("success"):
                response["message"] += " and documented in Google Docs"
                response["google_docs_synced"] = True
                response["google_doc_id"] = google_result.get("doc_id")
                response["google_doc_url"] = google_result.get("doc_url")
                
                # Store Google Doc ID in goal data
                await self.firestore.update_goal(goal_id, {"google_doc_id": google_result.get("doc_id")})
            else:
                response["google_sync_warning"] = google_result.get("message")
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating goal: {e}")
            return {
                "success": False,
                "message": "Failed to create goal. Please try again."
            }
    
    async def update_goal_progress(self, goal_id: str, progress_percentage: int, notes: str = "") -> Dict[str, Any]:
        """Update goal progress"""
        try:
            # Validate progress percentage
            if not 0 <= progress_percentage <= 100:
                return {
                    "success": False,
                    "message": "Progress percentage must be between 0 and 100."
                }
            
            # Get goal data to check for Google Doc ID
            goal_data = await self.firestore.get_goal(goal_id)
            if not goal_data:
                return {
                    "success": False,
                    "message": "Goal not found."
                }
            
            # Create update data
            update_data = {
                "progress_percentage": progress_percentage,
                "updated_at": datetime.now().isoformat()
            }
            
            # Mark as completed if 100%
            if progress_percentage == 100:
                update_data["status"] = "completed"
                update_data["completed_at"] = datetime.now().isoformat()
            
            # Add progress entry
            progress_entry = {
                "percentage": progress_percentage,
                "notes": notes,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update in Firestore
            await self.firestore.update_goal_progress(goal_id, update_data, progress_entry)
            
            # Update Google Doc if available
            google_doc_id = goal_data.get("google_doc_id")
            if google_doc_id:
                progress_update = f"\n- {datetime.now().strftime('%Y-%m-%d %H:%M')}: Progress updated to {progress_percentage}%"
                if notes:
                    progress_update += f" - {notes}"
                
                # Update the Progress Updates section in the Google Doc
                google_result = await self.google_workspace.update_google_doc(
                    doc_id=google_doc_id,
                    content=progress_update,
                    append_to_section="Progress Updates"
                )
                
                if not google_result.get("success"):
                    logger.warning(f"Failed to update Google Doc for goal {goal_id}: {google_result.get('message')}")
            
            status_msg = "completed" if progress_percentage == 100 else f"updated to {progress_percentage}%"
            logger.info(f"Updated goal {goal_id} progress to {progress_percentage}%")
            
            response = {
                "success": True,
                "message": f"Goal progress {status_msg}"
            }
            
            if google_doc_id:
                response["message"] += " and documented in Google Docs"
            
            return response
            
        except Exception as e:
            logger.error(f"Error updating goal progress: {e}")
            return {
                "success": False,
                "message": "Failed to update goal progress. Please try again."
            }
    
    async def add_milestone(self, goal_id: str, milestone_name: str, target_date: str, description: str = "") -> Dict[str, Any]:
        """Add a milestone to a goal"""
        try:
            # Parse target date
            parsed_date = self._parse_date(target_date)
            if not parsed_date:
                return {
                    "success": False,
                    "message": f"Could not parse milestone date: {target_date}."
                }
            
            # Create milestone data
            milestone = {
                "name": milestone_name,
                "description": description,
                "target_date": parsed_date.isoformat(),
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            # Add to goal
            await self.firestore.add_goal_milestone(goal_id, milestone)
            
            logger.info(f"Added milestone to goal {goal_id}: {milestone_name}")
            return {
                "success": True,
                "message": f"Milestone '{milestone_name}' added to goal"
            }
            
        except Exception as e:
            logger.error(f"Error adding milestone: {e}")
            return {
                "success": False,
                "message": "Failed to add milestone. Please try again."
            }
    
    async def list_goals(self, status: str = "active", category: Optional[str] = None) -> Dict[str, Any]:
        """List goals with optional filtering"""
        try:
            # Build filters
            filters = {"status": status}
            if category:
                filters["category"] = category
            
            # Get goals from Firestore
            goals = await self.firestore.get_goals(filters)
            
            if not goals:
                filter_desc = f"{status} goals"
                if category:
                    filter_desc += f" in category '{category}'"
                return {
                    "success": True,
                    "message": f"No {filter_desc} found.",
                    "goals": []
                }
            
            # Format goal list for response
            goal_list = []
            for goal in goals:
                target_date = datetime.fromisoformat(goal["target_date"]).strftime("%Y-%m-%d")
                progress = goal["progress_percentage"]
                goal_list.append(f"• {goal['name']} (Progress: {progress}%, Target: {target_date})")
            
            filter_desc = f"{status} goals"
            if category:
                filter_desc += f" in category '{category}'"
            message = f"Found {len(goals)} {filter_desc}:\n" + "\n".join(goal_list)
            
            logger.info(f"Listed {len(goals)} goals")
            return {
                "success": True,
                "message": message,
                "goals": goals
            }
            
        except Exception as e:
            logger.error(f"Error listing goals: {e}")
            return {
                "success": False,
                "message": "Failed to retrieve goals. Please try again."
            }
    
    async def get_goal_details(self, goal_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific goal"""
        try:
            goal = await self.firestore.get_goal(goal_id)
            
            if not goal:
                return {
                    "success": False,
                    "message": "Goal not found."
                }
            
            # Format goal details
            target_date = datetime.fromisoformat(goal["target_date"]).strftime("%Y-%m-%d")
            created_date = datetime.fromisoformat(goal["created_at"]).strftime("%Y-%m-%d")
            
            message = f"Goal Details:\n"
            message += f"• Name: {goal['name']}\n"
            message += f"• Description: {goal.get('description', 'No description')}\n"
            message += f"• Category: {goal['category']}\n"
            message += f"• Progress: {goal['progress_percentage']}%\n"
            message += f"• Status: {goal['status']}\n"
            message += f"• Target Date: {target_date}\n"
            message += f"• Created: {created_date}\n"
            
            # Add milestones if any
            milestones = goal.get('milestones', [])
            if milestones:
                message += f"• Milestones ({len(milestones)}):" + "\n"
                for milestone in milestones:
                    milestone_date = datetime.fromisoformat(milestone["target_date"]).strftime("%Y-%m-%d")
                    status_icon = "✅" if milestone["status"] == "completed" else "⏳"
                    message += f"  {status_icon} {milestone['name']} (Target: {milestone_date})\n"
            
            logger.info(f"Retrieved goal details for {goal_id}")
            return {
                "success": True,
                "message": message,
                "goal": goal
            }
            
        except Exception as e:
            logger.error(f"Error getting goal details: {e}")
            return {
                "success": False,
                "message": "Failed to retrieve goal details. Please try again."
            }
    
    async def get_goal_summary(self) -> Dict[str, Any]:
        """Get a summary of all goals"""
        try:
            summary = await self.firestore.get_goal_summary()
            
            message = f"Goal Summary:\n"
            message += f"• Active goals: {summary.get('active_goals', 0)}\n"
            message += f"• Completed goals: {summary.get('completed_goals', 0)}\n"
            message += f"• Average progress: {summary.get('average_progress', 0):.1f}%\n"
            message += f"• Goals due this month: {summary.get('due_this_month', 0)}\n"
            message += f"• Overdue goals: {summary.get('overdue_goals', 0)}"
            
            logger.info("Retrieved goal summary")
            return {
                "success": True,
                "message": message,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error getting goal summary: {e}")
            return {
                "success": False,
                "message": "Failed to retrieve goal summary. Please try again."
            }
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats and relative terms"""
        date_str = date_str.lower().strip()
        now = datetime.now()
        
        # Handle relative terms
        if date_str in ["next week", "1 week"]:
            return now + timedelta(weeks=1)
        elif date_str in ["next month", "1 month"]:
            return now + timedelta(days=30)
        elif date_str in ["next year", "1 year"]:
            return now + timedelta(days=365)
        elif date_str in ["end of month"]:
            # Get last day of current month
            if now.month == 12:
                return datetime(now.year + 1, 1, 1) - timedelta(days=1)
            else:
                return datetime(now.year, now.month + 1, 1) - timedelta(days=1)
        elif date_str in ["end of year"]:
            return datetime(now.year, 12, 31)
        
        # Handle "in X months/years" format
        if "in " in date_str:
            try:
                parts = date_str.split()
                if len(parts) >= 3:
                    amount = int(parts[1])
                    unit = parts[2]
                    
                    if "month" in unit:
                        return now + timedelta(days=amount * 30)
                    elif "year" in unit:
                        return now + timedelta(days=amount * 365)
                    elif "week" in unit:
                        return now + timedelta(weeks=amount)
            except (ValueError, IndexError):
                pass
        
        # Handle standard date formats
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%d/%m/%Y",
            "%d-%m-%Y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None