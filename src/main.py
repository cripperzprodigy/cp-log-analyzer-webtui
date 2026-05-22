import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Button, Static, TabbedContent, TabPane, Markdown, DirectoryTree, Label
from textual.binding import Binding

from src.ai_agent import AIAgent
from src.log_searcher import LogSearcher

class AIChatTab(Container):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Container(Static("AI Investigator initialized. How can I help you?", id="chat_history"), id="chat_container")
            with Horizontal(id="input_container"):
                yield Input(placeholder="Ask the AI to investigate a folder or log file...", id="chat_input")
                yield Button("Send", id="send_button", variant="primary")

class CoreSearchTab(Container):
    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="search_controls"):
                yield Input(placeholder="Filepath to search...", id="filepath_input")
                yield Input(placeholder="Keyword...", id="keyword_input")
                yield Input(placeholder="Regex...", id="regex_input")
                yield Button("Search", id="run_search_button", variant="success")
            yield Container(Static("Search results will appear here.", id="search_results"), id="results_container")

class LogAnalyzerApp(App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    #sidebar {
        width: 30;
        dock: left;
        height: 100%;
        border-right: solid green;
    }
    
    #main_area {
        width: 1fr;
        height: 100%;
    }
    
    #chat_container {
        height: 1fr;
        border: solid blue;
        padding: 1;
        overflow-y: scroll;
    }
    
    #input_container {
        height: 3;
        dock: bottom;
    }
    
    #chat_input {
        width: 1fr;
    }
    
    #search_controls {
        height: 3;
        dock: top;
    }
    
    #results_container {
        height: 1fr;
        border: solid yellow;
        padding: 1;
        overflow-y: scroll;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_agent = AIAgent()
        self.log_searcher = LogSearcher()
        self.messages = []
        self.chat_history_text = ""

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("Directory Tree", classes="panel_title")
                yield DirectoryTree("./")
                
            with Vertical(id="main_area"):
                with TabbedContent(initial="ai_chat"):
                    with TabPane("AI Investigation", id="ai_chat"):
                        yield AIChatTab()
                    with TabPane("Core Search", id="core_search"):
                        yield CoreSearchTab()
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Log Searcher & AI Analyzer"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send_button":
            await self.handle_ai_chat()
        elif event.button.id == "run_search_button":
            await self.handle_core_search()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chat_input":
            await self.handle_ai_chat()
        elif event.input.id in ["filepath_input", "keyword_input", "regex_input"]:
            await self.handle_core_search()

    async def handle_ai_chat(self) -> None:
        chat_input = self.query_one("#chat_input", Input)
        user_text = chat_input.value.strip()
        if not user_text:
            return
            
        chat_input.value = ""
        self.chat_history_text += f"\n\n[bold green]You:[/bold green] {user_text}\n"
        
        chat_history_widget = self.query_one("#chat_history", Static)
        chat_history_widget.update(self.chat_history_text)
        chat_history_widget.scroll_end()
        
        # Add user message to state
        self.messages.append({"role": "user", "content": user_text})
        
        # Call AI Agent (this runs in the event loop, so it's non-blocking for the UI updates but we might want to run it in a worker for very long tasks. For now, await is fine).
        self.chat_history_text += "\n[bold blue]AI is investigating...[/bold blue]\n"
        chat_history_widget.update(self.chat_history_text)
        
        try:
            # Run the chat async
            ai_response, self.messages = await self.ai_agent.chat(self.messages)
            
            # Remove the 'investigating' placeholder
            self.chat_history_text = self.chat_history_text.replace("\n[bold blue]AI is investigating...[/bold blue]\n", "")
            
            self.chat_history_text += f"\n\n[bold purple]AI:[/bold purple] {ai_response}\n"
            chat_history_widget.update(self.chat_history_text)
            chat_history_widget.scroll_end()
        except Exception as e:
            self.chat_history_text += f"\n\n[bold red]Error:[/bold red] {str(e)}\n"
            chat_history_widget.update(self.chat_history_text)
            chat_history_widget.scroll_end()

    async def handle_core_search(self) -> None:
        filepath = self.query_one("#filepath_input", Input).value.strip()
        keyword = self.query_one("#keyword_input", Input).value.strip()
        regex = self.query_one("#regex_input", Input).value.strip()
        
        results_widget = self.query_one("#search_results", Static)
        
        if not filepath:
            results_widget.update("Error: Please provide a filepath.")
            return
            
        results_widget.update("Searching...")
        
        try:
            results = await self.log_searcher.search_file(filepath, keyword=keyword if keyword else None, regex=regex if regex else None)
            
            if not results:
                results_widget.update("No matches found.")
            else:
                formatted_results = "\n".join([f"Line {r.get('line_num', '?')}: {r.get('content', r.get('error', r.get('info', '')))}" for r in results])
                results_widget.update(formatted_results)
        except Exception as e:
             results_widget.update(f"Error during search: {str(e)}")


import sys
import yaml

def load_config(path="config.yaml"):
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Could not load config file: {e}")
        return {}

if __name__ == "__main__":
    if "--web" in sys.argv:
        try:
            from src.web_ui import run_web_ui
            
            config = load_config()
            web_config = config.get("web", {})
            
            # Default to config file, but allow command line override
            port = web_config.get("port", 8000)
            host = web_config.get("host", "127.0.0.1")
            
            if "--port" in sys.argv:
                try:
                    port_idx = sys.argv.index("--port")
                    port = int(sys.argv[port_idx + 1])
                except (ValueError, IndexError):
                    print(f"Invalid port specified in arguments. Defaulting to {port}.")
            
            run_web_ui(host=host, port=port)
        except ImportError as e:
            print(f"Error loading Web UI: {e}")
            print("Please ensure you have installed the required web dependencies (fastapi, uvicorn, jinja2, python-multipart).")
    else:
        app = LogAnalyzerApp()
        app.run()
