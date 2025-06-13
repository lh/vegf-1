import { test } from '@playwright/test';
import { StreamlitPage } from '../helpers/streamlit-page';

test.describe('Simple Baseline Screenshots', () => {
  test('Capture all pages', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Home page
    await page.goto('/');
    await streamlit.waitForLoad();
    await streamlit.screenshot('baseline-home');
    
    // Protocol Manager
    await page.goto('/Protocol_Manager');
    await streamlit.waitForLoad();
    await streamlit.screenshot('baseline-protocol-manager');
    
    // Run Simulation
    await page.goto('/Run_Simulation');
    await streamlit.waitForLoad();
    await streamlit.screenshot('baseline-run-simulation');
    
    // Analysis Overview
    await page.goto('/Analysis_Overview');
    await streamlit.waitForLoad();
    await streamlit.screenshot('baseline-analysis-overview');
  });

  test('Capture navigation buttons on home', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    await page.goto('/');
    await streamlit.waitForLoad();
    
    // Find the actual navigation buttons by their text content
    const protocolButton = page.locator('button:has-text("Protocol Manager")');
    const simulationButton = page.locator('button:has-text("Run Simulation")');
    const analysisButton = page.locator('button:has-text("Analysis")');
    
    // Take individual screenshots
    if (await protocolButton.isVisible()) {
      await protocolButton.screenshot({ 
        path: 'tests/playwright/screenshots/baseline-protocol-button.png' 
      });
    }
    
    if (await simulationButton.isVisible()) {
      await simulationButton.screenshot({ 
        path: 'tests/playwright/screenshots/baseline-simulation-button.png' 
      });
    }
    
    if (await analysisButton.isVisible()) {
      await analysisButton.screenshot({ 
        path: 'tests/playwright/screenshots/baseline-analysis-button.png' 
      });
    }
  });
});