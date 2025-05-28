import os
from google.cloud import speech

def test_google_stt_permissions():
    """Tests Google STT API permissions with current credentials."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    print(f"[TEST SCRIPT] Using GOOGLE_APPLICATION_CREDENTIALS: {creds_path}")

    if not creds_path:
        print("[TEST SCRIPT] ERROR: GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
        return
    
    if not os.path.exists(creds_path):
        print(f"[TEST SCRIPT] ERROR: Credential file NOT FOUND at: {creds_path}")
        return

    try:
        client = speech.SpeechClient()

        # This is a dummy config and audio, the goal is to trigger the API call
        # that requires the 'speech.recognizers.recognize' permission.
        # We don't need actual audio data for this permission test.
        # A more complex call would involve config and audio data.
        # This simple call to recognize implicitly checks credentials and permissions
        # when the client tries to interact with the service endpoint.
        # For a direct permission check on a specific recognizer, one might use
        # client.get_recognizer(name="projects/your-project/locations/global/recognizers/_dontexist_")
        # but that requires knowing a recognizer path. A general client instantiation
        # and a simple operation is often enough to trigger auth checks.

        # A more direct way to test the recognize permission might be to list recognizers
        # or attempt a simple, non-streaming recognition, though these also need permissions.
        # Let's try a very basic call that interacts with the service.
        # The client constructor itself can sometimes perform initial auth checks.
        
        print("[TEST SCRIPT] SpeechClient initialized successfully.")
        print("[TEST SCRIPT] Attempting to list recognizers (requires 'speech.recognizers.list')...")
        
        # Note: Your service account might not have a default project set up in a way
        # that `client.list_recognizers(parent=f"projects/{project_id}/locations/global")`
        # would work without specifying the project_id.
        # The core test is whether the API call is attempted and what auth error occurs.
        
        # Let's try to make a call that usually triggers permission checks during its setup phase
        # or initial communication with the service.
        # The following is a very lightweight call, but should involve auth.
        # A dummy streaming_recognize call, even without sending audio,
        # will try to establish a connection.
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )
        streaming_config = speech.StreamingRecognitionConfig(config=config)
        
        print("[TEST SCRIPT] Attempting to initiate a streaming recognize call (requires 'speech.recognizers.recognize')...")
        # We don't need to send audio, just initiate the call
        responses = client.streaming_recognize(config=streaming_config, requests=(iter(()))) # Empty iterator

        print("[TEST SCRIPT] Streaming recognize call initiated (or at least didn't fail on auth immediately).")
        print("[TEST SCRIPT] To fully test, this might need to iterate responses, but an immediate 403 would show here.")
        # Consume the generator to see if an error is raised during the API call itself
        for response in responses:
            pass # We don't care about the response, just if an error occurs

        print("[TEST SCRIPT] Permissions appear to be OK if no error by this point after iterating responses.")

    except Exception as e:
        print(f"[TEST SCRIPT] AN ERROR OCCURRED: {type(e).__name__} - {e}")

if __name__ == "__main__":
    # Ensure .env is loaded if you use it for GOOGLE_APPLICATION_CREDENTIALS
    from dotenv import load_dotenv
    load_dotenv(override=True) 
    print("[TEST SCRIPT] .env loaded (if present)")
    test_google_stt_permissions() 