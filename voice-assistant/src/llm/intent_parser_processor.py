# voice-assistant/src/llm/intent_parser_processor.py
from pipecat.frames.frames import Frame, TextFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.frames.frames import Frame, TextFrame, SystemFrame, TranscriptionFrame, InterimTranscriptionFrame

# Potentially a new Frame type for intents
class IntentFrame(Frame):
    def __init__(self, intent: str, parameters: dict, original_text: str):
        super().__init__()
        self.intent = intent
        self.parameters = parameters
        self.original_text = original_text

    def __str__(self):
        return f"IntentFrame(intent='{self.intent}', parameters={self.parameters}, original_text='{self.original_text}')"

class IntentParserFrameProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        # Initialize any necessary models or configurations for intent parsing
        # This might be an LLM client, a local NLP model, etc.
        print("IntentParserFrameProcessor initialized")

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction) # Important to call super

        if isinstance(frame, TextFrame) and direction == FrameDirection.DOWNSTREAM:
            # Assuming TextFrame from STT (e.g., Gemini's transcription output)
            # or a TextFrame explicitly pushed for intent parsing.
            user_text = frame.text
            print(f"IntentParserFrameProcessor received TextFrame: {user_text}")

            # Improved intent parsing logic
            parsed_intent = "unknown"
            parameters = {}

            user_text_lower = user_text.lower()

            if "hello" in user_text_lower or "hi" in user_text_lower or "hey" in user_text_lower:
                parsed_intent = "greet"
            elif "create task" in user_text_lower or "add task" in user_text_lower or "new task" in user_text_lower:
                parsed_intent = "create_task"
                # Try to extract description more robustly
                if "create task to " in user_text_lower:
                    task_description = user_text_lower.split("create task to ", 1)[-1].strip()
                elif "create task " in user_text_lower:
                    task_description = user_text_lower.split("create task ", 1)[-1].strip()
                elif "add task to " in user_text_lower:
                    task_description = user_text_lower.split("add task to ", 1)[-1].strip()
                elif "add task " in user_text_lower:
                    task_description = user_text_lower.split("add task ", 1)[-1].strip()
                elif "new task to " in user_text_lower:
                    task_description = user_text_lower.split("new task to ", 1)[-1].strip()
                elif "new task " in user_text_lower:
                    task_description = user_text_lower.split("new task ", 1)[-1].strip()
                else:
                    task_description = user_text_lower # Fallback, less precise
                
                # Remove potential leading "to" if it's part of the description due to splitting
                if task_description.startswith("to "):
                    task_description = task_description[3:]
                
                parameters = {"description": task_description.strip() if task_description else "unspecified task"}
            elif "what time is it" in user_text_lower or "current time" in user_text_lower:
                parsed_intent = "get_time"
            
            # Create and push an IntentFrame
            intent_frame = IntentFrame(
                intent=parsed_intent,
                parameters=parameters,
                original_text=user_text
            )
            print(f"Pushing IntentFrame: {intent_frame}")
            await self.push_frame(intent_frame, FrameDirection.DOWNSTREAM)
        else:
            # Pass through other frames or handle as needed
            await self.push_frame(frame, direction)