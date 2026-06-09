# System Architecture & Flow

**Author:** jules01
**Target Audience:** vsc01, opc01, claw01

This document outlines the high-level architecture of the Log Searcher & AI Analyzer. If you are extending the system, you must understand these core domains.

## Core Design Philosophy
The system is built to be **lean, portable, and entirely Python-based**. There is intentionally zero Node.js, NPM, or complex build pipelines. The backend and frontends share a single unified Python core.

---

## 1. The Core Engines (`src/`)

### A. Virtual File System (`src/vfs.py`)
Because we support querying remote logs (SFTP, Windows SMB shares) without requiring admin privileges to mount drives at the OS level, we use a Virtual File System abstraction.
*   **URI Schema:** Remote connections are registered with an ID and accessed via `vfs://<connection_id>/path`.
*   **Protocol Support:** Supports `local` (using `aiofiles`), `sftp` (using `paramiko`), and `smb` (using `smbprotocol`/`smbclient`).
*   **Purpose:** Exposes asynchronous `list_dir()` and `read_lines()` methods. The rest of the application consumes this transparently, agnostic to where the file physically lives.

### B. OS Mounting (`src/os_mount.py`)
Fallback layer. Contains cross-platform subprocess commands (`net use`, `mount -t cifs`) for actual OS-level mounting if virtual streaming is insufficient.

### C. Log Searcher (`src/log_searcher.py`)
Responsible for reading massive files chunk-by-chunk to prevent memory exhaustion.
*   Delegates all file reads to the VFS.
*   **Smart Search:** Converts user input into case-insensitive, word-boundary regex patterns, while allowing `*` as a wildcard.

### D. AI Agent (`src/ai_agent.py`)
Powered by `litellm` to provide universal compatibility with local models (Ollama, LM-Studio) and cloud models (OpenAI, Anthropic, OpenRouter).
*   **Tools (Function Calling):** The agent is equipped with definitions for `list_files`, `read_file`, and `search_logs`. It can recursively call these tools to autonomously investigate directories and logs.

---

## 2. The Interfaces

The application intentionally supports two first-class user interfaces. Features added to the backend must be exposed in both interfaces.

### A. The Terminal UI (TUI) -> `src/main.py`
Built using `Textual`, providing a modern CLI experience with mouse support, scrollbars, and sidebar panels.
*   Runs directly in the terminal via `python src/main.py`.
*   Includes a native Modal popup (`AddNetworkDriveScreen`) for credential entry and VFS mapping.

### B. The Web UI -> `src/web_ui.py` & `src/templates/index.html`
A lightweight, modern web frontend built entirely with FastAPI and vanilla HTML/JS/CSS.
*   Runs via `python src/main.py --web` (which spins up `uvicorn`).
*   Uses `marked.js` for markdown rendering of AI responses.
*   Includes a typing indicator, AI/User chat bubbles, and an interactive Search Guide.

---

## 3. Configuration & Startup
*   **`config.yaml`**: The single source of truth for the system. Defines the AI Provider, API keys, Web UI port, and VFS chunk sizes. By default, NO AI is selected so the app fails gracefully if a local server isn't running.
*   **`start.sh` & `start.bat`**: Portable bootstrap scripts. They check for Python, create a `venv`, install dependencies, and launch the app.