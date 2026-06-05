# DADDY — Personal AI Assistant

> A fully local, 100% free, voice-controlled personal AI assistant that runs entirely on your Windows 11 laptop. No cloud. No subscriptions. No internet required. Everything — the AI brain, speech recognition, text-to-speech, memory, and document processing — runs on your own machine.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Guide](#setup-guide)
- [Running the Project](#running-the-project)
- [Command Guide](#command-guide)
  - [Special Commands](#special-commands)
  - [File System Commands](#file-system-commands)
  - [Word Document Commands](#word-document-commands)
  - [Knowledge Base Commands](#knowledge-base-commands)
  - [Memory Commands](#memory-commands)
  - [Wake Word & Voice Commands](#wake-word--voice-commands)
- [System Tray Guide](#system-tray-guide)
- [Troubleshooting](#troubleshooting)

---

## Features

- **100% Local & Private** — Nothing leaves your computer. No API keys needed.
- **Wake Word Detection** — Say *"Hey Daddy"* to activate Daddy hands-free.
- **Three Input Modes** — Wake word, voice, or text — switch anytime.
- **File System Control** — Create, delete, move, rename, find files and folders using natural language.
- **Word Document Agent** — Create, read, edit, summarize `.docx` files without opening Word.
- **RAG Knowledge Base** — Index your personal PDFs, Word files, and notes. Ask questions from them.
- **Persistent Memory** — Daddy remembers conversations, preferences, and tasks across sessions.
- **Smart Summarization** — Old conversations automatically summarized to save space.
- **System Tray App** — Runs silently in the Windows taskbar with a right-click menu.
- **Auto-Start on Boot** — Enable Daddy to launch automatically when Windows starts.
- **Graceful Shutdown** — Memory is always saved before closing.

---

## Tech Stack

| Component | Technology |
|---|---|
| AI Brain | Llama 3.2 3B via Ollama |
| Speech to Text | Faster-Whisper (base model) |
| Text to Speech | pyttsx3 |
| Wake Word | Whisper tiny model |
| Vector Database | ChromaDB |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| PDF Reading | pypdf |
| Word Documents | python-docx |
| System Tray | pystray + Pillow |
| Auto Start | Windows Registry via winreg |
| Logging | loguru |
| Terminal UI | rich |

---

## Project Structure

```
Daddy-assistant/
│
├── launcher.py                  ← Main entry point — run this
├── startup.py                   ← Windows auto-start manager
├── main.py                      ← Daddy's core loop
├── config.py                    ← Settings and environment variables
├── .env                         ← Model name, URL, assistant name
├── requirements.txt
│
├── core/
│   ├── llm.py                   ← Llama 3.2 connection via Ollama
│   ├── memory.py                ← In-session conversation memory
│   ├── persistent_memory.py     ← Cross-session long-term memory
│   ├── speech_input.py          ← Mic recording + Whisper STT
│   ├── speech_output.py         ← pyttsx3 TTS engine
│   ├── wakeword.py              ← "Hey Daddy" detector
│   ├── router.py                ← Routes commands to correct agent
│   ├── rag.py                   ← RAG engine (embed, store, retrieve)
│   └── tray.py                  ← System tray icon manager
│
├── agents/
│   ├── base_agent.py            ← Abstract base all agents inherit
│   ├── filesystem_agent.py      ← File and folder operations
│   ├── word_agent.py            ← Microsoft Word operations
│   └── rag_agent.py             ← Knowledge base operations
│
├── knowledge/
│   ├── raw_docs/                ← Drop your documents here
│   └── vector_store/            ← ChromaDB saves here automatically
│
├── memory/
│   └── persistent_memory.json   ← Long-term memory storage
│
├── assets/
│   └── daddy_icon.png           ← System tray icon
│
└── logs/
    └── assistant.log            ← Debug and error logs
```

---

## Setup Guide

Follow every step carefully. This guide assumes a fresh Windows 11 PC.

### Step 1 — Install Python 3.11

1. Go to [https://python.org/downloads](https://python.org/downloads)
2. Download **Python 3.11.x**
3. Run the installer
4. ⚠️ **IMPORTANT:** Check the box **"Add Python to PATH"** before clicking Install

Verify in Command Prompt:
```cmd
python --version
```
Should show `Python 3.11.x`

---

### Step 2 — Install Ollama and Download Llama 3.2

1. Go to [https://ollama.ai](https://ollama.ai)
2. Click **Download for Windows** and run the installer
3. After install, open Command Prompt and run:

```cmd
ollama pull llama3.2
```

This downloads the Llama 3.2 3B model (~2GB). Wait for it to finish.

Verify it works:
```cmd
ollama run llama3.2
```
Type `Hello` and press Enter. You should get a response. Type `/bye` to exit.

---

### Step 3 — Install VS Code (Recommended)

1. Go to [https://code.visualstudio.com](https://code.visualstudio.com)
2. Download and install
3. Install the **Python extension** inside VS Code

---

### Step 4 — Clone or Download the Project

```cmd
cd %USERPROFILE%\Desktop
git clone https://github.com/yourusername/Daddy-assistant.git
cd Daddy-assistant
```

Or download the ZIP from GitHub, extract it to your Desktop, and open the folder.

---

### Step 5 — Create Virtual Environment

Open the project folder in VS Code, then open the terminal (`` Ctrl+` ``) and run:

```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` at the start of your terminal line. Always activate this before running the project.

---

### Step 6 — Install All Dependencies

With venv activated:

```cmd
pip install -r requirements.txt
```

Then install Playwright browser support:

```cmd
playwright install chromium
```

---

### Step 7 — Configure the `.env` File

Open `.env` in the project root and make sure it contains:

```
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
ASSISTANT_NAME=DADDY
```

You can change `ASSISTANT_NAME` to anything you like.

---

### Step 8 — Create the Tray Icon

Run this once to generate Daddy's system tray icon:

```cmd
python assets/create_icon.py
```

This creates `assets/daddy_icon.png`.

---

### Step 9 — Create Required Folders

```cmd
mkdir knowledge\raw_docs
mkdir knowledge\vector_store
mkdir memory
mkdir logs
```

---

### Step 10 — Verify Ollama is Running

Open a **separate** Command Prompt and run:

```cmd
ollama serve
```

Leave this window open. Ollama must be running for Daddy to work.

---

### Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| RAM | 8 GB | 16 GB |
| Storage | 10 GB free | 20 GB+ |
| Microphone | Any built-in mic | USB noise-cancelling mic |
| GPU | Not required | Optional (speeds up Whisper) |
| OS | Windows 10 | Windows 11 |

---

## Running the Project

### Option 1 — Normal Launch (Terminal)

Asks you to choose input mode at startup:

```cmd
python main.py
```

### Option 2 — Launch with System Tray (Recommended)

Launches Daddy in the background with a tray icon. Auto-starts in wake word mode:

```cmd
python launcher.py
```

### Option 3 — Launch Without Tray

Full features, no tray icon:

```cmd
python launcher.py --notray
```

### Choosing Input Mode

When running `python main.py` you will be asked:

```
Choose input mode:
  1 → Text mode      (type your messages)
  2 → Voice mode     (press Enter then speak)
  3 → Wake word mode (say 'Hey Daddy' to activate)

Enter 1, 2 or 3:
```

When launched via `launcher.py`, Daddy automatically starts in **wake word mode**.

---

## Command Guide

This section covers every capability Daddy has, with exact prompts and examples for each function.

---

### Special Commands

These work in all three modes — just type or say them exactly.

| Command | What it does |
|---|---|
| `quit` / `exit` / `bye` | Save memory and shut down Daddy |
| `clear` | Clear in-session conversation memory |
| `switch` | Toggle between text / wake word modes |
| `memory status` | Show count of conversations, preferences, tasks |
| `my tasks` / `show tasks` / `pending tasks` | List all pending tasks |
| `complete task <keyword>` | Mark a task as done |
| `clear conversations` | Wipe conversation history, keep preferences and tasks |
| `clear all memory` | Wipe everything including preferences and tasks |
| `threshold <number>` | Adjust wake word mic sensitivity |
| `voices` | List all available TTS voices on your system |

**Examples:**
```
complete task assignment
threshold 1500
threshold 800
```

---

### File System Commands

Daddy understands natural language for all file and folder operations. The supported location names are: `Desktop`, `Documents`, `Downloads`, `Pictures`, `Music`, `Videos`. Subpaths like `Downloads/Video` or `Desktop/Projects` also work.

---

#### Create a Folder

```
Create a folder called Projects on Desktop
Create a folder called Python inside Projects on Desktop
Make a new folder called Archive in Documents
```

---

#### Delete a Single File or Folder

```
Delete the folder called Projects from Desktop
Delete the file called notes.txt from Desktop
Remove the folder OldFiles from Downloads
```

---

#### Rename a File or Folder

```
Rename MyFolder to Project_1 on Desktop
Rename report.txt to final_report.txt in Documents
Rename the folder called Old to Archive in Downloads
```

For folders inside subfolders:
```
Rename MyFolder to Project_1 inside the Video folder in Downloads
```

---

#### Move a File or Folder

```
Move report.pdf from Desktop to Documents
Move the folder called Projects from Desktop to Documents
Move notes.txt from Downloads to Desktop
```

---

#### List Folder Contents

```
List the contents of Desktop
Show me what is inside Downloads
What files are in Documents
```

---

#### Find Files

```
Find all PDF files in Downloads
Find files starting with report in Documents
Find files ending with final in Desktop
Find files containing the word invoice in Downloads
Find all Python files in Documents
```

---

#### Create a Text File with Content

```
Create a text file called todo.txt on Desktop with content Buy groceries
Create a file called notes.txt in Documents with content Meeting at 3pm
```

---

#### Read a Text File

```
Read the file notes.txt from Desktop
Show me the contents of todo.txt on Desktop
```

---

#### Get File or Folder Info

```
Give me info about report.docx in Documents
What is the size of notes.txt on Desktop
Show info about the Downloads folder
```

---

#### Create Multiple Files at Once

Pattern-based:
```
Create files file_1.txt to file_5.txt on Desktop
Create 4 text files named report_1 to report_4 on Desktop
Create files log_n.txt where n is 1 to 3 in Documents
```

Explicit names:
```
Create two files named sample.txt and portfolio.txt on Desktop
Create three files called intro.txt body.txt and conclusion.txt on Desktop
```

---

#### Delete Multiple Files at Once

Pattern-based:
```
Delete files file_1.txt to file_3.txt from Desktop
```

Explicit names:
```
Delete sample.txt and portfolio.txt from Desktop
Remove intro.txt body.txt and conclusion.txt from Desktop
```

---

#### Delete Files by Pattern (Wildcard)

```
Delete every file starting with Moviesda in Video folder inside Downloads
Delete all PDF files in Downloads
Delete files containing the word temp in Documents
Delete all text files from Desktop
```

---

#### Move Files by Pattern

```
Move all PDF files from Downloads to Documents
Move every file starting with report from Downloads to Desktop
Move all text files from Desktop to Documents
```

---

### Word Document Commands

Daddy can create, read, and edit Microsoft Word `.docx` files without opening Word. Always specify the file name with `.docx` and include the location.

---

#### Create a New Word Document

```
Create a new Word document called report.docx on Desktop
Create a Word document called essay.docx in Documents with title My Essay
Create a new Word file called project.docx on Desktop
```

---

#### Read a Document

```
Read the contents of report.docx on Desktop
Show me what is inside essay.docx in Documents
```

---

#### Summarize a Document

```
Summarize report.docx on Desktop
Give me a summary of essay.docx in Documents
What is report.docx about
```

---

#### Add a Heading

```
Add a heading called Introduction to report.docx on Desktop
Add a level 2 heading called Background to essay.docx in Documents
Add a heading called Conclusion with level 1 to project.docx on Desktop
```

---

#### Add a Paragraph

```
Add a paragraph saying This is my personal AI assistant project to report.docx on Desktop
Add a paragraph This project was built in Python to essay.docx in Documents
```

---

#### Replace Text

```
Replace the word old with new in report.docx on Desktop
Replace assistant with system in project.docx on Desktop
Find and replace introduction with overview in essay.docx in Documents
```

---

#### Add a Table

```
Add a table with headers Name Age Score to report.docx on Desktop with rows Arun 22 95 and Raj 25 88
Add a table with columns Month Revenue to sales.docx on Desktop
```

---

#### Count Words

```
Count the words in report.docx on Desktop
How many words are in essay.docx in Documents
Word count of project.docx on Desktop
```

---

#### Delete a Paragraph

```
Delete paragraphs containing introduction from report.docx on Desktop
Remove paragraphs with the word draft in essay.docx in Documents
```

---

#### Set Font

```
Set the font to Arial size 12 in report.docx on Desktop
Change font to Times New Roman size 14 in essay.docx in Documents
```

---

### Knowledge Base Commands

Daddy can learn from your personal documents and answer questions from them. Before using this, place your files (`.txt`, `.pdf`, `.docx`) inside the `knowledge/raw_docs/` folder.

---

#### Index Your Documents

Run this first after adding new files to `knowledge/raw_docs/`:

```
Index my documents
Index all my files
```

This reads every supported file, splits it into chunks, embeds each chunk, and stores them in ChromaDB.

---

#### Ask Questions from Your Documents

```
What does my knowledge base say about Python
According to my documents what is machine learning
What did I write about neural networks
Find information about deep learning in my files
Tell me about RAG from my documents
What do my notes say about the project deadline
```

---

#### Summarize a Specific Document

```
Summarize my notes file test_notes.txt
Summarize the document called project_summary.pdf
Give me a summary of my file called meeting_notes.txt
```

---

#### Search Across All Documents

```
Search my notes for machine learning
Search my documents for anything about Python
Search my files for the word deadline
```

---

#### Check Knowledge Base Status

```
How many documents are indexed
Knowledge base status
How many chunks are stored
```

---

#### Clear the Knowledge Base

```
Clear my knowledge base
Delete all indexed documents
Wipe the knowledge base
```

---

### Memory Commands

---

#### Save a Preference

Daddy automatically detects these from your natural speech:

```
Call me Arun              → saves your name
Keep it short             → Daddy gives concise replies
Be more detailed          → Daddy gives detailed replies
Speak slower              → saves speech speed preference
Speak faster              → saves speech speed preference
Reply in Malayalam        → saves language preference
Reply in English          → saves language preference
```

---

#### Add a Task

Daddy automatically detects tasks from these patterns:

```
Remind me to submit the assignment tomorrow
Remember to call the doctor on Monday
Don't forget to send the email tonight
I need to buy groceries
Make sure to back up my files
Track this: finish the project report
Add to my tasks: review the code
Note this: meeting at 3pm on Friday
```

---

#### View Pending Tasks

```
My tasks
Show tasks
Pending tasks
List my tasks
```

---

#### Complete a Task

```
Complete task assignment
Complete task doctor
Complete task groceries
```

Daddy matches by keyword — so `complete task doctor` marks the task containing "doctor" as done.

---

#### Memory Status

```
Memory status
```

Shows:
- Number of recent conversations stored
- Whether an old summary exists
- Number of saved preferences
- Total tasks and how many are pending

---

#### Clear Memory

```
clear                    → clears only in-session memory (current conversation)
clear conversations      → clears all saved conversation history, keeps preferences and tasks
clear all memory         → wipes everything including preferences and tasks
```

---

### Wake Word & Voice Commands

---

#### Wake Word Mode

Say the wake word clearly and wait for Daddy to respond:

```
Hey Daddy
```

Daddy will respond: *"Daddy is here. Tell me?"*

Then speak your command within 10 seconds.

If Daddy misses your command 3 times in a row, it says *"Daddy is going to take a nap"* and goes back to listening for the wake word.

---

#### Adjusting Wake Word Sensitivity

If Daddy wakes up on background noise:
```
threshold 1500
threshold 2000
```

If Daddy isn't responding to your voice:
```
threshold 500
threshold 300
```

Default is `500`. For quiet rooms `1500` is recommended.

---

#### Voice Mode

Press `Enter` to start recording, speak your command, and Daddy will transcribe and process it.

Speak clearly and close to the microphone. Default recording time is 10 seconds.

---

#### Switching Modes

```
switch
```

Cycles through: text → wake word → text

---

## System Tray Guide

When launched via `python launcher.py`, a custom icon appears in your Windows system tray (bottom-right taskbar area).

**Right-click the icon for these options:**

| Menu Item | Action |
|---|---|
| Open Daddy | Launch a new Daddy terminal window |
| Restart Daddy | Restart Daddy's background thread |
| Enable Auto-Start | Add Daddy to Windows startup (boots with PC) |
| Disable Auto-Start | Remove Daddy from Windows startup |
| Startup Status | Check if auto-start is currently enabled |
| Quit | Save memory and shut everything down |

### Enable Auto-Start

1. Launch Daddy: `python launcher.py`
2. Right-click the tray icon
3. Click **Enable Auto-Start**

Daddy will now launch automatically every time Windows boots, directly in wake word mode.

### Disable Auto-Start

1. Right-click the tray icon
2. Click **Disable Auto-Start**

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `ollama: command not found` | Ollama not in PATH | Restart Command Prompt after installing Ollama |
| `Connection refused` error | Ollama not running | Run `ollama serve` in a separate terminal |
| `Module not found` error | venv not activated | Run `venv\Scripts\activate` first |
| Llama is very slow on first message | Model loading into RAM | Normal — subsequent messages are faster |
| `python: command not found` | Python not in PATH | Reinstall Python and check "Add to PATH" |
| Nothing detected in voice mode | Mic too quiet or wrong device | Speak louder, check mic is not muted |
| Wake word triggers on background noise | Threshold too low | Run `threshold 1500` or `threshold 2000` |
| Wake word never triggers | Threshold too high | Run `threshold 500` or `threshold 300` |
| `Package not found` in RAG | Wrong file reader called | Make sure files in `raw_docs/` have correct extensions |
| Tray icon not appearing | pystray or Pillow not installed | Run `pip install pystray pillow` |
| Daddy not starting on boot | Auto-start not enabled | Right-click tray → Enable Auto-Start |
| TTS stops working after a few responses | pyttsx3 engine state issue | Already fixed — engine reinitialised every call |
| JSON decode error in agents | Llama returned non-JSON | Run the command again — rare with temperature=0 |
| ChromaDB errors on first run | Folder missing | Run `mkdir knowledge\vector_store` |

---

## Privacy

- All processing happens locally on your machine
- No data is sent to any external server
- No API keys required
- ChromaDB telemetry is explicitly disabled
- Whisper, Llama, and sentence-transformers all run fully offline
- Your documents, memory, and conversations never leave your laptop

---

## License

This project is open source and free to use for personal and educational purposes.

---

## Acknowledgements

- [Ollama](https://ollama.ai) — Local LLM runner
- [Meta Llama 3.2](https://llama.meta.com) — The AI brain
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) — Speech recognition
- [ChromaDB](https://www.trychroma.com) — Local vector database
- [sentence-transformers](https://www.sbert.net) — Text embeddings
- [LangChain](https://www.langchain.com) — LLM orchestration
- [pystray](https://github.com/moses-palmer/pystray) — System tray support

---

*Built with Python — 100% local, 100% private, 100% yours.*
