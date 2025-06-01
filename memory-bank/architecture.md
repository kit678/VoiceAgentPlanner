Call every day.# Architecture & Technical Design

## Technology Stack & Decisions

### Core Technologies
- **Voice Processing**: Gemini 2.0 Flash Live API (unified STT+LLM+TTS)
- **Framework**: Pipecat-AI (with Function Calling) for voice agent orchestration
- **Desktop Platform**: Electron (JavaScript/TypeScript)
- **Database**: Firebase Firestore (real-time sync)
- **Integrations**: Zapier (Trello, Notion, Google Calendar) (planned)
- **Target OS**: Windows (primary)

### Key Architectural Decisions (ADRs)

**2024-12-19 – Seven Node Architecture Pattern**
- **Decision**: Adopt seven-node architecture (LLM, Tool, Control, Memory, Input, Guardrail, Fallback)
- **Rationale**: Provides clear separation of concerns, testability, and scalability

**2024-12-19 – Full Cloud Architecture**
- **Decision**: Adopt fully cloud-based architecture for all components
- **Rationale**: Maximizes capability while minimizing local complexity, leverages free tiers

**2024-12-19 – Electron Framework Selection**
- **Decision**: Use Electron for desktop application framework
- **Rationale**: Faster MVP development, robust audio libraries, simplified cloud integration

**2024-05- **Pipecat Framework Adoption**:
- **Decision**: Adopt Pipecat-AI for voice agent development and STT/TTS integration, leveraging its Function Calling capabilities for command processing.
- **Rationale**: Robust real-time audio processing, structured conversational logic management, and native LLM function integration.

**2024-06-15 – Switched to DeepSeek API**
- **Decision**: Switch to DeepSeek API for better Chinese support and cost efficiency
- **Rationale**: Superior Chinese language support and cost optimization vs Google Gemini

**2024-12-19 – Firebase Firestore Selection**
- **Decision**: Use Firebase Firestore for persistent storage
- **Rationale**: Real-time capabilities, Google ecosystem alignment, ease of integration

**2024-12-19 – Voice Input Validation Layer**
- **Decision**: Implement dedicated validation between STT and command execution
- **Rationale**: Improves reliability, provides better UX through proactive clarification

**2024-12-19 – Windows-First Approach**
- **Decision**: Target Windows as primary platform for initial release
- **Rationale**: Aligns with user's environment, simplifies initial development

## Current Implementation Architecture

```mermaid
graph TB
    subgraph "Desktop Application Layer"
        A[Electron Main Process ✅] --> B[Audio Capture ✅]
        A --> C[Hotkey Management ✅]
        A --> D[WebSocket Bridge ✅]
        A --> E[OAuth UI Flow ✅]
    end
    
    subgraph "Voice Processing Layer"
        F[Pipecat Pipeline ✅] --> G[Gemini 2.0 Flash Live ✅]
        G --> H[Function Calling ✅]
        H --> I[Response Generation ✅]
        F --> J[Audio Gate Processor ✅]
        F --> K[WebSocket Processor ✅]
    end
    
    subgraph "Function Library (9 Classes)"
        L[TaskFunctions ✅] --> M[Google Tasks API ✅]
        N[ReminderFunctions ✅] --> O[Google Calendar API ✅]
        P[NoteFunctions ✅] --> Q[Context Capture ✅]
        R[GoalFunctions ✅] --> S[Progress Tracking ✅]
        T[TimerFunctions ✅] --> U[Timer Management ✅]
        V[ContextFunctions ✅] --> W[Browser Detection ✅]
        X[UtilityFunctions ✅] --> Y[System Status ✅]
        Z[GoogleWorkspaceFunctions ✅] --> AA[Complete Google APIs ✅]
        BB[IntegrationFunctions ✅] --> CC[Legacy Zapier ✅]
    end
    
    subgraph "Data Persistence Layer"
        DD[Firebase Firestore ✅] --> EE[Tasks Collection ✅]
        DD --> FF[Goals Collection ✅]
        DD --> GG[Notes Collection ✅]
        DD --> HH[Reminders Collection ✅]
        DD --> II[Timers Collection ✅]
        DD --> JJ[Conversation Turns ✅]
    end
    
    subgraph "Authentication Layer"
        KK[Google OAuth 2.0 ✅] --> LL[Credential Manager ✅]
        LL --> MM[Token Storage ✅]
        KK --> NN[Scope Management ✅]
        KK --> OO[Electron Auth Bridge ✅]
    end
    
    subgraph "Google Workspace Integration"
        PP[Google Tasks API ✅] --> QQ[Task CRUD Operations ✅]
        RR[Google Calendar API ✅] --> SS[Event Management ✅]
        TT[Google Drive API ✅] --> UU[File Operations ✅]
        VV[Google Docs API ✅] --> WW[Document Management ✅]
    end
    
    subgraph "Context Awareness"
        XX[Browser URL Detection ✅] --> YY[Selenium WebDriver ✅]
        ZZ[Window Title Capture ✅] --> AAA[Windows API ✅]
        BBB[Context Storage ✅] --> DD
    end
    
    A --> F
    F --> L
    F --> N
    F --> P
    F --> R
    F --> T
    F --> V
    F --> X
    F --> Z
    F --> BB
    L --> DD
    N --> DD
    P --> DD
    R --> DD
    T --> DD
    L --> KK
    N --> KK
    Z --> KK
    KK --> PP
    KK --> RR
    KK --> TT
    KK --> VV
    P --> XX
    P --> ZZ
    XX --> BBB
    ZZ --> BBB
    
    classDef implemented fill:#90EE90,stroke:#006400,stroke-width:2px
    classDef blocked fill:#FFB6C1,stroke:#8B0000,stroke-width:2px
    
    class A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,AA,BB,CC,DD,EE,FF,GG,HH,II,JJ,KK,LL,MM,NN,OO,PP,QQ,RR,SS,TT,UU,VV,WW,XX,YY,ZZ,AAA,BBB implemented
```

### Implementation Status Summary
- **✅ Fully Implemented**: All core components operational
- **❌ Blocked**: Manual OAuth setup required for testing
- **Total Components**: 50+ components implemented
- **Code Coverage**: ~3,500+ lines of production code

## Current Working Implementation

### ✅ **Implemented Components**
1. **Electron UI**: Desktop app with hotkey activation (Ctrl+Shift+X)
2. **WebSocket Bridge**: Real-time communication between UI and backend
3. **Pipecat Pipeline**: Voice processing orchestration framework
4. **Gemini Live API**: Unified STT + LLM + TTS service
5. **Audio Capture**: LocalAudioTransport with microphone selection
6. **IntentParserFrameProcessor**: Integrated for intent parsing.
7. **CommandProcessorFrameProcessor**: Integrated for command processing.
8. **Parameter Extraction**: Basic parameter extraction is now functional.

### **Current User Flow (Working)**
```
User presses Ctrl+Shift+X → UI appears → User speaks → 
Gemini Live processes (STT+LLM+TTS) → Response played + displayed → UI hides
```

### ❌ **Missing Components (Updated)**
1. **Advanced Command Classification & Parameter Extraction**: Robust intent recognition and data extraction for all productivity commands.
2. **Full Firestore Integration**: Storing conversation history, assistant-specific goals/notes, and metadata for externally managed items. Implementing search and backup strategies.
3. **External Integrations**: Zapier connections to Trello/Notion/Calendar with full data flow and error handling.
4. **Goal Management**: Task breakdown and prioritization logic
5. **Daily Briefing**: Morning reviews and agenda generation
6. **Timer System**: Focus sessions and reminders
7. **Contextual Awareness**: Browser/window detection
8. **Error Handling**: Comprehensive failure recovery

## Target Architecture (4-Week MVP)

### **Week 1**: Command Processing Foundation (✅ Completed)
- Refactored `IntentParser` to `IntentParserFrameProcessor`
- Refactored `CommandProcessor` to `CommandProcessorFrameProcessor`
- Integrated FrameProcessors into Pipecat pipeline
- [ ] Implement parameter extraction from voice commands
- [ ] Create command validation and confirmation

### **Week 2**: Data Persistence (Firestore Focus)
- Complete Firestore integration for all internal data types (conversation history, assistant-specific goals/notes).
- Refine data models to clearly distinguish internal data vs. metadata for external services.
- Implement basic CRUD operations for all Firestore-managed entities.
- Begin implementing search for conversation history.

### **Week 3**: External Integration
- Configure Zapier webhook system
- Build Trello integration for task creation
- Add action dispatch and error handling

### **Week 4**: Daily Briefing
- Implement morning progress summaries
- Add daily agenda generation
- Create goal alignment checking

## Technical Stack Summary

**Current Working Stack**:
- **Frontend**: Electron + WebSocket client
- **Backend**: Python with Pipecat framework for core orchestration (including custom `FrameProcessors` for intent/command handling)
- **Voice Processing**: Gemini 2.0 Flash Live API
- **Communication**: WebSocket bridge

**To Be Added / In Progress**:
- **Database**: Firebase Firestore (Partially integrated for tasks, needs expansion for other entities and metadata management)
- **Authentication**: Google OAuth 2.0 for Workspace services, extensible OAuth manager for other providers
- **Direct API Integrations**: 
  - **Primary**: Google Tasks, Google Calendar, Google Keep/Docs, Google Drive
  - **Future**: JIRA, Notion, Slack, Todoist (user-selectable)
- **Integration Architecture**: Service registry pattern for pluggable integrations

## Framework Decision

Based on the requirement for rapid MVP development on Windows while focusing on voice interaction capabilities, **Electron** is recommended for the initial implementation:

- **Pros for this project**:
  - Faster development cycle with web technologies
  - Extensive libraries for audio handling and UI feedback
  - Simpler integration with cloud services via JavaScript SDKs
  - Better suited for quick MVP iteration

- **Alternative**:
  - **.NET MAUI** would provide better native Windows integration but at the cost of longer development time
  - Could be considered for v2 once the voice workflow is validated

## Direct API Integration Architecture

### **Google Workspace Integration (Single Sign-On)**

**Authentication Flow**:
```
User clicks "Sign in with Google" → OAuth 2.0 flow → 
Receive access tokens for all Google services → Store securely → 
Use tokens for API calls to Tasks, Calendar, Keep, Drive
```

**Google Services Coverage**:
- **Google Tasks/Kanbanchi**: Task creation, updates, completion tracking
- **Google Calendar**: Event creation, reminders, scheduling
- **Google Keep/Docs**: Note-taking, document creation, quick captures
- **Google Drive**: File storage, document management, sharing

**API Endpoints & Capabilities**:
```python
# Google Tasks API
- tasks().list() - Get task lists
- tasks().insert() - Create new tasks
- tasks().update() - Update task status/details
- tasks().delete() - Remove tasks

# Google Calendar API
- events().list() - Get calendar events
- events().insert() - Create new events
- events().update() - Modify existing events
- events().delete() - Remove events

# Google Keep API (via Drive API + Apps Script)
- Create notes with metadata
- Search and retrieve notes
- Update note content

# Google Drive API
- files().create() - Upload documents
- files().list() - Search files
- files().get() - Download content
```

### **Extensible Integration Framework**

**Service Registry Pattern**:
```python
class ServiceRegistry:
    def register_provider(self, service_type: str, provider: ServiceProvider)
    def get_provider(self, service_type: str, user_preference: str)
    def list_available_providers(self, service_type: str)

# Example usage:
registry.register_provider("tasks", GoogleTasksProvider())
registry.register_provider("tasks", JIRAProvider())
registry.register_provider("notes", GoogleKeepProvider())
registry.register_provider("notes", NotionProvider())
```

**Multi-Provider Authentication**:
```python
class AuthenticationManager:
    def authenticate_google(self) -> GoogleCredentials
    def authenticate_jira(self, server_url: str) -> JIRACredentials
    def authenticate_notion(self) -> NotionCredentials
    def get_active_credentials(self, service_type: str) -> Credentials
```

**Unified API Gateway**:
```python
class APIGateway:
    def create_task(self, task_data: dict, provider: str = None)
    def create_event(self, event_data: dict, provider: str = None)
    def create_note(self, note_data: dict, provider: str = None)
    def sync_data(self, service_types: list)
```

### **User Configuration & Preferences**

**Service Selection UI**:
```
┌─ Integration Settings ─────────────────┐
│ ✅ Google Workspace (Connected)        │
│   ├─ Tasks: Google Tasks              │
│   ├─ Calendar: Google Calendar        │
│   ├─ Notes: Google Keep               │
│   └─ Files: Google Drive              │
│                                       │
│ ⚪ Alternative Providers               │
│   ├─ Tasks: [ JIRA ] [Connect]        │
│   ├─ Notes: [ Notion ] [Connect]      │
│   └─ Chat: [ Slack ] [Connect]        │
│                                       │
│ [Save Preferences]                    │
└───────────────────────────────────────┘
```

**Migration Path from Zapier**:
1. **Phase 1**: Replace Zapier webhooks with direct Google API calls
2. **Phase 2**: Implement service registry and multi-provider support
3. **Phase 3**: Add alternative providers (JIRA, Notion, Slack)
4. **Phase 4**: User preference management and provider switching

### **Implementation Priority**

**Week 1-2: Google Integration Foundation**
- Implement Google OAuth 2.0 flow
- Create Google Tasks API integration
- Add Google Calendar API integration
- Basic Google Keep/Drive integration

**Week 3-4: Framework & Extensibility**
- Build service registry pattern
- Implement authentication manager
- Create unified API gateway
- Add user preference management

**Future Phases: Alternative Providers**
- JIRA integration for enterprise task management
- Notion integration for advanced note-taking
- Slack integration for team communication
- Todoist integration for personal task management

## Next Steps

1. **Immediate**: Update integration_functions.py to use Google APIs instead of Zapier
2. **Authentication**: Implement Google OAuth 2.0 flow in Electron app
3. **API Integration**: Create Google Tasks and Calendar API clients
4. **Framework**: Build service registry for future extensibility
5. **Testing**: Validate single sign-on flow and API operations