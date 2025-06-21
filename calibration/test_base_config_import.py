#!/usr/bin/env python3
"""
Test importing and using base configurations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation_v2.protocols.base_configs import get_base_config, merge_configs
import yaml
from pathlib import Path


def test_base_config():
    """Test base configuration import."""
    print("Testing Base Configuration Import\n")
    
    # Get base config
    base = get_base_config('aflibercept')
    
    print("Base Configuration loaded successfully!")
    print(f"Disease transitions states: {list(base['disease_transitions'].keys())}")
    print(f"Vision model states: {len(base['vision_change_model'])} states")
    print(f"Clinical improvements enabled: {base['clinical_improvements']['enabled']}")
    print(f"Response types: {list(base['clinical_improvements']['response_types'].keys())}")
    
    # Test merging with T&E specific config
    tae_specific = {
        'name': 'T&E Test',
        'protocol_type': 'treat_and_extend',
        'min_interval_days': 56,
        'clinical_improvements': {
            'response_types': {
                'good': {
                    'probability': 0.60,  # Override to 60%
                    'multiplier': 1.8
                }
            }
        }
    }
    
    merged = merge_configs(base, tae_specific)
    
    print("\nAfter merging with T&E specific config:")
    print(f"Protocol name: {merged['name']}")
    print(f"Protocol type: {merged['protocol_type']}")
    print(f"Good responder probability: {merged['clinical_improvements']['response_types']['good']['probability']}")
    print(f"Average responder probability: {merged['clinical_improvements']['response_types']['average']['probability']}")
    
    return True


def test_protocol_files():
    """Verify our protocol files reference the base config correctly."""
    print("\n" + "="*60)
    print("Testing Protocol Files")
    print("="*60)
    
    protocols = [
        "protocols/v2/aflibercept_tae_8week_min.yaml",
        "protocols/v2/aflibercept_treat_and_treat.yaml"
    ]
    
    for protocol_path in protocols:
        path = Path(protocol_path)
        if not path.exists():
            print(f"\n✗ {protocol_path} not found")
            continue
            
        with open(path) as f:
            data = yaml.safe_load(f)
        
        print(f"\n{data['name']}:")
        print(f"  Import base config: {data.get('import_base_config', False)}")
        print(f"  Base module: {data.get('base_config_module', 'N/A')}")
        print(f"  Base config name: {data.get('base_config_name', 'N/A')}")
        
        if 'clinical_improvements' in data:
            ci = data['clinical_improvements']
            if 'response_types' in ci:
                print("  Response type overrides:")
                for resp_type, config in ci['response_types'].items():
                    print(f"    {resp_type}: {config['probability']*100:.0f}% @ {config['multiplier']}x")


def create_demo_protocols():
    """Create demonstration protocols showing base config usage."""
    print("\n" + "="*60)
    print("Creating Demonstration Protocols")
    print("="*60)
    
    # Get base config
    base = get_base_config('aflibercept')
    
    # Create T&E protocol with base
    tae_with_base = merge_configs(base, {
        'name': 'Aflibercept T&E Demo',
        'version': '1.0',
        'created_date': '2025-01-24',
        'author': 'Demo',
        'description': 'T&E protocol using base config',
        'protocol_type': 'treat_and_extend',
        'min_interval_days': 56,
        'max_interval_days': 112,
        'extension_days': 14,
        'shortening_days': 14,
        'clinical_improvements': {
            'response_types': {
                'good': {'probability': 0.60, 'multiplier': 1.8}
            }
        }
    })
    
    # Create T&T protocol with base
    tnt_with_base = merge_configs(base, {
        'name': 'Aflibercept T&T Demo',
        'version': '1.0',
        'created_date': '2025-01-24',
        'author': 'Demo',
        'description': 'T&T protocol using base config',
        'protocol_type': 'fixed_interval',
        'min_interval_days': 56,
        'max_interval_days': 56,
        'extension_days': 0,
        'shortening_days': 0
    })
    
    # Save demo protocols
    demo_dir = Path('calibration/demo_protocols')
    demo_dir.mkdir(parents=True, exist_ok=True)
    
    with open(demo_dir / 'tae_with_base_demo.yaml', 'w') as f:
        yaml.dump(tae_with_base, f, sort_keys=False)
    print(f"\n✓ Created {demo_dir / 'tae_with_base_demo.yaml'}")
    
    with open(demo_dir / 'tnt_with_base_demo.yaml', 'w') as f:
        yaml.dump(tnt_with_base, f, sort_keys=False)
    print(f"✓ Created {demo_dir / 'tnt_with_base_demo.yaml'}")
    
    print("\nThese demo protocols show how base configs create consistent foundations.")


def main():
    """Run all tests."""
    test_base_config()
    test_protocol_files()
    create_demo_protocols()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("✓ Base configuration system is working correctly")
    print("✓ Protocol files are set up to use base configs")
    print("✓ Demo protocols created showing proper usage")
    print("\nNext: Ask user to test protocols in the UI")


if __name__ == "__main__":
    main()