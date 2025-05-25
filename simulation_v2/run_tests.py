#!/usr/bin/env python3
"""
Simple test runner to demonstrate TDD approach.

Run from the CC directory:
    python simulation_v2/run_tests.py
"""

import sys
import os

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can run a simple test
from simulation_v2.core.disease_model import DiseaseState, DiseaseModel

print("Testing Disease Model Implementation")
print("=" * 40)

# Test 1: Disease states exist
print("\n1. Testing disease states exist...")
try:
    assert DiseaseState.NAIVE.value == 0
    assert DiseaseState.STABLE.value == 1
    assert DiseaseState.ACTIVE.value == 2
    assert DiseaseState.HIGHLY_ACTIVE.value == 3
    print("   ✓ All disease states defined correctly")
except AssertionError:
    print("   ✗ Disease states not defined correctly")

# Test 2: Model creation
print("\n2. Testing model creation...")
try:
    model = DiseaseModel()
    assert model is not None
    assert hasattr(model, 'transition_probabilities')
    print("   ✓ Model created successfully")
except Exception as e:
    print(f"   ✗ Model creation failed: {e}")

# Test 3: NAIVE transitions
print("\n3. Testing NAIVE transitions (should never stay NAIVE)...")
try:
    outcomes = []
    for i in range(20):
        model = DiseaseModel(seed=i)
        new_state = model.transition(DiseaseState.NAIVE)
        outcomes.append(new_state)
    
    assert DiseaseState.NAIVE not in outcomes
    print(f"   ✓ NAIVE always transitions to other states")
    print(f"   - STABLE: {outcomes.count(DiseaseState.STABLE)}/20")
    print(f"   - ACTIVE: {outcomes.count(DiseaseState.ACTIVE)}/20")
    print(f"   - HIGHLY_ACTIVE: {outcomes.count(DiseaseState.HIGHLY_ACTIVE)}/20")
except AssertionError:
    print("   ✗ NAIVE incorrectly stayed NAIVE")

# Test 4: Treatment effect
print("\n4. Testing treatment effect on ACTIVE state...")
try:
    no_treatment_stable = 0
    with_treatment_stable = 0
    
    for i in range(50):
        model = DiseaseModel(seed=i)
        
        # Without treatment
        no_treat_result = model.transition(DiseaseState.ACTIVE, treated=False)
        if no_treat_result == DiseaseState.STABLE:
            no_treatment_stable += 1
            
        # With treatment (same seed)
        model = DiseaseModel(seed=i)
        treat_result = model.transition(DiseaseState.ACTIVE, treated=True)
        if treat_result == DiseaseState.STABLE:
            with_treatment_stable += 1
    
    print(f"   - Without treatment: {no_treatment_stable}/50 became STABLE")
    print(f"   - With treatment: {with_treatment_stable}/50 became STABLE")
    
    assert with_treatment_stable > no_treatment_stable
    print("   ✓ Treatment improves outcomes")
except AssertionError:
    print("   ✗ Treatment did not improve outcomes")

print("\n" + "=" * 40)
print("Basic tests complete!")
print("\nNext steps:")
print("1. Implement Patient class to pass patient tests")
print("2. Implement serialization to pass FOV→TOM tests")
print("3. Implement engines to pass comparison tests")