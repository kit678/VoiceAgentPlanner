#!/usr/bin/env python3
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger
from firebase.firestore_service import FirestoreService

from functions.google_workspace_functions import GoogleWorkspaceFunctions

class ReminderFunctions:
    """Reminder and timer management functions for the voice assistant"""
    
    def __init__(self):
        self.firestore = FirestoreService()

        self.google_workspace = GoogleWorkspaceFunctions()  # Google Calendar integration
        logger.info("ReminderFunctions initialized with Google Calendar integration")
    
    async def set_reminder(self, reminder_text: str, reminder_time: str) -> Dict[str, Any]:
        """Set a reminder for a specific time"""
        try:
            # Parse reminder time
            parsed_time = self._parse_time(reminder_time)
            if not parsed_time:
                return {
                    "success": False,
                    "message": f"Could not parse reminder time: {reminder_time}. Please use formats like '2:30 PM', 'in 30 minutes', or 'tomorrow at 9 AM'."
                }
            
            # Create reminder data
            reminder_data = {
                "text": reminder_text,
                "reminder_time": parsed_time.isoformat(),
                "status": "active",
                "type": "reminder",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Save to Firestore
            reminder_id = await self.firestore.create_reminder(reminder_data)
            reminder_data["id"] = reminder_id
            
            # Create calendar event via Google Calendar (primary integration)
            calendar_event = {
                "summary": f"Reminder: {reminder_text}",
                "start_time": parsed_time.isoformat(),
                "end_time": (parsed_time + timedelta(minutes=15)).isoformat(),
                "description": f"Voice Assistant Reminder: {reminder_text}"
            }
            calendar_result = await self.google_workspace.create_calendar_event(
                summary=calendar_event["summary"],
                start_time=calendar_event["start_time"],
                end_time=calendar_event["end_time"],
                description=calendar_event["description"]
            )
            
            logger.info(f"Created reminder: {reminder_text} (ID: {reminder_id})")
            response = {
                "success": True,
                "message": f"Reminder set for {parsed_time.strftime('%Y-%m-%d at %I:%M %p')}: {reminder_text}",
                "reminder_id": reminder_id,
                "reminder_data": reminder_data
            }
            
            # Add Google Calendar sync status to response
            if calendar_result.get("success"):
                response["message"] += " and added to Google Calendar"
                response["google_calendar_synced"] = True
                response["google_event_id"] = calendar_result.get("event_id")
                
                # Store Google Calendar event ID in reminder data
                await self.firestore.update_reminder(reminder_id, {"google_event_id": calendar_result.get("event_id")})
            else:
                response["google_sync_warning"] = calendar_result.get("message")
                # Google Calendar sync failed - no fallback available
            
            return response
            
        except Exception as e:
            logger.error(f"Error setting reminder: {e}")
            return {
                "success": False,
                "message": "Failed to set reminder. Please try again."
            }
    
    async def start_timer(self, duration: str, timer_name: str = "Timer") -> Dict[str, Any]:
        """Start a countdown timer"""
        try:
            # Parse duration
            duration_seconds = self._parse_duration(duration)
            if not duration_seconds:
                return {
                    "success": False,
                    "message": f"Could not parse timer duration: {duration}. Please use formats like '5 minutes', '30 seconds', or '1 hour'."
                }
            
            # Calculate end time
            end_time = datetime.now() + timedelta(seconds=duration_seconds)
            
            # Create timer data
            timer_data = {
                "name": timer_name,
                "duration_seconds": duration_seconds,
                "end_time": end_time.isoformat(),
                "status": "running",
                "type": "timer",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Save to Firestore
            timer_id = await self.firestore.create_timer(timer_data)
            
            logger.info(f"Started timer: {timer_name} for {duration} (ID: {timer_id})")
            return {
                "success": True,
                "message": f"Timer '{timer_name}' started for {self._format_duration(duration_seconds)}",
                "timer_id": timer_id,
                "timer_data": timer_data
            }
            
        except Exception as e:
            logger.error(f"Error starting timer: {e}")
            return {
                "success": False,
                "message": "Failed to start timer. Please try again."
            }
    
    async def list_reminders(self, status: str = "active") -> Dict[str, Any]:
        """List active reminders"""
        try:
            # Get reminders from Firestore
            filters = {"status": status, "type": "reminder"}
            reminders = await self.firestore.get_reminders(filters)
            
            if not reminders:
                return {
                    "success": True,
                    "message": f"No {status} reminders found.",
                    "reminders": []
                }
            
            # Format reminder list for response
            reminder_list = []
            for reminder in reminders:
                reminder_time = datetime.fromisoformat(reminder["reminder_time"]).strftime("%Y-%m-%d at %I:%M %p")
                reminder_list.append(f"• {reminder['text']} ({reminder_time})")
            
            message = f"Found {len(reminders)} {status} reminder(s):\n" + "\n".join(reminder_list)
            
            logger.info(f"Listed {len(reminders)} reminders")
            return {
                "success": True,
                "message": message,
                "reminders": reminders
            }
            
        except Exception as e:
            logger.error(f"Error listing reminders: {e}")
            return {
                "success": False,
                "message": "Failed to retrieve reminders. Please try again."
            }
    
    async def list_timers(self, status: str = "running") -> Dict[str, Any]:
        """List active timers"""
        try:
            # Get timers from Firestore
            filters = {"status": status, "type": "timer"}
            timers = await self.firestore.get_timers(filters)
            
            if not timers:
                return {
                    "success": True,
                    "message": f"No {status} timers found.",
                    "timers": []
                }
            
            # Format timer list for response
            timer_list = []
            now = datetime.now()
            for timer in timers:
                end_time = datetime.fromisoformat(timer["end_time"])
                remaining = max(0, int((end_time - now).total_seconds()))
                timer_list.append(f"• {timer['name']} ({self._format_duration(remaining)} remaining)")
            
            message = f"Found {len(timers)} {status} timer(s):\n" + "\n".join(timer_list)
            
            logger.info(f"Listed {len(timers)} timers")
            return {
                "success": True,
                "message": message,
                "timers": timers
            }
            
        except Exception as e:
            logger.error(f"Error listing timers: {e}")
            return {
                "success": False,
                "message": "Failed to retrieve timers. Please try again."
            }
    
    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """Parse various time formats and relative terms"""
        time_str = time_str.lower().strip()
        now = datetime.now()
        
        # Handle "in X minutes/hours" format
        if "in " in time_str:
            try:
                parts = time_str.split()
                if len(parts) >= 3:
                    amount = int(parts[1])
                    unit = parts[2]
                    
                    if "minute" in unit:
                        return now + timedelta(minutes=amount)
                    elif "hour" in unit:
                        return now + timedelta(hours=amount)
                    elif "day" in unit:
                        return now + timedelta(days=amount)
            except (ValueError, IndexError):
                pass
        
        # Handle "tomorrow at X" format
        if "tomorrow at" in time_str:
            time_part = time_str.replace("tomorrow at", "").strip()
            parsed_time = self._parse_time_of_day(time_part)
            if parsed_time:
                tomorrow = now + timedelta(days=1)
                return tomorrow.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
        
        # Handle time of day formats
        parsed_time = self._parse_time_of_day(time_str)
        if parsed_time:
            # If the time has already passed today, schedule for tomorrow
            scheduled = now.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
            if scheduled <= now:
                scheduled += timedelta(days=1)
            return scheduled
        
        return None
    
    def _parse_time_of_day(self, time_str: str) -> Optional[datetime]:
        """Parse time of day formats like '2:30 PM', '14:30', etc."""
        time_formats = [
            "%I:%M %p",  # 2:30 PM
            "%I %p",     # 2 PM
            "%H:%M",     # 14:30
            "%H",        # 14
        ]
        
        for fmt in time_formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse duration strings and return seconds"""
        duration_str = duration_str.lower().strip()
        
        try:
            parts = duration_str.split()
            if len(parts) >= 2:
                amount = int(parts[0])
                unit = parts[1]
                
                if "second" in unit:
                    return amount
                elif "minute" in unit:
                    return amount * 60
                elif "hour" in unit:
                    return amount * 3600
                elif "day" in unit:
                    return amount * 86400
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human-readable string"""
        if seconds < 60:
            return f"{seconds} second{'s' if seconds != 1 else ''}"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes > 0:
                return f"{hours} hour{'s' if hours != 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"
            else:
                return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            if hours > 0:
                return f"{days} day{'s' if days != 1 else ''} and {hours} hour{'s' if hours != 1 else ''}"
            else:
                return f"{days} day{'s' if days != 1 else ''}"