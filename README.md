````markdown
# Project Setup Guide

This project uses Python and requires installing several dependencies before running.

## 📦 Installation

First, install all required packages:

```bash
pip install -r requirements.txt
````

## ⚠️ Important Note (google-api-core)

The package `google-generativeai` automatically installs `google-api-core==2.25.1`,
but the project requires **google-api-core >= 2.28.1**.

So uninstall the old one:

```bash
pip uninstall google-api-core
```

Then install the correct version:

```bash
pip install google-api-core==2.28.1
```

## ✔️ You’re Ready to Go

After completing the steps above, the environment should be correctly set up
and the project will run without dependency issues.

---

If any installation conflicts appear (backtracking issues, version loops, etc.),
repeat the uninstall/install step for `google-api-core`.