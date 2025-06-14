// test_playwright_simple.js - Minimal test to verify Playwright works
const { chromium } = require('playwright');

(async () => {
  console.log('Testing Playwright connection to Streamlit...');
  
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    await page.goto('http://localhost:8502', { timeout: 10000 });
    console.log('✅ Successfully connected to Streamlit app!');
    
    const content = await page.content();
    console.log(`📄 Page content length: ${content.length} characters`);
    
    await page.screenshot({ path: 'logs/test_connection.png' });
    console.log('📸 Screenshot saved to logs/test_connection.png');
    
  } catch (error) {
    console.error('❌ Failed to connect:', error.message);
    console.log('\n💡 Troubleshooting tips:');
    console.log('1. Make sure Streamlit is running: streamlit run app.py');
    console.log('2. Check if port 8502 is being used');
    console.log('3. Try accessing http://localhost:8502 in your browser');
  } finally {
    await browser.close();
  }
})();