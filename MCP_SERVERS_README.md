# MCP Servers Setup Guide

## Automatic Startup

Your MCP servers are configured to start automatically when you log in to your Mac.

### Manual Controls

- **Start all servers**: 
  ```bash
  ./start-mcp-servers.sh
  ```

- **Enable automatic startup**:
  ```bash
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

### Configuration

- Scripts are located at: 
  - `/Users/rose/Code/CC/start-mcp-servers.sh`
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