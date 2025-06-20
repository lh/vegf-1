"""
Script to add clinical improvements section to existing protocols.

This script adds a clinical_improvements section to protocol YAML files
with all improvements disabled by default for backward compatibility.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
import sys


def add_clinical_improvements_to_protocol(yaml_path: Path, enable: bool = False) -> None:
    """
    Add clinical improvements section to a protocol YAML file.
    
    Args:
        yaml_path: Path to the protocol YAML file
        enable: Whether to enable improvements by default
    """
    # Read existing protocol
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Check if already has clinical improvements
    if 'clinical_improvements' in data:
        print(f"✓ {yaml_path.name} already has clinical_improvements section")
        return
    
    # Add clinical improvements section
    clinical_improvements = {
        'enabled': enable,
        'use_loading_phase': True,
        'use_time_based_discontinuation': True,
        'use_response_based_vision': True,
        'use_baseline_distribution': False,  # They already have baseline distribution
        'use_response_heterogeneity': True,
        
        # Parameters can be customized per protocol
        'loading_phase_parameters': {
            'loading_injections': 3,
            'loading_interval_days': 28
        },
        
        'discontinuation_parameters': {
            'annual_probabilities': {
                1: 0.125,
                2: 0.15,
                3: 0.12,
                4: 0.08,
                5: 0.075
            }
        },
        
        'vision_response_parameters': {
            'loading': {'mean': 3.0, 'std': 1.0},
            'year1': {'mean': 0.5, 'std': 0.5},
            'year2': {'mean': 0.0, 'std': 0.5},
            'year3plus': {'mean': -0.2, 'std': 0.3}
        },
        
        'response_types': {
            'good': {'probability': 0.3, 'multiplier': 1.2},
            'average': {'probability': 0.5, 'multiplier': 1.0},
            'poor': {'probability': 0.2, 'multiplier': 0.6}
        }
    }
    
    # Add to data
    data['clinical_improvements'] = clinical_improvements
    
    # Read original file to preserve comments
    with open(yaml_path, 'r') as f:
        original_lines = f.readlines()
    
    # Find where to insert (before discontinuation_rules if it exists)
    insert_index = len(original_lines)
    for i, line in enumerate(original_lines):
        if line.strip().startswith('discontinuation_rules:'):
            insert_index = i
            break
    
    # Create the new section as YAML
    improvements_yaml = yaml.dump(
        {'clinical_improvements': clinical_improvements},
        default_flow_style=False,
        sort_keys=False
    )
    
    # Add header comment
    improvements_section = [
        '\n',
        '# Clinical improvements - optional enhancements for realism\n',
        '# Set enabled: true to activate all improvements\n'
    ] + improvements_yaml.splitlines(keepends=True)
    
    # Insert into original lines
    new_lines = (
        original_lines[:insert_index] + 
        improvements_section + 
        ['\n'] +
        original_lines[insert_index:]
    )
    
    # Write back
    with open(yaml_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"✅ Added clinical_improvements to {yaml_path.name} (enabled={enable})")


def main():
    """Add clinical improvements to all V2 protocols."""
    
    # Get protocol directory
    if len(sys.argv) > 1:
        protocol_dir = Path(sys.argv[1])
    else:
        # Default to v2 protocols relative to this script
        protocol_dir = Path(__file__).parent.parent.parent / "protocols" / "v2"
    
    if not protocol_dir.exists():
        print(f"❌ Protocol directory not found: {protocol_dir}")
        return
    
    print(f"Adding clinical improvements to protocols in: {protocol_dir}")
    print("-" * 60)
    
    # Process all YAML files
    yaml_files = list(protocol_dir.glob("*.yaml")) + list(protocol_dir.glob("*.yml"))
    
    if not yaml_files:
        print("❌ No YAML files found")
        return
    
    for yaml_file in yaml_files:
        try:
            # Skip example and test files
            if 'example' in yaml_file.name or 'test' in yaml_file.name:
                print(f"⏭️  Skipping {yaml_file.name}")
                continue
                
            add_clinical_improvements_to_protocol(yaml_file, enable=False)
            
        except Exception as e:
            print(f"❌ Error processing {yaml_file.name}: {e}")
    
    print("-" * 60)
    print("✅ Done! Clinical improvements added with enabled=false")
    print("   Set enabled: true in any protocol to activate improvements")


if __name__ == "__main__":
    main()