import { Page, Locator, expect } from '@playwright/test';

/**
 * Helper class for interacting with Streamlit pages
 * Provides common Streamlit-specific operations
 */
export class StreamlitPage {
  constructor(public readonly page: Page) {}

  /**
   * Wait for Streamlit to finish loading
   */
  async waitForLoad() {
    // Wait for Streamlit's loading indicator to disappear
    await this.page.waitForSelector('[data-testid="stAppViewContainer"]', { state: 'visible' });
    await this.page.waitForLoadState('networkidle');
    // Additional wait for any spinners
    await this.page.waitForSelector('.stSpinner', { state: 'hidden' }).catch(() => {});
  }

  /**
   * Get a Streamlit button by its label text
   */
  async getButton(label: string): Promise<Locator> {
    // Streamlit buttons can be in different containers
    return this.page.locator(`button:has-text("${label}")`).first();
  }

  /**
   * Click a button and wait for Streamlit to process
   */
  async clickButton(label: string) {
    const button = await this.getButton(label);
    await button.click();
    await this.waitForLoad();
  }

  /**
   * Get a form submit button by label
   */
  async getFormSubmitButton(label: string): Promise<Locator> {
    return this.page.locator(`[data-testid="stFormSubmitButton"]:has-text("${label}")`);
  }

  /**
   * Fill a text input by label
   */
  async fillTextInput(label: string, value: string) {
    const input = this.page.locator(`[aria-label="${label}"]`).or(
      this.page.locator(`input`).locator(`near(:text("${label}"))`)
    );
    await input.fill(value);
  }

  /**
   * Select from a selectbox by label and value
   */
  async selectOption(label: string, value: string) {
    const selectbox = this.page.locator(`[data-testid="stSelectbox"]`).locator(`near(:text("${label}"))`);
    await selectbox.click();
    await this.page.locator(`[data-testid="stSelectboxOption"]:has-text("${value}")`).click();
  }

  /**
   * Check if a success message is displayed
   */
  async expectSuccess(message: string) {
    await expect(this.page.locator('.stSuccess').locator(`text="${message}"`)).toBeVisible();
  }

  /**
   * Check if an error message is displayed
   */
  async expectError(message: string) {
    await expect(this.page.locator('.stError').locator(`text="${message}"`)).toBeVisible();
  }

  /**
   * Check if an info message is displayed
   */
  async expectInfo(message: string) {
    await expect(this.page.locator('.stInfo').locator(`text="${message}"`)).toBeVisible();
  }

  /**
   * Navigate to a specific page in the app
   */
  async navigateToPage(pageName: string) {
    // Click on sidebar navigation
    const navButton = this.page.locator(`[data-testid="stSidebar"] >> text="${pageName}"`);
    await navButton.click();
    await this.waitForLoad();
  }

  /**
   * Take a screenshot with consistent naming
   */
  async screenshot(name: string) {
    return await this.page.screenshot({ 
      path: `tests/playwright/screenshots/${name}.png`,
      fullPage: true 
    });
  }

  /**
   * Get all buttons on the current page
   */
  async getAllButtons(): Promise<Locator[]> {
    const buttons = await this.page.locator('button').all();
    return buttons;
  }

  /**
   * Check if a button exists
   */
  async hasButton(label: string): Promise<boolean> {
    const button = await this.getButton(label);
    return await button.isVisible().catch(() => false);
  }

  /**
   * Get button properties for comparison
   */
  async getButtonProperties(label: string) {
    const button = await this.getButton(label);
    const boundingBox = await button.boundingBox();
    const isEnabled = await button.isEnabled();
    const classes = await button.getAttribute('class');
    
    return {
      label,
      boundingBox,
      isEnabled,
      classes,
      // Will be extended for Carbon button properties
    };
  }
}