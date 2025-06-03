# Placeholder script: submit_auth_code_script.py
import sys
import asyncio
import os

# Adjust Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir)) # Add 'src' to path

from auth.google_oauth import GoogleOAuthManager

async def main():
    if len(sys.argv) < 2:
        print("FAILURE: No auth code provided")
        return

    auth_code = sys.argv[1]
    manager = GoogleOAuthManager()
    try:
        success = await manager.handle_callback(auth_code, redirect_uri='http://localhost:8080/oauth/callback')
        if success:
            print("SUCCESS")
        else:
            print("FAILURE: Token exchange failed")
    except Exception as e:
        print(f"FAILURE: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())