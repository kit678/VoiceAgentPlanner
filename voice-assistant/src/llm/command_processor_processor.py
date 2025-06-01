# voice-assistant/src/llm/command_processor_processor.py
from pipecat.frames.frames import Frame, TextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from .intent_parser_processor import IntentFrame
from .command_validator import CommandValidator
from ..firebase.firestore_service import FirestoreService
from ..functions.task_functions import TaskFunctions
from ..functions.note_functions import NoteFunctions
from ..functions.reminder_functions import ReminderFunctions
from ..functions.goal_functions import GoalFunctions
from ..functions.context_functions import ContextFunctions
from loguru import logger
import asyncio
from datetime import datetime, timedelta
import uuid

class CommandProcessorFrameProcessor(FrameProcessor):
    def __init__(self, firestore_service: FirestoreService = None):
        super().__init__()
        self._firestore_service = firestore_service or FirestoreService()
        self.command_validator = CommandValidator()
        self.pending_confirmations = {}  # Store commands awaiting confirmation
        
        # Initialize function classes
        self.task_functions = TaskFunctions(self._firestore_service)
        self.note_functions = NoteFunctions(self._firestore_service)
        self.reminder_functions = ReminderFunctions(self._firestore_service)
        self.goal_functions = GoalFunctions(self._firestore_service)
        self.context_functions = ContextFunctions(self._firestore_service)
        
        logger.info("CommandProcessorFrameProcessor initialized with FirestoreService and command validator")

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        # Handle IntentFrames from the IntentParserFrameProcessor
        if isinstance(frame, IntentFrame):
            logger.info(f"CommandProcessor received IntentFrame: {frame}")
            
            intent = frame.intent
            parameters = frame.parameters
            original_text = frame.original_text
            confidence = frame.confidence
            
            # Check if this is a confirmation response
            if await self._handle_confirmation_response(intent, parameters, original_text):
                return
            
            # Validate command before execution
            validation_result = await self.command_validator.validate_command(intent, parameters)
            
            if validation_result["valid"]:
                # Execute the command
                await self._execute_command(intent, parameters, original_text, confidence)
            elif validation_result["needs_confirmation"]:
                # Store command for confirmation and ask user
                confirmation_id = str(uuid.uuid4())
                self.pending_confirmations[confirmation_id] = {
                    "intent": intent,
                    "parameters": parameters,
                    "original_text": original_text,
                    "confidence": confidence,
                    "timestamp": datetime.now()
                }
                
                # Send confirmation request to user
                confirmation_text = validation_result["confirmation_prompt"]
                await self._send_response(confirmation_text)
                
            elif validation_result["needs_clarification"]:
                # Ask for clarification
                clarification_text = validation_result["clarification_prompt"]
                await self._send_response(clarification_text)
            else:
                # Invalid command
                error_text = validation_result.get("error", "I couldn't understand that command.")
                await self._send_response(error_text)
        
        # Pass through other frames
        await self.push_frame(frame, direction)

    async def _handle_confirmation_response(self, intent: str, parameters: dict, original_text: str) -> bool:
        """Handle confirmation responses (yes/no) for pending commands"""
        if not self.pending_confirmations:
            return False
        
        # Check if this is a confirmation response
        text_lower = original_text.lower()
        is_yes = any(word in text_lower for word in ["yes", "yeah", "yep", "confirm", "ok", "okay"])
        is_no = any(word in text_lower for word in ["no", "nope", "cancel", "nevermind"])
        
        if is_yes or is_no:
            # Get the most recent pending confirmation
            latest_confirmation = max(self.pending_confirmations.items(), 
                                    key=lambda x: x[1]["timestamp"])
            confirmation_id, command_data = latest_confirmation
            
            if is_yes:
                # Execute the confirmed command
                await self._execute_command(
                    command_data["intent"],
                    command_data["parameters"],
                    command_data["original_text"],
                    command_data["confidence"]
                )
            else:
                await self._send_response("Command cancelled.")
            
            # Remove the confirmation
            del self.pending_confirmations[confirmation_id]
            return True
        
        return False
    
    async def _execute_command(self, intent: str, parameters: dict, original_text: str, confidence: float):
        """Execute a validated command"""
        try:
            # Route to appropriate handler based on intent
            if intent == "greet":
                await self._handle_greet(parameters, original_text)
            elif intent == "create_task":
                await self._handle_create_task(parameters, original_text)
            elif intent == "set_reminder":
                await self._handle_set_reminder(parameters, original_text)
            elif intent == "start_timer":
                await self._handle_start_timer(parameters, original_text)
            elif intent == "take_note":
                await self._handle_take_note(parameters, original_text)
            elif intent == "create_goal":
                await self._handle_create_goal(parameters, original_text)
            elif intent == "get_time":
                await self._handle_get_time(parameters, original_text)
            elif intent == "get_status":
                await self._handle_get_status(parameters, original_text)
            else:
                await self._handle_unknown_intent(intent, parameters, original_text)
        except Exception as e:
            logger.error(f"Error executing command {intent}: {e}")
            await self._send_response("Sorry, I encountered an error while processing that command.")
    
    async def _send_response(self, text: str):
        """Send a text response to the user"""
        logger.info(f"Sending response: {text}")
        await self.push_frame(TextFrame(text), FrameDirection.UPSTREAM)
    
    async def _handle_greet(self, parameters: dict, original_text: str):
        """Handle greeting intents"""
        logger.info("Handling greet intent")
        await self._send_response("Hello! How can I help you today?")
    
    async def _handle_create_task(self, parameters: dict, original_text: str):
        """Handle task creation intents"""
        logger.info(f"Handling create_task intent with parameters: {parameters}")
        
        try:
            # Extract task parameters
            description = parameters.get("description", "Unspecified task")
            priority = parameters.get("priority", "medium")
            due_date = parameters.get("due_date")
            
            # Create task data
            task_data = {
                "description": description,
                "completed": False,
                "created_at": datetime.now(),
                "priority": priority,
                "due_date": due_date
            }
            
            # Save to Firestore
            task_id = await self._firestore_service.add_document("tasks", task_data)
            
            logger.info(f"Task created successfully with ID: {task_id}")
            
            # Build response message
            response = f"Task created: '{description}'"
            if priority != "medium":
                response += f" (Priority: {priority})"
            if due_date:
                response += f" (Due: {due_date})"
            
            await self._send_response(response)
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            await self._send_response("Sorry, I couldn't create that task. Please try again.")
    
    async def _handle_set_reminder(self, parameters: dict, original_text: str):
        """Handle reminder creation intents"""
        logger.info(f"Handling set_reminder intent with parameters: {parameters}")
        
        try:
            description = parameters.get("description", "Reminder")
            reminder_time = parameters.get("reminder_time")
            
            reminder_data = {
                "description": description,
                "reminder_time": reminder_time,
                "created_at": datetime.now(),
                "completed": False
            }
            
            # Save to Firestore
            reminder_id = await self._firestore_service.add_document("reminders", reminder_data)
            
            response = f"Reminder set: '{description}'"
            if reminder_time:
                response += f" for {reminder_time}"
            
            await self._send_response(response)
            
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            await self._send_response("Sorry, I couldn't set that reminder. Please try again.")
    
    async def _handle_start_timer(self, parameters: dict, original_text: str):
        """Handle timer start intents"""
        logger.info(f"Handling start_timer intent with parameters: {parameters}")
        
        try:
            duration_minutes = parameters.get("duration_minutes", 25)  # Default to 25 min Pomodoro
            description = parameters.get("description", "Focus session")
            
            timer_data = {
                "description": description,
                "duration_minutes": duration_minutes,
                "start_time": datetime.now(),
                "end_time": datetime.now() + timedelta(minutes=duration_minutes),
                "active": True
            }
            
            # Save to Firestore
            timer_id = await self._firestore_service.add_document("timers", timer_data)
            
            await self._send_response(f"Timer started: {description} for {duration_minutes} minutes")
            
        except Exception as e:
            logger.error(f"Error starting timer: {e}")
            await self._send_response("Sorry, I couldn't start that timer. Please try again.")
    
    async def _handle_take_note(self, parameters: dict, original_text: str):
        """Handle note taking intents"""
        logger.info(f"Handling take_note intent with parameters: {parameters}")
        
        try:
            content = parameters.get("content", original_text)
            
            note_data = {
                "content": content,
                "created_at": datetime.now(),
                "tags": []
            }
            
            # Save to Firestore
            note_id = await self._firestore_service.add_document("notes", note_data)
            
            await self._send_response(f"Note saved: '{content[:50]}{'...' if len(content) > 50 else ''}'") 
            
        except Exception as e:
            logger.error(f"Error saving note: {e}")
            await self._send_response("Sorry, I couldn't save that note. Please try again.")
    
    async def _handle_create_goal(self, parameters: dict, original_text: str):
        """Handle goal creation intents"""
        logger.info(f"Handling create_goal intent with parameters: {parameters}")
        
        try:
            description = parameters.get("description", "New goal")
            target_date = parameters.get("target_date")
            priority = parameters.get("priority", "medium")
            
            goal_data = {
                "description": description,
                "target_date": target_date,
                "priority": priority,
                "created_at": datetime.now(),
                "completed": False,
                "progress": 0
            }
            
            # Save to Firestore
            goal_id = await self._firestore_service.add_document("goals", goal_data)
            
            response = f"Goal created: '{description}'"
            if target_date:
                response += f" (Target: {target_date})"
            
            await self._send_response(response)
            
        except Exception as e:
            logger.error(f"Error creating goal: {e}")
            await self._send_response("Sorry, I couldn't create that goal. Please try again.")
    
    async def _handle_get_time(self, parameters: dict, original_text: str):
        """Handle time query intents"""
        logger.info("Handling get_time intent")
        current_time = datetime.now().strftime("%I:%M %p")
        await self._send_response(f"The current time is {current_time}")
    
    async def _handle_get_status(self, parameters: dict, original_text: str):
        """Handle status query intents"""
        logger.info(f"Handling get_status intent with parameters: {parameters}")
        
        try:
            status_type = parameters.get("type", "all")
            
            if status_type == "tasks" or status_type == "all":
                # Get recent tasks
                tasks = await self._firestore_service.query_collection(
                    "tasks", 
                    order_by=[("created_at", "desc")], 
                    limit=5
                )
                if tasks:
                    task_list = "\n".join([f"- {task.get('description', 'No description')}" for task in tasks])
                    await self._send_response(f"Your recent tasks:\n{task_list}")
                else:
                    await self._send_response("You have no recent tasks.")
            else:
                await self._send_response(f"Status for {status_type} is not yet implemented.")
                
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            await self._send_response("Sorry, I couldn't retrieve your status. Please try again.")
    
    async def _handle_unknown_intent(self, intent: str, parameters: dict, original_text: str):
        """Handle unknown or unrecognized intents"""
        logger.warning(f"Unknown intent '{intent}' received. Original text: {original_text}")
        await self._send_response("I'm sorry, I didn't understand that. Could you please rephrase?")

    # Example of a more complex command handler (can be added as needed)
    async def _execute_create_calendar_event(self, parameters: dict) -> str:
        summary = parameters.get("summary", "Unnamed Event")
        start_time = parameters.get("start_time", "now")
        # Placeholder for actual calendar event creation
        print(f"COMMAND_PROCESSOR: TODO: Create calendar event: {summary} at {start_time}")
        return f"Calendar event '{summary}' creation (simulated)."