#!/usr/bin/env python3
"""
Test MCP Server via HTTP/SSE endpoint
Works with the running docker-compose service
"""

import requests
import json
import sys
import time
from typing import Optional, Dict, Any

# Configuration
MCP_HOST = "localhost"
MCP_PORT = 3001
BASE_URL = f"http://{MCP_HOST}:{MCP_PORT}"

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(70)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")


def print_success(text: str):
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    print(f"{RED}✗ {text}{RESET}")


def print_info(text: str):
    print(f"{CYAN}ℹ {text}{RESET}")


def print_warning(text: str):
    print(f"{YELLOW}⚠ {text}{RESET}")


def check_server_running() -> bool:
    """Check if the server is accessible"""
    print_header("Checking Server Status")
    
    endpoints_to_try = [
        "/",
        "/sse",
        "/message",
        "/health",
    ]
    
    for endpoint in endpoints_to_try:
        try:
            url = f"{BASE_URL}{endpoint}"
            print_info(f"Trying: {url}")
            response = requests.get(url, timeout=3)
            print_success(f"Server responded with status {response.status_code}")
            
            if response.status_code < 500:  # Any non-server-error response means it's running
                print_success(f"✓ MCP Server is running on {BASE_URL}")
                return True
                
        except requests.exceptions.ConnectionError:
            print_warning(f"Cannot connect to {endpoint}")
        except Exception as e:
            print_warning(f"Error checking {endpoint}: {str(e)}")
    
    print_error("Cannot connect to MCP server")
    print_info(f"Make sure the server is running:")
    print_info(f"  cd /home/mohmd/Documents/Shakiba/slack-mcp-server")
    print_info(f"  docker-compose up -d")
    return False


def test_sse_endpoint() -> bool:
    """Test SSE endpoint availability"""
    print_header("Testing SSE Endpoint")
    
    try:
        url = f"{BASE_URL}/sse"
        print_info(f"Testing SSE endpoint: {url}")
        
        # Try to establish SSE connection
        response = requests.get(
            url,
            headers={'Accept': 'text/event-stream'},
            stream=True,
            timeout=5
        )
        
        print_success(f"SSE endpoint responded with status {response.status_code}")
        
        if response.status_code == 200:
            print_success("✓ SSE transport is working")
            
            # Try to read first few events
            print_info("Reading SSE events (first 3)...")
            event_count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    print(f"  {CYAN}{line[:100]}{RESET}")
                    event_count += 1
                    if event_count >= 3:
                        break
            
            return True
        else:
            print_warning(f"Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print_warning("SSE endpoint timed out (this might be normal)")
        return True  # Timeout on SSE can be normal as it's a streaming endpoint
    except Exception as e:
        print_error(f"SSE test failed: {str(e)}")
        return False


def get_session_id() -> Optional[str]:
    """Get sessionId from SSE endpoint"""
    try:
        url = f"{BASE_URL}/sse"
        response = requests.get(
            url,
            headers={'Accept': 'text/event-stream'},
            stream=True,
            timeout=10
        )
        
        # Read the first few lines to get the session endpoint
        for line in response.iter_lines(decode_unicode=True):
            if line and 'data:' in line:
                # Extract the message endpoint with sessionId
                # Format: data: /message?sessionId=xxx
                if '/message?sessionId=' in line:
                    session_url = line.split('data:')[1].strip()
                    session_id = session_url.split('sessionId=')[1]
                    return session_id
        
        return None
    except Exception as e:
        print_warning(f"Failed to get sessionId: {str(e)}")
        return None


def send_jsonrpc_request(method: str, params: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> Optional[Dict]:
    """Send a JSON-RPC request to the message endpoint"""
    
    request_id = int(time.time() * 1000)
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method
    }
    
    if params:
        payload["params"] = params
    
    try:
        if session_id:
            url = f"{BASE_URL}/message?sessionId={session_id}"
        else:
            url = f"{BASE_URL}/message"
            
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print_error(f"HTTP {response.status_code}: {response.text[:200]}")
            return None
            
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return None


def test_initialize(session_id: str) -> bool:
    """Test MCP initialize"""
    print_header("Testing MCP Initialize")
    
    print_info("Sending initialize request...")
    
    response = send_jsonrpc_request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "roots": {
                "listChanged": True
            }
        },
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    }, session_id)
    
    if not response:
        print_error("No response received")
        return False
    
    if "error" in response:
        print_error(f"Server error: {json.dumps(response['error'], indent=2)}")
        return False
    
    if "result" in response:
        result = response["result"]
        print_success("✓ Server initialized successfully!")
        
        if "serverInfo" in result:
            server_info = result["serverInfo"]
            print(f"\n{BOLD}Server Information:{RESET}")
            print(f"  Name: {CYAN}{server_info.get('name', 'N/A')}{RESET}")
            print(f"  Version: {CYAN}{server_info.get('version', 'N/A')}{RESET}")
        
        if "capabilities" in result:
            caps = result["capabilities"]
            print(f"\n{BOLD}Server Capabilities:{RESET}")
            print(f"  {json.dumps(caps, indent=2)}")
        
        return True
    
    print_error("Unexpected response format")
    print(json.dumps(response, indent=2))
    return False


def test_list_tools(session_id: str) -> bool:
    """Test listing available tools"""
    print_header("Listing Available Tools")
    
    print_info("Requesting tools list...")
    
    response = send_jsonrpc_request("tools/list", {}, session_id)
    
    if not response:
        print_error("No response received")
        return False
    
    if "error" in response:
        print_error(f"Server error: {json.dumps(response['error'], indent=2)}")
        return False
    
    if "result" in response and "tools" in response["result"]:
        tools = response["result"]["tools"]
        print_success(f"✓ Found {len(tools)} tools\n")
        
        for i, tool in enumerate(tools, 1):
            print(f"{BOLD}{i}. {CYAN}{tool['name']}{RESET}")
            print(f"   Description: {tool.get('description', 'N/A')}")
            
            if 'inputSchema' in tool:
                schema = tool['inputSchema']
                if 'properties' in schema:
                    required = schema.get('required', [])
                    print(f"   {BOLD}Parameters:{RESET}")
                    for param, info in schema['properties'].items():
                        req_mark = f"{RED}*{RESET}" if param in required else " "
                        param_type = info.get('type', 'any')
                        param_desc = info.get('description', '')
                        print(f"     {req_mark} {param} ({param_type}): {param_desc[:60]}")
            print()
        
        return True
    
    print_error("Unexpected response format")
    return False


def test_list_resources(session_id: str) -> bool:
    """Test listing available resources"""
    print_header("Listing Available Resources")
    
    print_info("Requesting resources list...")
    
    response = send_jsonrpc_request("resources/list", {}, session_id)
    
    if not response:
        print_error("No response received")
        return False
    
    if "error" in response:
        print_error(f"Server error: {json.dumps(response['error'], indent=2)}")
        return False
    
    if "result" in response and "resources" in response["result"]:
        resources = response["result"]["resources"]
        print_success(f"✓ Found {len(resources)} resources\n")
        
        for i, resource in enumerate(resources, 1):
            print(f"{BOLD}{i}. {CYAN}{resource['name']}{RESET}")
            print(f"   URI: {resource.get('uri', 'N/A')}")
            print(f"   Description: {resource.get('description', 'N/A')}")
            print(f"   MIME Type: {resource.get('mimeType', 'N/A')}")
            print()
        
        return True
    
    print_error("Unexpected response format")
    return False


def test_channels_list(session_id: str) -> bool:
    """Test the channels_list tool"""
    print_header("Testing Tool: channels_list")
    
    print_info("Calling channels_list tool...")
    
    response = send_jsonrpc_request("tools/call", {
        "name": "channels_list",
        "arguments": {}
    }, session_id)
    
    if not response:
        print_error("No response received")
        return False
    
    if "error" in response:
        print_error(f"Server error: {json.dumps(response['error'], indent=2)}")
        return False
    
    if "result" in response:
        result = response["result"]
        print_success("✓ Successfully retrieved channels list")
        
        # Parse the content
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
                lines = text.strip().split('\n')
                
                print(f"\n{BOLD}Channel List (showing first 10):{RESET}")
                for line in lines[:11]:  # Header + 10 channels
                    print(f"  {line}")
                
                if len(lines) > 11:
                    print(f"  ... and {len(lines) - 11} more channels")
                
                print(f"\n{GREEN}✓ Total channels found: {len(lines) - 1}{RESET}")
        
        return True
    
    print_error("Unexpected response format")
    return False


def test_search_messages(session_id: str) -> bool:
    """Test the search messages tool"""
    print_header("Testing Tool: conversations_search_messages")
    
    print_info("Searching for messages containing 'hello'...")
    
    response = send_jsonrpc_request("tools/call", {
        "name": "conversations_search_messages",
        "arguments": {
            "query": "hello",
            "count": 3
        }
    }, session_id)
    
    if not response:
        print_error("No response received")
        return False
    
    if "error" in response:
        error_msg = response["error"].get("message", "Unknown error")
        print_warning(f"Search returned error: {error_msg}")
        # Some errors are expected if search scope isn't configured
        if "search:read" in error_msg.lower():
            print_info("Note: Message search requires the 'search:read' scope in your Slack app")
        return False
    
    if "result" in response:
        result = response["result"]
        print_success("✓ Search completed")
        
        # Parse the content
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
                print(f"\n{BOLD}Search Results:{RESET}")
                print(text[:500])
                if len(text) > 500:
                    print("...")
        
        return True
    
    return False


def main():
    """Main test function"""
    print(f"\n{BOLD}{GREEN}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          Slack MCP Server - Comprehensive Test Suite            ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(RESET)
    
    # Check if server is running
    if not check_server_running():
        sys.exit(1)
    
    # Test SSE endpoint
    test_sse_endpoint()
    
    # Get session ID
    print_header("Getting Session ID")
    print_info("Connecting to SSE endpoint to get session ID...")
    session_id = get_session_id()
    
    if not session_id:
        print_error("Failed to get session ID from SSE endpoint")
        print_info("The server might not be configured for SSE transport")
        sys.exit(1)
    
    print_success(f"Got session ID: {session_id[:20]}...")
    
    # Run MCP protocol tests
    tests_passed = 0
    tests_total = 0
    
    tests = [
        ("Initialize", lambda: test_initialize(session_id)),
        ("List Tools", lambda: test_list_tools(session_id)),
        ("List Resources", lambda: test_list_resources(session_id)),
        ("Get Channels", lambda: test_channels_list(session_id)),
        ("Search Messages", lambda: test_search_messages(session_id)),
    ]
    
    for test_name, test_func in tests:
        tests_total += 1
        try:
            if test_func():
                tests_passed += 1
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {str(e)}")
    
    # Final summary
    print_header("Test Summary")
    
    print(f"{BOLD}Results:{RESET}")
    print(f"  Tests Passed: {GREEN}{tests_passed}{RESET}/{tests_total}")
    print(f"  Tests Failed: {RED}{tests_total - tests_passed}{RESET}/{tests_total}")
    
    if tests_passed == tests_total:
        print(f"\n{BOLD}{GREEN}🎉 All tests passed! Your Slack MCP Server is working perfectly!{RESET}\n")
    elif tests_passed > 0:
        print(f"\n{BOLD}{YELLOW}⚠ Some tests passed. Server is partially working.{RESET}\n")
    else:
        print(f"\n{BOLD}{RED}✗ All tests failed. Please check your configuration.{RESET}\n")
    
    print_info("Server Information:")
    print(f"  URL: {CYAN}{BASE_URL}{RESET}")
    print(f"  SSE Endpoint: {CYAN}{BASE_URL}/sse{RESET}")
    print(f"  Message Endpoint: {CYAN}{BASE_URL}/message{RESET}")
    
    print(f"\n{BOLD}Next Steps:{RESET}")
    print("  • View server logs: docker-compose logs -f")
    print("  • Stop server: docker-compose down")
    print("  • Restart server: docker-compose restart")
    print("  • Update .env file and restart to change configuration")
    
    return 0 if tests_passed == tests_total else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

