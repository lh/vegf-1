#!/usr/bin/env python3
"""Test workload results PDF generation."""

import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ape.utils.workload_results_pdf_generator import generate_workload_results_pdf

# Test data
simulation_info = {
    'protocol': 'T&E Standard',
    'n_patients': 1000,
    'duration_years': 5,
    'engine': 'ABS',
    'seed': '12345'
}

workload_summary = {
    'total_visits': 45678,
    'peak_daily_demand': {
        'injector': 28,
        'vision_tester': 35,
        'oct_operator': 32,
        'decision_maker': 24
    },
    'average_daily_demand': {
        'injector': 15.3,
        'vision_tester': 18.7,
        'oct_operator': 16.2,
        'decision_maker': 12.8
    },
    'total_sessions_needed': {
        'injector': 3265,
        'vision_tester': 2987,
        'oct_operator': 3102,
        'decision_maker': 2845
    }
}

total_costs = {
    'total': 2456789,
    'drug': 1850000,
    'injection_procedure': 380000,
    'consultation': 125000,
    'oct_scan': 101789
}

utilization_data = [
    {
        'Role': 'injector',
        'Average Daily Demand': '15.3',
        'Peak Daily Demand': 28,
        'Utilization %': '55%',
        'Total Sessions': 3265
    },
    {
        'Role': 'vision_tester',
        'Average Daily Demand': '18.7',
        'Peak Daily Demand': 35,
        'Utilization %': '47%',
        'Total Sessions': 2987
    }
]

staffing_data = [
    {
        'Role': 'injector',
        'Average Sessions/Day': '1.1',
        'Peak Sessions': '2.0',
        'Staff Needed (Average)': '0.55',
        'Staff Needed (Peak)': 1
    },
    {
        'Role': 'vision_tester',
        'Average Sessions/Day': '0.9',
        'Peak Sessions': '1.8',
        'Staff Needed (Average)': '0.45',
        'Staff Needed (Peak)': 1
    }
]

bottlenecks = [
    {
        'date': '2024-03-15',
        'role': 'injector',
        'sessions_needed': 2.5,
        'sessions_available': 2,
        'overflow': 0.5,
        'procedures_affected': 7
    },
    {
        'date': '2024-06-22',
        'role': 'decision_maker',
        'sessions_needed': 2.2,
        'sessions_available': 2,
        'overflow': 0.2,
        'procedures_affected': 3
    }
]

# Test PDF generation
print("Generating workload results PDF...")
try:
    pdf_bytes = generate_workload_results_pdf(
        simulation_info=simulation_info,
        workload_summary=workload_summary,
        total_costs=total_costs,
        utilization_data=utilization_data,
        staffing_data=staffing_data,
        bottlenecks=bottlenecks
    )
    
    # Save to file for inspection
    output_file = Path("test_workload_results.pdf")
    with open(output_file, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"✅ PDF generated successfully!")
    print(f"   Size: {len(pdf_bytes):,} bytes")
    print(f"   Saved to: {output_file}")
    
except Exception as e:
    print(f"❌ Error generating PDF: {e}")
    import traceback
    traceback.print_exc()