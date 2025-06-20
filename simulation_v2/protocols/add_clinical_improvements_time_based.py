#!/usr/bin/env python3
"""
Add clinical improvements section to time-based protocols.
Adapted for time-based model characteristics.
"""

import yaml
from pathlib import Path

def add_clinical_improvements_to_time_based():
    """Add clinical improvements section to time-based protocol files."""
    
    # Time-based protocols directory
    protocols_dir = Path(__file__).parent.parent.parent / "protocols" / "v2_time_based"
    
    # Clinical improvements section adapted for time-based models
    clinical_improvements = {
        'enabled': False,
        # Loading phase still makes sense - 3 monthly injections
        'use_loading_phase': True,
        # Time-based discontinuation fits well with the model
        'use_time_based_discontinuation': True,
        # Response-based vision can work with time-based progression
        'use_response_based_vision': True,
        # Baseline distribution is independent of model type
        'use_baseline_distribution': False,
        # Response heterogeneity works for any model
        'use_response_heterogeneity': True,
        # Parameters remain the same
        'loading_phase_parameters': {
            'loading_injections': 3,
            'loading_interval_days': 28
        },
        'discontinuation_parameters': {
            'annual_probabilities': {
                1: 0.125,  # 12.5% in year 1
                2: 0.15,   # 15% in year 2
                3: 0.12,   # 12% in year 3
                4: 0.08,   # 8% in year 4
                5: 0.075   # 7.5% in year 5+
            }
        },
        'vision_response_parameters': {
            'loading': {
                'mean': 3.0,
                'std': 1.0
            },
            'year1': {
                'mean': 0.5,
                'std': 0.5
            },
            'year2': {
                'mean': 0.0,
                'std': 0.5
            },
            'year3plus': {
                'mean': -0.2,
                'std': 0.3
            }
        },
        'response_types': {
            'good': {
                'probability': 0.3,
                'multiplier': 1.2
            },
            'average': {
                'probability': 0.5,
                'multiplier': 1.0
            },
            'poor': {
                'probability': 0.2,
                'multiplier': 0.6
            }
        }
    }
    
    print(f"Adding clinical improvements to time-based protocols in: {protocols_dir}")
    print("-" * 60)
    
    # Process all YAML files
    yaml_files = list(protocols_dir.glob("*.yaml"))
    
    for yaml_file in yaml_files:
        try:
            # Load existing protocol
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
            
            # Check if already has clinical_improvements
            if 'clinical_improvements' in data:
                print(f"✓ {yaml_file.name} already has clinical_improvements section")
                continue
            
            # Add clinical improvements section
            data['clinical_improvements'] = clinical_improvements
            
            # Save updated protocol
            with open(yaml_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            
            print(f"✅ Added clinical_improvements to {yaml_file.name}")
            
        except Exception as e:
            print(f"❌ Error processing {yaml_file.name}: {e}")
    
    print("-" * 60)
    print("✅ Done! Clinical improvements added to time-based protocols")
    print("   Note: Time-based models will need special handling in the engine")


if __name__ == "__main__":
    add_clinical_improvements_to_time_based()