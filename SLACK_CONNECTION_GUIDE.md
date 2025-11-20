# Slack Connection Guide

This guide will help you connect the Slack MCP Server to your existing Slack workspace.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Authentication Methods](#authentication-methods)
3. [Method 1: OAuth Token (Recommended)](#method-1-oauth-token-recommended)
4. [Method 2: Browser Session Tokens](#method-2-browser-session-tokens)
5. [Verifying Your Connection](#verifying-your-connection)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

- Access to a Slack workspace
- Admin permissions (for OAuth method) or browser access (for session tokens)
- The Slack MCP Server installed or running

## Authentication Methods

The Slack MCP Server supports two authentication methods:

1. **OAuth Token (XOXP)** - Recommended for production use
   - More secure
   - Doesn't require browser session extraction
   - Works with Slack apps

2. **Browser Session Tokens (XOXC/XOXD)** - Alternative method
   - Extracted from your browser
   - Requires active browser session
   - May expire when browser session expires

> **Note**: You only need **one** method. Choose the one that best fits your needs.

## Method 1: OAuth Token (Recommended)

This is the recommended method for production environments as it's more secure and doesn't require extracting tokens from your browser.

### Step 1: Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Enter an app name (e.g., "Slack MCP Server")
5. Select your workspace
6. Click **"Create App"**

### Step 2: Configure OAuth Scopes

1. In your app settings, go to **"OAuth & Permissions"** in the left sidebar
2. Scroll down to **"Scopes"** section
3. Under **"User Token Scopes"**, add the following scopes:

   **Required Scopes:**
   - `channels:history` - View messages in public channels
   - `channels:read` - View basic information about public channels
   - `groups:history` - View messages in private channels
   - `groups:read` - View basic information about private channels
   - `im:history` - View messages in direct messages
   - `im:read` - View basic information about direct messages
   - `mpim:history` - View messages in group direct messages
   - `mpim:read` - View basic information about group direct messages
   - `users:read` - View people in a workspace

   **Optional Scopes (if you want to post messages):**
   - `chat:write` - Send messages on a user's behalf
   - `im:write` - Start direct messages with people
   - `mpim:write` - Start group direct messages
   - `search:read` - Search a workspace's content

### Step 3: Install App to Workspace

1. Scroll to the top of the **"OAuth & Permissions"** page
2. Click **"Install to Workspace"**
3. Review the permissions and click **"Allow"**

### Step 4: Copy Your OAuth Token

1. After installation, you'll be redirected back to the **"OAuth & Permissions"** page
2. Under **"OAuth Tokens for Your Workspace"**, find **"User OAuth Token"**
3. Click **"Copy"** to copy the token (it starts with `xoxp-`)
4. Save this token securely

### Step 5: Configure the Server

Add the token to your `.env` file:

```bash
SLACK_MCP_XOXP_TOKEN=xoxp-your-token-here
```

Or set it as an environment variable:

```bash
export SLACK_MCP_XOXP_TOKEN=xoxp-your-token-here
```

### Quick Setup with App Manifest

Alternatively, you can create the app using a manifest with all permissions preconfigured:

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From an app manifest"**
4. Select your workspace
5. Paste the following manifest:

```json
{
    "display_information": {
        "name": "Slack MCP Server"
    },
    "oauth_config": {
        "scopes": {
            "user": [
                "channels:history",
                "channels:read",
                "groups:history",
                "groups:read",
                "im:history",
                "im:read",
                "im:write",
                "mpim:history",
                "mpim:read",
                "mpim:write",
                "users:read",
                "chat:write",
                "search:read"
            ]
        }
    },
    "settings": {
        "org_deploy_enabled": false,
        "socket_mode_enabled": false,
        "token_rotation_enabled": false
    }
}
```

6. Click **"Create"**
7. Install the app to your workspace
8. Copy the User OAuth Token as described in Step 4

## Method 2: Browser Session Tokens

This method extracts tokens from your active Slack browser session. Use this if you don't have permission to create Slack apps or prefer not to use OAuth.

### Step 1: Open Slack in Your Browser

1. Open your Slack workspace in a web browser (Chrome, Firefox, or Edge)
2. Make sure you're logged in

### Step 2: Extract XOXC Token

1. Open your browser's Developer Console:
   - **Chrome/Edge**: Press `F12` or `Ctrl+Shift+I` (Windows/Linux) / `Cmd+Option+I` (Mac)
   - **Firefox**: Press `F12` or `Ctrl+Shift+I` (Windows/Linux) / `Cmd+Option+I` (Mac)
2. Switch to the **Console** tab
3. Type `allow pasting` and press Enter (this enables pasting in some browsers)
4. Paste the following code and press Enter:

```javascript
JSON.parse(localStorage.localConfig_v2).teams[document.location.pathname.match(/^\/client\/([A-Z0-9]+)/)[1]].token
```

5. The token (starting with `xoxc-`) will be displayed
6. Copy this token and save it securely

### Step 3: Extract XOXD Token

1. In the Developer Tools, switch to the **Application** tab (Chrome) or **Storage** tab (Firefox)
2. In the left sidebar, expand **Cookies**
3. Click on your Slack workspace URL (e.g., `https://yourworkspace.slack.com`)
4. Find the cookie named `d` (just the letter "d")
5. Double-click the **Value** column to select it
6. Copy the value (it starts with `xoxd-`)
7. Save this token securely

### Step 4: Configure the Server

Add both tokens to your `.env` file:

```bash
SLACK_MCP_XOXC_TOKEN=xoxc-your-token-here
SLACK_MCP_XOXD_TOKEN=xoxd-your-token-here
```

Or set them as environment variables:

```bash
export SLACK_MCP_XOXC_TOKEN=xoxc-your-token-here
export SLACK_MCP_XOXD_TOKEN=xoxd-your-token-here
```

> **Important**: These tokens are tied to your browser session and may expire when you log out or your session expires. You may need to re-extract them periodically.

## Verifying Your Connection

### Using Docker Compose

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your tokens

3. Start the server:
   ```bash
   docker-compose up
   ```

4. Check the logs for successful authentication:
   ```
   Successfully authenticated with Slack
   Slack MCP Server is fully ready
   ```

### Using Docker

```bash
docker run -i --rm \
  -e SLACK_MCP_XOXP_TOKEN=xoxp-your-token-here \
  ghcr.io/korotovsky/slack-mcp-server:latest \
  mcp-server --transport stdio
```

### Using Go Binary

```bash
export SLACK_MCP_XOXP_TOKEN=xoxp-your-token-here
go run cmd/slack-mcp-server/main.go --transport stdio
```

### Expected Output

When successfully connected, you should see logs like:

```
INFO    Authenticating with Slack API...
INFO    Successfully authenticated with Slack    {"team": "Your Workspace", "user": "your-username"}
INFO    Caching users collection...
INFO    Caching channels collection...
INFO    Slack MCP Server is fully ready
```

## Troubleshooting

### Authentication Failed

**Error**: `Failed to authenticate with Slack`

**Solutions**:
- Verify your token is correct and not expired
- For OAuth tokens: Ensure the app is installed in your workspace
- For browser tokens: Make sure you're still logged into Slack in your browser
- Check that you're using the correct token format (`xoxp-...`, `xoxc-...`, or `xoxd-...`)

### Token Expired

**Error**: `invalid_auth` or `token_expired`

**Solutions**:
- For OAuth tokens: Reinstall the app or regenerate the token
- For browser tokens: Re-extract tokens from your browser session

### Enterprise Slack Issues

If you're using Enterprise Slack and experiencing connection issues:

1. Set a custom User-Agent matching your browser:
   ```bash
   SLACK_MCP_USER_AGENT="Mozilla/5.0 (Your Browser User Agent)"
   ```

2. Enable custom TLS:
   ```bash
   SLACK_MCP_CUSTOM_TLS=true
   ```

3. Extract tokens from the same browser session where you set the User-Agent

### Rate Limiting

If you encounter rate limiting:

- The server includes automatic rate limit handling
- Wait a few minutes and try again
- Consider using cache files to reduce API calls:
  ```bash
  SLACK_MCP_USERS_CACHE=.users_cache.json
  SLACK_MCP_CHANNELS_CACHE=.channels_cache_v2.json
  ```

### Cache Issues

If channels or users aren't loading:

1. Delete cache files:
   ```bash
   rm .users_cache.json .channels_cache_v2.json
   ```

2. Restart the server to rebuild caches

### Still Having Issues?

1. Check the logs with debug level:
   ```bash
   SLACK_MCP_LOG_LEVEL=debug
   ```

2. Verify your environment variables are set correctly:
   ```bash
   env | grep SLACK_MCP
   ```

3. Review the [main documentation](README.md) for more details

4. Check the [authentication setup guide](docs/01-authentication-setup.md) for detailed instructions

## Security Best Practices

1. **Never commit tokens to version control**
   - Always use `.env` files (which should be in `.gitignore`)
   - Use environment variables in production

2. **Use OAuth tokens for production**
   - More secure than browser session tokens
   - Can be revoked independently
   - Don't expire with browser sessions

3. **Rotate tokens periodically**
   - Regenerate OAuth tokens if compromised
   - Re-extract browser tokens if you suspect unauthorized access

4. **Use API keys for SSE/HTTP transports**
   - Set `SLACK_MCP_API_KEY` when exposing the server over network
   - Never expose the server without authentication in production

5. **Restrict message posting**
   - Only enable `SLACK_MCP_ADD_MESSAGE_TOOL` for specific channels if needed
   - Review channel restrictions regularly

## Next Steps

Once connected, you can:

- Use the MCP server with Claude Desktop or other MCP clients
- Access Slack channels, messages, and users
- Search messages across your workspace
- Post messages (if enabled)

For more information, see:
- [Installation Guide](docs/02-installation.md)
- [Configuration and Usage](docs/03-configuration-and-usage.md)
- [Main README](README.md)

