#!/bin/bash

# MCP Code Checker Installation Script (Using Python 3.13)
echo "🚀 Installing MCP Code Checker with Python 3.13..."

# Define installation directory
MCP_DIR="$HOME/Code/mcp"
CODE_CHECKER_DIR="$MCP_DIR/mcp-code-checker"
PYTHON313="/opt/homebrew/bin/python3"

# Verify Python 3.13 is available
echo "🐍 Checking Python version..."
PYTHON_VERSION=$($PYTHON313 --version 2>&1)
echo "   Found: $PYTHON_VERSION"

if [[ ! $PYTHON_VERSION =~ "3.13" ]]; then
    echo "❌ Error: Python 3.13 not found at $PYTHON313"
    exit 1
fi

# Create MCP directory if it doesn't exist
echo "📁 Creating MCP directory structure..."
mkdir -p "$MCP_DIR"

# Navigate to MCP directory
cd "$MCP_DIR"

# Remove existing directory if present and clone fresh
echo "📥 Setting up mcp-code-checker repository..."
if [ -d "$CODE_CHECKER_DIR" ]; then
    echo "   Removing existing directory..."
    rm -rf "$CODE_CHECKER_DIR"
fi

git clone https://github.com/MarcusJellinghaus/mcp-code-checker.git
cd "$CODE_CHECKER_DIR"

# Create virtual environment with Python 3.13
echo "🐍 Creating Python 3.13 virtual environment..."
$PYTHON313 -m venv .venv

# Activate virtual environment
echo "   Activating virtual environment..."
source .venv/bin/activate

# Verify we're using the right Python
echo "   Verifying Python version in venv..."
python --version

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -e .

echo "✅ Installation complete!"
echo ""
echo "📝 Adding to Claude configuration..."

# Create a wrapper script for easier execution
echo "📄 Creating wrapper script..."
cat > "$CODE_CHECKER_DIR/run_mcp_server.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
python -m src.main "$@"
EOF
chmod +x "$CODE_CHECKER_DIR/run_mcp_server.sh"

# Add to Claude MCP configuration
echo "   Adding code-checker to Claude MCP..."
claude mcp add code-checker -s user -- "$CODE_CHECKER_DIR/run_mcp_server.sh" --project-dir /Users/rose/Code/CC

echo ""
echo "🎉 MCP Code Checker installed and configured!"
echo "   The server will automatically connect when Claude starts."
echo "   Project directory: /Users/rose/Code/CC"
echo ""
echo "To manually run the server:"
echo "   $CODE_CHECKER_DIR/run_mcp_server.sh --project-dir /Users/rose/Code/CC"