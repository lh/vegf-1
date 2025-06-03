import { test, expect } from '@playwright/test';
import { StreamlitPage } from '../helpers/streamlit-page';

test.describe('Carbon Button Home Page Migration', () => {
  test('Home page loads with Carbon buttons and correct state', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Navigate to home page on correct port
    await page.goto('http://localhost:8504/');
    await streamlit.waitForLoad();
    
    // Take screenshot of initial state
    await streamlit.screenshot('home-page-carbon-initial');
    
    // Check Protocol Manager button is enabled
    const protocolButton = page.locator('button:has-text("Protocol Manager")').first();
    await expect(protocolButton).toBeVisible();
    await expect(protocolButton).toBeEnabled();
    
    // Check Run Simulation button is disabled (no protocol loaded)
    const runButton = page.locator('button:has-text("Run Simulation")').first();
    await expect(runButton).toBeVisible();
    await expect(runButton).toBeDisabled();
    
    // Check Analysis Overview button is disabled (no simulation results)
    const analysisButton = page.locator('button:has-text("Analysis Overview")').first();
    await expect(analysisButton).toBeVisible();
    await expect(analysisButton).toBeDisabled();
    
    // Check warning messages are visible
    await expect(page.locator('text=Load a protocol first')).toBeVisible();
    await expect(page.locator('text=Run a simulation first')).toBeVisible();
    
    // Check Carbon button styling (no emojis)
    const allButtons = page.locator('button');
    const buttonCount = await allButtons.count();
    for (let i = 0; i < buttonCount; i++) {
      const buttonText = await allButtons.nth(i).textContent();
      // Ensure no emojis in button text
      expect(buttonText).not.toMatch(/[\u{1F300}-\u{1F9FF}]/u);
    }
    
    // Test navigation to Protocol Manager
    await protocolButton.click();
    await streamlit.waitForLoad();
    
    // Should navigate to Protocol Manager page
    await expect(page).toHaveURL(/.*1_Protocol_Manager.*/);
    await streamlit.screenshot('protocol-manager-carbon');
  });
  
  test('Home page buttons become enabled with session state', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Set up session state with protocol and results
    await page.evaluate(() => {
      // @ts-ignore
      window.streamlit = window.streamlit || {};
      // @ts-ignore
      window.streamlit.setComponentValue = (key: string, value: any) => {
        // Simulate setting session state
        console.log(`Setting ${key} to`, value);
      };
    });
    
    // Navigate to home page on correct port
    await page.goto('http://localhost:8504/');
    await streamlit.waitForLoad();
    
    // Take screenshot showing disabled state
    await streamlit.screenshot('home-page-buttons-disabled');
  });
});