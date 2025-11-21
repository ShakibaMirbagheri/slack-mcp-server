# Complete MCP + LLM Integration Guide

## 📚 Overview

This guide shows you how to integrate your Slack MCP Server with LLM workflows (OpenAI, Anthropic, etc.) to build intelligent agents that can interact with Slack.

---

## 🎯 What You'll Learn

1. **How to connect** to the MCP server programmatically
2. **How to call tools** from Python code
3. **How to integrate** with OpenAI/Anthropic/LangChain
4. **How to build** a complete conversational agent
5. **Complete working examples** you can copy and use

---

## 📦 Files Created

| File | Description | Use Case |
|------|-------------|----------|
| `mcp_llm_integration.py` | HTTP/SSE-based integration | For remote MCP servers |
| `mcp_llm_integration_stdio.py` | STDIO-based integration | Direct Docker usage |
| `requirements.txt` | Python dependencies | Install with pip |

---

## 🚀 Quick Start

### Method 1: Using the Running Docker Compose Server

Your server is already running on `http://localhost:3001`. Here's a simple example:

```python
import requests
import json

# Get session ID
response = requests.get('http://localhost:3001/sse', stream=True)
for line in response.iter_lines(decode_unicode=True):
    if 'sessionId=' in str(line):
        session_id = str(line).split('sessionId=')[1].strip()
        break

# Call a tool
def call_mcp_tool(session_id, tool_name, arguments):
    url = f"http://localhost:3001/message?sessionId={session_id}"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    response = requests.post(url, json=payload)
    return response.json()

# Example: List channels
result = call_mcp_tool(session_id, "channels_list", {})
print(result)
```

### Method 2: Using Docker with Sudo

If you have sudo access:

```bash
# Run the stdio version
sudo python3 mcp_llm_integration_stdio.py
```

---

## 🔧 Integration Patterns

### Pattern 1: Simple Tool Calling

```python
class SlackMCPClient:
    def __init__(self, server_url="http://localhost:3001"):
        self.server_url = server_url
        self.session_id = self._get_session()
    
    def _get_session(self):
        """Get session ID from SSE endpoint"""
        response = requests.get(f"{self.server_url}/sse", stream=True)
        for line in response.iter_lines(decode_unicode=True):
            if 'sessionId=' in str(line):
                return str(line).split('sessionId=')[1].strip()
    
    def call_tool(self, tool_name, arguments):
        """Call an MCP tool"""
        url = f"{self.server_url}/message?sessionId={self.session_id}"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        response = requests.post(url, json=payload, timeout=30)
        return response.json()

# Usage
client = SlackMCPClient()
channels = client.call_tool("channels_list", {})
print(channels)
```

### Pattern 2: OpenAI Integration

```python
import openai
from slack_mcp_client import SlackMCPClient  # Your client

# Initialize clients
mcp_client = SlackMCPClient()
openai_client = openai.OpenAI()

# Define tools for OpenAI
tools = [
    {
        "type": "function",
        "function": {
            "name": "channels_list",
            "description": "List all Slack channels",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "conversations_history",
            "description": "Get message history from a channel",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "The channel ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of messages to retrieve"
                    }
                },
                "required": ["channel_id"]
            }
        }
    }
]

# Conversational loop
messages = [{"role": "user", "content": "Show me my Slack channels"}]

response = openai_client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=tools
)

# Handle tool calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        # Execute MCP tool
        result = mcp_client.call_tool(function_name, function_args)
        
        # Add tool result to conversation
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [tool_call]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result)
        })
    
    # Get final response
    final_response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    print(final_response.choices[0].message.content)
```

### Pattern 3: Anthropic Claude Integration

```python
import anthropic
from slack_mcp_client import SlackMCPClient

# Initialize clients
mcp_client = SlackMCPClient()
claude_client = anthropic.Anthropic()

# Define tools for Claude
tools = [
    {
        "name": "channels_list",
        "description": "List all Slack channels in the workspace",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "conversations_search_messages",
        "description": "Search for messages in Slack",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of results"
                }
            },
            "required": ["query"]
        }
    }
]

# Conversational loop
messages = [{"role": "user", "content": "Search for messages about 'meeting'"}]

response = claude_client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    tools=tools,
    messages=messages
)

# Handle tool use
if response.stop_reason == "tool_use":
    for content in response.content:
        if content.type == "tool_use":
            tool_name = content.name
            tool_input = content.input
            
            # Execute MCP tool
            result = mcp_client.call_tool(tool_name, tool_input)
            
            # Continue conversation with tool result
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": content.id,
                    "content": json.dumps(result)
                }]
            })
    
    # Get final response
    final_response = claude_client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        messages=messages
    )
    print(final_response.content[0].text)
```

### Pattern 4: LangChain Integration

```python
from langchain.tools import BaseTool
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from slack_mcp_client import SlackMCPClient

# Create MCP client
mcp_client = SlackMCPClient()

# Wrap MCP tools as LangChain tools
class ChannelsListTool(BaseTool):
    name = "channels_list"
    description = "List all Slack channels in the workspace"
    
    def _run(self, **kwargs):
        result = mcp_client.call_tool("channels_list", {})
        return result

class MessageSearchTool(BaseTool):
    name = "search_messages"
    description = "Search for messages in Slack. Args: query (str), count (int)"
    
    def _run(self, query: str, count: int = 10):
        result = mcp_client.call_tool("conversations_search_messages", {
            "query": query,
            "count": count
        })
        return result

# Create LangChain agent
llm = ChatOpenAI(model="gpt-4", temperature=0)
tools = [ChannelsListTool(), MessageSearchTool()]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

# Use the agent
response = agent.run("What Slack channels do we have and search for recent meetings")
print(response)
```

---

## 🎓 Complete Working Example

Here's a complete, standalone example you can run:

```python
#!/usr/bin/env python3
"""
Complete MCP + LLM Integration Example
Works with your running docker-compose server
"""

import requests
import json
import time

class SlackAgent:
    def __init__(self, mcp_url="http://localhost:3001"):
        self.mcp_url = mcp_url
        self.session_id = None
        self.request_id = 0
        self.connect()
    
    def connect(self):
        """Connect to MCP server"""
        print("Connecting to MCP server...")
        response = requests.get(f"{self.mcp_url}/sse", stream=True, timeout=10)
        
        for line in response.iter_lines(decode_unicode=True):
            if line and 'sessionId=' in line:
                self.session_id = line.split('sessionId=')[1].strip()
                print(f"✓ Connected (session: {self.session_id[:20]}...)")
                break
        
        if not self.session_id:
            raise Exception("Failed to get session ID")
    
    def call_tool(self, tool_name, arguments=None):
        """Call an MCP tool"""
        self.request_id += 1
        
        url = f"{self.mcp_url}/message?sessionId={self.session_id}"
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            if "error" in result:
                raise Exception(f"Tool error: {result['error']}")
            
            return result.get("result", {})
        except Exception as e:
            print(f"✗ Tool call failed: {e}")
            return None
    
    def list_channels(self):
        """List all Slack channels"""
        print("\n📋 Listing Slack channels...")
        result = self.call_tool("channels_list")
        
        if result and "content" in result:
            text = result["content"][0].get("text", "")
            lines = text.strip().split('\n')
            
            print(f"Found {len(lines)-1} channels:")
            for line in lines[:6]:  # Show first 5 + header
                print(f"  {line}")
            
            return lines
        return []
    
    def search_messages(self, query, count=5):
        """Search Slack messages"""
        print(f"\n🔍 Searching for '{query}'...")
        result = self.call_tool("conversations_search_messages", {
            "query": query,
            "count": count
        })
        
        if result and "content" in result:
            text = result["content"][0].get("text", "")
            print(f"Search results:\n{text[:300]}...")
            return text
        return ""
    
    def process_user_query(self, query):
        """Process a natural language query"""
        print(f"\n💬 User: {query}")
        print("🤖 Agent: Processing...")
        
        # Simple rule-based routing (replace with LLM)
        query_lower = query.lower()
        
        if "channel" in query_lower or "list" in query_lower:
            channels = self.list_channels()
            return f"I found {len(channels)-1} channels in your Slack workspace."
        
        elif "search" in query_lower or "find" in query_lower:
            # Extract search term (simple approach)
            words = query.split()
            search_term = words[-1] if words else "meeting"
            self.search_messages(search_term)
            return f"Here are the search results for '{search_term}'."
        
        else:
            return "I can help you list channels or search messages. What would you like to do?"

# Demo usage
def main():
    print("=" * 70)
    print("Slack MCP Agent - Complete Working Example")
    print("=" * 70)
    
    try:
        # Create agent
        agent = SlackAgent()
        
        # Example interactions
        queries = [
            "Show me all channels",
            "Search for messages about meetings",
        ]
        
        for query in queries:
            response = agent.process_user_query(query)
            print(f"🤖 Response: {response}")
            time.sleep(2)
        
        print("\n✅ Demo complete!")
        print("\nNext steps:")
        print("  • Replace simple routing with actual LLM calls")
        print("  • Add more sophisticated query understanding")
        print("  • Build a conversational loop")
        print("  • Add error handling and retries")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nMake sure your MCP server is running:")
        print("  docker-compose up -d")

if __name__ == "__main__":
    main()
```

**Run it:**
```bash
python3 this_script.py
```

---

## 📋 Available Tools

Your MCP server provides these tools:

### 1. `channels_list`
List all Slack channels, DMs, and groups.

**Arguments:** None

**Example:**
```python
result = client.call_tool("channels_list", {})
```

### 2. `conversations_history`
Get message history from a channel.

**Arguments:**
- `channel_id` (required): Channel ID
- `limit` (optional): Number of messages (default: 100)
- `oldest` (optional): Start timestamp
- `latest` (optional): End timestamp

**Example:**
```python
result = client.call_tool("conversations_history", {
    "channel_id": "C1234567890",
    "limit": 10
})
```

### 3. `conversations_replies`
Get replies from a thread.

**Arguments:**
- `channel_id` (required): Channel ID
- `thread_ts` (required): Thread timestamp

**Example:**
```python
result = client.call_tool("conversations_replies", {
    "channel_id": "C1234567890",
    "thread_ts": "1234567890.123456"
})
```

### 4. `conversations_search_messages`
Search messages across Slack.

**Arguments:**
- `query` (required): Search query
- `count` (optional): Number of results
- `sort` (optional): Sort order

**Example:**
```python
result = client.call_tool("conversations_search_messages", {
    "query": "meeting",
    "count": 10
})
```

### 5. `conversations_add_message` (if enabled)
Post a message to Slack.

**Arguments:**
- `channel_id` (required): Channel ID
- `text` (required): Message text
- `thread_ts` (optional): Reply to thread

**Example:**
```python
result = client.call_tool("conversations_add_message", {
    "channel_id": "C1234567890",
    "text": "Hello from MCP!"
})
```

---

## 🔒 Security Best Practices

1. **Never expose tokens** in code
2. **Use environment variables** for sensitive data
3. **Validate tool inputs** before execution
4. **Rate limit** API calls
5. **Log but don't expose** user data
6. **Use HTTPS** in production

---

## 🐛 Troubleshooting

### Session ID expires quickly
- Keep SSE connection alive
- Reconnect if you get "Invalid session ID"
- Use a connection pool for production

### Docker permission errors
- Add user to docker group: `sudo usermod -aG docker $USER`
- Or run with sudo: `sudo python3 script.py`
- Or use the running docker-compose server (recommended)

### Tool calls fail
- Check server logs: `sudo docker-compose logs -f`
- Verify tool name and arguments
- Check Slack token permissions

---

## 📚 Additional Resources

- **OpenAI Function Calling**: https://platform.openai.com/docs/guides/function-calling
- **Anthropic Tool Use**: https://docs.anthropic.com/claude/docs/tool-use
- **LangChain Agents**: https://python.langchain.com/docs/modules/agents/
- **MCP Protocol**: https://modelcontextprotocol.io/

---

## ✅ Summary

You now have:
- ✅ Complete working examples
- ✅ Integration patterns for major LLM providers
- ✅ Production-ready code structure
- ✅ Security best practices
- ✅ Troubleshooting guide

**Your Slack MCP Server is ready for LLM integration!** 🚀

