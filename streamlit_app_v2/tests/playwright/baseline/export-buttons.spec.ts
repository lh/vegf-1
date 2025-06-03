import { test, expect } from '@playwright/test';
import { StreamlitPage } from '../helpers/streamlit-page';

test.describe('Export Buttons - Baseline', () => {
  test('Analysis Overview - Export buttons', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    // Navigate to Analysis Overview where export buttons are likely located
    await page.goto('/Analysis_Overview');
    await streamlit.waitForLoad();
    
    // Take baseline screenshot
    await streamlit.screenshot('baseline-export-buttons');
    
    // Common export formats to look for
    const exportFormats = ['PNG', 'SVG', 'JPEG', 'WebP', 'PDF', 'CSV'];
    const foundExportButtons = [];
    
    for (const format of exportFormats) {
      // Check various patterns
      const patterns = [
        format,
        `Export ${format}`,
        `Export as ${format}`,
        `Download ${format}`,
        `📥 ${format}`,
        `💾 ${format}`
      ];
      
      for (const pattern of patterns) {
        if (await streamlit.hasButton(pattern)) {
          foundExportButtons.push({
            format,
            label: pattern,
            properties: await streamlit.getButtonProperties(pattern)
          });
          break;
        }
      }
    }
    
    console.log('Found export buttons:', foundExportButtons);
    
    // Save export button inventory
    const fs = require('fs');
    fs.writeFileSync(
      'tests/playwright/reports/baseline-export-buttons.json',
      JSON.stringify(foundExportButtons, null, 2)
    );
  });

  test('Export button layout patterns', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    await page.goto('/Analysis_Overview');
    await streamlit.waitForLoad();
    
    // Look for buttons with export-related icons
    const exportIconButtons = await page.locator('button:has-text("📥"), button:has-text("💾"), button:has-text("⬇")').all();
    
    if (exportIconButtons.length > 0) {
      console.log(`Found ${exportIconButtons.length} buttons with export icons`);
      
      // Check if they're arranged in a row (common pattern)
      const positions = [];
      for (const button of exportIconButtons) {
        const box = await button.boundingBox();
        if (box) {
          positions.push({
            x: box.x,
            y: box.y,
            width: box.width,
            height: box.height
          });
        }
      }
      
      // Check if buttons are horizontally aligned
      if (positions.length > 1) {
        const yPositions = positions.map(p => p.y);
        const isHorizontallyAligned = Math.max(...yPositions) - Math.min(...yPositions) < 10;
        console.log('Export buttons horizontally aligned:', isHorizontallyAligned);
      }
      
      // Document the layout
      const fs = require('fs');
      fs.writeFileSync(
        'tests/playwright/reports/baseline-export-layout.json',
        JSON.stringify({ buttons: exportIconButtons.length, positions }, null, 2)
      );
    }
  });

  test('Export button click behavior', async ({ page, context }) => {
    const streamlit = new StreamlitPage(page);
    
    await page.goto('/Analysis_Overview');
    await streamlit.waitForLoad();
    
    // Set up download listener
    const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null);
    
    // Try to find and click an export button
    const exportButtons = await page.locator('button').filter({ hasText: /export|download|📥|💾/i }).all();
    
    if (exportButtons.length > 0) {
      // Click the first export button
      await exportButtons[0].click();
      
      // Wait a bit to see if download triggered
      const download = await downloadPromise;
      
      if (download) {
        console.log('Export triggered download:', await download.suggestedFilename());
        // Cancel the download for testing
        await download.cancel();
      } else {
        console.log('Export button clicked but no download triggered');
        // Take screenshot to see what happened
        await streamlit.screenshot('baseline-export-click-result');
      }
    }
  });
});