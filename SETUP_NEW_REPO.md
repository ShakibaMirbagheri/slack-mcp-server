# Setup New GitHub Repository

Follow these steps to create and push to a new GitHub repository.

## Step 1: Create New Repository on GitHub

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the **"+"** icon in the top right → **"New repository"**
3. Fill in the details:
   - **Repository name**: `slack-mcp-server` (or your preferred name)
   - **Description**: "Production-ready Slack MCP Server"
   - **Visibility**: Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click **"Create repository"**

## Step 2: Copy Your New Repository URL

After creating the repository, GitHub will show you the repository URL. It will look like:
- `https://github.com/YOUR_USERNAME/slack-mcp-server.git` (HTTPS)
- `git@github.com:YOUR_USERNAME/slack-mcp-server.git` (SSH)

Copy this URL - you'll need it in the next step.

## Step 3: Run These Commands

Replace `YOUR_NEW_REPO_URL` with the URL from Step 2.

```bash
# Remove the old remote
git remote remove origin

# Add your new repository as remote
git remote add origin YOUR_NEW_REPO_URL

# Stage all changes
git add .

# Commit all changes
git commit -m "Initial commit: Production-ready Slack MCP Server with CI/CD, connection guide, and environment configuration"

# Push to the new repository
git push -u origin master
```

If your new repository uses `main` as the default branch:

```bash
# Push to main branch instead
git push -u origin master:main
```

Or rename your local branch to main first:

```bash
# Rename local branch to main
git branch -M main

# Push to main
git push -u origin main
```

## Quick Copy-Paste Commands

**For HTTPS:**
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/slack-mcp-server.git
git add .
git commit -m "Initial commit: Production-ready Slack MCP Server"
git push -u origin master
```

**For SSH:**
```bash
git remote remove origin
git remote add origin git@github.com:YOUR_USERNAME/slack-mcp-server.git
git add .
git commit -m "Initial commit: Production-ready Slack MCP Server"
git push -u origin master
```

## Troubleshooting

If you get authentication errors:
- For HTTPS: Use a Personal Access Token instead of password
- For SSH: Make sure your SSH key is added to GitHub

If the repository already has commits:
```bash
git pull origin master --allow-unrelated-histories
git push -u origin master
```

