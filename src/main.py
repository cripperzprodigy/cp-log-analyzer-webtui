import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, Input, Button, Static, TabbedContent, TabPane, Markdown, DirectoryTree, Label, Select
from textual.binding import Binding
from textual.screen import ModalScreen

from src.ai_agent import AIAgent
from src.log_searcher import LogSearcher
from src.vfs import vfs

class AIChatTab(Container):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Container(Static("AI Investigator initialized. How can I help you?", id="chat_history"), id="chat_container")
            with Horizontal(id="input_container"):
                yield Input(placeholder="Ask the AI to investigate a folder or log file...", id="chat_input")
                yield Button("Send", id="send_button", variant="primary")

class AddNetworkDriveScreen(ModalScreen):
    """A modal screen to add a network drive (SFTP or SMB)."""
    
    CSS = """
    AddNetworkDriveScreen {
        align: center middle;
    }
    
    #modal_container {
        width: 60;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: thick $primary;
    }
    
    #modal_title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .form_row {
        height: 3;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="modal_container"):
            yield Label("Add Network Drive", id="modal_title")
            yield Input(placeholder="Connection Name (ID) e.g. prod_logs", id="nd_id")
            yield Select([("SMB (Windows Share)", "smb"), ("SFTP (SSH)", "sftp")], prompt="Protocol", id="nd_proto", value="smb")
            yield Input(placeholder="Host / IP", id="nd_host")
            yield Input(placeholder="Share Name (For SMB only)", id="nd_share")
            yield Input(placeholder="Port (Optional, usually 22 for SFTP)", id="nd_port")
            yield Input(placeholder="Username (Optional for Guest SMB)", id="nd_user")
            yield Input(placeholder="Password (Optional)", id="nd_pass", password=True)
            with Horizontal(classes="form_row"):
                yield Button("Cancel", id="btn_cancel", variant="error")
                yield Button("Add Drive", id="btn_add", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.dismiss(None)
        elif event.button.id == "btn_add":
            conn_id = self.query_one("#nd_id", Input).value.strip()
            proto = self.query_one("#nd_proto", Select).value
            host = self.query_one("#nd_host", Input).value.strip()
            share = self.query_one("#nd_share", Input).value.strip()
            port_str = self.query_one("#nd_port", Input).value.strip()
            user = self.query_one("#nd_user", Input).value.strip()
            password = self.query_one("#nd_pass", Input).value
            
            if not conn_id or not host:
                return # In a full app, show a toast/error here
            
            if proto == "smb" and not share:
                return 

            config = {
                "protocol": proto,
                "host": host,
                "username": user if user else None,
                "password": password if password else None,
                "share_name": share if proto == "smb" else None,
                "port": int(port_str) if port_str and proto == "sftp" else None
            }
            
            vfs.add_connection(conn_id, config)
            self.dismiss(conn_id)


class CoreSearchTab(Container):
    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="search_controls"):
                yield Input(placeholder="Filepath to search...", id="filepath_input")
                yield Select(
                    [("Smart Search", "smart"), ("Exact Keyword", "keyword"), ("Raw Regex", "regex")],
                    prompt="Search Type",
                    id="search_type_select",
                    value="smart"
                )
                yield Input(placeholder="Search Query...", id="query_input")
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
        Binding("n", "add_network_drive", "Add Network Drive"),
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
                yield Label("Network Drives", classes="panel_title", style="margin-top: 1;")
                yield Static("No drives mapped. Press 'n' to add.", id="vfs_list_display")
                
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
        elif event.input.id in ["filepath_input", "query_input"]:
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
        query = self.query_one("#query_input", Input).value.strip()
        search_type = self.query_one("#search_type_select", Select).value
        
        results_widget = self.query_one("#search_results", Static)
        
        if not filepath:
            results_widget.update("Error: Please provide a filepath.")
            return
            
        results_widget.update("Searching...")
        
        try:
            results = await self.log_searcher.search_file(filepath, query=query if query else None, search_type=search_type)
            
            if not results:
                results_widget.update("No matches found.")
            else:
                formatted_results = "\n".join([f"Line {r.get('line_num', '?')}: {r.get('content', r.get('error', r.get('info', '')))}" for r in results])
                results_widget.update(formatted_results)
        except Exception as e:
             results_widget.update(f"Error during search: {str(e)}")

    async def action_add_network_drive(self) -> None:
        def check_result(conn_id: str | None) -> None:
            if conn_id:
                # Update the sidebar VFS list display
                vfs_display = self.query_one("#vfs_list_display", Static)
                connections = list(vfs.connections.keys())
                if connections:
                    formatted_list = "\n".join([f"🌐 vfs://{c}" for c in connections])
                    vfs_display.update(formatted_list)
                
                # Let user know in chat
                self.chat_history_text += f"\n\n[bold green]System:[/bold green] Added network drive: vfs://{conn_id}\n"
                chat_history_widget = self.query_one("#chat_history", Static)
                chat_history_widget.update(self.chat_history_text)
                chat_history_widget.scroll_end()

        self.push_screen(AddNetworkDriveScreen(), check_result)


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
