# voice-assistant/src/llm/parameter_extractor.py

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from loguru import logger
import json

class ParameterExtractor:
    """Extracts structured parameters from natural language commands."""
    
    def __init__(self):
        self.priority_keywords = {
            "high": 3, "urgent": 3, "important": 3, "critical": 3,
            "medium": 2, "normal": 2, "moderate": 2,
            "low": 1, "minor": 1, "later": 1
        }
        
        self.time_patterns = {
            # Relative times
            r"in (\d+) minutes?": lambda m: datetime.now() + timedelta(minutes=int(m.group(1))),
            r"in (\d+) hours?": lambda m: datetime.now() + timedelta(hours=int(m.group(1))),
            r"in (\d+) days?": lambda m: datetime.now() + timedelta(days=int(m.group(1))),
            r"tomorrow": lambda m: datetime.now() + timedelta(days=1),
            r"next week": lambda m: datetime.now() + timedelta(weeks=1),
            r"next month": lambda m: datetime.now() + timedelta(days=30),
            
            # Specific times
            r"at (\d{1,2}):(\d{2})\s*(am|pm)?": self._parse_time,
            r"at (\d{1,2})\s*(am|pm)": self._parse_simple_time,
            
            # Days of week
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)": self._parse_weekday,
            r"next (monday|tuesday|wednesday|thursday|friday|saturday|sunday)": self._parse_next_weekday,
        }
    
    def _parse_time(self, match):
        """Parse time like '2:30 pm' or '14:30'"""
        hour = int(match.group(1))
        minute = int(match.group(2))
        period = match.group(3).lower() if match.group(3) else None
        
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
            
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time has passed today, schedule for tomorrow
        if target <= now:
            target += timedelta(days=1)
            
        return target
    
    def _parse_simple_time(self, match):
        """Parse time like '2 pm' or '14'"""
        hour = int(match.group(1))
        period = match.group(2).lower() if match.group(2) else None
        
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
            
        now = datetime.now()
        target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        if target <= now:
            target += timedelta(days=1)
            
        return target
    
    def _parse_weekday(self, match):
        """Parse weekday names"""
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekday = weekdays[match.group(1).lower()]
        now = datetime.now()
        days_ahead = target_weekday - now.weekday()
        
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
            
        return now + timedelta(days=days_ahead)
    
    def _parse_next_weekday(self, match):
        """Parse 'next monday' etc."""
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekday = weekdays[match.group(1).lower()]
        now = datetime.now()
        days_ahead = target_weekday - now.weekday() + 7  # Always next week
        
        return now + timedelta(days=days_ahead)
    
    def extract_datetime(self, text: str) -> Optional[datetime]:
        """Extract datetime from natural language text."""
        text_lower = text.lower()
        
        for pattern, parser in self.time_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                try:
                    if callable(parser):
                        return parser(match)
                    else:
                        return parser
                except Exception as e:
                    logger.warning(f"Error parsing datetime from '{text}': {e}")
                    continue
        
        return None
    
    def extract_priority(self, text: str) -> int:
        """Extract priority level from text (0=none, 1=low, 2=medium, 3=high)."""
        text_lower = text.lower()
        
        for keyword, priority in self.priority_keywords.items():
            if keyword in text_lower:
                return priority
        
        return 0  # Default priority
    
    def extract_task_description(self, text: str, intent: str) -> str:
        """Extract clean task description from command text."""
        text_lower = text.lower()
        
        # Remove command prefixes
        prefixes_to_remove = [
            "create task to ", "create task ", "add task to ", "add task ",
            "new task to ", "new task ", "remind me to ", "reminder to ",
            "set reminder to ", "set reminder ", "todo ", "to do "
        ]
        
        description = text_lower
        for prefix in prefixes_to_remove:
            if description.startswith(prefix):
                description = description[len(prefix):].strip()
                break
        
        # Remove priority and time indicators to get clean description
        priority_words = list(self.priority_keywords.keys())
        time_words = ["tomorrow", "today", "next week", "next month", "monday", "tuesday", 
                     "wednesday", "thursday", "friday", "saturday", "sunday", "am", "pm"]
        
        words = description.split()
        clean_words = []
        
        i = 0
        while i < len(words):
            word = words[i].lower().strip('.,!?')
            
            # Skip priority words
            if word in priority_words:
                i += 1
                continue
            
            # Skip time-related phrases
            if word in time_words:
                i += 1
                continue
            
            # Skip "at" followed by time
            if word == "at" and i + 1 < len(words):
                next_word = words[i + 1].lower()
                if re.match(r"\d{1,2}(:\d{2})?(am|pm)?", next_word):
                    i += 2
                    continue
            
            # Skip "in X minutes/hours/days"
            if word == "in" and i + 2 < len(words):
                if re.match(r"\d+", words[i + 1]) and words[i + 2].lower() in ["minute", "minutes", "hour", "hours", "day", "days"]:
                    i += 3
                    continue
            
            clean_words.append(words[i])
            i += 1
        
        clean_description = " ".join(clean_words).strip()
        return clean_description if clean_description else "unspecified task"
    
    def extract_parameters(self, intent: str, text: str) -> Dict[str, Any]:
        """Extract all relevant parameters from natural language command."""
        parameters = {}
        
        try:
            if intent == "create_task":
                parameters["description"] = self.extract_task_description(text, intent)
                
                due_date = self.extract_datetime(text)
                if due_date:
                    parameters["due_date"] = due_date.isoformat()
                
                priority = self.extract_priority(text)
                if priority > 0:
                    parameters["priority"] = priority
            
            elif intent == "set_reminder":
                parameters["description"] = self.extract_task_description(text, intent)
                
                reminder_time = self.extract_datetime(text)
                if reminder_time:
                    parameters["reminder_time"] = reminder_time.isoformat()
                else:
                    # Default to 1 hour from now if no time specified
                    default_time = datetime.now() + timedelta(hours=1)
                    parameters["reminder_time"] = default_time.isoformat()
            
            elif intent == "start_timer":
                # Extract duration
                duration_match = re.search(r"(\d+)\s*(minute|minutes|min|hour|hours|hr|second|seconds|sec)", text.lower())
                if duration_match:
                    value = int(duration_match.group(1))
                    unit = duration_match.group(2)
                    
                    if unit.startswith("min"):
                        parameters["duration_seconds"] = value * 60
                    elif unit.startswith("hour") or unit.startswith("hr"):
                        parameters["duration_seconds"] = value * 3600
                    elif unit.startswith("sec"):
                        parameters["duration_seconds"] = value
                else:
                    # Default to 25 minutes (Pomodoro)
                    parameters["duration_seconds"] = 25 * 60
                
                # Extract timer name/description
                timer_name = self.extract_task_description(text, intent)
                if timer_name and timer_name != "unspecified task":
                    parameters["name"] = timer_name
            
            elif intent == "take_note":
                # For notes, the entire text after command is the content
                prefixes_to_remove = ["take note ", "note ", "remember ", "write down "]
                content = text.lower()
                
                for prefix in prefixes_to_remove:
                    if content.startswith(prefix):
                        content = text[len(prefix):].strip()  # Use original case
                        break
                
                parameters["content"] = content if content else text
            
            elif intent == "create_goal":
                # Extract goal name/description
                prefixes_to_remove = ["create goal to ", "create goal ", "add goal to ", "add goal ", "new goal to ", "new goal "]
                goal_name = text.lower()
                
                for prefix in prefixes_to_remove:
                    if goal_name.startswith(prefix):
                        goal_name = text[len(prefix):].strip()  # Use original case
                        break
                
                parameters["name"] = goal_name if goal_name else "Unnamed Goal"
                
                # Extract target date if mentioned
                target_date = self.extract_datetime(text)
                if target_date:
                    parameters["target_date"] = target_date.isoformat()
            
            logger.info(f"Extracted parameters for intent '{intent}': {parameters}")
            
        except Exception as e:
            logger.error(f"Error extracting parameters from '{text}': {e}")
            parameters["description"] = text  # Fallback
        
        return parameters
    
    def validate_parameters(self, intent: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted parameters."""
        validated = parameters.copy()
        
        try:
            if intent == "create_task":
                # Ensure description exists and is meaningful
                if not validated.get("description") or validated["description"] == "unspecified task":
                    validated["needs_clarification"] = "task_description"
                
                # Validate due_date format
                if "due_date" in validated:
                    try:
                        datetime.fromisoformat(validated["due_date"])
                    except ValueError:
                        logger.warning(f"Invalid due_date format: {validated['due_date']}")
                        del validated["due_date"]
                
                # Validate priority range
                if "priority" in validated:
                    priority = validated["priority"]
                    if not isinstance(priority, int) or priority < 0 or priority > 3:
                        validated["priority"] = 0
            
            elif intent == "set_reminder":
                if not validated.get("description"):
                    validated["needs_clarification"] = "reminder_description"
                
                if not validated.get("reminder_time"):
                    validated["needs_clarification"] = "reminder_time"
            
            elif intent == "start_timer":
                if "duration_seconds" not in validated or validated["duration_seconds"] <= 0:
                    validated["duration_seconds"] = 25 * 60  # Default Pomodoro
            
            elif intent == "take_note":
                if not validated.get("content"):
                    validated["needs_clarification"] = "note_content"
        
        except Exception as e:
            logger.error(f"Error validating parameters for intent '{intent}': {e}")
        
        return validated