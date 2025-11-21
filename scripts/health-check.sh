#!/bin/bash
# ============================================
# Health Check Script
# ============================================

set -euo pipefail

# Configuration
HOST="${SLACK_MCP_HOST:-localhost}"
PORT="${SLACK_MCP_PORT:-3001}"
TIMEOUT="${TIMEOUT:-10}"
MAX_RETRIES="${MAX_RETRIES:-3}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Check HTTP endpoint
check_http() {
    local url="$1"
    local name="$2"
    
    log_info "Checking ${name}..."
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time "$TIMEOUT" \
        "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        log_success "${name} is healthy (HTTP 200)"
        return 0
    else
        log_error "${name} check failed (HTTP ${response})"
        return 1
    fi
}

# Check service availability
check_service() {
    log_info "Checking service on ${HOST}:${PORT}..."
    
    if nc -z -w ${TIMEOUT} ${HOST} ${PORT} 2>/dev/null; then
        log_success "Service is listening on ${HOST}:${PORT}"
        return 0
    else
        log_error "Service is not responding on ${HOST}:${PORT}"
        return 1
    fi
}

# Check Docker container
check_docker() {
    log_info "Checking Docker container..."
    
    if docker ps --filter "name=slack-mcp" --filter "status=running" | grep -q slack-mcp; then
        local container_name=$(docker ps --filter "name=slack-mcp" --format "{{.Names}}" | head -1)
        log_success "Container is running: ${container_name}"
        
        # Check container health
        local health=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "none")
        if [ "$health" != "none" ]; then
            if [ "$health" = "healthy" ]; then
                log_success "Container health: ${health}"
            else
                log_error "Container health: ${health}"
                return 1
            fi
        fi
        return 0
    else
        log_error "No running container found"
        return 1
    fi
}

# Check Kubernetes pod
check_kubernetes() {
    if ! command -v kubectl >/dev/null 2>&1; then
        return 0  # Skip if kubectl not available
    fi
    
    log_info "Checking Kubernetes pods..."
    
    local pods=$(kubectl get pods -n slack-mcp -l app=slack-mcp-server \
        -o jsonpath='{.items[*].status.phase}' 2>/dev/null || echo "")
    
    if [ -n "$pods" ]; then
        if echo "$pods" | grep -q "Running"; then
            log_success "Kubernetes pods are running"
            return 0
        else
            log_error "Kubernetes pods status: ${pods}"
            return 1
        fi
    fi
    
    return 0  # Not running in Kubernetes
}

# Main health check
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                 Slack MCP Server - Health Check                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    
    local checks_passed=0
    local checks_total=0
    
    # Service check
    ((checks_total++))
    check_service && ((checks_passed++)) || true
    
    # HTTP health endpoint
    ((checks_total++))
    check_http "http://${HOST}:${PORT}/health" "Health endpoint" && ((checks_passed++)) || true
    
    # SSE endpoint
    ((checks_total++))
    check_http "http://${HOST}:${PORT}/sse" "SSE endpoint" && ((checks_passed++)) || true
    
    # Container check
    ((checks_total++))
    check_docker && ((checks_passed++)) || true
    
    # Kubernetes check (if applicable)
    ((checks_total++))
    check_kubernetes && ((checks_passed++)) || true
    
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                        Results Summary                           ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    
    echo "Checks passed: ${checks_passed}/${checks_total}"
    
    if [ $checks_passed -ge 3 ]; then
        echo -e "${GREEN}✓ Service is healthy${NC}"
        exit 0
    else
        echo -e "${RED}✗ Service has issues${NC}"
        exit 1
    fi
}

main "$@"

