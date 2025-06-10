#!/usr/bin/env python3
import asyncio
import sys
import os
import signal
from dotenv import load_dotenv
from loguru import logger

from pipecat.frames.frames import Frame, TextFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.observers.loggers.transcription_log_observer import TranscriptionLogObserver

# Import Gemini Multimodal Live service
from pipecat.services.gemini_multimodal_live.gemini import (
    GeminiMultimodalLiveLLMService,
    InputParams,
    GeminiMultimodalModalities
)
from pipecat.transcriptions.language import Language

# Import Pipecat's function calling capabilities
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.services.llm_service import FunctionCallParams

# Import LLM context classes
from pipecat.services.openai.llm import OpenAILLMContext

# Import WebSocket bridge
from websocket_server import bridge, start_websocket_bridge

# Import function implementations
from functions.task_functions import TaskFunctions
from functions.reminder_functions import ReminderFunctions
from functions.timer_functions import TimerFunctions
from functions.note_functions import NoteFunctions
from functions.goal_functions import GoalFunctions
from functions.context_functions import ContextFunctions
from functions.utility_functions import UtilityFunctions

from functions.google_workspace_functions import GoogleWorkspaceFunctions

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'), override=True)

# Simple logging setup like the previous version
logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

# Windows-compatible PipelineRunner wrapper
class WindowsCompatiblePipelineRunner(PipelineRunner):
    """
    Windows-compatible wrapper for PipelineRunner that handles the 
    NotImplementedError when signal handlers are not supported on Windows.
    """
    
    def __init__(self):
        try:
            super().__init__()
            logger.debug("PipelineRunner initialized with signal handlers")
        except Exception as e:
            logger.warning(f"Error initializing PipelineRunner: {e}")
            # Initialize the base class manually without signal handlers
            self._pipeline_task = None
            self._stop_task = None
            logger.debug("PipelineRunner initialized without signal handlers (Windows compatibility)")
    
    def _setup_sigint(self):
        """Override signal setup to handle Windows NotImplementedError"""
        try:
            super()._setup_sigint()
            logger.debug("Signal handlers set up successfully")
        except NotImplementedError:
            logger.debug("Signal handlers not supported on this platform (Windows) - continuing without them")
        except Exception as e:
            logger.warning(f"Unexpected error setting up signal handlers: {e}")

# Custom processor to bridge Pipecat events to WebSocket
class WebSocketBridgeProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.bridge = bridge
        # State for selective audio-frame logging
        self._log_audio_after_response = False  # toggled when a Gemini text response is seen
        self._audio_log_count = 0
        self._audio_log_limit = 10  # log only the first N audio frames after response
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        # Call parent class method first
        await super().process_frame(frame, direction)
        
        # Forward relevant frames to WebSocket clients and manage selective audio logging
        from pipecat.frames.frames import AudioRawFrame  # Local import to avoid circular deps

        if isinstance(frame, TextFrame) and direction == FrameDirection.UPSTREAM:
            # Gemini has produced a text response (likely after function call)
            await self.bridge.on_response_text(frame.text)

            # Enable limited audio-frame logging for the upcoming TTS frames
            self._log_audio_after_response = True
            self._audio_log_count = 0
            logger.debug("WebSocketBridgeProcessor: Enabled audio-frame logging window after Gemini response")

        # Log only the first few AudioRawFrames after a Gemini response
        if isinstance(frame, AudioRawFrame) and self._log_audio_after_response:
            if self._audio_log_count < self._audio_log_limit:
                logger.debug(
                    f"AudioRawFrame #{self._audio_log_count + 1} | direction={direction.name} | samples={getattr(frame, 'num_samples', 'n/a')}"
                )
            self._audio_log_count += 1
            if self._audio_log_count >= self._audio_log_limit:
                self._log_audio_after_response = False
                logger.debug("WebSocketBridgeProcessor: Audio-frame logging window closed")
        
        # Always pass the frame through the pipeline
        await self.push_frame(frame, direction)

    async def handle_text_from_ui(self, user_text: str):
        """Handles text commands sent from the UI via WebSocket, pushing them into the pipeline."""
        logger.debug(f"WebSocketBridgeProcessor received text from UI: {user_text}")
        # Push the user's text as a TextFrame into the pipeline for LLM processing
        await self.push_frame(TextFrame(user_text), FrameDirection.DOWNSTREAM)
        logger.debug(f"Pushed TextFrame: '{user_text}' into pipeline from UI.")

# Audio gate processor for controlling audio flow
class AudioGateProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.enabled = False  # Start disabled
        logger.debug("AudioGateProcessor initialized - disabled by default")
    
    def enable(self):
        self.enabled = True
        logger.debug("AudioGateProcessor enabled")
    
    def disable(self):
        self.enabled = False
        logger.debug("AudioGateProcessor disabled")
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        from pipecat.frames.frames import AudioRawFrame
        
        # Always allow non-audio frames through
        if not isinstance(frame, AudioRawFrame):
            await self.push_frame(frame, direction)
            return
            
        # For audio frames, only pass through if enabled
        if self.enabled:
            await self.push_frame(frame, direction)
        # If disabled, just drop the audio frame (don't push it)

def create_function_schemas():
    """Create function schemas for voice assistant capabilities"""
    
    function_schemas = [
        # Task Management
        FunctionSchema(
            name="list_tasks",
            description="List all tasks or filter by status or due date",
            properties={
                "status": {
                    "type": "string",
                    "description": "Filter tasks by status: 'all', 'pending', 'completed', 'overdue'",
                    "enum": ["all", "pending", "completed", "overdue"]
                },
                "due_date": {
                    "type": "string", 
                    "description": "Filter tasks by due date (YYYY-MM-DD format) or relative dates like 'today', 'tomorrow'"
                }
            },
            required=[]
        ),
        
        # Reminder Management
        FunctionSchema(
            name="set_reminder",
            description="Set a reminder for a specific time or date",
            properties={
                "reminder_text": {
                    "type": "string",
                    "description": "The reminder message text"
                },
                "reminder_time": {
                    "type": "string",
                    "description": "When to remind (e.g., '2024-06-01 14:30', 'tomorrow at 3pm', 'in 30 minutes')"
                }
            },
            required=["reminder_text", "reminder_time"]
        ),
        
        # Timer Management
        FunctionSchema(
            name="start_timer",
            description="Start a countdown timer",
            properties={
                "duration_minutes": {
                    "type": "integer",
                    "description": "Timer duration in minutes"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description for what the timer is for"
                }
            },
            required=["duration_minutes"]
        ),
        
        # Note Taking
        FunctionSchema(
            name="take_note",
            description="Take a note, save a memo, or record information when user says 'take a note', 'make a note', 'remember this', 'jot this down', 'record this', 'note that', or similar note-taking requests",
            properties={
                "content": {
                    "type": "string",
                    "description": "The note content to save"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tags to categorize the note"
                }
            },
            required=["content"]
        ),
        
        # Goal Management
        FunctionSchema(
            name="create_goal",
            description="Create a new goal with target date",
            properties={
                "title": {
                    "type": "string",
                    "description": "The goal title or description"
                },
                "target_date": {
                    "type": "string",
                    "description": "Target completion date (YYYY-MM-DD format)"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the goal"
                },
                "category": {
                    "type": "string",
                    "description": "Goal category (personal, work, health, etc.)",
                    "enum": ["personal", "work", "health", "learning", "financial", "other"]
                }
            },
            required=["title", "target_date"]
        ),
        
        # Context Management
        FunctionSchema(
            name="get_status",
            description="Get current status of tasks, reminders, goals, or all items",
            properties={
                "type": {
                    "type": "string",
                    "description": "Type of status to get",
                    "enum": ["tasks", "reminders", "goals", "all"]
                }
            },
            required=[]
        ),
        
        FunctionSchema(
            name="get_current_window_context",
            description="Get information about the currently active window or browser tab for context-aware assistance",
            properties={},
            required=[]
        ),
        
        # Utility Functions
        FunctionSchema(
            name="get_current_time",
            description="Get the current time and date",
            properties={
                "timezone": {
                    "type": "string",
                    "description": "Timezone (e.g., 'UTC', 'America/New_York', 'local')"
                }
            },
            required=[]
        ),
        
        # Integration Functions
        
        FunctionSchema(
            name="create_calendar_event",
            description="Create a calendar event",
            properties={
                "event_data": {
                    "type": "object",
                    "description": "Event data including title, start/end times, description"
                }
            },
            required=["event_data"]
        ),
        
        FunctionSchema(
            name="get_integration_status",
            description="Get the status of available integrations (Google Workspace only)",
            properties={},
            required=[]
        ),
        
        # Google Workspace Functions
        FunctionSchema(
            name="create_google_task",
            description="Create a new Google Task in the user's Google Tasks",
            properties={
                "task_name": {
                    "type": "string",
                    "description": "The name/title of the task to create"
                },
                "due_date": {
                    "type": "string",
                    "description": "Optional due date for the task (YYYY-MM-DD format or relative like 'tomorrow')"
                },
                "priority": {
                    "type": "string",
                    "description": "Task priority level",
                    "enum": ["low", "medium", "high"]
                },
                "list_name": {
                    "type": "string",
                    "description": "The Google Tasks list to add the task to (defaults to 'My Tasks')"
                }
            },
            required=["task_name"]
        ),
        
        FunctionSchema(
            name="list_google_tasks",
            description="List Google Tasks from the user's Google Tasks account",
            properties={
                "tasklist_id": {
                    "type": "string",
                    "description": "The ID of the task list to retrieve tasks from (defaults to @default)"
                }
            },
            required=[]
        ),
        
        FunctionSchema(
            name="create_google_calendar_event",
            description="Create a new event in Google Calendar",
            properties={
                "summary": {
                    "type": "string",
                    "description": "Event title/summary"
                },
                "start_time": {
                    "type": "string",
                    "description": "Event start time (ISO format or natural language)"
                },
                "end_time": {
                    "type": "string",
                    "description": "Event end time (ISO format or natural language)"
                },
                "description": {
                    "type": "string",
                    "description": "Event description"
                },
                "location": {
                    "type": "string",
                    "description": "Event location"
                }
            },
            required=["summary", "start_time", "end_time"]
        ),
        
        FunctionSchema(
            name="list_google_calendar_events",
            description="List upcoming Google Calendar events",
            properties={
                "time_min": {
                    "type": "string",
                    "description": "Start time for event listing (ISO format)"
                },
                "time_max": {
                    "type": "string",
                    "description": "End time for event listing (ISO format)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of events to return"
                }
            },
            required=[]
        ),
        
        FunctionSchema(
            name="upload_to_google_drive",
            description="Upload a file to Google Drive",
            properties={
                "file_path": {
                    "type": "string",
                    "description": "Local path to the file to upload"
                },
                "file_name": {
                    "type": "string",
                    "description": "Name for the file in Google Drive"
                },
                "folder_id": {
                    "type": "string",
                    "description": "Google Drive folder ID (optional)"
                }
            },
            required=["file_path", "file_name"]
        ),
        
        FunctionSchema(
            name="create_google_doc",
            description="Create a new Google Document",
            properties={
                "title": {
                    "type": "string",
                    "description": "Document title"
                },
                "content": {
                    "type": "string",
                    "description": "Initial document content"
                }
            },
            required=["title"]
        )
    ]
    
    # Create function name to schema mapping for easy lookup
    function_mapping = {schema.name: schema for schema in function_schemas}
    
    return function_schemas, function_mapping

# Global server reference for cleanup
websocket_server = None

async def cleanup_and_shutdown():
    """Cleanup resources and shutdown gracefully"""
    logger.info("Starting graceful shutdown...")
    
    # Close WebSocket server
    global websocket_server
    if websocket_server:
        logger.info("Closing WebSocket server...")
        websocket_server.close()
        await websocket_server.wait_closed()
        logger.info("WebSocket server closed")
    
    # Close all WebSocket connections
    if bridge.clients:
        logger.info(f"Closing {len(bridge.clients)} WebSocket connections...")
        for client in bridge.clients.copy():
            await client.close()
        bridge.clients.clear()
        logger.info("All WebSocket connections closed")
    
    logger.info("Graceful shutdown completed")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    # Create a new event loop for cleanup if needed
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule cleanup in the running loop
            loop.create_task(cleanup_and_shutdown())
            # Give some time for cleanup
            loop.call_later(2.0, lambda: sys.exit(0))
        else:
            # Run cleanup in a new loop
            asyncio.run(cleanup_and_shutdown())
            sys.exit(0)
    except Exception as e:
        logger.error(f"Error during signal handling: {e}")
        sys.exit(1)

# Define a function to create and run the pipeline
async def main():
    logger.info("Starting Pipecat pipeline with Gemini function calling and WebSocket bridge...")
    
    # Set up signal handlers for graceful shutdown
    if sys.platform != 'win32':
        # Unix-like systems
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("Signal handlers registered for SIGINT and SIGTERM")
    else:
        # Windows - only SIGINT (Ctrl+C) is supported
        signal.signal(signal.SIGINT, signal_handler)
        logger.info("Signal handler registered for SIGINT (Ctrl+C)")

    # Configure Audio Transport - simple setup like previous version
    transport_params = LocalAudioTransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    )
    transport = LocalAudioTransport(transport_params)

    # Create audio gate (starts disabled)
    audio_gate = AudioGateProcessor()

    # Initialize function implementations
    task_functions = TaskFunctions()
    reminder_functions = ReminderFunctions()
    timer_functions = TimerFunctions()
    note_functions = NoteFunctions()
    goal_functions = GoalFunctions()
    context_functions = ContextFunctions()
    utility_functions = UtilityFunctions()

    google_workspace_functions = GoogleWorkspaceFunctions()

    # Create function schemas using the previous version's approach
    function_schemas_list, _ = create_function_schemas()
    
    # Convert FunctionSchema objects to tools for Gemini
    tools = ToolsSchema(standard_tools=function_schemas_list)
    
    # Create initial context messages
    initial_messages = [{
        "role": "system",
        "content": """You are a helpful voice assistant that can manage tasks, reminders, timers, notes, and goals. 
        
Your primary goal is to assist the user conversationally. Only call functions when the user explicitly requests an action that matches a function's description. Do NOT proactively suggest or call functions without a clear user intent. If a user's request is ambiguous, ask for clarification before attempting to call a function.

Examples of when you MUST call functions:
- "Create a Google task" → call create_google_task
- "List my Google tasks" → call list_google_tasks  
- "Set a reminder" → call set_reminder
- "Start a timer" → call start_timer
- "Take a note" → call take_note

You MUST use the provided function_declarations for ANY request that matches their descriptions.

When formatting function results, follow these templates:

For task listing results:
- If no tasks: "You currently have no tasks in that list."
- If 1 task: "You have 1 task: [task_title]"
- If 2-5 tasks: "You have [count] tasks: [task1], [task2], etc."
- If >5 tasks: "You have [count] tasks. The first 5 are: [list], and [remaining_count] more."

For task creation results:
- Success: "I've successfully created the task '[task_name]' for you."
- Failure: "I couldn't create that task. [error_message]"
        
Keep responses brief and natural for speech. Confirm actions clearly after function completion."""
    }]

    # Create LLM context without tools (tools go directly to Gemini service)
    context = OpenAILLMContext(messages=initial_messages)
    
    # GEMINI SERVICE with Function Calling using new API
    gemini_service = GeminiMultimodalLiveLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="models/gemini-2.0-flash-live-001",
        voice_id="Puck",
        tools=tools,  # Pass tools directly to the service
        inference_on_context_initialization=False,  # Disable automatic greeting
        input_params=InputParams(
            language=Language.EN_US,
            modalities=GeminiMultimodalModalities.AUDIO,
            enable_automatic_punctuation=True,
        )
    )
    
    # Create context aggregator for proper conversation handling
    context_aggregator = gemini_service.create_context_aggregator(context)

    # Register function handlers using the NEW FunctionCallParams API
    async def handle_list_tasks(params: FunctionCallParams):
        logger.info(f"=== handle_list_tasks called with new API ===")
        logger.info(f"Function: {params.function_name}")
        logger.info(f"Args: {params.arguments}")
        
        result = await task_functions.list_tasks(
            params.arguments.get('status', 'all'), 
            params.arguments.get('due_date')
        )
        await params.result_callback(result)

    async def handle_set_reminder(params: FunctionCallParams):
        logger.info(f"=== handle_set_reminder called with new API ===")
        result = await reminder_functions.set_reminder(
            params.arguments.get('reminder_text'), 
            params.arguments.get('reminder_time')
        )
        await params.result_callback(result)

    async def handle_start_timer(params: FunctionCallParams):
        logger.info(f"=== handle_start_timer called with new API ===")
        result = await timer_functions.start_timer(
            params.arguments.get('duration_minutes'), 
            params.arguments.get('description')
        )
        await params.result_callback(result)

    async def handle_take_note(params: FunctionCallParams):
        logger.info(f"=== handle_take_note called with new API ===")
        result = await note_functions.take_note(
            params.arguments.get('content'), 
            params.arguments.get('tags', [])
        )
        await params.result_callback(result)

    async def handle_create_goal(params: FunctionCallParams):
        logger.info(f"=== handle_create_goal called with new API ===")
        result = await goal_functions.create_goal(
            params.arguments.get('title'), 
            params.arguments.get('target_date'), 
            params.arguments.get('description', ''), 
            params.arguments.get('category', 'personal')
        )
        await params.result_callback(result)

    async def handle_get_status(params: FunctionCallParams):
        logger.info(f"=== handle_get_status called with new API ===")
        result = await context_functions.get_status(params.arguments.get('type', 'all'))
        await params.result_callback(f"Status: {result['message']}")

    async def handle_get_current_window_context(params: FunctionCallParams):
        logger.info(f"=== handle_get_current_window_context called with new API ===")
        result = await context_functions.get_current_window_context()
        if result.get('success'):
            context_info = result.get('context', {})
            if context_info.get('is_browser') and context_info.get('context_url'):
                await params.result_callback(f"Current browser context: {context_info.get('context_title', 'Unknown page')} at {context_info.get('context_url')}")
            else:
                await params.result_callback(f"Current window: {context_info.get('window_title', 'Unknown')} ({context_info.get('process_name', 'Unknown process')})")
        else:
            await params.result_callback(f"Context capture failed: {result.get('message', 'Unknown error')}")

    async def handle_get_current_time(params: FunctionCallParams):
        logger.info(f"=== handle_get_current_time called with new API ===")
        result = await utility_functions.get_current_time(params.arguments.get('timezone', 'local'))
        await params.result_callback(result)

    # Integration function handlers with new API
    
    async def handle_create_calendar_event(params: FunctionCallParams):
        logger.info(f"=== handle_create_calendar_event called with new API ===")
        result = {"success": False, "message": "Calendar event creation via legacy integrations is no longer supported. Use Google Calendar integration instead."}
        await params.result_callback(result)
    
    async def handle_get_integration_status(params: FunctionCallParams):
        logger.info(f"=== handle_get_integration_status called with new API ===")
        result = {"success": True, "integrations": {"google_workspace": "active"}, "message": "Only Google Workspace integration is available"}
        await params.result_callback(result)
    
    # Google Workspace function handlers with new API
    async def handle_create_google_task(params: FunctionCallParams):
        logger.info(f"=== GOOGLE TASKS: handle_create_google_task called with new API ===")
        logger.info(f"Function: {params.function_name}")
        logger.info(f"Args: {params.arguments}")
        
        try:
            task_name = params.arguments.get('task_name', 'Untitled Task')
            due_date = params.arguments.get('due_date')
            priority = params.arguments.get('priority', 'medium')
            list_name = params.arguments.get('list_name', 'My Tasks')
            
            logger.info(f"Creating Google task: task_name='{task_name}', due_date='{due_date}', list_name='{list_name}'")
            
            result = await google_workspace_functions.create_google_task(
                task_name=task_name,
                due_date=due_date, 
                priority=priority,
                list_id=list_name  # Changed from list_name to list_id
            )
            logger.info(f"Google Tasks API result: {result}")
            
            # Return result for the LLM to format
            await params.result_callback(result)
                
        except Exception as e:
            logger.error(f"Exception in handle_create_google_task: {e}", exc_info=True)
            error_response = {
                "success": False,
                "error": True,
                "message": f"There was an error trying to create your task: {str(e)}"
            }
            await params.result_callback(error_response)
    
    async def handle_list_google_tasks(params: FunctionCallParams):
        logger.info(f"=== GOOGLE TASKS: handle_list_google_tasks called with new API ===")
        logger.info(f"Function: {params.function_name}")
        logger.info(f"Args: {params.arguments}")
        
        try:
            list_id = params.arguments.get('tasklist_id', '@default')
            
            result = await google_workspace_functions.list_google_tasks(
                list_id=list_id,
                status_filter="all" 
            )
            logger.info(f"Google Tasks API result: {result}")
            
            # Return result for the LLM to format
            await params.result_callback(result)
            
        except Exception as e:
            logger.error(f"Exception in handle_list_google_tasks: {e}", exc_info=True)
            error_response = {
                "success": False,
                "error": True,
                "task_count": 0,
                "tasks": [],
                "message": f"There was an error trying to list your tasks: {str(e)}"
            }
            await params.result_callback(error_response)
    
    async def handle_create_google_calendar_event(params: FunctionCallParams):
        logger.info(f"=== handle_create_google_calendar_event called with new API ===")
        result = await google_workspace_functions.create_calendar_event(
            params.arguments.get('summary'), 
            params.arguments.get('start_time'), 
            params.arguments.get('end_time'), 
            params.arguments.get('description', ''), 
            params.arguments.get('location', '')
        )
        await params.result_callback(result)
    
    async def handle_list_google_calendar_events(params: FunctionCallParams):
        logger.info(f"=== handle_list_google_calendar_events called with new API ===")
        # Reverting to positional arguments as the keyword argument 'time_min' caused an unexpected error,
        # despite the function definition appearing to accept it. This suggests a runtime discrepancy.
        result = await google_workspace_functions.list_google_calendar_events(
            params.arguments.get('time_min'), 
            params.arguments.get('time_max'), 
            params.arguments.get('max_results', 10) # Defaulting max_results here as well
        )
        await params.result_callback(result)
    
    async def handle_upload_to_google_drive(params: FunctionCallParams):
        logger.info(f"=== handle_upload_to_google_drive called with new API ===")
        result = await google_workspace_functions.upload_to_drive(
            params.arguments.get('file_path'), 
            params.arguments.get('file_name'), 
            params.arguments.get('folder_id')
        )
        await params.result_callback(result)
    
    async def handle_create_google_doc(params: FunctionCallParams):
        logger.info(f"=== handle_create_google_doc called with new API ===")
        result = await google_workspace_functions.create_google_doc(
            params.arguments.get('title'), 
            params.arguments.get('content', '')
        )
        await params.result_callback(result)

    # Register all functions with the service using the NEW API
    gemini_service.register_function("list_tasks", handle_list_tasks)
    gemini_service.register_function("set_reminder", handle_set_reminder)
    gemini_service.register_function("start_timer", handle_start_timer)
    gemini_service.register_function("take_note", handle_take_note)
    gemini_service.register_function("create_goal", handle_create_goal)
    gemini_service.register_function("get_status", handle_get_status)
    gemini_service.register_function("get_current_window_context", handle_get_current_window_context)
    gemini_service.register_function("get_current_time", handle_get_current_time)
    
    # Integration functions
    gemini_service.register_function("create_calendar_event", handle_create_calendar_event)
    gemini_service.register_function("get_integration_status", handle_get_integration_status)
    
    # Google Workspace functions
    gemini_service.register_function("create_google_task", handle_create_google_task)
    gemini_service.register_function("list_google_tasks", handle_list_google_tasks)
    gemini_service.register_function("create_google_calendar_event", handle_create_google_calendar_event)
    gemini_service.register_function("list_google_calendar_events", handle_list_google_calendar_events)
    gemini_service.register_function("upload_to_google_drive", handle_upload_to_google_drive)
    gemini_service.register_function("create_google_doc", handle_create_google_doc)

    # Create WebSocket bridge processor
    websocket_processor = WebSocketBridgeProcessor()
    bridge.set_text_input_handler(websocket_processor.handle_text_from_ui)

    logger.info("Creating pipeline with proper context aggregation...")
    # Create the pipeline with proper context aggregation
    pipeline = Pipeline([
        transport.input(),           # Transport input (audio from mic)
        context_aggregator.user(),   # User context aggregation (CRITICAL for function calling)
        gemini_service,              # Gemini LLM with function calling
        transport.output(),          # Transport output (audio to speakers)
        context_aggregator.assistant(),  # Assistant context aggregation (CRITICAL for function calling)
        websocket_processor,         # WebSocket bridge (for UI communication)
    ])

    # Create pipeline parameters
    params = PipelineParams(
        allow_interruptions=True,
        enable_metrics=True,
        enable_usage_metrics=True,
    )

    # Create and run pipeline task
    runner = WindowsCompatiblePipelineRunner()
    task = PipelineTask(pipeline, params=params)

    # Enable audio gate and start WebSocket server
    audio_gate.enable()
    
    # Start WebSocket bridge server in the background
    global websocket_server
    websocket_server = await start_websocket_bridge()
    
    # Add transcription observer for debugging
    transcription_observer = TranscriptionLogObserver()
    task.add_observer(transcription_observer)

    logger.info("🎙️ Voice assistant ready with function calling support!")
    logger.info("Say 'list my Google tasks' or 'create a Google task' to test function calling")
    logger.info("Press Ctrl+C to shutdown gracefully")
    
    try:
        await runner.run(task)
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down...")
        await cleanup_and_shutdown()
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        await cleanup_and_shutdown()
        raise
    finally:
        await cleanup_and_shutdown()

# if __name__ == "__main__":
#     asyncio.run(main())
