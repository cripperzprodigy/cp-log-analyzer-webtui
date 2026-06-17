# AI Agent Chatpad & Development Log

> **RULES FOR THIS FILE:**
> 1. **Purpose:** This file is our active conversation platform. Use it to brainstorm, debug, instruct, and share ideas directly with your fellow AI agents.
> 2. **Entry Lifecycle & Pruning:** When you finish a specific task or development phase, you **SHOULD** delete your own messy brainstorming/debugging blocks. Replace them with a clean, concise summary of what you did, the clues/ideas you discovered, and clarity for the next agent.
> 3. **Never Delete Others' Work:** You may only edit, condense, or delete your *own* entries. You are strictly forbidden from modifying or deleting the active working blocks of other AI agents.
> 4. **CRITICAL LIMIT:** This file MUST stay under 2000 lines. Keep it tidy by following Rule #2. If it is still too long, archive the oldest summaries to `chatpad_archive.md`.
> 5. **Format:** Every single entry MUST begin with a clear timestamp: `### [Agent Name] - [YYYY-MM-DD HH:MM UTC]`.

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

---

### [jules01] - [2024-06-02 08:35 UTC]

Just dropping a quick update for the team before I log off. Based on user feedback, I implemented a significant UX improvement for moving data between the Search and AI Chat tabs.

*   **Web UI:** Hovering over any search result now reveals a "Copy" clipboard icon and a "Send to AI" robot icon. Clicking the robot instantly switches the tab and populates the chat box.
*   **TUI:** I upgraded the basic `Static` search results block into an interactive Textual `DataTable`. You can use arrow keys to select a row, and pressing `Enter` will instantly send that log to the AI Chat input.
*   **Memory Reset:** I added a "Clear Chat" button to the Web UI and bound `c` in the TUI to wipe the `ai_agent` memory so users don't have to restart the app to clear context.

Keep this Data Table/Hover action paradigm in mind if you add new search output features!

---

### [jules01] - [2024-06-02 09:10 UTC]

Hello again team. I just finished a focused refactor on the AI Retrieval logic (`src/log_searcher.py`) and Prompting (`system_prompt.txt`). 

Here are the critical updates you need to be aware of:

*   **Context-Window Retrieval:** Our `search_logs` function no longer returns orphaned lines. It now natively returns the 2 lines *before* and 2 lines *after* the matched line. This gives the AI vital context (like a variable assignment right before an error trace) without needing semantic RAG.
*   **Token Protection:** I slashed the hard-limit of search matches from 1000 down to 50. Dumping 1000 lines into an LLM causes severe "Lost in the Middle" syndrome and crashes context windows. If you write new tools, do NOT allow them to dump massive payloads back to the LLM. 50 matches is plenty; if the AI needs more, it should refine its query.
*   **Strict Citations:** I updated the `system_prompt.txt` to include a `CRITICAL CITATION RULE`. The AI must now format its findings explicitly like `[vfs://logs/app.log:45]`. If you adjust prompt behavior, ensure you do not overwrite this grounding rule—we need absolute determinism in log analysis.
*   **Memory Philosophy:** We are sticking with simple Session Memory (an array wiped via the Clear Chat button). Do not attempt to overengineer long-term Vector DB memory stores for this project; log troubleshooting requires a clean slate per session.