import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger

class TimerFunctions:
    """Timer and countdown functions for the voice assistant"""
    
    def __init__(self):
        self.active_timers = {}
        logger.info("TimerFunctions initialized")
    
    async def set_timer(self, duration: str, label: str = "Timer") -> Dict[str, Any]:
        """Set a timer for a specified duration"""
        try:
            # Parse duration (e.g., "5 minutes", "30 seconds", "1 hour")
            seconds = self._parse_duration(duration)
            if seconds is None:
                return {
                    "success": False,
                    "message": f"Could not parse duration: {duration}. Please use formats like '5 minutes', '30 seconds', or '1 hour'."
                }
            
            timer_id = f"{label}_{datetime.now().timestamp()}"
            end_time = datetime.now() + timedelta(seconds=seconds)
            
            self.active_timers[timer_id] = {
                "label": label,
                "duration": seconds,
                "end_time": end_time,
                "started_at": datetime.now()
            }
            
            logger.info(f"Timer set: {label} for {duration} ({seconds} seconds)")
            return {
                "success": True,
                "message": f"Timer '{label}' set for {duration}",
                "timer_id": timer_id,
                "duration_seconds": seconds,
                "end_time": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error setting timer: {e}")
            return {
                "success": False,
                "message": f"Failed to set timer: {str(e)}"
            }
    
    async def start_timer(self, duration_minutes: float, description: str = "Timer") -> Dict[str, Any]:
        """Start a timer for a specified duration in minutes"""
        try:
            # Convert minutes to seconds
            seconds = duration_minutes * 60
            
            timer_id = f"{description}_{datetime.now().timestamp()}"
            end_time = datetime.now() + timedelta(seconds=seconds)
            
            self.active_timers[timer_id] = {
                "label": description,
                "duration": seconds,
                "end_time": end_time,
                "started_at": datetime.now()
            }
            
            # Format duration for display
            if duration_minutes < 1:
                formatted_duration = f"{int(duration_minutes * 60)} seconds"
            elif duration_minutes == 1:
                formatted_duration = "1 minute"
            else:
                formatted_duration = f"{duration_minutes} minutes"
            
            logger.info(f"Timer started: {description} for {formatted_duration} ({seconds} seconds)")
            return {
                "success": True,
                "message": f"Timer '{description}' started for {formatted_duration}",
                "timer_id": timer_id,
                "duration_seconds": seconds,
                "end_time": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error setting timer: {e}")
            return {
                "success": False,
                "message": f"Failed to set timer: {str(e)}"
            }
    
    async def check_timers(self) -> Dict[str, Any]:
        """Check status of all active timers"""
        try:
            if not self.active_timers:
                return {
                    "success": True,
                    "message": "No active timers",
                    "timers": []
                }
            
            current_time = datetime.now()
            active_timers = []
            expired_timers = []
            
            for timer_id, timer_data in self.active_timers.items():
                time_remaining = (timer_data["end_time"] - current_time).total_seconds()
                
                if time_remaining <= 0:
                    expired_timers.append({
                        "id": timer_id,
                        "label": timer_data["label"],
                        "expired": True
                    })
                else:
                    active_timers.append({
                        "id": timer_id,
                        "label": timer_data["label"],
                        "time_remaining": int(time_remaining),
                        "time_remaining_formatted": self._format_duration(int(time_remaining))
                    })
            
            return {
                "success": True,
                "message": f"Found {len(active_timers)} active timers, {len(expired_timers)} expired",
                "active_timers": active_timers,
                "expired_timers": expired_timers
            }
            
        except Exception as e:
            logger.error(f"Error checking timers: {e}")
            return {
                "success": False,
                "message": f"Failed to check timers: {str(e)}"
            }
    
    async def cancel_timer(self, timer_label: str) -> Dict[str, Any]:
        """Cancel a timer by label"""
        try:
            timer_id = None
            for tid, timer_data in self.active_timers.items():
                if timer_data["label"].lower() == timer_label.lower():
                    timer_id = tid
                    break
            
            if timer_id:
                del self.active_timers[timer_id]
                logger.info(f"Timer cancelled: {timer_label}")
                return {
                    "success": True,
                    "message": f"Timer '{timer_label}' cancelled successfully"
                }
            else:
                return {
                    "success": False,
                    "message": f"No active timer found with label '{timer_label}'"
                }
                
        except Exception as e:
            logger.error(f"Error cancelling timer: {e}")
            return {
                "success": False,
                "message": f"Failed to cancel timer: {str(e)}"
            }
    
    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse duration string into seconds"""
        try:
            duration_str = duration_str.lower().strip()
            
            # Handle common formats
            if "second" in duration_str:
                return int(duration_str.split()[0])
            elif "minute" in duration_str:
                return int(duration_str.split()[0]) * 60
            elif "hour" in duration_str:
                return int(duration_str.split()[0]) * 3600
            elif duration_str.isdigit():
                # Assume seconds if just a number
                return int(duration_str)
            
            return None
            
        except (ValueError, IndexError):
            return None
    
    def _format_duration(self, seconds: int) -> str:
        """Format seconds into human-readable duration"""
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            if remaining_seconds == 0:
                return f"{minutes} minutes"
            else:
                return f"{minutes} minutes {remaining_seconds} seconds"
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            if remaining_minutes == 0:
                return f"{hours} hours"
            else:
                return f"{hours} hours {remaining_minutes} minutes"