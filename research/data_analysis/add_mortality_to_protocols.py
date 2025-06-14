"""
Add mortality parameters to existing protocol YAML files based on real-world data analysis
"""

import yaml
import os
from pathlib import Path
import argparse
from typing import Dict, Any

# Mortality parameters from our analysis
MORTALITY_PARAMS = {
    'mortality': {
        'enabled': True,
        'base_annual_rate': 0.078,  # 7.8% per year from patient-year analysis
        'monthly_rate': 0.0065,     # Approximate monthly rate
        'age_adjustment': {
            'enabled': True,
            'reference_age': 89.5,   # Average age at death
            'min_age': 70,          # Minimum observed death age
            'max_age': 106,         # Maximum observed death age
            'comment': 'Mortality risk doubles approximately every 8 years'
        },
        'treatment_gap_multipliers': {
            'regular': 1.0,         # <90 days between injections
            'short_gap': 1.22,      # 90-180 days
            'long_gap': 1.34,       # 180-365 days  
            'discontinued': 1.37,   # >365 days
            'comment': 'Multipliers based on observed mortality by treatment pattern'
        },
        'data_source': 'Real-world Eylea patient data (n=1,775, 2007-2025)',
        'notes': [
            'Based on 7.8 deaths per 100 patient-years',
            'Average age at death: 89.5 years',
            'Treatment gaps significantly increase mortality risk'
        ]
    }
}

def load_protocol(filepath: Path) -> Dict[str, Any]:
    """Load a protocol YAML file."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def save_protocol(filepath: Path, protocol: Dict[str, Any], backup: bool = True):
    """Save protocol back to YAML file."""
    if backup and filepath.exists():
        backup_path = filepath.with_suffix('.yaml.backup')
        filepath.rename(backup_path)
        print(f"Created backup: {backup_path}")
    
    with open(filepath, 'w') as f:
        yaml.dump(protocol, f, default_flow_style=False, sort_keys=False, width=120)

def add_mortality_to_protocol(protocol: Dict[str, Any]) -> Dict[str, Any]:
    """Add mortality parameters to a protocol if not already present."""
    if 'mortality' in protocol:
        print("  Protocol already has mortality parameters")
        response = input("  Overwrite existing mortality parameters? (y/n): ").lower()
        if response != 'y':
            return protocol
    
    # Add mortality parameters
    protocol['mortality'] = MORTALITY_PARAMS['mortality'].copy()
    return protocol

def process_protocols(directory: Path, dry_run: bool = False):
    """Process all protocol files in a directory."""
    yaml_files = list(directory.glob('*.yaml')) + list(directory.glob('*.yml'))
    
    if not yaml_files:
        print(f"No YAML files found in {directory}")
        return
    
    print(f"Found {len(yaml_files)} protocol files in {directory}")
    
    for filepath in yaml_files:
        print(f"\nProcessing: {filepath.name}")
        
        try:
            protocol = load_protocol(filepath)
            
            # Skip if not a protocol file (check for required fields)
            if not all(key in protocol for key in ['name', 'phases']):
                print(f"  Skipping - doesn't appear to be a protocol file")
                continue
            
            # Add mortality parameters
            updated_protocol = add_mortality_to_protocol(protocol)
            
            if not dry_run:
                save_protocol(filepath, updated_protocol)
                print(f"  ✓ Updated with mortality parameters")
            else:
                print(f"  Would add mortality parameters (dry run)")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Add mortality parameters to AMD protocol files'
    )
    parser.add_argument(
        '--dir',
        type=str,
        default='protocols',
        help='Directory containing protocol YAML files (default: protocols)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--single',
        type=str,
        help='Process a single protocol file'
    )
    
    args = parser.parse_args()
    
    if args.single:
        filepath = Path(args.single)
        if not filepath.exists():
            print(f"Error: File not found: {filepath}")
            return
            
        print(f"Processing single file: {filepath}")
        try:
            protocol = load_protocol(filepath)
            updated_protocol = add_mortality_to_protocol(protocol)
            
            if not args.dry_run:
                save_protocol(filepath, updated_protocol)
                print("✓ Updated with mortality parameters")
            else:
                print("Would add mortality parameters (dry run)")
                print("\nMortality parameters to add:")
                print(yaml.dump(MORTALITY_PARAMS, default_flow_style=False))
                
        except Exception as e:
            print(f"Error: {e}")
    else:
        protocol_dir = Path(args.dir)
        if not protocol_dir.exists():
            print(f"Error: Directory not found: {protocol_dir}")
            return
            
        process_protocols(protocol_dir, args.dry_run)
    
    if args.dry_run:
        print("\n" + "="*60)
        print("DRY RUN - No files were modified")
        print("Run without --dry-run to apply changes")

if __name__ == "__main__":
    main()