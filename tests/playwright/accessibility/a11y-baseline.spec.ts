import { test, expect } from '@playwright/test';
import { StreamlitPage } from '../helpers/streamlit-page';
import { injectAxe, checkA11y, getViolations } from 'axe-playwright';

test.describe('Accessibility Baseline Tests', () => {
  test('Document current accessibility violations', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    const violations: any[] = [];
    
    const pages = [
      { name: 'Home', url: '/' },
      { name: 'Protocol Manager', url: '/Protocol_Manager' },
      { name: 'Run Simulation', url: '/Run_Simulation' },
      { name: 'Analysis Overview', url: '/Analysis_Overview' }
    ];
    
    for (const pageInfo of pages) {
      await page.goto(pageInfo.url);
      await streamlit.waitForLoad();
      await injectAxe(page);
      
      // Check for violations but don't fail - we're establishing baseline
      try {
        await checkA11y(page, undefined, {
          detailedReport: true,
          detailedReportOptions: {
            html: true
          }
        });
      } catch (e: any) {
        // Capture violations
        const pageViolations = await getViolations(page);
        violations.push({
          page: pageInfo.name,
          url: pageInfo.url,
          violationCount: pageViolations.length,
          violations: pageViolations
        });
      }
    }
    
    // Save baseline accessibility report
    const fs = require('fs');
    const report = {
      timestamp: new Date().toISOString(),
      totalViolations: violations.reduce((sum, p) => sum + p.violationCount, 0),
      pages: violations
    };
    
    fs.writeFileSync(
      'tests/playwright/reports/baseline-accessibility.json',
      JSON.stringify(report, null, 2)
    );
    
    console.log('Baseline accessibility report created');
    console.log(`Total violations found: ${report.totalViolations}`);
  });

  test('Button-specific accessibility checks', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    const buttonA11yIssues: any[] = [];
    
    // Check all pages
    const pages = [
      { name: 'Home', url: '/' },
      { name: 'Protocol Manager', url: '/Protocol_Manager' },
      { name: 'Run Simulation', url: '/Run_Simulation' },
      { name: 'Analysis Overview', url: '/Analysis_Overview' }
    ];
    
    for (const pageInfo of pages) {
      await page.goto(pageInfo.url);
      await streamlit.waitForLoad();
      
      // Find all buttons
      const buttons = await page.locator('button').all();
      
      for (let i = 0; i < buttons.length; i++) {
        const button = buttons[i];
        const text = await button.textContent() || '';
        
        // Check for ARIA labels on icon-only buttons
        const hasText = text.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '').trim().length > 0;
        const ariaLabel = await button.getAttribute('aria-label');
        const title = await button.getAttribute('title');
        
        if (!hasText && !ariaLabel) {
          buttonA11yIssues.push({
            page: pageInfo.name,
            issue: 'Icon-only button without aria-label',
            buttonText: text,
            index: i
          });
        }
        
        // Check color contrast
        const backgroundColor = await button.evaluate(el => 
          window.getComputedStyle(el).backgroundColor
        );
        const color = await button.evaluate(el => 
          window.getComputedStyle(el).color
        );
        
        // Check if button is keyboard accessible
        const tabIndex = await button.getAttribute('tabindex');
        if (tabIndex === '-1') {
          buttonA11yIssues.push({
            page: pageInfo.name,
            issue: 'Button not keyboard accessible',
            buttonText: text,
            index: i
          });
        }
      }
    }
    
    // Save button accessibility report
    const fs = require('fs');
    fs.writeFileSync(
      'tests/playwright/reports/baseline-button-accessibility.json',
      JSON.stringify({
        timestamp: new Date().toISOString(),
        totalIssues: buttonA11yIssues.length,
        issues: buttonA11yIssues
      }, null, 2)
    );
    
    console.log(`Found ${buttonA11yIssues.length} button accessibility issues`);
  });

  test('Keyboard navigation baseline', async ({ page }) => {
    const streamlit = new StreamlitPage(page);
    
    await page.goto('/');
    await streamlit.waitForLoad();
    
    // Test tab navigation through buttons
    const tabOrder: string[] = [];
    
    // Start from body
    await page.keyboard.press('Tab');
    
    // Tab through elements up to 20 times
    for (let i = 0; i < 20; i++) {
      const focusedElement = await page.evaluate(() => {
        const el = document.activeElement;
        if (el && el.tagName === 'BUTTON') {
          return {
            tag: el.tagName,
            text: el.textContent,
            class: el.className
          };
        }
        return null;
      });
      
      if (focusedElement) {
        tabOrder.push(focusedElement.text || 'Unnamed button');
      }
      
      await page.keyboard.press('Tab');
    }
    
    // Save keyboard navigation order
    const fs = require('fs');
    fs.writeFileSync(
      'tests/playwright/reports/baseline-keyboard-navigation.json',
      JSON.stringify({
        timestamp: new Date().toISOString(),
        tabOrder: tabOrder
      }, null, 2)
    );
    
    console.log('Documented tab order for buttons');
  });
});