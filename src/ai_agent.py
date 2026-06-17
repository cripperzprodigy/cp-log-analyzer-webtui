import hashlib
import json
from typing import Any, Dict, List, Tuple

import litellm
from cachetools import TTLCache
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

from src.core.config import config as app_config
from src.core.exceptions import AIProviderError
from src.core.logger import logger
from src.core.security import PIIMasker
from src.log_searcher import LogSearcher


class AIAgent:
    """
    The AI Agent orchestrates communication with LiteLLM and executes tool calls
    against the LogSearcher engine.
    """

    def __init__(
        self, log_searcher: LogSearcher, system_prompt_path: str = "system_prompt.txt"
    ):
        self.log_searcher = log_searcher
        self.system_prompt = self._load_system_prompt(system_prompt_path)

        # Inject configurations from validated Pydantic model
        self.model = app_config.ai.model
        self.api_base = app_config.ai.api_base
        self.api_key = app_config.ai.api_key
        self.temperature = app_config.ai.temperature

        # LRU Cache for AI responses to save tokens and time (1 hour TTL)
        self.cache = TTLCache(maxsize=1000, ttl=3600)

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
                                "description": "The directory path to list files from.",
                            }
                        },
                        "required": ["directory"],
                    },
                },
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
                                "description": "The path to the file.",
                            },
                            "start_line": {
                                "type": "integer",
                                "description": "The line number to start reading from. Default is 1.",
                            },
                            "max_lines": {
                                "type": "integer",
                                "description": "Maximum number of lines to read. Default is 100.",
                            },
                        },
                        "required": ["filepath"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_logs",
                    "description": "Searches a specific file using a search query.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "The file to search.",
                            },
                            "query": {
                                "type": "string",
                                "description": "The search query.",
                            },
                            "search_type": {
                                "type": "string",
                                "description": "One of: 'smart' (default, case-insensitive, allows *), 'keyword' (exact match), 'regex' (raw regex).",
                            },
                        },
                        "required": ["filepath", "query"],
                    },
                },
            },
        ]

    def _load_system_prompt(self, path: str) -> str:
        """Loads the base system prompt from disk."""
        try:
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            logger.warning("system_prompt_load_failed", error=str(e))
            return "You are an AI assistant."

    async def _execute_tool(self, tool_call) -> str:
        """Executes a tool call requested by the AI."""
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        try:
            if name == "list_files":
                result = await self.log_searcher.list_files_in_dir(
                    args.get("directory")
                )
                return json.dumps(result)
            elif name == "read_file":
                result = await self.log_searcher.read_file_chunk(
                    args.get("filepath"),
                    start_line=args.get("start_line", 1),
                    max_lines=args.get("max_lines", 100),
                )
                return json.dumps(result)
            elif name == "search_logs":
                result = await self.log_searcher.search_file(
                    args.get("filepath"),
                    query=args.get("query"),
                    search_type=args.get("search_type", "smart"),
                )
                return json.dumps(result)
            else:
                logger.warning("unknown_tool_called", tool_name=name)
                return f"Error: Unknown tool {name}"
        except Exception as e:
            logger.error("tool_execution_failed", tool_name=name, error=str(e))
            return f"Error executing tool {name}: {str(e)}"

    def _cache_key(self, kwargs: dict) -> str:
        """Generates a stable cache key for an LLM request."""
        # We only cache the messages to avoid hashing function pointers
        msgs = json.dumps(kwargs.get("messages", []))
        return hashlib.sha256(msgs.encode()).hexdigest()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def _call_litellm(self, kwargs: dict) -> Any:
        """Wraps litellm.acompletion with exponential backoff retries and LRU caching."""
        key = self._cache_key(kwargs)
        if key in self.cache:
            logger.debug("litellm_cache_hit", key=key)
            return self.cache[key]

        logger.debug("calling_litellm", model=kwargs.get("model"))
        response = await litellm.acompletion(**kwargs)
        self.cache[key] = response
        return response

    async def chat(
        self, messages: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Sends messages to the AI and handles tool calls in a loop until a final answer is produced.

        Args:
            messages (List[Dict]): The conversational history.

        Returns:
            Tuple[str, List[Dict]]: The final AI response and the updated conversation history.
        """
        if not self.model:
            logger.info("chat_aborted_no_model")
            return (
                "⚠️ **Configuration Required**\n\nNo AI model is currently configured. Please open `config.yaml` and uncomment or define your preferred AI provider (e.g., Ollama, OpenAI, Anthropic, OpenRouter) to enable the AI Investigator.",
                messages,
            )

        if not messages:
            messages = [{"role": "system", "content": self.system_prompt}]

        # Sanitize latest user message for PII
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] = PIIMasker.mask_pii(messages[-1]["content"])

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "tools": self.tools,
            "tool_choice": "auto",
        }

        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.api_key:
            kwargs["api_key"] = self.api_key

        while True:
            try:
                response = await self._call_litellm(kwargs)
                response_message = response.choices[0].message

                messages.append(response_message)

                if response_message.tool_calls:
                    for tool_call in response_message.tool_calls:
                        tool_result = await self._execute_tool(tool_call)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": tool_result,
                            }
                        )
                else:
                    return response_message.content, messages
            except Exception as e:
                logger.error("ai_chat_failed", error=str(e))
                return f"AI Error: {str(e)}", messages
