#!/bin/bash
# Development environment setup script

echo "🚀 Setting up development environment for streamlit_app_v2"

# Check if in correct directory
if [ ! -f "APE.py" ]; then
    echo "❌ Error: Please run this script from the streamlit_app_v2 directory"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install dev dependencies
echo "📦 Installing development dependencies..."
pip install pytest pytest-cov pytest-watch pytest-xdist
pip install playwright
playwright install chromium

# Setup git hooks
echo "🪝 Setting up git hooks..."
python scripts/setup_git_hooks.py

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOL
# Development settings
SKIP_UI_TESTS=0
PYTEST_WORKERS=auto
EOL
fi

echo "✅ Development setup complete!"
echo ""
echo "Quick commands:"
echo "  Run all tests:      python scripts/run_tests.py --all"
echo "  Run unit tests:     python scripts/run_tests.py"
echo "  Run UI tests:       python scripts/run_tests.py --ui"
echo "  Watch mode:         python scripts/run_tests.py --watch"
echo "  Skip UI on commit:  SKIP_UI_TESTS=1 git commit -m 'message'"