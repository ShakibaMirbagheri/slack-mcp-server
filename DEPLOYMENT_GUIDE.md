# 🚀 Production Deployment Guide

Complete guide for deploying Slack MCP Server to production environments.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Setup](#pre-deployment-setup)
3. [Configuration](#configuration)
4. [Build Process](#build-process)
5. [Deployment Options](#deployment-options)
6. [Post-Deployment](#post-deployment)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)
9. [CI/CD Pipeline](#cicd-pipeline)

---

## 📦 Prerequisites

### Required Tools:
- Docker (20.10+)
- Docker Compose (2.0+)
- Git
- Make

### Optional (for Kubernetes):
- kubectl
- Helm (optional)

### Optional (for CI/CD):
- GitHub Actions
- GitLab CI
- Jenkins

---

## 🔧 Pre-Deployment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/slack-mcp-server.git
cd slack-mcp-server
```

### 2. Create Production Environment File

```bash
# Copy template
cp env.production.template .env.production

# Edit configuration
nano .env.production
```

**Required Configuration:**

```bash
# CRITICAL: Fill these in!
SLACK_MCP_XOXP_TOKEN=xoxp-your-actual-token
SLACK_MCP_API_KEY=$(openssl rand -hex 32)  # Generate secure key
SLACK_MCP_ALLOWED_ORIGINS=https://your-domain.com
```

### 3. Security Checklist

- [ ] Set strong `SLACK_MCP_API_KEY`
- [ ] Configure `SLACK_MCP_ALLOWED_ORIGINS`
- [ ] Review `SLACK_MCP_ADD_MESSAGE_TOOL` settings
- [ ] Enable HTTPS only (`SLACK_MCP_HTTPS_ONLY=true`)
- [ ] Never commit `.env.production` to git
- [ ] Set up firewall rules
- [ ] Configure SSL/TLS certificates

---

## 🏗️ Build Process

### Automated Build

```bash
# Run build script
chmod +x scripts/build.sh
./scripts/build.sh
```

This will:
- Clean previous builds
- Build Go binaries for all platforms
- Build Docker image
- Run tests
- Run security scan
- Tag image with version

### Manual Build

```bash
# Build Go binary
make build

# Build Docker image
docker build -t slack-mcp-server:latest .

# Run tests
make test
```

### Build for Multiple Platforms

```bash
# Build for multiple architectures
PLATFORMS=linux/amd64,linux/arm64 ./scripts/build.sh
```

---

## 🚀 Deployment Options

### Option 1: Docker Compose (Recommended for Single Server)

#### Quick Deploy

```bash
# Make deploy script executable
chmod +x scripts/deploy.sh

# Deploy to production
./scripts/deploy.sh production
```

#### Manual Deploy

```bash
# Pull latest image
docker-compose -f docker-compose.production.yml pull

# Start services
docker-compose -f docker-compose.production.yml up -d

# Check logs
docker-compose -f docker-compose.production.yml logs -f
```

#### Deploy Features:
- ✅ Automatic backups
- ✅ Health checks
- ✅ Rolling updates
- ✅ Volume persistence
- ✅ Resource limits
- ✅ Automatic restart

---

### Option 2: Kubernetes (Recommended for Multiple Servers)

#### Prerequisites

```bash
# Configure kubectl
kubectl config use-context your-cluster

# Create namespace
kubectl create namespace slack-mcp
```

#### Deploy

```bash
# Update secrets in kubernetes-deployment.yaml
# Then apply:
kubectl apply -f kubernetes-deployment.yaml

# Check deployment
kubectl get pods -n slack-mcp
kubectl get svc -n slack-mcp
```

#### Features:
- ✅ Auto-scaling (HPA)
- ✅ High availability (2+ replicas)
- ✅ Rolling updates
- ✅ Health checks
- ✅ Resource management
- ✅ Network policies
- ✅ Pod disruption budgets

#### Scale Deployment

```bash
# Scale manually
kubectl scale deployment slack-mcp-server --replicas=5 -n slack-mcp

# Auto-scaling is configured (2-10 replicas)
```

---

### Option 3: Manual Docker Run

```bash
docker run -d \
  --name slack-mcp-production \
  --restart unless-stopped \
  -p 3001:3001 \
  -v slack_cache:/data/cache \
  -v slack_logs:/var/log/slack-mcp-server \
  --env-file .env.production \
  slack-mcp-server:latest
```

---

## ✅ Post-Deployment

### 1. Health Check

```bash
# Run health check script
chmod +x scripts/health-check.sh
./scripts/health-check.sh
```

Or manually:

```bash
# Check service
curl http://localhost:3001/health

# Check SSE endpoint
curl http://localhost:3001/sse
```

### 2. Verify Deployment

**Docker Compose:**

```bash
docker-compose -f docker-compose.production.yml ps
docker-compose -f docker-compose.production.yml logs --tail=50
```

**Kubernetes:**

```bash
kubectl get pods -n slack-mcp
kubectl logs -f deployment/slack-mcp-server -n slack-mcp
kubectl describe deployment slack-mcp-server -n slack-mcp
```

### 3. Test Integration

```bash
# Test with Python client
python3 simple_agent_example.py

# Or use curl
curl -X POST http://localhost:3001/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

---

## 📊 Monitoring & Maintenance

### Log Management

**Docker Compose:**

```bash
# View logs
docker-compose -f docker-compose.production.yml logs -f

# View specific service
docker-compose -f docker-compose.production.yml logs -f slack-mcp-server

# Export logs
docker-compose -f docker-compose.production.yml logs > logs.txt
```

**Kubernetes:**

```bash
# View logs
kubectl logs -f deployment/slack-mcp-server -n slack-mcp

# View logs from all pods
kubectl logs -f -l app=slack-mcp-server -n slack-mcp

# Export logs
kubectl logs deployment/slack-mcp-server -n slack-mcp > logs.txt
```

### Backups

**Automated:**

```bash
# Run backup script
chmod +x scripts/backup.sh
./scripts/backup.sh
```

**Schedule with Cron:**

```bash
# Add to crontab
0 2 * * * /path/to/scripts/backup.sh
```

**Manual Backup:**

```bash
# Backup volumes
docker run --rm \
  -v slack_cache:/source:ro \
  -v /backups:/backup \
  alpine tar czf /backup/cache-$(date +%Y%m%d).tar.gz -C /source .

# Backup configuration
tar czf backup-config-$(date +%Y%m%d).tar.gz .env.production *.yml
```

### Updates

**Docker Compose:**

```bash
# Pull latest image
docker-compose -f docker-compose.production.yml pull

# Recreate containers
docker-compose -f docker-compose.production.yml up -d
```

**Kubernetes:**

```bash
# Update image
kubectl set image deployment/slack-mcp-server \
  slack-mcp-server=slack-mcp-server:new-version \
  -n slack-mcp

# Check rollout
kubectl rollout status deployment/slack-mcp-server -n slack-mcp
```

### Rollback

**Using Deploy Script:**

```bash
./scripts/deploy.sh production --rollback
```

**Docker Compose:**

```bash
# Restore from backup
tar -xzf backup-config-20231201.tar.gz
docker-compose -f docker-compose.production.yml up -d
```

**Kubernetes:**

```bash
# Rollback deployment
kubectl rollout undo deployment/slack-mcp-server -n slack-mcp

# Check status
kubectl rollout status deployment/slack-mcp-server -n slack-mcp
```

---

## 🐛 Troubleshooting

### Service Not Starting

**Check logs:**

```bash
# Docker Compose
docker-compose -f docker-compose.production.yml logs

# Kubernetes
kubectl logs deployment/slack-mcp-server -n slack-mcp
```

**Common issues:**

1. **Missing environment variables**
   ```bash
   # Verify .env.production exists and is correct
   cat .env.production | grep SLACK_MCP_XOXP_TOKEN
   ```

2. **Port already in use**
   ```bash
   # Check what's using port 3001
   lsof -i :3001
   # Or change port in .env.production
   ```

3. **Invalid Slack token**
   ```bash
   # Test token manually
   curl -H "Authorization: Bearer SLACK_MCP_XOXP_TOKEN" \
     https://slack.com/api/auth.test
   ```

### Health Check Failing

```bash
# Run detailed health check
./scripts/health-check.sh

# Check if service is listening
netstat -tlnp | grep 3001

# Test endpoints
curl -v http://localhost:3001/health
curl -v http://localhost:3001/sse
```

### Performance Issues

**Check resource usage:**

```bash
# Docker
docker stats slack-mcp-production

# Kubernetes
kubectl top pods -n slack-mcp
```

**Increase resources:**

Edit `docker-compose.production.yml` or `kubernetes-deployment.yaml`:

```yaml
resources:
  limits:
    memory: "1Gi"
    cpu: "2000m"
```

### Connection Issues

**Check network:**

```bash
# Docker network
docker network inspect slack-mcp-production

# Kubernetes network
kubectl get netpol -n slack-mcp
```

**Check firewall:**

```bash
# Allow port 3001
sudo ufw allow 3001/tcp

# Or iptables
sudo iptables -A INPUT -p tcp --dport 3001 -j ACCEPT
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

Pipeline file: `.github/workflows/production-deploy.yml`

**Features:**
- ✅ Automated builds on push
- ✅ Run tests
- ✅ Security scanning
- ✅ Automatic deployment
- ✅ Health checks
- ✅ Notifications

**Setup:**

1. **Add secrets to GitHub:**
   - `SLACK_MCP_XOXP_TOKEN`
   - `SLACK_MCP_API_KEY`
   - `KUBE_CONFIG` (for Kubernetes)
   - `SLACK_WEBHOOK` (for notifications)

2. **Configure deployment:**
   ```yaml
   # Edit .github/workflows/production-deploy.yml
   # Update domain and environment variables
   ```

3. **Trigger deployment:**
   ```bash
   # Push to main branch
   git push origin main
   
   # Or create a tag
   git tag v1.0.0
   git push origin v1.0.0
   ```

### Manual Trigger

```bash
# Trigger via GitHub CLI
gh workflow run production-deploy.yml

# Or via API
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/YOUR_ORG/slack-mcp-server/actions/workflows/production-deploy.yml/dispatches \
  -d '{"ref":"main"}'
```

---

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] Review `.env.production` configuration
- [ ] Generate secure `SLACK_MCP_API_KEY`
- [ ] Configure Slack app with required scopes
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Test in staging environment
- [ ] Document custom configurations
- [ ] Review security settings

### Deployment

- [ ] Run build script
- [ ] Run tests
- [ ] Create backup of current deployment
- [ ] Deploy using chosen method
- [ ] Run health checks
- [ ] Verify all services are running
- [ ] Test integration
- [ ] Monitor logs for errors
- [ ] Update documentation
- [ ] Notify team

### Post-Deployment

- [ ] Monitor service for 24 hours
- [ ] Check error rates
- [ ] Verify backups are running
- [ ] Test failover procedures
- [ ] Update runbooks
- [ ] Schedule post-deployment review

---

## 🔒 Security Best Practices

1. **Never expose secrets**
   - Use `.env` files (never commit)
   - Use secrets management (Vault, K8s secrets)
   - Rotate credentials regularly

2. **Network security**
   - Use HTTPS only
   - Configure CORS properly
   - Set up firewall rules
   - Use network policies (K8s)

3. **Access control**
   - Require API key authentication
   - Limit message posting capabilities
   - Use least privilege principle
   - Enable audit logging

4. **Regular maintenance**
   - Update dependencies
   - Apply security patches
   - Rotate credentials
   - Review access logs
   - Test backups

---

## 📞 Support

**Common Commands:**

```bash
# View service status
./scripts/health-check.sh

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Create backup
./scripts/backup.sh

# Deploy
./scripts/deploy.sh production

# Rollback
./scripts/deploy.sh production --rollback
```

**Documentation:**

- `README.md` - Project overview
- `MCP_LLM_INTEGRATION_GUIDE.md` - LLM integration
- `FINAL_SUMMARY.md` - Complete summary
- `INDEX.md` - File index

---

## ✨ Summary

Your production deployment includes:

✅ **Automated build process**  
✅ **Multiple deployment options** (Docker Compose, Kubernetes, Manual)  
✅ **Health checks and monitoring**  
✅ **Automated backups**  
✅ **CI/CD pipeline** (GitHub Actions)  
✅ **Rollback procedures**  
✅ **Security best practices**  
✅ **Complete documentation**  

**Quick Deploy:**

```bash
# 1. Configure
cp env.production.template .env.production
nano .env.production  # Add your Slack token

# 2. Deploy
chmod +x scripts/*.sh
./scripts/deploy.sh production

# 3. Verify
./scripts/health-check.sh
```

**That's it! Your Slack MCP Server is production-ready! 🎉**

---

*For questions or issues, refer to the troubleshooting section or check the logs.*

