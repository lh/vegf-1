#!/usr/bin/env python3
"""Test PDF generation for protocols."""

from pathlib import Path
from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from ape.utils.protocol_pdf_generator import generate_protocol_pdf

# Test with a time-based protocol
protocol_file = Path("protocols/v2_time_based/aflibercept_tae_8week_min_time_based.yaml")

if protocol_file.exists():
    print(f"Loading protocol from {protocol_file}")
    spec = TimeBasedProtocolSpecification.from_yaml(protocol_file)
    
    print(f"Protocol name: {spec.name}")
    print(f"Protocol version: {spec.version}")
    
    print("\nGenerating PDF...")
    try:
        pdf_bytes = generate_protocol_pdf(spec, is_time_based=True)
        
        # Save to file for inspection
        output_file = Path("test_protocol_report.pdf")
        with open(output_file, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"✅ PDF generated successfully!")
        print(f"   Size: {len(pdf_bytes):,} bytes")
        print(f"   Saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"Protocol file not found: {protocol_file}")