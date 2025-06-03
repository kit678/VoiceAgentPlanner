import asyncio
import sys
import os

# Add the parent directory (src) to sys.path to allow imports from other packages like 'auth'
# This assumes the script is in voice-assistant/src/auth/
# and google_oauth.py is in voice-assistant/src/auth/
# and credential_manager.py is in voice-assistant/src/auth/
# Adjust if your structure is different.
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir) # This should be the 'src' directory
sys.path.insert(0, src_dir)

from auth.google_oauth import GoogleOAuthManager # Adjusted import path
from utils.logger import logger # Assuming logger is in src/utils

async def main():
    """Performs the Google OAuth logout operation."""
    try:
        # The client_secrets_path will be resolved by GoogleOAuthManager default constructor
        # to voice-assistant/config/google_client_secrets.json
        oauth_manager = GoogleOAuthManager()
        success = await oauth_manager.logout()
        
        if success:
            logger.info("Logout script: Logout successful.")
            print("{\"success\": true}") # Output JSON for Electron to parse
        else:
            logger.error("Logout script: Logout failed.")
            print("{\"success\": false, \"error\": \"Logout operation failed in Python script.\"}")
            sys.exit(1) # Indicate failure with a non-zero exit code
            
    except Exception as e:
        logger.error(f"Logout script: An error occurred: {e}")
        # Ensure to print JSON even on unexpected error for Electron to handle gracefully
        print(f"{{\"success\": false, \"error\": \"An unexpected error occurred: {str(e).replace('"', '\\\"')}\"}}")
        sys.exit(1) # Indicate failure

if __name__ == "__main__":
    # Ensure the script is run from a context where it can find its modules.
    # The CWD for execFile in main.js is set to src/auth, which should be fine.
    asyncio.run(main())