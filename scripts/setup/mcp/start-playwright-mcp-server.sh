#!/bin/bash

# Start the Playwright MCP server
cd "$(dirname "$0")/streamlit_app"
npx -y @executeautomation/playwright-mcp-server > playwright-mcp-server.log 2>&1 &
echo $! > playwright-mcp-server.pid
echo "Playwright MCP server started with PID $(cat playwright-mcp-server.pid)"