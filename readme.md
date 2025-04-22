# INIQUITY - 25 
## Drop-In `main.py` for Open WebUI
**Adds persistent memory, time awareness, personality, and natural conversation flow**

---

## 🧠 What Is This?

This is a drop-in replacement `main.py` and launcher setup for [Open WebUI](https://github.com/open-webui/open-webui). It adds features like:
- Persistent memory (stored in SQLite)
- Time awareness (e.g., "It's been 2 days since we last spoke")
- Real conversation context across sessions
- AI preferences and personality customization

It’s designed to run from your **own folder** without modifying Open WebUI permanently. Easy to set up, easy to update.

---

## 🗂️ Setup (EASY MODE)

### Step 1: Create Your AI Folder
Create a folder anywhere on your PC. Example:
```
C:\AI_Companion\data
```

Put these 3 files in that folder:
- `main.py` ← **From this GitHub repo** (customized backend)
- `personality.txt` ← Write your AI's personality, tone, or backstory here
- `run_ai.bat` ← Launcher that does everything for you

---

### Step 2: Run the Setup Bat
Double-click `run_ai.bat`. It will:
1. Ask you for the name of your virtual environment (like `myAI`)
2. Automatically:
   - Backup the original `main.py`
   - Replace it with your custom version
   - Set up `base_dir.txt` so everything knows where to look
   - Install `wikipedia` (if needed)
   - Launch Open WebUI
   - Restore the original file after you exit

---

## ✅ Tested Models
This version works with:
- `mistral-nemo`
- `llama2` and `llama3`
- `qwen` (some issues with JSON parsing in older versions)
- `phi-1.2b` (lighter model, runs on lower-end systems)
- Anything compatible with Open WebUI chat-completion interface

---

## 💡 Features Overview

| Feature             | Default Open WebUI | This Version              |
|---------------------|---------------------|----------------------------|
| Chat History        | Persistent          | Persistent                 |
| User Preferences    | Not stored          | Likes/dislikes (SQLite)   |
| People Memory       | Not stored          | Stored in DB              |
| Personality Prompt  | Minimal             | Injected at runtime       |
| Trigger Detection   | Manual              | Auto: "I like..." etc.    |
| Time Awareness      | Not included        | Tracks visit gaps         |
| Storage Format      | SQLite/Postgres     | SQLite + base_dir fallback|

---

## 📊 Example Interactions
- **You say**: "I like thunderstorms."
- **AI says (next session)**: "You mentioned thunderstorms — is it stormy today?"

- **You say**: "Remember Companion is my wife."
- **AI**: Logs her as a person and will reference it naturally later.

- **Leave for 3 days...**
- **AI opens with**: "It’s been a few days — how have you been holding up?"

---

## 🛠 Advanced Dev Info
All memory files and database stay inside the custom folder. This makes it easy to:
- Port your setup to another PC
- Maintain multiple AIs (just duplicate the folder)
- Update WebUI without breaking your mod

---

## 📂 Files in This Repo
- `main.py` — Drop-in replacement backend
- `run_ai.bat` — Automates setup + restore
- `personality.txt` — Your custom AI backstory

---

## 🤝 Credits
Built on the shoulders of [Open WebUI](https://github.com/open-webui/open-webui). This project adds enhancements on top of their amazing work.

Created with ❤️ for AI companionship, tinkering, and emotional realism.


