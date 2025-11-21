#!/bin/bash
# ============================================
# Backup Script
# ============================================

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/data/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="slack-mcp-backup-${TIMESTAMP}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                     Creating Backup                               ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

log_info "Backup name: ${BACKUP_NAME}"
log_info "Backup directory: ${BACKUP_DIR}"

# Backup Docker volumes
if docker volume ls | grep -q slack; then
    log_info "Backing up Docker volumes..."
    
    for volume in $(docker volume ls --format '{{.Name}}' | grep slack); do
        log_info "Backing up volume: ${volume}"
        docker run --rm \
            -v ${volume}:/source:ro \
            -v ${BACKUP_DIR}:/backup \
            alpine \
            tar czf /backup/${BACKUP_NAME}-${volume}.tar.gz -C /source .
    done
    
    log_success "Docker volumes backed up"
fi

# Backup configuration files
log_info "Backing up configuration..."
tar czf "${BACKUP_DIR}/${BACKUP_NAME}-config.tar.gz" \
    .env.production \
    docker-compose.production.yml \
    kubernetes-deployment.yaml \
    2>/dev/null || true

log_success "Configuration backed up"

# Backup Kubernetes resources (if applicable)
if command -v kubectl >/dev/null 2>&1; then
    log_info "Backing up Kubernetes resources..."
    kubectl get all -n slack-mcp -o yaml > "${BACKUP_DIR}/${BACKUP_NAME}-k8s.yaml" 2>/dev/null || true
    log_success "Kubernetes resources backed up"
fi

# Create backup manifest
cat > "${BACKUP_DIR}/${BACKUP_NAME}-manifest.txt" <<EOF
Backup: ${BACKUP_NAME}
Date: $(date)
Hostname: $(hostname)
Version: $(git describe --tags --always 2>/dev/null || echo 'unknown')
EOF

log_success "Backup manifest created"

# Cleanup old backups
log_info "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "slack-mcp-backup-*" -type f -mtime +${RETENTION_DAYS} -delete

# Create latest symlink
ln -sf "${BACKUP_DIR}/${BACKUP_NAME}-config.tar.gz" "${BACKUP_DIR}/latest-backup.tar.gz"

echo ""
log_success "╔══════════════════════════════════════════════════════════════════╗"
log_success "║                  Backup Complete! 🎉                             ║"
log_success "╚══════════════════════════════════════════════════════════════════╝"
echo ""
log_info "Backup location: ${BACKUP_DIR}"
log_info "Backup files:"
ls -lh "${BACKUP_DIR}/${BACKUP_NAME}"* 2>/dev/null || true
echo ""

