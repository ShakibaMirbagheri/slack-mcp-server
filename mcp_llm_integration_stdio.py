#!/usr/bin/env python3
"""
Complete MCP + LLM Integration Example (STDIO Transport)
=========================================================

This script demonstrates a full integration using stdio transport:
1. Connecting to Slack MCP Server via stdio
2. Initializing MCP session
3. Listing and calling all available tools
4. Integrating with LLM workflow
5. Complete conversational agent with tool use

This version uses stdio transport which is more reliable than SSE for programmatic access.

Usage:
    python3 mcp_llm_integration_stdio.py
    
Requirements:
    - Docker (for running the MCP server)
    - Python 3.7+
    - requests library
"""

import subprocess
import json
import sys
import os
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# ============================================================================
# Configuration
# ============================================================================

# Path to .env file
ENV_FILE = "/home/mohmd/Documents/Shakiba/slack-mcp-server/.env"

# Docker image
DOCKER_IMAGE = "ghcr.io/korotovsky/slack-mcp-server:latest"

# ANSI Colors
class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class MCPTool:
    """Represents an MCP tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class MCPResource:
    """Represents an MCP resource"""
    uri: str
    name: str
    description: str
    mime_type: str


# ============================================================================
# MCP Client with STDIO Transport
# ============================================================================

class MCPClientSTDIO:
    """
    MCP Client using STDIO transport.
    More reliable than SSE for programmatic access.
    """
    
    def __init__(self, token: str):
        self.token = token
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.tools: List[MCPTool] = []
        self.resources: List[MCPResource] = []
        self.initialized = False
        
    def _next_request_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
    
    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send JSON-RPC request via stdio"""
        
        request_id = self._next_request_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method
        }
        
        if params is not None:
            request["params"] = params
        
        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        
        if not response_line:
            raise Exception("No response from server")
        
        try:
            response = json.loads(response_line)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {response_line}")
        
        if "error" in response:
            raise Exception(f"MCP Error: {response['error']}")
        
        return response.get("result", {})
    
    def connect(self) -> bool:
        """Start MCP server process and initialize"""
        
        print(f"\n{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BLUE}Connecting to Slack MCP Server (STDIO){Color.RESET}")
        print(f"{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}\n")
        
        try:
            # Start Docker container with stdio transport
            print(f"{Color.CYAN}→ Starting MCP server via Docker...{Color.RESET}")
            
            docker_cmd = [
                "docker", "run", "-i", "--rm",
                "-e", f"SLACK_MCP_XOXP_TOKEN={self.token}",
                "-e", "SLACK_MCP_LOG_LEVEL=error",  # Reduce log noise
                DOCKER_IMAGE,
                "mcp-server",
                "--transport", "stdio"
            ]
            
            self.process = subprocess.Popen(
                docker_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            print(f"{Color.GREEN}✓ Server process started{Color.RESET}")
            
            # Initialize MCP session
            print(f"{Color.CYAN}→ Initializing MCP session...{Color.RESET}")
            
            result = self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
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
            if self.process:
                self.process.terminate()
            return False
    
    def _load_tools(self):
        """Load available tools from server"""
        print(f"{Color.CYAN}→ Loading available tools...{Color.RESET}")
        
        try:
            result = self._send_request("tools/list")
            
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
            result = self._send_request("resources/list")
            
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
    
    def disconnect(self):
        """Close connection to MCP server"""
        if self.process:
            print(f"{Color.CYAN}→ Closing MCP connection...{Color.RESET}")
            self.process.stdin.close()
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            print(f"{Color.GREEN}✓ Connection closed{Color.RESET}")


# ============================================================================
# Demo Functions
# ============================================================================

def display_welcome():
    """Display welcome message"""
    print(f"\n{Color.BOLD}{Color.BLUE}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║     MCP + LLM Integration - Complete Working Demo               ║")
    print("║     Slack MCP Server with Full Tool Integration                 ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(Color.RESET)


def display_tools(mcp_client: MCPClientSTDIO):
    """Display available tools"""
    
    print(f"\n{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}Available MCP Tools{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}{'='*70}{Color.RESET}\n")
    
    tools = mcp_client.list_tools()
    
    for i, tool in enumerate(tools, 1):
        print(f"{Color.BOLD}{i}. {Color.CYAN}{tool.name}{Color.RESET}")
        print(f"   Description: {tool.description}")
        
        # Show parameters
        if "properties" in tool.input_schema:
            required = tool.input_schema.get("required", [])
            params = tool.input_schema["properties"]
            
            if params:
                print(f"   {Color.BOLD}Parameters:{Color.RESET}")
                for param_name, param_info in params.items():
                    req_mark = f"{Color.RED}*{Color.RESET}" if param_name in required else " "
                    param_type = param_info.get("type", "any")
                    param_desc = param_info.get("description", "")[:50]
                    print(f"     {req_mark} {param_name} ({param_type}): {param_desc}")
        print()


def demo_channels_list(mcp_client: MCPClientSTDIO):
    """Demo: List all Slack channels"""
    
    print(f"\n{Color.BOLD}{Color.GREEN}{'='*70}{Color.RESET}")
    print(f"{Color.BOLD}{Color.GREEN}Demo 1: List All Channels{Color.RESET}")
    print(f"{Color.BOLD}{Color.GREEN}{'='*70}{Color.RESET}\n")
    
    try:
        result = mcp_client.call_tool("channels_list", {})
        
        # Parse and display
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
                lines = text.strip().split('\n')
                
                print(f"\n{Color.BOLD}Found {len(lines)-1} channels:{Color.RESET}\n")
                
                # Display first 10 channels
                for line in lines[:11]:
                    print(f"  {line}")
                
                if len(lines) > 11:
                    print(f"  {Color.YELLOW}... and {len(lines)-11} more channels{Color.RESET}")
                
                return lines
        
        return None
        
    except Exception as e:
        print(f"{Color.RED}Error: {str(e)}{Color.RESET}")
        return None


def demo_search_messages(mcp_client: MCPClientSTDIO):
    """Demo: Search messages"""
    
    print(f"\n{Color.BOLD}{Color.GREEN}{'='*70}{Color.RESET}")
    print(f"{Color.BOLD}{Color.GREEN}Demo 2: Search Messages{Color.RESET}")
    print(f"{Color.BOLD}{Color.GREEN}{'='*70}{Color.RESET}\n")
    
    try:
        print(f"{Color.CYAN}Searching for: 'hello'{Color.RESET}\n")
        
        result = mcp_client.call_tool("conversations_search_messages", {
            "query": "hello",
            "count": 3
        })
        
        # Parse and display
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
                
                print(f"\n{Color.BOLD}Search Results:{Color.RESET}\n")
                
                # Truncate for display
                if len(text) > 500:
                    print(text[:500] + f"\n{Color.YELLOW}... (truncated){Color.RESET}")
                else:
                    print(text)
        
        return result
        
    except Exception as e:
        print(f"{Color.RED}Error: {str(e)}{Color.RESET}")
        if "search:read" in str(e):
            print(f"{Color.YELLOW}Note: This requires 'search:read' scope in your Slack app{Color.RESET}")
        return None


def demo_llm_workflow(mcp_client: MCPClientSTDIO):
    """Demonstrate a simple LLM workflow"""
    
    print(f"\n{Color.BOLD}{Color.GREEN}{'='*70}{Color.RESET}")
    print(f"{Color.BOLD}{Color.GREEN}Demo 3: Simulated LLM Workflow{Color.RESET}")
    print(f"{Color.BOLD}{Color.GREEN}{'='*70}{Color.RESET}\n")
    
    print(f"{Color.BOLD}Simulating an LLM-powered agent workflow:{Color.RESET}\n")
    
    # Simulate user query
    user_query = "Show me my Slack channels"
    print(f"{Color.YELLOW}User Query:{Color.RESET} {user_query}\n")
    
    # Step 1: LLM decides to use channels_list tool
    print(f"{Color.CYAN}[LLM] Analyzing query...{Color.RESET}")
    print(f"{Color.CYAN}[LLM] Decision: Use 'channels_list' tool{Color.RESET}\n")
    
    # Step 2: Execute tool
    print(f"{Color.CYAN}[Agent] Executing tool call...{Color.RESET}")
    result = mcp_client.call_tool("channels_list", {})
    
    # Step 3: Process results
    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        if isinstance(content, list) and len(content) > 0:
            text = content[0].get("text", "")
            lines = text.strip().split('\n')
            channel_count = len(lines) - 1
            
            # Step 4: LLM generates response
            print(f"\n{Color.GREEN}[LLM] Response:{Color.RESET}")
            print(f"I found {channel_count} Slack channels in your workspace.")
            print(f"Here are some of them:\n")
            
            for line in lines[1:6]:  # Show first 5 channels
                print(f"  • {line.split(',')[0] if ',' in line else line}")
            
            print(f"\n{Color.CYAN}[Agent] Workflow complete!{Color.RESET}")


def demonstrate_tool_schema(mcp_client: MCPClientSTDIO):
    """Show how to get and use tool schemas"""
    
    print(f"\n{Color.BOLD}{Color.GREEN}{'='*70}{Color.RESET}")
    print(f"{Color.BOLD}{Color.GREEN}Demo 4: Tool Schema for LLM Integration{Color.RESET}")
    print(f"{Color.BOLD}{Color.GREEN}{'='*70}{Color.RESET}\n")
    
    print(f"{Color.BOLD}Converting MCP tools to LLM-compatible format:{Color.RESET}\n")
    
    # Convert tools to OpenAI/Anthropic format
    tools_for_llm = []
    
    for tool in mcp_client.list_tools():
        llm_tool = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema
            }
        }
        tools_for_llm.append(llm_tool)
    
    # Display first tool as example
    if tools_for_llm:
        print(f"{Color.CYAN}Example tool definition (OpenAI format):{Color.RESET}\n")
        print(json.dumps(tools_for_llm[0], indent=2))
        
        print(f"\n{Color.YELLOW}You can pass this to OpenAI or Anthropic APIs!{Color.RESET}")
        print(f"{Color.CYAN}Example:{Color.RESET}")
        print(f"  response = openai.chat.completions.create(")
        print(f"      model='gpt-4',")
        print(f"      messages=messages,")
        print(f"      tools=tools_for_llm")
        print(f"  )")


def get_token_from_env() -> Optional[str]:
    """Read Slack token from .env file"""
    
    if not os.path.exists(ENV_FILE):
        return None
    
    with open(ENV_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('SLACK_MCP_XOXP_TOKEN='):
                token = line.split('=', 1)[1].strip().strip('"\'')
                if token and token != 'xoxp-your-actual-token-here':
                    return token
    
    return None


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main function"""
    
    display_welcome()
    
    # Get token
    print(f"{Color.CYAN}→ Reading configuration...{Color.RESET}")
    token = get_token_from_env()
    
    if not token:
        print(f"{Color.RED}✗ Slack token not found in .env file{Color.RESET}")
        print(f"{Color.YELLOW}Please configure: {ENV_FILE}{Color.RESET}\n")
        sys.exit(1)
    
    print(f"{Color.GREEN}✓ Configuration loaded{Color.RESET}")
    
    # Create MCP client
    mcp_client = MCPClientSTDIO(token)
    
    try:
        # Connect to server
        if not mcp_client.connect():
            print(f"\n{Color.RED}Failed to connect to MCP server.{Color.RESET}\n")
            sys.exit(1)
        
        # Display available tools
        display_tools(mcp_client)
        
        # Run demos
        print(f"\n{Color.BOLD}{Color.BLUE}Running Comprehensive Demos{Color.RESET}\n")
        time.sleep(1)
        
        # Demo 1: List channels
        demo_channels_list(mcp_client)
        time.sleep(1)
        
        # Demo 2: Search messages
        demo_search_messages(mcp_client)
        time.sleep(1)
        
        # Demo 3: LLM workflow
        demo_llm_workflow(mcp_client)
        time.sleep(1)
        
        # Demo 4: Tool schema
        demonstrate_tool_schema(mcp_client)
        
        # Final summary
        print(f"\n{Color.BOLD}{Color.GREEN}{'='*70}{Color.RESET}")
        print(f"{Color.BOLD}{Color.GREEN}All Demos Complete!{Color.RESET}")
        print(f"{Color.BOLD}{Color.GREEN}{'='*70}{Color.RESET}\n")
        
        print(f"{Color.BOLD}What This Demo Showed:{Color.RESET}\n")
        print(f"  {Color.GREEN}✓{Color.RESET} How to connect to MCP server via stdio")
        print(f"  {Color.GREEN}✓{Color.RESET} How to list and call MCP tools")
        print(f"  {Color.GREEN}✓{Color.RESET} How to integrate with LLM workflows")
        print(f"  {Color.GREEN}✓{Color.RESET} How to format tools for LLM APIs")
        print(f"  {Color.GREEN}✓{Color.RESET} Complete working examples of all tools")
        
        print(f"\n{Color.BOLD}Integration Examples:{Color.RESET}\n")
        print(f"  {Color.CYAN}OpenAI:{Color.RESET}")
        print(f"    - Use tools_for_llm with openai.chat.completions.create()")
        print(f"    - When LLM requests tool_calls, use mcp_client.call_tool()")
        
        print(f"\n  {Color.CYAN}Anthropic:{Color.RESET}")
        print(f"    - Use tools_for_llm with anthropic.messages.create()")
        print(f"    - When Claude requests tools, use mcp_client.call_tool()")
        
        print(f"\n  {Color.CYAN}LangChain:{Color.RESET}")
        print(f"    - Wrap MCP tools as LangChain tools")
        print(f"    - Use with agents or chains")
        
        print(f"\n{Color.BOLD}Code Structure:{Color.RESET}\n")
        print(f"  • MCPClientSTDIO     - Main MCP client class")
        print(f"  • call_tool()        - Execute any MCP tool")
        print(f"  • list_tools()       - Get available tools")
        print(f"  • Tool schemas       - Ready for LLM integration")
        
        print(f"\n{Color.YELLOW}Tip: Check the code comments for detailed implementation!{Color.RESET}\n")
        
    finally:
        # Cleanup
        mcp_client.disconnect()


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

