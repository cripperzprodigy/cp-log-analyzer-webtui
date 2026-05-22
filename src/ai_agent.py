import yaml
import litellm
import json
from src.log_searcher import LogSearcher

class AIAgent:
    def __init__(self, config_path="config.yaml", system_prompt_path="system_prompt.txt"):
        self.config = self._load_config(config_path)
        self.system_prompt = self._load_system_prompt(system_prompt_path)
        self.log_searcher = LogSearcher(chunk_size=self.config.get('search', {}).get('chunk_size_bytes', 1048576))
        
        # Configure litellm based on our settings
        self.model = self.config['ai']['model']
        self.api_base = self.config['ai'].get('api_base')
        self.api_key = self.config['ai'].get('api_key')
        self.temperature = self.config['ai'].get('temperature', 0.2)
        
        # Define the tools available to the AI
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "Lists all files in a given directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "The directory path to list files from."
                            }
                        },
                        "required": ["directory"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Reads a chunk of lines from a file. Useful to read log files or source code.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "The path to the file."
                            },
                            "start_line": {
                                "type": "integer",
                                "description": "The line number to start reading from. Default is 1."
                            },
                            "max_lines": {
                                "type": "integer",
                                "description": "Maximum number of lines to read. Default is 100."
                            }
                        },
                        "required": ["filepath"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_logs",
                    "description": "Searches a specific file for a keyword or regex pattern.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "The file to search."
                            },
                            "keyword": {
                                "type": "string",
                                "description": "The exact keyword to search for (optional)."
                            },
                            "regex": {
                                "type": "string",
                                "description": "The regex pattern to search for (optional)."
                            }
                        },
                        "required": ["filepath"]
                    }
                }
            }
        ]

    def _load_config(self, path):
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {"ai": {"model": "ollama/llama3"}, "search": {}}

    def _load_system_prompt(self, path):
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            return "You are an AI assistant."

    async def _execute_tool(self, tool_call):
        """Executes a tool call requested by the AI."""
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        try:
            if name == "list_files":
                result = await self.log_searcher.list_files_in_dir(args.get("directory"))
                return json.dumps(result)
            elif name == "read_file":
                result = await self.log_searcher.read_file_chunk(
                    args.get("filepath"), 
                    start_line=args.get("start_line", 1), 
                    max_lines=args.get("max_lines", 100)
                )
                return json.dumps(result)
            elif name == "search_logs":
                result = await self.log_searcher.search_file(
                    args.get("filepath"),
                    keyword=args.get("keyword"),
                    regex=args.get("regex")
                )
                return json.dumps(result)
            else:
                return f"Error: Unknown tool {name}"
        except Exception as e:
            return f"Error executing tool {name}: {str(e)}"

    async def chat(self, messages):
        """
        Sends messages to the AI and handles tool calls in a loop until a final answer is produced.
        """
        if not messages:
            messages = [{"role": "system", "content": self.system_prompt}]
            
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "tools": self.tools,
            "tool_choice": "auto"
        }
        
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.api_key:
            kwargs["api_key"] = self.api_key

        while True:
            try:
                # Need to use litellm.acompletion for async
                response = await litellm.acompletion(**kwargs)
                response_message = response.choices[0].message
                
                messages.append(response_message)
                
                if response_message.tool_calls:
                    for tool_call in response_message.tool_calls:
                        tool_result = await self._execute_tool(tool_call)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": tool_result
                        })
                else:
                    return response_message.content, messages
            except Exception as e:
                return f"AI Error: {str(e)}", messages
