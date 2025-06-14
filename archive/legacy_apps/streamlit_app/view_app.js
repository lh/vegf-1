/**
 * Simple script to open Streamlit app and take screenshots
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Configuration
const APP_URL = 'http://localhost:8502';
const SCREENSHOT_DIR = './screenshots/monitoring';
const LOG_FILE = path.join(SCREENSHOT_DIR, 'monitoring_log.txt');

// Create screenshots directory if it doesn't exist
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

/**
 * Helper function to log debug information
 */
function log(message, data = null) {
  const timestamp = new Date().toISOString();
  const formattedMessage = `[${timestamp}] ${message}`;
  console.log(formattedMessage);

  if (data) {
    console.log(JSON.stringify(data, null, 2));
  }

  // Log to file
  fs.appendFileSync(LOG_FILE, formattedMessage + (data ? '\n' + JSON.stringify(data, null, 2) : '') + '\n', 
    { encoding: 'utf8' });
}

/**
 * Run the monitoring process
 */
async function monitorApp() {
  log('Starting APE viewer');
  
  // Launch browser without headless mode so you can interact with it
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: { width: 1280, height: 900 },
    args: ['--no-sandbox', '--window-size=1280,900'],
  });
  
  try {
    const page = await browser.newPage();
    
    // Monitor console messages
    page.on('console', message => {
      log(`CONSOLE ${message.type()}: ${message.text()}`);
    });
    
    // Navigate to the app
    log('Navigating to Streamlit app...');
    await page.goto(APP_URL);
    
    // Display instructions
    log('Browser opened. Please:');
    log('1. Manually interact with the Streamlit app');
    log('2. Test different features and navigation');
    log('3. Check for visual anomalies and errors');
    log('4. Close the browser when done to save screenshots');
    
    // Wait until browser is closed by user
    log('Waiting for you to close the browser...');
    
    // Auto capture initial screenshot after 5 seconds
    await new Promise(resolve => setTimeout(resolve, 5000));
    await page.screenshot({ 
      path: `${SCREENSHOT_DIR}/initial_state.png`, 
      fullPage: true 
    });
    log('Initial screenshot captured');
    
    // Event for when a new page is created
    browser.on('targetcreated', async target => {
      if (target.type() === 'page') {
        log('New page detected');
        const newPage = await target.page();
        if (newPage) {
          // Monitor console on the new page too
          newPage.on('console', message => {
            log(`CONSOLE (new page) ${message.type()}: ${message.text()}`);
          });
        }
      }
    });
    
    // Wait for browser to be closed
    await browser.waitForTarget(target => target.type() === 'browser', { timeout: 0 });
  } catch (error) {
    log(`ERROR: ${error.message}`);
  } finally {
    try {
      // Try to close the browser if it's still open
      if (browser && browser.process() != null) {
        await browser.close();
      }
    } catch (closeError) {
      // Ignore errors on close
    }
    log('Browser closed, monitoring complete');
  }
}

// Run the app
monitorApp().catch(error => {
  log(`UNHANDLED ERROR: ${error.message}`);
  process.exit(1);
});