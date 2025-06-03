#!/bin/bash

# Setup script for Playwright testing infrastructure
echo "🚀 Setting up Playwright for Carbon button migration testing..."

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js and npm first."
    exit 1
fi

# Install dependencies
echo "📦 Installing Playwright and dependencies..."
npm install

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
npx playwright install chromium firefox webkit

# Create necessary directories
echo "📁 Creating test directories..."
mkdir -p tests/playwright/{screenshots,reports,downloads}

# Make script executable
chmod +x run-baseline-tests.sh

echo "✅ Playwright setup complete!"
echo ""
echo "Next steps:"
echo "1. Run baseline tests: ./run-baseline-tests.sh"
echo "2. Review reports in tests/playwright/reports/"
echo "3. Start Day 1 implementation after baseline is established"