#!/bin/bash

# Setup Playwright for Streamlit application
# Based on recommendations from https://discuss.streamlit.io/t/using-playwright-with-streamlit/28380/10

echo "Setting up Playwright for Streamlit integration..."

# Move to the application directory
cd "$(dirname "$0")"

# Install dependencies
echo "Installing dependencies..."
npm install

# Explicitly install Playwright browsers (critical step)
echo "Installing Playwright browsers..."
npx playwright install chromium

echo "Testing Playwright setup..."
node -e "const { chromium } = require('playwright'); (async () => { const browser = await chromium.launch(); console.log('Playwright browser launched successfully'); await browser.close(); })().catch(console.error);"

echo "Setup complete. You can now run the test script with:"
echo "npm run test:playwright"