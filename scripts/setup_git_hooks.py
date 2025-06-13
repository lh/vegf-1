#!/usr/bin/env python3
"""
Setup git hooks for automatic testing.

Run this script to install pre-commit hooks that run tests before each commit.
"""

import os
import sys
import stat
from pathlib import Path


PRE_COMMIT_HOOK = '''#!/bin/bash
# Pre-commit hook to run tests before committing

echo "🧪 Running pre-commit tests..."

# Change to the streamlit_app_v2 directory
cd "$(git rev-parse --show-toplevel)/streamlit_app_v2" || exit 1

# Check if we're in the right directory
if [ ! -f "APE.py" ]; then
    echo "❌ Error: Not in streamlit_app_v2 directory"
    exit 1
fi

# Run quick unit tests first (exclude slow UI tests)
echo "📋 Running unit tests..."
python -m pytest tests/ -v --ignore=tests/ui/test_streamlit_ui.py -x
if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed. Commit aborted."
    exit 1
fi

# Check if UI tests should be run
# You can set SKIP_UI_TESTS=1 to skip them
if [ "$SKIP_UI_TESTS" = "1" ]; then
    echo "⏭️  Skipping UI tests (SKIP_UI_TESTS=1)"
else
    echo "🖥️  Running UI tests (set SKIP_UI_TESTS=1 to skip)..."
    python -m pytest tests/ui/test_streamlit_ui.py -v -x
    if [ $? -ne 0 ]; then
        echo "❌ UI tests failed. Commit aborted."
        echo "💡 Tip: Set SKIP_UI_TESTS=1 to skip UI tests for quick commits"
        exit 1
    fi
fi

echo "✅ All tests passed! Proceeding with commit..."
exit 0
'''


def setup_git_hooks():
    """Install git hooks for the project."""
    # Find git directory
    git_dir = Path.cwd()
    while git_dir != git_dir.parent:
        if (git_dir / '.git').exists():
            break
        git_dir = git_dir.parent
    else:
        print("❌ Error: Not in a git repository")
        return False
    
    hooks_dir = git_dir / '.git' / 'hooks'
    pre_commit_path = hooks_dir / 'pre-commit'
    
    # Create backup if hook already exists
    if pre_commit_path.exists():
        backup_path = hooks_dir / 'pre-commit.backup'
        print(f"📁 Backing up existing hook to {backup_path}")
        pre_commit_path.rename(backup_path)
    
    # Write the hook
    print(f"📝 Writing pre-commit hook to {pre_commit_path}")
    pre_commit_path.write_text(PRE_COMMIT_HOOK)
    
    # Make it executable
    st = pre_commit_path.stat()
    pre_commit_path.chmod(st.st_mode | stat.S_IEXEC)
    
    print("✅ Git hooks installed successfully!")
    print("\nUsage:")
    print("  - Tests will run automatically before each commit")
    print("  - To skip UI tests: SKIP_UI_TESTS=1 git commit -m 'message'")
    print("  - To skip all hooks: git commit --no-verify -m 'message'")
    
    return True


if __name__ == "__main__":
    if setup_git_hooks():
        sys.exit(0)
    else:
        sys.exit(1)