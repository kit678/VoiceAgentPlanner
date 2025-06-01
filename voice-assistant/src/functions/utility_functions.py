#!/usr/bin/env python3
import os
from datetime import datetime
from typing import Dict, Any
from loguru import logger

class UtilityFunctions:
    """Utility functions for common operations in the voice assistant"""
    
    def __init__(self):
        logger.info("UtilityFunctions initialized")
    
    async def get_current_time(self, timezone: str = "local") -> Dict[str, Any]:
        """Get the current time"""
        try:
            now = datetime.now()
            
            # Format time in different ways
            time_12h = now.strftime("%I:%M %p")
            time_24h = now.strftime("%H:%M")
            date_str = now.strftime("%A, %B %d, %Y")
            
            message = f"Current time: {time_12h} ({time_24h})\nDate: {date_str}"
            
            logger.info("Retrieved current time")
            return {
                "success": True,
                "message": message,
                "time_data": {
                    "time_12h": time_12h,
                    "time_24h": time_24h,
                    "date": date_str,
                    "timestamp": now.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting current time: {e}")
            return {
                "success": False,
                "message": "Failed to get current time. Please try again."
            }
    
    async def get_status(self, component: str = "all") -> Dict[str, Any]:
        """Get system status information"""
        try:
            status_info = {
                "voice_assistant": "active",
                "database": "connected",
                "audio_processing": "ready",
                "timestamp": datetime.now().isoformat()
            }
            
            if component == "all":
                message = "System Status:\n"
                message += f"• Voice Assistant: {status_info['voice_assistant']}\n"
                message += f"• Database: {status_info['database']}\n"
                message += f"• Audio Processing: {status_info['audio_processing']}\n"
                message += f"• Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                component_status = status_info.get(component, "unknown")
                message = f"{component.title()} Status: {component_status}"
            
            logger.info(f"Retrieved status for: {component}")
            return {
                "success": True,
                "message": message,
                "status": status_info
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                "success": False,
                "message": "Failed to get system status. Please try again."
            }
    
    async def greet_user(self, user_name: str = "there") -> Dict[str, Any]:
        """Generate a greeting message"""
        try:
            now = datetime.now()
            hour = now.hour
            
            # Determine time of day greeting
            if 5 <= hour < 12:
                time_greeting = "Good morning"
            elif 12 <= hour < 17:
                time_greeting = "Good afternoon"
            elif 17 <= hour < 21:
                time_greeting = "Good evening"
            else:
                time_greeting = "Hello"
            
            message = f"{time_greeting}, {user_name}! How can I help you today?"
            
            logger.info(f"Generated greeting for user: {user_name}")
            return {
                "success": True,
                "message": message,
                "greeting_data": {
                    "time_greeting": time_greeting,
                    "user_name": user_name,
                    "timestamp": now.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating greeting: {e}")
            return {
                "success": False,
                "message": "Hello! How can I help you today?"
            }
    
    async def help_info(self, topic: str = "general") -> Dict[str, Any]:
        """Provide help information about available commands"""
        try:
            help_topics = {
                "general": {
                    "title": "Voice Assistant Help",
                    "content": [
                        "Available commands:",
                        "• Task Management: 'create task', 'list tasks', 'complete task'",
                        "• Reminders: 'set reminder', 'list reminders'",
                        "• Timers: 'start timer', 'list timers'",
                        "• Notes: 'take note', 'search notes', 'list notes'",
                        "• Goals: 'create goal', 'update progress', 'list goals'",
                        "• Utilities: 'what time is it', 'system status', 'help'",
                        "",
                        "Say 'help [topic]' for specific information about any category."
                    ]
                },
                "tasks": {
                    "title": "Task Management Help",
                    "content": [
                        "Task commands:",
                        "• 'Create task [name] due [date]' - Create a new task",
                        "• 'List tasks' - Show all pending tasks",
                        "• 'Complete task [name]' - Mark task as completed",
                        "• 'List completed tasks' - Show finished tasks",
                        "",
                        "Examples:",
                        "• 'Create task finish report due tomorrow'",
                        "• 'Create task buy groceries due next week'"
                    ]
                },
                "reminders": {
                    "title": "Reminder Help",
                    "content": [
                        "Reminder commands:",
                        "• 'Set reminder [text] at [time]' - Create a reminder",
                        "• 'List reminders' - Show active reminders",
                        "",
                        "Time formats:",
                        "• 'at 3 PM', 'at 15:30', 'in 30 minutes'",
                        "• 'tomorrow at 9 AM', 'next Monday at 2 PM'",
                        "",
                        "Examples:",
                        "• 'Set reminder call mom at 6 PM'",
                        "• 'Set reminder meeting in 1 hour'"
                    ]
                },
                "timers": {
                    "title": "Timer Help",
                    "content": [
                        "Timer commands:",
                        "• 'Start timer for [duration]' - Start a countdown timer",
                        "• 'Start timer [name] for [duration]' - Named timer",
                        "• 'List timers' - Show running timers",
                        "",
                        "Duration formats:",
                        "• '5 minutes', '30 seconds', '1 hour'",
                        "• '2 hours 30 minutes'",
                        "",
                        "Examples:",
                        "• 'Start timer for 25 minutes'",
                        "• 'Start timer pomodoro for 25 minutes'"
                    ]
                },
                "notes": {
                    "title": "Note-Taking Help",
                    "content": [
                        "Note commands:",
                        "• 'Take note [content]' - Create a new note",
                        "• 'Search notes [query]' - Find notes by content",
                        "• 'List notes' - Show recent notes",
                        "• 'List notes in [category]' - Filter by category",
                        "",
                        "Examples:",
                        "• 'Take note remember to buy milk'",
                        "• 'Search notes meeting'",
                        "• 'List notes in work category'"
                    ]
                },
                "goals": {
                    "title": "Goal Management Help",
                    "content": [
                        "Goal commands:",
                        "• 'Create goal [name] by [date]' - Set a new goal",
                        "• 'Update goal progress [percentage]' - Track progress",
                        "• 'List goals' - Show active goals",
                        "• 'Goal summary' - Overview of all goals",
                        "",
                        "Examples:",
                        "• 'Create goal learn Spanish by end of year'",
                        "• 'Update goal progress 75 percent'"
                    ]
                }
            }
            
            topic_info = help_topics.get(topic.lower(), help_topics["general"])
            message = f"{topic_info['title']}\n\n" + "\n".join(topic_info['content'])
            
            logger.info(f"Provided help for topic: {topic}")
            return {
                "success": True,
                "message": message,
                "help_data": {
                    "topic": topic,
                    "available_topics": list(help_topics.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"Error providing help: {e}")
            return {
                "success": False,
                "message": "Sorry, I couldn't provide help information right now. Please try again."
            }