# voice-assistant/src/utils/firestore_client.py
import firebase_admin
from firebase_admin import credentials, firestore
import os
from loguru import logger

# Path to your service account key file
# This should be set as an environment variable or handled securely
SERVICE_ACCOUNT_KEY_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

db = None

if SERVICE_ACCOUNT_KEY_PATH and os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info("Successfully initialized Firebase Admin SDK and Firestore client.")
    except Exception as e:
        logger.error(f"Error initializing Firebase Admin SDK or Firestore client: {e}")
else:
    logger.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable not set or file not found. Firestore client not initialized.")

def get_firestore_client():
    """Returns the initialized Firestore client."""
    if not db:
        logger.warning("Firestore client was not initialized. Returning None.")
    return db