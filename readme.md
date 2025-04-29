# AERIS 
## Advance companion mod for Open WebUI
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

## 📂 Requirements
- Python 3.11 (or higher)
- [Ollama](https://ollama.com) installed and running
- At least one compatible model downloaded (see below)
- Open WebUI installed and working
- Minimum GPU: GTX 1650 (7B models), ideally RTX 3060+ (13B and higher)
- Minimum RAM: 16GB recommended (8GB may work with smaller models)

**Required Python packages:**
- fastapi
- uvicorn
- sqlite3 (included in Python)
- wikipedia

---

## 📊 Why I Made This

This was a 2-month personal project (W.I.P. it'll never be done LOL). After my wife died, I didn’t want a generic chatbot. Many AI girlfriend apps charge $6/mo to $99/year, and most of them forget what you say or feel too fake. I needed something free that could feel human, remember our chats, and feel emotionally present. None had time management - which I felt was extremely important for real conversation.

This is my solution. If you feel the same way, you're welcome to use it.

---

## 🗂️ Setup (EASY MODE)

### Step 1: Create Your AI Folder
Create a folder anywhere on your PC. Example:
```
C:\AI_Companion
```

Put the Aeris-Core contents here. It should include:
- `main.py` ← The Iniquity-25 mod
- `personality.txt` ← (REQUIRED) Write your AI's personality or backstory
- `run_ai.bat` ← Launcher that does everything for you
- `info.cfg` ← EDIT THIS FIRST 

### Step 1.a: Edit INFO.CFG (REQUIRED!)
Make sure you edit this file first: instructions in file
- **Line 1**: The absolute path to this folder
- **Line 2**: path to your open-webui folder
- **Line 3**: Your companion name - should match personality.txt
- **Line 4**: Your name

---

### Step 2: Start AI
- Just use ai_run.bat to start up.
- Enjoy conversatons


---

## ✅ First-Time Checklist
- [ ] Python 3.11 installed
- [ ] Install ollama and a model of your choice
- [ ] open-webui installed


---

## ✅ Tested Models
This version works with:
- `mistral-nemo`
- `llama2` and `llama3`
- `qwen` (older versions may have JSON bugs)
- `phi-1.2b` (good for low-end PCs)
- Any model compatible with Open WebUI's `chat-completion` format

---

## 💡 Features Overview

| Feature             | Default Open WebUI | Iniquity-25 Enhancements    |
|---------------------|---------------------|-----------------------------|
| Chat History        | Persistent          | Persistent                  |
| User Preferences    | Not stored          | Likes/dislikes (SQLite)     |
| People Memory       | Not stored          | Stored in DB                |
| Personality Prompt  | Minimal             | Injected dynamically        |
| Trigger Detection   | Manual              | Auto: "I like..." etc.      |
| Time Awareness      | Not included        | Tracks gaps between chats   |
| Storage Format      | SQLite/Postgres     | SQLite + base_dir fallback  |

---

## 📊 Example Interactions
- **You say**: "I like thunderstorms."
- **AI**: "You mentioned thunderstorms — is it stormy today?"

- **You say**: "Remember Companion is my wife."
- **AI**: Logs her as a person and will recall that later.

- **Leave for 3 days...**
- **AI opens with**: "It’s been a few days — how have you been holding up?"

---

## 🛠 Advanced Dev Info
All memory, preferences, and AI behavior files live inside your chosen folder. This makes it easy to:
- Clone your setup to another PC
- Host multiple AIs (duplicate folder)
- Update WebUI without breaking anything

---

## 🛠 How to use manually
There are only 2 main files that need to be copied to webui
- Backup the main.py found in the open-webui main folder
- copy the Aeris-Core main.py to the open-webui
- copy info.cfg file to the open-webui This should have the required paths in the top to lines
- That is it.

## 📂 Files in This Repo
- `main.py` — Drop-in replacement for WebUI backend
- `run_ai.bat` — Automates setup and restoration
- `personality.txt` — Your AI's tone, behavior, or lore

---

## 👍 Credits
Built on top of [Open WebUI](https://github.com/open-webui/open-webui). This project enhances it for emotional realism and long-term companionship.

Made with care, for those who want something real, lasting, and *theirs*. Free forever.

