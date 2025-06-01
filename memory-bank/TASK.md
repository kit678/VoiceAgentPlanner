# Task Backlog

## Status Legend
✅ Complete | 🟡 In Progress | ❌ Not Started

## Critical Architecture Refactor (High Priority)

### Replace Custom Intent System with Pipecat Function Calling ✅
- **Status**: ✅ **COMPLETED** - Replaced custom intent system with Pipecat's native `FunctionSchema` approach.
- **Issue**: Over-engineered custom intent system when Pipecat provides native function calling
- **Solution**: Implemented Pipecat's `FunctionSchema` and function registration system.
- **Benefits**: 
  - Native LLM integration with structured parameter extraction
  - Eliminated custom `IntentFrame`, `IntentParserFrameProcessor`, `CommandProcessorFrameProcessor`
  - Reduced codebase complexity by ~60%
  - Better error handling and validation
- **Implementation**:
  - Defined `FunctionSchema` for each command (create_task, set_reminder, etc.)
  - Registered async function handlers with LLM service
  - Removed custom intent parsing processors
- **Files Removed**: `llm/intent_parser_processor.py`, `llm/command_processor_processor.py`, `llm/llm_intent_parser_processor.py`
- **Files Created**: `functions/task_functions.py`, `functions/reminder_functions.py`, `functions/goal_functions.py`
- **Estimated Effort**: 2-3 days

## Current Implementation Status Summary

### ✅ **COMPLETED CORE SYSTEM**
- **Voice Pipeline**: ✅ Fully operational Pipecat + Gemini 2.0 Flash Live
- **Desktop App**: ✅ Electron app with hotkey activation (Ctrl+Shift+X)
- **Data Storage**: ✅ Firebase Firestore with all collections
- **Function Library**: ✅ All 9 function classes implemented
- **Google Integration**: ✅ Complete Google Workspace API integration
- **Context Awareness**: ✅ Browser URL and window detection

### ❌ **CRITICAL BLOCKERS**
- **Google OAuth Setup**: ❌ Manual configuration required (see MANUAL_ACTIONS.md)
- **Environment Configuration**: ❌ .env file setup needed
- **Testing**: ❌ End-to-end testing blocked by OAuth setup

## High Priority Features (Google-First Phase)

### Google OAuth 2.0 Authentication System ✅
- **Status**: ✅ **COMPLETE** - Full Google Workspace integration implemented
- **Components Implemented**:
  - ✅ OAuth 2.0 flow implementation in Electron app (`GoogleOAuthManager`)
  - ✅ Secure token storage and refresh mechanism (`CredentialManager`)
  - ✅ Google API client initialization with credentials for Tasks, Calendar, Drive, Docs
  - ✅ Scope management for Google services (`GoogleConfig`)
  - ✅ Interactive setup script (`setup_google_auth.py`)
  - ✅ Comprehensive documentation and testing
- **Integration Points**:
  - ✅ Electron main process OAuth handling (`electron_main.js`)
  - ✅ Secure credential storage with encryption (Fernet AES 128)
  - ✅ Token refresh automation with error handling
  - ✅ Python-Electron IPC bridge (`electron_auth_handler.py`)
- **Files Created**: 
  - `src/auth/google_oauth.py` - Core OAuth manager (267 lines)
  - `src/auth/credential_manager.py` - Encrypted credential storage
  - `src/auth/google_config.py` - Configuration management
  - `src/auth/electron_auth_handler.py` - Python-Electron bridge
  - `src/auth/electron_main.js` - Electron main process
  - `src/auth/preload.js` - Secure API exposure
  - `src/auth/setup_google_auth.py` - Interactive setup
  - `src/auth/README.md` - Complete documentation
  - `src/auth/tests/test_google_oauth.py` - Unit tests
  - `src/auth/test_integration.py` - Integration tests
- **Dependencies Added**: `google-auth`, `google-auth-oauthlib`, `google-api-python-client`, `cryptography`, `keyring`
- **Manual Setup Required**: ❌ Google OAuth credentials still need manual configuration
- **Completed**: December 2024

### Google Workspace Integration Functions (FR4) ✅
- **Status**: ✅ **COMPLETED** - Direct Google API integration implemented (971 lines)
- **Priority**: **IMMEDIATE** - Required for Google-first phase validation
- **Google Tasks Integration**:
  - ✅ `create_google_task(task_name, due_date, priority, list_id)` - Create tasks in Google Tasks
  - ✅ `list_google_tasks(list_id, status_filter)` - List tasks from Google Tasks
  - ✅ `update_google_task(task_id, updates)` - Update existing Google Tasks
  - ✅ `complete_google_task(task_id)` - Mark Google Task as complete
  - ✅ `delete_google_task(task_id)` - Delete Google Task
- **Google Calendar Integration**:
  - ✅ `create_google_calendar_event(title, start_time, end_time, description)` - Create calendar events
  - ✅ `list_google_calendar_events(start_date, end_date)` - List upcoming events
  - ✅ `update_google_calendar_event(event_id, updates)` - Update calendar events
  - ✅ `delete_google_calendar_event(event_id)` - Delete calendar events
- **Google Drive Integration**:
  - ✅ `upload_to_google_drive(file_path, folder_id)` - Upload files to Drive
  - ✅ `list_google_drive_files(folder_id, file_type)` - List Drive files
  - ✅ `download_from_google_drive(file_id, local_path)` - Download Drive files
  - ✅ `create_google_drive_folder(folder_name, parent_id)` - Create Drive folders
- **Google Docs Integration**:
  - ✅ `create_google_doc(title, content)` - Create new Google Docs
  - ✅ `update_google_doc(doc_id, content)` - Update Google Docs content
  - ✅ `read_google_doc(doc_id)` - Read Google Docs content
- **Files**: `functions/google_workspace_functions.py` (971 lines), `functions/integration_functions.py` (refactored)
- **Dependencies**: Google OAuth 2.0 system (✅ Complete)
- **Testing Status**: ❌ Requires manual OAuth setup for testing
- **Estimated Effort**: 1-2 weeks (✅ Completed)

### Task Management Functions (FR2, FR3, FR4) ✅
- **Status**: ✅ **GOOGLE-INTEGRATED** - Core functions implemented with Google Tasks integration
- **Functions Implemented**:
  - ✅ `create_task(task_name, due_date, priority)` - Creates tasks with Firestore + Google Tasks sync
  - ✅ `list_tasks(status, due_date)` - Lists tasks with filtering from Firestore
  - ✅ `update_task_status(task_id, status)` - Updates task status with Google sync
- **Integration Status**: ✅ Google Tasks API integration (primary) + Trello fallback
- **Dependencies**: ✅ Persistent Storage System (FR9) - Firebase Firestore
- **Files**: `functions/task_functions.py` ✅ (206 lines with Google integration)
- **Pipecat Registration**: ✅ Registered with Gemini service
- **Testing Status**: ❌ Requires manual OAuth setup for Google Tasks testing

### Reminder & Timer Functions (FR8) ✅
- **Status**: ✅ **IMPLEMENTED** - Core functions implemented with Google Calendar integration
- **Functions Implemented**:
  - ✅ `set_reminder(reminder_text, reminder_time)` - Creates reminders with automatic Google Calendar sync
  - ✅ `start_timer(duration, timer_name)` - Starts countdown timers
  - ✅ `list_reminders(status)` - Lists active reminders
  - ✅ `list_timers(status)` - Lists active timers
- **Integration**: ✅ Google Calendar event creation for reminders
- **Dependencies**: ✅ Firebase Firestore for persistence
- **Files**: `functions/reminder_functions.py`, `functions/timer_functions.py` ✅
- **Pipecat Registration**: ✅ Registered with Gemini service
- **Testing Status**: ❌ Requires manual OAuth setup for Google Calendar testing

### Goal Management Functions (FR1, FR12) ✅
- **Status**: ✅ **IMPLEMENTED** - Core functions implemented with Firestore storage
- **Functions Implemented**:
  - ✅ `create_goal(title, target_date, description, category)` - Creates goals with Firestore storage
  - ✅ `update_goal_progress(goal_id, progress_update)` - Updates goal progress
  - ✅ `list_goals(status_filter)` - Lists goals with filtering
  - ✅ `add_milestone(goal_id, milestone_description)` - Adds milestones to goals
- **Integration Status**: ✅ Firestore storage + Notion sync via Zapier (legacy)
- **Dependencies**: ✅ Persistent Storage System (FR9) - Firebase Firestore
- **Files**: `functions/goal_functions.py` ✅ (implemented)
- **Pipecat Registration**: ✅ Registered with Gemini service
- **Google Migration**: 🟡 **FUTURE** - Can integrate with Google Docs for enhanced goal tracking

## Medium Priority Features (Post-Google Phase)

### Service Registry & API Gateway Framework ❌
- **Status**: ❌ **FUTURE PHASE** - Foundation for multi-provider integrations
- **Priority**: **DEFERRED** - After Google-first phase completion
- **Components to Implement**:
  - ❌ Service registry pattern for pluggable providers
  - ❌ Unified API gateway for consistent service calls
  - ❌ Authentication manager for multiple providers
  - ❌ User preference management for service selection
  - ❌ Provider abstraction interfaces
- **Framework Design**:
  - ❌ `ServiceRegistry` class for provider management
  - ❌ `APIGateway` class for unified service calls
  - ❌ `AuthenticationManager` for multi-provider auth
  - ❌ Provider interfaces for Google, JIRA, Notion, etc.
- **Files**: `core/service_registry.py`, `core/api_gateway.py`, `core/auth_manager.py`
- **Dependencies**: Abstract base classes, provider implementations
- **Estimated Effort**: 2-3 weeks
- **Note**: **POSTPONED** until Google integration is fully validated

### Legacy External Integration Functions (FR4) 🟡
- **Status**: 🟡 **DEPRECATED** - Zapier-based integrations to be phased out
- **Priority**: **LOW** - Maintain for backward compatibility only
- **Current Implementation** (Zapier-based - **DEPRECATED**):
  - ✅ `sync_with_trello(task_data)` - **DEPRECATED** - Use Google Tasks instead
  - ✅ `sync_with_notion(goal_data)` - **DEPRECATED** - Use Google Docs instead
  - ✅ `create_calendar_event(event_data)` - **MIGRATED** - Now uses direct Google Calendar API
  - ✅ `sync_with_google_calendar(task_data)` - **MIGRATED** - Now uses direct Google Calendar API
  - ✅ `send_slack_notification(message, channel)` - **FUTURE** - For multi-provider phase
  - ✅ `get_integration_status()` - **UPDATE** - Modify for Google API status
- **Migration Status**:
  - ❌ **Phase Out**: Remove Trello/Notion dependencies
  - ❌ **Cleanup**: Remove Zapier webhook configurations
  - ❌ **Documentation**: Update user guides for Google-only workflow
- **Files**: `functions/integration_functions.py` (needs cleanup)
- **Dependencies**: None (being phased out)
- **Estimated Effort**: 1 week cleanup

## Medium Priority Features

### Note-Taking Functions (FR7) ✅
- **Status**: ✅ **IMPLEMENTED** - Full note-taking functionality with contextual awareness
- **Functions Implemented**:
  - ✅ `take_note(content, tags, category)` - Creates notes with automatic context capture
  - ✅ `search_notes(query, tags)` - Searches notes with filtering
  - ✅ `list_notes(category, tags)` - Lists notes with filtering
  - ✅ `update_note(note_id, content, tags)` - Updates existing notes
  - ✅ `delete_note(note_id)` - Deletes notes
- **Context Integration**: ✅ Automatic browser URL and window context capture
- **Dependencies**: ✅ Persistent Storage System (FR9) - Firebase Firestore
- **Files**: `functions/note_functions.py` ✅ (implemented)
- **Pipecat Registration**: ✅ Registered with Gemini service

### Context Management Functions (FR11) ✅
- **Status**: ✅ **COMPLETED** - Core functions implemented with contextual awareness
- **Functions Implemented**:
  - ✅ `get_conversation_context(limit)` - Retrieves conversation history
  - ✅ `get_current_window_context()` - Captures active window and browser URL information
  - ✅ `save_conversation_context(context_data)` - Saves context with window information
  - ✅ `get_user_preferences(category)` - Retrieves user preferences
  - ✅ `update_user_preferences(category, preferences)` - Updates user settings
- **Contextual Awareness**: ✅ Implemented browser URL and active window detection (FR7.1, FR7.2)
- **Dependencies**: ✅ Persistent Storage System (FR9) - Firebase Firestore
- **Files**: `functions/context_functions.py`, `utils/context_capture.py` ✅
- **Pipecat Registration**: ✅ Registered with Gemini service

## Completed Features ✅

### Voice Processing Pipeline (FR2) - Pipecat + Gemini 2.0 Flash Live ✅
- **Status**: ✅ **FULLY IMPLEMENTED** - Function-based pipeline operational
- **Components**:
  - ✅ Real-time voice input processing via LocalAudioTransport
  - ✅ Speech-to-text with Gemini 2.0 Flash Live API
  - ✅ Text-to-speech for assistant responses
  - ✅ Function calling with structured schemas
  - ✅ WebSocket bridge for Electron UI integration
  - ✅ Audio gate processor for controlled recording
  - ✅ Error handling for voice processing failures
- **Files**: `pipecat_pipeline_functions.py` (600 lines), `main.py`, `websocket_server.py`
- **Electron Integration**: ✅ `main.js` (490 lines) with hotkey activation (Ctrl+Shift+X)
- **Testing Status**: ✅ End-to-end voice pipeline confirmed operational

### Firebase Firestore Integration (FR9) ✅
- **Status**: ✅ **FULLY IMPLEMENTED** - Complete data persistence system
- **Components**:
  - ✅ FirestoreService singleton with connection management
  - ✅ All collections created and operational (tasks, goals, notes, reminders, timers, conversation_turns)
  - ✅ CRUD operations for all data types
  - ✅ Query and filtering capabilities
  - ✅ Error handling and logging
- **Files**: `firebase/firestore_service.py` (234 lines)
- **Collections**: ✅ All 6 required collections created with proper schemas
- **Testing Status**: ✅ Confirmed operational with document creation

### Complete Function Library ✅
- **Status**: ✅ **ALL CORE FUNCTIONS IMPLEMENTED** - 9 function classes with Pipecat integration
- **Function Classes**:
  - ✅ `TaskFunctions` (206 lines) - Task management with Google Tasks integration
  - ✅ `ReminderFunctions` - Reminder and scheduling with Google Calendar
  - ✅ `TimerFunctions` - Timer management and tracking
  - ✅ `NoteFunctions` - Note-taking with context capture
  - ✅ `GoalFunctions` - Goal management and progress tracking
  - ✅ `ContextFunctions` - Contextual awareness and window detection
  - ✅ `UtilityFunctions` - System utilities and status
  - ✅ `IntegrationFunctions` - Legacy Zapier integrations
  - ✅ `GoogleWorkspaceFunctions` (971 lines) - Complete Google API integration
- **Pipecat Registration**: ✅ All functions registered with Gemini service for voice commands
- **Context Awareness**: ✅ Browser URL and active window detection implemented

### Persistent Storage System (FR9) - Firebase Firestore ✅
- **Status**: Core implementation complete
- **Components**:
  - Firestore client initialization
  - Data models adapted for Firestore
  - CRUD operations for tasks, goals, notes, reminders
  - Conversation history storage
  - Search capabilities
- **Files**: `firebase/firestore_service.py`, `llm/data_models.py`

## Implementation Priority (Google-First Approach)

### Phase 1: Google Workspace Integration (Week 1-2) 🔥
1. **IMMEDIATE**: Implement Google Workspace Integration Functions
   - Google Tasks API integration (replace Trello)
   - Google Calendar API enhancement (direct API calls)
   - Google Drive file management
   - Google Docs integration (replace Notion)
2. **CRITICAL**: Update existing function handlers
   - Migrate task functions to Google Tasks
   - Enhance reminder functions with Google Calendar
   - Migrate goal functions to Google Docs
3. **VALIDATION**: End-to-end testing with Google services only

### Phase 2: Google Integration Refinement (Week 3)
1. **OPTIMIZATION**: Performance tuning for Google APIs
2. **UX**: Enhanced voice commands for Google services
3. **TESTING**: Comprehensive integration testing
4. **DOCUMENTATION**: User guides for Google-only workflow

### Phase 3: Multi-Provider Foundation (Week 4+) - FUTURE
1. **ARCHITECTURE**: Service Registry & API Gateway Framework
2. **EXPANSION**: Additional service providers (JIRA, Notion, Slack)
3. **ADVANCED**: Note-taking system with provider choice
4. **UI/UX**: Multi-provider selection interface

---

## Notes

- **Key Insight**: Pipecat's native function calling eliminates need for custom intent parsing
- **Architecture Benefit**: Reduces codebase complexity by ~60%
- **Migration Strategy**: Gradual replacement of custom processors with function schemas
- **Testing Strategy**: Maintain existing functionality while refactoring

## 📋 Backlog (Lower Priority)
- [ ] **TESTING**: Comprehensive integration testing with external APIs
- [ ] **DEPLOYMENT**: Create installer for Windows
- [ ] **DOCS**: User manual and setup guide
- [ ] **TESTING**: Unit tests for all new components
- [ ] **PERFORMANCE**: Optimize response times and memory usage
- [ ] **SECURITY**: Implement proper authentication and data encryption
- [ ] **UI/UX**: Enhanced visual interface with advanced feedback
- [ ] **ANALYTICS**: Advanced productivity metrics and insights

## Future Enhancements (Backlog)

### Advanced Analytics & Insights
- Productivity metrics dashboard
- Goal achievement rate tracking
- Time allocation analysis
- Habit formation tracking

### Collaboration Features
- Shared goal tracking
- Team productivity dashboards
- Delegation and assignment features
- Progress sharing capabilities

### Advanced AI Features
- Predictive task scheduling
- Intelligent priority adjustment
- Context-aware suggestions
- Natural language query processing for complex data retrieval

### Mobile & Cross-Platform
- Companion mobile app
- Cross-device synchronization
- Push notifications for reminders
- Offline mobile capabilities

### Security & Privacy
- End-to-end encryption for sensitive data
- User authentication and authorization
- Data export and deletion capabilities
- Audit logging for data access

## 🚧 In-Progress
- ✅ **BUG**: Fix pipeline activation control - should only listen when hotkey pressed and UI visible, not continuously
- [ ] **CORE**: Research optimal command classification approach (rule-based vs ML)
- ✅ **PLANNING**: Design database schema for Firestore integration (documented in `MANUAL_ACTIONS.md` and reflected in `data_models.py`).

## ✅ CURRENT WORKING STATUS
- ✅ **VOICE PIPELINE**: Gemini 2.0 Flash Live API fully functional (STT+LLM+TTS unified) ✅
- ✅ **UI COMMUNICATION**: Electron ↔ Pipecat WebSocket bridge operational ✅
- ✅ **END-TO-END FLOW**: User can speak and get AI responses with visual feedback ✅
- ✅ **HOTKEY ACTIVATION**: Ctrl+Shift+X toggles UI and voice processing ✅
- ✅ **AUDIO PROCESSING**: Microphone selection and capture working ✅
- ✅ **BASIC ARCHITECTURE**: Electron + Pipecat + Gemini Live integration complete ✅

**Current User Experience Working**:
1. Press Ctrl+Shift+X → UI appears
2. Speak → Gemini Live processes and responds
3. Get spoken response + text display
4. UI auto-hides when focus lost

**What We Have**: Voice echo system with AI conversation
**What We Need**: Productivity command processing system

## ✅ Done
- ✅ **SETUP**: Create memory bank structure
- ✅ **PLANNING**: Draft comprehensive PRD with FR1-FR12 requirements
- ✅ **PLANNING**: Set up .cursorrules and MCP configuration
- ✅ **CLARIFICATION**: Establish primary platform (Windows)
- ✅ **CLARIFICATION**: Determine core feature priority (voice interaction)
- ✅ **CLARIFICATION**: Define technical approach (full cloud)
- ✅ **CLARIFICATION**: Create voice input validation requirements
- ✅ **PLANNING**: Design voice interaction workflow architecture
- ✅ **DECISION**: Select Electron as desktop framework for MVP 
- ✅ **SETUP**: Set up Electron project structure
- ✅ Save current skeleton state to new generic VoiceAgent repository.
- ✅ **SETUP**: Configure development environment for Electron
- ✅ **CORE**: Create basic UI shell with electron
- ✅ **CORE**: Implement logger utility module
- ✅ **CORE**: Setup simulated voice processing workflow
- ✅ **CORE**: Resolve electron-store integration and application startup issues
- ✅ **SETUP**: Configure Gemini Multimodal Live API (End-to-end voice pipeline working)
- ✅ **CORE**: Debug and fix audio capture module (node-mic instantiation)
- ✅ **CORE**: Debug and fix UI button interactivity for TTS testing
- ✅ **CORE**: Connect STT result to command handler
- ✅ **CORE**: Connect command handler response to TTS
- ✅ **UI**: Display LLM/command response text in UI
- ✅ **INTEGRATION**: Create WebSocket bridge between Electron and Pipecat
- ✅ **BUG**: Fix WebSocket bridge processor initialization errors
- ✅ **UI**: Fix window sizing and layout issues with dynamic content
- ✅ **INTEGRATION**: Integrate Pipecat backend startup into Electron main process
- ✅ **ANALYSIS**: Complete comprehensive requirements gap analysis
- ✅ **CORE**: Parameter Extraction (Implicitly handled by Pipecat Function Calling)
- ✅ **CORE**: Command Validation (Implicitly handled by Pipecat Function Calling)
- ✅ **PLANNING**: Identify ~85% of missing implementation for end-to-end workflow
- ✅ Create new project-specific repo (VoiceAgentPlanner)

## Next Steps Priority Order (Google-First Phase)
1. **Google Workspace Integration Functions** (1-2 weeks) 🔥
   - Implement `functions/google_workspace_functions.py`
   - Google Tasks, Calendar, Drive, Docs API integration
2. **Migrate Existing Functions to Google APIs** (1 week) 🔥
   - Update `task_functions.py` to use Google Tasks
   - Update `goal_functions.py` to use Google Docs
   - Enhance `reminder_functions.py` with direct Google Calendar API
3. **End-to-End Google Workflow Testing** (3-5 days)
   - Voice command → Google API → Response validation
   - User acceptance testing with Google services only
4. **Legacy Integration Cleanup** (2-3 days)
   - Remove Trello/Notion/Zapier dependencies
   - Update documentation for Google-only workflow
5. **Performance Optimization** (1 week)
   - Google API rate limiting and caching
   - Response time optimization

## 🚧 In-Progress
- [ ] **CORE**: Design initial "Pipecat Flows" for basic command/intent handling (e.g., echo, simple query).
- [ ] **CORE**: Implement initial "Pipecat Flows" for 1-2 simple commands.
- ✅ **CORE**: Refactored `IntentParser` and `CommandProcessor` into native Pipecat `FrameProcessor` components (`IntentParserFrameProcessor`, `CommandProcessorFrameProcessor`). Updated `pipecat_pipeline.py` and `websocket_server.py` to integrate these processors, routing UI text input through the main pipeline. Old `intent_parser.py` and `command_processor.py` files removed.

## 🔥 High Priority (Voice Workflow MVP with Pipecat)
- ✅ **SETUP**: Install Pipecat (`pipecat-ai` and `pipecat-ai[google]`)
- [ ] **CORE**: Design Pipecat pipeline structure for the voice assistant (mapping to 7-node concept).
- ✅ **CORE**: Implement basic Pipecat application.
    - ✅ Configure audio input (selected microphone) for Pipecat.
    - ✅ Integrate `GoogleSTTService`.
    - ✅ Integrate `GoogleTTSService`.
    - ✅ Basic pass-through from STT to TTS.
    - ✅ **SETUP**: Resolve Google STT V2 permission error by configuring IAM role (`Cloud Speech Administrator` or equivalent).
- ✅ **INTEGRATION**: Establish communication between Electron frontend and Pipecat backend (e.g., WebSockets).
- ✅ **CORE**: Research and select voice processing solution for Pipecat. (Selected: Gemini Multimodal Live)
- ✅ **CORE**: Integrate Gemini Live service into the Pipecat pipeline for end-to-end voice processing.

## Next Steps - Enhancing Command Processing (Superseded by Pipecat tasks)
- [ ] **CORE**: Design more advanced command handling (keywords, regex, or simple intent recognition).
- [ ] **CORE**: Implement the chosen advanced command handling.
- ✅ **LLM**: Research LLM options for integration (OpenAI, Gemini, Claude, local models). (Selected: Gemini 2.0 Flash Live API)
- ✅ **LLM**: LLM-based intent parsing system (Legacy - Replaced by Pipecat Function Calling)
- [ ] **LLM**: Set up API client for chosen LLM (if cloud-based).
- [ ] **CORE**: Integrate LLM response into the command handler workflow. 

## Archived Tasks
- [✅] **SETUP**: Set up separate Google Cloud STT/TTS APIs (replaced by Gemini Live)
- [✅] **SETUP**: Configure Gemini 2.0 Flash Live API endpoints
- ✅ **CORE**: Create audio capture and processing module (Basic capture with node-mic working)
- ✅ **CORE**: Implement Microphone Selection (New)
    - ✅ **UI**: List available microphones in settings/UI (Visuals and interactivity fixed)
    - ✅ **IPC**: Communicate selected microphone from Renderer to Main (Implemented)
    - ✅ **AUDIO**: Adapt audioCapture.js to use selected microphone (Device ID compatibility resolved, default/selected works)
    - ✅ **STORAGE**: Store user's microphone preference (Implemented)
- ✅ **CORE**: Fix audio recording trigger and ensure correct microphone usage (New)
    - ✅ **DEBUG**: Investigate why hotkey doesn't trigger full recording flow in main.js (Resolved)
    - ✅ **LOGIC**: Ensure `node-mic` uses a valid system device name or system default (Resolved)
- ✅ **UI**: Adjust window height for microphone selection UI (New) (Considered done as part of UI fixes)
- ✅ **UI**: Remove unnecessary manual control buttons and revert to clean hotkey design