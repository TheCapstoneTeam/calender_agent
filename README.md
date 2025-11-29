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
├── credentials.json              # Google OAuth client credentials
├── main.py                        # Entry point for CLI/manual testing
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
│   │
│   ├── tools/                     # 🔧 Modular tools package (SOLID)
│   │   ├── __init__.py
│   │   ├── availability.py        # Attendee availability checking
│   │   ├── events.py              # Event creation and management
│   │   ├── facilities.py          # Meeting room search and booking
│   │   ├── holidays.py            # 🏖️ Holiday & Vacation logic
│   │   ├── search.py              # Team member lookup
│   │   └── validation.py          # Policy and conflict validation
│   │
│   ├── sub_agents/                # 🤖 ADK hierarchical agents (Capstone)
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
│   ├── facilities.json            # Meeting room definitions
│   ├── policies.json              # Organizational policies
│   └── users.json                 # Team/user data
│
├── examples/                      # 📚 Demo scripts
│   ├── README.md                  # How to run demos
│   ├── adk_agent_demo.py          # Shows ADK architecture
│   ├── parallel_availability_demo.py  # Shows 5-10x speedup
│   └── validation_demo.py         # Shows comprehensive validation
│
├── tests/                         # 🧪 Test suite
│   ├── README.md
│   ├── conftest.py                # Pytest fixtures
│   ├── test_adk_sub_agents.py     # Tests ADK architecture
│   ├── test_calendar_tools.py     # Tests tool functions
│   └── test_validation_stage2.py  # Tests validation system
│
├── docs/                          # 📖 Documentation
│   ├── agent_diagrams.md          # Architecture diagrams
│   ├── advanced_agent_concepts.md # Deep dive on patterns
│   └── ...
│
├── test_timezone.py               # Timezone testing utility
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
