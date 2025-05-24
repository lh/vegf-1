# Playwright Integration with Streamlit App

## Current MCP Server Status and Setup

We've successfully configured the MCP servers to run properly on this system. The key improvements include:

1. Fixed the startup script to use direct commands rather than relying on the Claude CLI
2. Updated the LaunchAgent configuration with proper environment variables
3. Implemented proper error handling and logging
4. Added a comprehensive troubleshooting guide

## Playwright Setup Complete

We've successfully set up Playwright for the Streamlit application:

1. **Dependencies**: Added Playwright and MCP server to package.json
2. **Script Creation**: Created a new Playwright script designed for Streamlit testing
3. **Browser Installation**: Installed required Chromium browser for Playwright
4. **MCP Server Integration**: Created a startup script for the Playwright MCP server

## Usage Instructions

### Starting the Playwright MCP Server

Run the following command to start the Playwright MCP server:

```bash
./start-playwright-mcp-server.sh
```

This will start the server in the background and create a PID file.

### Testing the Streamlit Application

Run the following command to test the Streamlit application using Playwright:

```bash
cd streamlit_app
npm run test:playwright
```

This will:
1. Launch a Chromium browser
2. Navigate to the Streamlit app (http://localhost:8501)
3. Wait for the app to load
4. Take a screenshot
5. Close the browser

### Stopping the Playwright MCP Server

To stop the server, you can use:

```bash
kill $(cat streamlit_app/playwright-mcp-server.pid)
```

## Current Streamlit App Overview

The APE (AMD Protocol Explorer) application is a scientific tool for simulating and analyzing AMD treatment protocols. Key components include:

1. **Simulation Configuration**: Parameters for running ABS/DES simulations
2. **Patient Explorer**: Individual patient data analysis
3. **Visualization Components**: Charts for visual acuity, treatment phases, and other clinical outcomes

## Technical Details

- Streamlit app running on: http://localhost:8502
- Custom MCP Playwright server running on: http://localhost:5006
- Custom MCP Playwright server script: `/Users/rose/Code/CC/streamlit_app/playwright-mcp-server.js`
- Playwright script: `/Users/rose/Code/CC/streamlit_app/playwright_streamlit.js`
- Current Puppeteer implementation files: 
  - `/Users/rose/Code/CC/streamlit_app/view_app.js`
  - `/Users/rose/Code/CC/streamlit_app/improved_puppeteer_test.js`

## Implemented Features

The Playwright integration now includes:

1. **Custom MCP Server**: A custom MCP server implementation that provides a health check endpoint on port 5006.
2. **LaunchAgent Configuration**: Automatically starts the Playwright MCP server on system boot.
3. **Test Script**: A comprehensive test script that navigates through the Streamlit app and takes screenshots.
4. **Claude Integration**: Registration with Claude's MCP system.

## Automated Testing

The test script (`playwright_streamlit.js`) performs the following actions:

1. Launches a Chromium browser and navigates to the Streamlit app
2. Waits for the app to fully load
3. Takes screenshots of the main page and sidebar
4. Navigates to different pages using sidebar links
5. Takes screenshots of each page visited
6. Saves all screenshots to the logs directory

## Troubleshooting

If the Playwright MCP server fails to start:

1. Check if the server is already running:
   ```bash
   curl -s http://localhost:5006/healthz
   ps aux | grep playwright-mcp-server
   ```

2. Check the log files for errors:
   ```bash
   cat streamlit_app/logs/playwright-mcp-server-error.log
   cat streamlit_app/logs/playwright-mcp-server-stderr.log
   ```

3. Verify that all dependencies are installed:
   ```bash
   cd streamlit_app
   npm install
   npx playwright install chromium
   ```

4. Restart the LaunchAgent:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.user.mcp-playwright-server.plist
   launchctl load -w ~/Library/LaunchAgents/com.user.mcp-playwright-server.plist
   ```

5. Ensure the Streamlit app is running on port 8502 before attempting to connect with Playwright.