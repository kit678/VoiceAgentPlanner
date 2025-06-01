# Google OAuth 2.0 Authentication System

This directory contains the complete Google OAuth 2.0 authentication system for the Voice Assistant, enabling seamless integration with Google Workspace services including Tasks, Calendar, Drive, and Docs.

## 🏗️ Architecture Overview

The authentication system consists of several key components:

```
src/auth/
├── google_oauth.py          # Core OAuth manager
├── credential_manager.py    # Secure credential storage
├── google_config.py         # Configuration settings
├── electron_auth_handler.py # Python-Electron bridge
├── electron_main.js         # Electron main process
├── preload.js              # Electron preload script
├── setup_google_auth.py    # Interactive setup script
└── README.md               # This file

renderer/
└── auth-flow.html          # OAuth UI interface
```

## 🚀 Quick Start

### 1. Run the Setup Script

```bash
cd /path/to/voice-assistant
python src/auth/setup_google_auth.py
```

The setup script will guide you through:
- Creating a Google Cloud project
- Enabling required APIs
- Configuring OAuth credentials
- Setting up environment variables
- Testing the authentication flow

### 2. Manual Setup (Alternative)

If you prefer manual setup:

#### Step 1: Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable these APIs:
   - Google Tasks API
   - Google Calendar API
   - Google Drive API
   - Google Docs API

#### Step 2: OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Desktop application"
4. Add redirect URI: `http://localhost:8080/callback`
5. Download the JSON credentials file

#### Step 3: Configure Application

1. Place the downloaded JSON file as `src/auth/client_secrets.json`
2. Create `.env` file in project root:

```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

### 3. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies
npm install
```

### 4. Start the Application

```bash
npm start
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_CLIENT_ID` | OAuth 2.0 Client ID | Yes |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 Client Secret | Yes |
| `GOOGLE_REDIRECT_URI` | OAuth redirect URI | No (defaults to localhost:8080) |
| `CREDENTIALS_DIR` | Directory for storing tokens | No (defaults to ~/.voice-assistant) |

### OAuth Scopes

The application requests these Google API scopes:

- **Tasks**: `https://www.googleapis.com/auth/tasks`
- **Calendar**: `https://www.googleapis.com/auth/calendar`
- **Drive**: `https://www.googleapis.com/auth/drive.file`
- **Docs**: `https://www.googleapis.com/auth/documents`

### Configuration Files

- `client_secrets.json`: OAuth 2.0 client configuration
- `~/.voice-assistant/credentials/`: Encrypted user tokens
- `.env`: Environment variables

## 🔐 Security Features

### Credential Encryption
- All stored credentials are encrypted using Fernet (AES 128)
- Encryption keys are managed securely using the system keyring
- Tokens are automatically refreshed when expired

### Secure Storage
- Credentials stored in user-specific directory
- File permissions restricted to current user
- No sensitive data in application logs

### Token Management
- Automatic token refresh
- Secure token revocation
- Session-based authentication state

## 🛠️ API Usage

### Python API

```python
from src.auth.google_oauth import GoogleOAuthManager

# Initialize OAuth manager
oauth_manager = GoogleOAuthManager()

# Check authentication status
if await oauth_manager.is_authenticated():
    # Get authenticated API clients
    tasks_service = await oauth_manager.get_tasks_service()
    calendar_service = await oauth_manager.get_calendar_service()
    drive_service = await oauth_manager.get_drive_service()
    docs_service = await oauth_manager.get_docs_service()
    
    # Use the services...
else:
    # Start authentication flow
    auth_url = await oauth_manager.get_authorization_url()
    print(f"Please visit: {auth_url}")
```

### Electron API (Renderer Process)

```javascript
// Check authentication status
const isAuthenticated = await window.electronAPI.google.isAuthenticated();

if (!isAuthenticated) {
    // Start authentication flow
    await window.electronAPI.google.authenticate();
}

// Use Google APIs
const tasks = await window.electronAPI.google.tasks.list();
const events = await window.electronAPI.google.calendar.listEvents();
```

## 📋 Supported Operations

### Google Tasks
- ✅ List task lists
- ✅ Create/update/delete tasks
- ✅ Mark tasks as complete
- ✅ Set due dates and notes

### Google Calendar
- ✅ List calendars
- ✅ Create/update/delete events
- ✅ List upcoming events
- ✅ Set reminders and attendees

### Google Drive
- ✅ List files and folders
- ✅ Upload/download files
- ✅ Create folders
- ✅ Share files

### Google Docs
- ✅ Create documents
- ✅ Read document content
- ✅ Update document text
- ✅ Format text (bold, italic, etc.)

## 🎯 Voice Commands

Once authenticated, you can use these voice commands:

### Task Management
- "Create a task: Buy groceries"
- "Add task: Call dentist for appointment"
- "Mark task 'Buy groceries' as complete"
- "Show my tasks for today"

### Calendar Management
- "Schedule meeting tomorrow at 2 PM"
- "Create event: Team standup on Friday at 9 AM"
- "Show my calendar for today"
- "What's my next meeting?"

### Document Management
- "Create a document called Meeting Notes"
- "Open document: Project Plan"
- "Add text to document: Meeting Notes"

### File Management
- "Upload file to Drive"
- "Create folder: Project Documents"
- "List files in Drive"

## 🔍 Troubleshooting

### Common Issues

#### Authentication Failed
- Verify client ID and secret in `.env` file
- Check that redirect URI matches Google Cloud Console
- Ensure required APIs are enabled

#### Token Expired
- Tokens are automatically refreshed
- If issues persist, delete `~/.voice-assistant/credentials/` and re-authenticate

#### Permission Denied
- Check OAuth scopes in Google Cloud Console
- Verify user has granted all required permissions
- Re-run authentication flow if needed

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Log Files

Check application logs:
- `logs/voice-assistant.log`: Main application log
- `logs/auth.log`: Authentication-specific log
- Console output during development

## 🧪 Testing

### Unit Tests

```bash
# Run authentication tests
python -m pytest src/auth/tests/ -v
```

### Integration Tests

```bash
# Test with real Google APIs (requires authentication)
python src/auth/test_integration.py
```

### Manual Testing

1. Run setup script: `python src/auth/setup_google_auth.py`
2. Start application: `npm start`
3. Complete OAuth flow in browser
4. Test voice commands

## 📚 API Reference

### GoogleOAuthManager

Main class for handling Google OAuth authentication.

#### Methods

- `get_authorization_url()`: Generate OAuth authorization URL
- `handle_callback(code)`: Process OAuth callback with authorization code
- `is_authenticated()`: Check if user is authenticated
- `get_user_info()`: Get authenticated user information
- `revoke_credentials()`: Revoke user authentication
- `get_tasks_service()`: Get authenticated Google Tasks API client
- `get_calendar_service()`: Get authenticated Google Calendar API client
- `get_drive_service()`: Get authenticated Google Drive API client
- `get_docs_service()`: Get authenticated Google Docs API client

### CredentialManager

Secure credential storage and management.

#### Methods

- `store_credentials(service, credentials)`: Store encrypted credentials
- `load_credentials(service)`: Load and decrypt credentials
- `delete_credentials(service)`: Delete stored credentials
- `list_services()`: List services with stored credentials
- `is_authenticated(service)`: Check authentication status

## 🤝 Contributing

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up pre-commit hooks: `pre-commit install`
4. Run tests: `pytest`

### Code Style

- Follow PEP 8 for Python code
- Use ESLint for JavaScript code
- Add type hints for all Python functions
- Include docstrings for all public methods

### Adding New Google Services

1. Add service configuration to `google_config.py`
2. Add service methods to `GoogleOAuthManager`
3. Update Electron preload script with new APIs
4. Add voice command handlers
5. Update documentation

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🆘 Support

For issues and questions:

1. Check this README and troubleshooting section
2. Review application logs
3. Check Google Cloud Console configuration
4. Create an issue in the project repository

---

**Note**: This authentication system is designed for desktop applications. For web applications, additional security considerations and different OAuth flows may be required.