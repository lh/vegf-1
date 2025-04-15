#!/usr/bin/env python3
"""
Numpy docstring parser for the DocGen MCP server.
Parses Python source code and extracts docstrings in Numpy format.
"""

import ast
import json
import sys
from typing import Dict, List, Optional, Any

class DocstringParser(ast.NodeVisitor):
    """AST visitor that extracts docstrings from Python code."""
    
    def __init__(self, strict: bool = False):
        self.docstrings: Dict[str, Any] = {
            'module': None,
            'classes': {},
            'functions': {},
        }
        self.strict = strict
        self.current_class = None
    
    def visit_Module(self, node: ast.Module) -> None:
        """Extract module-level docstring."""
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            self.docstrings['module'] = self._parse_docstring(node.body[0].value.s)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Extract class docstring and method docstrings."""
        prev_class = self.current_class
        self.current_class = node.name
        
        docstring = ast.get_docstring(node)
        if docstring:
            self.docstrings['classes'][node.name] = {
                'docstring': self._parse_docstring(docstring),
                'methods': {},
            }
        
        self.generic_visit(node)
        self.current_class = prev_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Extract function/method docstring."""
        docstring = ast.get_docstring(node)
        if not docstring and self.strict:
            print(f"Warning: Missing docstring for {node.name}", file=sys.stderr)
            return
        
        if docstring:
            parsed = self._parse_docstring(docstring)
            if self.current_class and self.current_class in self.docstrings['classes']:
                self.docstrings['classes'][self.current_class]['methods'][node.name] = parsed
            else:
                self.docstrings['functions'][node.name] = parsed
    
    def _parse_docstring(self, docstring: str) -> Dict[str, Any]:
        """Parse a Numpy-style docstring into structured data.
        
        Parameters
        ----------
        docstring : str
            The docstring to parse
            
        Returns
        -------
        dict
            Structured docstring data with sections like Parameters, Returns, etc.
        """
        sections = {
            'summary': '',
            'parameters': [],
            'returns': [],
            'raises': [],
            'examples': [],
            'notes': [],
        }
        
        current_section = 'summary'
        lines = docstring.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line in ('Parameters', 'Returns', 'Raises', 'Examples', 'Notes'):
                current_section = line.lower()
                i += 2  # Skip the section header and dashed line
                continue
            
            if current_section == 'summary':
                if line:
                    sections['summary'] += line + ' '
            
            elif current_section == 'parameters':
                if line and ' : ' in line:
                    param_name, param_type = line.split(' : ', 1)
                    param_desc = []
                    i += 1
                    while i < len(lines) and lines[i].strip():
                        param_desc.append(lines[i].strip())
                        i += 1
                    sections['parameters'].append({
                        'name': param_name.strip(),
                        'type': param_type.strip(),
                        'description': ' '.join(param_desc)
                    })
                    continue
            
            elif current_section in ('returns', 'raises'):
                if line:
                    sections[current_section].append(line)
            
            elif current_section in ('examples', 'notes'):
                if line:
                    sections[current_section].append(line)
            
            i += 1
        
        sections['summary'] = sections['summary'].strip()
        return sections

def parse_source(source_code: str, strict: bool = False) -> Dict[str, Any]:
    """Parse Python source code and extract docstrings.
    
    Parameters
    ----------
    source_code : str
        Python source code to parse
    strict : bool, optional
        Enable strict validation, by default False
        
    Returns
    -------
    dict
        Structured docstring data for the module, classes, and functions
    """
    tree = ast.parse(source_code)
    parser = DocstringParser(strict=strict)
    parser.visit(tree)
    return parser.docstrings

def main():
    """Main entry point for CLI usage."""
    try:
        input_data = json.loads(sys.stdin.readline())
        result = parse_source(input_data['code'], input_data.get('strict', False))
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({
            'error': str(e),
            'type': type(e).__name__
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
