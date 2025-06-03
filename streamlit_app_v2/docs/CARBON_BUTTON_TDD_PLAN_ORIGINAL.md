# Test-Driven Carbon Button Migration Plan

## Overview
Use Playwright to create comprehensive tests for all existing button functionality BEFORE migration, ensuring no regressions during the Carbon button implementation.

## TDD Workflow
1. **Capture Current Behavior**: Write tests for all existing buttons
2. **Verify Tests Pass**: Ensure all tests pass with current implementation
3. **Migrate to Carbon**: Replace buttons while keeping tests green
4. **Enhance Tests**: Add new tests for Carbon-specific features

## Phase 0: Test Infrastructure Setup (Day 1)

### Setup Playwright Test Framework

```bash
# Install test dependencies
npm install -D @playwright/test
pip install pytest-playwright

# Install browsers
npx playwright install chromium
```

### Create Test Configuration

`playwright.config.ts`:
```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  retries: 2,
  workers: 1, // Streamlit apps should run tests serially
  use: {
    baseURL: 'http://localhost:8501',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'streamlit run APE.py --server.headless true',
    port: 8501,
    reuseExistingServer: !process.env.CI,
  },
});
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
    await this.page.waitForTimeout(1000); // Streamlit render time
  }

  async clickButton(label: string): Promise<void> {
    // Current button selector
    const button = this.page.getByRole('button', { name: label });
    await button.click();
    await this.page.waitForTimeout(500); // Streamlit response time
  }

  async clickButtonByTestId(testId: string): Promise<void> {
    await this.page.locator(`[data-testid="${testId}"]`).click();
    await this.page.waitForTimeout(500);
  }

  async expectSuccessMessage(text: string) {
    await expect(this.page.getByText(text)).toBeVisible({ timeout: 5000 });
  }

  async expectPageSwitch(expectedUrl: string) {
    await expect(this.page).toHaveURL(expectedUrl, { timeout: 5000 });
  }

  async fillInput(label: string, value: string) {
    await this.page.getByLabel(label).fill(value);
  }

  async selectOption(label: string, value: string) {
    await this.page.getByLabel(label).selectOption(value);
  }
}
```

## Phase 1: Capture Current Behavior (Day 2-3)

### Test Templates for Each Button Type

#### Navigation Button Tests

`tests/e2e/navigation.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { StreamlitPage } from './utils/streamlit-helpers';

test.describe('Navigation Buttons - Current Behavior', () => {
  let app: StreamlitPage;

  test.beforeEach(async ({ page }) => {
    app = new StreamlitPage(page);
    await page.goto('/');
    await app.waitForLoad();
  });

  test('Home button navigates to main page', async ({ page }) => {
    // Navigate away first
    await page.goto('/#/Protocol_Manager');
    await app.waitForLoad();
    
    // Click home button
    await app.clickButton('🏠 Home'); // Current emoji-based label
    
    // Verify navigation
    await expect(page).toHaveURL('http://localhost:8501/');
  });

  test('Protocol Manager navigation', async ({ page }) => {
    await app.clickButton('📋 Protocol Manager');
    await expect(page).toHaveURL('/#/Protocol_Manager');
  });

  test('Run Simulation navigation', async ({ page }) => {
    await app.clickButton('🚀 Run Simulation');
    await expect(page).toHaveURL('/#/Run_Simulation');
  });

  test('Analysis Overview navigation', async ({ page }) => {
    await app.clickButton('📊 Analysis Overview');
    await expect(page).toHaveURL('/#/Analysis_Overview');
  });
});
```

#### Form Action Tests

`tests/e2e/protocol-manager.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { StreamlitPage } from './utils/streamlit-helpers';

test.describe('Protocol Manager Actions - Current Behavior', () => {
  let app: StreamlitPage;

  test.beforeEach(async ({ page }) => {
    app = new StreamlitPage(page);
    await page.goto('/#/Protocol_Manager');
    await app.waitForLoad();
  });

  test('Save protocol button', async ({ page }) => {
    // Fill protocol form
    await app.fillInput('Protocol Name', 'Test Protocol');
    await app.fillInput('Initial Dose', '2.0');
    
    // Click save
    await app.clickButton('💾 Save Protocol');
    
    // Verify success
    await app.expectSuccessMessage('Protocol saved successfully');
  });

  test('Load protocol button', async ({ page }) => {
    // Select a protocol
    await app.selectOption('Select Protocol', 'eylea.yaml');
    
    // Click load
    await app.clickButton('📂 Load Protocol');
    
    // Verify loaded
    await expect(page.getByText('Protocol loaded')).toBeVisible();
  });

  test('Delete protocol button shows confirmation', async ({ page }) => {
    // Select a protocol
    await app.selectOption('Select Protocol', 'test_protocol.yaml');
    
    // Click delete
    await app.clickButton('🗑️ Delete Protocol');
    
    // Verify confirmation appears
    await expect(page.getByText('Are you sure')).toBeVisible();
  });
});
```

#### Primary Action Tests

`tests/e2e/run-simulation.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { StreamlitPage } from './utils/streamlit-helpers';

test.describe('Run Simulation Actions - Current Behavior', () => {
  let app: StreamlitPage;

  test.beforeEach(async ({ page }) => {
    app = new StreamlitPage(page);
    await page.goto('/#/Run_Simulation');
    await app.waitForLoad();
  });

  test('Run Simulation button starts simulation', async ({ page }) => {
    // Set parameters
    await app.fillInput('Number of Patients', '100');
    await app.fillInput('Simulation Years', '2');
    
    // Click run
    await app.clickButton('▶️ Run Simulation');
    
    // Verify simulation starts
    await expect(page.getByText('Running simulation')).toBeVisible();
    
    // Wait for completion
    await expect(page.getByText('Simulation complete')).toBeVisible({ 
      timeout: 30000 
    });
  });

  test('Reset button clears form', async ({ page }) => {
    // Fill some values
    await app.fillInput('Number of Patients', '500');
    
    // Click reset
    await app.clickButton('🔄 Reset');
    
    // Verify reset
    const input = page.getByLabel('Number of Patients');
    await expect(input).toHaveValue('1000'); // Default value
  });
});
```

#### Export Button Tests

`tests/e2e/analysis-export.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { StreamlitPage } from './utils/streamlit-helpers';
import { Download } from '@playwright/test';

test.describe('Export Actions - Current Behavior', () => {
  let app: StreamlitPage;

  test.beforeEach(async ({ page }) => {
    app = new StreamlitPage(page);
    await page.goto('/#/Analysis_Overview');
    await app.waitForLoad();
    
    // Ensure we have data to export
    await page.evaluate(() => {
      window.sessionStorage.setItem('simulation_results', 'test_data');
    });
  });

  test('Export PNG button downloads image', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download');
    
    await app.clickButton('📥 PNG');
    
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.png');
  });

  test('Export SVG button downloads vector', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download');
    
    await app.clickButton('📥 SVG');
    
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.svg');
  });

  test('Export data button downloads CSV', async ({ page }) => {
    const downloadPromise = page.waitForEvent('download');
    
    await app.clickButton('💾 Export Data');
    
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.csv');
  });
});
```

### Create Baseline Screenshot Tests

`tests/e2e/visual-regression.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { StreamlitPage } from './utils/streamlit-helpers';

test.describe('Visual Regression - Current Buttons', () => {
  let app: StreamlitPage;

  test.beforeEach(async ({ page }) => {
    app = new StreamlitPage(page);
  });

  test('Navigation buttons baseline', async ({ page }) => {
    await page.goto('/');
    await app.waitForLoad();
    
    // Capture navigation area
    const navArea = page.locator('.stApp header');
    await expect(navArea).toHaveScreenshot('navigation-baseline.png');
  });

  test('Form buttons baseline', async ({ page }) => {
    await page.goto('/#/Protocol_Manager');
    await app.waitForLoad();
    
    const formArea = page.locator('form');
    await expect(formArea).toHaveScreenshot('form-buttons-baseline.png');
  });

  test('Export buttons baseline', async ({ page }) => {
    await page.goto('/#/Analysis_Overview');
    await app.waitForLoad();
    
    const exportArea = page.locator('[data-testid="export-controls"]');
    await expect(exportArea).toHaveScreenshot('export-buttons-baseline.png');
  });
});
```

## Phase 2: Migration Test Strategy (Day 4-14)

### Create Migration Test Runner

`tests/e2e/utils/migration-helper.ts`:
```typescript
export class MigrationTester {
  constructor(private page: Page) {}

  async testButtonMigration(
    oldSelector: string,
    newSelector: string,
    actionValidator: () => Promise<void>
  ) {
    // Test old button
    console.log(`Testing old button: ${oldSelector}`);
    await this.page.click(oldSelector);
    await actionValidator();
    
    // Switch to Carbon buttons (via feature flag)
    await this.page.evaluate(() => {
      window.sessionStorage.setItem('USE_CARBON_BUTTONS', 'true');
    });
    await this.page.reload();
    
    // Test new button
    console.log(`Testing new button: ${newSelector}`);
    await this.page.click(newSelector);
    await actionValidator();
  }

  async compareButtonBehavior(buttonLabel: string) {
    const results = {
      oldButton: { clicked: false, responseTime: 0 },
      newButton: { clicked: false, responseTime: 0 }
    };

    // Test old button
    const oldStart = Date.now();
    await this.page.getByRole('button', { name: buttonLabel }).click();
    results.oldButton.responseTime = Date.now() - oldStart;
    results.oldButton.clicked = true;

    // Enable Carbon buttons
    await this.page.evaluate(() => {
      window.sessionStorage.setItem('USE_CARBON_BUTTONS', 'true');
    });
    await this.page.reload();

    // Test new button
    const newStart = Date.now();
    await this.page.getByRole('button', { name: buttonLabel }).click();
    results.newButton.responseTime = Date.now() - newStart;
    results.newButton.clicked = true;

    return results;
  }
}
```

### Progressive Migration Tests

`tests/e2e/migration-progress.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { MigrationTester } from './utils/migration-helper';

test.describe('Progressive Migration Tests', () => {
  test('Day 3-4: Navigation buttons work identically', async ({ page }) => {
    const tester = new MigrationTester(page);
    
    // Test each navigation button
    const navButtons = ['Home', 'Protocol Manager', 'Run Simulation', 'Analysis Overview'];
    
    for (const button of navButtons) {
      const results = await tester.compareButtonBehavior(button);
      
      // Verify both clicked successfully
      expect(results.oldButton.clicked).toBe(true);
      expect(results.newButton.clicked).toBe(true);
      
      // Verify performance is acceptable
      expect(results.newButton.responseTime).toBeLessThan(
        results.oldButton.responseTime * 1.5 // Allow 50% slower max
      );
    }
  });

  test('Day 5-6: Form actions maintain functionality', async ({ page }) => {
    await page.goto('/#/Protocol_Manager');
    
    // Test save action with both button types
    const tester = new MigrationTester(page);
    
    await tester.testButtonMigration(
      'button:has-text("💾 Save")',
      'button:has-text("Save")',
      async () => {
        // Verify save succeeded
        await expect(page.getByText('saved successfully')).toBeVisible();
      }
    );
  });

  test('Day 7: Export functions work correctly', async ({ page }) => {
    await page.goto('/#/Analysis_Overview');
    
    const exportFormats = ['PNG', 'SVG', 'JPEG', 'WebP'];
    
    for (const format of exportFormats) {
      // Test with old buttons
      const oldDownload = page.waitForEvent('download');
      await page.getByRole('button', { name: `📥 ${format}` }).click();
      const oldFile = await oldDownload;
      
      // Enable Carbon buttons
      await page.evaluate(() => {
        window.sessionStorage.setItem('USE_CARBON_BUTTONS', 'true');
      });
      await page.reload();
      
      // Test with new buttons
      const newDownload = page.waitForEvent('download');
      await page.getByRole('button', { name: format }).click();
      const newFile = await newDownload;
      
      // Verify both produce files
      expect(oldFile.suggestedFilename()).toContain(format.toLowerCase());
      expect(newFile.suggestedFilename()).toContain(format.toLowerCase());
    }
  });
});
```

### Accessibility Tests

`tests/e2e/accessibility.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('Accessibility Improvements', () => {
  test('Carbon buttons improve accessibility', async ({ page }) => {
    await page.goto('/');
    await injectAxe(page);
    
    // Check accessibility with old buttons
    const oldResults = await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: { html: true }
    });
    
    // Enable Carbon buttons
    await page.evaluate(() => {
      window.sessionStorage.setItem('USE_CARBON_BUTTONS', 'true');
    });
    await page.reload();
    await injectAxe(page);
    
    // Check accessibility with new buttons
    const newResults = await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: { html: true }
    });
    
    // Carbon buttons should have fewer or equal violations
    expect(newResults.violations.length).toBeLessThanOrEqual(
      oldResults.violations.length
    );
  });

  test('Icon-only buttons have proper ARIA labels', async ({ page }) => {
    await page.goto('/');
    
    // Enable Carbon buttons
    await page.evaluate(() => {
      window.sessionStorage.setItem('USE_CARBON_BUTTONS', 'true');
    });
    await page.reload();
    
    // Find all icon-only buttons
    const iconButtons = page.locator('button:not(:has-text(*))');
    const count = await iconButtons.count();
    
    for (let i = 0; i < count; i++) {
      const button = iconButtons.nth(i);
      const ariaLabel = await button.getAttribute('aria-label');
      
      // Every icon-only button must have an aria-label
      expect(ariaLabel).toBeTruthy();
      expect(ariaLabel.length).toBeGreaterThan(0);
    }
  });
});
```

### Performance Tests

`tests/e2e/performance.spec.ts`:
```typescript
import { test, expect } from '@playwright/test';

test.describe('Performance Metrics', () => {
  test('Page load time comparison', async ({ page }) => {
    // Measure old button load time
    const oldMetrics = await page.goto('/', { waitUntil: 'networkidle' });
    const oldLoadTime = oldMetrics.timing().domContentLoadedEventEnd - 
                       oldMetrics.timing().navigationStart;
    
    // Enable Carbon buttons
    await page.evaluate(() => {
      window.sessionStorage.setItem('USE_CARBON_BUTTONS', 'true');
    });
    
    // Measure new button load time
    const newMetrics = await page.goto('/', { waitUntil: 'networkidle' });
    const newLoadTime = newMetrics.timing().domContentLoadedEventEnd - 
                       newMetrics.timing().navigationStart;
    
    // Should not increase by more than 100ms
    expect(newLoadTime - oldLoadTime).toBeLessThan(100);
    
    console.log(`Old load time: ${oldLoadTime}ms`);
    console.log(`New load time: ${newLoadTime}ms`);
    console.log(`Difference: ${newLoadTime - oldLoadTime}ms`);
  });

  test('Button click responsiveness', async ({ page }) => {
    await page.goto('/');
    
    // Test old button response time
    await page.evaluate(() => {
      window.buttonClickTime = 0;
      document.addEventListener('click', (e) => {
        if (e.target.matches('button')) {
          window.buttonClickTime = performance.now();
        }
      });
    });
    
    const oldButton = page.getByRole('button').first();
    await oldButton.click();
    const oldResponseTime = await page.evaluate(() => window.buttonClickTime);
    
    // Enable Carbon buttons and test
    await page.evaluate(() => {
      window.sessionStorage.setItem('USE_CARBON_BUTTONS', 'true');
    });
    await page.reload();
    
    await page.evaluate(() => {
      window.buttonClickTime = 0;
      document.addEventListener('click', (e) => {
        if (e.target.matches('button')) {
          window.buttonClickTime = performance.now();
        }
      });
    });
    
    const newButton = page.getByRole('button').first();
    await newButton.click();
    const newResponseTime = await page.evaluate(() => window.buttonClickTime);
    
    // Response time should be under 50ms
    expect(newResponseTime).toBeLessThan(50);
    
    console.log(`Old button response: ${oldResponseTime}ms`);
    console.log(`New button response: ${newResponseTime}ms`);
  });
});
```

## Phase 3: Continuous Integration (Ongoing)

### GitHub Actions Workflow

`.github/workflows/button-migration-tests.yml`:
```yaml
name: Button Migration Tests

on:
  push:
    branches: [feature/carbon-buttons]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest-playwright
        npm ci
        npx playwright install chromium
    
    - name: Run baseline tests (old buttons)
      run: |
        npx playwright test --grep "@baseline"
      env:
        USE_CARBON_BUTTONS: false
    
    - name: Run migration tests (new buttons)
      run: |
        npx playwright test --grep "@migration"
      env:
        USE_CARBON_BUTTONS: true
    
    - name: Run comparison tests
      run: |
        npx playwright test --grep "@comparison"
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: playwright-report
        path: playwright-report/
        retention-days: 30
    
    - name: Upload screenshots
      uses: actions/upload-artifact@v3
      if: failure()
      with:
        name: screenshots
        path: tests/e2e/screenshots/
```

### Test Execution Strategy

`package.json`:
```json
{
  "scripts": {
    "test:baseline": "USE_CARBON_BUTTONS=false playwright test --grep @baseline",
    "test:migration": "USE_CARBON_BUTTONS=true playwright test --grep @migration",
    "test:comparison": "playwright test --grep @comparison",
    "test:visual": "playwright test --grep @visual --update-snapshots",
    "test:a11y": "playwright test --grep @accessibility",
    "test:perf": "playwright test --grep @performance",
    "test:all": "npm run test:baseline && npm run test:migration && npm run test:comparison",
    "test:watch": "playwright test --ui"
  }
}
```

## Phase 4: Migration Execution

### Day-by-Day Test-Driven Process

#### Day 1-2: Setup & Baseline
```bash
# Create all baseline tests
npm run test:baseline -- --update-snapshots

# Generate test report
npm run test:baseline -- --reporter=html

# Document all button behaviors
npm run test:baseline -- --reporter=json > baseline-behavior.json
```

#### Day 3-4: Navigation Migration
```bash
# Run navigation tests continuously during migration
npm run test:watch -- --grep "Navigation"

# After each file change
npm run test:comparison -- --grep "Navigation"
```

#### Day 5-6: Form Actions
```bash
# Focus on form functionality
npm run test:watch -- --grep "Form|Save|Load|Delete"

# Verify no regressions
npm run test:all -- --grep "Protocol Manager"
```

#### Day 7: Export Actions
```bash
# Test export functionality
npm run test:watch -- --grep "Export"

# Verify downloads work
npm run test:comparison -- --grep "download"
```

#### Day 8-14: Polish & Performance
```bash
# Run all tests
npm run test:all

# Check accessibility improvements
npm run test:a11y

# Verify performance
npm run test:perf

# Final visual regression
npm run test:visual
```

## Success Criteria

All tests must pass with Carbon buttons:
- ✅ 100% functional parity with old buttons
- ✅ No visual regressions (or approved changes)
- ✅ Improved accessibility scores
- ✅ Performance within acceptable limits
- ✅ All user journeys preserved

## Test Maintenance

### Post-Migration
1. Archive old button tests (don't delete)
2. Update tests to use Carbon-specific features
3. Add new tests for enhanced functionality
4. Set up monitoring dashboard for test results
5. Regular visual regression updates

### Living Documentation
- Test results as documentation
- Screenshot comparisons in PR reviews
- Performance benchmarks tracked over time
- Accessibility scores monitored