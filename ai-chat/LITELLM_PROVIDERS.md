# LiteLLM Provider Routing & Configuration Guide

This document is a technical reference for connecting the Log Analyzer to various AI APIs using the underlying `litellm` library. 

The `litellm` library acts as a universal translator, enabling us to write OpenAI-style code (with `messages` arrays and `tools`) while effortlessly routing the requests to over 100+ supported providers.

## Understanding the `model` parameter

When configuring `config.yaml`, the `model` string is critical. It tells `litellm` *which provider* to route the request to.

### 1. Cloud Providers

*   **OpenAI:** Models usually do not require a prefix, though `openai/` can be used to explicitly force the routing.
    *   *Examples:* `gpt-4o`, `gpt-3.5-turbo`, `openai/gpt-4o-mini`
*   **Anthropic:** Does not require a prefix for standard models.
    *   *Examples:* `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`
*   **OpenRouter:** Requires the `openrouter/` prefix to map to their unified API.
    *   *Examples:* `openrouter/anthropic/claude-3.5-sonnet`, `openrouter/meta-llama/llama-3.1-8b-instruct`

### 2. Local Providers

To point the tool at an AI model running on the user's own hardware, the configuration depends heavily on the server software they are running.

#### A. Ollama
Ollama exposes a specific API format.
*   **Format:** `ollama/<model_name>`
*   **Base URL:** Usually `http://localhost:11434`
*   **Examples:** `ollama/llama3`, `ollama/mistral`, `ollama/qwen2.5`

#### B. LM-Studio, LocalAI, vLLM (OpenAI Compatible)
Most local inferencing servers try to emulate the OpenAI API specification to maximize compatibility. To route to these servers, you must use the `openai/` prefix, telling litellm to format the payload identically to how it would for standard ChatGPT.
*   **Format:** `openai/<model_name_or_alias>`
*   **Base URL (LM-Studio):** `http://localhost:1234/v1`
*   **Base URL (vLLM):** `http://localhost:8000/v1`
*   **Base URL (LocalAI):** `http://localhost:8080/v1`
*   **Note:** Often, local OpenAI-compatible servers don't actually enforce the `<model_name>` parameter, so `openai/local-model` is usually a sufficient string, but the `openai/` prefix is mandatory.

## Advanced: Chat vs Text Completions

Modern LLMs utilize "Chat Completions", where the input is a structured JSON array of messages with specific roles (`system`, `user`, `assistant`). This project inherently uses the Chat Completion format to manage conversational history and tool-calling.

### Legacy Support
If a user tries to connect an older local model (or a specific base model) that only supports **Text Completions** (a single raw string prompt), the standard `openai/` routing will throw an error from their local server because it won't understand the JSON `messages` array.

To fix this, litellm provides a special router: `text-completion-openai/`.
When configured, litellm will intercept our Chat `messages` array, flatten it into a raw string prompt, and send it to the local server using the legacy `/v1/completions` endpoint instead of `/v1/chat/completions`.

*   **Format:** `text-completion-openai/<model_name>`
*   **Base URL:** Still the base endpoint, e.g., `http://localhost:1234/v1`