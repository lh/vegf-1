# MCP Servers Setup Guide

## Automatic Startup

Your MCP servers are configured to start automatically when you log in to your Mac.

### Manual Controls

- **Start all servers**: 
  ```bash
  ./start-mcp-servers-fixed.sh
  ```

- **Enable automatic startup**:
  ```bash
  cp ~/Code/CC/com.rose.mcpservers-fixed.plist ~/Library/LaunchAgents/com.rose.mcpservers.plist
  launchctl unload ~/Library/LaunchAgents/com.rose.mcpservers.plist
  launchctl load ~/Library/LaunchAgents/com.rose.mcpservers.plist
  ```

- **Disable automatic startup**:
  ```bash
  launchctl unload ~/Library/LaunchAgents/com.rose.mcpservers.plist
  ```

- **Check running servers**:
  ```bash
  claude mcp list
  ```

- **Restart all servers (if there are issues)**:
  ```bash
  claude mcp stop all
  ./start-mcp-servers-fixed.sh
  ```

### Configuration

- Scripts are located at: 
  - `/Users/rose/Code/CC/start-mcp-servers-fixed.sh`
  - `/Users/rose/Library/LaunchAgents/com.rose.mcpservers.plist`

- Logs are written to:
  - `/Users/rose/Library/Logs/mcp-servers.log`

### Installed MCP Servers

- sequential-thinking
- filesystem
- puppeteer
- fetch
- firecrawl
- browser-tools
- memory
- code-checker
- playwright

### Troubleshooting

If you encounter "Connection failed" errors with the Playwright MCP server:
1. Install or reinstall the package: `npm install -g @executeautomation/playwright-mcp-server`
2. Restart the servers

For browser-tools errors about "Error checking localhost:XXXX", these are typically harmless discovery attempts. The browser-tools server will connect to a browser when one is opened.