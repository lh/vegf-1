import { Page } from '@playwright/test';
import { StreamlitPage } from './streamlit-page';

export interface ButtonInfo {
  label: string;
  page: string;
  type: 'navigation' | 'action' | 'form' | 'export' | 'danger';
  hasIcon: boolean;
  iconEmoji?: string;
  fullWidth: boolean;
  inSidebar: boolean;
  formContext: boolean;
  key?: string;
}

/**
 * Helper class to inventory all buttons in the application
 */
export class ButtonInventory {
  private buttons: ButtonInfo[] = [];

  constructor(private page: Page) {}

  /**
   * Scan a page for all buttons and catalog them
   */
  async scanPage(pageName: string) {
    const streamlit = new StreamlitPage(this.page);
    await streamlit.waitForLoad();

    // Get all buttons on the page
    const allButtons = await this.page.locator('button').all();

    for (const button of allButtons) {
      const text = await button.textContent() || '';
      const classes = await button.getAttribute('class') || '';
      const dataTestId = await button.getAttribute('data-testid') || '';
      const boundingBox = await button.boundingBox();
      const parentForm = await button.locator('xpath=ancestor::form').count() > 0;
      const inSidebar = await button.locator('xpath=ancestor::section[@data-testid="stSidebar"]').count() > 0;

      // Detect emoji icons (common pattern in current buttons)
      const emojiRegex = /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/u;
      const hasEmoji = emojiRegex.test(text);
      const emojiMatch = text.match(emojiRegex);

      // Classify button type
      let type: ButtonInfo['type'] = 'action';
      if (text.toLowerCase().includes('delete') || text.includes('⚠️')) {
        type = 'danger';
      } else if (text.toLowerCase().includes('export') || text.includes('📥')) {
        type = 'export';
      } else if (parentForm) {
        type = 'form';
      } else if (inSidebar || pageName === 'navigation') {
        type = 'navigation';
      }

      // Check if button is full width
      const pageWidth = await this.page.evaluate(() => window.innerWidth);
      const isFullWidth = boundingBox ? (boundingBox.width / pageWidth) > 0.8 : false;

      this.buttons.push({
        label: text.replace(emojiRegex, '').trim(),
        page: pageName,
        type,
        hasIcon: hasEmoji,
        iconEmoji: emojiMatch ? emojiMatch[0] : undefined,
        fullWidth: isFullWidth,
        inSidebar,
        formContext: parentForm,
        key: dataTestId || undefined,
      });
    }
  }

  /**
   * Scan all pages in the application
   */
  async scanAllPages() {
    const pages = [
      { name: 'Home', url: '/' },
      { name: 'Protocol Manager', url: '/Protocol_Manager' },
      { name: 'Run Simulation', url: '/Run_Simulation' },
      { name: 'Analysis Overview', url: '/Analysis_Overview' },
    ];

    for (const pageInfo of pages) {
      await this.page.goto(pageInfo.url);
      await this.scanPage(pageInfo.name);
    }
  }

  /**
   * Generate a markdown report of all buttons
   */
  generateReport(): string {
    let report = '# Button Inventory Report\n\n';
    report += `Generated: ${new Date().toISOString()}\n\n`;
    report += `Total buttons found: ${this.buttons.length}\n\n`;

    // Group by type
    const byType = this.groupBy(this.buttons, 'type');
    
    for (const [type, buttons] of Object.entries(byType)) {
      report += `## ${type.charAt(0).toUpperCase() + type.slice(1)} Buttons (${buttons.length})\n\n`;
      report += '| Label | Page | Icon | Full Width | Sidebar | Form |\n';
      report += '|-------|------|------|------------|---------|------|\n';
      
      for (const button of buttons) {
        report += `| ${button.label} | ${button.page} | ${button.iconEmoji || '-'} | ${button.fullWidth ? '✓' : '-'} | ${button.inSidebar ? '✓' : '-'} | ${button.formContext ? '✓' : '-'} |\n`;
      }
      report += '\n';
    }

    // Generate migration checklist
    report += '## Migration Checklist\n\n';
    for (const button of this.buttons) {
      report += `- [ ] ${button.page}: ${button.iconEmoji || ''} ${button.label}\n`;
    }

    return report;
  }

  /**
   * Generate JSON data for programmatic use
   */
  toJSON() {
    return {
      timestamp: new Date().toISOString(),
      totalButtons: this.buttons.length,
      buttons: this.buttons,
      byType: this.groupBy(this.buttons, 'type'),
      byPage: this.groupBy(this.buttons, 'page'),
    };
  }

  private groupBy<T, K extends keyof T>(array: T[], key: K): Record<string, T[]> {
    return array.reduce((result, item) => {
      const group = String(item[key]);
      if (!result[group]) result[group] = [];
      result[group].push(item);
      return result;
    }, {} as Record<string, T[]>);
  }
}