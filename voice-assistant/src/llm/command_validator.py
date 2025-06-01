# voice-assistant/src/llm/command_validator.py

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from loguru import logger
from llm.data_models import Task, Reminder, Timer, Note

class CommandValidator:
    """Validates commands and generates confirmation prompts."""
    
    def __init__(self):
        self.required_fields = {
            "create_task": ["description"],
            "set_reminder": ["description", "reminder_time"],
            "start_timer": ["duration_seconds"],
            "take_note": ["content"],
            "create_goal": ["name"],
        }
        
        self.optional_fields = {
            "create_task": ["due_date", "priority", "goal_id"],
            "set_reminder": ["task_id"],
            "start_timer": ["name", "task_id"],
            "take_note": ["tags"],
            "create_goal": ["description", "target_date"],
        }
    
    def validate_command(self, intent: str, parameters: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate a command and return validation status, missing fields, and suggestions.
        
        Returns:
            Tuple of (is_valid, missing_fields, validation_info)
        """
        is_valid = True
        missing_fields = []
        validation_info = {}
        
        try:
            # Check if intent is supported
            if intent not in self.required_fields:
                return False, ["unsupported_intent"], {"error": f"Intent '{intent}' is not supported"}
            
            # Check required fields
            required = self.required_fields.get(intent, [])
            for field in required:
                if field not in parameters or not parameters[field]:
                    missing_fields.append(field)
                    is_valid = False
            
            # Check for clarification needs
            if "needs_clarification" in parameters:
                missing_fields.append(parameters["needs_clarification"])
                is_valid = False
            
            # Validate specific field types and values
            validation_errors = self._validate_field_types(intent, parameters)
            if validation_errors:
                validation_info["field_errors"] = validation_errors
                is_valid = False
            
            # Generate suggestions for improvement
            suggestions = self._generate_suggestions(intent, parameters, missing_fields)
            if suggestions:
                validation_info["suggestions"] = suggestions
            
            logger.info(f"Command validation for '{intent}': valid={is_valid}, missing={missing_fields}")
            
        except Exception as e:
            logger.error(f"Error validating command '{intent}': {e}")
            return False, ["validation_error"], {"error": str(e)}
        
        return is_valid, missing_fields, validation_info
    
    def _validate_field_types(self, intent: str, parameters: Dict[str, Any]) -> List[str]:
        """Validate field types and formats."""
        errors = []
        
        try:
            # Validate datetime fields
            datetime_fields = ["due_date", "reminder_time", "target_date"]
            for field in datetime_fields:
                if field in parameters:
                    try:
                        if isinstance(parameters[field], str):
                            datetime.fromisoformat(parameters[field])
                        elif not isinstance(parameters[field], datetime):
                            errors.append(f"Invalid {field} format")
                    except ValueError:
                        errors.append(f"Invalid {field} format")
            
            # Validate numeric fields
            if "priority" in parameters:
                priority = parameters["priority"]
                if not isinstance(priority, int) or priority < 0 or priority > 3:
                    errors.append("Priority must be 0-3")
            
            if "duration_seconds" in parameters:
                duration = parameters["duration_seconds"]
                if not isinstance(duration, int) or duration <= 0:
                    errors.append("Duration must be positive")
            
            # Validate string fields
            string_fields = ["description", "content", "name"]
            for field in string_fields:
                if field in parameters:
                    value = parameters[field]
                    if not isinstance(value, str) or len(value.strip()) == 0:
                        errors.append(f"{field} cannot be empty")
        
        except Exception as e:
            logger.error(f"Error validating field types: {e}")
            errors.append("Field validation error")
        
        return errors
    
    def _generate_suggestions(self, intent: str, parameters: Dict[str, Any], missing_fields: List[str]) -> List[str]:
        """Generate helpful suggestions for improving the command."""
        suggestions = []
        
        try:
            if intent == "create_task":
                if "description" in missing_fields:
                    suggestions.append("Try: 'Create task to finish the report'")
                
                if "due_date" not in parameters:
                    suggestions.append("Add a due date like 'tomorrow' or 'next Friday'")
                
                if "priority" not in parameters:
                    suggestions.append("Specify priority: 'high priority task' or 'low priority'")
            
            elif intent == "set_reminder":
                if "description" in missing_fields:
                    suggestions.append("Try: 'Remind me to call John'")
                
                if "reminder_time" in missing_fields:
                    suggestions.append("Specify when: 'in 30 minutes' or 'at 3 PM'")
            
            elif intent == "start_timer":
                if "duration_seconds" not in parameters:
                    suggestions.append("Specify duration: '25 minutes' or '1 hour'")
                
                if "name" not in parameters:
                    suggestions.append("Add a name: 'Start 25 minute focus timer'")
            
            elif intent == "take_note":
                if "content" in missing_fields:
                    suggestions.append("Try: 'Take note: Meeting notes from today'")
        
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
        
        return suggestions
    
    def generate_confirmation_prompt(self, intent: str, parameters: Dict[str, Any]) -> str:
        """Generate a human-readable confirmation prompt."""
        try:
            if intent == "create_task":
                description = parameters.get("description", "unspecified task")
                prompt = f"I'll create a task: '{description}'"
                
                if "due_date" in parameters:
                    due_date = datetime.fromisoformat(parameters["due_date"])
                    prompt += f" due {self._format_datetime(due_date)}"
                
                if "priority" in parameters and parameters["priority"] > 0:
                    priority_names = {1: "low", 2: "medium", 3: "high"}
                    prompt += f" with {priority_names[parameters['priority']]} priority"
                
                return prompt + ". Is this correct?"
            
            elif intent == "set_reminder":
                description = parameters.get("description", "unspecified reminder")
                reminder_time = datetime.fromisoformat(parameters["reminder_time"])
                
                return f"I'll remind you to '{description}' {self._format_datetime(reminder_time)}. Is this correct?"
            
            elif intent == "start_timer":
                duration = parameters.get("duration_seconds", 1500)
                duration_text = self._format_duration(duration)
                
                name = parameters.get("name", "focus session")
                return f"I'll start a {duration_text} timer for '{name}'. Ready to begin?"
            
            elif intent == "take_note":
                content = parameters.get("content", "")
                preview = content[:50] + "..." if len(content) > 50 else content
                return f"I'll save this note: '{preview}'. Is this correct?"
            
            elif intent == "create_goal":
                name = parameters.get("name", "unspecified goal")
                prompt = f"I'll create a goal: '{name}'"
                
                if "target_date" in parameters:
                    target_date = datetime.fromisoformat(parameters["target_date"])
                    prompt += f" with target date {self._format_datetime(target_date)}"
                
                return prompt + ". Is this correct?"
            
            else:
                return f"I'll execute the '{intent}' command. Is this correct?"
        
        except Exception as e:
            logger.error(f"Error generating confirmation prompt: {e}")
            return "I'll execute this command. Is this correct?"
    
    def generate_clarification_prompt(self, intent: str, missing_fields: List[str], validation_info: Dict[str, Any]) -> str:
        """Generate a prompt asking for missing information."""
        try:
            if "unsupported_intent" in missing_fields:
                return "I'm sorry, I don't understand that command. Could you please rephrase?"
            
            if "validation_error" in missing_fields:
                return "I encountered an error processing your command. Could you please try again?"
            
            # Handle specific missing fields
            if intent == "create_task":
                if "task_description" in missing_fields or "description" in missing_fields:
                    return "I can create a task, but I need to know what you'd like to do. What should the task be?"
            
            elif intent == "set_reminder":
                if "reminder_description" in missing_fields or "description" in missing_fields:
                    return "I can set a reminder, but what should I remind you about?"
                
                if "reminder_time" in missing_fields:
                    return "When should I remind you? For example, 'in 30 minutes' or 'at 3 PM'."
            
            elif intent == "start_timer":
                if "duration_seconds" in missing_fields:
                    return "How long should the timer run? For example, '25 minutes' or '1 hour'."
            
            elif intent == "take_note":
                if "note_content" in missing_fields or "content" in missing_fields:
                    return "What would you like me to note down?"
            
            # Generic fallback
            suggestions = validation_info.get("suggestions", [])
            if suggestions:
                return f"I need more information. {suggestions[0]}"
            
            return "I need more information to complete this command. Could you provide more details?"
        
        except Exception as e:
            logger.error(f"Error generating clarification prompt: {e}")
            return "I need more information to complete this command. Could you provide more details?"
    
    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for human-readable display."""
        now = datetime.now()
        
        # If it's today
        if dt.date() == now.date():
            return f"today at {dt.strftime('%I:%M %p').lower()}"
        
        # If it's tomorrow
        elif dt.date() == (now.date().replace(day=now.day + 1) if now.day < 28 else (now + timedelta(days=1)).date()):
            return f"tomorrow at {dt.strftime('%I:%M %p').lower()}"
        
        # If it's this week
        elif (dt - now).days < 7:
            return f"{dt.strftime('%A')} at {dt.strftime('%I:%M %p').lower()}"
        
        # Otherwise, full date
        else:
            return dt.strftime('%B %d at %I:%M %p').lower()
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human-readable text."""
        if seconds < 60:
            return f"{seconds} second{'s' if seconds != 1 else ''}"
        
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        if minutes < 60:
            if remaining_seconds == 0:
                return f"{minutes} minute{'s' if minutes != 1 else ''}"
            else:
                return f"{minutes} minute{'s' if minutes != 1 else ''} and {remaining_seconds} second{'s' if remaining_seconds != 1 else ''}"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours != 1 else ''} and {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"