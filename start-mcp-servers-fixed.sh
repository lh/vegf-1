#!/bin/bash

# Script to automatically start MCP servers
echo "🚀 Starting MCP servers..."

# Start mcp servers using the correct npx commands directly
# Servers will be automatically registered with Claude if they're not already running

# Start Sequential Thinking MCP
echo "📊 Starting Sequential Thinking..."
npx -y @modelcontextprotocol/server-sequential-thinking > /dev/null 2>&1 &

# Start Filesystem MCP
echo "📁 Starting Filesystem access..."
npx -y @modelcontextprotocol/server-filesystem /Users/rose/Code > /dev/null 2>&1 &

# Start Puppeteer MCP
echo "🌐 Starting Puppeteer..."
npx -y @modelcontextprotocol/server-puppeteer > /dev/null 2>&1 &

# Start Web Fetching MCP
echo "🔍 Starting Fetch..."
npx -y @kazuph/mcp-fetch > /dev/null 2>&1 &

# Start Firecrawl MCP
echo "🔎 Starting Firecrawl..."
env FIRECRAWL_API_KEY=fc-5834e3dc185a4c20924d9906df1b0163 npx -y firecrawl-mcp > /dev/null 2>&1 &

# Start Browser Tools MCP
echo "🧰 Starting Browser Tools..."
npx -y @agentdeskai/browser-tools-mcp@1.2.1 > /dev/null 2>&1 &

# Start Memory MCP
echo "🧠 Starting Memory service..."
uv --directory /Users/rose/Code/mcp-memory-service run memory > /dev/null 2>&1 &

# Start Code Checker MCP
echo "🔧 Starting Code Checker..."
/Users/rose/Code/mcp/mcp-code-checker/run_mcp_server.sh --project-dir /Users/rose/Code/CC > /dev/null 2>&1 &

# Start Playwright MCP
echo "🎭 Starting Playwright..."
npx -y @executeautomation/playwright-mcp-server > /dev/null 2>&1 &

# Wait for servers to start
sleep 3

echo "✅ MCP servers started!"
echo "To verify all servers are running, use: claude mcp list"