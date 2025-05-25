# MCP Servers Setup Guide

## Automatic Startup

Your MCP servers are configured to start automatically when you log in to your Mac.

### Manual Controls

- **Start all servers manually**: 
  ```bash
  ./start-mcp-servers-fixed.sh
  ```

- **Restart all servers** (if having issues):
  ```bash
  pkill -f "mcp" && sleep 2 && ./start-mcp-servers-fixed.sh
  ```

- **Enable automatic startup**:
  ```bash
  cp ~/Code/CC/com.rose.mcpservers-fixed.plist ~/Library/LaunchAgents/com.rose.mcpservers.plist
  launchctl unload ~/Library/LaunchAgents/com.rose.mcpservers.plist 2>/dev/null || true
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
  - `/Users/rose/Code/CC/start-mcp-servers-fixed.sh` - Main startup script 
  - `/Users/rose/Library/LaunchAgents/com.rose.mcpservers.plist` - LaunchAgent configuration

- Logs are written to:
  - `/Users/rose/Library/Logs/mcp-servers.log`

### Installed MCP Servers

- sequential-thinking - Used for step-by-step thinking processes
- filesystem - Provides access to /Users/rose/Code directory
- puppeteer - Browser automation
- fetch - Web content fetching
- firecrawl - Web crawling and search capabilities
- browser-tools - Browser debug and testing tools
- memory - Long-term memory capabilities
- code-checker - Code quality and testing tools
- playwright - Additional browser automation

### Troubleshooting

#### Playwright Connection Failed
If you see "Connection failed: spawn npx -y @executeautomation/playwright-mcp-server ENOENT":
1. Install the package: `npm install -g @executeautomation/playwright-mcp-server`
2. Restart the servers: `pkill -f "mcp" && sleep 2 && ./start-mcp-servers-fixed.sh`

#### Browser-tools Connection Errors
Messages like "Error checking localhost:3025: fetch failed" are normal during startup. 
The browser-tools server is searching for a browser instance and will connect to one when available.

#### Command not found Errors
If you see "command not found" errors in the log:
1. Make sure node and npm are in your PATH
2. Update the PATH in the `com.rose.mcpservers-fixed.plist` file
3. Copy the updated plist to LaunchAgents and reload

#### General Troubleshooting
1. Check the logs: `cat ~/Library/Logs/mcp-servers.log`
2. Restart all servers: `pkill -f "mcp" && sleep 2 && ./start-mcp-servers-fixed.sh`
3. Verify running servers: `claude mcp list`
4. If a specific server is missing, check its dependencies