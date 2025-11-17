# Project Setup Guide

This project uses **Python 3** and a **virtual environment (venv)**.  
Follow these steps to set up the project on any machine.

---

## 🚀 1. Clone the Repository
```bash
git clone <https://github.com/Pro1943/KraggleCapstone.git>
````

---

## 🧰 2. Create a Virtual Environment (EVERY teammate must do this)

The `venv/` folder is **NOT** committed to GitHub, so each teammate must create their own.

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

---

## 📦 3. Install Project Requirements

Run:

```bash
pip install -r requirements.txt
```

---

## ⚠️ 4. Fix for google-generativeai Dependency

The package `google-generativeai` auto-installs an outdated version of `google-api-core`.

Uninstall it:

```bash
pip uninstall google-api-core -y
```

Install working version:

```bash
pip install google-api-core==2.28.1
```

---

## ✔️ Setup Complete!

You’re now ready to run:

```bash
python test.py
```

or any other project script.

---

## 📝 Notes

* Never commit your `venv/` folder.
* Always activate your venv before running scripts.
* If you install new packages, update `requirements.txt` using:

```bash
pip freeze > requirements.txt
```

---