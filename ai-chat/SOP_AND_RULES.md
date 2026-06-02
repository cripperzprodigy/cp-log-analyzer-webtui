# Standard Operating Procedures & AI Rules

If you are an AI Agent operating within this repository, you **MUST** adhere to the following rules and operating procedures to ensure the codebase remains stable, lean, and aligned with its core philosophy.

## 1. Coding Style & Constraints
*   **Pure Python / Zero Node.js:** You must **never** introduce Node.js, NPM, React, Vue, or heavy frontend build steps. The Web UI must remain vanilla HTML/CSS/JS served directly via FastAPI/Jinja2.
*   **Portability First:** Do not rely on OS-specific commands where a cross-platform Python library exists. Do not assume the user has root/Administrator privileges.
*   **Parity:** If you add a feature (e.g., a new search filter, a new VFS protocol), you must make a best effort to expose that feature in **both** the TUI (`src/main.py`) and the Web UI (`src/templates/index.html`).
*   **Centralized Config:** Do not hardcode configuration values (ports, models, chunk sizes). Read them from `config.yaml`.

## 2. Testing SOP
Before submitting any changes, you must test your code:
1.  **Test the TUI:** Run the TUI (`python src/main.py`) and ensure it boots up. Note: Textual apps can sometimes be tricky to automate, so ensure the code is logically sound.
2.  **Test the Web UI:** Run the Web UI (`python src/main.py --web`) via a background process.
3.  **Playwright Verification:** If you modify `src/templates/index.html`, you **MUST** write a Playwright Python script to navigate to `http://localhost:8000`, interact with your new feature, and take a screenshot to verify it visually.

## 3. Collaboration Instructions
*   **Read the History:** Before proposing massive structural changes, read `PROJECT_HISTORY.md` to understand why things are the way they are (e.g., why we use VFS instead of OS mounting).
*   **Tool Calling:** Remember that the `ai_agent.py` exposes tools to the user's AI. If you add new capabilities to the backend, consider updating the `tools` list in `AIAgent` so the user's AI can utilize the new feature.
*   **Keep it Lean:** If you need to add a library to `requirements.txt`, ensure it is strictly necessary. We want to keep the install footprint small.