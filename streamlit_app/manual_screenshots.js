/**
 * Screenshot capture script for AMD Protocol Explorer
 * This script directly captures screenshots of all main pages and any UI issues
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Configuration
const APP_URL = 'http://localhost:8502';
const SCREENSHOT_DIR = './screenshots/monitoring';

// Create screenshots directory if it doesn't exist
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Helper function to log and save to file
 */
function log(message) {
  console.log(message);
  fs.appendFileSync(path.join(SCREENSHOT_DIR, 'capture_log.txt'), message + '\n');
}

/**
 * Save a screenshot with timestamp and description
 */
async function captureScreen(page, description) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `${timestamp}_${description.replace(/\s+/g, '_').toLowerCase()}.png`;
  await page.screenshot({ 
    path: path.join(SCREENSHOT_DIR, filename),
    fullPage: true 
  });
  log(`Captured screenshot: ${filename}`);
  return filename;
}

/**
 * Check for UI errors and warnings
 */
async function checkForUIIssues(page) {
  const issues = await page.evaluate(() => {
    // Find alerts and warnings
    const alerts = Array.from(document.querySelectorAll('.stAlert'));
    return alerts.map(alert => ({
      type: alert.classList.contains('stError') ? 'error' : 
            alert.classList.contains('stWarning') ? 'warning' : 'info',
      message: alert.textContent.trim()
    }));
  });
  
  if (issues.length > 0) {
    log(`Found ${issues.length} UI issues: ${JSON.stringify(issues)}`);
  }
  return issues;
}

/**
 * Main function to capture screenshots
 */
async function captureScreenshots() {
  log('Starting screenshot capture');
  
  const browser = await puppeteer.launch({
    headless: "new",
    defaultViewport: { width: 1280, height: 900 },
    args: ['--no-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    
    // Track network errors
    const failedRequests = [];
    page.on('requestfailed', request => {
      failedRequests.push({
        url: request.url(),
        method: request.method(),
        error: request.failure() ? request.failure().errorText : 'unknown error'
      });
    });
    
    // Monitor console logs
    const consoleLogs = {
      error: [],
      warning: [],
      info: []
    };
    
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      
      if (type === 'error') {
        consoleLogs.error.push(text);
      } else if (type === 'warning') {
        consoleLogs.warning.push(text);
      } else {
        consoleLogs.info.push(text);
      }
    });
    
    // Navigate to home page and take screenshot
    log('Navigating to home page');
    await page.goto(APP_URL, { waitUntil: 'networkidle0', timeout: 60000 });
    await sleep(3000);
    await captureScreen(page, 'home_page');
    
    // Check for UI issues
    await checkForUIIssues(page);
    
    // Create a report of findings
    const report = {
      timestamp: new Date().toISOString(),
      consoleLogs,
      failedRequests,
      uiIssues: await checkForUIIssues(page)
    };
    
    // Save the report as JSON
    fs.writeFileSync(
      path.join(SCREENSHOT_DIR, 'monitoring_report.json'),
      JSON.stringify(report, null, 2)
    );
    
    log('All screenshots captured, report saved.');
  } catch (error) {
    log(`ERROR: ${error.message}`);
    
    // Try to capture error state
    try {
      await page.screenshot({ 
        path: path.join(SCREENSHOT_DIR, 'error_state.png'),
        fullPage: true 
      });
    } catch (e) {
      // Ignore screenshot errors
    }
  } finally {
    await browser.close();
  }
}

// Run the capture
captureScreenshots().catch(error => {
  log(`UNHANDLED ERROR: ${error.message}`);
});