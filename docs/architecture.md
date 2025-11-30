# Agent Workflow Diagrams

These diagrams visualize the operational flow of the Calendar Agent system, including the new **parallel sub-agent architecture**.

---

## System Architecture Overview

This diagram shows the complete multi-agent system with the **ADK hierarchical sub-agent architecture**.

```mermaid
graph TB
    User[👤 User] --> RootAgent[🤖 Calendar Coordinator]
    
    subgraph ADK["ADK Sub-Agents"]
        RootAgent -->|Delegates to| AvailAgent[Availability Checker]
        RootAgent -->|Delegates to| FacilityAgent[Facility Manager]
        RootAgent -->|Delegates to| ValidatorAgent[Event Validator]
        RootAgent -->|Delegates to| CreatorAgent[Event Creator]
        
        AvailAgent --> Tools1[check_availability<br/>is_working_time]
        FacilityAgent --> Tools2[find_facility<br/>get_facility_info]
        ValidatorAgent --> Tools3[check_policies<br/>check_conflict]
        CreatorAgent --> Tools4[create_event<br/>validate_emails]
    end
    
    subgraph Persistence["Persistence Layer"]
        SessionDB[("Sessions DB<br/>SQLite")]
        MemoryDB[("Memory DB<br/>SQLite")]
        
        RootAgent -->|"After each turn"| SessionDB
        RootAgent -->|"Auto-save"| MemoryDB
        
        SessionDB -.->|"Resumable workflows"| RootAgent
        MemoryDB -.->|"Long-term context"| RootAgent
    end
    
    subgraph External["External Services"]
        Tools1 --> GoogleAPI[Google Calendar API]
        Tools1 --> GoogleSearch["Google Search<br/>for Holidays"]
        Tools1 --> UserPrefs["users.json<br/>Preferences"]
        Tools3 --> GoogleAPI
        Tools4 --> GoogleAPI
        ValidatorAgent --> PolicyJSON[policies.json]
    end
    
    style RootAgent fill:#2e7d32,stroke:#1b5e20,stroke-width:3px,color:#fff
    style AvailAgent fill:#1565c0,stroke:#0d47a1,stroke-width:2px,color:#fff
    style FacilityAgent fill:#1565c0,stroke:#0d47a1,stroke-width:2px,color:#fff
    style ValidatorAgent fill:#e65100,stroke:#bf360c,stroke-width:2px,color:#fff
    style CreatorAgent fill:#6a1b9a,stroke:#4a148c,stroke-width:2px,color:#fff
    style SessionDB fill:#ffd54f,stroke:#fbc02d,stroke-width:2px,color:#000
    style MemoryDB fill:#ffd54f,stroke:#fbc02d,stroke-width:2px,color:#000
```

---

## Sequence Diagram: ADK Delegation Flow

This diagram shows the interaction between the Root Agent and its Sub-Agents.

```mermaid
sequenceDiagram
    actor User
    participant Root as Calendar Coordinator
    participant Avail as Availability Checker
    participant Facility as Facility Manager
    participant Validator as Event Validator
    participant Creator as Event Creator

    User->>Root: "Schedule meeting with Team tomorrow 2pm, need projector"
    
    Note over Root: Parse request & Plan delegation
    
    rect rgba(245, 245, 245, 0.31)
        Note right of Root: Step 1: Check Availability
        Root->>Avail: Check availability for Team
        Avail->>Avail: Resolve team members
        Avail->>Avail: Check FreeBusy
        Avail-->>Root: "All available"
    end
    
    rect rgba(245, 245, 245, 0.31)
        Note right of Root: Step 2: Find Room
        Root->>Facility: Find room with projector
        Facility->>Facility: Search rooms
        Facility-->>Root: "Conference Room A"
    end
    
    rect rgba(245, 245, 245, 0.31)
        Note right of Root: Step 3: Validate
        Root->>Validator: Validate event details
        Validator->>Validator: Check policies
        Validator->>Validator: Check conflicts
        Validator-->>Root: "Valid (no violations)"
    end
    
    rect rgba(245, 245, 245, 0.31)
        Note right of Root: Step 4: Create
        Root->>Creator: Create event
        Creator->>Creator: Validate emails
        Creator->>Creator: Call API
        Creator-->>Root: "Event created: Link..."
    end
    
    Root-->>User: "✅ Event scheduled! Link: ..."
```

---

## State Diagram: Enhanced with Sub-Agent States

This diagram represents the logical states of the system including sub-agent orchestration.

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> ParsingInput: User Request
    
    state "Validating Emails" as Validate
    state "Comprehensive Validation" as CompValidate
    state "Parallel Availability Check" as ParallelCheck
    state "Policy Validation" as PolicyValidate
    state "Creating Event" as Create
    state "Awaiting User Input" as Await

    ParsingInput --> Validate: Attendees present
    ParsingInput --> CompValidate: No attendees

    Validate --> Await: Invalid/Typo found
    Await --> Validate: User correction
    Validate --> CompValidate: All emails valid

    state CompValidate {
        [*] --> ParallelCheck
        [*] --> PolicyValidate
        [*] --> TimezoneCheck
        [*] --> RoomCheck
        
        state ParallelCheck {
            [*] --> SpawnSubAgents
            SpawnSubAgents --> RunningConcurrently
            RunningConcurrently --> AggregateResults
            AggregateResults --> [*]
        }
        
        PolicyValidate --> [*]
        TimezoneCheck --> [*]
        RoomCheck --> [*]
    }

    CompValidate --> Await: Blocking issues found
    CompValidate --> Create: Validation passed
    Await --> CompValidate: User provides corrections

    Create --> Idle: Success
    Create --> Await: API Error

    Await --> Idle: User cancels
```

---

## Parallel Execution Flow

This diagram visualizes how the parallel sub-agents execute concurrently.

```mermaid
gantt
    title Parallel Availability Checking Timeline
    dateFormat X
    axisFormat %L ms

    section Sequential (Old)
    Check Attendee 1 :0, 1000
    Check Attendee 2 :1000, 2000
    Check Attendee 3 :2000, 3000
    Check Attendee 4 :3000, 4000
    Check Attendee 5 :4000, 5000
    Check Attendee 6 :5000, 6000
    Check Attendee 7 :6000, 7000
    Check Attendee 8 :7000, 8000
    Check Attendee 9 :8000, 9000
    Check Attendee 10 :9000, 10000

    section Parallel (New)
    Sub-Agent 1 :crit, 0, 1200
    Sub-Agent 2 :crit, 0, 1100
    Sub-Agent 3 :crit, 0, 1300
    Sub-Agent 4 :crit, 0, 1150
    Sub-Agent 5 :crit, 0, 1250
    Sub-Agent 6 :crit, 0, 1180
    Sub-Agent 7 :crit, 0, 1220
    Sub-Agent 8 :crit, 0, 1190
    Sub-Agent 9 :crit, 0, 1280
    Sub-Agent 10 :crit, 0, 1240
```

**Note**: Sequential execution takes ~10 seconds, while parallel execution completes in ~1.3 seconds (slowest agent) = **7.7x faster**

---

## Data Flow Diagram

This diagram shows how data flows through the sub-agent system.

```mermaid
flowchart LR
    Input[User Input:<br/>10 attendees,<br/>date, time] --> Parser[Natural Language<br/>Parser]
    
    Parser --> EventData{Event<br/>Details}
    
    EventData --> Validator[Comprehensive<br/>Validator]
    
    subgraph "Parallel Validation"
        Validator --> V1[Calendar<br/>Conflicts]
        Validator --> V2[Room<br/>Availability]
        Validator --> V3[Timezone<br/>Check]
        Validator --> V4[Policy<br/>Rules]
        
        V1 --> ParallelCoord[Parallel<br/>Coordinator]
        
        subgraph "Parallel Sub-Agents"
            ParallelCoord --> SA1[Agent 1]
            ParallelCoord --> SA2[Agent 2]
            ParallelCoord --> SA3[Agent N]
        end
        
        SA1 --> R1[Result 1]
        SA2 --> R2[Result 2]
        SA3 --> RN[Result N]
        
        R1 --> Aggregator[Result<br/>Aggregator]
        R2 --> Aggregator
        RN --> Aggregator
        
        Aggregator --> V1
    end
    
    V1 --> FinalResult{Validation<br/>Result}
    V2 --> FinalResult
    V3 --> FinalResult
    V4 --> FinalResult
    
    FinalResult -->|Valid| CreateEvent[Create<br/>Event]
    FinalResult -->|Invalid| UserFeedback[Return<br/>Issues]
    
    CreateEvent --> Success[✅ Success]
    UserFeedback --> User[👤 User]
    Success --> User
    
    style Validator fill:#e65100,stroke:#bf360c,stroke-width:2px,color:#fff
    style ParallelCoord fill:#1565c0,stroke:#0d47a1,stroke-width:2px,color:#fff
    style FinalResult fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff
```

---

## Component Diagram

This diagram shows the system's component architecture.

```mermaid
graph TB
    subgraph "Root Agent Layer"
        RootAgent[Calendar Agent<br/>google.adk.Agent]
    end
    
    subgraph "Sub-Agent Layer"
        subgraph "Stage 1: Performance"
            Coordinator[ParallelAvailabilityCoordinator]
            AvailChecker[AvailabilityCheckerAgent]
        end
        
        subgraph "Stage 2: Validation"
            Validator[ConflictValidationAgent]
            PolicyEngine[PolicyEngine]
        end
    end
    
    subgraph "Integration Layer"
        Tools[tools/ package]
        AsyncWrapper[async wrapper functions]
    end
    
    subgraph "External Services"
        GoogleCal[Google Calendar API]
        PolicyJSON[policies.json]
    end
    
    subgraph "Observability"
        ReasoningEngine[ReasoningEngine]
    end
    
    RootAgent --> CalTools
    CalTools --> AsyncWrapper
    AsyncWrapper --> Coordinator
    AsyncWrapper --> Validator
    
    Coordinator --> AvailChecker
    AvailChecker --> GoogleCal
    
    Validator --> Coordinator
    Validator --> PolicyEngine
    PolicyEngine --> PolicyJSON
    
    RootAgent --> ReasoningEngine
    Coordinator --> ReasoningEngine
    Validator --> ReasoningEngine
    
    style RootAgent fill:#2e7d32,stroke:#1b5e20,stroke-width:3px,color:#fff
    style Coordinator fill:#1565c0,stroke:#0d47a1,stroke-width:2px,color:#fff
    style Validator fill:#e65100,stroke:#bf360c,stroke-width:2px,color:#fff
    style ReasoningEngine fill:#6a1b9a,stroke:#4a148c,stroke-width:2px,color:#fff
```

---

## Performance Comparison

Visual representation of performance improvement:

```mermaid
graph LR
    subgraph "Before: Sequential"
        A1[Check 1<br/>1s] --> A2[Check 2<br/>1s]
        A2 --> A3[Check 3<br/>1s]
        A3 --> A4[...<br/>...]
        A4 --> A5[Check 10<br/>1s]
        A5 --> Result1[Total: 10s]
    end
    
    subgraph "After: Parallel"
        B1[Agent 1<br/>1s]
        B2[Agent 2<br/>1s]
        B3[Agent 3<br/>1s]
        B4[...<br/>...]
        B5[Agent 10<br/>1s]
        
        B1 --> Result2[Total: 1.5s]
        B2 --> Result2
        B3 --> Result2
        B4 --> Result2
        B5 --> Result2
    end
    
    Result1 -.->|"6.7x slower"| Comparison{Performance}
    Result2 -.->|"6.7x faster"| Comparison
    
    style Result1 fill:#c62828,stroke:#b71c1c,stroke-width:2px,color:#fff
    style Result2 fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff
    style Comparison fill:#1565c0,stroke:#0d47a1,stroke-width:2px,color:#fff
```

---

## Observable Reasoning Flow

How the reasoning engine integrates with the sub-agent system:

```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant Reasoning as ReasoningEngine
    participant SubAgents as Sub-Agents

    User->>Agent: Schedule meeting
    Agent->>Reasoning: 💭 [PLANNING] "Analyzing request"
    
    Agent->>SubAgents: Start parallel checks
    SubAgents->>Reasoning: 💭 [DECISION] "Spawning 10 sub-agents"
    
    loop For each sub-agent result
        SubAgents->>Reasoning: 💭 [VALIDATION] "alice@: Available"
        SubAgents->>Reasoning: 💭 [CONCERN] "bob@: Busy"
    end
    
    SubAgents->>Reasoning: 💭 [ANALYSIS] "8 available, 2 busy (1.42s)"
    
    Agent->>Reasoning: 💭 [RECOMMENDATION] "Suggest alternative time"
    
    Reasoning-->>User: Show complete reasoning chain
    Agent-->>User: Final response with context
```

---

## Session & Memory Management

The agent now maintains persistent sessions and long-term memory using SQLite databases.

```mermaid
graph TB
    User[👤 User] -->|"Interaction"| Agent[🤖 Calendar Coordinator]
    
    Agent -->|"Each turn"| SessionService[DatabaseSessionService]
    Agent -->|"After callback"| MemoryService[SQLiteMemoryService]
    
    SessionService --> SessionDB[("calendar_agent_sessions.db")]
    MemoryService --> MemoryDB[("calendar_agent_memory.db")]
    
    SessionDB -->|"Resume"| Agent
    MemoryDB -->|"Context"| Agent
    
    subgraph "Persistence Features"
        F1["- Full conversation history"]
        F2["- Resumable workflows"]
        F3["- Long-term memory"]
        F4["- Full-text search"]
    end
    
    style Agent fill:#2e7d32,stroke:#1b5e20,stroke-width:3px,color:#fff
    style SessionDB fill:#ffd54f,stroke:#fbc02d,stroke-width:2px,color:#000
    style MemoryDB fill:#ffd54f,stroke:#fbc02d,stroke-width:2px,color:#000
```

### How It Works

1. **Session Persistence**: Every user interaction is stored in `data/calendar_agent_sessions.db`
   - Allows resuming conversations later
   - Tracks full interaction history per session ID
   
2. **Memory Storage**: Important information is extracted and stored in `data/calendar_agent_memory.db`
   - Uses SQLite FTS (Full-Text Search) for efficient retrieval
   - Automatically saves context after each agent turn
   - Searchable with `session_memory_manager.search_memory(query)`

3. **Database Schema**:
   - **Sessions**: Stores events, states, and metadata per session
   - **Memories**: Stores content with full-text search support
   
### Usage Example

```python
from scheduler_agent.agent import session_memory_manager

# Resume a previous conversation
await session_memory_manager.run_session(
    ["What did we discuss last time?"],
    session_id="previous-session-123"
)

# Search through memories
memories = await session_memory_manager.search_memory("meeting rooms")
```

---

## Key Implementation Features

### Multi-Agent Architecture
- **Root Agent**: Main orchestrator using Google ADK
- **Parallel Sub-Agents**: Specialized agents for concurrent execution
- **Validation Agent**: Multi-dimensional validation coordinator
- **Policy Engine**: Rule-based validation system

### Performance Characteristics
- **Sequential**: O(n) where n = number of attendees
- **Parallel**: O(1) + network latency (constant time regardless of attendees)
- **Speedup**: 5-10x for typical use cases

### Observable Reasoning
- All agents log to shared ReasoningEngine
- Complete transparency of decision-making
- Real-time thought streaming
- Helpful for debugging and user trust

---

## Legend

| Symbol | Meaning |
|--------|---------|
| 🤖 | Root Agent |
| 👤 | User |
| 💭 | Thought/Reasoning |
| ✓ | Success/Available |
| ⚠️ | Warning |
| ❌ | Error/Blocking Issue |
| ✅ | Completed Successfully |

---

*These diagrams represent the enhanced calendar agent system with parallel sub-agent architecture implemented in November 2025.*
