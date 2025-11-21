# 📁 Git Repository Guide

## ✅ What's Tracked in Git

This guide shows what files are tracked in the repository and what's excluded.

---

## 📦 Files Tracked (Safe to Commit)

### Core Application Code
```
✅ cmd/                          - Go application code
✅ pkg/                          - Go packages
✅ go.mod, go.sum               - Go dependencies
✅ Dockerfile                   - Docker build configuration
✅ Makefile                     - Build automation
```

### Production Deployment
```
✅ env.production.template      - Environment template (NO SECRETS!)
✅ docker-compose.production.yml - Production Docker setup
✅ kubernetes-deployment.yaml   - Kubernetes deployment
✅ Makefile.production          - Production make targets
```

### Deployment Scripts
```
✅ scripts/deploy.sh            - Deployment automation
✅ scripts/build.sh             - Build automation
✅ scripts/health-check.sh      - Health monitoring
✅ scripts/backup.sh            - Backup automation
✅ scripts/git-cleanup.sh       - Git cleanup
```

### CI/CD
```
✅ .github/workflows/production-deploy.yml - GitHub Actions pipeline
```

### Integration & Testing
```
✅ simple_agent_example.py      - Main agent class
✅ mcp_llm_integration.py       - HTTP/SSE integration
✅ mcp_llm_integration_stdio.py - STDIO integration
✅ test_simple.sh               - Quick test script
✅ test_server_working.py       - Comprehensive test
✅ test_mcp_http.py             - HTTP testing
✅ requirements.txt             - Python dependencies
```

### Documentation
```
✅ README.md                    - Project overview
✅ DEPLOYMENT_GUIDE.md          - Deployment instructions
✅ PRODUCTION_DEPLOYMENT_SUMMARY.md - Deployment summary
✅ MCP_LLM_INTEGRATION_GUIDE.md - LLM integration guide
✅ FINAL_SUMMARY.md             - Complete summary
✅ INDEX.md                     - File index
✅ GIT_REPOSITORY_GUIDE.md      - This file
✅ SLACK_CONNECTION_GUIDE.md    - Slack setup
✅ SECURITY.md                  - Security policies
✅ LICENSE                      - License file
```

### Configuration
```
✅ .gitignore                   - Git ignore rules
✅ .dockerignore                - Docker ignore rules
```

---

## ❌ Files NOT Tracked (Excluded by .gitignore)

### 🔒 CRITICAL: Never Commit These!

```
❌ .env                         - Contains SECRETS!
❌ .env.production              - Contains production SECRETS!
❌ .env.staging                 - Contains staging SECRETS!
❌ .env.*                       - All environment files
❌ *.pem, *.key, *.crt          - SSL/TLS certificates
❌ secrets/                     - Any secrets directory
❌ credentials/                 - Credentials
```

### Build Artifacts
```
❌ build/                       - Build output
❌ dist/                        - Distribution files
❌ *.exe, *.dll, *.so           - Compiled binaries
❌ vendor/                      - Go vendor directory
```

### Cache Files
```
❌ .users_cache.json            - Slack users cache
❌ .channels_cache*.json        - Slack channels cache
❌ *.cache                      - Any cache files
```

### Logs
```
❌ *.log                        - Log files
❌ logs/                        - Log directory
❌ npm-debug.log                - npm logs
```

### Backups
```
❌ backups/                     - Backup directory
❌ *.backup, *.bak              - Backup files
❌ *.tar.gz, *.zip              - Archive files
```

### Temporary Files
```
❌ tmp/, temp/                  - Temporary directories
❌ *.tmp, *.swp                 - Temp/swap files
❌ .DS_Store                    - macOS files
❌ Thumbs.db                    - Windows files
```

### IDE/Editor
```
❌ .vscode/                     - VS Code settings
❌ .idea/                       - IntelliJ settings
❌ *.sublime-*                  - Sublime Text
```

### Python
```
❌ __pycache__/                 - Python cache
❌ *.pyc, *.pyo                 - Python compiled
❌ venv/, env/                  - Virtual environments
❌ .pytest_cache/               - Pytest cache
```

### Node.js (if used)
```
❌ node_modules/                - npm packages
❌ package-lock.json            - npm lock file
```

---

## 🔄 Git Workflow

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/your-org/slack-mcp-server.git
cd slack-mcp-server

# 2. Create your environment file (NOT tracked!)
cp env.production.template .env.production
nano .env.production  # Add your secrets

# 3. The .env.production file is automatically ignored by .gitignore
# It will NEVER be committed
```

### Making Changes

```bash
# 1. Create feature branch
git checkout -b feature/your-feature

# 2. Make your changes
# Edit files...

# 3. Check what will be committed
git status

# 4. Add files
git add <files>

# 5. Commit (secrets are automatically excluded!)
git commit -m "Add your feature"

# 6. Push
git push origin feature/your-feature
```

### Deploying

```bash
# 1. Merge to main
git checkout main
git merge feature/your-feature

# 2. Tag release
git tag -a v1.0.0 -m "Release v1.0.0"

# 3. Push
git push origin main --tags

# 4. CI/CD pipeline automatically deploys
# Or deploy manually:
./scripts/deploy.sh production
```

---

## 🧹 Cleaning Repository

If you accidentally committed secrets or unnecessary files:

### Quick Cleanup

```bash
# Run cleanup script
./scripts/git-cleanup.sh

# Review changes
git status

# Commit cleanup
git commit -m "Clean up repository"
```

### Manual Cleanup

```bash
# Remove file from tracking (keeps local file)
git rm --cached .env

# Remove directory from tracking
git rm -r --cached backups/

# Commit removal
git commit -m "Remove unnecessary files from tracking"
```

### Remove from History (if secrets were committed!)

```bash
# ⚠️ WARNING: This rewrites history!
# Use only if you committed secrets

# Remove file from all history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env.production" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (⚠️ dangerous!)
git push origin --force --all
```

---

## 📋 Pre-Commit Checklist

Before every commit, verify:

- [ ] No `.env` or `.env.*` files are staged
- [ ] No `*.log` files are staged
- [ ] No cache files are staged
- [ ] No backup files are staged
- [ ] No secrets or credentials are staged
- [ ] Run: `git status` to review
- [ ] Run: `git diff --cached` to see changes
- [ ] Only necessary files are being committed

---

## 🔐 Security Checklist

- [ ] `.gitignore` excludes all secret files
- [ ] Environment files use `.template` extension (no secrets)
- [ ] No API keys, tokens, or passwords in code
- [ ] No database credentials in repository
- [ ] No SSL certificates in repository
- [ ] Secrets are managed via environment variables
- [ ] CI/CD uses secrets management (GitHub Secrets, etc.)

---

## 📊 Repository Structure

```
slack-mcp-server/
├── 📁 Core Application
│   ├── cmd/                    ✅ Tracked
│   ├── pkg/                    ✅ Tracked
│   ├── go.mod, go.sum          ✅ Tracked
│   └── Dockerfile              ✅ Tracked
│
├── 📁 Deployment
│   ├── env.production.template ✅ Tracked (template only!)
│   ├── docker-compose.production.yml ✅ Tracked
│   ├── kubernetes-deployment.yaml    ✅ Tracked
│   ├── Makefile.production     ✅ Tracked
│   └── .env.production         ❌ NOT tracked (secrets!)
│
├── 📁 Scripts
│   ├── deploy.sh               ✅ Tracked
│   ├── build.sh                ✅ Tracked
│   ├── health-check.sh         ✅ Tracked
│   ├── backup.sh               ✅ Tracked
│   └── git-cleanup.sh          ✅ Tracked
│
├── 📁 Integration
│   ├── simple_agent_example.py ✅ Tracked
│   ├── mcp_llm_integration.py  ✅ Tracked
│   ├── requirements.txt        ✅ Tracked
│   └── test_simple.sh          ✅ Tracked
│
├── 📁 Documentation
│   ├── README.md               ✅ Tracked
│   ├── DEPLOYMENT_GUIDE.md     ✅ Tracked
│   ├── MCP_LLM_INTEGRATION_GUIDE.md ✅ Tracked
│   └── *.md                    ✅ Tracked
│
├── 📁 CI/CD
│   └── .github/workflows/      ✅ Tracked
│
└── 📁 Excluded (NOT in git)
    ├── .env, .env.*            ❌ Secrets
    ├── logs/                   ❌ Logs
    ├── backups/                ❌ Backups
    ├── build/                  ❌ Build artifacts
    └── *_cache.json            ❌ Cache files
```

---

## 🎯 Common Scenarios

### Scenario 1: Accidentally Staged .env File

```bash
# Remove from staging
git reset .env

# Verify it's excluded
cat .gitignore | grep "^.env$"
# Should show: .env
```

### Scenario 2: Need to Share Configuration

```bash
# DON'T commit .env.production!
# Instead, update the template:
cp .env.production env.production.template

# Remove any secrets from template
nano env.production.template
# Replace actual values with placeholders

# Commit template
git add env.production.template
git commit -m "Update configuration template"
```

### Scenario 3: Fresh Clone Setup

```bash
# After cloning
git clone <repo>
cd slack-mcp-server

# Create environment file
cp env.production.template .env.production

# Add your secrets
nano .env.production

# The file is automatically ignored!
git status  # .env.production not shown
```

---

## ✅ Verification Commands

### Check What's Tracked

```bash
# List all tracked files
git ls-files

# Check if specific file is tracked
git ls-files | grep ".env"
# Should return nothing!
```

### Check .gitignore is Working

```bash
# Create test .env file
echo "SECRET=test" > .env

# Check git status
git status
# Should NOT show .env

# Verify ignore
git check-ignore -v .env
# Should show: .gitignore:7:.env    .env
```

### Verify No Secrets in History

```bash
# Search for potential secrets in history
git log --all --full-history --source --oneline -- .env .env.production

# Should be empty or show only removals
```

---

## 📞 Quick Commands

```bash
# Clean repository
./scripts/git-cleanup.sh

# Check status
git status

# See what's ignored
git status --ignored

# Verify .gitignore
git check-ignore -v <filename>

# List tracked files
git ls-files

# Commit deployment ready
git add -A
git commit -m "Production deployment ready"
git push origin main
```

---

## ✨ Summary

**Your repository is configured to:**

✅ Track only necessary deployment files  
✅ Exclude all secrets and credentials  
✅ Exclude cache, logs, and temporary files  
✅ Exclude build artifacts  
✅ Keep environment templates (without secrets)  
✅ Include all deployment automation  
✅ Include complete documentation  

**NEVER commit:**
- `.env` or `.env.production` (contains secrets!)
- Cache files
- Log files
- Backup files
- Build artifacts
- IDE settings

**Safe to commit:**
- `env.production.template` (template only, no secrets!)
- All scripts and documentation
- Deployment configurations
- Application code

---

## 🚀 Ready for Deployment!

Your repository is clean and ready for:
- ✅ Production deployment
- ✅ CI/CD pipelines
- ✅ Team collaboration
- ✅ Open source (if applicable)

**No secrets or sensitive data will ever be committed!**

---

*For questions, run: `./scripts/git-cleanup.sh` or check `.gitignore`*

