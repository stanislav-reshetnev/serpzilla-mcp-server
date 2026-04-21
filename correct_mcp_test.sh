#!/bin/bash
# correct_mcp_test.sh

echo "🚀 Starting MCP Server Test"
echo "============================"

# Function to send a message to MCP server
send_message() {
    local message="$1"
    echo "$message"
}

# Launch the server and send a sequence of messages
(
    # 1. Initialize - mandatory first request
    echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"0.1.0","clientInfo":{"name":"cli-test","version":"1.0.0"},"capabilities":{}}}'
    sleep 0.5

    # 2. Initialized notification - mandatory after initialize
    echo '{"jsonrpc":"2.0","method":"initialized"}'
    sleep 0.5

    # 3. Now we can request tools
    echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
    sleep 0.5

    # 4. Call the authorize tool
    echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"authorize","arguments":{}}}'
    sleep 0.5

    # 5. Call the list_projects tool
    echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"list_projects","arguments":{}}}'

) | docker run -i --rm \
    --env-file .env \
    serpzilla-mcp-stdio-server 2>/dev/null | while IFS= read -r line; do
        # Format the output with jq if it is JSON
        if echo "$line" | jq -e . >/dev/null 2>&1; then
            echo "$line" | jq '.'
        else
            echo "$line"
        fi
    done