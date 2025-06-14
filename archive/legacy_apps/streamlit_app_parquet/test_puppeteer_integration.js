/**
 * Puppeteer Test Script for AMD Protocol Explorer
 * This script demonstrates how to interact with the Streamlit app using Puppeteer
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Configuration
const APP_URL = 'http://localhost:8502';
const SCREENSHOT_DIR = './screenshots';
const TIMEOUT = 15000; // 15 seconds timeout for operations

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

  // Optionally log to file
  fs.appendFileSync(path.join(SCREENSHOT_DIR, 'test_log.txt'),
    formattedMessage + (data ? '\n' + JSON.stringify(data, null, 2) : '') + '\n',
    { encoding: 'utf8' });
}

async function runTest() {
  console.log('Starting Puppeteer test for AMD Protocol Explorer');
  
  // Launch browser
  const browser = await puppeteer.launch({
    headless: "new", // Use the new headless mode for Chrome
    defaultViewport: { width: 1280, height: 900 },
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  
  try {
    const page = await browser.newPage();

    // Navigate to the app
    console.log('Navigating to AMD Protocol Explorer...');
    await page.goto(APP_URL, { waitUntil: 'networkidle0', timeout: TIMEOUT });
    await sleep(5000); // Increased wait time

    // Take initial screenshot
    await page.screenshot({ path: `${SCREENSHOT_DIR}/01_home_page.png` });
    console.log('Home page loaded');

    // Dump HTML for debugging
    const html = await page.content();
    require('fs').writeFileSync(`${SCREENSHOT_DIR}/page_html.txt`, html);
    console.log('Saved page HTML for debugging');

    // Check if we have Puppeteer helpers
    const hasHelpers = await page.evaluate(() => {
      return typeof window.puppeteerHelpers !== 'undefined';
    });

    console.log(`Puppeteer helpers available: ${hasHelpers}`);
    
    // Get available test IDs if helpers are available
    if (hasHelpers) {
      const elements = await page.evaluate(() => {
        return window.puppeteerHelpers.getAllElements();
      });
      console.log('Available elements:', elements);
    }
    
    // Navigate to Run Simulation page
    console.log('Navigating to Run Simulation page...');
    // Try using the sidebar navigation with multiple approaches
    try {
      // First try using the marker
      await page.waitForSelector('[data-test-id="main-navigation-marker"]', { timeout: 5000 });
      // Then click the Run Simulation radio button (second option in the radio group)
      await page.click('[data-testid="stRadio"] label:nth-child(2)');
    } catch (e) {
      console.log('Could not find navigation marker, trying alternative selector');
      // Fallback to the standard Streamlit selector
      await page.click('[data-testid="stRadio"] label:nth-child(2)');
    }
    
    await sleep(2000);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/02_run_simulation.png` });
    
    // Set simulation parameters
    console.log('Configuring simulation...');
    
    // Set simulation type to ABS (if needed - it's already the default)
    try {
      console.log('Looking for simulation type selector...');

      // First, check if the marker exists
      const markerExists = await page.evaluate(() => {
        return document.querySelector('[data-test-id="simulation-type-select-marker"]') !== null;
      });

      console.log(`Simulation type marker exists: ${markerExists}`);

      // Use a more general selector approach
      const selectboxes = await page.$$('[data-testid="stSelectbox"]');
      console.log(`Found ${selectboxes.length} selectboxes on page`);

      if (selectboxes.length > 0) {
        // Click the first selectbox (likely the simulation type)
        await selectboxes[0].click();
        await sleep(1000);

        // Try to click the first option (ABS)
        const options = await page.$$('[role="option"]');
        if (options.length > 0) {
          await options[0].click();
        }
      }
    } catch (selectError) {
      console.log('Error selecting simulation type, continuing anyway:', selectError.message);
    }

    await sleep(1000);
    
    // Adjust population size to 500 (default is 1000)
    try {
      console.log('Looking for population size slider...');

      // Find all sliders on the page
      const sliders = await page.$$('[data-testid="stSlider"]');
      console.log(`Found ${sliders.length} sliders on the page`);

      if (sliders.length > 0) {
        // Assume the first slider is the population size
        const populationSlider = sliders[0];

        // Find dimensions of the slider
        const sliderBounds = await populationSlider.boundingBox();
        console.log(`Slider dimensions: ${JSON.stringify(sliderBounds)}`);

        // Click at around 30% of the slider width to set approximately 500
        await page.mouse.click(
          sliderBounds.x + sliderBounds.width * 0.3,
          sliderBounds.y + sliderBounds.height / 2
        );
        console.log('Clicked slider at 30% position');
      } else {
        console.log('No sliders found, skipping population adjustment');
      }
    } catch (sliderError) {
      console.log('Error adjusting population slider:', sliderError.message);
    }
    
    await sleep(1000);
    
    // Run the simulation
    console.log('Running simulation...');
    try {
      // Look for the marker first
      const markerExists = await page.evaluate(() => {
        return document.querySelector('[data-test-id="run-simulation-btn-marker"]') !== null;
      });

      console.log(`Run simulation button marker exists: ${markerExists}`);

      // Find all primary buttons
      const buttons = await page.$$('.stButton button');
      console.log(`Found ${buttons.length} buttons on page`);

      let runButtonFound = false;

      // Try to find a button with "Run" or "Simulation" in its text
      for (const button of buttons) {
        const buttonText = await button.evaluate(el => el.textContent);
        console.log(`Button text: "${buttonText}"`);

        if (buttonText.includes('Run') || buttonText.includes('Simulation')) {
          console.log('Found Run Simulation button, clicking...');
          await button.click();
          runButtonFound = true;
          break;
        }
      }

      // If no specific button found, click the first button
      if (!runButtonFound && buttons.length > 0) {
        console.log('No specific Run button found, clicking first button');
        await buttons[0].click();
      }

    } catch (e) {
      console.log('Error interacting with Run Simulation button:', e.message);
      console.log('Trying alternative selector...');

      try {
        // Fallback to standard button selector
        await page.click('.stButton button');
      } catch (fallbackError) {
        console.log('Could not click any button:', fallbackError.message);
      }
    }
    
    // Wait for simulation to complete (looking for success message)
    console.log('Waiting for simulation to complete...');
    await page.waitForSelector('.stSuccess', { timeout: 60000 });
    await sleep(2000);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/03_simulation_results.png` });
    
    // Look for visual acuity plot
    console.log('Checking for visual acuity plot...');
    await page.waitForSelector('text/Visual Acuity Over Time', { timeout: 10000 });
    
    // Navigate to Patient Explorer
    console.log('Navigating to Patient Explorer...');
    await page.click('[data-testid="stRadio"] label:nth-child(3)');
    await sleep(2000);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/04_patient_explorer.png` });
    
    // Check if patient data is available
    const patientDataAvailable = await page.evaluate(() => {
      return !document.body.textContent.includes('No simulation data available');
    });
    
    if (patientDataAvailable) {
      console.log('Patient data available, exploring patients...');
      
      // Try to expand a patient detail section
      const detailExpanders = await page.$$('details');
      if (detailExpanders.length > 0) {
        // Click the first expander's summary element
        await detailExpanders[0].click();
        await sleep(1000);
        await page.screenshot({ path: `${SCREENSHOT_DIR}/05_patient_details.png` });
      }
    } else {
      console.log('No patient data available');
    }
    
    // Navigate to Reports section
    console.log('Navigating to Reports section...');
    await page.click('[data-testid="stRadio"] label:nth-child(4)');
    await sleep(2000);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/06_reports.png` });
    
    // Check About section
    console.log('Navigating to About section...');
    await page.click('[data-testid="stRadio"] label:nth-child(5)');
    await sleep(2000);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/07_about.png` });
    
    console.log('Test completed successfully!');
  } catch (error) {
    console.error('Test failed:', error);
    // Take a screenshot of the failure state if possible
    try {
      await page.screenshot({ path: `${SCREENSHOT_DIR}/error_state.png` });
      console.log('Saved error state screenshot');
    } catch (screenshotError) {
      console.error('Could not save error screenshot:', screenshotError);
    }
  } finally {
    try {
      await browser.close();
    } catch (closeError) {
      console.error('Error closing browser:', closeError);
    }
  }
}

// Run the test
runTest().catch(console.error);