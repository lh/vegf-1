#!/bin/bash

# Script to automatically start MCP servers
echo "🚀 Starting MCP servers..."

# Start Sequential Thinking MCP
echo "📊 Starting Sequential Thinking..."
claude mcp start sequential-thinking &

# Start Filesystem MCP
echo "📁 Starting Filesystem access..."
claude mcp start filesystem &

# Start Puppeteer MCP
echo "🌐 Starting Puppeteer..."
claude mcp start puppeteer &

# Start Web Fetching MCP
echo "🔍 Starting Fetch..."
claude mcp start fetch &

# Start Firecrawl MCP
echo "🔎 Starting Firecrawl..."
claude mcp start firecrawl &

# Start Browser Tools MCP
echo "🧰 Starting Browser Tools..."
claude mcp start browser-tools &

# Start Memory MCP
echo "🧠 Starting Memory service..."
claude mcp start memory &

echo "✅ MCP servers started!"
echo "To verify all servers are running, use: claude mcp list"