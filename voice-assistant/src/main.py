import asyncio
from llm.pipeline import VoicePipeline

async def main():
    pipeline = VoicePipeline()
    await pipeline.start()

if __name__ == "__main__":
    asyncio.run(main()) 