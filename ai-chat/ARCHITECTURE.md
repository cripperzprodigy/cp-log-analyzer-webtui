# System Architecture & Flow

This document outlines the high-level architecture of the Log Searcher & AI Analyzer.

## Core Design Philosophy
The system is built to be **lean, portable, and entirely Python-based**. There is intentionally zero Node.js, NPM, or complex build pipelines required to run this. The backend and frontends share a single unified Python core.

## 1. The Core Engines (`src/`)

### A. Virtual File System (`vfs.py`)
Because we need to support querying remote logs (SFTP, Windows SMB shares) without requiring admin privileges to mount drives at the OS level, we use a Virtual File System abstraction.
*   **URI Schema:** Remote connections are registered with an ID and accessed via `vfs://<connection_id>/path`.
*   **Protocol Support:** It supports `local` (using `aiofiles`), `sftp` (using `paramiko`), and `smb` (using `smbprotocol`/`smbclient`).
*   **Purpose:** Exposes asynchronous `list_dir()` and `read_lines()` methods that the rest of the application consumes transparently, completely agnostic to where the file physically lives.

### B. Log Searcher (`log_searcher.py`)
Responsible for reading massive files chunk-by-chunk to prevent memory exhaustion.
*   It delegates all reads to the `vfs.py`.
*   **Smart Search:** Converts simple user inputs into case-insensitive, word-boundary regex patterns, while allowing `*` as a wildcard.
*   **Exact / Regex:** Also supports exact keyword mapping and pure Regular Expressions.

### C. AI Agent (`ai_agent.py`)
Powered by `litellm` to provide universal compatibility with local models (Ollama, LM-Studio) and cloud models (OpenAI, Anthropic, OpenRouter).
*   **Tools (Function Calling):** The agent is equipped with definitions for `list_files`, `read_file`, and `search_logs`.
*   **Autonomy:** When a user asks "Why did the app crash in the logs folder?", the AI autonomously iterates, exploring directories and searching files using its toolset before generating a final markdown answer.

## 2. The Interfaces

The application intentionally supports two first-class user interfaces.

### A. The Terminal UI (TUI) -> `main.py`
Built using `Textual`, it provides a modern CLI experience with mouse support, scrollbars, and sidebar panels.
*   Runs directly in the terminal via `python src/main.py`.
*   Supports mapping network drives via a native Modal popup.

### B. The Web UI -> `web_ui.py` & `templates/index.html`
A lightweight, modern web frontend built entirely with FastAPI and vanilla HTML/JS/CSS.
*   Runs via `python src/main.py --web` (which spins up `uvicorn`).
*   Uses `marked.js` for markdown rendering of AI responses.
*   Exposes endpoints (`/api/chat`, `/api/search`, `/api/directory`, `/api/vfs/*`) that wrap the core engines.

## 3. Configuration & Startup
*   **`config.yaml`**: The single source of truth for the system. Defines the AI Provider, model, API keys, Web UI port, and search chunk sizes.
*   **`start.sh` & `start.bat`**: Portable bootstrap scripts. They automatically check for Python, create a `venv`, install `requirements.txt`, and launch the app (TUI by default, or Web if `--web` is passed).