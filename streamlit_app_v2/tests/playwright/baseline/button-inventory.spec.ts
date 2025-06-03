import { test } from '@playwright/test';
import { ButtonInventory } from '../helpers/button-inventory';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Button Inventory - Baseline Documentation', () => {
  test('Create comprehensive button inventory', async ({ page }) => {
    // Create inventory instance
    const inventory = new ButtonInventory(page);

    // Scan all pages
    await inventory.scanAllPages();

    // Generate reports
    const markdownReport = inventory.generateReport();
    const jsonReport = inventory.toJSON();

    // Create reports directory if it doesn't exist
    const reportsDir = path.join(process.cwd(), 'tests', 'playwright', 'reports');
    if (!fs.existsSync(reportsDir)) {
      fs.mkdirSync(reportsDir, { recursive: true });
    }

    // Save reports
    fs.writeFileSync(
      path.join(reportsDir, 'button-inventory.md'),
      markdownReport
    );

    fs.writeFileSync(
      path.join(reportsDir, 'button-inventory.json'),
      JSON.stringify(jsonReport, null, 2)
    );

    console.log('Button inventory created successfully!');
    console.log(`Total buttons found: ${jsonReport.totalButtons}`);
    console.log('Reports saved to tests/playwright/reports/');
  });
});