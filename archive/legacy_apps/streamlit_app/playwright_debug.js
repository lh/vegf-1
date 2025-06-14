// playwright_debug.js - Simple Playwright script for debugging Streamlit app
const { chromium } = require('playwright');

/**
 * Interactive Playwright session for debugging Streamlit app
 * This script launches a visible browser and provides debugging capabilities
 */
async function debugStreamlitApp() {
  console.log('🚀 Starting Playwright debug session for Streamlit app...');
  
  // Launch browser in headed mode (visible) with devtools
  const browser = await chromium.launch({ 
    headless: false,  // Show the browser window
    devtools: true,   // Open Chrome DevTools
    slowMo: 100       // Slow down actions by 100ms for better visibility
  });
  
  try {
    const context = await browser.newContext({
      viewport: { width: 1280, height: 720 }
    });
    
    const page = await context.newPage();
    
    // Enable console logging
    page.on('console', msg => {
      console.log(`📄 Console [${msg.type()}]:`, msg.text());
    });
    
    // Log network errors
    page.on('requestfailed', request => {
      console.log(`❌ Request failed: ${request.url()}`);
    });
    
    // Navigate to Streamlit app
    console.log('📍 Navigating to http://localhost:8502...');
    try {
      await page.goto('http://localhost:8502', { 
        waitUntil: 'networkidle',
        timeout: 30000 
      });
      console.log('✅ Successfully loaded Streamlit app!');
    } catch (error) {
      console.error('❌ Failed to load Streamlit app:', error.message);
      console.log('💡 Make sure your Streamlit app is running on port 8502');
      console.log('   Run: streamlit run app.py');
    }
    
    // Wait a bit to see if the page loads
    await page.waitForTimeout(2000);
    
    // Take a screenshot
    const screenshotPath = 'logs/debug_screenshot.png';
    await page.screenshot({ 
      path: screenshotPath,
      fullPage: true 
    });
    console.log(`📸 Screenshot saved to: ${screenshotPath}`);
    
    // Get page title and URL
    const title = await page.title();
    const url = page.url();
    console.log(`📝 Page title: ${title}`);
    console.log(`🔗 Current URL: ${url}`);
    
    // Check for Streamlit elements
    console.log('\n🔍 Checking for Streamlit elements...');
    
    // Check for common Streamlit selectors
    const checks = [
      { selector: 'iframe[title="streamlit_app"]', name: 'Streamlit iframe' },
      { selector: '[data-testid="stApp"]', name: 'Streamlit app container' },
      { selector: 'h1', name: 'H1 heading' },
      { selector: '[data-testid="stSidebar"]', name: 'Sidebar' },
      { selector: 'button', name: 'Buttons' },
      { selector: 'a[href]', name: 'Links' }
    ];
    
    for (const check of checks) {
      const elements = await page.$$(check.selector);
      console.log(`   ${check.name}: ${elements.length} found`);
    }
    
    // Interactive debugging commands
    console.log('\n🛠️  Debugging session is active!');
    console.log('   Browser window is open with DevTools');
    console.log('   You can interact with the page manually');
    console.log('   Press Ctrl+C to exit when done\n');
    
    // Keep the browser open for manual interaction
    await new Promise(resolve => {
      process.on('SIGINT', () => {
        console.log('\n👋 Closing debugging session...');
        resolve();
      });
    });
    
  } catch (error) {
    console.error('❌ Error during debugging:', error);
  } finally {
    await browser.close();
    console.log('✅ Browser closed');
  }
}

// Run the debug session
debugStreamlitApp().catch(console.error);