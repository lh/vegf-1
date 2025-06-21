#!/bin/bash
# Compile the NAMD presentation with LuaLaTeX

cd "$(dirname "$0")"

echo "Compiling NAMD presentation with LuaLaTeX..."
lualatex -interaction=nonstopmode namd_presentation.tex

# Run twice for references
echo "Second pass for references..."
lualatex -interaction=nonstopmode namd_presentation.tex

echo "Done! PDF created: namd_presentation.pdf"