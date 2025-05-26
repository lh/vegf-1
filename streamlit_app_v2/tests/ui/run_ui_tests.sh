#!/bin/bash

# Script to run Streamlit UI tests with Playwright

echo "Streamlit UI Test Runner"
echo "========================"
echo ""

# Check if Streamlit is running
if ! curl -s http://localhost:8501 > /dev/null; then
    echo "⚠️  Streamlit app is not running on http://localhost:8501"
    echo ""
    echo "Please start the app first:"
    echo "  cd streamlit_app_v2"
    echo "  streamlit run APE.py"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ Streamlit app detected on http://localhost:8501"
echo ""

# Check if Playwright is installed
if ! python -c "import playwright" 2>/dev/null; then
    echo "Installing Playwright..."
    pip install playwright pytest-playwright
    playwright install chromium
fi

# Run the tests
echo "Running UI tests..."
echo ""

# Run with different verbosity based on argument
if [ "$1" == "-v" ]; then
    pytest tests/ui/test_streamlit_ui.py -v
elif [ "$1" == "-vv" ]; then
    pytest tests/ui/test_streamlit_ui.py -vv -s
elif [ "$1" == "--headed" ]; then
    # Run with visible browser
    HEADED=true pytest tests/ui/test_streamlit_ui.py -v
else
    pytest tests/ui/test_streamlit_ui.py
fi

echo ""
echo "UI tests completed!"