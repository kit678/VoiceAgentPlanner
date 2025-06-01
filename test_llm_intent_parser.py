#!/usr/bin/env python3
"""
Test script for LLM-based intent parsing

This script demonstrates the new LLM-based intent parser that uses Gemini
for intent classification and parameter extraction, replacing the rule-based approach.
"""

import asyncio
import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Add the src directory to the path
import sys
sys.path.append('voice-assistant/src')

from llm.llm_intent_parser_processor import LLMIntentParserFrameProcessor
from pipecat.frames.frames import TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

class TestFrameCollector(FrameProcessor):
    """Simple frame collector to capture output frames"""
    
    def __init__(self):
        super().__init__()
        self.frames = []
    
    async def process_frame(self, frame, direction=FrameDirection.DOWNSTREAM):
        logger.info(f"TestFrameCollector received frame: {type(frame).__name__}")
        await super().process_frame(frame, direction)
        self.frames.append(frame)
        logger.info(f"Collected frame: {type(frame).__name__} (total: {len(self.frames)})")
        if hasattr(frame, 'intent'):
            logger.info(f"  Intent: {frame.intent}")
            logger.info(f"  Parameters: {frame.parameters}")
            logger.info(f"  Confidence: {frame.confidence}")

async def test_llm_intent_parser():
    """Test the LLM-based intent parser with various inputs"""
    
    logger.info("Testing LLM Intent Parser")
    
    # Create the LLM intent parser
    intent_parser = LLMIntentParserFrameProcessor()
    
    # Create a frame collector to capture outputs
    collector = TestFrameCollector()
    
    # Connect the parser to the collector
    intent_parser.link(collector)
    
    # Test cases
    test_inputs = [
        "Create a task to buy groceries",
        "Set a reminder for my meeting at 3 PM",
        "Start a timer for 10 minutes",
        "Take a note about the project deadline",
        "Create a goal to exercise daily",
        "What time is it?",
        "Hello there",
        "Can you help me with something?",
        "Schedule a meeting with John tomorrow",
        "Add milk to my shopping list"
    ]
    
    logger.info(f"Testing {len(test_inputs)} different inputs...")
    
    for i, text in enumerate(test_inputs, 1):
        logger.info(f"\n--- Test {i}: '{text}' ---")
        
        # Clear previous frames
        initial_frame_count = len(collector.frames)
        
        # Create a transcription frame
        frame = TranscriptionFrame(text, "user_id", timestamp=None)
        
        # Process the frame
        try:
            await intent_parser.process_frame(frame, FrameDirection.DOWNSTREAM)
            
            # Check if we got new frames
            new_frame_count = len(collector.frames)
            if new_frame_count > initial_frame_count:
                # Find the new intent frame
                for new_frame in collector.frames[initial_frame_count:]:
                    if hasattr(new_frame, 'intent'):
                        logger.success(f"✅ Successfully classified: {new_frame.intent} (confidence: {new_frame.confidence:.2f})")
                        break
                else:
                    logger.warning("⚠️ New frames collected but no intent frame found")
            else:
                logger.warning("⚠️ No new frames collected")
                
        except Exception as e:
            logger.error(f"❌ Error processing '{text}': {e}")
    
    logger.info(f"\n=== Test Summary ===")
    logger.info(f"Total frames collected: {len(collector.frames)}")
    
    # Show summary of results
    intent_counts = {}
    for frame in collector.frames:
        if hasattr(frame, 'intent'):
            intent = frame.intent
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    logger.info("Intent distribution:")
    for intent, count in intent_counts.items():
        logger.info(f"  {intent}: {count}")

async def test_gemini_intent_service():
    """Test the Gemini intent service directly"""
    
    logger.info("\nTesting Gemini Intent Service directly...")
    
    try:
        from llm.gemini_intent_service import GeminiIntentService
        
        service = GeminiIntentService()
        
        test_text = "Create a task to buy groceries"
        logger.info(f"Testing with: '{test_text}'")
        
        intent, parameters, confidence = await service.classify_intent(test_text)
        
        logger.success(f"✅ Direct service test successful:")
        logger.info(f"  Intent: {intent}")
        logger.info(f"  Parameters: {parameters}")
        logger.info(f"  Confidence: {confidence}")
        
    except Exception as e:
        logger.error(f"❌ Direct service test failed: {e}")

def main():
    """Main test function"""
    
    # Check for required environment variables
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("❌ GOOGLE_API_KEY environment variable not set")
        logger.info("Please set your Google API key in the .env file")
        return
    
    logger.info("🚀 Starting LLM Intent Parser Tests")
    
    # Run the tests
    asyncio.run(test_gemini_intent_service())
    asyncio.run(test_llm_intent_parser())
    
    logger.info("🏁 Tests completed")

if __name__ == "__main__":
    main()