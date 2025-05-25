// playwright_streamlit.js
const { chromium } = require('playwright');

/**
 * Test the Streamlit application using Playwright
 */
async function testStreamlitApp() {
  let browser = null;
  try {
    console.log('Starting Playwright test for Streamlit app...');
    
    // Launch browser
    browser = await chromium.launch({ 
      headless: false,
      slowMo: 500 // Slow down actions for better visibility
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Navigate to Streamlit app
    console.log('Navigating to Streamlit app...');
    await page.goto('http://localhost:8502');
    
    // Wait for Streamlit to fully load
    console.log('Waiting for Streamlit app to load...');
    await page.waitForSelector('h1:has-text("APE: AMD Protocol Explorer")', { 
      timeout: 30000 
    });
    console.log('Streamlit app loaded successfully');
    
    // Take a screenshot of the main page
    console.log('Taking screenshot of main page...');
    await page.screenshot({ 
      path: 'logs/streamlit_main_page.png',
      fullPage: true 
    });
    
    // Take a screenshot of the sidebar
    console.log('Taking screenshot of sidebar...');
    await page.screenshot({ 
      path: 'logs/streamlit_sidebar.png',
      fullPage: true 
    });
    
    // Use more specific selectors for navigation
    console.log('Testing navigation...');
    
    // Find sidebar navigation elements
    const sidebarLinks = await page.$$('a[href]');
    console.log(`Found ${sidebarLinks.length} sidebar links`);
    
    // Navigate to Run Simulation page using the sidebar link
    console.log('Navigating to Run Simulation page...');
    const runSimLink = await page.getByRole('link', { name: /run simulation/i });
    if (runSimLink) {
      await runSimLink.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ 
        path: 'logs/streamlit_run_simulation.png',
        fullPage: true 
      });
    } else {
      console.log('Run Simulation link not found');
    }
    
    // Return to Dashboard using the sidebar link
    console.log('Returning to Dashboard...');
    const dashboardLink = await page.getByRole('link', { name: /dashboard/i });
    if (dashboardLink) {
      await dashboardLink.click();
      await page.waitForTimeout(2000);
      await page.screenshot({ 
        path: 'logs/streamlit_dashboard.png',
        fullPage: true 
      });
    } else {
      console.log('Dashboard link not found');
    }
    await page.waitForTimeout(1000);
    
    console.log('Navigation test completed successfully');
    
    // Take a final screenshot
    await page.screenshot({ 
      path: 'logs/streamlit_final.png',
      fullPage: true 
    });
    
    console.log('Screenshots saved in logs directory');
    
    return {
      success: true,
      message: 'Streamlit app test completed successfully'
    };
  } catch (error) {
    console.error('Error during Playwright test:', error);
    return {
      success: false,
      message: `Test failed: ${error.message}`,
      error
    };
  } finally {
    // Close the browser
    if (browser) {
      await browser.close();
    }
  }
}

// Run the test and report results
(async () => {
  const result = await testStreamlitApp();
  if (result.success) {
    console.log('✅ ' + result.message);
    process.exit(0);
  } else {
    console.error('❌ ' + result.message);
    process.exit(1);
  }
})();