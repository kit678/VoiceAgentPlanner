# voice-assistant/src/llm/command_processor_processor.py
from pipecat.frames.frames import Frame, TextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from .intent_parser_processor import IntentFrame # Import the custom IntentFrame
from ..utils.firestore_client import get_firestore_client # Import Firestore client
from .data_models import Task # Import Task data model
from loguru import logger # For better logging

class CommandProcessorFrameProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self._db = get_firestore_client()
        logger.info("CommandProcessorFrameProcessor initialized.")
        if self._db:
            logger.info("Firestore client successfully obtained in CommandProcessor.")
        else:
            logger.warning("Firestore client not available in CommandProcessor.")

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction) # Important to call super

        if isinstance(frame, IntentFrame) and direction == FrameDirection.DOWNSTREAM:
            intent = frame.intent
            parameters = frame.parameters
            original_text = frame.original_text

            print(f"CommandProcessorFrameProcessor received IntentFrame: intent='{intent}', params={parameters}")

            response_text = ""
            # Map intents to handler methods
            intent_handlers = {
                "greet": self._handle_greet,
                "create_task": self._handle_create_task,
                "get_time": self._handle_get_time,
                # Add more intents and handlers here
            }

            handler = intent_handlers.get(intent, self._handle_unknown_intent)
            response_text = await handler(parameters, original_text)

            if response_text:
                logger.info(f"Pushing TextFrame (response): {response_text}")
                await self.push_frame(TextFrame(response_text), FrameDirection.UPSTREAM)
        else:
            await self.push_frame(frame, direction)

    async def _handle_greet(self, parameters: dict, original_text: str) -> str:
        return "Hello there! How can I help you today?"

    async def _handle_create_task(self, parameters: dict, original_text: str) -> str:
        task_description = parameters.get("description")
        if not task_description:
            logger.warning("COMMAND_PROCESSOR: Task description missing for create_task intent.")
            return "I can create a task, but I need a description. What would you like to do?"

        if not self._db:
            logger.error("COMMAND_PROCESSOR: Firestore client not available. Cannot create task.")
            return "I'm having trouble connecting to the database to save your task. Please try again later."

        try:
            new_task = Task(
                description=task_description,
                raw_command=original_text,
                # user_id can be set here if available, e.g., from session or config
            )
            # Convert Pydantic model to dictionary for Firestore
            task_dict = new_task.model_dump(mode='json')
            # Firestore automatically generates an ID if not provided
            doc_ref = await self._db.collection("tasks").add(task_dict)
            
            logger.info(f"COMMAND_PROCESSOR: Successfully created task with ID: {doc_ref[1].id}")
            return f"Okay, I've created a task: '{task_description}'."

        except Exception as e:
            logger.exception(f"COMMAND_PROCESSOR: Error creating task '{task_description}': {e}")
            return f"I encountered an error while trying to create the task: '{task_description}'."

    async def _handle_get_time(self, parameters: dict, original_text: str) -> str:
        import datetime
        now = datetime.datetime.now()
        current_time = now.strftime("%I:%M %p") # Format as H:MM AM/PM
        return f"The current time is {current_time}."

    async def _handle_unknown_intent(self, parameters: dict, original_text: str) -> str:
        logger.warning(f"COMMAND_PROCESSOR: Unknown intent. Original text: '{original_text}', Params: {parameters}")
        return "I'm sorry, I didn't understand that command. Could you please rephrase?"

    # Example of a more complex command handler (can be added as needed)
    async def _execute_create_calendar_event(self, parameters: dict) -> str:
        summary = parameters.get("summary", "Unnamed Event")
        start_time = parameters.get("start_time", "now")
        # Placeholder for actual calendar event creation
        print(f"COMMAND_PROCESSOR: TODO: Create calendar event: {summary} at {start_time}")
        return f"Calendar event '{summary}' creation (simulated)."