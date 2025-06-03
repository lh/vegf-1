# Test-Driven Carbon Button Migration Plan (Improved)

## Overview
Use Playwright to create comprehensive tests for all existing button functionality BEFORE migration, ensuring no regressions during the Carbon button implementation.

## Why TDD for This Migration?
- **Zero Risk**: Every button behavior is captured before changes
- **Objective Metrics**: Performance and accessibility measured, not guessed
- **Safe Refactoring**: Tests ensure functionality remains intact
- **Living Documentation**: Tests document expected behavior permanently
- **Confidence**: Green tests = safe to deploy

## TDD Workflow
1. **Capture Current Behavior**: Write tests for all existing buttons
2. **Verify Tests Pass**: Ensure all tests pass with current implementation
3. **Migrate to Carbon**: Replace buttons while keeping tests green
4. **Enhance Tests**: Add new tests for Carbon-specific features
5. **Monitor**: Continuous testing catches future regressions

## Phase 0: Test Infrastructure Setup (Day 0)

### Prerequisites Check
```bash
# Verify Node.js version (need 16+)
node --version

# Verify Python version (need 3.8+)
python --version

# Check if npm is installed
npm --version
```

### Setup Playwright Test Framework

```bash
# Create package.json if it doesn't exist
npm init -y

# Install test dependencies
npm install -D @playwright/test
npm install -D typescript @types/node
npm install -D axe-playwright  # For accessibility testing

# Python dependencies
pip install pytest-playwright
pip install pytest-html  # For HTML test reports

# Install browsers (only Chromium needed for Streamlit)
npx playwright install chromium
npx playwright install-deps  # System dependencies
```

### Create Test Configuration

`playwright.config.ts`:
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  outputDir: './tests/e2e/test-results',
  timeout: 30000,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Streamlit apps should run tests serially
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'test-results.json' }],
    ['list'],
  ],
  use: {
    baseURL: 'http://localhost:8501',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'on-first-retry',
    // Streamlit-specific settings
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // Ensure consistent viewport for visual tests
        viewport: { width: 1280, height: 720 },
      },
    },
  ],
  webServer: {
    command: 'streamlit run APE.py --server.port 8501 --server.headless true',
    port: 8501,
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe',
  },
});
```

### Create Test Directory Structure
```bash
mkdir -p tests/e2e/{utils,baseline,migration,visual,performance,accessibility}
mkdir -p tests/e2e/test-results
mkdir -p tests/e2e/screenshots/{baseline,current}
```

### Create Base Test Utilities

`tests/e2e/utils/streamlit-helpers.ts`:
```typescript
import { Page, Locator, expect } from '@playwright/test';

export class StreamlitPage {
  constructor(public page: Page) {}

  async waitForLoad() {
    // Wait for Streamlit to be ready
    await this.page.waitForSelector('[data-testid="stApp"]', { state: 'visible' });
    // Wait for any pending network requests
    await this.page.waitForLoadState('networkidle');
    // Additional wait for Streamlit's internal rendering
    await this.page.waitForTimeout(1000);
  }

  async waitForRerun() {
    // Wait for Streamlit to process changes
    await this.page.waitForTimeout(500);
    await this.page.waitForLoadState('networkidle');
  }

  async clickButton(label: string, options?: { exact?: boolean }): Promise<void> {
    const button = this.page.getByRole('button', { 
      name: label, 
      exact: options?.exact ?? true 
    });
    await button.waitFor({ state: 'visible' });
    await button.click();
    await this.waitForRerun();
  }

  async clickButtonByTestId(testId: string): Promise<void> {
    const button = this.page.locator(`[data-testid="${testId}"]`);
    await button.waitFor({ state: 'visible' });
    await button.click();
    await this.waitForRerun();
  }

  async expectSuccessMessage(text: string) {
    // Streamlit success messages appear in specific containers
    const success = this.page.locator('.stSuccess').filter({ hasText: text });
    await expect(success).toBeVisible({ timeout: 5000 });
  }

  async expectErrorMessage(text: string) {
    const error = this.page.locator('.stError').filter({ hasText: text });
    await expect(error).toBeVisible({ timeout: 5000 });
  }

  async expectPageSwitch(expectedUrl: string) {
    await expect(this.page).toHaveURL(expectedUrl, { timeout: 5000 });
  }

  async fillInput(label: string, value: string) {
    const input = this.page.getByLabel(label);
    await input.fill(value);
  }

  async selectOption(label: string, value: string) {
    const select = this.page.getByLabel(label);
    await select.selectOption(value);
  }

  async getButtonCount(): Promise<number> {
    return await this.page.getByRole('button').count();
  }

  async getAllButtonLabels(): Promise<string[]> {
    const buttons = await this.page.getByRole('button').all();
    const labels: string[] = [];
    for (const button of buttons) {
      const label = await button.textContent();
      if (label) labels.push(label.trim());
    }
    return labels;
  }

  async checkButtonExists(label: string): Promise<boolean> {
    const button = this.page.getByRole('button', { name: label, exact: true });
    return await button.isVisible().catch(() => false);
  }

  async getButtonByPartialText(partialText: string): Promise<Locator> {
    return this.page.locator(`button:has-text("${partialText}")`);
  }
}

// Helper for feature flag management
export class FeatureFlags {
  constructor(private page: Page) {}

  async enableCarbonButtons() {
    await this.page.evaluate(() => {
      window.sessionStorage.setItem('USE_CARBON_BUTTONS', 'true');
    });
  }

  async disableCarbonButtons() {
    await this.page.evaluate(() => {
      window.sessionStorage.setItem('USE_CARBON_BUTTONS', 'false');
    });
  }

  async toggleCarbonButtons(enable: boolean) {
    if (enable) {
      await this.enableCarbonButtons();
    } else {
      await this.disableCarbonButtons();
    }
  }
}
```

### Create Button Inventory Generator

`tests/e2e/utils/button-inventory.ts`:
```typescript
import { test } from '@playwright/test';
import { StreamlitPage } from './streamlit-helpers';
import * as fs from 'fs';
import * as path from 'path';

export async function generateButtonInventory() {
  const inventory: Record<string, string[]> = {};
  
  test('Generate button inventory', async ({ page }) => {
    const app = new StreamlitPage(page);
    
    // Visit each page and collect buttons
    const pages = [
      { url: '/', name: 'Home' },
      { url: '/#/Protocol_Manager', name: 'Protocol Manager' },
      { url: '/#/Run_Simulation', name: 'Run Simulation' },
      { url: '/#/Analysis_Overview', name: 'Analysis Overview' },
    ];
    
    for (const pageInfo of pages) {
      await page.goto(pageInfo.url);
      await app.waitForLoad();
      
      const buttons = await app.getAllButtonLabels();
      inventory[pageInfo.name] = buttons;
    }
    
    // Save inventory
    const inventoryPath = path.join(process.cwd(), 'tests/e2e/button-inventory.json');
    fs.writeFileSync(inventoryPath, JSON.stringify(inventory, null, 2));
    
    console.log('Button inventory saved to:', inventoryPath);
    console.log('Total pages:', Object.keys(inventory).length);
    console.log('Total buttons:', Object.values(inventory).flat().length);
  });
}
```

## Phase 1: Capture Current Behavior (Day 1)

### Test Organization Strategy

Each test file should follow this structure:
1. **Descriptive test names** that explain the expected behavior
2. **Tags** for test categorization (@baseline, @migration, @visual, etc.)
3. **Proper setup and teardown**
4. **Clear assertions** with helpful error messages

### Enhanced Navigation Button Tests

`tests/e2e/baseline/navigation.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { StreamlitPage, FeatureFlags } from '../utils/streamlit-helpers';

test.describe('Navigation Buttons - Current Behavior @baseline', () => {
  let app: StreamlitPage;
  let flags: FeatureFlags;

  test.beforeEach(async ({ page }) => {
    app = new StreamlitPage(page);
    flags = new FeatureFlags(page);
    await flags.disableCarbonButtons(); // Ensure we're testing old buttons
    await page.goto('/');
    await app.waitForLoad();
  });

  test('Home button navigates to main page', async ({ page }) => {
    // Navigate away first
    await page.goto('/#/Protocol_Manager');
    await app.waitForLoad();
    
    // Verify we're not on home
    expect(page.url()).toContain('Protocol_Manager');
    
    // Look for home button with various possible formats
    const homeButton = await app.checkButtonExists('🏠 Home') 
      ? '🏠 Home' 
      : await app.checkButtonExists('Home') 
      ? 'Home' 
      : '🦍 Home';
    
    // Click home button
    await app.clickButton(homeButton);
    
    // Verify navigation
    await expect(page).toHaveURL('http://localhost:8501/');
    
    // Verify we're on the home page by checking for expected content
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('All navigation buttons are visible and clickable', async ({ page }) => {
    const expectedButtons = [
      { label: '📋 Protocol Manager', url: '/#/Protocol_Manager' },
      { label: '🚀 Run Simulation', url: '/#/Run_Simulation' },
      { label: '📊 Analysis Overview', url: '/#/Analysis_Overview' },
    ];

    for (const { label, url } of expectedButtons) {
      // Check button exists
      const exists = await app.checkButtonExists(label);
      expect(exists).toBe(true);
      
      // Click and verify navigation
      await app.clickButton(label);
      await expect(page).toHaveURL(url);
      
      // Navigate back home
      await page.goto('/');
      await app.waitForLoad();
    }
  });

  test('Navigation persists across page refreshes', async ({ page }) => {
    // Navigate to a specific page
    await app.clickButton('📊 Analysis Overview');
    await expect(page).toHaveURL('/#/Analysis_Overview');
    
    // Refresh the page
    await page.reload();
    await app.waitForLoad();
    
    // Should still be on the same page
    await expect(page).toHaveURL('/#/Analysis_Overview');
  });
});
```

### Enhanced Form Action Tests

`tests/e2e/baseline/protocol-manager.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { StreamlitPage, FeatureFlags } from '../utils/streamlit-helpers';
import * as path from 'path';

test.describe('Protocol Manager Actions - Current Behavior @baseline', () => {
  let app: StreamlitPage;
  let flags: FeatureFlags;

  test.beforeEach(async ({ page }) => {
    app = new StreamlitPage(page);
    flags = new FeatureFlags(page);
    await flags.disableCarbonButtons();
    await page.goto('/#/Protocol_Manager');
    await app.waitForLoad();
  });

  test('Save protocol button validates required fields', async ({ page }) => {
    // Try to save without filling required fields
    await app.clickButton('💾 Save Protocol');
    
    // Should show validation error
    await app.expectErrorMessage('Protocol name is required');
  });

  test('Save protocol button saves valid protocol', async ({ page }) => {
    // Fill protocol form with valid data
    await app.fillInput('Protocol Name', 'Test Protocol ' + Date.now());
    await app.fillInput('Initial Dose', '2.0');
    await app.selectOption('Frequency', 'Monthly');
    
    // Click save
    await app.clickButton('💾 Save Protocol');
    
    // Verify success
    await app.expectSuccessMessage('Protocol saved successfully');
    
    // Verify the saved protocol appears in the list
    const savedProtocol = page.locator('text=Test Protocol');
    await expect(savedProtocol).toBeVisible();
  });

  test('Load protocol button populates form', async ({ page }) => {
    // Ensure we have a protocol to load
    const protocolFile = 'eylea.yaml';
    
    // Select a protocol
    await app.selectOption('Select Protocol', protocolFile);
    
    // Click load
    await app.clickButton('📂 Load Protocol');
    
    // Verify form is populated
    const nameInput = page.getByLabel('Protocol Name');
    await expect(nameInput).not.toBeEmpty();
    
    // Verify success message
    await app.expectSuccessMessage('Protocol loaded');
  });

  test('Delete protocol button requires confirmation', async ({ page }) => {
    // Select a protocol to delete
    await app.selectOption('Select Protocol', 'test_protocol.yaml');
    
    // Click delete
    await app.clickButton('🗑️ Delete Protocol');
    
    // Verify confirmation dialog appears
    const confirmDialog = page.locator('text=Are you sure');
    await expect(confirmDialog).toBeVisible();
    
    // Should have confirm and cancel options
    await expect(page.getByRole('button', { name: 'Confirm' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
  });

  test('Form validation works correctly', async ({ page }) => {
    // Test various invalid inputs
    await app.fillInput('Initial Dose', '-1');
    await app.clickButton('💾 Save Protocol');
    await app.expectErrorMessage('Dose must be positive');
    
    await app.fillInput('Initial Dose', '999');
    await app.clickButton('💾 Save Protocol');
    await app.expectErrorMessage('Dose exceeds maximum');
  });
});
```

### Primary Action Tests with Timing

`tests/e2e/baseline/run-simulation.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { StreamlitPage, FeatureFlags } from '../utils/streamlit-helpers';

test.describe('Run Simulation Actions - Current Behavior @baseline', () => {
  let app: StreamlitPage;
  let flags: FeatureFlags;

  test.beforeEach(async ({ page }) => {
    app = new StreamlitPage(page);
    flags = new FeatureFlags(page);
    await flags.disableCarbonButtons();
    await page.goto('/#/Run_Simulation');
    await app.waitForLoad();
  });

  test('Run Simulation button starts simulation with progress', async ({ page }) => {
    // Set up small simulation for faster testing
    await app.fillInput('Number of Patients', '10');
    await app.fillInput('Simulation Years', '1');
    
    // Record start time
    const startTime = Date.now();
    
    // Click run
    await app.clickButton('▶️ Run Simulation');
    
    // Verify simulation starts
    const progressIndicator = page.locator('text=Running simulation');
    await expect(progressIndicator).toBeVisible();
    
    // Verify progress updates
    const progressBar = page.locator('[role="progressbar"]');
    if (await progressBar.isVisible()) {
      // Check that progress increases
      const initialProgress = await progressBar.getAttribute('aria-valuenow');
      await page.waitForTimeout(1000);
      const updatedProgress = await progressBar.getAttribute('aria-valuenow');
      expect(Number(updatedProgress)).toBeGreaterThan(Number(initialProgress));
    }
    
    // Wait for completion
    await expect(page.locator('text=Simulation complete')).toBeVisible({ 
      timeout: 60000 
    });
    
    // Record completion time
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    console.log(`Simulation completed in ${duration}ms`);
    
    // Verify results are displayed
    await expect(page.locator('text=Simulation Results')).toBeVisible();
  });

  test('Reset button clears all form inputs', async ({ page }) => {
    // Fill all inputs with non-default values
    await app.fillInput('Number of Patients', '500');
    await app.fillInput('Simulation Years', '10');
    await app.selectOption('Recruitment Mode', 'Constant Rate');
    
    // Click reset
    await app.clickButton('🔄 Reset');
    
    // Verify all inputs return to defaults
    const patientsInput = page.getByLabel('Number of Patients');
    await expect(patientsInput).toHaveValue('1000');
    
    const yearsInput = page.getByLabel('Simulation Years');
    await expect(yearsInput).toHaveValue('5');
    
    const modeSelect = page.getByLabel('Recruitment Mode');
    await expect(modeSelect).toHaveValue('Fixed Total');
  });

  test('Stop button interrupts running simulation', async ({ page }) => {
    // Start a long simulation
    await app.fillInput('Number of Patients', '10000');
    await app.fillInput('Simulation Years', '10');
    
    await app.clickButton('▶️ Run Simulation');
    
    // Wait for simulation to start
    await expect(page.locator('text=Running simulation')).toBeVisible();
    
    // Stop button should appear
    const stopButton = await app.getButtonByPartialText('Stop');
    await expect(stopButton).toBeVisible();
    
    // Click stop
    await stopButton.click();
    
    // Verify simulation stopped
    await expect(page.locator('text=Simulation stopped')).toBeVisible();
  });
});
```

### Export Button Tests with File Validation

`tests/e2e/baseline/analysis-export.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { StreamlitPage, FeatureFlags } from '../utils/streamlit-helpers';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Export Actions - Current Behavior @baseline', () => {
  let app: StreamlitPage;
  let flags: FeatureFlags;

  test.beforeEach(async ({ page }) => {
    app = new StreamlitPage(page);
    flags = new FeatureFlags(page);
    await flags.disableCarbonButtons();
    
    // Navigate to analysis page
    await page.goto('/#/Analysis_Overview');
    await app.waitForLoad();
    
    // Ensure we have data to export by checking session state
    const hasData = await page.evaluate(() => {
      return window.sessionStorage.getItem('simulation_results') !== null;
    });
    
    if (!hasData) {
      // Load sample data if needed
      await page.evaluate(() => {
        window.sessionStorage.setItem('simulation_results', JSON.stringify({
          patients: 100,
          duration: 5,
          data: [] // Minimal data for testing
        }));
      });
      await page.reload();
      await app.waitForLoad();
    }
  });

  const exportFormats = [
    { button: '📥 PNG', extension: '.png', mimeType: 'image/png' },
    { button: '📥 SVG', extension: '.svg', mimeType: 'image/svg+xml' },
    { button: '📥 JPEG', extension: '.jpeg', mimeType: 'image/jpeg' },
    { button: '📥 WebP', extension: '.webp', mimeType: 'image/webp' },
  ];

  for (const format of exportFormats) {
    test(`Export ${format.extension} button downloads correct file`, async ({ page }) => {
      // Set up download promise before clicking
      const downloadPromise = page.waitForEvent('download');
      
      // Click export button
      await app.clickButton(format.button);
      
      // Wait for download
      const download = await downloadPromise;
      
      // Verify filename
      const filename = download.suggestedFilename();
      expect(filename).toContain(format.extension);
      
      // Save and verify file
      const downloadPath = path.join('tests/e2e/downloads', filename);
      await download.saveAs(downloadPath);
      
      // Verify file exists and has content
      const stats = fs.statSync(downloadPath);
      expect(stats.size).toBeGreaterThan(0);
      
      // Clean up
      fs.unlinkSync(downloadPath);
    });
  }

  test('Export data button downloads CSV with correct structure', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download');
    
    await app.clickButton('💾 Export Data');
    
    const download = await downloadPromise;
    const filename = download.suggestedFilename();
    expect(filename).toContain('.csv');
    
    // Save and read CSV
    const downloadPath = path.join('tests/e2e/downloads', filename);
    await download.saveAs(downloadPath);
    
    const csvContent = fs.readFileSync(downloadPath, 'utf-8');
    
    // Verify CSV structure
    const lines = csvContent.split('\n');
    expect(lines.length).toBeGreaterThan(1); // Header + data
    
    const headers = lines[0].split(',');
    expect(headers).toContain('patient_id');
    expect(headers).toContain('time');
    
    // Clean up
    fs.unlinkSync(downloadPath);
  });
});
```

### Enhanced Visual Regression Tests

`tests/e2e/visual/visual-regression.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { StreamlitPage, FeatureFlags } from '../utils/streamlit-helpers';

test.describe('Visual Regression - Current Buttons @visual @baseline', () => {
  let app: StreamlitPage;
  let flags: FeatureFlags;

  test.beforeEach(async ({ page }) => {
    app = new StreamlitPage(page);
    flags = new FeatureFlags(page);
    await flags.disableCarbonButtons();
    
    // Set consistent viewport
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('Navigation area visual baseline', async ({ page }) => {
    await page.goto('/');
    await app.waitForLoad();
    
    // Wait for any animations to complete
    await page.waitForTimeout(500);
    
    // Capture full navigation area
    await expect(page).toHaveScreenshot('navigation-full-baseline.png', {
      fullPage: false,
      clip: { x: 0, y: 0, width: 1280, height: 200 }
    });
    
    // Capture individual navigation buttons
    const navButtons = await page.locator('button').filter({ 
      hasText: /Protocol Manager|Run Simulation|Analysis Overview/ 
    }).all();
    
    for (let i = 0; i < navButtons.length; i++) {
      await expect(navButtons[i]).toHaveScreenshot(`nav-button-${i}-baseline.png`);
    }
  });

  test('Form buttons visual baseline', async ({ page }) => {
    await page.goto('/#/Protocol_Manager');
    await app.waitForLoad();
    
    // Capture form area
    const formArea = page.locator('section').filter({ has: page.locator('form') });
    await expect(formArea).toHaveScreenshot('form-area-baseline.png');
    
    // Capture individual form buttons
    const saveButton = page.getByRole('button', { name: /Save/ });
    await expect(saveButton).toHaveScreenshot('save-button-baseline.png');
    
    const loadButton = page.getByRole('button', { name: /Load/ });
    await expect(loadButton).toHaveScreenshot('load-button-baseline.png');
    
    const deleteButton = page.getByRole('button', { name: /Delete/ });
    await expect(deleteButton).toHaveScreenshot('delete-button-baseline.png');
  });

  test('Button hover states', async ({ page }) => {
    await page.goto('/');
    await app.waitForLoad();
    
    const button = page.getByRole('button').first();
    
    // Normal state
    await expect(button).toHaveScreenshot('button-normal-state.png');
    
    // Hover state
    await button.hover();
    await page.waitForTimeout(100); // Wait for hover transition
    await expect(button).toHaveScreenshot('button-hover-state.png');
  });

  test('Button focus states', async ({ page }) => {
    await page.goto('/');
    await app.waitForLoad();
    
    const button = page.getByRole('button').first();
    
    // Focus state
    await button.focus();
    await page.waitForTimeout(100); // Wait for focus transition
    await expect(button).toHaveScreenshot('button-focus-state.png');
  });
});
```

## Phase 2: Migration Test Strategy (Day 2-14)

### Enhanced Migration Test Runner

`tests/e2e/utils/migration-helper.ts`:
```typescript
import { Page, expect } from '@playwright/test';
import { StreamlitPage, FeatureFlags } from './streamlit-helpers';

export interface MigrationTestResult {
  feature: string;
  oldButton: {
    success: boolean;
    responseTime: number;
    error?: string;
  };
  newButton: {
    success: boolean;
    responseTime: number;
    error?: string;
  };
  visualDifference: boolean;
  functionallyEquivalent: boolean;
}

export class MigrationTester {
  private app: StreamlitPage;
  private flags: FeatureFlags;
  private results: MigrationTestResult[] = [];

  constructor(private page: Page) {
    this.app = new StreamlitPage(page);
    this.flags = new FeatureFlags(page);
  }

  async testButtonMigration(
    feature: string,
    testFunction: () => Promise<void>
  ): Promise<MigrationTestResult> {
    const result: MigrationTestResult = {
      feature,
      oldButton: { success: false, responseTime: 0 },
      newButton: { success: false, responseTime: 0 },
      visualDifference: false,
      functionallyEquivalent: false,
    };

    // Test with old buttons
    await this.flags.disableCarbonButtons();
    await this.page.reload();
    await this.app.waitForLoad();

    const oldStart = Date.now();
    try {
      await testFunction();
      result.oldButton.success = true;
    } catch (error) {
      result.oldButton.error = error.message;
    }
    result.oldButton.responseTime = Date.now() - oldStart;

    // Test with new buttons
    await this.flags.enableCarbonButtons();
    await this.page.reload();
    await this.app.waitForLoad();

    const newStart = Date.now();
    try {
      await testFunction();
      result.newButton.success = true;
    } catch (error) {
      result.newButton.error = error.message;
    }
    result.newButton.responseTime = Date.now() - newStart;

    // Determine functional equivalence
    result.functionallyEquivalent = 
      result.oldButton.success === result.newButton.success;

    this.results.push(result);
    return result;
  }

  async compareVisual(elementSelector: string, testName: string) {
    // Capture with old buttons
    await this.flags.disableCarbonButtons();
    await this.page.reload();
    await this.app.waitForLoad();
    
    const oldElement = this.page.locator(elementSelector);
    await oldElement.screenshot({ 
      path: `tests/e2e/screenshots/comparison/${testName}-old.png` 
    });

    // Capture with new buttons
    await this.flags.enableCarbonButtons();
    await this.page.reload();
    await this.app.waitForLoad();
    
    const newElement = this.page.locator(elementSelector);
    await newElement.screenshot({ 
      path: `tests/e2e/screenshots/comparison/${testName}-new.png` 
    });
  }

  async generateReport(): Promise<string> {
    const totalTests = this.results.length;
    const successfulMigrations = this.results.filter(r => r.functionallyEquivalent).length;
    const averageSpeedChange = this.calculateAverageSpeedChange();

    const report = `
# Migration Test Report

## Summary
- Total Features Tested: ${totalTests}
- Successful Migrations: ${successfulMigrations}
- Failed Migrations: ${totalTests - successfulMigrations}
- Average Speed Change: ${averageSpeedChange.toFixed(2)}%

## Detailed Results
${this.results.map(r => this.formatResult(r)).join('\n')}

## Recommendations
${this.generateRecommendations()}
`;

    return report;
  }

  private calculateAverageSpeedChange(): number {
    const changes = this.results.map(r => 
      ((r.newButton.responseTime - r.oldButton.responseTime) / r.oldButton.responseTime) * 100
    );
    return changes.reduce((a, b) => a + b, 0) / changes.length;
  }

  private formatResult(result: MigrationTestResult): string {
    const status = result.functionallyEquivalent ? '✅' : '❌';
    const speedChange = ((result.newButton.responseTime - result.oldButton.responseTime) / 
                        result.oldButton.responseTime * 100).toFixed(2);
    
    return `
### ${status} ${result.feature}
- Old Button: ${result.oldButton.success ? 'Success' : 'Failed'} (${result.oldButton.responseTime}ms)
- New Button: ${result.newButton.success ? 'Success' : 'Failed'} (${result.newButton.responseTime}ms)
- Speed Change: ${speedChange}%
${result.oldButton.error ? `- Old Error: ${result.oldButton.error}` : ''}
${result.newButton.error ? `- New Error: ${result.newButton.error}` : ''}
`;
  }

  private generateRecommendations(): string {
    const failed = this.results.filter(r => !r.functionallyEquivalent);
    if (failed.length === 0) {
      return '✅ All features successfully migrated!';
    }

    return `
⚠️ ${failed.length} features need attention:
${failed.map(f => `- ${f.feature}: ${f.newButton.error || 'Unknown issue'}`).join('\n')}
`;
  }
}
```

### Progressive Migration Tests

`tests/e2e/migration/progressive-migration.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { MigrationTester } from '../utils/migration-helper';
import * as fs from 'fs';

test.describe('Progressive Migration Tests @migration', () => {
  let tester: MigrationTester;

  test.beforeEach(async ({ page }) => {
    tester = new MigrationTester(page);
  });

  test.afterAll(async () => {
    // Generate and save migration report
    const report = await tester.generateReport();
    fs.writeFileSync('tests/e2e/migration-report.md', report);
  });

  test('Navigation buttons maintain functionality', async ({ page }) => {
    const navTests = [
      {
        name: 'Home Navigation',
        test: async () => {
          await page.goto('/#/Protocol_Manager');
          await page.getByRole('button', { name: /Home/ }).click();
          await expect(page).toHaveURL('/');
        }
      },
      {
        name: 'Protocol Manager Navigation',
        test: async () => {
          await page.goto('/');
          await page.getByRole('button', { name: /Protocol Manager/ }).click();
          await expect(page).toHaveURL('/#/Protocol_Manager');
        }
      },
      {
        name: 'Run Simulation Navigation',
        test: async () => {
          await page.goto('/');
          await page.getByRole('button', { name: /Run Simulation/ }).click();
          await expect(page).toHaveURL('/#/Run_Simulation');
        }
      },
    ];

    for (const navTest of navTests) {
      await tester.testButtonMigration(navTest.name, navTest.test);
    }
  });

  test('Form actions preserve behavior', async ({ page }) => {
    await page.goto('/#/Protocol_Manager');
    
    const result = await tester.testButtonMigration(
      'Protocol Save Action',
      async () => {
        // Fill form
        await page.getByLabel('Protocol Name').fill('Test Migration Protocol');
        await page.getByLabel('Initial Dose').fill('2.0');
        
        // Click save
        await page.getByRole('button', { name: /Save/ }).click();
        
        // Verify success
        await expect(page.locator('.stSuccess')).toBeVisible();
      }
    );

    expect(result.functionallyEquivalent).toBe(true);
  });

  test('Export functionality unchanged', async ({ page }) => {
    await page.goto('/#/Analysis_Overview');
    
    // Ensure data exists
    await page.evaluate(() => {
      window.sessionStorage.setItem('simulation_results', JSON.stringify({ test: true }));
    });
    
    const formats = ['PNG', 'SVG', 'JPEG', 'WebP'];
    
    for (const format of formats) {
      const result = await tester.testButtonMigration(
        `Export ${format}`,
        async () => {
          const downloadPromise = page.waitForEvent('download');
          await page.getByRole('button', { name: new RegExp(format) }).click();
          const download = await downloadPromise;
          expect(download.suggestedFilename()).toContain(format.toLowerCase());
        }
      );
      
      expect(result.functionallyEquivalent).toBe(true);
    }
  });

  test('Visual comparison of button styles', async ({ page }) => {
    await page.goto('/');
    
    // Compare navigation area
    await tester.compareVisual('header', 'navigation-area');
    
    // Compare individual buttons
    await page.goto('/#/Protocol_Manager');
    await tester.compareVisual('button:has-text("Save")', 'save-button');
    await tester.compareVisual('button:has-text("Load")', 'load-button');
  });
});
```

### Enhanced Accessibility Tests

`tests/e2e/accessibility/accessibility-improvements.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y, getViolations } from 'axe-playwright';
import { FeatureFlags } from '../utils/streamlit-helpers';

test.describe('Accessibility Improvements @accessibility', () => {
  let flags: FeatureFlags;

  test.beforeEach(async ({ page }) => {
    flags = new FeatureFlags(page);
  });

  test('Overall accessibility score improves', async ({ page }) => {
    await page.goto('/');
    
    // Test old buttons
    await flags.disableCarbonButtons();
    await page.reload();
    await injectAxe(page);
    
    const oldViolations = await getViolations(page);
    const oldCritical = oldViolations.filter(v => v.impact === 'critical').length;
    const oldSerious = oldViolations.filter(v => v.impact === 'serious').length;
    
    // Test new buttons
    await flags.enableCarbonButtons();
    await page.reload();
    await injectAxe(page);
    
    const newViolations = await getViolations(page);
    const newCritical = newViolations.filter(v => v.impact === 'critical').length;
    const newSerious = newViolations.filter(v => v.impact === 'serious').length;
    
    // Should have fewer or equal violations
    expect(newCritical).toBeLessThanOrEqual(oldCritical);
    expect(newSerious).toBeLessThanOrEqual(oldSerious);
    
    // Generate detailed report
    console.log(`
Accessibility Comparison:
Old Buttons: ${oldViolations.length} violations (${oldCritical} critical, ${oldSerious} serious)
New Buttons: ${newViolations.length} violations (${newCritical} critical, ${newSerious} serious)
Improvement: ${oldViolations.length - newViolations.length} fewer violations
`);
  });

  test('All buttons have proper ARIA attributes', async ({ page }) => {
    await page.goto('/');
    await flags.enableCarbonButtons();
    await page.reload();
    
    const buttons = await page.getByRole('button').all();
    
    for (const button of buttons) {
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      const ariaDescribedBy = await button.getAttribute('aria-describedby');
      
      // Every button should have either visible text or aria-label
      if (!text || text.trim() === '') {
        expect(ariaLabel).toBeTruthy();
        expect(ariaLabel!.length).toBeGreaterThan(0);
      }
      
      // Buttons with icons should have descriptive labels
      const hasIcon = await button.locator('svg, img, i').count() > 0;
      if (hasIcon && (!text || text.trim() === '')) {
        expect(ariaLabel).toMatch(/[A-Za-z]+/); // Should contain actual words
      }
    }
  });

  test('Keyboard navigation works correctly', async ({ page }) => {
    await page.goto('/');
    await flags.enableCarbonButtons();
    await page.reload();
    
    // Start from body
    await page.locator('body').focus();
    
    // Tab through all buttons
    const buttons = await page.getByRole('button').all();
    for (let i = 0; i < buttons.length; i++) {
      await page.keyboard.press('Tab');
      
      // Check that focus is visible
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).toBe('BUTTON');
      
      // Verify focus indicator is visible (outline or other visual indicator)
      const focusVisible = await page.evaluate(() => {
        const active = document.activeElement as HTMLElement;
        const styles = window.getComputedStyle(active);
        return styles.outlineWidth !== '0px' || styles.boxShadow !== 'none';
      });
      expect(focusVisible).toBe(true);
    }
  });

  test('Color contrast meets WCAG standards', async ({ page }) => {
    await page.goto('/');
    await flags.enableCarbonButtons();
    await page.reload();
    await injectAxe(page);
    
    // Check specifically for color contrast violations
    const violations = await getViolations(page, null, {
      runOnly: ['color-contrast']
    });
    
    expect(violations).toHaveLength(0);
  });

  test('Screen reader announcements work correctly', async ({ page }) => {
    await page.goto('/#/Run_Simulation');
    await flags.enableCarbonButtons();
    await page.reload();
    
    // Set up ARIA live region listener
    await page.evaluate(() => {
      window.ariaAnnouncements = [];
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'childList') {
            const target = mutation.target as HTMLElement;
            if (target.getAttribute('aria-live') || target.getAttribute('role') === 'alert') {
              window.ariaAnnouncements.push(target.textContent);
            }
          }
        });
      });
      observer.observe(document.body, { childList: true, subtree: true });
    });
    
    // Trigger an action that should announce
    await page.getByRole('button', { name: /Run Simulation/ }).click();
    
    // Check for announcements
    await page.waitForTimeout(1000);
    const announcements = await page.evaluate(() => window.ariaAnnouncements);
    
    expect(announcements.length).toBeGreaterThan(0);
    expect(announcements.some(a => a?.includes('simulation'))).toBe(true);
  });
});
```

### Performance Monitoring Tests

`tests/e2e/performance/performance-metrics.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { FeatureFlags } from '../utils/streamlit-helpers';

interface PerformanceMetrics {
  pageLoadTime: number;
  firstButtonInteractive: number;
  memoryUsage: number;
  buttonRenderCount: number;
}

test.describe('Performance Metrics @performance', () => {
  let flags: FeatureFlags;

  test.beforeEach(async ({ page }) => {
    flags = new FeatureFlags(page);
  });

  test('Page load performance comparison', async ({ page }) => {
    const metrics: { old: PerformanceMetrics, new: PerformanceMetrics } = {
      old: { pageLoadTime: 0, firstButtonInteractive: 0, memoryUsage: 0, buttonRenderCount: 0 },
      new: { pageLoadTime: 0, firstButtonInteractive: 0, memoryUsage: 0, buttonRenderCount: 0 }
    };

    // Measure old buttons
    await flags.disableCarbonButtons();
    await page.goto('/', { waitUntil: 'networkidle' });
    
    metrics.old = await page.evaluate(() => {
      const perf = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        pageLoadTime: perf.loadEventEnd - perf.fetchStart,
        firstButtonInteractive: perf.domInteractive - perf.fetchStart,
        memoryUsage: (performance as any).memory?.usedJSHeapSize || 0,
        buttonRenderCount: document.querySelectorAll('button').length
      };
    });

    // Measure new buttons
    await flags.enableCarbonButtons();
    await page.goto('/', { waitUntil: 'networkidle' });
    
    metrics.new = await page.evaluate(() => {
      const perf = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        pageLoadTime: perf.loadEventEnd - perf.fetchStart,
        firstButtonInteractive: perf.domInteractive - perf.fetchStart,
        memoryUsage: (performance as any).memory?.usedJSHeapSize || 0,
        buttonRenderCount: document.querySelectorAll('button').length
      };
    });

    // Assertions
    expect(metrics.new.pageLoadTime - metrics.old.pageLoadTime).toBeLessThan(100);
    expect(metrics.new.firstButtonInteractive - metrics.old.firstButtonInteractive).toBeLessThan(50);
    
    // Log detailed metrics
    console.log('Performance Comparison:', JSON.stringify(metrics, null, 2));
  });

  test('Button interaction performance', async ({ page }) => {
    await page.goto('/');
    
    const measureButtonClick = async (buttonText: string) => {
      const metrics = await page.evaluate((text) => {
        return new Promise<number>((resolve) => {
          const button = Array.from(document.querySelectorAll('button'))
            .find(b => b.textContent?.includes(text));
          
          if (!button) {
            resolve(-1);
            return;
          }
          
          const startTime = performance.now();
          button.addEventListener('click', () => {
            const endTime = performance.now();
            resolve(endTime - startTime);
          }, { once: true });
          
          button.click();
        });
      }, buttonText);
      
      return metrics;
    };

    // Test with old buttons
    await flags.disableCarbonButtons();
    await page.reload();
    const oldClickTime = await measureButtonClick('Protocol');

    // Test with new buttons
    await flags.enableCarbonButtons();
    await page.reload();
    const newClickTime = await measureButtonClick('Protocol');

    expect(newClickTime).toBeLessThan(50); // Should respond within 50ms
    expect(newClickTime).toBeLessThanOrEqual(oldClickTime * 1.5); // At most 50% slower
  });

  test('Memory usage under button-heavy load', async ({ page }) => {
    // Navigate to page with most buttons
    await page.goto('/#/Analysis_Overview');
    await flags.enableCarbonButtons();
    await page.reload();
    
    // Measure initial memory
    const initialMemory = await page.evaluate(() => 
      (performance as any).memory?.usedJSHeapSize || 0
    );
    
    // Interact with many buttons
    const buttons = await page.getByRole('button').all();
    for (let i = 0; i < Math.min(buttons.length, 10); i++) {
      await buttons[i].hover();
      await page.waitForTimeout(50);
    }
    
    // Measure memory after interactions
    const finalMemory = await page.evaluate(() => 
      (performance as any).memory?.usedJSHeapSize || 0
    );
    
    const memoryIncrease = finalMemory - initialMemory;
    const percentIncrease = (memoryIncrease / initialMemory) * 100;
    
    expect(percentIncrease).toBeLessThan(10); // Less than 10% memory increase
    
    console.log(`Memory usage: Initial=${initialMemory}, Final=${finalMemory}, Increase=${percentIncrease.toFixed(2)}%`);
  });
});
```

## Phase 3: Continuous Integration

### Enhanced GitHub Actions Workflow

`.github/workflows/carbon-button-tests.yml`:
```yaml
name: Carbon Button Migration Tests

on:
  push:
    branches: [feature/carbon-buttons]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Nightly at 2 AM

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-type: [baseline, migration, visual, accessibility, performance]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: |
          ~/.cache/pip
          node_modules
          ~/.cache/ms-playwright
        key: ${{ runner.os }}-deps-${{ hashFiles('**/requirements.txt', '**/package-lock.json') }}
    
    - name: Install Python dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest-playwright pytest-html
    
    - name: Install Node dependencies
      run: |
        npm ci
        npx playwright install chromium
        npx playwright install-deps
    
    - name: Run ${{ matrix.test-type }} tests
      run: |
        npm run test:${{ matrix.test-type }}
      env:
        USE_CARBON_BUTTONS: ${{ matrix.test-type == 'migration' && 'true' || 'false' }}
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: ${{ matrix.test-type }}-results
        path: |
          playwright-report/
          tests/e2e/test-results/
          tests/e2e/screenshots/
        retention-days: 30
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      if: matrix.test-type == 'migration'
      with:
        file: ./coverage/lcov.info
    
    - name: Comment PR with results
      uses: actions/github-script@v6
      if: github.event_name == 'pull_request' && always()
      with:
        script: |
          const fs = require('fs');
          const testResults = fs.readFileSync('test-results.json', 'utf8');
          const results = JSON.parse(testResults);
          
          const comment = `## Carbon Button Test Results - ${{ matrix.test-type }}
          
          | Metric | Value |
          |--------|-------|
          | Total Tests | ${results.total} |
          | Passed | ${results.passed} |
          | Failed | ${results.failed} |
          | Duration | ${results.duration}ms |
          
          [View full report](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})`;
          
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: comment
          });

  merge-results:
    needs: test
    runs-on: ubuntu-latest
    if: always()
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Download all artifacts
      uses: actions/download-artifact@v3
    
    - name: Merge test results
      run: |
        npm install --save-dev @playwright/test
        npx playwright merge-reports --reporter html ./*/playwright-report
    
    - name: Deploy test results to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      if: github.ref == 'refs/heads/feature/carbon-buttons'
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./playwright-report
        destination_dir: carbon-button-tests/${{ github.run_number }}
```

### Test Execution Scripts

`package.json`:
```json
{
  "name": "ape-carbon-button-tests",
  "version": "1.0.0",
  "scripts": {
    "test:baseline": "playwright test --grep @baseline",
    "test:migration": "playwright test --grep @migration",
    "test:visual": "playwright test --grep @visual",
    "test:accessibility": "playwright test --grep @accessibility",
    "test:performance": "playwright test --grep @performance",
    "test:all": "playwright test",
    "test:watch": "playwright test --ui",
    "test:debug": "playwright test --debug",
    "test:headed": "playwright test --headed",
    "test:report": "playwright show-report",
    "test:update-snapshots": "playwright test --update-snapshots",
    "test:specific": "playwright test -g",
    "pretest": "npm run lint && npm run type-check",
    "lint": "eslint tests/e2e --ext .ts",
    "type-check": "tsc --noEmit"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0",
    "@types/node": "^20.0.0",
    "axe-playwright": "^1.2.3",
    "typescript": "^5.0.0",
    "eslint": "^8.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0"
  }
}
```

## Phase 4: Migration Execution Guide

### Day-by-Day Checklist

#### Day 0: Setup
```bash
# 1. Install dependencies
npm install
pip install -r requirements.txt

# 2. Generate button inventory
npx playwright test tests/e2e/utils/button-inventory.ts

# 3. Create baseline tests for all buttons
# Review button-inventory.json and ensure all buttons have tests

# 4. Run all baseline tests
npm run test:baseline -- --update-snapshots

# 5. Verify all tests pass
npm run test:baseline

# 6. Commit baseline
git add tests/e2e
git commit -m "test: Add comprehensive baseline tests for all buttons"
```

#### Day 1-2: Test Development
```bash
# Run tests in watch mode while writing
npm run test:watch

# Verify test coverage
npm run test:all -- --reporter=html
open playwright-report/index.html

# Ensure 100% button coverage before proceeding
```

#### Day 3-14: Progressive Migration
```bash
# For each component:

# 1. Run relevant tests in watch mode
npm run test:watch -- --grep "Navigation"

# 2. Make changes to one button at a time

# 3. Verify tests still pass

# 4. Run visual comparison
npm run test:visual

# 5. Check accessibility
npm run test:accessibility

# 6. Verify performance
npm run test:performance

# 7. Commit when all tests green
git add .
git commit -m "feat: Migrate navigation buttons to Carbon"
```

## Success Criteria Verification

Run this script to verify all success criteria are met:

`tests/e2e/verify-success.ts`:
```typescript
import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test('Verify migration success criteria', async () => {
  const results = {
    functionalParity: false,
    visualApproval: false,
    accessibilityImproved: false,
    performanceAcceptable: false,
    allJourneysWork: false,
  };

  // Check functional test results
  const functionalResults = JSON.parse(
    fs.readFileSync('test-results.json', 'utf-8')
  );
  results.functionalParity = functionalResults.failed === 0;

  // Check visual test results
  const visualDir = 'tests/e2e/screenshots/comparison';
  const visualFiles = fs.readdirSync(visualDir);
  results.visualApproval = visualFiles.length > 0; // Assumes manual review

  // Check accessibility results
  const a11yReport = fs.readFileSync('tests/e2e/accessibility-report.json', 'utf-8');
  const a11y = JSON.parse(a11yReport);
  results.accessibilityImproved = a11y.newViolations <= a11y.oldViolations;

  // Check performance results
  const perfReport = fs.readFileSync('tests/e2e/performance-report.json', 'utf-8');
  const perf = JSON.parse(perfReport);
  results.performanceAcceptable = perf.loadTimeIncrease < 100;

  // Check E2E results
  const e2eResults = JSON.parse(
    fs.readFileSync('tests/e2e/e2e-results.json', 'utf-8')
  );
  results.allJourneysWork = e2eResults.failed === 0;

  // Generate final report
  const allCriteriaMet = Object.values(results).every(v => v === true);
  
  console.log(`
🎉 Migration Success Criteria Check 🎉
=====================================
✅ Functional Parity: ${results.functionalParity}
✅ Visual Approval: ${results.visualApproval}
✅ Accessibility Improved: ${results.accessibilityImproved}
✅ Performance Acceptable: ${results.performanceAcceptable}
✅ All User Journeys Work: ${results.allJourneysWork}

${allCriteriaMet ? '🚀 READY TO DEPLOY! 🚀' : '⚠️  Some criteria not met. Review reports.'}
`);

  expect(allCriteriaMet).toBe(true);
});
```

## Best Practices

1. **Test First, Code Second**: Never migrate a button without tests
2. **One Button at a Time**: Migrate incrementally, test continuously
3. **Visual Review**: Always check screenshots for unexpected changes
4. **Performance Monitoring**: Track metrics throughout migration
5. **Accessibility Focus**: Verify improvements with each change
6. **Documentation**: Keep test results as migration documentation

## Troubleshooting

### Common Issues

1. **Tests timing out**
   - Increase timeout in playwright.config.ts
   - Add explicit waits for Streamlit elements
   - Check for console errors

2. **Visual differences**
   - Update snapshots if changes are intentional
   - Use threshold for minor pixel differences
   - Check for animation/transition states

3. **Flaky tests**
   - Add proper wait conditions
   - Use data-testid attributes
   - Avoid hardcoded timeouts

4. **Performance degradation**
   - Profile button render times
   - Check for memory leaks
   - Optimize Carbon button imports