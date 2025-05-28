# Task Backlog

**Status Legend:**
- ✅ Complete
- 🟡 In Progress  
- ❌ Not Started
- 🔴 High Priority (Blocking MVP)
- 🟠 Medium Priority
- 🟢 Low Priority/Future

## 🔥 CRITICAL MISSING COMPONENTS (MVP Blockers)

### Command Processing & Intent Classification (FR6)
- [ ] **CORE**: Design command classification system for Pipecat flows
- [x] **CORE**: Implement intent recognition for basic commands ("take note", "create task", "set reminder", "start timer") - Refactored to `IntentParserFrameProcessor` with keyword matching for `greet` and `create_task`.
- [ ] **CORE**: Build parameter extraction from natural language (dates, priorities, descriptions)
- [ ] **CORE**: Create command validation and confirmation system
- [x] **CORE**: Implement action routing to appropriate handlers - Refactored to `CommandProcessorFrameProcessor` with stubs for `greet` and `create_task`.

### Persistent Storage System (FR9) - Firestore
- [x] **SETUP**: Document manual Firestore setup (Firebase project, database creation, basic security rules) in `MANUAL_ACTIONS.md`.
- [x] **CORE**: Adapt data models (`data_models.py`) for Firestore compatibility (UUIDs to strings).
- [x] **CORE**: Implement Firestore client initialization (`utils/firestore_client.py`).
- [✅] **CORE**: Integrate Firestore for task creation in `CommandProcessorFrameProcessor` (`command_processor_processor.py`). *(Fixed credentials path)*
- [ ] **CORE**: Implement Firestore storage for `conversation_turns`.
- [ ] **CORE**: Implement Firestore storage for assistant-specific `goals` and `notes` (metadata if linked to external services).
- [ ] **CORE**: Implement Firestore storage for `reminders` and `timers` metadata (if primary data is external or if they are internal assistant features).
- [ ] **CORE**: Review and refine data models to clearly distinguish between fully stored data and metadata for externally managed items.
- [ ] **CORE**: Implement search capabilities for `conversation_turns`.
- [ ] **CORE**: Define backup strategy for Firestore data.

### Goal Management System (FR1, FR12)
- [ ] **CORE**: Implement goal breakdown logic with LLM assistance
- [ ] **CORE**: Create task prioritization algorithms
- [ ] **CORE**: Build goal dependency tracking
- [ ] **CORE**: Implement progress calculation and review system
- [ ] **CORE**: Create goal timeline adjustment based on progress

### External Integrations (FR4)
- [ ] **INTEGRATION**: Set up Zapier webhook system
- [ ] **INTEGRATION**: Implement Trello integration for task management
- [ ] **INTEGRATION**: Create Notion integration for note storage
- [ ] **INTEGRATION**: Build Google Calendar integration for events/reminders
- [ ] **INTEGRATION**: Design action dispatch system with error handling

## 📋 HIGH PRIORITY FEATURES

### Daily Briefing System (FR3)
- [ ] **CORE**: Implement daily progress summarization
- [ ] **CORE**: Create morning briefing with yesterday's review
- [ ] **CORE**: Build prioritized daily agenda generation
- [ ] **CORE**: Add goal alignment checking for daily tasks

### Timer & Focus Management (FR8)
- [ ] **CORE**: Implement multiple timer system
- [ ] **CORE**: Create focus session management with break reminders
- [ ] **CORE**: Build time tracking for tasks and projects
- [ ] **CORE**: Add timer completion notifications

### Contextual Awareness (FR7)
- [ ] **CORE**: Implement active window detection for context capture
- [ ] **CORE**: Add browser URL and title capture for notes
- [ ] **CORE**: Create timestamp and session context enrichment
- [ ] **CORE**: Build contextual metadata storage system

## 🚧 MEDIUM PRIORITY ENHANCEMENTS

### Input Validation & Clarification (FR2.2.3-4)
- [ ] **CORE**: Enhance grammar and syntax correction beyond Gemini Live
- [ ] **CORE**: Implement ambiguity detection and clarification prompts
- [ ] **CORE**: Build confidence scoring for voice commands
- [ ] **CORE**: Create specialized terminology handling

### Proactive Assistance (FR10)
- [ ] **CORE**: Implement user pattern analysis
- [ ] **CORE**: Create productivity scheduling suggestions
- [ ] **CORE**: Build deadline reminder system
- [ ] **CORE**: Add weekly/monthly productivity summaries

### Error Handling & Offline Capabilities (FR11)
- [ ] **CORE**: Implement local command queue for offline scenarios
- [ ] **CORE**: Create comprehensive error recovery system
- [ ] **CORE**: Build degraded operation modes
- [ ] **CORE**: Add service status monitoring and notifications

## 📋 Backlog (Lower Priority)
- [ ] **TESTING**: Comprehensive integration testing with external APIs
- [ ] **DEPLOYMENT**: Create installer for Windows
- [ ] **DOCS**: User manual and setup guide
- [ ] **TESTING**: Unit tests for all new components
- [ ] **PERFORMANCE**: Optimize response times and memory usage
- [ ] **SECURITY**: Implement proper authentication and data encryption
- [ ] **UI/UX**: Enhanced visual interface with advanced feedback
- [ ] **ANALYTICS**: Advanced productivity metrics and insights

## 🚧 In-Progress
- [x] **BUG**: Fix pipeline activation control - should only listen when hotkey pressed and UI visible, not continuously
- [ ] **CORE**: Research optimal command classification approach (rule-based vs ML)
- [x] **PLANNING**: Design database schema for Firestore integration (documented in `MANUAL_ACTIONS.md` and reflected in `data_models.py`).

## ✅ CURRENT WORKING STATUS
- [x] **VOICE PIPELINE**: Gemini 2.0 Flash Live API fully functional (STT+LLM+TTS unified)
- [x] **UI COMMUNICATION**: Electron ↔ Pipecat WebSocket bridge operational
- [x] **END-TO-END FLOW**: User can speak and get AI responses with visual feedback
- [x] **HOTKEY ACTIVATION**: Ctrl+Shift+X toggles UI and voice processing
- [x] **AUDIO PROCESSING**: Microphone selection and capture working
- [x] **BASIC ARCHITECTURE**: Electron + Pipecat + Gemini Live integration complete

**Current User Experience Working**:
1. Press Ctrl+Shift+X → UI appears
2. Speak → Gemini Live processes and responds
3. Get spoken response + text display
4. UI auto-hides when focus lost

**What We Have**: Voice echo system with AI conversation
**What We Need**: Productivity command processing system

## ✅ Done
- [x] **SETUP**: Create memory bank structure
- [x] **PLANNING**: Draft comprehensive PRD with FR1-FR12 requirements
- [x] **PLANNING**: Set up cursor rules and MCP configuration
- [x] **CLARIFICATION**: Establish primary platform (Windows)
- [x] **CLARIFICATION**: Determine core feature priority (voice interaction)
- [x] **CLARIFICATION**: Define technical approach (full cloud)
- [x] **CLARIFICATION**: Create voice input validation requirements
- [x] **PLANNING**: Design voice interaction workflow architecture
- [x] **DECISION**: Select Electron as desktop framework for MVP 
- [x] **SETUP**: Set up Electron project structure
- [x] **SETUP**: Configure development environment for Electron
- [x] **CORE**: Create basic UI shell with electron
- [x] **CORE**: Implement logger utility module
- [x] **CORE**: Setup simulated voice processing workflow
- [x] **CORE**: Resolve electron-store integration and application startup issues
- [x] **SETUP**: Configure Gemini Multimodal Live API (End-to-end voice pipeline working)
- [x] **CORE**: Debug and fix audio capture module (node-mic instantiation)
- [x] **CORE**: Debug and fix UI button interactivity for TTS testing
- [x] **CORE**: Connect STT result to command handler
- [x] **CORE**: Connect command handler response to TTS
- [x] **UI**: Display LLM/command response text in UI
- [x] **INTEGRATION**: Create WebSocket bridge between Electron and Pipecat
- [x] **BUG**: Fix WebSocket bridge processor initialization errors
- [x] **UI**: Fix window sizing and layout issues with dynamic content
- [x] **INTEGRATION**: Integrate Pipecat backend startup into Electron main process
- [x] **ANALYSIS**: Complete comprehensive requirements gap analysis
- [x] **PLANNING**: Identify ~85% of missing implementation for end-to-end workflow

## Next Steps Priority Order
1. **Fix Pipeline Activation** (1 week)
2. **Basic Command Classification** (1-2 weeks)
3. **Firestore Integration & Refinement** (1-2 weeks)
4. **Simple Action Handlers** (1 week)
5. **First External Integration** (1-2 weeks)

## 🚧 In-Progress
- [ ] **CORE**: Design initial "Pipecat Flows" for basic command/intent handling (e.g., echo, simple query).
- [ ] **CORE**: Implement initial "Pipecat Flows" for 1-2 simple commands.
- [x] **CORE**: Refactored `IntentParser` and `CommandProcessor` into native Pipecat `FrameProcessor` components (`IntentParserFrameProcessor`, `CommandProcessorFrameProcessor`). Updated `pipecat_pipeline.py` and `websocket_server.py` to integrate these processors, routing UI text input through the main pipeline. Old `intent_parser.py` and `command_processor.py` files removed.

## 🔥 High Priority (Voice Workflow MVP with Pipecat)
- [x] **SETUP**: Install Pipecat (`pipecat-ai` and `pipecat-ai[google]`)
- [ ] **CORE**: Design Pipecat pipeline structure for the voice assistant (mapping to 7-node concept).
- [x] **CORE**: Implement basic Pipecat application.
    - [x] Configure audio input (selected microphone) for Pipecat.
    - [x] Integrate `GoogleSTTService`.
    - [x] Integrate `GoogleTTSService`.
    - [x] Basic pass-through from STT to TTS.
    - [x] **SETUP**: Resolve Google STT V2 permission error by configuring IAM role (`Cloud Speech Administrator` or equivalent).
- [x] **INTEGRATION**: Establish communication between Electron frontend and Pipecat backend (e.g., WebSockets).
- [x] **CORE**: Research and select voice processing solution for Pipecat. (Selected: Gemini Multimodal Live)
- [x] **CORE**: Integrate Gemini Live service into the Pipecat pipeline for end-to-end voice processing.

## Next Steps - Enhancing Command Processing (Superseded by Pipecat tasks)
- [ ] **CORE**: Design more advanced command handling (keywords, regex, or simple intent recognition).
- [ ] **CORE**: Implement the chosen advanced command handling.
- [x] **LLM**: Research LLM options for integration (OpenAI, Gemini, Claude, local models). (Selected: Gemini 2.0 Flash Live API)
- [ ] **LLM**: Set up API client for chosen LLM (if cloud-based).
- [ ] **CORE**: Integrate LLM response into the command handler workflow. 

## Archived Tasks
- [✅] **SETUP**: Set up separate Google Cloud STT/TTS APIs (replaced by Gemini Live)
- [✅] **SETUP**: Configure Gemini 2.0 Flash Live API endpoints
- [x] **CORE**: Create audio capture and processing module (Basic capture with node-mic working)
- [x] **CORE**: Implement Microphone Selection (New)
    - [x] **UI**: List available microphones in settings/UI (Visuals and interactivity fixed)
    - [x] **IPC**: Communicate selected microphone from Renderer to Main (Implemented)
    - [x] **AUDIO**: Adapt audioCapture.js to use selected microphone (Device ID compatibility resolved, default/selected works)
    - [x] **STORAGE**: Store user's microphone preference (Implemented)
- [x] **CORE**: Fix audio recording trigger and ensure correct microphone usage (New)
    - [x] **DEBUG**: Investigate why hotkey doesn't trigger full recording flow in main.js (Resolved)
    - [x] **LOGIC**: Ensure `node-mic` uses a valid system device name or system default (Resolved)
- [x] **UI**: Adjust window height for microphone selection UI (New) (Considered done as part of UI fixes)
- [x] **UI**: Remove unnecessary manual control buttons and revert to clean hotkey design