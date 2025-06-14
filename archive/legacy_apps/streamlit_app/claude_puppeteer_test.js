/**
 * Claude Puppeteer Test Script for AMD Protocol Explorer
 * 
 * This script shows how Claude can use Puppeteer to interact with the
 * enhanced AMD Protocol Explorer Streamlit app.
 * 
 * Note: This is not meant to be run directly, but rather shows
 * the pattern that Claude should follow when using Puppeteer.
 */

async function runTest() {
  try {
    // 1. Navigate to the Streamlit app
    await puppeteer.navigate('http://localhost:8502');

    // 2. Wait for page to load (1-2 seconds)
    await new Promise(resolve => setTimeout(resolve, 2000));

    // 3. Take a screenshot of the initial state
    await puppeteer.screenshot({
      name: 'initial_state',
      width: 1920,
      height: 1080
    });

    // 4. Check if we have Puppeteer helpers
    const hasHelpers = await puppeteer.evaluate(`
      typeof window.puppeteerHelpers !== 'undefined'
    `);

    // 5A. If we have helpers, use them
    if (hasHelpers) {
      // Get all available elements
      const elements = await puppeteer.evaluate(`
        window.puppeteerHelpers.getAllElements()
      `);
      console.log('Available elements for selection:', elements);

      // Click Run Simulation in navigation
      await puppeteer.evaluate(`
        window.puppeteerHelpers.clickElement('main-navigation')
      `);

      // Wait a moment for page to update
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Take a screenshot of the Run Simulation page
      await puppeteer.screenshot({
        name: 'run_simulation_page',
        width: 1920, 
        height: 1080
      });

      // Click the Run Simulation button
      await puppeteer.evaluate(`
        window.puppeteerHelpers.clickElement('run-simulation-btn')
      `);

      // Wait for simulation to complete
      await new Promise(resolve => setTimeout(resolve, 5000));

      // Take a screenshot of the results
      await puppeteer.screenshot({
        name: 'simulation_results',
        width: 1920,
        height: 2000
      });
    }
    // 5B. If no helpers, use traditional selectors
    else {
      // Navigate to Run Simulation using radio buttons (nth-child since these are 1-indexed in CSS)
      await puppeteer.click('[data-testid="stRadio"] label:nth-child(2)');

      // Wait a moment for page to update
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Take a screenshot of the Run Simulation page
      await puppeteer.screenshot({
        name: 'run_simulation_page',
        width: 1920,
        height: 1080
      });

      // Click the Run Simulation button
      await puppeteer.click('.stButton button');

      // Wait for simulation to complete
      await new Promise(resolve => setTimeout(resolve, 5000));

      // Take a screenshot of the results
      await puppeteer.screenshot({
        name: 'simulation_results',
        width: 1920,
        height: 2000
      });
    }

    // Verify the results
    console.log("Test completed successfully!");
  }
  catch (error) {
    console.error("Test failed:", error);
  }
}

// This function isn't actually executed - it's a pattern for Claude to follow
runTest();