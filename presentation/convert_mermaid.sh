#!/bin/bash

# Check if mmdc (mermaid-cli) is installed
if ! command -v mmdc &> /dev/null; then
    echo "mermaid-cli (mmdc) is not installed."
    echo "Install it with: npm install -g @mermaid-js/mermaid-cli"
    exit 1
fi

# Convert the mermaid diagram to PDF with clean styling
echo "Converting APE architecture diagram to PDF..."
mmdc -i ape_architecture.md -o ape_architecture.pdf -t default -b white --pdfFit

echo "Done! Check ape_architecture.pdf"