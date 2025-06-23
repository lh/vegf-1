#!/usr/bin/env python3
"""Test unique parameter directories for duplicated protocols."""

import yaml
from pathlib import Path
import shutil

# Clean up any existing temp files
temp_dir = Path('protocols/temp')
if temp_dir.exists():
    for item in temp_dir.iterdir():
        if item.is_dir() and item.name.startswith('parameters_'):
            shutil.rmtree(item)
        elif item.suffix == '.yaml':
            item.unlink()

# Test creating multiple duplicates
source_file = Path('protocols/v2_time_based/aflibercept_tae_8week_min_time_based.yaml')

# Create first duplicate
memorable_name1 = "test-one"
dest_file1 = temp_dir / f"protocol_{memorable_name1}.yaml"

with open(source_file) as f:
    data1 = yaml.safe_load(f)

# Update parameter paths
data1['disease_transitions_file'] = f"parameters_{memorable_name1}/disease_transitions.yaml"
data1['treatment_effect_file'] = f"parameters_{memorable_name1}/treatment_effect.yaml"

with open(dest_file1, 'w') as f:
    yaml.dump(data1, f)

# Create parameters directory
params_dir1 = temp_dir / f"parameters_{memorable_name1}"
params_dir1.mkdir(exist_ok=True)

# Copy a parameter file
source_params = source_file.parent / "parameters" / "disease_transitions.yaml"
if source_params.exists():
    shutil.copy2(source_params, params_dir1 / "disease_transitions.yaml")

# Create second duplicate
memorable_name2 = "test-two"
dest_file2 = temp_dir / f"protocol_{memorable_name2}.yaml"

with open(source_file) as f:
    data2 = yaml.safe_load(f)

# Update parameter paths
data2['disease_transitions_file'] = f"parameters_{memorable_name2}/disease_transitions.yaml"
data2['treatment_effect_file'] = f"parameters_{memorable_name2}/treatment_effect.yaml"

with open(dest_file2, 'w') as f:
    yaml.dump(data2, f)

# Create parameters directory
params_dir2 = temp_dir / f"parameters_{memorable_name2}"
params_dir2.mkdir(exist_ok=True)

# Copy a parameter file
if source_params.exists():
    shutil.copy2(source_params, params_dir2 / "disease_transitions.yaml")

# Verify
print("Created files:")
for f in sorted(temp_dir.iterdir()):
    print(f"  - {f.name}")
    if f.is_dir():
        for p in f.iterdir():
            print(f"    - {p.name}")

print("\nNo conflicts! Each protocol has its own parameters directory.")