// playwright_advanced_debug.js - Advanced debugging utilities for Streamlit
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

class StreamlitDebugger {
  constructor() {
    this.browser = null;
    this.page = null;
    this.context = null;
  }

  async initialize() {
    console.log('🚀 Initializing Streamlit Debugger...');
    
    this.browser = await chromium.launch({ 
      headless: false,
      devtools: true,
      args: ['--start-maximized']
    });
    
    this.context = await this.browser.newContext({
      viewport: null,  // Use full window size
      recordVideo: {
        dir: 'logs/videos/',
        size: { width: 1280, height: 720 }
      }
    });
    
    this.page = await this.context.newPage();
    
    // Set up event listeners
    this.setupEventListeners();
    
    return this;
  }

  setupEventListeners() {
    // Console messages
    this.page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      const location = msg.location();
      console.log(`[${type.toUpperCase()}] ${text}`);
      if (location.url) {
        console.log(`  at ${location.url}:${location.lineNumber}`);
      }
    });

    // Page errors
    this.page.on('pageerror', error => {
      console.error('❌ Page error:', error.message);
    });

    // Request failures
    this.page.on('requestfailed', request => {
      console.error(`❌ Request failed: ${request.url()} - ${request.failure().errorText}`);
    });

    // Dialog handling
    this.page.on('dialog', async dialog => {
      console.log(`📢 Dialog (${dialog.type()}): ${dialog.message()}`);
      await dialog.accept();
    });
  }

  async navigateToStreamlit(port = 8502) {
    const url = `http://localhost:${port}`;
    console.log(`📍 Navigating to ${url}...`);
    
    try {
      const response = await this.page.goto(url, { 
        waitUntil: 'networkidle',
        timeout: 30000 
      });
      
      console.log(`✅ Page loaded with status: ${response.status()}`);
      
      // Wait for Streamlit to initialize
      await this.page.waitForTimeout(2000);
      
      return true;
    } catch (error) {
      console.error('❌ Navigation failed:', error.message);
      return false;
    }
  }

  async captureDebugInfo(prefix = 'debug') {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const debugDir = 'logs/debug';
    
    // Create debug directory
    if (!fs.existsSync(debugDir)) {
      fs.mkdirSync(debugDir, { recursive: true });
    }
    
    console.log('📸 Capturing debug information...');
    
    // Screenshot
    const screenshotPath = path.join(debugDir, `${prefix}_${timestamp}.png`);
    await this.page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`  ✓ Screenshot: ${screenshotPath}`);
    
    // HTML content
    const htmlPath = path.join(debugDir, `${prefix}_${timestamp}.html`);
    const html = await this.page.content();
    fs.writeFileSync(htmlPath, html);
    console.log(`  ✓ HTML: ${htmlPath}`);
    
    // Page metrics
    const metrics = await this.page.metrics();
    const metricsPath = path.join(debugDir, `${prefix}_${timestamp}_metrics.json`);
    fs.writeFileSync(metricsPath, JSON.stringify(metrics, null, 2));
    console.log(`  ✓ Metrics: ${metricsPath}`);
    
    // Network log
    const requests = [];
    this.page.on('request', request => requests.push({
      url: request.url(),
      method: request.method(),
      headers: request.headers()
    }));
    
    return { screenshotPath, htmlPath, metricsPath };
  }

  async findStreamlitElements() {
    console.log('🔍 Analyzing Streamlit structure...');
    
    const elements = {
      app: await this.page.$$('[data-testid="stApp"]'),
      sidebar: await this.page.$$('[data-testid="stSidebar"]'),
      mainContent: await this.page.$$('[data-testid="stMain"]'),
      headers: await this.page.$$('h1, h2, h3'),
      buttons: await this.page.$$('button'),
      inputs: await this.page.$$('input'),
      selectboxes: await this.page.$$('select'),
      dataframes: await this.page.$$('[data-testid="stDataFrame"]'),
      plots: await this.page.$$('[data-testid="stPlot"]'),
      metrics: await this.page.$$('[data-testid="stMetric"]')
    };
    
    console.log('📊 Element counts:');
    for (const [name, els] of Object.entries(elements)) {
      console.log(`  ${name}: ${els.length}`);
    }
    
    return elements;
  }

  async interactiveMode() {
    console.log('\n🛠️  Interactive debugging mode activated!');
    console.log('Commands:');
    console.log('  screenshot - Take a screenshot');
    console.log('  elements - Find Streamlit elements');
    console.log('  debug - Capture full debug info');
    console.log('  reload - Reload the page');
    console.log('  exit - Close debugger');
    console.log('\nThe browser window is open. You can interact with it directly.');
    console.log('Press Ctrl+C to exit.\n');
    
    // Keep running until interrupted
    await new Promise(resolve => {
      process.on('SIGINT', resolve);
    });
  }

  async cleanup() {
    console.log('🧹 Cleaning up...');
    
    if (this.context) {
      const video = await this.page.video();
      if (video) {
        const videoPath = await video.path();
        console.log(`📹 Video saved: ${videoPath}`);
      }
    }
    
    if (this.browser) {
      await this.browser.close();
    }
    
    console.log('✅ Cleanup complete');
  }
}

// Main execution
async function main() {
  const debugger = new StreamlitDebugger();
  
  try {
    await debugger.initialize();
    
    const connected = await debugger.navigateToStreamlit();
    if (!connected) {
      console.log('💡 Make sure Streamlit is running: streamlit run app.py');
      return;
    }
    
    await debugger.findStreamlitElements();
    await debugger.captureDebugInfo('initial');
    
    await debugger.interactiveMode();
    
  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    await debugger.cleanup();
  }
}

// Run the debugger
main().catch(console.error);