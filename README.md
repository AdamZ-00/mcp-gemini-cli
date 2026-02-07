# MCP Chat CLI (Gemini Edition)

This project is a command-line interface (CLI) for chatting with **Google Gemini** models. It is built upon the **Model Context Protocol (MCP)** architecture, originally designed for Anthropic's Claude, and adapted here to run with Google's GenAI SDK.

## About Model Context Protocol (MCP)

The [Model Context Protocol (MCP)](https://anthropic.skilljar.com/introduction-to-model-context-protocol) is an open standard that enables AI models to securely connect to local data and tools. Instead of building custom integrations for every data source, MCP provides a universal language for:
* **Resources**: Reading local files or data (e.g., `@document.md`).
* **Tools**: Executing functions (e.g., executing a script).
* **Prompts**: Using reusable templates.

This project implements an **MCP Client** that connects to a local MCP Server (`mcp_server.py`), but swaps the underlying intelligence engine from Claude to Gemini.

## Setup

### 1. Prerequisites
* Python 3.9+
* A Google API Key (available at [Google AI Studio](https://aistudio.google.com/))

### 2. Configuration
Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY="AIzaSy..."
CLAUDE_MODEL="gemini-2.5-flash"
```

### 3. Installation

**Using uv (Recommended):**
```bash
pip install uv
uv pip install -r requirements.txt
```

## Usage

### Basic Interaction

Simply type your message and press Enter to chat with the model.

### Document Retrieval

Use the @ symbol followed by a document ID to include document content in your query:

```
> Tell me about @deposition.md
```

### Commands

Use the / prefix to execute commands defined in the MCP server:

```
> /summarize deposition.md
```

Commands will auto-complete when you press Tab.


