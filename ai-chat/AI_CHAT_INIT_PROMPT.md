# AI-CHAT Framework Initialization Prompt

**Purpose:** This file contains the "Master Prompt" used to bootstrap the `ai-chat/` collaboration framework into any brand new repository. 

**Instructions for Humans:** Copy the prompt block below and paste it into your chat with an AI Agent when starting a new project. It will automatically scaffold out the entire governance and collaboration structure so multiple AI agents can work together smoothly.

---

### Copy Below This Line 👇

```markdown
# Objective
You are the founding AI Agent of this repository. Your first task is to scaffold a multi-agent collaboration framework. 

Create a directory named `ai-chat/` in the root of this project. Inside this directory, you will generate a suite of governance and communication files. These files will establish the "AI-CHAT Protocol", ensuring that any future AI agents that work on this repository maintain strict coding standards, do not step on each other's toes, and have a clear channel of communication.

Please create the following files inside `ai-chat/` with the exact rules and placeholders described below:

### 1. `ai-chat/README.md`
This is the entry point. Write a welcome message instructing any new AI agent to read the files in this specific order before touching any code:
1. `SOP.md`
2. `AGENT_REGISTRY.md`
3. `chatpad.md`
4. `ARCHITECTURE.md`
5. `PROJECT_HISTORY.md`

### 2. `ai-chat/SOP.md`
This is the master governance document.
- **CRITICAL DIRECTIVE:** At the very top, in bold, add a warning: "🛑 NO AI AGENT IS PERMITTED TO MODIFY THIS FILE WITHOUT EXPLICIT APPROVAL FROM A HUMAN."
- Define the project's strict coding constraints (e.g., specific languages to use, frameworks to avoid, formatting rules). Leave placeholders for the human to fill in specific technology rules later.
- Define a strict Testing SOP (e.g., "You must write unit tests for every new function before committing").

### 3. `ai-chat/AGENT_REGISTRY.md`
This is the active roster.
- Create a markdown table with columns: `Agent ID`, `Date Joined`, `Role / Objective`, and `Status`.
- Add a rule stating that any new AI agent entering the workspace MUST add a row to this table registering their presence and current task so agents do not overwrite each other.
- Add yourself as the Founding Agent in the first row.

### 4. `ai-chat/chatpad.md`
This is the dynamic asynchronous communication channel.
- Add these exact rules at the top:
  1. **Purpose:** This file is an active conversation and brainstorming platform for AI agents.
  2. **Entry Lifecycle:** When you finish a task, you SHOULD condense and replace your messy brainstorming blocks with a clean summary, lessons learned, and clues for the next agent.
  3. **Never Delete Others' Work:** You may only edit or condense your *own* entries. You are strictly forbidden from modifying the active blocks of other AI agents.
  4. **CRITICAL LIMIT:** This file MUST stay under 2000 lines. If it gets too long, archive older summaries to `chatpad_archive.md`.
  5. **Format:** Every entry MUST begin with: `### [Your Agent ID] - [YYYY-MM-DD HH:MM UTC]`.
- Add your first timestamped entry summarizing that the AI-CHAT Protocol has been initialized.

### 5. `ai-chat/ARCHITECTURE.md`
- Create a skeleton document with sections for "Core Engines", "Interfaces", and "Data Flow".
- Leave placeholders instructing future agents to document the high-level system architecture here as they build the project.

### 6. `ai-chat/PROJECT_HISTORY.md`
- Create a skeleton document.
- Instruct future agents to log major design decisions, pivots, and historical context here (e.g., "Why did we choose Postgres over SQLite?").

Please execute this scaffolding immediately and confirm when the `ai-chat/` protocol is ready.
```