#!/usr/bin/env python3
"""
Debug script to test audio input and gate functionality
"""

import asyncio
import websockets
import json
import sys
import os
from loguru import logger

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_websocket_connection():
    """Test WebSocket connection and audio gate control"""
    uri = "ws://localhost:8765"
    
    try:
        logger.info("Connecting to WebSocket server...")
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Send start listening command
            start_message = {
                "type": "start_listening",
                "data": {
                    "timestamp": 1234567890
                }
            }
            
            logger.info("Sending start_listening command...")
            await websocket.send(json.dumps(start_message))
            logger.info("start_listening command sent")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"Received response: {response}")
            except asyncio.TimeoutError:
                logger.warning("No response received within 5 seconds")
            
            # Wait a bit then send stop listening
            await asyncio.sleep(2)
            
            stop_message = {
                "type": "stop_listening",
                "data": {
                    "timestamp": 1234567890
                }
            }
            
            logger.info("Sending stop_listening command...")
            await websocket.send(json.dumps(stop_message))
            logger.info("stop_listening command sent")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"Received response: {response}")
            except asyncio.TimeoutError:
                logger.warning("No response received within 5 seconds")
                
    except Exception as e:
        logger.error(f"WebSocket connection failed: {e}")
        return False
    
    return True

async def main():
    logger.info("Starting audio debug test...")
    
    # Test WebSocket connection
    success = await test_websocket_connection()
    
    if success:
        logger.info("WebSocket test completed successfully")
    else:
        logger.error("WebSocket test failed")
        
if __name__ == "__main__":
    asyncio.run(main())