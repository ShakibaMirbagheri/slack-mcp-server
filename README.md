# Slack MCP Server

[![Trust Score](https://archestra.ai/mcp-catalog/api/badge/quality/korotovsky/slack-mcp-server)](https://archestra.ai/mcp-catalog/korotovsky__slack-mcp-server)

A production-ready Model Context Protocol (MCP) server for Slack Workspaces. Connect your AI assistants to Slack with support for channels, DMs, threads, search, and message posting.

## Features

- **🔐 Multiple Authentication Methods**: OAuth tokens (recommended) or browser session tokens
- **💬 Full Channel Support**: Public channels, private channels, DMs, and group DMs
- **🔍 Smart Search**: Search messages with advanced filters (date, user, channel, content)
- **📝 Message Posting**: Optional message posting with channel restrictions for safety
- **⚡ Smart History**: Fetch messages by date range or count with pagination
- **🏢 Enterprise Ready**: Works with Enterprise Slack workspaces
- **🚀 Multiple Transports**: Stdio, SSE, and HTTP transports supported
- **💾 Caching**: User and channel caching for faster access
- **🔒 Production Ready**: Secure, tested, and ready for deployment

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/slack-mcp-server.git
cd slack-mcp-server
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env and add your Slack tokens
```

### 3. Connect to Slack

Follow the comprehensive [Slack Connection Guide](SLACK_CONNECTION_GUIDE.md) to:
- Set up OAuth tokens (recommended for production)
- Or extract browser session tokens
- Verify your connection

### 4. Run with Docker (Recommended)

```bash
# Create network if it doesn't exist
docker network create app-tier

# Start the server
docker-compose up -d
```

### 5. Run Locally

```bash
# Install dependencies
go mod download

# Run the server
go run cmd/slack-mcp-server/main.go --transport stdio
```

## Installation Methods

### Docker Compose (Production)

```bash
docker-compose up -d
```

The server will be available on `http://localhost:3001` (SSE transport).

### Docker

```bash
docker run -d \
  --name slack-mcp-server \
  -p 3001:3001 \
  -e SLACK_MCP_XOXP_TOKEN=xoxp-your-token \
  -e SLACK_MCP_HOST=0.0.0.0 \
  -e SLACK_MCP_PORT=3001 \
  ghcr.io/your-username/slack-mcp-server:latest
```

### Go Binary

```bash
go build -o slack-mcp-server ./cmd/slack-mcp-server
./slack-mcp-server --transport stdio
```

## Configuration

### Environment Variables

All configuration is done via environment variables. See [`.env.example`](.env.example) for a complete list.

**Required:**
- `SLACK_MCP_XOXP_TOKEN` - OAuth token (recommended), OR
- `SLACK_MCP_XOXC_TOKEN` + `SLACK_MCP_XOXD_TOKEN` - Browser session tokens

**Common Optional:**
- `SLACK_MCP_HOST` - Server host (default: `127.0.0.1`)
- `SLACK_MCP_PORT` - Server port (default: `13080`)
- `SLACK_MCP_API_KEY` - Bearer token for SSE/HTTP authentication
- `SLACK_MCP_ADD_MESSAGE_TOOL` - Enable message posting (disabled by default)

See [`.env.example`](.env.example) for all available options.

## MCP Tools

### conversations_history
Fetch messages from a channel or DM with pagination support.

### conversations_replies
Get thread messages by channel ID and thread timestamp.

### conversations_add_message
Post messages to channels (disabled by default, enable via `SLACK_MCP_ADD_MESSAGE_TOOL`).

### conversations_search_messages
Search messages across channels, threads, and DMs with advanced filters.

### channels_list
List all channels (public, private, DMs, group DMs).

## Resources

- `slack://<workspace>/channels` - CSV directory of all channels
- `slack://<workspace>/users` - CSV directory of all users

## Documentation

- **[Slack Connection Guide](SLACK_CONNECTION_GUIDE.md)** - Complete guide to connecting to Slack
- **[Authentication Setup](docs/01-authentication-setup.md)** - Detailed authentication instructions
- **[Installation](docs/02-installation.md)** - Installation methods
- **[Configuration](docs/03-configuration-and-usage.md)** - Configuration options

## Development

### Prerequisites

- Go 1.24.4 or later
- Docker and Docker Compose (optional)

### Build

```bash
make build
```

### Test

```bash
make test
```

### Run Tests

```bash
# Unit tests
go test -v ./...

# Integration tests
go test -v -run=".*Integration.*" ./...
```

## CI/CD

This project includes GitHub Actions workflows for:
- Automated testing
- Docker image building
- Container registry publishing

See [`.github/workflows/build-and-deploy.yml`](.github/workflows/build-and-deploy.yml) for details.

## Security

- Never commit `.env` files or tokens to version control
- Use OAuth tokens for production (more secure than browser tokens)
- Set `SLACK_MCP_API_KEY` when exposing the server over a network
- Review [SECURITY.md](SECURITY.md) for security policies

## Production Deployment

1. **Set up environment variables** - Copy `.env.example` to `.env` and configure
2. **Connect to Slack** - Follow [SLACK_CONNECTION_GUIDE.md](SLACK_CONNECTION_GUIDE.md)
3. **Deploy with Docker** - Use `docker-compose.yml` or Kubernetes
4. **Configure monitoring** - Set up logging and health checks
5. **Enable authentication** - Set `SLACK_MCP_API_KEY` for SSE/HTTP transports

## Troubleshooting

See the [Troubleshooting section](SLACK_CONNECTION_GUIDE.md#troubleshooting) in the connection guide for common issues.

## License

Licensed under MIT - see [LICENSE](LICENSE) file.

This is not an official Slack product.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

- 📖 Check the [Slack Connection Guide](SLACK_CONNECTION_GUIDE.md)
- 📚 Review the [documentation](docs/)
- 🐛 Open an issue on GitHub
- 🔒 Report security issues to [SECURITY.md](SECURITY.md)
