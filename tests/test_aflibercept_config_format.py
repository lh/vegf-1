#!/usr/bin/env python3
"""Test the aflibercept config format handling.

This test documents the expected format for configs that use:
- Nested drug cost objects with unit_cost and list_price
- Visit types with total_override instead of total_cost
- Automatic calculation of totals from components when override is null
"""

import yaml
from pathlib import Path

# Load the aflibercept config
config_path = Path("protocols/cost_configs/aflibercept_2mg_nhs_2025.yaml")
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

print("Aflibercept Config Analysis")
print("=" * 50)

# Check drug costs
print("\nDrug Costs:")
drug_costs = config.get('drug_costs', {})
for drug_id, cost_data in drug_costs.items():
    if isinstance(cost_data, dict):
        unit_cost = cost_data.get('unit_cost', 0)
        list_price = cost_data.get('list_price', None)
        print(f"  {drug_id}: Unit Cost = £{unit_cost}, List Price = £{list_price}")
    else:
        print(f"  {drug_id}: £{cost_data}")

# Check visit components
print("\nVisit Components:")
components = config.get('visit_components', {})
for comp_id, cost in sorted(components.items()):
    print(f"  {comp_id}: £{cost}")

# Check visit types
print("\nVisit Types:")
visit_types = config.get('visit_types', {})
for visit_name, visit_info in visit_types.items():
    print(f"\n  {visit_name}:")
    if 'components' in visit_info:
        component_total = sum(components.get(comp, 0) for comp in visit_info['components'])
        print(f"    Components: {visit_info['components']}")
        print(f"    Calculated Total: £{component_total}")
    
    total_override = visit_info.get('total_override')
    total_cost = visit_info.get('total_cost')
    print(f"    total_override: {total_override}")
    print(f"    total_cost: {total_cost}")
    
    # Logic from our fix
    if total_cost is not None:
        final_total = total_cost
    elif total_override is not None:
        final_total = total_override
    else:
        final_total = component_total
    print(f"    Final Total: £{final_total}")