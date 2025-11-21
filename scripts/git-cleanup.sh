#!/bin/bash
# ============================================
# Git Repository Cleanup Script
# ============================================
# Removes unnecessary files and prepares repo for deployment

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║              Git Repository Cleanup                              ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Remove files that shouldn't be tracked
log_info "Removing tracked files that should be ignored..."

# Remove environment files from tracking
git rm --cached .env 2>/dev/null || true
git rm --cached .env.* 2>/dev/null || true
git rm --cached env.production 2>/dev/null || true

# Remove cache files
git rm --cached .users_cache.json 2>/dev/null || true
git rm --cached .channels_cache*.json 2>/dev/null || true
git rm --cached users_cache.json 2>/dev/null || true
git rm --cached channels_cache*.json 2>/dev/null || true

# Remove log files
git rm --cached *.log 2>/dev/null || true
git rm -r --cached logs/ 2>/dev/null || true

# Remove backup files
git rm -r --cached backups/ 2>/dev/null || true
git rm --cached *.backup 2>/dev/null || true
git rm --cached *.tar.gz 2>/dev/null || true

# Remove build artifacts
git rm -r --cached build/ 2>/dev/null || true
git rm --cached *.test 2>/dev/null || true

# Remove temp files
git rm -r --cached tmp/ 2>/dev/null || true
git rm -r --cached temp/ 2>/dev/null || true

# Remove unnecessary test files (keep the essential ones)
git rm --cached test_mcp_server.py 2>/dev/null || true
git rm --cached test_mcp_simple.py 2>/dev/null || true

log_success "Unnecessary files removed from tracking"

# Add deployment files
log_info "Adding deployment-ready files..."

# Configuration templates
git add -f .gitignore
git add -f env.production.template
git add -f docker-compose.production.yml
git add -f kubernetes-deployment.yaml

# Deployment scripts
git add -f scripts/deploy.sh
git add -f scripts/build.sh
git add -f scripts/health-check.sh
git add -f scripts/backup.sh

# CI/CD
git add -f .github/workflows/production-deploy.yml

# Makefiles
git add -f Makefile
git add -f Makefile.production

# Documentation
git add -f DEPLOYMENT_GUIDE.md
git add -f PRODUCTION_DEPLOYMENT_SUMMARY.md
git add -f MCP_LLM_INTEGRATION_GUIDE.md
git add -f FINAL_SUMMARY.md
git add -f INDEX.md
git add -f README.md

# Integration code
git add -f simple_agent_example.py
git add -f mcp_llm_integration.py
git add -f mcp_llm_integration_stdio.py

# Requirements
git add -f requirements.txt

# Essential test scripts
git add -f test_simple.sh
git add -f test_server_working.py
git add -f test_mcp_http.py

log_success "Deployment files added"

# Show status
echo ""
log_info "Current git status:"
git status --short

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    Cleanup Summary                                ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

log_success "✓ Removed cached unnecessary files"
log_success "✓ Added deployment-ready files"
log_success "✓ Repository is clean and ready for deployment"

echo ""
log_info "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Commit changes: git commit -m 'Production deployment ready'"
echo "  3. Push to remote: git push origin main"
echo ""
log_warning "Files to NEVER commit:"
echo "  • .env or .env.production (contains secrets!)"
echo "  • Cache files (.users_cache.json, etc.)"
echo "  • Log files (*.log)"
echo "  • Backup files (*.tar.gz, backups/)"
echo ""

