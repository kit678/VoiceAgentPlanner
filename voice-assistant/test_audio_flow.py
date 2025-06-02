#!/usr/bin/env python3
"""
Test script to check audio flow through the pipeline
"""

import asyncio
import websockets
import json
import time
from loguru import logger

async def test_audio_flow():
    """Test if audio frames flow through when gate is enabled"""
    uri = "ws://localhost:8765"
    
    try:
        logger.info("Connecting to WebSocket server...")
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Send start listening command
            start_message = {
                "type": "start_listening",
                "data": {
                    "timestamp": int(time.time())
                }
            }
            
            logger.info("Sending start_listening command...")
            await websocket.send(json.dumps(start_message))
            logger.info("start_listening command sent")
            
            # Wait for status response
            response = await websocket.recv()
            logger.info(f"Received response: {response}")
            
            # Listen for any incoming messages for 10 seconds
            logger.info("Listening for audio processing messages for 10 seconds...")
            logger.info("Please speak into your microphone now!")
            
            end_time = time.time() + 10
            message_count = 0
            
            while time.time() < end_time:
                try:
                    # Check for incoming messages with short timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    message_count += 1
                    logger.info(f"Message {message_count}: {message}")
                except asyncio.TimeoutError:
                    # No message received, continue listening
                    continue
            
            # Send stop listening command
            stop_message = {
                "type": "stop_listening",
                "data": {
                    "timestamp": int(time.time())
                }
            }
            
            logger.info("Sending stop_listening command...")
            await websocket.send(json.dumps(stop_message))
            
            # Wait for final response
            response = await websocket.recv()
            logger.info(f"Final response: {response}")
            
            if message_count == 0:
                logger.warning("No audio processing messages received - audio input may not be working")
            else:
                logger.info(f"Received {message_count} messages - audio processing appears to be working")
                
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_audio_flow())