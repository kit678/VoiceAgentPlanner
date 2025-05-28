import asyncio
import sys
import os
from dotenv import load_dotenv
from loguru import logger

from pipecat.frames.frames import Frame, TextFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
from pipecat.observers.loggers.transcription_log_observer import TranscriptionLogObserver

# Import Gemini Multimodal Live service (replaces both DeepSeek LLM + Google TTS)
from pipecat.services.gemini_multimodal_live.gemini import (
    GeminiMultimodalLiveLLMService,
    InputParams,
    GeminiMultimodalModalities
)
from pipecat.transcriptions.language import Language

# Import WebSocket bridge
from websocket_server import bridge, start_websocket_bridge

# Import Frame Processors
from llm.intent_parser_processor import IntentParserFrameProcessor, IntentFrame
from llm.command_processor_processor import CommandProcessorFrameProcessor

load_dotenv(override=True)

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
            if direction == FrameDirection.DOWNSTREAM:
                # This could be a transcription from STT (Gemini) or other text sources.
                # If it's a direct transcription meant for UI display before intent parsing:
                # Consider if this should still be sent, or if UI only gets final responses.
                # For now, let's assume transcriptions are for intent parsing first.
                # await self.bridge.on_transcription(frame.text, is_final=True)
                pass # TextFrames from STT will go to IntentParserFrameProcessor
            elif direction == FrameDirection.UPSTREAM:
                # This is a response from LLM (Gemini) or CommandProcessorFrameProcessor
                await self.bridge.on_response_text(frame.text)
        elif isinstance(frame, IntentFrame) and direction == FrameDirection.DOWNSTREAM:
            # IntentFrames are handled by CommandProcessorFrameProcessor, not directly by UI bridge
            pass
        
        # Always pass the frame through the pipeline
        await self.push_frame(frame, direction)

    async def handle_text_from_ui(self, user_text: str):
        """Handles text commands sent from the UI via WebSocket, pushing them into the pipeline."""
        logger.debug(f"WebSocketBridgeProcessor received text from UI: {user_text}")
        # Push the user's text as a TextFrame into the pipeline for intent parsing
        # The direction is DOWNSTREAM as it's initiating a new processing sequence
        await self.push_frame(TextFrame(user_text), FrameDirection.DOWNSTREAM)
        logger.debug(f"Pushed TextFrame: '{user_text}' into pipeline from UI.")

    # The set_command_processor method is no longer needed as processing happens in pipeline.


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

async def main():
    logger.info("Starting Pipecat pipeline with Gemini Multimodal Live and WebSocket bridge...")

    # Start WebSocket server
    websocket_server = await start_websocket_bridge()
    logger.info("WebSocket bridge started on localhost:8765")

    # Configure Audio Transport
    transport_params = LocalAudioTransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    )
    transport = LocalAudioTransport(transport_params)

    # Create audio gate (starts disabled)
    audio_gate = AudioGateProcessor()

    # SINGLE SERVICE: Gemini handles BOTH LLM reasoning AND TTS
    gemini_service = GeminiMultimodalLiveLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="models/gemini-2.0-flash-live-001",  # Use the correct Live API model
        voice_id="Puck",  # Options: Aoede, Charon, Fenrir, Kore, Puck
        transcribe_user_audio=True,
        system_instruction="You are a helpful voice assistant. Keep responses brief and natural for speech. Avoid special characters that might cause audio issues.",
        params=InputParams(
            temperature=0.7,
            language=Language.EN_US,
            modalities=GeminiMultimodalModalities.AUDIO  # Output audio directly
        )
    )

    # Create Frame Processors
    intent_parser_fp = IntentParserFrameProcessor()
    command_processor_fp = CommandProcessorFrameProcessor()

    # Create WebSocket bridge processor
    websocket_processor = WebSocketBridgeProcessor()

    # REFACTORED PIPELINE:
    # Audio Input -> Audio Gate -> Gemini (STT) -> Intent Parser FP -> Command Processor FP -> Gemini (TTS) -> WebSocket Bridge -> Audio Output
    # Text Input (from UI) -> WebSocket Bridge -> Intent Parser FP -> Command Processor FP -> WebSocket Bridge (for text response)

    # Note: GeminiMultimodalLiveLLMService can produce TextFrame (from STT) and consume TextFrame (for TTS).
    # We need to ensure the flow is correct.
    # If Gemini STT outputs TextFrame, it goes to IntentParser.
    # If CommandProcessor outputs TextFrame (response), it should go to Gemini for TTS (if voice out) or WebSocketBridge (if text out).

    # For voice interactions:
    # Mic -> Gate -> Gemini (STT) -> [TextFrame] -> IntentParserFP -> [IntentFrame] -> CommandProcessorFP -> [TextFrame for TTS] -> Gemini (TTS) -> [AudioFrame] -> WebSocketBridge (for audio sync/info) -> Speakers
    # For text interactions (from UI):
    # UI Text -> WebSocketBridge (pushes TextFrame) -> IntentParserFP -> [IntentFrame] -> CommandProcessorFP -> [TextFrame for UI] -> WebSocketBridge (sends to UI)

    pipeline = Pipeline([
        transport.input(),          # Audio input from microphone
        audio_gate,                 # Audio gate (controllable)
        gemini_service,             # Gemini: STT (produces TextFrame), LLM, TTS (consumes TextFrame, produces AudioFrame)
        # After Gemini STT, TextFrame goes downstream
        intent_parser_fp,           # Consumes TextFrame, produces IntentFrame (downstream)
        command_processor_fp,       # Consumes IntentFrame, produces TextFrame (upstream for TTS/response)
        # The TextFrame from CommandProcessorFP needs to go to Gemini for TTS (if voice) or WebSocketBridge (if text).
        # Gemini service will handle TextFrames in UPSTREAM direction for TTS.
        # WebSocketBridge will handle TextFrames in UPSTREAM for UI text responses.
        websocket_processor,        # Bridges frames to/from WebSocket for Electron UI
        transport.output()          # Audio output to speakers
    ])

    # The WebSocketBridgeProcessor will now push TextFrames from the UI into the pipeline (downstream)
    # and send TextFrames from the pipeline (upstream) to the UI.
    # Gemini service will handle TextFrames from CommandProcessorFP (upstream) for TTS.

    # Attach audio gate to pipeline for WebSocket control
    pipeline.audio_gate = audio_gate
    
    # Connect pipeline and text input handler to bridge
    bridge.set_pipeline(pipeline)
    bridge.set_text_input_handler(websocket_processor.handle_text_from_ui) # Renamed for clarity

    runner_params = {}
    if sys.platform == "win32":
        logger.info("Disabling PipelineRunner SIGINT handling on Windows.")
        runner_params["handle_sigint"] = False

    runner = PipelineRunner(**runner_params)
    logger.info("Starting pipeline: Audio -> Gemini Live -> WebSocket Bridge -> Audio")
    
    task = PipelineTask(
        pipeline,
        params=PipelineParams(allow_interruptions=True, enable_metrics=True),
        observers=[TranscriptionLogObserver()]
    )
    
    try:
        await runner.run(task)
    finally:
        # Clean up WebSocket server
        websocket_server.close()
        await websocket_server.wait_closed()
        logger.info("WebSocket server closed")

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


class CommandProcessorFrameProcessor(FrameProcessor):
    async def process_frame(self, frame: Frame) -> AsyncGenerator[Frame, None]:
        if isinstance(frame, IntentFrame):
            # Extract parameters from parsed intent
            intent_type = frame.intent['type']
            params = frame.intent.get('params', {})

            # Handle task creation intent
            if intent_type == 'create_task':
                # Validate required parameters
                required = ['task_name', 'due_date']
                if all(param in params for param in required):
                    # Create Supabase task record
                    supabase_client = create_client(
                        os.getenv('SUPABASE_URL'),
                        os.getenv('SUPABASE_KEY'))
                    
                    task_data = {
                        'name': params['task_name'],
                        'due_date': params['due_date'],
                        'priority': params.get('priority', 'medium'),
                        'status': 'pending'
                    }
                    
                    try:
                        result = supabase_client.table('tasks').insert(task_data).execute()
                        yield TextFrame(f"Task created: {params['task_name']} due {params['due_date']}")
                    except Exception as e:
                        yield TextFrame("Failed to create task. Please try again.")
                else:
                    missing = [p for p in required if p not in params]
                    yield TextFrame(f"Please clarify: {', '.join(missing)}")
            # Add other intent handlers here
        
        await self.push_frame(frame)