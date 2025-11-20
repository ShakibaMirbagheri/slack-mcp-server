#!/bin/bash

# Script to push to a new GitHub repository
# Usage: ./push_to_new_repo.sh YOUR_NEW_REPO_URL

if [ -z "$1" ]; then
    echo "Usage: ./push_to_new_repo.sh YOUR_NEW_REPO_URL"
    echo "Example: ./push_to_new_repo.sh https://github.com/username/slack-mcp-server.git"
    exit 1
fi

NEW_REPO_URL=$1

echo "Removing old remote..."
git remote remove origin 2>/dev/null || echo "No old remote to remove"

echo "Adding new remote: $NEW_REPO_URL"
git remote add origin "$NEW_REPO_URL"

echo "Staging all changes..."
git add .

echo "Committing changes..."
git commit -m "Initial commit: Production-ready Slack MCP Server with CI/CD, connection guide, and environment configuration"

echo "Pushing to new repository..."
git push -u origin master

echo "Done! Your repository is now at: $NEW_REPO_URL"
