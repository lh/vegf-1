#!/bin/bash

# Script to automatically start MCP servers
echo "🚀 Starting MCP servers..."

# Full path to Claude CLI
CLAUDE_PATH="/Users/rose/.nvm/versions/node/v20.9.0/bin/claude"

# Start Sequential Thinking MCP
echo "📊 Starting Sequential Thinking..."
$CLAUDE_PATH mcp start sequential-thinking &

# Start Filesystem MCP
echo "📁 Starting Filesystem access..."
$CLAUDE_PATH mcp start filesystem &

# Start Puppeteer MCP
echo "🌐 Starting Puppeteer..."
$CLAUDE_PATH mcp start puppeteer &

# Start Web Fetching MCP
echo "🔍 Starting Fetch..."
$CLAUDE_PATH mcp start fetch &

# Start Firecrawl MCP
echo "🔎 Starting Firecrawl..."
$CLAUDE_PATH mcp start firecrawl &

# Start Browser Tools MCP
echo "🧰 Starting Browser Tools..."
$CLAUDE_PATH mcp start browser-tools &

# Start Memory MCP
echo "🧠 Starting Memory service..."
$CLAUDE_PATH mcp start memory &

# Start Code Checker MCP (if needed)
echo "🔧 Starting Code Checker..."
$CLAUDE_PATH mcp start code-checker --project-dir /Users/rose/Code/CC &

# Wait for all services to start
sleep 2

echo "✅ MCP servers started!"
echo "To verify all servers are running, use: $CLAUDE_PATH mcp list"