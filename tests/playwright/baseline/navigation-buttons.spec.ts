import { test, expect } from '@playwright/test';
import { StreamlitPage } from '../helpers/streamlit-page';

test.describe('Navigation Buttons - Baseline', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    const streamlit = new StreamlitPage(page);
    await streamlit.waitForLoad();
  });

  test('Homepage navigation buttons', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Take baseline screenshot
    await streamlit.screenshot('baseline-homepage-navigation');

    // Check that main navigation buttons exist
    expect(await streamlit.hasButton('Protocol Manager')).toBeTruthy();
    expect(await streamlit.hasButton('Run Simulation')).toBeTruthy();
    expect(await streamlit.hasButton('Analysis Overview')).toBeTruthy();
  });

  test('Navigate to Protocol Manager', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Click navigation button
    await streamlit.clickButton('Protocol Manager');
    
    // Verify navigation occurred
    expect(page.url()).toContain('Protocol_Manager');
    
    // Take screenshot of destination
    await streamlit.screenshot('baseline-protocol-manager-page');
  });

  test('Navigate to Run Simulation', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Click navigation button
    await streamlit.clickButton('Run Simulation');
    
    // Verify navigation occurred
    expect(page.url()).toContain('Run_Simulation');
    
    // Take screenshot
    await streamlit.screenshot('baseline-run-simulation-page');
  });

  test('Navigate to Analysis Overview', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Click navigation button
    await streamlit.clickButton('Analysis Overview');
    
    // Verify navigation occurred
    expect(page.url()).toContain('Analysis_Overview');
    
    // Take screenshot
    await streamlit.screenshot('baseline-analysis-overview-page');
  });

  test('Sidebar navigation elements', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Check for sidebar navigation
    const sidebar = page.locator('[data-testid="stSidebar"]');
    await expect(sidebar).toBeVisible();
    
    // Take screenshot of sidebar
    await page.locator('[data-testid="stSidebar"]').screenshot({ 
      path: 'tests/playwright/screenshots/baseline-sidebar-navigation.png' 
    });
  });

  test('Navigation button visual properties', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Document current button styling
    const buttons = ['Protocol Manager', 'Run Simulation', 'Analysis Overview'];
    const properties = [];
    
    for (const buttonLabel of buttons) {
      const props = await streamlit.getButtonProperties(buttonLabel);
      properties.push(props);
    }
    
    // Save properties for comparison
    const fs = require('fs');
    fs.writeFileSync(
      'tests/playwright/reports/baseline-navigation-properties.json',
      JSON.stringify(properties, null, 2)
    );
  });
});