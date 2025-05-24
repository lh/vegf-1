#!/bin/bash

# MCP Code Checker Installation Script
echo "🚀 Installing MCP Code Checker..."

# Define installation directory
MCP_DIR="$HOME/Code/mcp"
CODE_CHECKER_DIR="$MCP_DIR/mcp-code-checker"

# Create MCP directory if it doesn't exist
echo "📁 Creating MCP directory structure..."
mkdir -p "$MCP_DIR"

# Navigate to MCP directory
cd "$MCP_DIR"

# Clone the repository
echo "📥 Cloning mcp-code-checker repository..."
if [ -d "$CODE_CHECKER_DIR" ]; then
    echo "   Directory already exists, pulling latest changes..."
    cd "$CODE_CHECKER_DIR"
    git pull
else
    git clone https://github.com/MarcusJellinghaus/mcp-code-checker.git
    cd "$CODE_CHECKER_DIR"
fi

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "   Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -e .

echo "✅ Installation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Add the MCP server to Claude's configuration"
echo "2. The command to run the server is:"
echo "   cd $CODE_CHECKER_DIR"
echo "   source .venv/bin/activate"
echo "   python -m src.main --project-dir /Users/rose/Code/CC"
echo ""
echo "Or use the Claude MCP command:"
echo "   claude mcp add code-checker -s user -- python -m src.main --project-dir /Users/rose/Code/CC"