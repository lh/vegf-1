/**
 * Visual Regression Testing for AMD Protocol Explorer
 * 
 * This script performs visual regression testing on the AMD Protocol Explorer app
 * by comparing screenshots with baseline images.
 * 
 * Usage:
 * 1. Run baseline mode to capture baseline screenshots:
 *    node visual_regression.js --mode=baseline
 * 
 * 2. Run test mode to compare with baseline:
 *    node visual_regression.js --mode=test
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const pixelmatch = require('pixelmatch');
const PNG = require('pngjs').PNG;

// Configuration
const APP_URL = 'http://localhost:8502';
const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots');
const BASELINE_DIR = path.join(__dirname, 'baseline');
const DIFF_DIR = path.join(__dirname, 'diff');
const TIMEOUT = 15000;

// Testing settings
const THRESHOLD = 0.1; // Threshold for pixel difference (0-1)
const WAIT_TIME = 2000; // Base wait time between actions

// Parse command line arguments
const args = process.argv.slice(2);
const MODE = args.find(arg => arg.startsWith('--mode='))?.split('=')[1] || 'test';

// Ensure directories exist
for (const dir of [SCREENSHOTS_DIR, BASELINE_DIR, DIFF_DIR]) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// Helper function to wait
async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Pages to test
const TEST_PAGES = [
  {
    name: 'home',
    navigate: async (page) => {
      await page.goto(APP_URL, { waitUntil: 'networkidle0', timeout: TIMEOUT });
      await sleep(WAIT_TIME);
    }
  },
  {
    name: 'run_simulation',
    navigate: async (page) => {
      await page.click('[data-testid="stRadio"] label:nth-child(2)');
      await sleep(WAIT_TIME);
    }
  },
  {
    name: 'patient_explorer',
    navigate: async (page) => {
      await page.click('[data-testid="stRadio"] label:nth-child(3)');
      await sleep(WAIT_TIME);
    }
  },
  {
    name: 'reports',
    navigate: async (page) => {
      await page.click('[data-testid="stRadio"] label:nth-child(4)');
      await sleep(WAIT_TIME);
    }
  },
  {
    name: 'about',
    navigate: async (page) => {
      await page.click('[data-testid="stRadio"] label:nth-child(5)');
      await sleep(WAIT_TIME);
    }
  }
];

// Run a simulation, can be used in the test flow
async function runSimulation(page) {
  // Navigate to Run Simulation page
  await page.click('[data-testid="stRadio"] label:nth-child(2)');
  await sleep(WAIT_TIME);
  
  // Configure a small simulation
  const populationSlider = await page.waitForSelector('[key="population_size_slider"] [data-testid="stSlider"]');
  const sliderBounds = await populationSlider.boundingBox();
  await page.mouse.click(
    sliderBounds.x + sliderBounds.width * 0.2, 
    sliderBounds.y + sliderBounds.height / 2
  );
  await sleep(WAIT_TIME / 2);
  
  // Run the simulation
  await page.click('.stButton button[kind="primary"]');
  
  // Wait for simulation to complete (max 30 seconds)
  try {
    await page.waitForSelector('.stSuccess', { timeout: 30000 });
    await sleep(WAIT_TIME);
    return true;
  } catch (e) {
    console.log('Simulation might have failed or timed out');
    return false;
  }
}

// Compare two PNG images and generate a diff
function compareImages(img1Path, img2Path, diffPath) {
  try {
    if (!fs.existsSync(img1Path) || !fs.existsSync(img2Path)) {
      console.log(`Missing images for comparison: ${!fs.existsSync(img1Path) ? img1Path : img2Path}`);
      return { pixelDifference: 1, totalPixels: 1, percentDifference: 100 };
    }
    
    const img1 = PNG.sync.read(fs.readFileSync(img1Path));
    const img2 = PNG.sync.read(fs.readFileSync(img2Path));
    
    // Images must have the same dimensions for comparison
    if (img1.width !== img2.width || img1.height !== img2.height) {
      console.log(`Image dimensions don't match: ${img1Path} (${img1.width}x${img1.height}) vs ${img2Path} (${img2.width}x${img2.height})`);
      return { pixelDifference: 1, totalPixels: 1, percentDifference: 100 };
    }
    
    const { width, height } = img1;
    const diff = new PNG({ width, height });
    
    // Compare images using pixelmatch
    const numDiffPixels = pixelmatch(
      img1.data, 
      img2.data, 
      diff.data, 
      width, 
      height, 
      { threshold: THRESHOLD }
    );
    
    // Save the diff image
    fs.writeFileSync(diffPath, PNG.sync.write(diff));
    
    const totalPixels = width * height;
    const percentDifference = (numDiffPixels / totalPixels) * 100;
    
    return {
      pixelDifference: numDiffPixels,
      totalPixels,
      percentDifference
    };
  } catch (error) {
    console.error(`Error comparing images: ${error.message}`);
    return { pixelDifference: 1, totalPixels: 1, percentDifference: 100 };
  }
}

// Main test function
async function runTest() {
  console.log(`Starting visual regression testing in ${MODE} mode`);
  
  const browser = await puppeteer.launch({
    headless: true, // Headless for CI/CD
    defaultViewport: { width: 1280, height: 900 },
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  
  try {
    const page = await browser.newPage();
    
    // Test results storage
    const results = [];
    
    // Run through each test page
    for (const testPage of TEST_PAGES) {
      console.log(`Testing page: ${testPage.name}`);
      
      // Navigate to the page
      await testPage.navigate(page);
      
      // Screenshot filename
      const screenshotName = `${testPage.name}.png`;
      const screenshotPath = path.join(SCREENSHOTS_DIR, screenshotName);
      const baselinePath = path.join(BASELINE_DIR, screenshotName);
      const diffPath = path.join(DIFF_DIR, screenshotName);
      
      // Take the screenshot
      await page.screenshot({ path: screenshotPath, fullPage: true });
      
      if (MODE === 'baseline') {
        // Copy to baseline directory
        fs.copyFileSync(screenshotPath, baselinePath);
        console.log(`Saved baseline for ${testPage.name}`);
        results.push({
          page: testPage.name,
          status: 'baseline_created',
          baselinePath
        });
      } else {
        // Compare with baseline
        if (fs.existsSync(baselinePath)) {
          const comparison = compareImages(baselinePath, screenshotPath, diffPath);
          const passed = comparison.percentDifference < 5; // Less than 5% difference is acceptable
          
          console.log(`Comparison for ${testPage.name}: ${comparison.percentDifference.toFixed(2)}% different`);
          
          results.push({
            page: testPage.name,
            status: passed ? 'passed' : 'failed',
            percentDifference: comparison.percentDifference,
            diffPath: passed ? null : diffPath
          });
          
          if (!passed) {
            console.log(`❌ Visual regression test FAILED for ${testPage.name}`);
            console.log(`   Difference: ${comparison.percentDifference.toFixed(2)}%`);
            console.log(`   Diff saved to: ${diffPath}`);
          } else {
            console.log(`✅ Visual regression test PASSED for ${testPage.name}`);
          }
        } else {
          console.log(`❌ No baseline found for ${testPage.name}`);
          results.push({
            page: testPage.name,
            status: 'no_baseline',
            screenshotPath
          });
        }
      }
    }
    
    // Optional: Run a simulation as part of the test flow
    if (MODE === 'test') {
      console.log('Running simulation test...');
      const simSuccess = await runSimulation(page);
      
      if (simSuccess) {
        // Take a screenshot of the simulation results
        const simScreenshotPath = path.join(SCREENSHOTS_DIR, 'simulation_results.png');
        const simBaselinePath = path.join(BASELINE_DIR, 'simulation_results.png');
        const simDiffPath = path.join(DIFF_DIR, 'simulation_results.png');
        
        await page.screenshot({ path: simScreenshotPath, fullPage: true });
        
        if (fs.existsSync(simBaselinePath)) {
          const comparison = compareImages(simBaselinePath, simScreenshotPath, simDiffPath);
          const passed = comparison.percentDifference < 10; // Higher threshold for dynamic content
          
          console.log(`Comparison for simulation_results: ${comparison.percentDifference.toFixed(2)}% different`);
          
          results.push({
            page: 'simulation_results',
            status: passed ? 'passed' : 'failed',
            percentDifference: comparison.percentDifference,
            diffPath: passed ? null : simDiffPath
          });
          
          if (!passed) {
            console.log(`❌ Visual regression test FAILED for simulation_results`);
          } else {
            console.log(`✅ Visual regression test PASSED for simulation_results`);
          }
        } else {
          console.log(`❌ No baseline found for simulation_results`);
          results.push({
            page: 'simulation_results',
            status: 'no_baseline',
            screenshotPath: simScreenshotPath
          });
        }
      }
    }
    
    // Save test results
    const resultsPath = path.join(__dirname, `visual_regression_${MODE}_results.json`);
    fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2));
    
    if (MODE === 'baseline') {
      console.log(`✅ Baseline screenshots saved successfully!`);
    } else {
      // Check for any failures
      const failures = results.filter(r => r.status === 'failed');
      if (failures.length > 0) {
        console.log(`❌ Visual regression tests completed with ${failures.length} failures`);
        for (const failure of failures) {
          console.log(`  - ${failure.page}: ${failure.percentDifference.toFixed(2)}% different`);
        }
      } else {
        console.log(`✅ All visual regression tests passed!`);
      }
    }
    
  } catch (error) {
    console.error(`Test failed: ${error.message}`);
    console.error(error.stack);
  } finally {
    await browser.close();
  }
}

// Run the test
runTest().catch(console.error);