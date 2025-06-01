- [x] **Firebase Project Setup**: Create a Firebase project, enable Firestore, and set up basic security rules. Generate a service account key JSON file and store it securely. Update `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` in the project root `.env` file to point to this key.
- [x] `firestore_service.py` created in `voice-assistant/src/firebase/` to encapsulate Firestore operations. Ensure `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` in the project root `.env` file points to your Firebase service account key JSON file.

# Manual Actions Required

*This file tracks steps that require manual intervention and cannot be automated.*

## 2024-12-19 - Google OAuth Setup Required

### [API_SETUP] Google OAuth Configuration - Status: ✅ Completed - 2025-05-30
**Required for**: Google Workspace integration (Tasks, Calendar, Drive, Docs)

**Steps to complete**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Enable required APIs:
   - Google Tasks API
   - Google Calendar API
   - Google Drive API
   - Google Docs API
4. Configure OAuth consent screen:
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" user type
   - Fill in required fields (App name, User support email, Developer contact)
   - Add scopes: tasks, calendar, drive, docs
5. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Web application"
   - Add authorized redirect URI: `http://localhost:8080/oauth/callback`
   - Download the JSON file as `google_client_secrets.json`
6. Set up environment variables:
   - Create `.env` file in project root if it doesn't exist
   - Add `GOOGLE_CLIENT_ID=your_client_id`
   - Add `GOOGLE_CLIENT_SECRET=your_client_secret`
7. Place credentials file:
   - Create `credentials/` directory in `voice-assistant/`
   - Move `google_client_secrets.json` to `voice-assistant/credentials/`

**Security Note**: Never commit OAuth credentials to version control.

## 2024-12-19 - Firebase Configuration Required

### [API_SETUP] Firebase Service Account Setup - Status: ✅ Completed - 2025-05-30
**Required for**: Voice assistant to store tasks, reminders, notes, and goals

**Steps to complete**:
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing project
3. Enable Firestore Database:
   - Go to "Firestore Database" in left sidebar
   - Click "Create database"
   - Choose "Start in test mode" for development
4. Create Service Account:
   - Go to Project Settings → Service Accounts
   - Click "Generate new private key"
   - Download the JSON file
   - Save it securely (e.g., `firebase-service-account-key.json`)
5. Update project root `.env` file:
   - Set `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` to the full path of your JSON file
   - Set `GEMINI_API_KEY` to your Google AI Studio API key

**Security Note**: Never commit the service account JSON file to version control.

### [API_SETUP] Gemini API Key Setup - Status: ✅ Completed - 2025-05-30
**Required for**: Voice recognition and natural language processing

**Steps to complete**:
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create API key for Gemini
3. Update project root `.env` file with your API key
4. Test the connection

## Manual Actions Required for Firestore Setup

To ensure the VoiceAssistant project can properly utilize Firestore for data persistence, please perform the following manual steps:

### 1. Set up Firestore Database

1.  **Go to Firebase Console**: Navigate to your Firebase project in the Firebase Console (<mcurl name="Firebase Console" url="https://console.firebase.google.com/"></mcurl>).
2.  **Create a Firestore Database**: In the left-hand navigation, select "Firestore Database" and click "Create database". Choose "Start in production mode" (you can adjust security rules later) and select a suitable location.

### 2. Configure Firestore Security Rules

By default, Firestore rules might be restrictive. For development, you might temporarily allow read/write access (though this is NOT recommended for production).

1.  In the Firebase Console, go to "Firestore Database" -> "Rules".
2.  Update your rules to allow read/write access for testing (e.g., for `tasks` collection):

    ```firestore
    rules_version = '2';
    service cloud.firestore {
      match /databases/{database}/documents {
        match /{document=**} {
          allow read, write: if true; // WARNING: This is insecure for production!
        }
      }
    }
    ```
    **NOTE**: This rule is highly insecure and should only be used for initial development and testing. For production, implement proper authentication and authorization rules.

### 3. Create Collections - Status: ✅ Completed (2024-12-19)

**All required Firestore collections have been successfully created:**

*   ✅ **`tasks` collection** - Document ID: 3g9i6ihifWOIaPznL1Wm
*   ✅ **`goals` collection** - Document ID: Y2upEfph9Mwor9rMDV2u
*   ✅ **`notes` collection** - Document ID: rtwPFIdiYxrnHPPucCWR
*   ✅ **`reminders` collection** - Document ID: i1lmqRM3h1rtKsy3apEG
*   ✅ **`timers` collection** - Document ID: FnT9CjgoCctwCOt27y8J
*   ✅ **`conversation_turns` collection** - Document ID: K6RoVdbPjF5C2maRtUqm

### 4. Install Context Capture Dependencies - Status: Pending

**Required for browser URL and window context capture functionality:**

```bash
conda activate voiceapp
pip install pywin32 pywinauto
```

- **pywin32** and **pywinauto**: These are Windows-specific libraries used for desktop application automation and window context capture. They are essential for the voice assistant to interact with and understand the user's current active window and browser context.
  - **Action**: Install these libraries using `pip install pywin32 pywinauto`.
  - **Status**: Completed - 2024-07-30
- **selenium** and **webdriver_manager**: These libraries are used for browser automation, specifically for capturing browser URL and title. Selenium requires a WebDriver (like ChromeDriver) to be installed, which `webdriver_manager` handles automatically.
  - **Action**: Install these libraries using `pip install selenium webdriver_manager`.
  - **Status**: Pending

**Collection Schema Reference:**

*   **`tasks` collection**: `description`, `created_at`, `updated_at`, `completed_at`, `is_active`, `raw_command`, `context_url`, `user_id`
*   **`goals` collection**: `description`, `created_at`, `updated_at`, `completed_at`, `is_active`, `raw_command`, `context_url`, `user_id`
*   **`notes` collection**: `content`, `created_at`, `updated_at`, `raw_command`, `context_url`, `user_id`
*   **`reminders` collection**: `description`, `due_at`, `created_at`, `updated_at`, `completed_at`, `is_active`, `raw_command`, `context_url`, `user_id`, `task_id`
*   **`timers` collection**: `duration_seconds`, `start_time`, `end_time`, `created_at`, `updated_at`, `is_active`, `raw_command`, `context_url`, `user_id`
*   **`conversation_turns` collection**: `speaker`, `text`, `timestamp`, `session_id`, `user_id`

**Firebase Project**: voiceapp-37f2e
**Console Access**: https://console.firebase.google.com/project/voiceapp-37f2e/firestore/data/

All collections are now ready for the voice assistant application to use.