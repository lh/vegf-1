#!/usr/bin/env python3
"""
Analyze import dependencies in the streamlit_app_v2 directory.
This helps identify potential circular dependencies and complex import chains
before refactoring.
"""

import os
import ast
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class ImportAnalyzer(ast.NodeVisitor):
    """Extract imports from Python files."""
    
    def __init__(self):
        self.imports = []
        self.from_imports = []
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.from_imports.append({
                'module': node.module,
                'names': [alias.name for alias in node.names],
                'level': node.level
            })
        self.generic_visit(node)

def analyze_file(file_path: Path) -> Dict[str, List]:
    """Analyze imports in a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        analyzer = ImportAnalyzer()
        analyzer.visit(tree)
        
        return {
            'imports': analyzer.imports,
            'from_imports': analyzer.from_imports
        }
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return {'imports': [], 'from_imports': []}

def categorize_imports(import_data: Dict[str, List]) -> Dict[str, Set[str]]:
    """Categorize imports into internal, external, and standard library."""
    categories = {
        'internal': set(),
        'external': set(),
        'stdlib': set()
    }
    
    # Common standard library modules
    stdlib_modules = {
        'os', 'sys', 'json', 'datetime', 'time', 'pathlib', 'collections',
        'itertools', 'functools', 'typing', 'enum', 'dataclasses', 'abc',
        'math', 'random', 'statistics', 'decimal', 'fractions', 'numbers',
        're', 'string', 'textwrap', 'unicodedata', 'struct', 'codecs',
        'io', 'pickle', 'csv', 'configparser', 'logging', 'warnings',
        'traceback', 'inspect', 'ast', 'importlib', 'pkgutil'
    }
    
    # Known external packages
    external_packages = {
        'streamlit', 'pandas', 'numpy', 'plotly', 'matplotlib', 'seaborn',
        'scipy', 'sklearn', 'yaml', 'pyyaml', 'requests', 'pytest',
        'altair', 'bokeh', 'holoviews', 'dash'
    }
    
    all_imports = set(import_data['imports'])
    
    for from_import in import_data['from_imports']:
        module = from_import['module']
        if module:
            all_imports.add(module.split('.')[0])
    
    for module in all_imports:
        base_module = module.split('.')[0]
        
        if base_module in stdlib_modules:
            categories['stdlib'].add(module)
        elif base_module in external_packages:
            categories['external'].add(module)
        elif base_module in ['pages', 'components', 'core', 'utils', 'visualizations', 'protocols']:
            categories['internal'].add(module)
        else:
            # Assume internal if not recognized
            categories['internal'].add(module)
    
    return categories

def find_circular_dependencies(dependencies: Dict[str, Set[str]]) -> List[List[str]]:
    """Find circular import dependencies."""
    circles = []
    visited = set()
    rec_stack = set()
    
    def dfs(module: str, path: List[str]) -> None:
        visited.add(module)
        rec_stack.add(module)
        path.append(module)
        
        if module in dependencies:
            for dep in dependencies[module]:
                if dep not in visited:
                    dfs(dep, path.copy())
                elif dep in rec_stack and dep in path:
                    # Found a cycle
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:] + [dep]
                    if cycle not in circles and list(reversed(cycle)) not in circles:
                        circles.append(cycle)
        
        path.pop()
        rec_stack.remove(module)
    
    for module in dependencies:
        if module not in visited:
            dfs(module, [])
    
    return circles

def main():
    """Main analysis function."""
    print("Analyzing import dependencies in streamlit_app_v2...")
    print("=" * 60)
    
    base_dir = Path("streamlit_app_v2")
    if not base_dir.exists():
        print(f"Error: {base_dir} directory not found!")
        return
    
    # Collect all Python files
    python_files = list(base_dir.rglob("*.py"))
    print(f"Found {len(python_files)} Python files")
    
    # Analyze each file
    file_dependencies = {}
    internal_dependencies = defaultdict(set)
    
    for file_path in python_files:
        rel_path = file_path.relative_to(base_dir)
        module_name = str(rel_path).replace('/', '.').replace('\\', '.')[:-3]
        
        import_data = analyze_file(file_path)
        categories = categorize_imports(import_data)
        
        file_dependencies[module_name] = {
            'file': str(rel_path),
            'categories': {k: list(v) for k, v in categories.items()},
            'raw_imports': import_data
        }
        
        # Build internal dependency graph
        for from_import in import_data['from_imports']:
            if from_import['module'] and from_import['module'].startswith(('pages', 'components', 'core', 'utils', 'visualizations', 'protocols')):
                internal_dependencies[module_name].add(from_import['module'])
    
    # Find circular dependencies
    circles = find_circular_dependencies(internal_dependencies)
    
    # Generate report
    report = {
        'summary': {
            'total_files': len(python_files),
            'circular_dependencies': len(circles),
            'modules_with_most_dependencies': []
        },
        'circular_dependencies': circles,
        'file_analysis': file_dependencies,
        'dependency_graph': {k: list(v) for k, v in internal_dependencies.items()}
    }
    
    # Find modules with most dependencies
    dep_counts = [(mod, len(deps)) for mod, deps in internal_dependencies.items()]
    dep_counts.sort(key=lambda x: x[1], reverse=True)
    report['summary']['modules_with_most_dependencies'] = dep_counts[:10]
    
    # Print summary
    print("\nSummary:")
    print(f"- Total Python files: {len(python_files)}")
    print(f"- Circular dependencies found: {len(circles)}")
    
    if circles:
        print("\nCircular Dependencies:")
        for i, circle in enumerate(circles, 1):
            print(f"  {i}. {' -> '.join(circle)}")
    
    print("\nTop 10 modules by dependency count:")
    for mod, count in dep_counts[:10]:
        print(f"  - {mod}: {count} dependencies")
    
    # Save detailed report
    output_file = "dev/migration/import_analysis_report.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {output_file}")
    
    # Check for potential issues
    print("\nPotential Issues:")
    issues_found = False
    
    # Check for pages importing from each other
    page_cross_imports = []
    for mod, deps in internal_dependencies.items():
        if mod.startswith('pages.'):
            for dep in deps:
                if dep.startswith('pages.') and dep != mod:
                    page_cross_imports.append((mod, dep))
    
    if page_cross_imports:
        issues_found = True
        print("- Pages importing from other pages (potential issue):")
        for src, dst in page_cross_imports[:5]:
            print(f"    {src} -> {dst}")
        if len(page_cross_imports) > 5:
            print(f"    ... and {len(page_cross_imports) - 5} more")
    
    if not issues_found:
        print("- No major issues found!")
    
    print("\nNext steps:")
    print("1. Review circular dependencies (if any)")
    print("2. Check page cross-imports")
    print("3. Plan module reorganization based on dependency patterns")

if __name__ == "__main__":
    main()