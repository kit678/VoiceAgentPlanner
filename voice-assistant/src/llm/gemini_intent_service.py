# voice-assistant/src/llm/gemini_intent_service.py
import google.generativeai as genai
import json
import os
from typing import Dict, Any, Tuple
from loguru import logger

class GeminiIntentService:
    """Service for using Gemini API directly for intent classification"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Use Gemini Flash for fast intent classification
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=self._get_intent_system_prompt()
        )
        
        logger.info("GeminiIntentService initialized")
    
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

Examples:

Input: "Remind me to call mom at 3pm"
Output: {
  "intent": "set_reminder",
  "parameters": {
    "reminder_text": "call mom",
    "reminder_time": "3pm",
    "original_text": "Remind me to call mom at 3pm"
  },
  "confidence": 0.9,
  "reasoning": "Clear reminder request with specific time"
}

Input: "Create a task to finish the report by Friday"
Output: {
  "intent": "create_task",
  "parameters": {
    "task_name": "finish the report",
    "due_date": "Friday",
    "priority": "medium",
    "original_text": "Create a task to finish the report by Friday"
  },
  "confidence": 0.95,
  "reasoning": "Explicit task creation with clear description and deadline"
}

Input: "Start a 25 minute pomodoro session"
Output: {
  "intent": "start_timer",
  "parameters": {
    "duration_minutes": 25,
    "description": "pomodoro session",
    "original_text": "Start a 25 minute pomodoro session"
  },
  "confidence": 0.9,
  "reasoning": "Clear timer request with specific duration and purpose"
}
"""
    
    async def classify_intent(self, text: str) -> Tuple[str, Dict[str, Any], float]:
        """Classify intent and extract parameters using Gemini API"""
        
        try:
            # Prepare the prompt
            user_prompt = f"Classify this user input and extract parameters: \"{text}\""
            
            # Generate response using Gemini
            response = await self._generate_response(user_prompt)
            
            # Parse the JSON response
            response_data = json.loads(response)
            
            intent = response_data.get("intent", "unknown_intent")
            parameters = response_data.get("parameters", {})
            confidence = response_data.get("confidence", 0.5)
            
            # Always include original text
            parameters["original_text"] = text
            
            # Log reasoning if provided
            if "reasoning" in response_data:
                logger.debug(f"Gemini reasoning: {response_data['reasoning']}")
            
            logger.info(f"Intent classified: {intent} (confidence: {confidence:.2f})")
            return intent, parameters, confidence
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Raw response: {response}")
            return "unknown_intent", {"original_text": text, "parse_error": str(e)}, 0.1
        
        except Exception as e:
            logger.error(f"Error in Gemini intent classification: {e}")
            return "unknown_intent", {"original_text": text, "gemini_error": str(e)}, 0.1
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate response from Gemini API"""
        
        try:
            # Use the synchronous API for now - you can make it async if needed
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent classification
                    max_output_tokens=500,
                    response_mime_type="application/json"  # Request JSON response
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            raise
    
    def test_classification(self, test_inputs: list = None) -> None:
        """Test the intent classification with sample inputs"""
        
        if test_inputs is None:
            test_inputs = [
                "Hello there",
                "Create a task to buy groceries",
                "Remind me to call the doctor at 2pm",
                "Start a 15 minute timer",
                "Take a note that the meeting is moved to Thursday",
                "Set a goal to exercise 3 times a week",
                "What time is it?",
                "Show me my tasks",
                "This is unclear input that doesn't match any intent"
            ]
        
        logger.info("Testing Gemini intent classification...")
        
        for test_input in test_inputs:
            try:
                import asyncio
                intent, params, confidence = asyncio.run(self.classify_intent(test_input))
                logger.info(f"Input: '{test_input}'")
                logger.info(f"  -> Intent: {intent} (confidence: {confidence:.2f})")
                logger.info(f"  -> Parameters: {params}")
                print()
            except Exception as e:
                logger.error(f"Error testing input '{test_input}': {e}")

if __name__ == "__main__":
    # Test the service
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../../.env'))
    
    service = GeminiIntentService()
    service.test_classification()