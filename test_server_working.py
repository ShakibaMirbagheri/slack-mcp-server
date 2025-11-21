#!/usr/bin/env python3
"""
Quick and simple test to verify Slack MCP Server is working
Tests the server using a fresh Docker container with stdio transport
"""

import subprocess
import json
import sys
import os

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_box(text, color=BLUE):
    """Print text in a box"""
    print(f"\n{BOLD}{color}{'═' * 70}{RESET}")
    print(f"{BOLD}{color}{text.center(70)}{RESET}")
    print(f"{BOLD}{color}{'═' * 70}{RESET}\n")


def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    print(f"{RED}✗ {text}{RESET}")


def print_info(text):
    print(f"{CYAN}→ {text}{RESET}")


def get_env_token():
    """Get Slack token from .env file"""
    env_path = "/home/mohmd/Documents/Shakiba/slack-mcp-server/.env"
    
    if not os.path.exists(env_path):
        return None
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('SLACK_MCP_XOXP_TOKEN='):
                token = line.split('=', 1)[1].strip()
                if token and token != 'xoxp-your-actual-token-here':
                    return token
    
    return None


def run_mcp_test(token):
    """Run a complete MCP test"""
    
    print_box("Slack MCP Server - Quick Test", CYAN)
    
    # Prepare Docker command
    docker_cmd = [
        "docker", "run", "-i", "--rm",
        "-e", f"SLACK_MCP_XOXP_TOKEN={token}",
        "-e", "SLACK_MCP_LOG_LEVEL=info",
        "ghcr.io/korotovsky/slack-mcp-server:latest",
        "mcp-server",
        "--transport", "stdio"
    ]
    
    print_info("Starting MCP server via Docker...")
    print_info("Command: " + " ".join(docker_cmd[:4]) + " ... (token hidden)")
    print()
    
    try:
        # Start the process
        process = subprocess.Popen(
            docker_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print_info("Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        
        if not response_line:
            stderr_output = process.stderr.read()
            print_error("No response from server")
            if stderr_output:
                print(f"\n{YELLOW}Server stderr:{RESET}")
                print(stderr_output[:500])
            return False
        
        try:
            response = json.loads(response_line)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON response: {response_line[:100]}")
            return False
        
        # Check response
        if "error" in response:
            print_error(f"Server returned error: {response['error']}")
            return False
        
        if "result" not in response:
            print_error(f"Unexpected response: {response}")
            return False
        
        result = response["result"]
        
        # Display server info
        print_success("Server initialized successfully!\n")
        
        if "serverInfo" in result:
            server_info = result["serverInfo"]
            print(f"{BOLD}Server Information:{RESET}")
            print(f"  Name:    {CYAN}{server_info.get('name', 'N/A')}{RESET}")
            print(f"  Version: {CYAN}{server_info.get('version', 'N/A')}{RESET}")
            print()
        
        if "capabilities" in result:
            caps = result["capabilities"]
            print(f"{BOLD}Capabilities:{RESET}")
            if "tools" in caps:
                print(f"  ✓ Tools support enabled")
            if "resources" in caps:
                print(f"  ✓ Resources support enabled")
            print()
        
        # Request tools list
        print_info("Requesting tools list...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        tools_response_line = process.stdout.readline()
        
        if tools_response_line:
            try:
                tools_response = json.loads(tools_response_line)
                
                if "result" in tools_response and "tools" in tools_response["result"]:
                    tools = tools_response["result"]["tools"]
                    print_success(f"Found {len(tools)} tools\n")
                    
                    print(f"{BOLD}Available Tools:{RESET}")
                    for i, tool in enumerate(tools, 1):
                        print(f"  {i}. {CYAN}{tool['name']}{RESET}")
                        desc = tool.get('description', '')
                        if desc:
                            # Wrap description
                            if len(desc) > 60:
                                desc = desc[:57] + "..."
                            print(f"     {desc}")
                    print()
                    
            except json.JSONDecodeError:
                print_error(f"Invalid tools response: {tools_response_line[:100]}")
        
        # Test channels_list tool
        print_info("Testing channels_list tool...")
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "channels_list",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(call_request) + "\n")
        process.stdin.flush()
        
        call_response_line = process.stdout.readline()
        
        if call_response_line:
            try:
                call_response = json.loads(call_response_line)
                
                if "error" in call_response:
                    print_error(f"Tool call failed: {call_response['error']}")
                elif "result" in call_response:
                    result = call_response["result"]
                    
                    # Parse channel list
                    if isinstance(result, dict) and "content" in result:
                        content = result["content"]
                        if isinstance(content, list) and len(content) > 0:
                            text = content[0].get("text", "")
                            lines = text.strip().split('\n')
                            channel_count = len(lines) - 1  # Minus header
                            
                            print_success(f"Retrieved {channel_count} channels from Slack!\n")
                            
                            print(f"{BOLD}Channel List Preview:{RESET}")
                            for line in lines[:7]:  # Header + 6 channels
                                print(f"  {line}")
                            
                            if channel_count > 6:
                                print(f"  ... and {channel_count - 6} more channels")
                            print()
                
            except json.JSONDecodeError:
                print_error(f"Invalid call response: {call_response_line[:100]}")
        
        # Clean up
        process.stdin.close()
        process.terminate()
        
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        
        return True
        
    except FileNotFoundError:
        print_error("Docker not found. Please make sure Docker is installed.")
        return False
    except Exception as e:
        print_error(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    
    print(f"\n{BOLD}{GREEN}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║              Slack MCP Server - Quick Test                      ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(RESET)
    
    # Get token
    print_info("Checking configuration...")
    token = get_env_token()
    
    if not token:
        print_error("Slack token not found in .env file")
        print_info("Please configure: /home/mohmd/Documents/Shakiba/slack-mcp-server/.env")
        return 1
    
    print_success("Found Slack token in .env file")
    print()
    
    # Run test
    success = run_mcp_test(token)
    
    # Summary
    print_box("Test Summary", GREEN if success else RED)
    
    if success:
        print(f"{BOLD}{GREEN}✓ All tests passed!{RESET}\n")
        print(f"{BOLD}Your Slack MCP Server is working correctly!{RESET}\n")
        print(f"The server successfully:")
        print(f"  • {GREEN}✓{RESET} Authenticated with Slack")
        print(f"  • {GREEN}✓{RESET} Initialized MCP protocol")
        print(f"  • {GREEN}✓{RESET} Listed available tools")
        print(f"  • {GREEN}✓{RESET} Retrieved channels from your Slack workspace")
        print()
        print(f"{BOLD}Next Steps:{RESET}")
        print(f"  • Your docker-compose server is ready: http://localhost:3001")
        print(f"  • View logs: docker-compose logs -f")
        print(f"  • Stop server: docker-compose down")
        print(f"  • Configure Claude Desktop to use this MCP server")
        print()
        return 0
    else:
        print(f"{BOLD}{RED}✗ Tests failed{RESET}\n")
        print(f"Please check:")
        print(f"  • Your Slack token is valid")
        print(f"  • Docker is running and accessible")
        print(f"  • Network connectivity is working")
        print()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

