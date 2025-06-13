# Test info

- Name: Carbon Button Home Page Migration >> Home page loads with Carbon buttons and correct state
- Location: /Users/rose/Code/CC/streamlit_app_v2/tests/playwright/carbon/test-home-migration.spec.ts:5:7

# Error details

```
Error: Timed out 5000ms waiting for expect(locator).toBeVisible()

Locator: locator('button:has-text("Protocol Manager")').first()
Expected: visible
Received: <element(s) not found>
Call log:
  - expect.toBeVisible with timeout 5000ms
  - waiting for locator('button:has-text("Protocol Manager")').first()

    at /Users/rose/Code/CC/streamlit_app_v2/tests/playwright/carbon/test-home-migration.spec.ts:17:34
```

# Page snapshot

```yaml
- banner:
  - button "Deploy"
  - button
- button
- list:
  - listitem:
    - link "APE":
      - /url: http://localhost:8502/
  - listitem:
    - link "Protocol Manager":
      - /url: http://localhost:8502/Protocol_Manager
  - listitem:
    - link "Run Simulation":
      - /url: http://localhost:8502/Run_Simulation
  - listitem:
    - link "Analysis Overview":
      - /url: http://localhost:8502/Analysis_Overview
  - listitem:
    - link "Experiments":
      - /url: http://localhost:8502/Experiments
  - listitem:
    - link "Carbon Button Test":
      - /url: http://localhost:8502/Carbon_Button_Test
- button "Fullscreen"
- img "0"
- heading "AMD Protocol Explorer" [level=1]
- paragraph: Welcome to the V2 simulation system with complete parameter traceability.
- heading "Getting Started" [level=3]
- list:
  - listitem:
    - text: Navigate to
    - strong: Protocol Manager
    - text: to view available protocols
  - listitem:
    - text: Go to
    - strong: Run Simulation
    - text: to execute a protocol
  - listitem:
    - text: View results in
    - strong: Analysis
    - text: pages
- heading "Key Features" [level=3]
- list:
  - listitem:
    - strong: No Hidden Parameters
    - text: ": Every parameter explicitly defined in protocol files"
  - listitem:
    - strong: Full Audit Trail
    - text: ": Complete tracking from parameter to result"
  - listitem:
    - strong: Protocol Library
    - text: ": Load and compare different treatment protocols"
  - listitem:
    - strong: Reproducible Results
    - text: ": Checksums ensure exact protocol versions"
- heading "Navigation" [level=3]
- iframe
- iframe
- paragraph: ⚠️ Load a protocol first
- iframe
- paragraph: ⚠️ Run a simulation first
- separator
- heading "Current Status" [level=3]
- alert:
  - paragraph: ⚠️ No protocol loaded
- alert:
  - paragraph: ℹ️ No simulation results yet
- separator
- paragraph: 🦍 APE V2 - Scientific simulation with complete traceability
```

# Test source

```ts
   1 | import { test, expect } from '@playwright/test';
   2 | import { StreamlitPage } from '../helpers/streamlit-page';
   3 |
   4 | test.describe('Carbon Button Home Page Migration', () => {
   5 |   test('Home page loads with Carbon buttons and correct state', async ({ page }) => {
   6 |     const streamlit = new StreamlitPage(page);
   7 |     
   8 |     // Navigate to home page
   9 |     await page.goto('/');
  10 |     await streamlit.waitForLoad();
  11 |     
  12 |     // Take screenshot of initial state
  13 |     await streamlit.screenshot('home-page-carbon-initial');
  14 |     
  15 |     // Check Protocol Manager button is enabled
  16 |     const protocolButton = page.locator('button:has-text("Protocol Manager")').first();
> 17 |     await expect(protocolButton).toBeVisible();
     |                                  ^ Error: Timed out 5000ms waiting for expect(locator).toBeVisible()
  18 |     await expect(protocolButton).toBeEnabled();
  19 |     
  20 |     // Check Run Simulation button is disabled (no protocol loaded)
  21 |     const runButton = page.locator('button:has-text("Run Simulation")').first();
  22 |     await expect(runButton).toBeVisible();
  23 |     await expect(runButton).toBeDisabled();
  24 |     
  25 |     // Check Analysis Overview button is disabled (no simulation results)
  26 |     const analysisButton = page.locator('button:has-text("Analysis Overview")').first();
  27 |     await expect(analysisButton).toBeVisible();
  28 |     await expect(analysisButton).toBeDisabled();
  29 |     
  30 |     // Check warning messages are visible
  31 |     await expect(page.locator('text=Load a protocol first')).toBeVisible();
  32 |     await expect(page.locator('text=Run a simulation first')).toBeVisible();
  33 |     
  34 |     // Check Carbon button styling (no emojis)
  35 |     const allButtons = page.locator('button');
  36 |     const buttonCount = await allButtons.count();
  37 |     for (let i = 0; i < buttonCount; i++) {
  38 |       const buttonText = await allButtons.nth(i).textContent();
  39 |       // Ensure no emojis in button text
  40 |       expect(buttonText).not.toMatch(/[\u{1F300}-\u{1F9FF}]/u);
  41 |     }
  42 |     
  43 |     // Test navigation to Protocol Manager
  44 |     await protocolButton.click();
  45 |     await streamlit.waitForLoad();
  46 |     
  47 |     // Should navigate to Protocol Manager page
  48 |     await expect(page).toHaveURL(/.*1_Protocol_Manager.*/);
  49 |     await streamlit.screenshot('protocol-manager-carbon');
  50 |   });
  51 |   
  52 |   test('Home page buttons become enabled with session state', async ({ page }) => {
  53 |     const streamlit = new StreamlitPage(page);
  54 |     
  55 |     // Set up session state with protocol and results
  56 |     await page.evaluate(() => {
  57 |       // @ts-ignore
  58 |       window.streamlit = window.streamlit || {};
  59 |       // @ts-ignore
  60 |       window.streamlit.setComponentValue = (key: string, value: any) => {
  61 |         // Simulate setting session state
  62 |         console.log(`Setting ${key} to`, value);
  63 |       };
  64 |     });
  65 |     
  66 |     // Navigate to home page
  67 |     await page.goto('/');
  68 |     await streamlit.waitForLoad();
  69 |     
  70 |     // Take screenshot showing disabled state
  71 |     await streamlit.screenshot('home-page-buttons-disabled');
  72 |   });
  73 | });
```