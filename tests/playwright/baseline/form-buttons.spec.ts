import { test, expect } from '@playwright/test';
import { StreamlitPage } from '../helpers/streamlit-page';

test.describe('Form Action Buttons - Baseline', () => {
  test('Protocol Manager - Save/Load/Delete buttons', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Navigate to Protocol Manager
    await page.goto('/Protocol_Manager');
    await streamlit.waitForLoad();
    
    // Take baseline screenshot
    await streamlit.screenshot('baseline-protocol-manager-forms');
    
    // Document Save button behavior
    if (await streamlit.hasButton('Save')) {
      const saveProps = await streamlit.getButtonProperties('Save');
      console.log('Save button properties:', saveProps);
    }
    
    // Document Load button behavior
    if (await streamlit.hasButton('Load')) {
      const loadProps = await streamlit.getButtonProperties('Load');
      console.log('Load button properties:', loadProps);
    }
    
    // Document Delete button behavior (danger action)
    if (await streamlit.hasButton('Delete')) {
      const deleteProps = await streamlit.getButtonProperties('Delete');
      console.log('Delete button properties:', deleteProps);
      
      // Verify it has danger styling (if any)
      const button = await streamlit.getButton('Delete');
      const classes = await button.getAttribute('class');
      // Document current danger button styling
    }
  });

  test('Run Simulation - Primary action button', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Navigate to Run Simulation page
    await page.goto('/Run_Simulation');
    await streamlit.waitForLoad();
    
    // Take baseline screenshot
    await streamlit.screenshot('baseline-run-simulation-actions');
    
    // Look for Run Simulation button
    const runButtonVariants = ['Run Simulation', '▶️ Run Simulation', 'Run', '▶️ Run'];
    let runButton = null;
    
    for (const variant of runButtonVariants) {
      if (await streamlit.hasButton(variant)) {
        runButton = variant;
        break;
      }
    }
    
    if (runButton) {
      // Document properties
      const props = await streamlit.getButtonProperties(runButton);
      
      // Check if it's full width
      const button = await streamlit.getButton(runButton);
      const box = await button.boundingBox();
      const pageWidth = await page.evaluate(() => window.innerWidth);
      
      console.log('Run button properties:', {
        ...props,
        isFullWidth: box ? (box.width / pageWidth) > 0.8 : false
      });
    }
  });

  test('Form submit behaviors', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Go to a page with forms (Protocol Manager likely has forms)
    await page.goto('/Protocol_Manager');
    await streamlit.waitForLoad();
    
    // Look for form submit buttons
    const formButtons = await page.locator('[data-testid="stFormSubmitButton"]').all();
    
    console.log(`Found ${formButtons.length} form submit buttons`);
    
    // Document each form button
    for (let i = 0; i < formButtons.length; i++) {
      const button = formButtons[i];
      const text = await button.textContent();
      const isVisible = await button.isVisible();
      const isEnabled = await button.isEnabled();
      
      console.log(`Form button ${i + 1}:`, {
        text,
        isVisible,
        isEnabled
      });
    }
    
    // Take screenshot of forms
    await streamlit.screenshot('baseline-form-buttons');
  });

  test('Button interaction states', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    await page.goto('/Protocol_Manager');
    await streamlit.waitForLoad();
    
    // Find an interactive button
    const buttons = await streamlit.getAllButtons();
    
    if (buttons.length > 0) {
      const firstButton = buttons[0];
      
      // Capture hover state
      await firstButton.hover();
      await page.waitForTimeout(100); // Brief pause for hover styles
      await streamlit.screenshot('baseline-button-hover-state');
      
      // Capture focus state
      await firstButton.focus();
      await page.waitForTimeout(100);
      await streamlit.screenshot('baseline-button-focus-state');
      
      // Document disabled state if any disabled buttons exist
      const disabledButtons = await page.locator('button:disabled').all();
      if (disabledButtons.length > 0) {
        await streamlit.screenshot('baseline-button-disabled-state');
      }
    }
  });
});