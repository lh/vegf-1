/**
 * APE Monitoring Script
 * 
 * This script monitors the AMD Protocol Explorer Streamlit app,
 * visits all pages, runs a simulation, and captures any issues.
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Configuration
const APP_URL = 'http://localhost:8502';
const SCREENSHOT_DIR = './screenshots/monitoring';
const TIMEOUT = 30000; // 30 seconds timeout for operations
const LOG_FILE = path.join(SCREENSHOT_DIR, 'monitoring_log.txt');

// Create screenshots directory if it doesn't exist
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

/**
 * Helper function to sleep for the specified number of milliseconds
 */
async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
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
 * Capture console logs from the browser
 */
function setupConsoleCapture(page) {
  // Capture console messages
  page.on('console', message => {
    const type = message.type();
    const text = message.text();
    log(`CONSOLE ${type}: ${text}`);
  });

  // Capture errors
  page.on('error', error => {
    log(`PAGE ERROR: ${error.message}`);
  });

  // Capture request failures
  page.on('requestfailed', request => {
    let errorText = '';
    try {
      errorText = request.failure().errorText;
    } catch (e) {
      errorText = 'Unknown error';
    }
    log(`REQUEST FAILED: ${request.url()} - ${errorText}`);
  });
}

/**
 * Run the monitoring process
 */
async function monitorApp() {
  log('Starting APE monitoring');
  
  const browser = await puppeteer.launch({
    headless: false, // Use visible browser for debugging
    defaultViewport: { width: 1280, height: 900 },
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  
  try {
    const page = await browser.newPage();
    setupConsoleCapture(page);

    // Navigate to the app
    log('Navigating to AMD Protocol Explorer...');
    await page.goto(APP_URL, { waitUntil: 'networkidle0', timeout: TIMEOUT });
    await sleep(5000); // Increased wait time for full load
    
    // Take initial screenshot
    await page.screenshot({ path: `${SCREENSHOT_DIR}/01_home_page.png`, fullPage: true });
    log('Home page loaded and screenshot captured');
    
    // Save the HTML for debugging
    const initialHtml = await page.content();
    fs.writeFileSync(path.join(SCREENSHOT_DIR, 'initial_html.txt'), initialHtml);
    log('Saved initial HTML for debugging');
    
    // Get the sidebar navigation options using more robust selectors
    const navSections = await page.evaluate(() => {
      // Try to find all radio buttons in the sidebar
      const radioLabels = Array.from(document.querySelectorAll('[data-testid="stSidebarNav"] label'));
      if (radioLabels.length > 0) {
        return radioLabels.map(label => ({
          name: label.textContent.trim(),
          index: Array.from(label.parentElement.children).indexOf(label)
        }));
      }
      
      // Fallback to all radio buttons
      const allRadioLabels = Array.from(document.querySelectorAll('[data-testid="stRadio"] label'));
      return allRadioLabels.map(label => ({
        name: label.textContent.trim(),
        index: Array.from(label.parentElement.children).indexOf(label)
      }));
    });
    
    log('Found navigation sections:', navSections);
    
    // Navigate to "Run Simulation" directly using the radio button index
    try {
      log('Navigating to Run Simulation page directly...');
      
      // Find and click "Run Simulation" radio option (usually the second option)
      const radioSelector = '[data-testid="stRadio"] label:nth-child(2)';
      await page.waitForSelector(radioSelector, { timeout: 5000 });
      await page.click(radioSelector);
      
      log('Clicked on Run Simulation radio button');
      await sleep(3000);
      
      // Take screenshot of Run Simulation page
      await page.screenshot({ 
        path: `${SCREENSHOT_DIR}/run_simulation.png`, 
        fullPage: true 
      });
      
      log('Run Simulation page loaded and screenshot captured');
      
      // Run a simulation
      await runSimulation(page);
    } catch (e) {
      log(`ERROR navigating to Run Simulation: ${e.message}`);
      // Take screenshot of the current state
      await page.screenshot({ 
        path: `${SCREENSHOT_DIR}/error_run_simulation.png`, 
        fullPage: true 
      });
    }
    
    // Check browser console for errors
    const consoleErrors = await page.evaluate(() => {
      if (window.console && window.console.error) {
        // This is a simplified way to check - in a real scenario you'd need to monkey patch console.error
        return window._consoleErrors || [];
      }
      return [];
    });
    
    if (consoleErrors && consoleErrors.length > 0) {
      log('CONSOLE ERRORS detected:', consoleErrors);
    }
    
    // Check for network errors
    const networkErrors = await page.evaluate(() => {
      if (window.performance) {
        return window.performance.getEntries()
          .filter(entry => entry.entryType === 'resource' && !entry.responseEnd)
          .map(entry => entry.name);
      }
      return [];
    });
    
    if (networkErrors && networkErrors.length > 0) {
      log('NETWORK ERRORS detected:', networkErrors);
    } else {
      log('No network errors detected');
    }
    
    // Check for UI errors or warnings
    const uiMessages = await page.evaluate(() => {
      const alerts = Array.from(document.querySelectorAll('.stAlert'));
      return alerts.map(alert => ({
        type: alert.classList.contains('stError') ? 'error' : 
              alert.classList.contains('stWarning') ? 'warning' : 'info',
        message: alert.textContent.trim()
      }));
    });
    
    if (uiMessages && uiMessages.length > 0) {
      log('UI ALERTS detected:', uiMessages);
    }
    
    log('Monitoring completed successfully');
  } catch (error) {
    log(`ERROR: ${error.message}`, error);
    
    // Attempt to take a screenshot of the error state
    try {
      await page.screenshot({ path: `${SCREENSHOT_DIR}/error_state.png`, fullPage: true });
      log('Error state screenshot captured');
    } catch (screenshotError) {
      log(`Failed to capture error screenshot: ${screenshotError.message}`);
    }
  } finally {
    await sleep(3000);
    await browser.close();
  }
}

/**
 * Run a simulation and capture the results
 */
async function runSimulation(page) {
  log('Setting up a simulation...');
  
  try {
    // Capture all sliders on the page
    const sliders = await page.$$('[data-testid="stSlider"]');
    log(`Found ${sliders.length} sliders on the page`);
    
    // Adjust population size (first slider)
    if (sliders.length > 0) {
      const sliderBounds = await sliders[0].boundingBox();
      // Click at 30% of the slider width for approximately 500 population
      await page.mouse.click(
        sliderBounds.x + sliderBounds.width * 0.3, 
        sliderBounds.y + sliderBounds.height / 2
      );
      log('Adjusted population size slider');
      await sleep(1000);
    }
    
    // Capture screenshot of configuration
    await page.screenshot({ 
      path: `${SCREENSHOT_DIR}/simulation_config.png`, 
      fullPage: true 
    });
    
    // Find and click the Run Simulation button
    log('Looking for Run Simulation button...');
    
    // Try different ways to locate the button
    const buttonSelectors = [
      "//button[contains(text(), 'Run Simulation')]",
      "//button[contains(@class, 'stButton')]",
      "//button[contains(@kind, 'primary')]"
    ];
    
    let runButton = null;
    for (const selector of buttonSelectors) {
      const buttons = await page.$x(selector);
      if (buttons.length > 0) {
        runButton = buttons[0];
        log(`Found run button using selector: ${selector}`);
        break;
      }
    }
    
    if (!runButton) {
      // One last attempt - find the first primary button
      const primaryButtons = await page.$$('.stButton button');
      if (primaryButtons.length > 0) {
        runButton = primaryButtons[0];
        log('Using first button as fallback');
      }
    }
    
    if (runButton) {
      await runButton.click();
      log('Clicked Run Simulation button');
      
      // Wait for simulation to complete
      log('Waiting for simulation to complete...');
      
      // Wait for 30 seconds - simulations can take time
      await sleep(30000);
      
      // Take screenshot after completion
      await page.screenshot({ 
        path: `${SCREENSHOT_DIR}/simulation_results.png`, 
        fullPage: true 
      });
      
      // Check for visualization elements
      const hasVisualization = await page.evaluate(() => {
        // Look for visual acuity plot title
        const headings = Array.from(document.querySelectorAll('h3'));
        const hasVisualAcuityHeading = headings.some(h => 
          h.textContent.includes('Visual Acuity') || 
          h.textContent.includes('Acuity') || 
          h.textContent.includes('Visualization')
        );
        
        // Also check for any SVG/canvas elements (plots)
        const hasSvg = document.querySelector('svg') !== null;
        const hasCanvas = document.querySelector('canvas') !== null;
        
        return {
          hasVisualAcuityHeading,
          hasSvg,
          hasCanvas
        };
      });
      
      log('Visualization check results:', hasVisualization);
      
      if (hasVisualization.hasVisualAcuityHeading || hasVisualization.hasSvg || hasVisualization.hasCanvas) {
        log('Visualization elements found');
      } else {
        log('WARNING: No visualization elements found');
      }
      
      // Check for success messages
      const successMessage = await page.evaluate(() => {
        const successElements = document.querySelectorAll('.stSuccess');
        return Array.from(successElements).map(el => el.textContent);
      });
      
      if (successMessage && successMessage.length > 0) {
        log('Success messages found:', successMessage);
      }
      
      // Check for error messages
      const errorMessages = await page.evaluate(() => {
        const errorElements = document.querySelectorAll('.stError, .stException, .stWarning');
        return Array.from(errorElements).map(el => ({
          type: el.classList.contains('stError') ? 'error' : 
                el.classList.contains('stWarning') ? 'warning' : 'exception',
          message: el.textContent
        }));
      });
      
      if (errorMessages && errorMessages.length > 0) {
        log('Error messages detected:', errorMessages);
      }
    } else {
      log('WARNING: Could not find Run Simulation button');
    }
  } catch (error) {
    log(`Error during simulation: ${error.message}`);
    
    // Try to take a screenshot of the error state
    try {
      await page.screenshot({ 
        path: `${SCREENSHOT_DIR}/simulation_error.png`, 
        fullPage: true 
      });
    } catch (screenshotError) {
      log(`Failed to capture error screenshot: ${screenshotError.message}`);
    }
  }
}

// Run the monitoring process
monitorApp().catch(err => {
  log(`Unhandled error: ${err.message}`, err);
  process.exit(1);
});