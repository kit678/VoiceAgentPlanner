#!/usr/bin/env python
"""
Simple WebSocket server test to debug connection issues
"""
import asyncio
import websockets
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def echo_handler(websocket, path):
    """Simple echo handler for testing"""
    logger.info(f"Client connected from {websocket.remote_address}")
    try:
        async for message in websocket:
            logger.info(f"Received: {message}")
            # Echo the message back
            await websocket.send(f"Echo: {message}")
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Handler error: {e}")

async def start_test_server():
    """Start a test WebSocket server"""
    host = "localhost"
    port = 8765
    
    logger.info(f"Starting test WebSocket server on {host}:{port}")
    
    try:
        server = await websockets.serve(echo_handler, host, port)
        logger.info(f"WebSocket server successfully started and serving on {host}:{port}")
        
        # Keep server running
        await server.wait_closed()
        
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(start_test_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}") 