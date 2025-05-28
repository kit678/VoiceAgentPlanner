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

### 3. Create Collections (Optional, as they are created on first write)

Firestore is schemaless, and collections are created automatically when you add the first document. However, for clarity, here are the expected collections and their primary fields:

*   **`tasks` collection**:
    *   `description` (string)
    *   `created_at` (timestamp)
    *   `updated_at` (timestamp)
    *   `completed_at` (timestamp, nullable)
    *   `is_active` (boolean)
    *   `raw_command` (string, nullable)
    *   `context_url` (string, nullable)
    *   `user_id` (string, nullable)

*   **`goals` collection**:
    *   `description` (string)
    *   `created_at` (timestamp)
    *   `updated_at` (timestamp)
    *   `completed_at` (timestamp, nullable)
    *   `is_active` (boolean)
    *   `raw_command` (string, nullable)
    *   `context_url` (string, nullable)
    *   `user_id` (string, nullable)

*   **`notes` collection**:
    *   `content` (string)
    *   `created_at` (timestamp)
    *   `updated_at` (timestamp)
    *   `raw_command` (string, nullable)
    *   `context_url` (string, nullable)
    *   `user_id` (string, nullable)

*   **`reminders` collection**:
    *   `description` (string)
    *   `due_at` (timestamp)
    *   `created_at` (timestamp)
    *   `updated_at` (timestamp)
    *   `completed_at` (timestamp, nullable)
    *   `is_active` (boolean)
    *   `raw_command` (string, nullable)
    *   `context_url` (string, nullable)
    *   `user_id` (string, nullable)
    *   `task_id` (string, nullable, foreign key to `tasks`)

*   **`timers` collection**:
    *   `duration_seconds` (integer)
    *   `start_time` (timestamp)
    *   `end_time` (timestamp)
    *   `created_at` (timestamp)
    *   `updated_at` (timestamp)
    *   `is_active` (boolean)
    *   `raw_command` (string, nullable)
    *   `context_url` (string, nullable)
    *   `user_id` (string, nullable)

*   **`conversation_turns` collection**:
    *   `speaker` (string, e.g., "user", "assistant")
    *   `text` (string)
    *   `timestamp` (timestamp)
    *   `session_id` (string)
    *   `user_id` (string, nullable)

These manual steps are crucial for the application to interact with Firestore correctly.