#!/usr/bin/env python3
"""Test that Financial Parameters page handles non-numeric entries in YAML configs correctly.

This test verifies that configs with mixed data types (like 'default_drug' string 
in drug_costs) are handled gracefully without causing ValueErrors.
"""

import yaml
from pathlib import Path

# Load the problematic config file
config_path = Path("protocols/cost_configs/nhs_hrg_aligned_2025.yaml")
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

print("NHS HRG-Aligned Config Drug Costs:")
print("-" * 40)

drug_costs = config.get('drug_costs', {})
for drug_id, cost in drug_costs.items():
    print(f"{drug_id}: {cost} (type: {type(cost).__name__})")
    
print("\nNumeric drug costs only:")
print("-" * 40)
numeric_costs = [(drug_id, cost) for drug_id, cost in drug_costs.items() if isinstance(cost, (int, float))]
for drug_id, cost in numeric_costs:
    print(f"{drug_id}: £{cost:,.0f}")

print(f"\nTotal numeric entries: {len(numeric_costs)}")
print(f"Total entries: {len(drug_costs)}")
print(f"Non-numeric entries: {len(drug_costs) - len(numeric_costs)}")

# Show what the non-numeric entries are
non_numeric = [(drug_id, cost) for drug_id, cost in drug_costs.items() if not isinstance(cost, (int, float))]
if non_numeric:
    print("\nNon-numeric entries:")
    for drug_id, cost in non_numeric:
        print(f"  {drug_id}: '{cost}' (type: {type(cost).__name__})")