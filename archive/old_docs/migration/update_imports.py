#!/usr/bin/env python3
"""
Update import statements after moving files from streamlit_app_v2 to ape directory.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Import mappings
IMPORT_MAPPINGS = {
    # Direct module imports
    'from components': 'from ape.components',
    'from core': 'from ape.core',
    'from pages': 'from ape.pages',
    'from protocols': 'from ape.protocols',
    'from utils': 'from ape.utils',
    'from visualizations': 'from ape.visualizations',
    
    # Relative imports that need updating
    'from ..components': 'from ..ape.components',
    'from ..core': 'from ..ape.core',
    'from ..pages': 'from ..ape.pages',
    'from ..protocols': 'from ..ape.protocols',
    'from ..utils': 'from ..ape.utils',
    'from ..visualizations': 'from ..ape.visualizations',
}

def update_file_imports(file_path: Path) -> List[Tuple[str, str]]:
    """Update imports in a single file."""
    changes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply import mappings
        for old_import, new_import in IMPORT_MAPPINGS.items():
            if old_import in content:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(old_import) + r'\b'
                content = re.sub(pattern, new_import, content)
                changes.append((old_import, new_import))
        
        # Handle sys.path manipulations
        if 'sys.path.append' in content and 'parent.parent' in content:
            # Remove sys.path manipulations as they're no longer needed
            lines = content.split('\n')
            new_lines = []
            skip_next = False
            
            for i, line in enumerate(lines):
                if skip_next:
                    skip_next = False
                    continue
                    
                if 'sys.path.append' in line and 'parent.parent' in line:
                    # Also check if there's an import sys line just for this
                    if i > 0 and 'import sys' in lines[i-1]:
                        new_lines.pop()  # Remove the import sys line
                    changes.append(('sys.path manipulation', 'removed'))
                    continue
                    
                new_lines.append(line)
            
            content = '\n'.join(new_lines)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {file_path}")
            for old, new in changes:
                print(f"  - {old} -> {new}")
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
    
    return changes

def main():
    """Update all Python files in the ape directory."""
    print("Updating imports in APE modules...")
    print("=" * 60)
    
    ape_dir = Path("ape")
    if not ape_dir.exists():
        print("Error: ape directory not found!")
        return
    
    # Find all Python files
    python_files = list(ape_dir.rglob("*.py"))
    print(f"Found {len(python_files)} Python files to update")
    
    total_changes = 0
    for file_path in python_files:
        changes = update_file_imports(file_path)
        total_changes += len(changes)
    
    print(f"\nTotal changes made: {total_changes}")
    
    # Also update any test files that might import from these modules
    print("\nChecking for test files to update...")
    test_locations = [
        Path("tests"),
        Path("streamlit_app_v2/tests"),
        Path("dev/test_scripts")
    ]
    
    test_files = []
    for test_dir in test_locations:
        if test_dir.exists():
            test_files.extend(test_dir.rglob("*.py"))
    
    if test_files:
        print(f"Found {len(test_files)} test files")
        for file_path in test_files:
            changes = update_file_imports(file_path)
            total_changes += len(changes)
    
    print(f"\nImport update complete! Total files changed: {total_changes}")

if __name__ == "__main__":
    main()