# AI Calendar Agent

**Autonomous Meeting Scheduling for Enterprise Teams**

## ⭐ Problem Statement

Scheduling meetings in enterprise environments is **complex and time-consuming**. Consider the challenge of coordinating a meeting for 10+ people across different timezones, while finding an available conference room with the right equipment, checking organizational policies, and avoiding conflicts.

**The Traditional Approach:**
- 🐌 **Slow**: Checking 10 attendees sequentially takes 10+ seconds
- 🤕 **Error-prone**: Manual timezone conversions, missed conflicts
- 😓 **Tedious**: Multiple tools (Calendar, Email, Room booking, Policy docs)
- 💸 **Costly**: ~100 hours/year wasted on scheduling for a mid-sized company

**Our Solution:**
An autonomous AI agent that handles the entire scheduling workflow through intelligent orchestration of specialized sub-agents, reducing scheduling time by **5-10x** while ensuring policy compliance and conflict-free meetings.
 

## Project Features

### 🤖 Multi-Agent System

Our system uses **Google ADK's hierarchical agent architecture** with a coordinator and four specialized sub-agents that work together to handle complex scheduling tasks:

```
Calendar Coordinator (Root Agent)
├── 🔍 Availability Checker → Parallel FreeBusy API calls
├── 🏢 Facility Manager     → Room search and booking
├── ✅ Event Validator      → Policy and conflict checking
└── 📅 Event Creator        → Calendar event creation
```

**Key Benefits:**
- **Parallel Execution**: Check 10 attendees in ~1.5s instead of 10s (7x faster)
- **Specialization**: Each sub-agent has focused responsibilities and tools
- **Scalability**: Add new sub-agents without changing existing code
- **Fault Isolation**: Sub-agent failures don't crash the entire system

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed diagrams.

### 🔧 Tools

The agent leverages multiple tools to interact with external systems and data sources:

| Tool Category | Tools | Purpose |
|--------------|-------|---------|
| **Calendar Integration** | `check_availability`, `create_event`, `check_conflict` | Google Calendar API for FreeBusy queries and event management |
| **Data Management** | `get_team_members`, `find_facility`, `get_user_details` | Search team/facility data from JSON files |
| **Validation** | `validate_emails`, `check_policies` | Email validation and org policy enforcement |
| **Intelligence** | `search_holidays`, `get_local_timezone` | Holiday detection via Google Search, timezone handling |

**Function Calling**: All tools are exposed to the LLM via Google ADK's function calling, allowing the agent to autonomously select and execute the right tool for each task.

### ⚙️ Context Engineering

Long conversations can quickly exhaust token limits. Our **ContextCompactor** optimizes context by intelligently summarizing older messages while preserving recent interactions:

**Strategy**: Summary + Recent Window
- Compacts 50+ message histories into a concise summary
- Keeps the last N messages for immediate context
- Reduces token usage by ~70% without losing continuity

**Example** (from `demo/run_demo.py`):
```python
compacted = context_compactor.compact_messages(messages)
# Original: 55 messages (5,500 tokens)
# Compacted: Summary + 10 recent messages (1,500 tokens)
# Savings: ~73% tokens
```

This enables long-running conversations without hitting API limits or degrading response quality.

### 🧠 Session & Memory

The scheduler agent wires a persistent session store via SQLite and an in-memory memory service through `scheduler_agent.session_memory`. The root agent attaches `preload_memory_tool` to every turn and uses an `after_agent_callback` to keep conversations synchronized with memory, so your history survives restarts and is replayable through `session_memory_manager`.

The compact session store lives at `data/calendar_agent_sessions.db`, and you can programmatically extend or replay conversations with the helper exported from `scheduler_agent.agent`:

```python
from scheduler_agent.agent import session_memory_manager

await session_memory_manager.run_session(
   ["Hi again", "What do you remember from earlier?"],
   session_id="user-follow-up",
)
```

Use `session_memory_manager.search_memory("favorite color")` or `get_session_events` to inspect what the agent persisted from prior conversations.


### 🔍 Observability: Chain-of-Thought Reasoning

Transparency is critical for trust in autonomous agents. Our **ReasoningEngine** implements Chain-of-Thought (CoT) to make decision-making visible:

**Thought Types**:
- 💭 **PLANNING**: High-level strategy ("Analyzing request for 10 attendees")
- 💭 **DECISION**: Tactical choices ("Spawning 10 parallel sub-agents")
- 💭 **VALIDATION**: Individual checks ("alice@: Available ✓")
- 💭 **CONCERN**: Potential issues ("bob@: Busy - 2 conflicts")
- 💭 **ANALYSIS**: Result synthesis ("8 available, 2 busy (1.42s, 7x speedup)")

**Example Output**:
```
💭 [PLANNING] Checking availability for 10 attendees in parallel
💭 [DECISION] Spawning 10 AvailabilityChecker sub-agents
💭 [VALIDATION] alice@example.com: Available ✓
💭 [VALIDATION] bob@example.com: Available ✓
💭 [CONCERN] carol@example.com: Busy (2 conflicts)
💭 [ANALYSIS] Results: 8 available, 2 busy (1.42s, ~7.0x speedup)
```

**Benefits**:
- 🐛 **Debugging**: Trace exactly where reasoning went wrong
- 🤝 **Trust**: Users understand why decisions were made
- 📊 **Metrics**: [future improvements] Measure sub-agent performance in real-tim

---

# Project Setup Guide

This project uses **Python 3.14** and a **virtual environment (venv)**.  
Follow these steps to set up the project on any machine.

---


## 🚀 0. Clone the Repository
```bash
git clone <git@github.com:TheCapstoneTeam/calender_agent.git>
````

---

## 🔐 1. Setup your authorizations

### Get your Google API key

If you have not done so, sign up and create an [API key in Google AI Studio](https://aistudio.google.com/app/api-keys). Create new file named `.env` . Then copy the line below and paste the line and your `api key` in the spot indicated.

```bash
GENAI_API_KEY={your_api_key}
```

### Get your Google credentials for the Calendar API

Follow the guide in [Create access credentials](https://developers.google.com/workspace/guides/create-credentials#oauth-client-id) from Google Cloud Workspace.

---

## 🧰 2. Create a Virtual Environment (optional if you decide to install the libraries globally)

The `venv/` folder is **NOT** committed to GitHub, so each teammate must create their own.

Change directory to `calendar_agent` and activate the `venv`. See default [venv manager](https://docs.python.org/3/library/venv.html) docs in python.

### Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```
OR
```bash
uv venv
source .venv/bin/activate
```

See [uv docs](https://docs.astral.sh/uv/) for more guides and installation instructions.

---

## 📦 3. Install Project Requirements

1. Make sure you have activated the virtual environment

1. Run:

   ```bash
   pip install -r requirements.txt
   ```

   OR

   ```bash
   uv pip install -r requirements.txt
   ```
---
## 📁 4. Folder Structure

At this point, your directory should look like this.

```
.
├── README.md
├── __init__.py
├── pyproject.toml                 # Project metadata and dependencies
├── requirements.txt               # Python package dependencies
├── scheduler_agent/
│   ├── __pycache__/
│   ├── agent.py                   # Root ADK agent (coordinates sub-agents)
│   ├── auth.py                    # Google Calendar OAuth authentication
│   ├── data_manager.py            # Team/facility data management
│   ├── datetime_utils.py          # Date/time parsing and timezone handling
│   ├── email_utils.py             # Email validation utilities
│   ├── reasoning_engine.py        # Observable reasoning/thinking system
│   ├── session_memory.py          # 🧠 Session & memory persistence (SQLite)
│   │
│   ├── tools/                     # 🔧 Modular tools package 
│   │   ├── __init__.py
│   │   ├── availability.py        # Attendee availability checking
│   │   ├── events.py              # Event creation and management
│   │   ├── facilities.py          # Meeting room search and booking
│   │   ├── holidays.py            # 🏖️ Holiday & Vacation logic
│   │   ├── search.py              # Team member lookup
│   │   ├── validation.py          # Policy and conflict validation
│   │
│   ├── sub_agents/                # 🤖 ADK hierarchical agents
│   │   ├── __init__.py
│   │   ├── availability_agent.py  # Sub-agent: Checks availability
│   │   ├── creator_agent.py       # Sub-agent: Creates events
│   │   ├── facility_agent.py      # Sub-agent: Manages rooms
│   │   └── validator_agent.py     # Sub-agent: Validates policies
│   │
│   └── parallel_execution/        # ⚡ Performance optimization (async)
│       ├── __init__.py
│       ├── README.md              # Explains parallel vs ADK approach
│       ├── availability_checker.py    # Async availability sub-agent
│       ├── parallel_coordinator.py    # Orchestrates parallel execution
│       ├── policy_engine.py           # Configurable policy rules
│       └── validation_agent.py        # Multi-dimensional validator
│
├── data/                          # Static data files
│   ├── calendar_agent_sessions.db # 💾 Session persistence (SQLite)
│   ├── calendar_agent_memory.db   # 💾 Long-term memory (SQLite + FTS)
│   ├── facilities.json            # Meeting room definitions
│   ├── policies.json              # Organizational policies
│   └── users.json                 # Team/user data
│
├── tests/                         # 🧪 Test suite
│   ├── README.md
│   ├── conftest.py                # Pytest fixtures
│   ├── test_adk_sub_agents.py     # Tests ADK architecture
│   ├── test_calendar_tools.py     # Tests tool functions
│   └── test_validation_stage2.py  # Tests validation system
|
├── token.json                     # Google OAuth access token (auto-generated)
└── uv.lock                        # Dependency lock file (if using uv)
```

---


## ✔️ Setup Complete!

You’re now ready to run the commands below

Run tests:
   ```bash
   python -m pytest tests/         # Run tests
   ```

Expected output:

   ```
   ==== 92 passed, 1 skipped, 1 warning in 10.44s  ====
   ```

Run the agent:
   ```bash
   adk run scheduler_agent         # Run the agent
   ```


---


## 🔍 Inspecting Data

The agent stores data in SQLite databases located in the `data/` directory:
- `data/calendar_agent_sessions.db`: Stores session history.
- `data/calendar_agent_memory.db`: Stores agent memories.

You can inspect these files using various tools:

### VS Code
1. Install the **SQLite Viewer** extension (by Florian Klampfer).
2. Click on a `.db` or `.sqlite` in the Explorer
2. A new panel would open to show database's contents.

### DBeaver
1. Create a new connection and select **SQLite**.
2. Browse to the `data/` folder and select the `.db` file.
3. Connect and browse tables in the Database Navigator.

### SQLiteStudio
1. Click **Database** > **Add a database**.
2. Select the `.db` file from the `data/` directory.
3. Double-click the table names to view data.


---

## 📝 Notes

* Never commit your `venv/` folder.
* Always activate your venv before running scripts.
* `pyproject.toml` and `*.lock` are present if you use `uv` as your python manager (or another environment manager that uses the `pyproject.toml` file).
* `token.json` file will be created when you're running the `adk run` command for the first time, and have successfully authorized the agent to access your Google Calendar
* If you install new packages, update `requirements.txt` using:

```bash
pip freeze > requirements.txt
```

---
