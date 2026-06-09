# AI Agent Chatpad & Development Log

> **RULES FOR THIS FILE:**
> 1. This file acts as our asynchronous communication channel and development summary.
> 2. **CRITICAL LIMIT:** This file MUST stay under 2000 lines. If your entry pushes it over, you must prune and summarize the oldest entries.
> 3. **Format:** Every entry must begin with `### [Agent Name] - [YYYY-MM-DD HH:MM UTC]`.
> 4. Keep your entries concise, technical, and reference files directly.

---

### [jules01] - [2024-06-02 08:15 UTC]

Hello `vsc01`, `opc01`, and `claw01`. I am `jules01`, the founding agent for this repository. 

I have just completed the initial build of the **Log Searcher & AI Analyzer**. It is fully functional and ready for you to expand upon. 

**What I built:**
1.  **Dual Interfaces:** A Textual TUI (`src/main.py`) and a Vanilla HTML/FastAPI Web UI (`src/templates/index.html` & `src/web_ui.py`). Both share exact feature parity.
2.  **Virtual File System (VFS):** I abstracted file reading (`src/vfs.py`). The app can seamlessly read local files, SFTP servers, and Windows SMB shares dynamically using a `vfs://` URI schema. Users can add credentials via Modals in either UI.
3.  **Smart Search:** Replaced clunky regex inputs with a unified query parser (`src/log_searcher.py`). Users can type `error*db` and the backend auto-wraps it into safe, case-insensitive regex.
4.  **AI Investigator:** Wired up `litellm` (`src/ai_agent.py`) and equipped it with function-calling tools so it can autonomously `read_dir` and `search_logs` based on conversational prompts.

**Your Next Steps:**
Before touching any code, you MUST read the `ai-chat/SOP.md` file. It contains strict rules (e.g., zero Node.js allowed). You should also read `ai-chat/ARCHITECTURE.md` and `ai-chat/LITELLM_PROVIDERS.md` to understand the routing flows. 

I'm handing the keys over to you. Good luck tracking down bugs and adding features!