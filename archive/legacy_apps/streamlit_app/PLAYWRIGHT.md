# Using Playwright with Streamlit

This project includes Playwright integration for automated testing of the Streamlit application. This document provides instructions for setting up and using Playwright with the Streamlit app.

## Setup

To set up Playwright for use with Streamlit, run the setup script:

```bash
./setup-playwright.sh
```

This script:
1. Installs Node.js dependencies
2. **Crucially** installs the Playwright browsers (Chromium)
3. Tests that the Playwright browser can be launched successfully

> **Important**: According to the [Streamlit community discussion](https://discuss.streamlit.io/t/using-playwright-with-streamlit/28380/10), simply installing Playwright via pip or npm is not sufficient. You must explicitly run `playwright install` to download the browser code.

## Running Tests

To run the Playwright tests:

```bash
npm run test:playwright
```

This will:
1. Launch a Chromium browser
2. Navigate to the Streamlit app (http://localhost:8502)
3. Verify that the app loads correctly
4. Take screenshots of different pages
5. Save the screenshots to the `logs` directory

## Test Script

The test script (`playwright_streamlit.js`) performs the following actions:

1. Launches a Chromium browser in headed mode (visible browser window)
2. Navigates to the Streamlit app on port 8502
3. Waits for the app to fully load
4. Takes screenshots of the main page and sidebar
5. Navigates to different pages using sidebar links
6. Takes screenshots of each page visited
7. Saves all screenshots to the logs directory

## Troubleshooting

If you encounter issues:

1. Ensure the Streamlit app is running on port 8502:
   ```bash
   streamlit run app.py
   ```

2. Make sure Playwright browsers are installed:
   ```bash
   npx playwright install chromium
   ```

3. Check that the browser can be launched:
   ```bash
   node -e "const { chromium } = require('playwright'); (async () => { const browser = await chromium.launch(); console.log('Browser launched successfully'); await browser.close(); })().catch(console.error);"
   ```

4. Review screenshots in the `logs` directory for visual verification

## Custom MCP Server (Optional)

The project also includes a custom MCP server for integration with Claude Code:

- Custom server: `playwright-mcp-server.js`
- Health check: http://localhost:5006/healthz

To start the custom MCP server manually:
```bash
node playwright-mcp-server.js
```