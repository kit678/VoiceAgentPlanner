import asyncio
import websockets
import json
import logging
from typing import Dict, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MessageType(Enum):
    # From Electron to Pipecat
    START_LISTENING = "start_listening"
    STOP_LISTENING = "stop_listening"
    SEND_TEXT = "send_text"
    GET_STATUS = "get_status"
    
    # From Pipecat to Electron
    TRANSCRIPTION = "transcription"
    RESPONSE_TEXT = "response_text"
    AUDIO_STARTED = "audio_started"
    AUDIO_STOPPED = "audio_stopped"
    STATUS = "status"
    ERROR = "error"

@dataclass
class WebSocketMessage:
    type: str
    data: dict = None
    timestamp: float = None

class PipecatWebSocketBridge:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.pipecat_pipeline = None
        self.is_listening = False
        
    async def register_client(self, websocket):
        """Register a new WebSocket client (Electron frontend)"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send initial status
        await self.send_to_client(websocket, MessageType.STATUS, {
            "connected": True,
            "listening": self.is_listening,
            "pipeline_ready": self.pipecat_pipeline is not None
        })
        
    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
        
    async def send_to_client(self, websocket, message_type: MessageType, data: dict = None):
        """Send message to a specific client"""
        message = {
            "type": message_type.value,
            "data": data or {},
            "timestamp": asyncio.get_event_loop().time()
        }
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            await self.unregister_client(websocket)
            
    async def broadcast_to_clients(self, message_type: MessageType, data: dict = None):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
            
        message = {
            "type": message_type.value,
            "data": data or {},
            "timestamp": asyncio.get_event_loop().time()
        }
        
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
                
        # Clean up disconnected clients
        for client in disconnected:
            await self.unregister_client(client)
            
    async def handle_client_message(self, websocket, message_data):
        """Handle incoming messages from Electron frontend"""
        try:
            message = json.loads(message_data)
            msg_type = message.get("type")
            data = message.get("data", {})
            
            logger.info(f"Received message: {msg_type}")
            
            if msg_type == MessageType.START_LISTENING.value:
                await self.start_listening()
            elif msg_type == MessageType.STOP_LISTENING.value:
                await self.stop_listening()
            elif msg_type == MessageType.SEND_TEXT.value:
                text = data.get("text", "")
                await self.send_text_to_pipeline(text)
            elif msg_type == MessageType.GET_STATUS.value:
                await self.send_status(websocket)
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from client")
            await self.send_to_client(websocket, MessageType.ERROR, {
                "message": "Invalid JSON format"
            })
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            await self.send_to_client(websocket, MessageType.ERROR, {
                "message": str(e)
            })
            
    async def start_listening(self):
        """Start the Pipecat pipeline listening"""
        logger.info("[WEBSOCKET] START_LISTENING command received from frontend")
        if self.pipecat_pipeline and not self.is_listening:
            self.is_listening = True
            logger.info("[WEBSOCKET] Setting listening state to True")
            
            # Enable the audio gate to allow audio through
            if hasattr(self.pipecat_pipeline, 'audio_gate'):
                logger.info("[WEBSOCKET] Enabling audio gate to allow audio flow")
                await self.pipecat_pipeline.audio_gate.enable()
            else:
                logger.warning("[WEBSOCKET] No audio_gate found on pipecat_pipeline")
            
            await self.broadcast_to_clients(MessageType.STATUS, {
                "listening": True,
                "message": "Voice assistant is now listening"
            })
            logger.info("[WEBSOCKET] Sent LISTENING status to frontend clients")
        else:
            if not self.pipecat_pipeline:
                logger.warning("[WEBSOCKET] Cannot start listening - no pipecat_pipeline")
            elif self.is_listening:
                logger.info("[WEBSOCKET] Already listening - ignoring START_LISTENING command")
            
    async def stop_listening(self):
        """Stop the Pipecat pipeline listening"""
        logger.info("[WEBSOCKET] STOP_LISTENING command received from frontend")
        if self.is_listening:
            self.is_listening = False
            self._text_input_handler = None # Renamed from _command_handler
            logger.info("[WEBSOCKET] Setting listening state to False")
            
            # Disable the audio gate to block audio
            if hasattr(self.pipecat_pipeline, 'audio_gate'):
                logger.info("[WEBSOCKET] Disabling audio gate to block audio flow")
                await self.pipecat_pipeline.audio_gate.disable()
            else:
                logger.warning("[WEBSOCKET] No audio_gate found on pipecat_pipeline")
            
            await self.broadcast_to_clients(MessageType.STATUS, {
                "listening": False,
                "message": "Voice assistant stopped listening"
            })
            logger.info("[WEBSOCKET] Sent STOPPED LISTENING status to frontend clients")
        else:
            logger.info("[WEBSOCKET] Already not listening - ignoring STOP_LISTENING command")
            
    async def send_text_to_pipeline(self, text: str):
        """Send text input to the command handler in Pipecat pipeline"""
        if hasattr(self, '_text_input_handler') and self._text_input_handler:
            logger.info(f"Sending text to text input handler: {text}")
            await self._text_input_handler(text) # This now pushes to pipeline
        else:
            logger.warning("Text input handler not set. Cannot process text command.")
            await self.broadcast_to_clients(MessageType.ERROR, {
                "message": "Text input processing not available."
            })
            
    async def send_status(self, websocket):
        """Send current status to client"""
        await self.send_to_client(websocket, MessageType.STATUS, {
            "connected": True,
            "listening": self.is_listening,
            "pipeline_ready": self.pipecat_pipeline is not None,
            "clients_connected": len(self.clients)
        })
        
    # Methods to be called by Pipecat pipeline
    async def on_transcription(self, text: str, is_final: bool = False):
        """Called when Pipecat receives transcription"""
        await self.broadcast_to_clients(MessageType.TRANSCRIPTION, {
            "text": text,
            "is_final": is_final
        })
        
    async def on_response_text(self, text: str):
        """Called when Pipecat generates response text"""
        await self.broadcast_to_clients(MessageType.RESPONSE_TEXT, {
            "text": text,
            "source": "llm_response"
        })
        
    async def on_audio_started(self):
        """Called when Pipecat starts generating audio"""
        await self.broadcast_to_clients(MessageType.AUDIO_STARTED, {})
        
    async def on_audio_stopped(self):
        """Called when Pipecat stops generating audio"""
        await self.broadcast_to_clients(MessageType.AUDIO_STOPPED, {})
        
    def set_pipeline(self, pipeline):
        """Set the Pipecat pipeline reference"""
        self.pipecat_pipeline = pipeline
        logger.info("[WEBSOCKET] Pipecat pipeline connected to WebSocket bridge")
        
        # Check if the pipeline has an audio gate
        if hasattr(pipeline, 'audio_gate'):
            logger.info(f"[WEBSOCKET] Audio gate found on pipeline: {type(pipeline.audio_gate).__name__}")
            logger.info(f"[WEBSOCKET] Audio gate initial state: {'ENABLED' if pipeline.audio_gate.is_enabled else 'DISABLED'}")
        else:
            logger.warning("[WEBSOCKET] No audio_gate attribute found on registered pipeline")
            logger.info(f"[WEBSOCKET] Pipeline attributes: {[attr for attr in dir(pipeline) if not attr.startswith('_')]}")

    def set_text_input_handler(self, handler_coroutine):
        """Set the coroutine to handle text commands from the UI."""
        self._text_input_handler = handler_coroutine
        logger.info("Text input handler connected to WebSocket bridge")
        
    async def client_handler(self, websocket, path):
        """Handle WebSocket client connections with improved error handling"""
        client_id = id(websocket)
        logger.info(f"WebSocket client {client_id} connected from {websocket.remote_address}")
        
        try:
            # Register the client first
            await self.register_client(websocket)
            
            # Handle incoming messages
            async for message in websocket:
                await self.handle_client_message(websocket, message)
            
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket client {client_id} disconnected normally")
        except Exception as e:
            logger.error(f"Error handling WebSocket client {client_id}: {e}")
        finally:
            # Unregister the client
            await self.unregister_client(websocket)
            logger.info(f"WebSocket client {client_id} cleaned up")

    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        try:
            server = await websockets.serve(
                self.client_handler,
                self.host,
                self.port
            )
            logger.info(f"WebSocket server successfully bound to {self.host}:{self.port}")
            return server
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            raise

# Global bridge instance
bridge = PipecatWebSocketBridge()

async def start_websocket_bridge():
    """Start the WebSocket bridge server"""
    logger.info("Attempting to start WebSocket bridge...")
    try:
        server = await bridge.start_server()
        logger.info("WebSocket server is now serving on localhost:8765")
        return server
    except Exception as e:
        logger.error(f"Failed to start WebSocket bridge: {e}")
        raise