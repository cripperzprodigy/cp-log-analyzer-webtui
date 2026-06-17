# Log Searcher & AI Analyzer

A powerful, cross-platform log analysis tool built entirely in Python. It features both a modern Terminal UI (TUI) and a sleek Web UI, allowing you to rapidly search massive log files and employ AI to investigate issues autonomously.

## Key Features
*   **Dual Interfaces:** Use the lightning-fast Terminal UI (`Textual`) or the polished Web UI (`FastAPI` + Vanilla JS).
*   **AI Investigator Engine:** Powered by `litellm`. The AI can autonomously browse your directories, read file chunks, and search through logs based on your conversational prompts to find root causes of errors.
*   **Enterprise-Grade Backend:** Features a robust Python backend including Pydantic configuration validation, exponential API retries (`tenacity`), LRU Caching for LLM responses, and structured logging (`structlog`) with rotation.
*   **Optional Data Privacy:** Integrated PII Masker can be toggled on in `config.yaml` to scrub emails, phone numbers, and credit cards from logs before they hit the UI or external LLMs. (Defaults to off for full sysadmin visibility).
*   **Remote Network Drives:** Map remote SFTP servers or Windows SMB shares directly into the app (via a Virtual File System) without needing OS-level Admin privileges.
*   **Smart Search:** Search gigabytes of logs asynchronously. The built-in "Smart Search" automatically handles case-insensitivity and wildcards (`*`), while pure Keyword and Raw Regex options remain available.
*   **Highly Portable:** Zero Node.js or NPM required. Setup is completely automated via bootstrap scripts.

---

## 🚀 Getting Started

### 1. Prerequisites (All Platforms)
1. **Python 3:** Ensure you have Python 3.10 or newer installed.
   * *Windows:* Download from python.org (check "Add Python to PATH" during installation).
   * *Linux/macOS:* Usually pre-installed. If not, install via your package manager (e.g., `sudo apt install python3 python3-venv`).
2. **AI Provider (Optional but recommended):** 
   * Open `config.yaml` in a text editor. By default, no AI is selected.
   * Uncomment the configuration block for your chosen AI provider (e.g., Ollama, LM-Studio, OpenAI, Anthropic, OpenRouter) and add your API key if required.

### 2. Running on Linux / macOS
We provide a portable bootstrap script that handles the virtual environment and dependencies for you.

1. Open your terminal and navigate to this project directory.
2. Make the script executable (you only need to do this once):
   ```bash
   chmod +x start.sh
   ```
3. **Launch the Terminal UI (TUI):**
   ```bash
   ./start.sh
   ```
4. **Launch the Web UI:**
   ```bash
   ./start.sh --web
   ```
   *The Web UI will start. Open your browser and navigate to `http://127.0.0.1:8000` (or the port defined in `config.yaml`).*

### 3. Running on Windows
We provide a batch script that automatically sets up the Python environment.

1. Open Command Prompt (`cmd`) or PowerShell and navigate to this project directory.
2. **Launch the Terminal UI (TUI):**
   ```cmd
   start.bat
   ```
3. **Launch the Web UI:**
   ```cmd
   start.bat --web
   ```
   *The script will launch the server. Open your web browser and navigate to `http://127.0.0.1:8000`.*

---

## 🛠️ Modifying the AI Behavior
You can edit the `system_prompt.txt` file to change how the AI acts. By default, it is instructed to act as a high-end technical investigator that proactively uses its tools to solve user queries.

## 🤖 For AI Agents
If you are an AI attempting to modify this codebase, please read the documentation in the `/ai-chat/` directory before making any changes.