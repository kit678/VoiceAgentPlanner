#!/usr/bin/env python3
import asyncio
import sys
import os
from dotenv import load_dotenv
from loguru import logger

from pipecat.frames.frames import Frame, TextFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.pipeline.pipeline import Pipeline # Removed FunctionImplementation
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
from functions.integration_functions import IntegrationFunctions
from functions.google_workspace_functions import GoogleWorkspaceFunctions

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'), override=True)

# Simple logging setup like the previous version
logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

# Custom processor to bridge Pipecat events to WebSocket
class WebSocketBridgeProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.bridge = bridge
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        # Call parent class method first
        await super().process_frame(frame, direction)
        
        # Forward relevant frames to WebSocket clients
        if isinstance(frame, TextFrame):
            if direction == FrameDirection.UPSTREAM:
                # This is a response from LLM (Gemini) after function execution
                await self.bridge.on_response_text(frame.text)
        
        # Always pass the frame through the pipeline
        await self.push_frame(frame, direction)

    async def handle_text_from_ui(self, user_text: str):
        """Handles text commands sent from the UI via WebSocket, pushing them into the pipeline."""
        logger.debug(f"WebSocketBridgeProcessor received text from UI: {user_text}")
        # Push the user's text as a TextFrame into the pipeline for LLM processing
        await self.push_frame(TextFrame(user_text), FrameDirection.DOWNSTREAM)
        logger.debug(f"Pushed TextFrame: '{user_text}' into pipeline from UI.")

# Audio gate processor that can enable/disable audio flow
class AudioGateProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self._is_enabled = False
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        # Call parent class method first (required by Pipecat)
        await super().process_frame(frame, direction)
        
        # Import frame types here to avoid circular imports
        from pipecat.frames.frames import AudioRawFrame, SystemFrame
        
        # Always pass non-audio frames through (like system control frames)
        if self._is_enabled or not isinstance(frame, AudioRawFrame):
            await self.push_frame(frame, direction)
        else:
            # Audio gate is closed - drop audio frames but log occasionally
            if hasattr(self, '_drop_count'):
                self._drop_count += 1
                if self._drop_count % 100 == 0:  # Log every 100 dropped frames
                    logger.debug(f"Audio gate: Dropped {self._drop_count} audio frames")
            else:
                self._drop_count = 1
                logger.debug("Audio gate: Started dropping audio frames")
    
    async def enable(self):
        """Enable audio flow"""
        if not self._is_enabled:
            logger.info("Audio gate: ENABLED - Audio will flow through")
            self._is_enabled = True
            if hasattr(self, '_drop_count'):
                logger.info(f"Audio gate: Stopped dropping audio frames (dropped {self._drop_count} total)")
                delattr(self, '_drop_count')
            
    async def disable(self):
        """Disable audio flow"""
        if self._is_enabled:
            logger.info("Audio gate: DISABLED - Audio will be blocked")
            self._is_enabled = False
            
    @property
    def is_enabled(self):
        return self._is_enabled

def create_function_schemas():
    all_schemas = [
        # Task management functions - TEMPORARILY DISABLED FOR GOOGLE TASKS TESTING
        # FunctionSchema(
        #     name="create_task",
        #     description="Create a new task with local storage (use this for general task requests unless user specifically mentions 'Google task')",
        #     properties={
        #         "task_name": {"type": "string", "description": "The name or description of the task"},
        #         "due_date": {"type": "string", "description": "The due date for the task (YYYY-MM-DD format or natural language like 'tomorrow', 'next week')"},
        #         "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "The priority level of the task"},
        #     },
        #     required=["task_name", "due_date"],
        # ),
        FunctionSchema(
            name="list_tasks",
            description="List all tasks, optionally filtered by status or due date",
            properties={
                "status": {"type": "string", "enum": ["pending", "completed", "all"], "description": "Filter tasks by status"},
                "due_date": {"type": "string", "description": "Filter tasks by due date (YYYY-MM-DD format or natural language)"},
            },
            required=[],
        ),
        
        # Reminder functions
        FunctionSchema(
            name="set_reminder",
            description="Set a reminder for a specific time",
            properties={
                "reminder_text": {"type": "string", "description": "The text content of the reminder"},
                "reminder_time": {"type": "string", "description": "When to trigger the reminder (time format or natural language like 'in 30 minutes', 'tomorrow at 9 AM')"},
            },
            required=["reminder_text", "reminder_time"],
        ),
        
        # Timer functions
        FunctionSchema(
            name="start_timer",
            description="Start a timer for a specified duration",
            properties={
                "duration_minutes": {"type": "number", "description": "Duration of the timer in minutes"},
                "description": {"type": "string", "description": "Optional description or label for the timer"},
            },
            required=["duration_minutes"],
        ),
        
        # Note functions
        FunctionSchema(
            name="take_note",
            description="Create a new note with content and optional tags",
            properties={
                "content": {"type": "string", "description": "The content of the note"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags for categorizing the note"},
            },
            required=["content"],
        ),
        
        # Goal functions
        FunctionSchema(
            name="create_goal",
            description="Create a new goal with a target date",
            properties={
                "title": {"type": "string", "description": "The title or name of the goal"},
                "target_date": {"type": "string", "description": "The target date for achieving the goal (YYYY-MM-DD format or natural language)"},
                "description": {"type": "string", "description": "Optional detailed description of the goal"},
                "category": {"type": "string", "description": "Optional category for the goal (e.g., 'personal', 'work', 'health')"},
            },
            required=["title", "target_date"],
        ),
        
        # Context functions
        FunctionSchema(
            name="get_status",
            description="Get the current status of tasks, reminders, goals, or all",
            properties={
                "type": {"type": "string", "enum": ["tasks", "reminders", "goals", "all"], "description": "The type of status information to retrieve"},
            },
            required=[],
        ),
        FunctionSchema(
            name="get_current_window_context",
            description="Get information about the currently active window and browser context",
            properties={},
            required=[],
        ),
        
        # Utility functions
        FunctionSchema(
            name="get_current_time",
            description="Get the current date and time",
            properties={
                "timezone": {"type": "string", "description": "Optional timezone specification (defaults to local time)"},
            },
            required=[],
        ),
        
        # Integration functions
        FunctionSchema(
            name="sync_with_trello",
            description="Sync task data with Trello via Zapier webhook",
            properties={
                "task_data": {"type": "object", "description": "Task data to sync with Trello"},
            },
            required=["task_data"],
        ),
        FunctionSchema(
            name="sync_with_notion",
            description="Sync goal data with Notion via Zapier webhook",
            properties={
                "goal_data": {"type": "object", "description": "Goal data to sync with Notion"},
            },
            required=["goal_data"],
        ),
        FunctionSchema(
            name="create_calendar_event",
            description="Create a calendar event in Google Calendar via Zapier webhook",
            properties={
                "event_data": {"type": "object", "description": "Calendar event data including title, start_time, end_time, description"},
            },
            required=["event_data"],
        ),
        FunctionSchema(
            name="get_integration_status",
            description="Get the status of external integrations (Trello, Notion, Google Calendar)",
            properties={},
            required=[],
        ),
        
        # Google Workspace functions
        FunctionSchema(
            name="create_google_task",
            description="Create a new task directly in Google Tasks (when user specifically mentions 'Google task' or 'Google Tasks')",
            properties={
                "title": {"type": "string", "description": "The title of the task"},
                "notes": {"type": "string", "description": "Optional notes or description for the task"},
                "due_date": {"type": "string", "description": "Optional due date for the task (ISO format or natural language)"},
            },
            required=["title"],
        ),
        FunctionSchema(
            name="list_google_tasks",
            description="List tasks from Google Tasks",
            properties={
                "tasklist_id": {"type": "string", "description": "Optional task list ID (defaults to @default)"},
                "max_results": {"type": "number", "description": "Maximum number of tasks to return (default: 10)"},
            },
            required=[],
        ),
        FunctionSchema(
            name="create_google_calendar_event",
            description="Create a new event in Google Calendar",
            properties={
                "summary": {"type": "string", "description": "The title/summary of the event"},
                "start_time": {"type": "string", "description": "Start time of the event (ISO format)"},
                "end_time": {"type": "string", "description": "End time of the event (ISO format)"},
                "description": {"type": "string", "description": "Optional description of the event"},
                "location": {"type": "string", "description": "Optional location of the event"},
            },
            required=["summary", "start_time", "end_time"],
        ),
        FunctionSchema(
            name="list_google_calendar_events",
            description="List events from Google Calendar",
            properties={
                "time_min": {"type": "string", "description": "Optional minimum time to list events from (ISO format)"},
                "time_max": {"type": "string", "description": "Optional maximum time to list events to (ISO format)"},
                "max_results": {"type": "number", "description": "Maximum number of events to return (default: 10)"},
            },
            required=[],
        ),
        FunctionSchema(
            name="upload_to_google_drive",
            description="Upload a file to Google Drive",
            properties={
                "file_path": {"type": "string", "description": "Local path to the file to upload"},
                "file_name": {"type": "string", "description": "Name for the file in Google Drive"},
                "folder_id": {"type": "string", "description": "Optional Google Drive folder ID to upload to"},
            },
            required=["file_path", "file_name"],
        ),
        FunctionSchema(
            name="create_google_doc",
            description="Create a new Google Document",
            properties={
                "title": {"type": "string", "description": "The title of the document"},
                "content": {"type": "string", "description": "Optional initial content for the document"},
            },
            required=["title"],
        ),
    ]
    return all_schemas, []

# Define a function to create and run the pipeline
async def main():
    logger.info("Starting Pipecat pipeline with Gemini function calling and WebSocket bridge...")

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
    integration_functions = IntegrationFunctions()
    google_workspace_functions = GoogleWorkspaceFunctions()

    # Create function schemas using the previous version's approach
    function_schemas_list, _ = create_function_schemas()
    
    # Convert FunctionSchema objects to Gemini-compatible function declaration dictionaries
    function_declarations = []
    for schema in function_schemas_list:
        function_declaration = {
            "name": schema.name,
            "description": schema.description,
            "parameters": {
                "type": "object",  # Ensure lowercase for JSON schema type
                "properties": schema.properties
            }
        }
        if schema.required: 
            function_declaration["parameters"]["required"] = schema.required
        function_declarations.append(function_declaration)

    # Create tools structure exactly as Google's API expects
    tools = [{
        "function_declarations": function_declarations
    }]

    # GEMINI SERVICE with Function Calling - using previous version's approach
    gemini_service = GeminiMultimodalLiveLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="models/gemini-2.0-flash-live-001",
        voice_id="Puck",
        transcribe_user_audio=True,
        system_instruction="""You are a helpful voice assistant that can manage tasks, reminders, timers, notes, and goals. 
        
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
        
Keep responses brief and natural for speech. Confirm actions clearly after function completion.""",
        tools=tools,  # Use the properly structured tools
        input_params=InputParams(
            language=Language.EN_US,
            modalities=GeminiMultimodalModalities.AUDIO,
            enable_automatic_punctuation=True,
        )
    )

    # Register function handlers using the previous version's approach
    async def handle_list_tasks(function_name, tool_call_id, args, llm, context, result_callback):
        result = await task_functions.list_tasks(args.get('status', 'all'), args.get('due_date'))
        await result_callback(result)

    async def handle_set_reminder(function_name, tool_call_id, args, llm, context, result_callback):
        result = await reminder_functions.set_reminder(args.get('reminder_text'), args.get('reminder_time'))
        await result_callback(result)

    async def handle_start_timer(function_name, tool_call_id, args, llm, context, result_callback):
        result = await timer_functions.start_timer(args.get('duration_minutes'), args.get('description'))
        await result_callback(result)

    async def handle_take_note(function_name, tool_call_id, args, llm, context, result_callback):
        result = await note_functions.take_note(args.get('content'), args.get('tags', []))
        await result_callback(result)

    async def handle_create_goal(function_name, tool_call_id, args, llm, context, result_callback):
        result = await goal_functions.create_goal(args.get('title'), args.get('target_date'), args.get('description', ''), args.get('category', 'personal'))
        await result_callback(result)

    async def handle_get_status(function_name, tool_call_id, args, llm, context, result_callback):
        result = await context_functions.get_status(args.get('type', 'all'))
        await result_callback(f"Status: {result['message']}")

    async def handle_get_current_window_context(function_name, tool_call_id, args, llm, context, result_callback):
        result = await context_functions.get_current_window_context()
        if result.get('success'):
            context_info = result.get('context', {})
            if context_info.get('is_browser') and context_info.get('context_url'):
                await result_callback(f"Current browser context: {context_info.get('context_title', 'Unknown page')} at {context_info.get('context_url')}")
            else:
                await result_callback(f"Current window: {context_info.get('window_title', 'Unknown')} ({context_info.get('process_name', 'Unknown process')})")
        else:
            await result_callback(f"Context capture failed: {result.get('message', 'Unknown error')}")

    async def handle_get_current_time(function_name, tool_call_id, args, llm, context, result_callback):
        result = await utility_functions.get_current_time(args.get('timezone', 'local'))
        await result_callback(result)

    # Integration function handlers
    async def handle_sync_with_trello(function_name, tool_call_id, args, llm, context, result_callback):
        result = await integration_functions.sync_with_trello(args.get('task_data'))
        await result_callback(result)
    
    async def handle_sync_with_notion(function_name, tool_call_id, args, llm, context, result_callback):
        result = await integration_functions.sync_with_notion(args.get('goal_data'))
        await result_callback(result)
    
    async def handle_create_calendar_event(function_name, tool_call_id, args, llm, context, result_callback):
        result = await integration_functions.create_calendar_event(args.get('event_data'))
        await result_callback(result)
    
    async def handle_get_integration_status(function_name, tool_call_id, args, llm, context, result_callback):
        result = await integration_functions.get_integration_status()
        await result_callback(result)
    
    # Google Workspace function handlers - updated to match current Google function implementations
    async def handle_create_google_task(function_name, tool_call_id, args, llm, context, result_callback):
        logger.info(f"=== GOOGLE TASKS: handle_create_google_task called ===")
        logger.info(f"Function args: {args}")
        
        try:
            task_name = args.get('title') or args.get('task_name', 'Untitled Task')
            due_date = args.get('due_date')
            priority = args.get('priority', 'medium')
            list_name = args.get('list_name', 'My Tasks')
            
            logger.info(f"Creating Google task: task_name='{task_name}', due_date='{due_date}', list_name='{list_name}'")
            
            result = await google_workspace_functions.create_google_task(
                task_name=task_name,
                due_date=due_date, 
                priority=priority,
                list_name=list_name
            )
            logger.info(f"Google Tasks API result: {result}")
            
            # Return raw data dictionary for the LLM to format
            if result.get("success"):
                formatted_result = {
                    "success": True,
                    "task_name": task_name,
                    "message": result.get("message", f"Successfully created task: {task_name}"),
                    "details": result.get("task_details", {})
                }
            else:
                formatted_result = {
                    "success": False,
                    "task_name": task_name,
                    "message": result.get("message", f"Failed to create task: {task_name}"),
                    "error_details": result.get("error", None)
                }
            
            await result_callback(formatted_result)
                
        except Exception as e:
            logger.error(f"Exception in handle_create_google_task: {e}", exc_info=True)
            error_response = {
                "success": False,
                "error": True,
                "message": f"There was an error trying to create your task: {str(e)}"
            }
            await result_callback(error_response)
    
    async def handle_list_google_tasks(function_name, tool_call_id, args, llm, context, result_callback):
        logger.info(f"=== GOOGLE TASKS: handle_list_google_tasks called ===")
        logger.info(f"Function args: {args}")
        
        try:
            list_id = args.get('tasklist_id', '@default')
            
            result = await google_workspace_functions.list_google_tasks(
                list_id=list_id,
                status_filter="all" 
            )
            logger.info(f"Google Tasks API result: {result}")
            
            # Return raw data dictionary for the LLM to format
            if result.get("success"):
                count = result.get("count", 0)
                tasks_data = result.get("tasks", [])
                
                formatted_result = {
                    "success": True,
                    "task_count": count,
                    "tasks": [{
                        "title": task.get('title', 'Untitled Task'),
                        "id": task.get('id', ''),
                        "status": task.get('status', 'needsAction')
                    } for task in tasks_data],
                    "list_id": list_id
                }
            else:
                formatted_result = {
                    "success": False,
                    "task_count": 0,
                    "tasks": [],
                    "message": result.get("message", "Sorry, I couldn't list your tasks right now."),
                    "error_details": result.get("error", None)
                }
            
            await result_callback(formatted_result)
            
        except Exception as e:
            logger.error(f"Exception in handle_list_google_tasks: {e}", exc_info=True)
            error_response = {
                "success": False,
                "error": True,
                "task_count": 0,
                "tasks": [],
                "message": f"There was an error trying to list your tasks: {str(e)}"
            }
            await result_callback(error_response)
    
    async def handle_create_google_calendar_event(function_name, tool_call_id, args, llm, context, result_callback):
        result = await google_workspace_functions.create_calendar_event(
            args.get('summary'), args.get('start_time'), args.get('end_time'), 
            args.get('description', ''), args.get('location', '')
        )
        await result_callback(result)
    
    async def handle_list_google_calendar_events(function_name, tool_call_id, args, llm, context, result_callback):
        result = await google_workspace_functions.list_calendar_events(
            args.get('time_min'), args.get('time_max'), args.get('max_results', 10)
        )
        await result_callback(result)
    
    async def handle_upload_to_google_drive(function_name, tool_call_id, args, llm, context, result_callback):
        result = await google_workspace_functions.upload_to_drive(
            args.get('file_path'), args.get('file_name'), args.get('folder_id')
        )
        await result_callback(result)
    
    async def handle_create_google_doc(function_name, tool_call_id, args, llm, context, result_callback):
        result = await google_workspace_functions.create_google_doc(
            args.get('title'), args.get('content', '')
        )
        await result_callback(result)

    # Register all functions with the service using the previous version's approach
    gemini_service.register_function("list_tasks", handle_list_tasks)
    gemini_service.register_function("set_reminder", handle_set_reminder)
    gemini_service.register_function("start_timer", handle_start_timer)
    gemini_service.register_function("take_note", handle_take_note)
    gemini_service.register_function("create_goal", handle_create_goal)
    gemini_service.register_function("get_status", handle_get_status)
    gemini_service.register_function("get_current_window_context", handle_get_current_window_context)
    gemini_service.register_function("get_current_time", handle_get_current_time)
    
    # Register integration functions
    gemini_service.register_function("sync_with_trello", handle_sync_with_trello)
    gemini_service.register_function("sync_with_notion", handle_sync_with_notion)
    gemini_service.register_function("create_calendar_event", handle_create_calendar_event)
    gemini_service.register_function("get_integration_status", handle_get_integration_status)
    
    # Register Google Workspace functions
    gemini_service.register_function("create_google_task", handle_create_google_task)
    gemini_service.register_function("list_google_tasks", handle_list_google_tasks)
    gemini_service.register_function("create_google_calendar_event", handle_create_google_calendar_event)
    gemini_service.register_function("list_google_calendar_events", handle_list_google_calendar_events)
    gemini_service.register_function("upload_to_google_drive", handle_upload_to_google_drive)
    gemini_service.register_function("create_google_doc", handle_create_google_doc)

    # Create WebSocket bridge processor
    websocket_processor = WebSocketBridgeProcessor()

    # SIMPLIFIED PIPELINE like the previous version - no monitoring processors
    # Audio/Text Input -> Audio Gate -> Gemini (STT + Function Calling + TTS) -> WebSocket Bridge -> Audio Output
    pipeline = Pipeline([
        transport.input(),          # Audio input from microphone
        audio_gate,                 # Audio gate (controllable)
        gemini_service,             # Gemini: STT, Function Calling, TTS
        websocket_processor,        # Bridges frames to/from WebSocket for Electron UI
        transport.output()          # Audio output to speakers
    ])

    # Attach audio gate to pipeline for WebSocket control
    pipeline.audio_gate = audio_gate
    
    # Connect pipeline and text input handler to bridge
    bridge.set_pipeline(pipeline)
    bridge.set_text_input_handler(websocket_processor.handle_text_from_ui)

    runner_params = {}
    if sys.platform == "win32":
        logger.info("Disabling PipelineRunner SIGINT handling on Windows.")
        runner_params["handle_sigint"] = False

    runner = PipelineRunner(**runner_params)
    logger.info("Starting pipeline: Audio -> Gemini Live (with Functions) -> WebSocket Bridge -> Audio")
    
    task = PipelineTask(
        pipeline,
        params=PipelineParams(allow_interruptions=True, enable_metrics=True),
        observers=[TranscriptionLogObserver()]
    )
    
    # Define async functions to run concurrently
    async def run_websocket_server():
        """Run the WebSocket server and keep it alive"""
        logger.info("Starting WebSocket server...")
        server = await start_websocket_bridge()
        logger.info("WebSocket server started and serving on localhost:8765")
        
        # Print BACKEND_READY signal for main.js to detect
        print("BACKEND_READY", flush=True)
        logger.info("BACKEND_READY signal sent to main process")
        
        # Keep the server alive by waiting for it to close
        try:
            await server.wait_closed()
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")
        finally:
            logger.info("WebSocket server has stopped")
    
    async def run_pipeline():
        """Run the Pipecat pipeline"""
        logger.info("Starting Pipecat pipeline...")
        await runner.run(task)
    
    try:
        # Run both WebSocket server and pipeline concurrently using gather
        logger.info("Starting WebSocket server and pipeline concurrently...")
        await asyncio.gather(
            run_websocket_server(),
            run_pipeline(),
            return_exceptions=True
        )
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            logger.debug("WindowsSelectorEventLoopPolicy set.")
        except Exception as e:
            logger.warning(f"Could not set WindowsSelectorEventLoopPolicy: {e}")
    
    try:
        logger.debug(f"Current asyncio event loop policy: {type(asyncio.get_event_loop_policy()).__name__}")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user (KeyboardInterrupt).")
    except Exception as e:
        logger.error(f"An error occurred: {type(e).__name__} - {repr(e)}")
        import traceback
        logger.error(traceback.format_exc())
