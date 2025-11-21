#!/bin/bash
# Simple test script to verify Slack MCP Server is working
# No special permissions required

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "\n${BOLD}${GREEN}╔══════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${GREEN}║    Slack MCP Server - Simple Connectivity Test          ║${RESET}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════╝${RESET}\n"

SERVER_URL="http://localhost:3001"
PASSED=0
FAILED=0

# Test 1: Check if port 3001 is listening
echo -e "${CYAN}→ Test 1: Checking if server port is open...${RESET}"
if ss -tln | grep -q ":3001"; then
    echo -e "${GREEN}  ✓ Port 3001 is LISTENING${RESET}"
    ((PASSED++))
else
    echo -e "${RED}  ✗ Port 3001 is NOT listening${RESET}"
    echo -e "${YELLOW}  ℹ Start the server with: sudo docker-compose up -d${RESET}"
    ((FAILED++))
fi
echo

# Test 2: Check if server responds to HTTP requests
echo -e "${CYAN}→ Test 2: Testing HTTP connectivity...${RESET}"
if curl -s -f -m 5 "$SERVER_URL/" > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Server responds to HTTP requests${RESET}"
    ((PASSED++))
elif curl -s -m 5 "$SERVER_URL/" 2>&1 | grep -q "404\|400\|Connection refused"; then
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 5 "$SERVER_URL/" 2>/dev/null)
    if [ "$STATUS" == "404" ] || [ "$STATUS" == "400" ]; then
        echo -e "${GREEN}  ✓ Server is responding (HTTP $STATUS)${RESET}"
        ((PASSED++))
    else
        echo -e "${RED}  ✗ Server not responding${RESET}"
        ((FAILED++))
    fi
else
    echo -e "${RED}  ✗ Cannot connect to server${RESET}"
    ((FAILED++))
fi
echo

# Test 3: Check SSE endpoint
echo -e "${CYAN}→ Test 3: Testing SSE endpoint (/sse)...${RESET}"
SSE_RESPONSE=$(timeout 3 curl -s -N -H "Accept: text/event-stream" "$SERVER_URL/sse" 2>&1 | head -n 3)
if echo "$SSE_RESPONSE" | grep -q "sessionId"; then
    echo -e "${GREEN}  ✓ SSE endpoint is working${RESET}"
    SESSION_ID=$(echo "$SSE_RESPONSE" | grep -oP 'sessionId=\K[^[:space:]]+' | head -1)
    echo -e "${CYAN}  → Session ID: ${SESSION_ID:0:20}...${RESET}"
    ((PASSED++))
else
    echo -e "${RED}  ✗ SSE endpoint not responding correctly${RESET}"
    ((FAILED++))
fi
echo

# Test 4: Check .env configuration
echo -e "${CYAN}→ Test 4: Checking configuration file...${RESET}"
if [ -f ".env" ]; then
    if grep -q "SLACK_MCP_XOXP_TOKEN=xoxp-" .env; then
        TOKEN=$(grep "SLACK_MCP_XOXP_TOKEN=" .env | cut -d= -f2 | tr -d ' "')
        if [ "$TOKEN" != "xoxp-your-actual-token-here" ] && [ ! -z "$TOKEN" ]; then
            echo -e "${GREEN}  ✓ .env file configured with Slack token${RESET}"
            echo -e "${CYAN}  → Token: ${TOKEN:0:15}...${RESET}"
            ((PASSED++))
        else
            echo -e "${YELLOW}  ⚠ .env file exists but token needs configuration${RESET}"
            ((FAILED++))
        fi
    else
        echo -e "${YELLOW}  ⚠ .env file exists but SLACK_MCP_XOXP_TOKEN not found${RESET}"
        ((FAILED++))
    fi
else
    echo -e "${RED}  ✗ .env file not found${RESET}"
    ((FAILED++))
fi
echo

# Test 5: Check if Docker container is running
echo -e "${CYAN}→ Test 5: Checking Docker container status...${RESET}"
if command -v docker &> /dev/null; then
    if sudo docker ps 2>/dev/null | grep -q "slack-mcp-server\|korotovsky/slack-mcp-server"; then
        CONTAINER_NAME=$(sudo docker ps 2>/dev/null | grep "slack-mcp-server\|korotovsky/slack-mcp-server" | awk '{print $NF}')
        echo -e "${GREEN}  ✓ Docker container is running: $CONTAINER_NAME${RESET}"
        ((PASSED++))
    else
        echo -e "${YELLOW}  ⚠ Docker container not found (permission issue or not running)${RESET}"
        echo -e "${CYAN}  → Try: sudo docker-compose ps${RESET}"
    fi
else
    echo -e "${YELLOW}  ⚠ Docker command not found${RESET}"
fi
echo

# Summary
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${BLUE}                     Test Summary                          ${RESET}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════${RESET}\n"

TOTAL=$((PASSED + FAILED))
echo -e "${BOLD}Results:${RESET}"
echo -e "  Tests Passed:  ${GREEN}${PASSED}${RESET}/${TOTAL}"
echo -e "  Tests Failed:  ${RED}${FAILED}${RESET}/${TOTAL}"
echo

if [ $FAILED -eq 0 ] && [ $PASSED -ge 3 ]; then
    echo -e "${BOLD}${GREEN}🎉 SUCCESS! Your Slack MCP Server is working correctly!${RESET}\n"
    
    echo -e "${BOLD}Server Information:${RESET}"
    echo -e "  • URL:          ${CYAN}http://localhost:3001${RESET}"
    echo -e "  • SSE Endpoint: ${CYAN}http://localhost:3001/sse${RESET}"
    echo -e "  • Status:       ${GREEN}✓ OPERATIONAL${RESET}"
    echo
    
    echo -e "${BOLD}Quick Commands:${RESET}"
    echo -e "  • View logs:    ${CYAN}sudo docker-compose logs -f${RESET}"
    echo -e "  • Restart:      ${CYAN}sudo docker-compose restart${RESET}"
    echo -e "  • Stop:         ${CYAN}sudo docker-compose down${RESET}"
    echo
    
    echo -e "${BOLD}Next Steps:${RESET}"
    echo -e "  1. Your server is ready to use with Claude Desktop or other MCP clients"
    echo -e "  2. See ${CYAN}TEST_RESULTS.md${RESET} for detailed setup instructions"
    echo -e "  3. Check ${CYAN}SLACK_CONNECTION_GUIDE.md${RESET} for more information"
    echo
    
    exit 0
else
    echo -e "${BOLD}${RED}⚠ Some tests failed. Please check the issues above.${RESET}\n"
    
    echo -e "${BOLD}Common Issues:${RESET}"
    if ! ss -tln | grep -q ":3001"; then
        echo -e "  • Server not running: ${CYAN}sudo docker-compose up -d${RESET}"
    fi
    if [ ! -f ".env" ]; then
        echo -e "  • Missing .env file: ${CYAN}cp .env.example .env${RESET}"
        echo -e "    Then edit .env with your Slack token"
    fi
    echo
    
    echo -e "${BOLD}Get Help:${RESET}"
    echo -e "  • View logs:    ${CYAN}sudo docker-compose logs -f${RESET}"
    echo -e "  • Check status: ${CYAN}sudo docker-compose ps${RESET}"
    echo -e "  • Read guide:   ${CYAN}cat SLACK_CONNECTION_GUIDE.md${RESET}"
    echo
    
    exit 1
fi

