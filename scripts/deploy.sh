#!/bin/bash
# ============================================
# Production Deployment Script
# ============================================
# 
# Usage:
#   ./scripts/deploy.sh [environment] [options]
#
# Examples:
#   ./scripts/deploy.sh production
#   ./scripts/deploy.sh staging --no-backup
#   ./scripts/deploy.sh production --rollback
#
# ============================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-production}"
BACKUP_ENABLED=true
ROLLBACK=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --no-backup)
            BACKUP_ENABLED=false
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
    esac
done

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    command -v docker >/dev/null 2>&1 || missing_tools+=("docker")
    command -v docker-compose >/dev/null 2>&1 || missing_tools+=("docker-compose")
    command -v kubectl >/dev/null 2>&1 || missing_tools+=("kubectl")
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Load environment configuration
load_environment() {
    log_info "Loading ${ENVIRONMENT} environment configuration..."
    
    local env_file="${PROJECT_ROOT}/.env.${ENVIRONMENT}"
    
    if [ ! -f "$env_file" ]; then
        log_error "Environment file not found: $env_file"
        log_info "Copy env.production.template to .env.${ENVIRONMENT} and configure it"
        exit 1
    fi
    
    # Export environment variables
    set -a
    source "$env_file"
    set +a
    
    log_success "Environment loaded: ${ENVIRONMENT}"
}

# Create backup
create_backup() {
    if [ "$BACKUP_ENABLED" = false ]; then
        log_warning "Backup disabled, skipping..."
        return 0
    fi
    
    log_info "Creating backup..."
    
    local backup_dir="${PROJECT_ROOT}/backups"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${backup_dir}/backup_${ENVIRONMENT}_${timestamp}.tar.gz"
    
    mkdir -p "$backup_dir"
    
    # Backup volumes and configuration
    tar -czf "$backup_file" \
        -C "$PROJECT_ROOT" \
        .env.${ENVIRONMENT} \
        docker-compose.${ENVIRONMENT}.yml \
        2>/dev/null || true
    
    log_success "Backup created: $backup_file"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    local image_tag="slack-mcp-server:${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"
    
    docker build \
        --tag "$image_tag" \
        --build-arg VERSION="${VERSION:-latest}" \
        --build-arg ENVIRONMENT="$ENVIRONMENT" \
        "$PROJECT_ROOT"
    
    log_success "Image built: $image_tag"
    echo "$image_tag" > "${PROJECT_ROOT}/.last_image"
}

# Deploy with Docker Compose
deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."
    
    cd "$PROJECT_ROOT"
    
    # Pull latest image
    docker-compose -f docker-compose.production.yml pull
    
    # Stop existing containers
    docker-compose -f docker-compose.production.yml down
    
    # Start new containers
    docker-compose -f docker-compose.production.yml up -d
    
    log_success "Deployment complete"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    # Apply configuration
    kubectl apply -f "${PROJECT_ROOT}/kubernetes-deployment.yaml"
    
    # Update deployment
    if [ -f "${PROJECT_ROOT}/.last_image" ]; then
        local image=$(cat "${PROJECT_ROOT}/.last_image")
        kubectl set image deployment/slack-mcp-server \
            slack-mcp-server="$image" \
            -n slack-mcp
    fi
    
    # Wait for rollout
    kubectl rollout status deployment/slack-mcp-server -n slack-mcp --timeout=300s
    
    log_success "Kubernetes deployment complete"
}

# Health check
health_check() {
    log_info "Running health check..."
    
    local max_attempts=30
    local attempt=1
    local endpoint="${SLACK_MCP_HOST:-localhost}:${SLACK_MCP_PORT:-3001}/health"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://${endpoint}" >/dev/null 2>&1; then
            log_success "Health check passed!"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts - waiting for service..."
        sleep 5
        ((attempt++))
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Rollback
rollback() {
    log_warning "Rolling back deployment..."
    
    if command -v kubectl >/dev/null 2>&1; then
        kubectl rollout undo deployment/slack-mcp-server -n slack-mcp
        kubectl rollout status deployment/slack-mcp-server -n slack-mcp
    else
        # Docker Compose rollback
        local backup_dir="${PROJECT_ROOT}/backups"
        local latest_backup=$(ls -t "${backup_dir}"/backup_${ENVIRONMENT}_*.tar.gz 2>/dev/null | head -1)
        
        if [ -n "$latest_backup" ]; then
            log_info "Restoring from: $latest_backup"
            tar -xzf "$latest_backup" -C "$PROJECT_ROOT"
            deploy_docker_compose
        else
            log_error "No backup found for rollback"
            exit 1
        fi
    fi
    
    log_success "Rollback complete"
}

# Cleanup old backups
cleanup_backups() {
    log_info "Cleaning up old backups..."
    
    local backup_dir="${PROJECT_ROOT}/backups"
    local retention_days="${BACKUP_RETENTION_DAYS:-30}"
    
    find "$backup_dir" -name "backup_${ENVIRONMENT}_*.tar.gz" \
        -type f -mtime +${retention_days} -delete
    
    log_success "Old backups cleaned up (retention: ${retention_days} days)"
}

# Main deployment flow
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║            Slack MCP Server - Production Deployment             ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Timestamp: $(date)"
    echo ""
    
    if [ "$ROLLBACK" = true ]; then
        rollback
        exit 0
    fi
    
    # Deployment steps
    check_prerequisites
    load_environment
    create_backup
    
    # Choose deployment method
    if command -v kubectl >/dev/null 2>&1 && kubectl cluster-info >/dev/null 2>&1; then
        log_info "Kubernetes cluster detected, using Kubernetes deployment"
        build_image
        deploy_kubernetes
    else
        log_info "Using Docker Compose deployment"
        deploy_docker_compose
    fi
    
    # Post-deployment
    health_check || {
        log_error "Deployment failed health check"
        log_warning "Consider rolling back: ./scripts/deploy.sh ${ENVIRONMENT} --rollback"
        exit 1
    }
    
    cleanup_backups
    
    echo ""
    log_success "╔══════════════════════════════════════════════════════════════════╗"
    log_success "║                  Deployment Successful! 🎉                       ║"
    log_success "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    log_info "Service URL: http://${SLACK_MCP_HOST:-localhost}:${SLACK_MCP_PORT:-3001}"
    log_info "Health check: http://${SLACK_MCP_HOST:-localhost}:${SLACK_MCP_PORT:-3001}/health"
    echo ""
    log_info "View logs: docker-compose -f docker-compose.production.yml logs -f"
    log_info "Or: kubectl logs -f deployment/slack-mcp-server -n slack-mcp"
    echo ""
}

# Run main function
main "$@"



