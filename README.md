# Project Setup Guide

This project uses **Python 3.14** and a **virtual environment (venv)**.  
Follow these steps to set up the project on any machine.

---


## 🚀 0. Clone the Repository
```bash
git clone <git@github.com:TheCapstoneTeam/calender_agent.git>
````

---

## 1. Get your Google API key

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
## 4. Folder Structure

At this point, your directory should look like this.

```
.
├── README.md
├── __init__.py
├── credentials.json
├── main.py
├── pyproject.toml
├── requirements.txt
├── scheduler_agent
│   ├── __pycache__/
│   ├── agent.py
│   ├── auth.py
│   └── calendar_tools.py
├── test_timezone.py
├── token.json
└── uv.lock
```

---

## ✔️ Setup Complete!

You’re now ready to run the command below:

   ```bash
   uv run python test_timezone.py 
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