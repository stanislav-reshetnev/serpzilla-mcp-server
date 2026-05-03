# Serpzilla MCP Server

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)
[![MCP](https://img.shields.io/badge/MCP-stdio-green.svg)](https://modelcontextprotocol.io)

MCP (Model Context Protocol) server for Serpzilla API that enables purchasing guest post placements for SEO purposes. Implements stdio transport and is ready to run in a Docker container.

A Docker image based on this repository is located at the URL: https://hub.docker.com/r/stanislavusbest/serpzilla-mcp-stdio-server/tags

## Features

- 🔐 **Dual Authentication** - Automatic AUTH_TICKET and JWT token management
- 📁 **Project Management** - Create and list projects
- 📝 **Content Management** - Add texts with anchors for promoted URLs
- 🔍 **Advanced Search** - Filter donor sites by multiple parameters:
  - Price range
  - Domain Rating (DR)
  - Traffic volume
  - Language
  - Majestic CF/TF
  - Moz DA/PA/Spam Score
  - Ahrefs metrics
  - Semrush metrics
  - Domain age
  - Placement time
  - And more...
- 💰 **Purchase Placements** - Buy guest posts, link insertions, and articles
- 📊 **Placement Tracking** - View all purchased placements per project

## Prerequisites

- Docker (recommended) or Python 3.11+
- Serpzilla account with [API token](https://passport.serpzilla.com/security/token/)

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/stanislav-reshetnev/serpzilla-mcp-server.git
cd serpzilla-mcp-server
```

2. **Build the Docker image**
```bash
docker build -t serpzilla-mcp-stdio-server:latest .
```

3. **Run the container (without logging)**
```bash
docker run -i --rm \
  -e SERPZILLA_LOGIN="your_email@example.com" \
  -e SERPZILLA_API_TOKEN="your_api_token" \
  serpzilla-mcp-stdio-server:latest <<EOF
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"0.1.0","clientInfo":{"name":"cli-test","version":"1.0.0"},"capabilities":{}}}
EOF
```

4. **Run with logging to a file**

To enable logs (controlled by ENABLE_LOGS=true), mount a log file from the host:

```bash
# Create an empty log file on the host and set permissions
touch /var/log/serpzilla-mcp-stdio-server.log
chmod 666 /var/log/serpzilla-mcp-stdio-server.log

docker run -i --rm \
  -v /var/log/serpzilla-mcp-stdio-server.log:/var/log/serpzilla-mcp-stdio-server.log \
  -e SERPZILLA_LOGIN="your_email@example.com" \
  -e SERPZILLA_API_TOKEN="your_api_token" \
  -e ENABLE_LOGS="true" \
  serpzilla-mcp-stdio-server:latest <<EOF
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"0.1.0","clientInfo":{"name":"cli-test","version":"1.0.0"},"capabilities":{}}}
EOF

# After the container exits, inspect the logs:
cat /var/log/serpzilla-mcp-stdio-server.log
```

Make sure the file exists and is writable by the container's user before starting.

### Using Python Directly

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SERPZILLA_LOGIN="your_email@example.com"
export SERPZILLA_API_TOKEN="your_api_token"

# Run the server
python server.py
```

## Environment Variables

| Variable              | Description | Required |
|-----------------------|-------------|----------|
| `SERPZILLA_LOGIN`     | Your Serpzilla account email | Yes |
| `SERPZILLA_API_TOKEN` | Your Serpzilla API token | Yes |
| `ENABLE_LOGS`         | Set to `true` to write logs to /var/log/serpzilla-mcp-stdio-server.log | No (default false) |

## Available Tools

| Tool | Description |
|------|-------------|
| `authorize` | Authenticate with Serpzilla API |
| `list_projects` | Get list of existing projects |
| `create_project` | Create new project for domain promotion |
| `search_sites` | Search donor sites with filters |
| `purchase_placement` | Buy placement on selected site |
| `add_text` | Add text with anchor for URL promotion |
| `get_project_placements` | Get all placements in a project |
| `get_user_info` | Get current user information including account balance. To top up your balance, visit: https://passport.serpzilla.com/deposit/ |

## Usage Example

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_sites",
    "arguments": {
      "project_id": 12345,
      "link_type": "link",
      "price_from": 10,
      "price_to": 100,
      "min_dr": 30,
      "language": "en"
    }
  }
}
```

## Integration with OpenClaw

Add to your OpenClaw configuration:

```bash
npx mcporter config add serpzilla --stdio \
 "docker run -i --rm --env SERPZILLA_LOGIN=XXX --env SERPZILLA_API_TOKEN=XXX serpzilla-mcp-stdio-server:latest"
```

## Project Structure

```
serpzilla-mcp-server/
├── server.py              # Main MCP server
├── serpzilla_client.py    # Serpzilla API client
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker build configuration
└── README.md              # This file
```

## API Reference

The server implements the Serpzilla API methods documented in the [official OpenAPI specification](https://app.serpzilla.com/openapi_spec).

### Supported Link Types

| Type | Description |
|------|-------------|
| `news` | Advertiser's Article (Guest Post) |
| `review` | Publisher's Article (Guest Post) |
| `link` | In The News (Link Insertion) |
| `archive` | In The Archive (Link Insertion) |

## Error Handling

The server automatically handles token expiration and retries authentication when receiving 401 responses. All errors are returned in JSON format with descriptive messages.

## License

MIT

## Disclaimer

This is an unofficial MCP server for Serpzilla. Use in accordance with Serpzilla's terms of service.

## Support

For issues or questions, please open an issue on GitHub.