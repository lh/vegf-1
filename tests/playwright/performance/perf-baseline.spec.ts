import { test } from '@playwright/test';
import { StreamlitPage } from '../helpers/streamlit-page';

test.describe('Performance Baseline Tests', () => {
  test('Page load performance baseline', async ({ page }) => {
    const metrics: any[] = [];
    
    const pages = [
      { name: 'Home', url: '/' },
      { name: 'Protocol Manager', url: '/Protocol_Manager' },
      { name: 'Run Simulation', url: '/Run_Simulation' },
      { name: 'Analysis Overview', url: '/Analysis_Overview' }
    ];
    
    for (const pageInfo of pages) {
      // Clear cache for consistent measurements
      await page.context().clearCookies();
      
      // Start measuring
      const startTime = Date.now();
      
      await page.goto(pageInfo.url);
      
      // Wait for Streamlit to be ready
      const streamlit = new StreamlitPage(page);
      await streamlit.waitForLoad();
      
      const loadTime = Date.now() - startTime;
      
      // Get performance metrics
      const performanceMetrics = await page.evaluate(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        return {
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
          loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
          firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
          firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
        };
      });
      
      // Count buttons on page
      const buttonCount = await page.locator('button').count();
      
      metrics.push({
        page: pageInfo.name,
        url: pageInfo.url,
        loadTime,
        buttonCount,
        ...performanceMetrics
      });
    }
    
    // Save baseline metrics
    const fs = require('fs');
    fs.writeFileSync(
      'tests/playwright/reports/baseline-performance.json',
      JSON.stringify({
        timestamp: new Date().toISOString(),
        metrics
      }, null, 2)
    );
    
    console.log('Performance baseline established');
  });

  test('Button interaction performance', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    const interactionMetrics: any[] = [];
    
    await page.goto('/');
    await streamlit.waitForLoad();
    
    // Find clickable buttons
    const buttons = await streamlit.getAllButtons();
    
    // Test first 5 buttons to avoid long test times
    const testButtons = buttons.slice(0, 5);
    
    for (let i = 0; i < testButtons.length; i++) {
      const button = testButtons[i];
      const text = await button.textContent() || `Button ${i}`;
      
      // Measure click response time
      const startTime = Date.now();
      
      await button.click();
      
      // Wait for any response (new elements, navigation, etc.)
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
      
      const responseTime = Date.now() - startTime;
      
      interactionMetrics.push({
        button: text.substring(0, 50), // Truncate long text
        responseTime
      });
      
      // Go back to original page if navigated away
      if (!page.url().endsWith('/')) {
        await page.goto('/');
        await streamlit.waitForLoad();
      }
    }
    
    // Save interaction metrics
    const fs = require('fs');
    fs.writeFileSync(
      'tests/playwright/reports/baseline-button-interactions.json',
      JSON.stringify({
        timestamp: new Date().toISOString(),
        averageResponseTime: interactionMetrics.reduce((sum, m) => sum + m.responseTime, 0) / interactionMetrics.length,
        interactions: interactionMetrics
      }, null, 2)
    );
  });

  test('Memory usage baseline', async ({ page, context }) => {
    const streamlit = new StreamlitPage(page);
    
    // Enable Chrome DevTools Protocol for memory measurements
    const client = await context.newCDPSession(page);
    
    const memorySnapshots: any[] = [];
    
    // Take initial memory snapshot
    const initialMetrics = await client.send('Performance.getMetrics');
    memorySnapshots.push({
      stage: 'initial',
      metrics: initialMetrics.metrics
    });
    
    // Navigate through pages and measure memory
    const pages = [
      { name: 'Home', url: '/' },
      { name: 'Protocol Manager', url: '/Protocol_Manager' },
      { name: 'Run Simulation', url: '/Run_Simulation' },
      { name: 'Analysis Overview', url: '/Analysis_Overview' }
    ];
    
    for (const pageInfo of pages) {
      await page.goto(pageInfo.url);
      await streamlit.waitForLoad();
      
      // Let page settle
      await page.waitForTimeout(1000);
      
      const metrics = await client.send('Performance.getMetrics');
      memorySnapshots.push({
        stage: pageInfo.name,
        metrics: metrics.metrics
      });
    }
    
    // Save memory baseline
    const fs = require('fs');
    fs.writeFileSync(
      'tests/playwright/reports/baseline-memory.json',
      JSON.stringify({
        timestamp: new Date().toISOString(),
        snapshots: memorySnapshots
      }, null, 2)
    );
  });
});