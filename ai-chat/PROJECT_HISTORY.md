# Project History & Development Thinking Process

This document logs the historical context, major decisions, and thinking process behind the initial build of this tool. Future AI agents should read this to understand *why* certain decisions were made, so they do not inadvertently revert or violate the core design philosophy.

## Initial Requirements & Vision
The user requested a portable, cross-platform log searcher and analyzer tool with an AI chat interface. The key constraints were:
1. Portable across Linux and Windows.
2. An advanced Terminal UI (TUI) as the primary interface.
3. Support for local AI (Ollama) and cloud APIs (OpenRouter, OpenAI).

## Phase 1: The Core TUI & AI Engine
*   **Thinking:** To build an advanced TUI with panels and mouse support in Python, `Textual` is the absolute best framework available.
*   **Thinking:** For universal AI provider support, `litellm` was chosen because it handles the API translation layer, meaning we only have to write the OpenAI-spec function-calling logic once, and it works for Anthropic, Ollama, and OpenRouter seamlessly.
*   **Decision:** The `config.yaml` was created. We intentionally disabled a default AI model later on to force the user to proactively choose their provider, preventing crashes or hangs if they didn't have Ollama running locally.

## Phase 2: The Web UI Pivot
*   **Requirement Change:** The user asked if a Web UI could be added locally, but it had to stay lean and Python-based.
*   **Thinking:** Typical Web UIs use React/Vue (Node.js). That would violate the "lean Python portable" constraint. 
*   **Decision:** I chose `FastAPI` + `Jinja2` with a single vanilla HTML/JS/CSS file (`src/templates/index.html`). This allows the app to serve a beautiful, modern Web UI without *any* build steps or NPM dependencies.
*   **Result:** The CLI scripts (`start.sh`, `start.bat`) were modified to accept a `--web` flag, allowing users to toggle between the TUI and Web UI easily.

## Phase 3: Remote Network Drives (SMB/SFTP)
*   **Requirement Change:** The user wanted the ability to mount shared drives for log processing.
*   **Thinking:** True OS-level mounting (`mount -t cifs`) requires root/Admin privileges, which destroys portability. 
*   **Decision:** I implemented a Virtual File System (`vfs.py`) abstraction layer. Using `paramiko` (SFTP) and `smbprotocol` (SMB), the app can stream file chunks directly over the network without mounting it to the OS. The `LogSearcher` was refactored to read exclusively from the VFS.

## Phase 4: Smart Search
*   **Requirement Change:** The user wanted a friendlier way to search, hiding raw regex complexity but keeping it powerful.
*   **Decision:** Replaced distinct `keyword` and `regex` inputs with a single `query` input and a `search_type` toggle. The "Smart Search" mode was written to automatically escape inputs, make them case-insensitive, and translate `*` into valid regex `.*` wildcards.

## Phase 5: UI/UX Quality of Life (Copy & Send-to-AI)
*   **Requirement Change:** The user noted that copying logs from the Search tab and pasting them into the AI Chat tab was tedious.
*   **Decision (Web UI):** Added hover actions (Copy to Clipboard, Send to AI) to every search result row.
*   **Decision (TUI):** Upgraded the TUI search results from a static block to an interactive `DataTable`. Selecting a row and pressing `Enter` now instantly forwards the log string to the AI tab, bypassing the lack of mouse-hover events in the terminal.
*   **Memory Management:** Added a `/api/chat/clear` endpoint and a Hotkey (`c`) to wipe AI memory instantly in both UIs.

## Phase 6: AI Retrieval & Grounding Enhancements
*   **Requirement Change:** The user requested an evaluation of the AI architecture, specifically regarding RAG (Retrieval-Augmented Generation), Memory, and general capabilities.
*   **Decision (RAG):** Rejected traditional Vector/Semantic RAG. Logs are highly structured (TraceIDs, exact timestamps); vector embeddings perform poorly on exact alphanumeric string matching. Instead, upgraded the existing keyword/regex tools to use **Context-Window Retrieval** (returning the 2 lines before and 2 lines after a match) to give the AI necessary state context without leaving the exact-match paradigm.
*   **Decision (Token Limits):** Reduced the maximum search result return limit from 1000 to 50. Large payload dumps were determined to be a risk to context windows and reasoning quality ("Lost in the Middle"). 
*   **Decision (Grounding):** Overhauled `system_prompt.txt` to include a strict citation rule. The AI is now required to append `[filepath:line_number]` to all claims, ensuring high determinism and traceability for developers using the tool.
*   **Decision (Memory):** Rejected complex vector-database long-term memory. Log troubleshooting is highly session-based. The simple Array-based session memory (wiped via the Phase 5 "Clear Chat" button) was determined to be the optimal architecture.