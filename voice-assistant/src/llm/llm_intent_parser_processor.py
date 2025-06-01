# voice-assistant/src/llm/llm_intent_parser_processor.py
from pipecat.frames.frames import Frame, TextFrame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
from loguru import logger
import json
import os
from typing import Dict, Any, Tuple

# Import the IntentFrame from the original processor
from .intent_parser_processor import IntentFrame
from .gemini_intent_service import GeminiIntentService

class LLMIntentParserFrameProcessor(FrameProcessor):
    """LLM-based intent parser that uses Gemini to identify intents and extract parameters"""
    
    def __init__(self, gemini_service: GeminiMultimodalLiveLLMService = None):
        super().__init__()
        
        # Create dedicated Gemini intent service for classification
        self.gemini_intent_service = GeminiIntentService()
        
        # Keep reference to main Gemini service if provided (for potential future use)
        self.main_gemini_service = gemini_service
        
        logger.info("LLMIntentParserFrameProcessor initialized with Gemini intent service")
    
    def _get_intent_system_prompt(self) -> str:
        """System prompt for intent classification and parameter extraction"""
        return """
You are an intent classification system for a voice assistant. Your job is to analyze user input and return structured JSON with the intent and extracted parameters.

Supported intents:
- greet: General greetings
- create_task: Creating tasks or todos
- set_reminder: Setting reminders
- start_timer: Starting timers or countdowns
- take_note: Taking notes or writing things down
- create_goal: Creating goals or objectives
- get_time: Asking for current time
- get_status: Asking for status of tasks, goals, etc.
- unknown_intent: When the intent is unclear

For each intent, extract relevant parameters:

**create_task:**
- task_name: The task description
- due_date: When the task is due (extract dates, times)
- priority: high, medium, low (infer from urgency words)
- category: work, personal, etc. (if mentioned)

**set_reminder:**
- reminder_text: What to be reminded about
- reminder_time: When to remind (extract dates, times)
- recurring: true/false (if it's a recurring reminder)

**start_timer:**
- duration_minutes: Timer duration in minutes
- description: What the timer is for

**take_note:**
- content: The note content
- category: If a category is mentioned

**create_goal:**
- goal_name: The goal description
- target_date: When to achieve the goal
- category: personal, professional, etc.

**get_status:**
- type: tasks, goals, reminders, timers, or all

Always respond with valid JSON in this format:
{
  "intent": "intent_name",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  },
  "confidence": 0.95,
  "reasoning": "Brief explanation of why this intent was chosen"
}

If you're unsure, use "unknown_intent" with lower confidence.
Always include the original_text in parameters.
"""
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process transcription frames to extract intents using LLM"""
        
        # Process transcription frames to extract intents
        if isinstance(frame, TranscriptionFrame):
            text = frame.text.strip()
            logger.debug(f"LLM processing transcription: {text}")
            
            try:
                # Use Gemini intent service to classify intent and extract parameters
                intent, parameters, confidence = await self.gemini_intent_service.classify_intent(text)
                
                # Create and push an IntentFrame
                intent_frame = IntentFrame(intent, parameters, frame.text, confidence)
                logger.info(f"Creating IntentFrame: {intent} (confidence: {confidence:.2f})")
                await self.push_frame(intent_frame, direction)
                logger.info(f"IntentFrame pushed downstream")
                
            except Exception as e:
                logger.error(f"Error in LLM intent classification: {e}")
                # Fallback to unknown intent
                fallback_frame = IntentFrame(
                    "unknown_intent", 
                    {"original_text": text, "error": str(e)}, 
                    frame.text, 
                    0.1
                )
                await self.push_frame(fallback_frame, direction)
        else:
            # Pass through other frames that aren't transcription frames
            await self.push_frame(frame, direction)
            
        # Call parent process_frame to complete the processing
        await super().process_frame(frame, direction)
    
    def set_gemini_service(self, service: GeminiMultimodalLiveLLMService):
        """Set the main Gemini service reference (for potential future use)"""
        self.main_gemini_service = service
        logger.info("Updated main Gemini service reference for LLM intent parsing")