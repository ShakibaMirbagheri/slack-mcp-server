#!/usr/bin/env python3
"""
Complete MCP + LLM Integration Example
======================================

This script demonstrates a full integration of:
1. Connecting to Slack MCP Server
2. Initializing MCP session
3. Listing and calling all available tools
4. Integrating with LLM workflow (OpenAI/Anthropic compatible)
5. Complete conversational agent with tool use

Usage:
    python3 mcp_llm_integration.py
    
Requirements:
    pip install requests anthropic openai
"""

import json
import requests
import time
import sys
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# Configuration
# ============================================================================

MCP_SERVER_URL = "http://localhost:3001"
MCP_SSE_ENDPOINT = f"{MCP_SERVER_URL}/sse"
MCP_MESSAGE_ENDPOINT = f"{MCP_SERVER_URL}/message"

# ANSI Colors for pretty output
class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


# ============================================================================
# MCP Client Implementation
# ============================================================================

@dataclass
class MCPTool:
    """Represents an MCP tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    
    def __str__(self):
        return f"{self.name}: {self.description}"


@dataclass
class MCPResource:
    """Represents an MCP resource"""
    uri: str
    name: str
    description: str
    mime_type: str


class MCPClient:
    """
    MCP Client for connecting to and interacting with MCP servers.
    Handles session management, tool calls, and resource access.
    """
    
    def __init__(self, server_url: str = MCP_SERVER_URL):
        self.server_url = server_url
        self.sse_endpoint = f"{server_url}/sse"
        self.message_endpoint = f"{server_url}/message"
        self.session_id: Optional[str] = None
        self.request_id = 0
        self.tools: List[MCPTool] = []
        self.resources: List[MCPResource] = []
        self.initialized = False
        
    def _next_request_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
    
    def _get_session_id(self) -> str:
        """Obtain session ID from SSE endpoint"""
        print(f"{Color.CYAN}→ Connecting to SSE endpoint...{Color.RESET}")
        
        try:
            response = requests.get(
                self.sse_endpoint,
                headers={'Accept': 'text/event-stream'},
                stream=True,
                timeout=10
            )
            
            # Read SSE stream to get session ID
            for line in response.iter_lines(decode_unicode=True):
                if line and 'sessionId=' in line:
                    session_id = line.split('sessionId=')[1].strip()
                    print(f"{Color.GREEN}✓ Session ID obtained: {session_id[:20]}...{Color.RESET}")
                    return session_id
            
            raise Exception("Failed to get session ID from SSE endpoint")
            
        except Exception as e:
            print(f"{Color.RED}✗ Failed to get session ID: {str(e)}{Color.RESET}")
            raise
    
    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send JSON-RPC request to MCP server"""
        
        request_id = self._next_request_id()
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method
        }
        
        if params:
            payload["params"] = params
        
        # Build URL with session ID
        url = f"{self.message_endpoint}?sessionId={self.session_id}"
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            result = response.json()
            
            if "error" in result:
                raise Exception(f"MCP Error: {result['error']}")
            
            return result.get("result", {})
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def connect(self) -> bool:
        """Connect to MCP server and initialize session"""
        print(f"\n{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BLUE}Connecting to Slack MCP Server{Color.RESET}")
        print(f"{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}\n")
        
        try:
            # Get session ID
            self.session_id = self._get_session_id()
            
            # Send initialize request
            print(f"{Color.CYAN}→ Initializing MCP session...{Color.RESET}")
            result = self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True}
                },
                "clientInfo": {
                    "name": "mcp-llm-integration",
                    "version": "1.0.0"
                }
            })
            
            # Display server info
            if "serverInfo" in result:
                server_info = result["serverInfo"]
                print(f"{Color.GREEN}✓ Connected to: {server_info.get('name')} v{server_info.get('version')}{Color.RESET}")
            
            self.initialized = True
            
            # Load tools and resources
            self._load_tools()
            self._load_resources()
            
            return True
            
        except Exception as e:
            print(f"{Color.RED}✗ Connection failed: {str(e)}{Color.RESET}")
            return False
    
    def _load_tools(self):
        """Load available tools from server"""
        print(f"{Color.CYAN}→ Loading available tools...{Color.RESET}")
        
        try:
            result = self._send_request("tools/list", {})
            
            if "tools" in result:
                self.tools = [
                    MCPTool(
                        name=tool["name"],
                        description=tool.get("description", ""),
                        input_schema=tool.get("inputSchema", {})
                    )
                    for tool in result["tools"]
                ]
                
                print(f"{Color.GREEN}✓ Loaded {len(self.tools)} tools{Color.RESET}")
                
        except Exception as e:
            print(f"{Color.RED}✗ Failed to load tools: {str(e)}{Color.RESET}")
    
    def _load_resources(self):
        """Load available resources from server"""
        print(f"{Color.CYAN}→ Loading available resources...{Color.RESET}")
        
        try:
            result = self._send_request("resources/list", {})
            
            if "resources" in result:
                self.resources = [
                    MCPResource(
                        uri=res["uri"],
                        name=res["name"],
                        description=res.get("description", ""),
                        mime_type=res.get("mimeType", "")
                    )
                    for res in result["resources"]
                ]
                
                print(f"{Color.GREEN}✓ Loaded {len(self.resources)} resources{Color.RESET}")
                
        except Exception as e:
            print(f"{Color.RED}✗ Failed to load resources: {str(e)}{Color.RESET}")
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool with arguments"""
        
        if not self.initialized:
            raise Exception("MCP client not initialized. Call connect() first.")
        
        print(f"{Color.CYAN}→ Calling tool: {tool_name}{Color.RESET}")
        
        try:
            result = self._send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            
            print(f"{Color.GREEN}✓ Tool call successful{Color.RESET}")
            return result
            
        except Exception as e:
            print(f"{Color.RED}✗ Tool call failed: {str(e)}{Color.RESET}")
            raise
    
    def list_tools(self) -> List[MCPTool]:
        """Get list of available tools"""
        return self.tools
    
    def list_resources(self) -> List[MCPResource]:
        """Get list of available resources"""
        return self.resources
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific tool"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.input_schema
        return None


# ============================================================================
# LLM Integration Layer
# ============================================================================

class LLMProvider(Enum):
    """Supported LLM providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    MOCK = "mock"  # For testing without API keys


class LLMAgent:
    """
    LLM Agent with MCP tool integration.
    Demonstrates how to integrate MCP tools with LLM workflows.
    """
    
    def __init__(self, mcp_client: MCPClient, provider: LLMProvider = LLMProvider.MOCK):
        self.mcp_client = mcp_client
        self.provider = provider
        self.conversation_history = []
        
    def _format_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Format MCP tools for LLM consumption (OpenAI/Anthropic format)"""
        tools = []
        
        for tool in self.mcp_client.list_tools():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            })
        
        return tools
    
    def _call_llm(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Call LLM with messages and available tools.
        This is a mock implementation. Replace with actual LLM API calls.
        """
        
        if self.provider == LLMProvider.MOCK:
            # Mock response for demonstration
            return {
                "role": "assistant",
                "content": "I'll help you list the Slack channels.",
                "tool_calls": [{
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "channels_list",
                        "arguments": "{}"
                    }
                }]
            }
        
        # For real implementations:
        elif self.provider == LLMProvider.OPENAI:
            # import openai
            # response = openai.chat.completions.create(
            #     model="gpt-4",
            #     messages=messages,
            #     tools=tools
            # )
            # return response.choices[0].message
            pass
        
        elif self.provider == LLMProvider.ANTHROPIC:
            # import anthropic
            # client = anthropic.Anthropic()
            # response = client.messages.create(
            #     model="claude-3-opus-20240229",
            #     messages=messages,
            #     tools=tools
            # )
            # return response.content[0]
            pass
    
    def process_query(self, user_query: str) -> str:
        """
        Process user query with LLM and MCP tools.
        This demonstrates the full agentic loop.
        """
        
        print(f"\n{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BLUE}Processing User Query{Color.RESET}")
        print(f"{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}\n")
        
        print(f"{Color.YELLOW}User: {user_query}{Color.RESET}\n")
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_query
        })
        
        # Get available tools
        tools = self._format_tools_for_llm()
        
        # Call LLM
        print(f"{Color.CYAN}→ Calling LLM with {len(tools)} available tools...{Color.RESET}")
        llm_response = self._call_llm(self.conversation_history, tools)
        
        # Check if LLM wants to use tools
        if "tool_calls" in llm_response and llm_response["tool_calls"]:
            print(f"{Color.GREEN}✓ LLM requested tool calls{Color.RESET}\n")
            
            # Execute each tool call
            tool_results = []
            for tool_call in llm_response["tool_calls"]:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])
                
                print(f"{Color.CYAN}→ Executing: {function_name}({json.dumps(function_args)}){Color.RESET}")
                
                try:
                    result = self.mcp_client.call_tool(function_name, function_args)
                    tool_results.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(result)
                    })
                except Exception as e:
                    print(f"{Color.RED}✗ Tool call failed: {str(e)}{Color.RESET}")
                    tool_results.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps({"error": str(e)})
                    })
            
            return tool_results
        
        # Return LLM response
        return llm_response.get("content", "No response")


# ============================================================================
# Demo Functions - Test Each Tool
# ============================================================================

def demo_list_channels(mcp_client: MCPClient):
    """Demo: List all Slack channels"""
    print(f"\n{Color.BOLD}{Color.GREEN}Demo: List Channels{Color.RESET}")
    print("="*70)
    
    try:
        result = mcp_client.call_tool("channels_list", {})
        
        # Parse and display results
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
                lines = text.strip().split('\n')
                
                print(f"\n{Color.BOLD}Found {len(lines)-1} channels:{Color.RESET}")
                for line in lines[:11]:  # Show first 10 + header
                    print(f"  {line}")
                
                if len(lines) > 11:
                    print(f"  ... and {len(lines) - 11} more")
        
        return result
        
    except Exception as e:
        print(f"{Color.RED}Error: {str(e)}{Color.RESET}")
        return None


def demo_get_conversation_history(mcp_client: MCPClient, channel_id: str = None):
    """Demo: Get conversation history from a channel"""
    print(f"\n{Color.BOLD}{Color.GREEN}Demo: Get Conversation History{Color.RESET}")
    print("="*70)
    
    if not channel_id:
        print(f"{Color.YELLOW}⚠ No channel ID provided. Skipping this demo.{Color.RESET}")
        print(f"{Color.CYAN}  Tip: Get a channel ID from channels_list first{Color.RESET}")
        return None
    
    try:
        result = mcp_client.call_tool("conversations_history", {
            "channel_id": channel_id,
            "limit": 5
        })
        
        print(f"\n{Color.BOLD}Recent messages from channel:{Color.RESET}")
        print(json.dumps(result, indent=2)[:500] + "...")
        
        return result
        
    except Exception as e:
        print(f"{Color.RED}Error: {str(e)}{Color.RESET}")
        return None


def demo_search_messages(mcp_client: MCPClient):
    """Demo: Search messages in Slack"""
    print(f"\n{Color.BOLD}{Color.GREEN}Demo: Search Messages{Color.RESET}")
    print("="*70)
    
    try:
        result = mcp_client.call_tool("conversations_search_messages", {
            "query": "hello",
            "count": 3
        })
        
        print(f"\n{Color.BOLD}Search results:{Color.RESET}")
        
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
                print(text[:500])
                if len(text) > 500:
                    print("...")
        
        return result
        
    except Exception as e:
        print(f"{Color.RED}Error: {str(e)}{Color.RESET}")
        print(f"{Color.YELLOW}Note: This may require 'search:read' scope in your Slack app{Color.RESET}")
        return None


def demo_get_thread_replies(mcp_client: MCPClient, channel_id: str = None, thread_ts: str = None):
    """Demo: Get thread replies"""
    print(f"\n{Color.BOLD}{Color.GREEN}Demo: Get Thread Replies{Color.RESET}")
    print("="*70)
    
    if not channel_id or not thread_ts:
        print(f"{Color.YELLOW}⚠ No channel ID or thread timestamp provided. Skipping this demo.{Color.RESET}")
        print(f"{Color.CYAN}  Tip: Get these from a conversation history first{Color.RESET}")
        return None
    
    try:
        result = mcp_client.call_tool("conversations_replies", {
            "channel_id": channel_id,
            "thread_ts": thread_ts
        })
        
        print(f"\n{Color.BOLD}Thread replies:{Color.RESET}")
        print(json.dumps(result, indent=2)[:500] + "...")
        
        return result
        
    except Exception as e:
        print(f"{Color.RED}Error: {str(e)}{Color.RESET}")
        return None


def demo_post_message(mcp_client: MCPClient, channel_id: str = None):
    """Demo: Post a message (if enabled)"""
    print(f"\n{Color.BOLD}{Color.GREEN}Demo: Post Message{Color.RESET}")
    print("="*70)
    
    # Check if tool is available
    tool_available = any(t.name == "conversations_add_message" for t in mcp_client.list_tools())
    
    if not tool_available:
        print(f"{Color.YELLOW}⚠ Message posting is not enabled.{Color.RESET}")
        print(f"{Color.CYAN}  To enable: Set SLACK_MCP_ADD_MESSAGE_TOOL=true in .env{Color.RESET}")
        return None
    
    if not channel_id:
        print(f"{Color.YELLOW}⚠ No channel ID provided. Skipping this demo.{Color.RESET}")
        return None
    
    try:
        result = mcp_client.call_tool("conversations_add_message", {
            "channel_id": channel_id,
            "text": "Test message from MCP integration! 🚀"
        })
        
        print(f"{Color.GREEN}✓ Message posted successfully!{Color.RESET}")
        return result
        
    except Exception as e:
        print(f"{Color.RED}Error: {str(e)}{Color.RESET}")
        return None


# ============================================================================
# Main Demo Application
# ============================================================================

def display_welcome():
    """Display welcome message"""
    print(f"\n{Color.BOLD}{Color.BLUE}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║        MCP + LLM Integration - Complete Demo                    ║")
    print("║        Slack MCP Server with LLM Workflow                       ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(Color.RESET)


def display_tools_and_resources(mcp_client: MCPClient):
    """Display available tools and resources"""
    print(f"\n{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}Available Tools and Resources{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}\n")
    
    # Display tools
    tools = mcp_client.list_tools()
    print(f"{Color.BOLD}Tools ({len(tools)}):{Color.RESET}\n")
    
    for i, tool in enumerate(tools, 1):
        print(f"{Color.BOLD}{i}. {Color.CYAN}{tool.name}{Color.RESET}")
        print(f"   {tool.description}")
        
        # Show parameters
        if "properties" in tool.input_schema:
            required = tool.input_schema.get("required", [])
            print(f"   {Color.BOLD}Parameters:{Color.RESET}")
            for param_name, param_info in tool.input_schema["properties"].items():
                req_mark = f"{Color.RED}*{Color.RESET}" if param_name in required else " "
                param_type = param_info.get("type", "any")
                print(f"     {req_mark} {param_name} ({param_type})")
        print()
    
    # Display resources
    resources = mcp_client.list_resources()
    if resources:
        print(f"{Color.BOLD}Resources ({len(resources)}):{Color.RESET}\n")
        
        for i, resource in enumerate(resources, 1):
            print(f"{Color.BOLD}{i}. {Color.CYAN}{resource.name}{Color.RESET}")
            print(f"   URI: {resource.uri}")
            print(f"   Type: {resource.mime_type}")
            print()


def run_comprehensive_demo(mcp_client: MCPClient):
    """Run comprehensive demo of all features"""
    
    print(f"\n{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}Running Comprehensive Tool Demo{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}\n")
    
    # Demo 1: List channels
    channels_result = demo_list_channels(mcp_client)
    time.sleep(1)
    
    # Demo 2: Search messages
    search_result = demo_search_messages(mcp_client)
    time.sleep(1)
    
    # Demo 3: Get conversation history (would need a channel ID)
    # Uncomment and provide channel ID to test:
    # demo_get_conversation_history(mcp_client, channel_id="C1234567890")
    
    # Demo 4: Get thread replies (would need channel ID and thread timestamp)
    # Uncomment and provide details to test:
    # demo_get_thread_replies(mcp_client, channel_id="C1234567890", thread_ts="1234567890.123456")
    
    # Demo 5: Post message (if enabled)
    # Uncomment and provide channel ID to test:
    # demo_post_message(mcp_client, channel_id="C1234567890")


def demo_llm_integration(mcp_client: MCPClient):
    """Demonstrate LLM integration"""
    
    print(f"\n{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}LLM Integration Demo{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}\n")
    
    # Create LLM agent
    agent = LLMAgent(mcp_client, provider=LLMProvider.MOCK)
    
    # Example queries
    queries = [
        "List all my Slack channels",
        "Search for messages about 'meeting'",
        "Get the recent messages from #general"
    ]
    
    for query in queries:
        result = agent.process_query(query)
        print(f"{Color.GREEN}✓ Query processed{Color.RESET}\n")
        time.sleep(1)


def main():
    """Main function"""
    
    display_welcome()
    
    # Create MCP client
    mcp_client = MCPClient(MCP_SERVER_URL)
    
    # Connect to server
    if not mcp_client.connect():
        print(f"\n{Color.RED}Failed to connect to MCP server.{Color.RESET}")
        print(f"{Color.YELLOW}Make sure the server is running: docker-compose up{Color.RESET}\n")
        sys.exit(1)
    
    # Display available tools and resources
    display_tools_and_resources(mcp_client)
    
    # Run comprehensive demo
    run_comprehensive_demo(mcp_client)
    
    # Demo LLM integration
    demo_llm_integration(mcp_client)
    
    # Final summary
    print(f"\n{Color.BOLD}{Color.GREEN}{'='*70}{Color.RESET}")
    print(f"{Color.BOLD}{Color.GREEN}Demo Complete!{Color.RESET}")
    print(f"{Color.BOLD}{Color.GREEN}{'='*70}{Color.RESET}\n")
    
    print(f"{Color.BOLD}What you learned:{Color.RESET}")
    print(f"  ✓ How to connect to an MCP server")
    print(f"  ✓ How to list and call MCP tools")
    print(f"  ✓ How to integrate MCP with LLM workflows")
    print(f"  ✓ How to build agentic applications with MCP")
    
    print(f"\n{Color.BOLD}Next steps:{Color.RESET}")
    print(f"  • Modify the LLMAgent class to use real LLM APIs (OpenAI/Anthropic)")
    print(f"  • Add error handling and retry logic")
    print(f"  • Build a conversational interface")
    print(f"  • Integrate with your application")
    
    print(f"\n{Color.CYAN}See the code comments for implementation details!{Color.RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}Demo interrupted by user{Color.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Color.RED}Error: {str(e)}{Color.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

