// playwright_debug_configurable.js - Configurable port for testing
const { chromium } = require('playwright');

// Get port from command line or use default
const PORT = process.argv[2] || 8503;  // Default to 8503, not 8502

/**
 * Interactive Playwright session for debugging Streamlit app
 * Usage: node playwright_debug_configurable.js [port]
 * Example: node playwright_debug_configurable.js 8503
 */
async function debugStreamlitApp(port = PORT) {
  console.log(`🚀 Starting Playwright debug session on port ${port}...`);
  console.log(`   (Your main app remains on port 8502)`);
  
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
    const url = `http://localhost:${port}`;
    console.log(`📍 Navigating to ${url}...`);
    
    try {
      await page.goto(url, { 
        waitUntil: 'networkidle',
        timeout: 30000 
      });
      console.log('✅ Successfully loaded page!');
    } catch (error) {
      console.error('❌ Failed to load page:', error.message);
      console.log(`\n💡 To test with a different Streamlit instance:`);
      console.log(`   1. Run: streamlit run app.py --server.port ${port}`);
      console.log(`   2. Or create a test app: streamlit run test_app.py --server.port ${port}`);
      console.log(`\n   Your main app on port 8502 is unaffected.`);
    }
    
    // Wait a bit to see if the page loads
    await page.waitForTimeout(2000);
    
    // Take a screenshot
    const screenshotPath = `logs/debug_port${port}_screenshot.png`;
    await page.screenshot({ 
      path: screenshotPath,
      fullPage: true 
    });
    console.log(`📸 Screenshot saved to: ${screenshotPath}`);
    
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