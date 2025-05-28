from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.services.google.stt import GoogleSTTService
from pipecat.services.google.tts import GoogleTTSService
# DeepSeek integration removed - now using Gemini 2.0 Flash Live API
from pipecat.services.service import Service
from pipecat.frames.frames import Frame

class VoicePipeline:
    def __init__(self):
        # Initialize services
        self.stt = GoogleSTTService()
        # DeepSeek service removed - using Gemini Live API in main pipeline
        self.tts = GoogleTTSService()
        
        # Create pipeline
        self.pipeline = Pipeline([
            self.stt,       # Speech to Text
            # LLM Processing now handled by Gemini Live API
            self.tts        # Text to Speech
        ])
        
        # Create runner
        self.runner = PipelineRunner()

    async def start(self):
        """Start the pipeline with a task"""
        await self.runner.run(PipelineTask(self.pipeline))