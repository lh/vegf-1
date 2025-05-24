#!/bin/bash

# MCP Playwright Installation and Configuration Script

echo "Installing and configuring MCP Playwright server..."

# Move to the project directory
cd "$(dirname "$0")"

# Install Playwright and dependencies in the streamlit_app directory
cd streamlit_app
npm install

# Install Playwright browsers
npx playwright install chromium

# Create logs directory
mkdir -p logs

# Return to the project root
cd ..

echo "Creating LaunchAgent configuration for MCP Playwright server..."

# Create LaunchAgent configuration file
LAUNCH_AGENT_FILE=~/Library/LaunchAgents/com.user.mcp-playwright-server.plist
cat > "${LAUNCH_AGENT_FILE}" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.mcp-playwright-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which node)</string>
        <string>$(pwd)/streamlit_app/playwright-mcp-server.js</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>$(pwd)/streamlit_app</string>
    <key>StandardOutPath</key>
    <string>$(pwd)/streamlit_app/logs/playwright-mcp-server-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$(pwd)/streamlit_app/logs/playwright-mcp-server-stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.nvm/versions/node/v20.9.0/bin</string>
        <key>NODE_PATH</key>
        <string>$HOME/.nvm/versions/node/v20.9.0/lib/node_modules</string>
    </dict>
</dict>
</plist>
EOF

# Unload any existing LaunchAgent
launchctl unload "${LAUNCH_AGENT_FILE}" 2>/dev/null || true

# Load the LaunchAgent
launchctl load -w "${LAUNCH_AGENT_FILE}"

echo "MCP Playwright server has been installed and configured to start automatically."
echo "You can check the status with: 'launchctl list | grep mcp-playwright'"
echo "Logs are available at: $(pwd)/streamlit_app/logs/"