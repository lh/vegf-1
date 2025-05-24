#!/bin/bash

# Stop the Playwright MCP server
if [ -f "streamlit_app/playwright-mcp-server.pid" ]; then
  PID=$(cat streamlit_app/playwright-mcp-server.pid)
  if ps -p $PID > /dev/null; then
    echo "Stopping Playwright MCP server with PID $PID"
    kill $PID
    rm streamlit_app/playwright-mcp-server.pid
  else
    echo "No running Playwright MCP server found with PID $PID"
    rm streamlit_app/playwright-mcp-server.pid
  fi
else
  echo "No PID file found for Playwright MCP server"
fi