#!/bin/bash

# Register the custom MCP Playwright server with Claude

echo "Registering custom MCP Playwright server with Claude..."

# Create Claude MCP configuration
CLAUDE_MCP_DIR="$HOME/.claude/mcp"
mkdir -p "$CLAUDE_MCP_DIR"

CONFIG_FILE="$CLAUDE_MCP_DIR/playwright.json"
cat > "$CONFIG_FILE" << EOF
{
  "name": "playwright",
  "version": "1.0.0",
  "description": "Custom Playwright MCP server for Streamlit integration",
  "url": "http://localhost:5006/playwright",
  "healthCheckUrl": "http://localhost:5006/healthz"
}
EOF

echo "Created MCP configuration at: $CONFIG_FILE"
echo ""
echo "To check if the server is registered with Claude, run:"
echo "  claude mcp list"
echo ""
echo "To manually test the server health, run:"
echo "  curl http://localhost:5006/healthz"
echo ""
echo "You may need to restart Claude for the changes to take effect."