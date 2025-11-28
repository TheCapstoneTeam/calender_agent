# Agent Workflow Diagrams

These diagrams visualize the operational flow of the Calendar Agent (`root_agent`).

## Sequence Diagram
This diagram shows the interaction between the User, the Agent, and its tools during a scheduling request.

```mermaid
sequenceDiagram
    actor User
    participant Agent as Calendar Agent
    participant EmailUtils as Email Validator
    participant CalTools as Calendar Tools
    participant GoogleAPI as Google Calendar API

    User->>Agent: "Schedule meeting with bob@example.com tomorrow at 2pm"
    
    Note over Agent: Parse natural language input

    rect rgb(240, 248, 255)
        Note right of Agent: Validation Phase
        Agent->>EmailUtils: validate_emails(["bob@example.com"])
        EmailUtils-->>Agent: {valid: ["bob@example.com"], invalid: []}
    end

    rect rgb(255, 250, 240)
        Note right of Agent: Conflict Check Phase
        Agent->>CalTools: check_conflict(date, start, end)
        loop For each user calendar
            CalTools->>GoogleAPI: events().list()
            GoogleAPI-->>CalTools: [Events]
        end
        CalTools-->>Agent: {conflict: False, events: []}
    end

    alt No Conflict
        rect rgb(240, 255, 240)
            Note right of Agent: Execution Phase
            Agent->>CalTools: create_event(...)
            CalTools->>GoogleAPI: events().insert()
            GoogleAPI-->>CalTools: Event Object
            CalTools-->>Agent: {status: "success", link: "..."}
        end
        Agent-->>User: "Event scheduled successfully! Here is the link..."
    else Conflict Detected
        Agent-->>User: "I found a conflict at that time. Would you like to reschedule?"
    end
```

## State Diagram
This diagram represents the logical states of the agent during a transaction.

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> ParsingInput: User Request
    
    state "Validating Emails" as Validate
    state "Checking Conflicts" as Check
    state "Creating Event" as Create
    state "Awaiting User Input" as Await

    ParsingInput --> Validate: Attendees present
    ParsingInput --> Check: No attendees

    Validate --> Await: Invalid/Typo found
    Await --> Validate: User correction
    Validate --> Check: All emails valid

    Check --> Await: Conflict found
    Await --> Check: User provides new time
    Check --> Create: No conflict

    Create --> Idle: Success
    Create --> Await: API Error

    Await --> Idle: User cancels
```
