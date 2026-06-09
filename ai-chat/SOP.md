# Standard Operating Procedures & AI Rules

**Author:** jules01
**Target Audience:** vsc01, opc01, claw01

Greetings `vsc01`, `opc01`, and `claw01`. If you are picking up this repository to fix bugs or build new features, you **MUST** adhere to the following rules and Standard Operating Procedures. Failure to do so will compromise the lean, portable philosophy of this project.

## 1. Coding Style & Constraints
*   **Python Purism:** You must **never** introduce Node.js, NPM, React, Vue, or heavy frontend build steps. The Web UI (`src/templates/index.html`) must remain vanilla HTML/CSS/JS served directly via FastAPI/Jinja2.
*   **Portability First:** Do not rely on OS-specific shell commands where a cross-platform Python library exists. Do not assume the user has root/Administrator privileges.
*   **Interface Parity:** If you add a feature (e.g., a new search filter, a new VFS protocol), you must implement it in **both** the TUI (`src/main.py`) and the Web UI.
*   **Centralized Config:** Do not hardcode configuration values (ports, models, timeouts). Read them from `config.yaml`.
*   **File Sizes:** Keep the application lean. Avoid massive monolithic files; if a module gets too complex, abstract it cleanly (as was done with `vfs.py`).

## 2. Testing SOP
Before committing any changes, you must execute the following validation steps:
1.  **Test the Core:** If you modify `vfs` or `log_searcher`, write a quick python test script to ensure local paths still resolve correctly and chunking hasn't broken.
2.  **Test the TUI:** Ensure the TUI boots up (`python src/main.py`). Textual apps can be tricky to automate, so read your code carefully to ensure logic flow.
3.  **Test the Web UI (Playwright):** If you modify `src/templates/index.html` or `src/web_ui.py`, you **MUST** run the FastAPI server in the background and write a Playwright Python script to navigate to `http://localhost:8000`, interact with your new feature, and take a screenshot to verify it visually.

## 3. Collaboration & Communication
*   **Update the Chatpad:** Every time you enter the environment and complete a session, you MUST log your actions in `ai-chat/chatpad.md`. See that file for formatting rules.
*   **Read the Architecture:** Do not guess how the system works. Read `ARCHITECTURE.md` and `LITELLM_PROVIDERS.md`.
*   **Tool Calling:** The `AIAgent` (`src/ai_agent.py`) relies on strict JSON schemas to call our python functions. If you alter the arguments of a core backend function (like `search_file`), you MUST also update the JSON schema inside the `AIAgent.tools` array so the AI investigator doesn't break.