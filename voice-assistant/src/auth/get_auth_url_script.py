# Placeholder script: get_auth_url_script.py
import asyncio
import sys
import os

# Adjust the Python path to include the parent directory of 'auth'
# so that 'from ..google_oauth import GoogleOAuthManager' works.
# This assumes 'get_auth_url_script.py' is in 'src/auth/' and 'google_oauth.py' is in 'src/auth/'
# and 'CredentialManager' is also accessible or its module is in sys.path.
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir)) # Add 'src' to path

from auth.google_oauth import GoogleOAuthManager

async def main():
    manager = GoogleOAuthManager()
    # Ensure this redirect_uri matches what's in main.js and Google Cloud Console
    url = manager.initialize_flow(redirect_uri='http://localhost:8080/oauth/callback')
    print(url)

if __name__ == '__main__':
    asyncio.run(main())