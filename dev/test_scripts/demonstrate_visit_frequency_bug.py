"""
Demonstrate the visit frequency bug in current ABS implementation.

This shows that patients with more frequent visits have higher
disease progression rates, which is biologically incorrect.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from simulation_v2.engines.abs_engine import ABSEngine
from simulation_v2.core.disease_model import DiseaseModel, DiseaseState
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.protocols.protocol_spec import ProtocolSpecification


def create_fixed_interval_protocol(interval_days, name):
    """Create a protocol with fixed visit intervals."""
    return {
        'name': name,
        'version': '1.0',
        'author': 'Test Script',
        'description': f'Fixed {interval_days}-day interval protocol for testing',
        'created_date': '2025-01-01',
        'protocol_type': 'treat_and_extend',
        'min_interval_days': interval_days,
        'max_interval_days': interval_days,
        'extension_days': 0,  # No extension for fixed intervals
        'shortening_days': 0,  # No shortening for fixed intervals
        'disease_transitions': {
            'NAIVE': {'NAIVE': 0.0, 'STABLE': 0.3, 'ACTIVE': 0.6, 'HIGHLY_ACTIVE': 0.1},
            'STABLE': {'NAIVE': 0.0, 'STABLE': 0.7, 'ACTIVE': 0.3, 'HIGHLY_ACTIVE': 0.0},
            'ACTIVE': {'NAIVE': 0.0, 'STABLE': 0.1, 'ACTIVE': 0.7, 'HIGHLY_ACTIVE': 0.2},
            'HIGHLY_ACTIVE': {'NAIVE': 0.0, 'STABLE': 0.0, 'ACTIVE': 0.1, 'HIGHLY_ACTIVE': 0.9}
        },
        'baseline_vision': {'mean': 70, 'std': 10, 'min': 20, 'max': 90},
        'vision_change_model': {
            'naive_treated': {'mean': 0.0, 'std': 1.0},
            'naive_untreated': {'mean': -1.0, 'std': 1.0},
            'stable_treated': {'mean': 1.0, 'std': 1.0},
            'stable_untreated': {'mean': -0.5, 'std': 1.0},
            'active_treated': {'mean': -1.0, 'std': 2.0},
            'active_untreated': {'mean': -3.0, 'std': 2.0},
            'highly_active_treated': {'mean': -2.0, 'std': 2.0},
            'highly_active_untreated': {'mean': -5.0, 'std': 3.0}
        },
        'treatment_effect_on_transitions': {
            'STABLE': {'multipliers': {'STABLE': 1.1, 'ACTIVE': 0.9}},
            'ACTIVE': {'multipliers': {'STABLE': 2.0, 'ACTIVE': 0.8, 'HIGHLY_ACTIVE': 0.5}},
            'HIGHLY_ACTIVE': {'multipliers': {'STABLE': 2.0, 'ACTIVE': 1.5, 'HIGHLY_ACTIVE': 0.75}}
        },
        'discontinuation_rules': {
            'poor_vision_threshold': 0,  # Disable poor vision discontinuation
            'poor_vision_probability': 0.0,
            'high_injection_count': 1000,  # Very high threshold
            'high_injection_probability': 0.0,
            'long_treatment_months': 1000,  # Very long
            'long_treatment_probability': 0.0
        },
        'source_file': f'/tmp/test_protocol_{interval_days}.yaml',
        'load_timestamp': '2025-01-01T00:00:00',
        'checksum': 'test_checksum'
    }


def run_comparison():
    """Run comparison of different visit frequencies."""
    print("=== Visit Frequency Bug Demonstration ===\n")
    
    # Test different visit intervals
    intervals = [
        (28, "4 weeks"),
        (42, "6 weeks"),
        (56, "8 weeks"),
        (84, "12 weeks"),
        (112, "16 weeks")
    ]
    
    n_patients = 500
    duration_years = 3
    seed = 42
    
    results_by_interval = {}
    
    for interval_days, interval_name in intervals:
        print(f"Running simulation with {interval_name} intervals...")
        
        # Create protocol
        spec_dict = create_fixed_interval_protocol(interval_days, f"protocol_{interval_days}d")
        # Extract baseline vision fields
        baseline = spec_dict.pop('baseline_vision')
        spec_dict['baseline_vision_mean'] = baseline['mean']
        spec_dict['baseline_vision_std'] = baseline['std']
        spec_dict['baseline_vision_min'] = baseline['min']
        spec_dict['baseline_vision_max'] = baseline['max']
        spec = ProtocolSpecification(**spec_dict)
        
        # Create engine
        disease_model = DiseaseModel(
            spec.disease_transitions,
            spec.treatment_effect_on_transitions,
            seed=seed
        )
        protocol = StandardProtocol(
            min_interval_days=spec.min_interval_days,
            max_interval_days=spec.max_interval_days,
            extension_days=spec.extension_days,
            shortening_days=spec.shortening_days
        )
        engine = ABSEngine(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=n_patients,
            seed=seed
        )
        
        # Run simulation
        results = engine.run(duration_years=duration_years)
        
        # Analyze results
        state_counts = {state: 0 for state in DiseaseState}
        total_transitions = 0
        total_visits = 0
        
        for patient in results.patient_histories.values():
            state_counts[patient.current_state] += 1
            
            # Count transitions
            visits = patient.visit_history
            total_visits += len(visits)
            
            for i in range(1, len(visits)):
                if visits[i]['disease_state'] != visits[i-1]['disease_state']:
                    total_transitions += 1
        
        # Calculate rates
        highly_active_rate = state_counts[DiseaseState.HIGHLY_ACTIVE] / n_patients
        avg_visits_per_patient = total_visits / n_patients
        transitions_per_patient = total_transitions / n_patients
        
        results_by_interval[interval_days] = {
            'name': interval_name,
            'highly_active_rate': highly_active_rate,
            'avg_visits': avg_visits_per_patient,
            'transitions_per_patient': transitions_per_patient,
            'state_counts': state_counts
        }
    
    # Display results
    print("\n=== RESULTS ===\n")
    print(f"{'Interval':<12} {'Visits/Patient':<15} {'Transitions/Pt':<15} {'% Highly Active':<15}")
    print("-" * 60)
    
    for interval_days, data in sorted(results_by_interval.items()):
        print(f"{data['name']:<12} {data['avg_visits']:<15.1f} "
              f"{data['transitions_per_patient']:<15.2f} "
              f"{data['highly_active_rate']*100:<15.1f}%")
    
    # Calculate correlation
    print("\n=== ANALYSIS ===\n")
    
    # Compare shortest vs longest interval
    short = results_by_interval[28]
    long = results_by_interval[112]
    
    ratio = short['highly_active_rate'] / long['highly_active_rate']
    
    print(f"Patients with 4-week visits: {short['highly_active_rate']*100:.1f}% highly active")
    print(f"Patients with 16-week visits: {long['highly_active_rate']*100:.1f}% highly active")
    print(f"Ratio: {ratio:.2f}x MORE progression with frequent visits!")
    print(f"\nThis is the OPPOSITE of what we'd expect clinically.")
    print(f"(Frequent visits usually indicate worse disease, not cause it!)")
    
    # Show state distribution
    print("\n=== Final State Distribution ===\n")
    print(f"{'Interval':<12} {'Naive':<10} {'Stable':<10} {'Active':<10} {'Highly Active':<15}")
    print("-" * 60)
    
    for interval_days, data in sorted(results_by_interval.items()):
        counts = data['state_counts']
        print(f"{data['name']:<12} "
              f"{counts[DiseaseState.NAIVE]:<10} "
              f"{counts[DiseaseState.STABLE]:<10} "
              f"{counts[DiseaseState.ACTIVE]:<10} "
              f"{counts[DiseaseState.HIGHLY_ACTIVE]:<15}")


if __name__ == "__main__":
    run_comparison()