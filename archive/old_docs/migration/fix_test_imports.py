#!/usr/bin/env python3
"""Fix imports in test files after refactoring."""

import os
import re
from pathlib import Path

# Import replacements
REPLACEMENTS = [
    # streamlit_app_v2 imports -> ape imports
    (r'from streamlit_app_v2\.components', 'from ape.components'),
    (r'from streamlit_app_v2\.core', 'from ape.core'),
    (r'from streamlit_app_v2\.utils', 'from ape.utils'),
    (r'from streamlit_app_v2\.visualizations', 'from ape.visualizations'),
    
    # Import statements
    (r'import streamlit_app_v2\.components', 'import ape.components'),
    (r'import streamlit_app_v2\.core', 'import ape.core'),
    (r'import streamlit_app_v2\.utils', 'import ape.utils'),
    (r'import streamlit_app_v2\.visualizations', 'import ape.visualizations'),
]

def fix_imports_in_file(filepath):
    """Fix imports in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        for old_pattern, new_pattern in REPLACEMENTS:
            content = re.sub(old_pattern, new_pattern, content)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed imports in: {filepath}")
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

def main():
    """Fix imports in all test files."""
    test_dir = Path("tests")
    
    if not test_dir.exists():
        print("No tests directory found!")
        return
    
    # Find all Python files in tests
    test_files = list(test_dir.rglob("*.py"))
    print(f"Found {len(test_files)} test files")
    
    fixed_count = 0
    for test_file in test_files:
        if fix_imports_in_file(test_file):
            fixed_count += 1
    
    print(f"\nFixed imports in {fixed_count} files")

if __name__ == "__main__":
    main()