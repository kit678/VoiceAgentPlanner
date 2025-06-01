# voice-assistant/src/llm/intent_parser_processor.py
from pipecat.frames.frames import Frame, TextFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.frames.frames import Frame, TextFrame, SystemFrame, TranscriptionFrame, InterimTranscriptionFrame
from llm.parameter_extractor import ParameterExtractor
from loguru import logger
import re

# Potentially a new Frame type for intents
class IntentFrame(Frame):
    def __init__(self, intent: str, parameters: dict, original_text: str, confidence: float = 1.0):
        super().__init__()
        self.intent = intent
        self.parameters = parameters
        self.original_text = original_text
        self.confidence = confidence

    def __str__(self):
        return f"IntentFrame(intent='{self.intent}', parameters={self.parameters}, original_text='{self.original_text}', confidence={self.confidence})"

class IntentParserFrameProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.parameter_extractor = ParameterExtractor()
        
        # Enhanced intent patterns with confidence scoring
        self.intent_patterns = {
            "greet": {
                "patterns": [r"\b(hello|hi|hey|good morning|good afternoon|good evening)\b"],
                "confidence": 0.9
            },
            "create_task": {
                "patterns": [
                    r"\b(create|add|new)\s+(task|todo|to-do)\b",
                    r"\b(remind me to|i need to|todo)\b",
                    r"\b(task to|add to my list)\b"
                ],
                "confidence": 0.8
            },
            "set_reminder": {
                "patterns": [
                    r"\b(remind me|set reminder|reminder)\b",
                    r"\b(don't forget|remember to)\b"
                ],
                "confidence": 0.8
            },
            "start_timer": {
                "patterns": [
                    r"\b(start|set)\s+(timer|countdown)\b",
                    r"\b(timer for|time me)\b",
                    r"\b(pomodoro|focus session)\b"
                ],
                "confidence": 0.8
            },
            "take_note": {
                "patterns": [
                    r"\b(take note|note|write down|remember)\b",
                    r"\b(jot down|make a note)\b"
                ],
                "confidence": 0.7
            },
            "create_goal": {
                "patterns": [
                    r"\b(create|set|new)\s+(goal|objective)\b",
                    r"\b(my goal is|i want to achieve)\b"
                ],
                "confidence": 0.7
            },
            "get_time": {
                "patterns": [
                    r"\b(what time|current time|time is it)\b",
                    r"\b(what's the time|tell me the time)\b"
                ],
                "confidence": 0.9
            },
            "get_status": {
                "patterns": [
                    r"\b(status|what's up|what do i have|my tasks)\b",
                    r"\b(show me|list my|what's on my)\b"
                ],
                "confidence": 0.6
            }
        }
        
        logger.info("IntentParserFrameProcessor initialized with enhanced pattern matching")

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        # Process transcription frames to extract intents
        if isinstance(frame, TranscriptionFrame):
            text = frame.text.lower().strip()
            logger.debug(f"Processing transcription: {text}")
            
            # Enhanced intent classification with parameter extraction
            intent, parameters, confidence = await self._parse_intent_with_parameters(text)
            
            # Create and push an IntentFrame with confidence
            intent_frame = IntentFrame(intent, parameters, frame.text, confidence)
            await self.push_frame(intent_frame, direction)
            
        # Pass through other frames
        await self.push_frame(frame, direction)
    
    async def _parse_intent_with_parameters(self, text: str):
        """Enhanced intent parsing with parameter extraction"""
        best_intent = "unknown_intent"
        best_confidence = 0.0
        best_parameters = {"original_text": text}
        
        # Check each intent pattern
        for intent_name, intent_config in self.intent_patterns.items():
            for pattern in intent_config["patterns"]:
                if re.search(pattern, text, re.IGNORECASE):
                    confidence = intent_config["confidence"]
                    if confidence > best_confidence:
                        best_intent = intent_name
                        best_confidence = confidence
                        
                        # Extract parameters based on intent type
                        parameters = await self._extract_parameters_for_intent(intent_name, text)
                        best_parameters = parameters
                        break
        
        logger.debug(f"Intent: {best_intent}, Confidence: {best_confidence}, Parameters: {best_parameters}")
        return best_intent, best_parameters, best_confidence
    
    async def _extract_parameters_for_intent(self, intent: str, text: str) -> dict:
        """Extract parameters specific to each intent type"""
        parameters = {}
        
        try:
            if intent == "create_task":
                # Extract task-specific parameters
                task_params = await self.parameter_extractor.extract_task_parameters(text)
                parameters.update(task_params)
                
            elif intent == "set_reminder":
                # Extract reminder-specific parameters
                reminder_params = await self.parameter_extractor.extract_reminder_parameters(text)
                parameters.update(reminder_params)
                
            elif intent == "start_timer":
                # Extract timer duration
                duration = await self.parameter_extractor.extract_duration(text)
                if duration:
                    parameters["duration_minutes"] = duration
                    
                # Extract timer description
                description = self._extract_timer_description(text)
                if description:
                    parameters["description"] = description
                    
            elif intent == "take_note":
                # Extract note content
                note_content = self._extract_note_content(text)
                if note_content:
                    parameters["content"] = note_content
                    
            elif intent == "create_goal":
                # Extract goal-specific parameters
                goal_params = await self.parameter_extractor.extract_goal_parameters(text)
                parameters.update(goal_params)
                
            elif intent == "get_status":
                # Extract status query type
                status_type = self._extract_status_type(text)
                if status_type:
                    parameters["type"] = status_type
                    
        except Exception as e:
            logger.error(f"Error extracting parameters for intent {intent}: {e}")
            parameters["extraction_error"] = str(e)
        
        # Always include original text for fallback
        parameters["original_text"] = text
        return parameters
    
    def _extract_timer_description(self, text: str) -> str:
        """Extract timer description from text"""
        # Remove timer trigger words and extract remaining description
        cleaned_text = text
        for phrase in ["start timer", "set timer", "timer for", "time me", "pomodoro", "focus session"]:
            cleaned_text = re.sub(rf"\b{re.escape(phrase)}\b", "", cleaned_text, flags=re.IGNORECASE)
        
        # Remove duration patterns
        cleaned_text = re.sub(r"\b\d+\s*(minutes?|mins?|hours?|hrs?)\b", "", cleaned_text, flags=re.IGNORECASE)
        
        return cleaned_text.strip() or "Focus session"
    
    def _extract_note_content(self, text: str) -> str:
        """Extract note content from text"""
        # Remove note trigger words
        cleaned_text = text
        for phrase in ["take note", "note", "write down", "remember", "jot down", "make a note"]:
            cleaned_text = re.sub(rf"\b{re.escape(phrase)}\b", "", cleaned_text, flags=re.IGNORECASE)
        
        return cleaned_text.strip()
    
    def _extract_status_type(self, text: str) -> str:
        """Extract status query type from text"""
        if "task" in text.lower():
            return "tasks"
        elif "goal" in text.lower():
            return "goals"
        elif "reminder" in text.lower():
            return "reminders"
        elif "timer" in text.lower():
            return "timers"
        else:
            return "all"