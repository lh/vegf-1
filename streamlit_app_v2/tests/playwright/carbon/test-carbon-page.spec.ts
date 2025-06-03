import { test } from '@playwright/test';
import { StreamlitPage } from '../helpers/streamlit-page';

test.describe('Carbon Button Test Page', () => {
  test('Test carbon button page loads and works', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Navigate to Carbon button test page
    await page.goto('/99_Carbon_Button_Test');
    await streamlit.waitForLoad();
    
    // Take screenshot of initial state
    await streamlit.screenshot('carbon-test-page-initial');
    
    // Toggle to use Carbon buttons
    const toggle = page.locator('input[type="checkbox"]').first();
    const isChecked = await toggle.isChecked();
    if (!isChecked) {
      await toggle.click();
      await streamlit.waitForLoad();
    }
    
    // Take screenshot with Carbon buttons
    await streamlit.screenshot('carbon-test-page-carbon-enabled');
    
    // Test clicking a Carbon button
    const primaryButton = page.locator('button:has-text("Primary Action")').first();
    if (await primaryButton.isVisible()) {
      await primaryButton.click();
      await streamlit.waitForLoad();
      await streamlit.screenshot('carbon-test-page-after-click');
    }
    
    // Toggle off to see old style
    await toggle.click();
    await streamlit.waitForLoad();
    await streamlit.screenshot('carbon-test-page-old-style');
  });
});