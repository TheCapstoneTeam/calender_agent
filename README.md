
## Project Features

### 

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


# Project Setup Guide

This project uses **Python 3.14** and a **virtual environment (venv)**.  
Follow these steps to set up the project on any machine.

---


## 🚀 0. Clone the Repository
```bash
git clone <git@github.com:TheCapstoneTeam/calender_agent.git>
````

---

## 🔐 1. Get your Google API key

If you have not done so, sign up and create an [API key in Google AI Studio](https://aistudio.google.com/app/api-keys). Create new file named `.env` . Then copy the line below and paste the line and your `api key` in the spot indicated.

```bash
GENAI_API_KEY={your_api_key}
```

---

## 🧰 2. Create a Virtual Environment (optional if you decide to install the libraries globally)

The `venv/` folder is **NOT** committed to GitHub, so each teammate must create their own.

Change directory to `calendar_agent` and activate the `venv`.

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

You’re now ready to run the command below:

   ```bash
   uv run python tests/
   adk run scheduler_agent
   ```
---



## 🔍 Inspecting Data

The agent stores data in SQLite databases located in the `data/` directory:
- `data/calendar_agent_sessions.db`: Stores session history.
- `data/calendar_agent_memory.db`: Stores agent memories.

You can inspect these files using various tools:

### VS Code
1. Install the **SQLite** extension (by alexcvzz) or **SQLite Viewer**.
2. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).
3. Type `SQLite: Open Database` and select the `.db` file.
4. Use the SQLite Explorer in the sidebar to browse tables and data.

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
