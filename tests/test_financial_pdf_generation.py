#!/usr/bin/env python3
"""Test financial PDF generation."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ape.utils.financial_pdf_generator import generate_financial_parameters_pdf

# Test with default resource configuration
print("Generating financial parameters PDF...")
try:
    pdf_bytes = generate_financial_parameters_pdf()
    
    # Save to file for inspection
    output_file = Path("test_financial_parameters.pdf")
    with open(output_file, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"✅ PDF generated successfully!")
    print(f"   Size: {len(pdf_bytes):,} bytes")
    print(f"   Saved to: {output_file}")
    
except Exception as e:
    print(f"❌ Error generating PDF: {e}")
    import traceback
    traceback.print_exc()