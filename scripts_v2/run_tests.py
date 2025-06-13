#!/usr/bin/env python3
"""
Test runner with various options for development.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle output."""
    print(f"\n🧪 {description}")
    print(f"   Command: {' '.join(cmd)}")
    print("-" * 60)
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    
    if result.returncode == 0:
        print(f"✅ {description} passed!")
    else:
        print(f"❌ {description} failed!")
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run tests for streamlit_app_v2")
    parser.add_argument('--all', action='store_true', 
                       help='Run all tests including UI tests')
    parser.add_argument('--ui', action='store_true',
                       help='Run only UI tests')
    parser.add_argument('--unit', action='store_true',
                       help='Run only unit tests (default)')
    parser.add_argument('--watch', action='store_true',
                       help='Watch for changes and re-run tests')
    parser.add_argument('--coverage', action='store_true',
                       help='Run with coverage report')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('-x', '--exitfirst', action='store_true',
                       help='Exit on first failure')
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = ['python', '-m', 'pytest']
    
    if args.verbose:
        base_cmd.append('-v')
    if args.exitfirst:
        base_cmd.append('-x')
    if args.coverage:
        base_cmd.extend(['--cov=.', '--cov-report=html', '--cov-report=term'])
    
    # Determine what to run
    all_success = True
    
    if args.ui:
        # Only UI tests
        cmd = base_cmd + ['tests/ui/test_streamlit_ui.py']
        success = run_command(cmd, "UI Tests")
        all_success = all_success and success
        
    elif args.all:
        # All tests
        cmd = base_cmd + ['tests/']
        success = run_command(cmd, "All Tests")
        all_success = all_success and success
        
    else:
        # Default: unit tests only
        cmd = base_cmd + ['tests/', '--ignore=tests/ui/test_streamlit_ui.py']
        success = run_command(cmd, "Unit Tests")
        all_success = all_success and success
    
    if args.watch:
        print("\n👀 Watching for changes... (Press Ctrl+C to stop)")
        try:
            # Use pytest-watch if available
            watch_cmd = ['ptw'] + base_cmd[2:]  # Skip 'python -m'
            if not args.all and not args.ui:
                watch_cmd.extend(['--ignore=tests/ui/test_streamlit_ui.py'])
            
            subprocess.run(watch_cmd, cwd=Path(__file__).parent.parent)
        except FileNotFoundError:
            print("❌ pytest-watch not installed. Install with: pip install pytest-watch")
            sys.exit(1)
    
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()