Call every day.# Architecture & Technical Design

## Technology Stack & Decisions

### Core Technologies
- **Voice Processing**: Gemini 2.0 Flash Live API (unified STT+LLM+TTS)
- **Framework**: Pipecat-AI for voice agent orchestration
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

**2024-05-25 – Pipecat Framework Adoption**
- **Decision**: Adopt Pipecat-AI for voice agent development and STT/TTS integration
- **Rationale**: Robust real-time audio processing, structured conversational logic management

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

## Current Implementation Architecture (Gemini Live API)

```mermaid
graph TB
    subgraph "Voice Assistant System"
        UI[Electron UI<br/>WebSocket Client]
        
        subgraph "User Input Node"
            Hotkey[Hotkey Registration<br/>Ctrl+Shift+X]
            AudioCapture[Audio Capture<br/>LocalAudioTransport]
        end
        
        subgraph "Pipecat Framework"
            Pipeline[Pipecat Pipeline]
            WSBridge[WebSocket Bridge<br/>Processor]
            GeminiLive[Gemini 2.0 Flash Live Service<br/>STT + Core LLM + TTS]
            IntentParserFP[IntentParserFrameProcessor]
            CommandProcessorFP[CommandProcessorFrameProcessor]
        end
        
        subgraph "Missing Components (To Be Built)"
            subgraph "Guardrail Node"
                Validation[Input Validation Layer]
                Clarification[Ambiguity Detection]
            end
            
            subgraph "LLM Node"
                CommandProcessing[Command/Intent Classification]
                ParamExtraction[Parameter Extraction]
            end
            
            subgraph "Tool Node"
                TimerTool[Timer System]
                NoteTool[Note-Taking]
                ZapierConnector[Zapier Integration]
            end
            
            subgraph "Memory Node"
                DB[Firebase Firestore<br/>Internal State & Metadata]
                SessionStore[Conversation History]
                UserPrefs[User Preferences]
            end
            
            subgraph "Control Node"
                Orchestrator[Workflow Orchestration]
                StateManager[Session State Management]
            end
            
            subgraph "Fallback Node"
                ErrorHandler[Error Recovery]
                Retry[API Retry Logic]
                Fallback[Degraded Operation]
            end
        end
    end
    
    subgraph "External Services (To Be Integrated)"
        Zapier[Zapier Webhooks]
        subgraph "Productivity Tools"
            Trello[Trello]
            Notion[Notion]
            GCal[Google Calendar]
        end
    end
    
    %% Current Working Flow
    Hotkey --> UI
    UI --> WSBridge
    WSBridge --> Pipeline
    Pipeline --> AudioCapture
    AudioCapture --> GeminiLive
    GeminiLive --> Pipeline
    Pipeline --> WSBridge
    WSBridge --> UI
    
    %% Current Working Flow - Extended
    GeminiLive --> IntentParserFP
    IntentParserFP --> CommandProcessorFP
    CommandProcessorFP --> Pipeline %% (Output to TTS or further processing)

    %% Future Integration Flow (To Be Built)
    CommandProcessorFP --> ParamExtraction
    ParamExtraction -.-> Orchestrator
    Orchestrator -.-> TimerTool
    Orchestrator -.-> NoteTool
    Orchestrator -.-> ZapierConnector
    ZapierConnector -.-> Zapier
    Zapier -.-> Trello
    Zapier -.-> Notion
    Zapier -.-> GCal
    
    %% Data Flow (To Be Built)
    CommandProcessing -.-> SessionStore
    Orchestrator -.-> UserPrefs
    SessionStore -.-> DB
    UserPrefs -.-> DB
    
    %% Error Handling (To Be Built)
    GeminiLive -.-> ErrorHandler
    ZapierConnector -.-> ErrorHandler
    ErrorHandler -.-> Retry
    Retry -.-> Fallback

    classDef workingNode fill:#4CAF50,stroke:#333,stroke-width:2px;
    classDef missingNode fill:#f96,stroke:#333,stroke-width:2px;
    classDef externalNode fill:#2196F3,stroke:#333,stroke-width:2px;
    
    class UI,Hotkey,AudioCapture,Pipeline,WSBridge,GeminiLive workingNode;
    class Validation,Clarification,TimerTool,NoteTool,ZapierConnector,DB,SessionStore,UserPrefs,Orchestrator,StateManager,ErrorHandler,Retry,Fallback missingNode;
    class IntentParserFP,CommandProcessorFP,ParamExtraction workingNode;
    class Zapier,Trello,Notion,GCal externalNode;
```

## Current Working Implementation

### ✅ **Implemented Components**
1. **Electron UI**: Desktop app with hotkey activation (Ctrl+Shift+X)
2. **WebSocket Bridge**: Real-time communication between UI and backend
3. **Pipecat Pipeline**: Voice processing orchestration framework
4. **Gemini Live API**: Unified STT + LLM + TTS service
5. **Audio Capture**: LocalAudioTransport with microphone selection

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
- **Integrations**: Zapier webhooks
- **External APIs**: Trello, Notion, Google Calendar

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

## Next Steps

1. Set up Electron project structure
2. Implement hotkey registration
3. Create audio capture module
4. Configure Google Cloud Speech-to-Text API
5. Build initial UI shell for testing