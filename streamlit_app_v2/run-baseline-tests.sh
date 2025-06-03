#!/bin/bash

# Script to run all baseline tests for Carbon button migration
echo "🧪 Running baseline tests for Carbon button migration..."
echo "=================================================="

# Create reports directory if it doesn't exist
mkdir -p tests/playwright/reports

# Check if Streamlit app is running
if ! curl -s http://localhost:8502 > /dev/null; then
    echo "⚠️  Streamlit app is not running on port 8502"
    echo "Starting Streamlit app in background..."
    streamlit run APE.py --server.port 8502 --server.headless true &
    STREAMLIT_PID=$!
    echo "Waiting for Streamlit to start..."
    sleep 10
else
    echo "✅ Streamlit app is already running"
    STREAMLIT_PID=""
fi

# Run button inventory first
echo ""
echo "📋 Creating button inventory..."
npx playwright test tests/playwright/baseline/button-inventory.spec.ts

# Run navigation baseline tests
echo ""
echo "🧭 Testing navigation buttons..."
npx playwright test tests/playwright/baseline/navigation-buttons.spec.ts

# Run form button tests
echo ""
echo "📝 Testing form buttons..."
npx playwright test tests/playwright/baseline/form-buttons.spec.ts

# Run export button tests
echo ""
echo "📥 Testing export buttons..."
npx playwright test tests/playwright/baseline/export-buttons.spec.ts

# Run visual regression baseline
echo ""
echo "📸 Capturing visual baselines..."
npx playwright test tests/playwright/visual/visual-regression.spec.ts --update-snapshots

# Run accessibility baseline
echo ""
echo "♿ Running accessibility checks..."
npx playwright test tests/playwright/accessibility/a11y-baseline.spec.ts

# Run performance baseline
echo ""
echo "⚡ Measuring performance baseline..."
npx playwright test tests/playwright/performance/perf-baseline.spec.ts

# Generate HTML report
echo ""
echo "📊 Generating test report..."
npx playwright show-report

# Stop Streamlit if we started it
if [ ! -z "$STREAMLIT_PID" ]; then
    echo ""
    echo "Stopping Streamlit app..."
    kill $STREAMLIT_PID
fi

echo ""
echo "✅ Baseline testing complete!"
echo ""
echo "📁 Reports saved to:"
echo "   - tests/playwright/reports/"
echo "   - tests/playwright/screenshots/"
echo "   - playwright-report/index.html"
echo ""
echo "Next steps:"
echo "1. Review the button inventory in tests/playwright/reports/button-inventory.md"
echo "2. Check baseline metrics in tests/playwright/reports/"
echo "3. Proceed to Day 1: Test Infrastructure Setup"