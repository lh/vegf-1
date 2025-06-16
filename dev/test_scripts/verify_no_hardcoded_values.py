#!/usr/bin/env python3
"""
Verify that the parameter-driven engine has no hardcoded values.
"""

import sys
import ast
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def find_hardcoded_values(file_path):
    """Find potential hardcoded numeric values in a Python file."""
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())
    
    hardcoded = []
    
    class NumericVisitor(ast.NodeVisitor):
        def visit_Num(self, node):
            # Check for numeric literals (Python < 3.8)
            if isinstance(node.n, (int, float)) and node.n not in [0, 1, -1, 100]:
                hardcoded.append((node.n, node.lineno))
            self.generic_visit(node)
        
        def visit_Constant(self, node):
            # Check for numeric constants (Python >= 3.8)
            if isinstance(node.value, (int, float)) and node.value not in [0, 1, -1, 100]:
                hardcoded.append((node.value, node.lineno))
            self.generic_visit(node)
    
    NumericVisitor().visit(tree)
    return hardcoded

def check_file(file_path):
    """Check a file for hardcoded values."""
    print(f"\n{'='*60}")
    print(f"Checking: {file_path.name}")
    print('='*60)
    
    hardcoded = find_hardcoded_values(file_path)
    
    if hardcoded:
        print(f"Found {len(hardcoded)} potential hardcoded values:")
        for value, line in hardcoded:
            print(f"  Line {line}: {value}")
            
        # Read the actual lines for context
        with open(file_path) as f:
            lines = f.readlines()
        
        print("\nContext for each value:")
        for value, line_num in hardcoded:
            if 0 < line_num <= len(lines):
                line_text = lines[line_num - 1].strip()
                print(f"  Line {line_num}: {line_text}")
    else:
        print("✓ No obvious hardcoded values found!")

def main():
    """Check both time-based engines for hardcoded values."""
    
    # Check the original engine
    original_engine = Path("simulation_v2/engines/abs_engine_time_based.py")
    check_file(original_engine)
    
    # Check the specs wrapper
    specs_engine = Path("simulation_v2/engines/abs_engine_time_based_with_specs.py")
    check_file(specs_engine)
    
    # Check the new parameter-driven engine
    params_engine = Path("simulation_v2/engines/abs_engine_time_based_with_params.py")
    check_file(params_engine)
    
    print("\n" + "="*60)
    print("Summary:")
    print("="*60)
    print("The ABSEngineTimeBasedWithParams should have NO hardcoded values.")
    print("All numeric values should come from parameter files.")

if __name__ == "__main__":
    main()