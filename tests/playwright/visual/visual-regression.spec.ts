import { test, expect } from '@playwright/test';
import { StreamlitPage } from '../helpers/streamlit-page';

test.describe('Visual Regression Tests', () => {
  test('Capture all page visual baselines', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    const pages = [
      { name: 'home', url: '/' },
      { name: 'protocol-manager', url: '/Protocol_Manager' },
      { name: 'run-simulation', url: '/Run_Simulation' },
      { name: 'analysis-overview', url: '/Analysis_Overview' }
    ];
    
    for (const pageInfo of pages) {
      await page.goto(pageInfo.url);
      await streamlit.waitForLoad();
      
      // Full page screenshot
      await expect(page).toHaveScreenshot(`${pageInfo.name}-full.png`, {
        fullPage: true,
        animations: 'disabled',
      });
      
      // Sidebar screenshot if visible
      const sidebar = page.locator('[data-testid="stSidebar"]');
      if (await sidebar.isVisible()) {
        await expect(sidebar).toHaveScreenshot(`${pageInfo.name}-sidebar.png`);
      }
      
      // Main content area
      const mainContent = page.locator('[data-testid="stAppViewContainer"]');
      await expect(mainContent).toHaveScreenshot(`${pageInfo.name}-content.png`);
    }
  });

  test('Button visual states', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Go to a page with various button types
    await page.goto('/Protocol_Manager');
    await streamlit.waitForLoad();
    
    // Find different button types
    const buttonSelectors = [
      { selector: 'button:has-text("Save")', name: 'save-button' },
      { selector: 'button:has-text("Load")', name: 'load-button' },
      { selector: 'button:has-text("Delete")', name: 'delete-button' },
      { selector: 'button[type="primary"]', name: 'primary-button' },
      { selector: 'button:has-text("📥")', name: 'icon-button' }
    ];
    
    for (const { selector, name } of buttonSelectors) {
      const button = page.locator(selector).first();
      if (await button.isVisible().catch(() => false)) {
        // Normal state
        await expect(button).toHaveScreenshot(`${name}-normal.png`);
        
        // Hover state
        await button.hover();
        await page.waitForTimeout(100);
        await expect(button).toHaveScreenshot(`${name}-hover.png`);
        
        // Focus state
        await button.focus();
        await page.waitForTimeout(100);
        await expect(button).toHaveScreenshot(`${name}-focus.png`);
      }
    }
  });

  test('Export button group layouts', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    await page.goto('/Analysis_Overview');
    await streamlit.waitForLoad();
    
    // Look for export button containers
    const exportContainers = await page.locator('div').filter({ 
      has: page.locator('button:has-text("PNG"), button:has-text("SVG"), button:has-text("📥")') 
    }).all();
    
    if (exportContainers.length > 0) {
      for (let i = 0; i < exportContainers.length; i++) {
        await expect(exportContainers[i]).toHaveScreenshot(`export-group-${i}.png`);
      }
    }
  });

  test('Form layouts with buttons', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    await page.goto('/Protocol_Manager');
    await streamlit.waitForLoad();
    
    // Find forms
    const forms = await page.locator('form').all();
    
    for (let i = 0; i < forms.length; i++) {
      const form = forms[i];
      if (await form.isVisible()) {
        await expect(form).toHaveScreenshot(`form-${i}-complete.png`);
        
        // Also capture just the button area of the form
        const formButtons = await form.locator('button').all();
        if (formButtons.length > 0) {
          const buttonContainer = form.locator('div:has(button)').last();
          await expect(buttonContainer).toHaveScreenshot(`form-${i}-buttons.png`);
        }
      }
    }
  });
});