#!/bin/bash
# ============================================
# Build Script for Slack MCP Server
# ============================================

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
VERSION="${VERSION:-$(git describe --tags --always --dirty 2>/dev/null || echo 'dev')}"
COMMIT_SHA="${COMMIT_SHA:-$(git rev-parse HEAD 2>/dev/null || echo 'unknown')}"
BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
REGISTRY="${REGISTRY:-ghcr.io}"
IMAGE_NAME="${IMAGE_NAME:-slack-mcp-server}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║              Slack MCP Server - Build Process                    ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

log_info "Version: ${VERSION}"
log_info "Commit: ${COMMIT_SHA}"
log_info "Build Date: ${BUILD_DATE}"
log_info "Platforms: ${PLATFORMS}"
echo ""

# Clean previous builds
log_info "Cleaning previous builds..."
rm -rf build/
mkdir -p build/

# Build Go binary
log_info "Building Go binaries..."
make build-all-platforms

log_success "Binaries built successfully"

# Build Docker image
log_info "Building Docker image..."

docker buildx build \
    --platform="${PLATFORMS}" \
    --build-arg VERSION="${VERSION}" \
    --build-arg COMMIT_SHA="${COMMIT_SHA}" \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --tag "${REGISTRY}/${IMAGE_NAME}:${VERSION}" \
    --tag "${REGISTRY}/${IMAGE_NAME}:latest" \
    --load \
    .

log_success "Docker image built: ${REGISTRY}/${IMAGE_NAME}:${VERSION}"

# Run tests
log_info "Running tests..."
make test || {
    log_error "Tests failed!"
    exit 1
}

log_success "All tests passed"

# Security scan
log_info "Running security scan..."
if command -v trivy >/dev/null 2>&1; then
    trivy image --severity HIGH,CRITICAL "${REGISTRY}/${IMAGE_NAME}:${VERSION}"
else
    log_info "Trivy not installed, skipping security scan"
fi

echo ""
log_success "╔══════════════════════════════════════════════════════════════════╗"
log_success "║                    Build Complete! 🎉                            ║"
log_success "╚══════════════════════════════════════════════════════════════════╝"
echo ""
log_info "Image: ${REGISTRY}/${IMAGE_NAME}:${VERSION}"
log_info "Size: $(docker images ${REGISTRY}/${IMAGE_NAME}:${VERSION} --format '{{.Size}}')"
echo ""
log_info "Push to registry: docker push ${REGISTRY}/${IMAGE_NAME}:${VERSION}"
log_info "Run locally: docker run -p 3001:3001 ${REGISTRY}/${IMAGE_NAME}:${VERSION}"
echo ""



