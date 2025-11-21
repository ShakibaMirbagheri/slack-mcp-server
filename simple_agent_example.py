#!/usr/bin/env python3
"""
Simple Slack MCP Agent - Complete Working Example
==================================================

This script works with your running docker-compose server.
No Docker permissions needed!

Usage:
    python3 simple_agent_example.py

Requirements:
    pip install requests
"""

import requests
import json
import time
import sys

# ANSI Colors
GREEN = '\033[92m'
BLUE = '\033[94m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

MCP_SERVER_URL = "http://localhost:3001"


class SlackMCPAgent:
    """
    Simple agent that connects to your MCP server and executes tools.
    Perfect starting point for building LLM-powered Slack agents.
    """
    
    def __init__(self, server_url=MCP_SERVER_URL):
        self.server_url = server_url
        self.session_id = None
        self.request_id = 0
        self.tools = []
        
    def connect(self):
        """Connect to MCP server and get session"""
        print(f"{CYAN}→ Connecting to MCP server at {self.server_url}...{RESET}")
        
        try:
            # Connect to SSE endpoint to get session ID
            response = requests.get(
                f"{self.server_url}/sse",
                stream=True,
                timeout=10
            )
            
            # Read session ID from SSE stream
            for line in response.iter_lines(decode_unicode=True):
                if line and 'sessionId=' in line:
                    self.session_id = line.split('sessionId=')[1].strip()
                    print(f"{GREEN}✓ Connected! Session: {self.session_id[:25]}...{RESET}\n")
                    return True
            
            print(f"{RED}✗ Failed to get session ID{RESET}")
            return False
            
        except requests.exceptions.ConnectionError:
            print(f"{RED}✗ Cannot connect to server{RESET}")
            print(f"{YELLOW}Make sure the server is running: docker-compose up -d{RESET}")
            return False
        except Exception as e:
            print(f"{RED}✗ Connection error: {str(e)}{RESET}")
            return False
    
    def _make_request(self, method, params=None):
        """Make JSON-RPC request to MCP server"""
        self.request_id += 1
        
        url = f"{self.server_url}/message?sessionId={self.session_id}"
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            if "error" in result:
                error_msg = result["error"].get("message", "Unknown error")
                print(f"{RED}✗ MCP Error: {error_msg}{RESET}")
                return None
            
            return result.get("result", {})
            
        except Exception as e:
            print(f"{RED}✗ Request failed: {str(e)}{RESET}")
            return None
    
    def list_tools(self):
        """Get list of available tools"""
        print(f"{CYAN}→ Loading available tools...{RESET}")
        
        result = self._make_request("tools/list")
        
        if result and "tools" in result:
            self.tools = result["tools"]
            print(f"{GREEN}✓ Loaded {len(self.tools)} tools{RESET}\n")
            
            print(f"{BOLD}Available Tools:{RESET}\n")
            for i, tool in enumerate(self.tools, 1):
                print(f"  {i}. {CYAN}{tool['name']}{RESET}")
                print(f"     {tool.get('description', 'No description')}")
            print()
            
            return self.tools
        
        return []
    
    def call_tool(self, tool_name, arguments=None):
        """Call a specific tool"""
        print(f"{CYAN}→ Calling tool: {BOLD}{tool_name}{RESET}")
        
        result = self._make_request("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        })
        
        if result:
            print(f"{GREEN}✓ Tool executed successfully{RESET}\n")
        
        return result
    
    def display_tool_result(self, result):
        """Pretty print tool results"""
        if not result:
            return
        
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
                
                # Truncate long results
                if len(text) > 800:
                    print(text[:800])
                    print(f"{YELLOW}... (truncated, {len(text)} total chars){RESET}\n")
                else:
                    print(text)
                    print()


def demo_list_channels(agent):
    """Demo: List all Slack channels"""
    print(f"{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}Demo 1: List All Slack Channels{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")
    
    result = agent.call_tool("channels_list")
    
    if result:
        agent.display_tool_result(result)
        
        # Count channels
        if isinstance(result, dict) and "content" in result:
            text = result["content"][0].get("text", "")
            channel_count = len(text.strip().split('\n')) - 1
            print(f"{GREEN}📊 Found {channel_count} channels total{RESET}\n")
    
    return result


def demo_search_messages(agent):
    """Demo: Search Slack messages"""
    print(f"{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}Demo 2: Search Slack Messages{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")
    
    search_query = "hello"
    print(f"{YELLOW}Searching for: '{search_query}'{RESET}\n")
    
    result = agent.call_tool("conversations_search_messages", {
        "query": search_query,
        "count": 5
    })
    
    if result:
        agent.display_tool_result(result)
    else:
        print(f"{YELLOW}Note: Search may require 'search:read' scope in your Slack app{RESET}\n")
    
    return result


def demo_simulated_llm_workflow(agent):
    """Demo: Simulate an LLM-powered workflow"""
    print(f"{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}Demo 3: Simulated LLM Agent Workflow{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")
    
    # Simulate user asking a question
    user_query = "What Slack channels do we have?"
    print(f"{YELLOW}👤 User:{RESET} {user_query}\n")
    
    # Step 1: LLM analyzes the query (simulated)
    print(f"{CYAN}🤖 Agent (thinking):{RESET} The user wants to know about Slack channels.")
    print(f"{CYAN}🤖 Agent (thinking):{RESET} I should use the 'channels_list' tool.\n")
    
    # Step 2: Agent calls the tool
    print(f"{CYAN}🤖 Agent (action):{RESET} Calling channels_list tool...\n")
    result = agent.call_tool("channels_list")
    
    # Step 3: Process results
    if result and isinstance(result, dict) and "content" in result:
        text = result["content"][0].get("text", "")
        lines = text.strip().split('\n')
        channel_count = len(lines) - 1
        
        # Step 4: Generate response (simulated LLM)
        print(f"{GREEN}🤖 Agent (response):{RESET}")
        print(f"I found {channel_count} Slack channels in your workspace. Here are the first few:\n")
        
        for line in lines[1:6]:  # Show first 5 channels
            channel_name = line.split(',')[0] if ',' in line else line
            print(f"  • {channel_name}")
        
        if channel_count > 5:
            print(f"  ... and {channel_count - 5} more channels")
        
        print(f"\n{GREEN}✓ Workflow complete!{RESET}\n")


def show_integration_code():
    """Show how to integrate with real LLMs"""
    print(f"{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}Integration with Real LLMs{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")
    
    print(f"{BOLD}To integrate with OpenAI GPT-4:{RESET}\n")
    print('''
import openai

# Define tools in OpenAI format
tools = [{
    "type": "function",
    "function": {
        "name": "channels_list",
        "description": "List all Slack channels",
        "parameters": {"type": "object", "properties": {}}
    }
}]

# Call OpenAI
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Show my Slack channels"}],
    tools=tools
)

# If GPT wants to use tools
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    result = agent.call_tool(tool_call.function.name, {})
    # Send result back to GPT...
''')
    
    print(f"\n{BOLD}To integrate with Anthropic Claude:{RESET}\n")
    print('''
import anthropic

client = anthropic.Anthropic()

tools = [{
    "name": "channels_list",
    "description": "List all Slack channels",
    "input_schema": {"type": "object", "properties": {}}
}]

response = client.messages.create(
    model="claude-3-opus-20240229",
    messages=[{"role": "user", "content": "Show my Slack channels"}],
    tools=tools
)

# If Claude wants to use tools
if response.stop_reason == "tool_use":
    for content in response.content:
        if content.type == "tool_use":
            result = agent.call_tool(content.name, content.input)
            # Send result back to Claude...
''')
    
    print(f"\n{YELLOW}💡 See MCP_LLM_INTEGRATION_GUIDE.md for complete examples!{RESET}\n")


def main():
    """Main function"""
    
    print(f"\n{BOLD}{GREEN}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║            Simple Slack MCP Agent - Working Example             ║")
    print("║            Ready for LLM Integration                            ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}\n")
    
    # Create agent
    agent = SlackMCPAgent()
    
    # Connect to server
    if not agent.connect():
        print(f"\n{RED}Failed to connect to MCP server.{RESET}")
        print(f"\n{YELLOW}Troubleshooting:{RESET}")
        print(f"  1. Check if server is running: {CYAN}docker-compose ps{RESET}")
        print(f"  2. Start server if needed: {CYAN}docker-compose up -d{RESET}")
        print(f"  3. Check logs: {CYAN}docker-compose logs -f{RESET}")
        sys.exit(1)
    
    # List available tools
    agent.list_tools()
    
    # Run demos
    print(f"{BOLD}Running Interactive Demos...{RESET}\n")
    time.sleep(1)
    
    # Demo 1: List channels
    demo_list_channels(agent)
    time.sleep(2)
    
    # Demo 2: Search messages
    demo_search_messages(agent)
    time.sleep(2)
    
    # Demo 3: Simulated LLM workflow
    demo_simulated_llm_workflow(agent)
    time.sleep(2)
    
    # Show integration examples
    show_integration_code()
    
    # Summary
    print(f"{BOLD}{GREEN}{'='*70}{RESET}")
    print(f"{BOLD}{GREEN}Demo Complete! 🎉{RESET}")
    print(f"{BOLD}{GREEN}{'='*70}{RESET}\n")
    
    print(f"{BOLD}What You Just Saw:{RESET}\n")
    print(f"  {GREEN}✓{RESET} Connection to MCP server")
    print(f"  {GREEN}✓{RESET} Listing available tools")
    print(f"  {GREEN}✓{RESET} Calling Slack tools programmatically")
    print(f"  {GREEN}✓{RESET} Processing and displaying results")
    print(f"  {GREEN}✓{RESET} Simulated LLM agent workflow")
    
    print(f"\n{BOLD}The SlackMCPAgent Class Provides:{RESET}\n")
    print(f"  • {CYAN}connect(){RESET} - Connect to MCP server")
    print(f"  • {CYAN}list_tools(){RESET} - Get available tools")
    print(f"  • {CYAN}call_tool(name, args){RESET} - Execute any tool")
    print(f"  • {CYAN}display_tool_result(){RESET} - Pretty print results")
    
    print(f"\n{BOLD}Next Steps:{RESET}\n")
    print(f"  1. Copy the {CYAN}SlackMCPAgent{RESET} class to your project")
    print(f"  2. Integrate with OpenAI/Anthropic (see examples above)")
    print(f"  3. Build your conversational agent!")
    print(f"  4. Read {CYAN}MCP_LLM_INTEGRATION_GUIDE.md{RESET} for complete patterns")
    
    print(f"\n{BOLD}Files You Can Use:{RESET}\n")
    print(f"  • {CYAN}simple_agent_example.py{RESET} (this file) - Copy and modify")
    print(f"  • {CYAN}MCP_LLM_INTEGRATION_GUIDE.md{RESET} - Complete guide")
    print(f"  • {CYAN}mcp_llm_integration.py{RESET} - Advanced HTTP/SSE example")
    print(f"  • {CYAN}mcp_llm_integration_stdio.py{RESET} - STDIO example")
    print(f"  • {CYAN}requirements.txt{RESET} - Python dependencies")
    
    print(f"\n{GREEN}✨ Your Slack MCP Server is ready for LLM integration! ✨{RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Demo interrupted by user{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}Error: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

