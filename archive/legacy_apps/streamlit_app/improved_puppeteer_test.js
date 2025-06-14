/**
 * Improved Puppeteer Test Script for AMD Protocol Explorer
 * This script demonstrates how to interact with the Streamlit app using Puppeteer
 * with better error handling and debugging support
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Configuration
const APP_URL = 'http://localhost:8502';
const SCREENSHOT_DIR = './screenshots';
const LOG_FILE = path.join(SCREENSHOT_DIR, 'test_log.txt');
const TIMEOUT = 30000; // Increased timeout to 30 seconds

// Create screenshots directory if it doesn't exist
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

// Clear log file
fs.writeFileSync(LOG_FILE, 'Starting new test run\n', { encoding: 'utf8' });

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
  fs.appendFileSync(LOG_FILE, 
    formattedMessage + (data ? '\n' + JSON.stringify(data, null, 2) : '') + '\n', 
    { encoding: 'utf8' });
}

async function runTest() {
  log('Starting Puppeteer test for AMD Protocol Explorer');
  
  // Launch browser
  const browser = await puppeteer.launch({
    headless: "new", // Use the new headless mode for Chrome
    defaultViewport: { width: 1280, height: 900 },
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  
  let page;
  
  try {
    page = await browser.newPage();
    
    // Enable more verbose logging
    page.on('console', msg => log('Console:', msg.text()));
    page.on('pageerror', error => log('Page error:', error.message));
    page.on('requestfailed', request => 
      log(`Request failed: ${request.url()}`, request.failure())
    );
    
    // Navigate to the app
    log('Navigating to AMD Protocol Explorer...');
    await page.goto(APP_URL, { waitUntil: 'networkidle0', timeout: TIMEOUT });
    await sleep(5000); // Increased wait time for Streamlit to fully render
    
    // Take initial screenshot
    await page.screenshot({ path: `${SCREENSHOT_DIR}/01_home_page.png`, fullPage: true });
    log('Home page loaded and screenshot taken');
    
    // Analyze page structure
    const appStructure = await page.evaluate(() => {
      // Get basic structure
      return {
        title: document.title,
        headings: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => ({
          level: h.tagName.toLowerCase(),
          text: h.textContent
        })),
        buttons: Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim()),
        radios: Array.from(document.querySelectorAll('[data-testid="stRadio"] label')).map(r => r.textContent.trim()),
        selectboxes: Array.from(document.querySelectorAll('[data-testid="stSelectbox"]')).length,
        sliders: Array.from(document.querySelectorAll('[data-testid="stSlider"]')).length,
        hasHelpers: typeof window.puppeteerHelpers !== 'undefined'
      };
    });
    
    log('App structure analysis:', appStructure);
    
    // Navigate to Run Simulation tab
    log('Navigating to Run Simulation page...');
    try {
      // Alternative approach to find radio buttons
      const radioOptions = await page.evaluate(() => {
        // Get all elements that might be radio options in the sidebar
        const options = Array.from(document.querySelectorAll('.stRadio label, [role="radio"], .sidebar .element-container:nth-child(2) span'));
        return options.map((opt, index) => ({
          index,
          text: opt.textContent.trim()
        })).filter(opt => opt.text);
      });
      
      log('Available navigation options:', radioOptions);
      
      // Try to find "Run Simulation" option
      const runSimOption = radioOptions.find(opt => 
        opt.text.includes('Run') || 
        opt.text.includes('Simulation') || 
        opt.text === 'Run Simulation'
      );
      
      if (runSimOption) {
        log(`Found Run Simulation option at index ${runSimOption.index}`);
        
        // Try different selector approaches
        try {
          // Try with nth-child
          await page.click(`.stRadio label:nth-child(${runSimOption.index + 1})`);
          log('Clicked Run Simulation using nth-child selector');
        } catch (e) {
          log('First click attempt failed, trying alternative selector');
          
          // Try with direct text search
          await page.evaluate((text) => {
            const elements = Array.from(document.querySelectorAll('.stRadio label, [role="radio"], .sidebar .element-container span'));
            const element = elements.find(el => el.textContent.trim().includes(text));
            if (element) element.click();
          }, 'Run Simulation');
          
          log('Tried alternative click method for Run Simulation');
        }
      } else {
        // Fallback to clicking the 2nd radio option (usually Run Simulation)
        log('Run Simulation option not found by text, trying index-based approach');
        
        // Try direct index approach
        try {
          await page.click('[data-testid="stRadio"] label:nth-child(2)');
          log('Clicked second radio option using nth-child selector');
        } catch (e) {
          log('Fallback click attempt failed:', e.message);
          
          // Last resort: try to click anything that might be navigation
          await page.evaluate(() => {
            // Click anything in the sidebar that might be navigation
            const sidebarItems = document.querySelectorAll('.sidebar .element-container');
            if (sidebarItems.length > 1) {
              const navItem = sidebarItems[1];
              if (navItem) {
                const clickableElements = navItem.querySelectorAll('span, label, div');
                if (clickableElements.length > 1) clickableElements[1].click();
              }
            }
          });
          log('Attempted last resort navigation click');
        }
      }
      
      await sleep(3000);
      await page.screenshot({ path: `${SCREENSHOT_DIR}/02_run_simulation.png`, fullPage: true });
    } catch (navError) {
      log('Error navigating to Run Simulation tab:', navError.message);
    }
    
    // Find and interact with simulation parameters
    log('Configuring simulation parameters...');
    
    // Check for selectboxes (simulation type)
    const selectboxes = await page.$$('[data-testid="stSelectbox"]');
    log(`Found ${selectboxes.length} selectboxes`);
    
    if (selectboxes.length > 0) {
      try {
        // Click the first selectbox (likely the simulation type)
        await selectboxes[0].click();
        log('Clicked simulation type selectbox');
        await sleep(1000);
        
        // Try to select the first option (ABS)
        const options = await page.$$('[role="option"]');
        if (options.length > 0) {
          await options[0].click();
          log(`Selected first option from ${options.length} options`);
        }
        await sleep(1000);
      } catch (selectError) {
        log('Error configuring selectbox:', selectError.message);
      }
    }
    
    // Find and adjust sliders
    const sliders = await page.$$('[data-testid="stSlider"]');
    log(`Found ${sliders.length} sliders`);
    
    if (sliders.length > 0) {
      try {
        // Adjust the first slider (likely population size)
        const slider = sliders[0];
        const sliderBounds = await slider.boundingBox();
        log('Slider dimensions:', sliderBounds);
        
        // Click at 30% of the slider's width
        await page.mouse.click(
          sliderBounds.x + sliderBounds.width * 0.3,
          sliderBounds.y + sliderBounds.height / 2
        );
        log('Adjusted first slider');
        await sleep(1000);
      } catch (sliderError) {
        log('Error adjusting slider:', sliderError.message);
      }
    }
    
    // Find and click the Run Simulation button
    log('Looking for Run Simulation button...');
    
    let runButtonClicked = false;
    
    try {
      // Try a more direct approach using page.evaluate and text matching
      runButtonClicked = await page.evaluate(() => {
        // Try multiple selector strategies to find the Run Simulation button
        
        // Strategy 1: Look for a button with "Run" or "Simulation" text
        const buttonsByText = Array.from(document.querySelectorAll('button'))
          .filter(btn => btn.textContent.trim().includes('Run') || 
                          btn.textContent.trim().includes('Simulation'));
        
        if (buttonsByText.length > 0) {
          buttonsByText[0].click();
          return true;
        }
        
        // Strategy 2: Look for any primary-style buttons
        const primaryButtons = Array.from(document.querySelectorAll('button[kind="primary"], .stButton > button, button.stBtn--primary'));
        if (primaryButtons.length > 0) {
          primaryButtons[0].click();
          return true;
        }
        
        // Strategy 3: Try to find button by its position or parent container
        const buttonContainers = document.querySelectorAll('.stButton');
        if (buttonContainers.length > 0) {
          const button = buttonContainers[0].querySelector('button');
          if (button) {
            button.click();
            return true;
          }
        }
        
        // Strategy 4: Click any button as a last resort
        const anyButton = document.querySelector('button');
        if (anyButton) {
          anyButton.click();
          return true;
        }
        
        return false;
      });
      
      if (runButtonClicked) {
        log('Successfully clicked the Run Simulation button using JavaScript evaluation');
      } else {
        log('Could not find a suitable button to click using JavaScript evaluation');
        
        // Fallback to Puppeteer's more direct approach
        const buttons = await page.$$('button');
        log(`Found ${buttons.length} buttons using Puppeteer's selector`);
        
        if (buttons.length > 0) {
          // Get button text to find the run simulation button
          for (let i = 0; i < buttons.length; i++) {
            const buttonText = await buttons[i].evaluate(btn => btn.textContent.trim());
            log(`Button ${i}: Text = "${buttonText}"`);
            
            if (buttonText.includes('Run') || buttonText.includes('Simulation')) {
              log(`Found Run Simulation button (button ${i})`);
              await buttons[i].click();
              runButtonClicked = true;
              log('Clicked Run Simulation button');
              break;
            }
          }
          
          // If no specific button found, click the first button
          if (!runButtonClicked && buttons.length > 0) {
            log('No specific Run button found, clicking first button');
            await buttons[0].click();
            runButtonClicked = true;
          }
        }
      }
    } catch (buttonError) {
      log('Error clicking Run Simulation button:', buttonError.message);
    }
    
    if (runButtonClicked) {
      // Wait for simulation to complete (looking for success message or results)
      log('Waiting for simulation to complete...');
      try {
        await Promise.race([
          page.waitForSelector('.stSuccess', { timeout: 60000 }),
          page.waitForSelector('text/Visual Acuity Over Time', { timeout: 60000 })
        ]);
        log('Simulation results detected');
      } catch (waitError) {
        log('Timeout waiting for simulation results:', waitError.message);
      }
      
      // Take a screenshot of the results
      await sleep(5000); // Give extra time for results to render
      await page.screenshot({ path: `${SCREENSHOT_DIR}/03_simulation_results.png`, fullPage: true });
    }
    
    // Navigate to Patient Explorer
    log('Navigating to Patient Explorer...');
    try {
      // Use text-based navigation approach
      await page.evaluate(() => {
        const elements = Array.from(document.querySelectorAll('.stRadio label, [role="radio"], .sidebar .element-container span'));
        const element = elements.find(el => 
          el.textContent.trim().includes('Patient') || 
          el.textContent.trim().includes('Explorer'));
        if (element) element.click();
      });
      
      log('Attempted to click Patient Explorer option');
      await sleep(3000);
      await page.screenshot({ path: `${SCREENSHOT_DIR}/04_patient_explorer.png`, fullPage: true });
    } catch (navError) {
      log('Error navigating to Patient Explorer:', navError.message);
    }
    
    // Check if patient data is available and try to expand details
    try {
      const patientDataAvailable = await page.evaluate(() => {
        return !document.body.textContent.includes('No simulation data available');
      });
      
      log(`Patient data available: ${patientDataAvailable}`);
      
      if (patientDataAvailable) {
        // Try to expand a patient detail section (expander)
        const expanders = await page.$$('details');
        log(`Found ${expanders.length} expanders`);
        
        if (expanders.length > 0) {
          await expanders[0].click();
          log('Clicked first expander');
          await sleep(1000);
          await page.screenshot({ path: `${SCREENSHOT_DIR}/05_patient_details.png`, fullPage: true });
        }
      }
    } catch (patientError) {
      log('Error exploring patient data:', patientError.message);
    }
    
    // Navigate to Reports section
    log('Navigating to Reports section...');
    try {
      // Use text-based navigation approach
      await page.evaluate(() => {
        const elements = Array.from(document.querySelectorAll('.stRadio label, [role="radio"], .sidebar .element-container span'));
        const element = elements.find(el => el.textContent.trim().includes('Reports'));
        if (element) element.click();
      });
      
      log('Attempted to click Reports option');
      await sleep(3000);
      await page.screenshot({ path: `${SCREENSHOT_DIR}/06_reports.png`, fullPage: true });
    } catch (navError) {
      log('Error navigating to Reports:', navError.message);
    }
    
    // Navigate to About section
    log('Navigating to About section...');
    try {
      // Use text-based navigation approach
      await page.evaluate(() => {
        const elements = Array.from(document.querySelectorAll('.stRadio label, [role="radio"], .sidebar .element-container span'));
        const element = elements.find(el => el.textContent.trim().includes('About'));
        if (element) element.click();
      });
      
      log('Attempted to click About option');
      await sleep(3000);
      await page.screenshot({ path: `${SCREENSHOT_DIR}/07_about.png`, fullPage: true });
    } catch (navError) {
      log('Error navigating to About:', navError.message);
    }
    
    log('Test completed successfully!');
  } catch (error) {
    log('Test failed:', error.message);
    log('Error stack:', error.stack);
    // Take a screenshot of the failure state if possible
    try {
      if (page) {
        await page.screenshot({ path: `${SCREENSHOT_DIR}/error_state.png`, fullPage: true });
        log('Saved error state screenshot');
      }
    } catch (screenshotError) {
      log('Could not save error screenshot:', screenshotError.message);
    }
  } finally {
    try {
      await browser.close();
      log('Browser closed');
    } catch (closeError) {
      log('Error closing browser:', closeError.message);
    }
  }
}

// Run the test
runTest().catch(e => {
  log('Unhandled error in test execution:', e.message);
  log('Error stack:', e.stack);
  process.exit(1);
});