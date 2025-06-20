#!/usr/bin/env python3
"""
Analyze why vision changes are negative in the calibration runs.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
import pandas as pd
import numpy as np
from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.core.simulation_runner import ABSEngineWithSpecs
from simulation_v2.clinical_improvements import ClinicalImprovements


def analyze_vision_mechanics():
    """Analyze the vision change mechanics in detail."""
    print("Analyzing Vision Change Mechanics\n")
    
    # Load protocol
    protocol_path = Path("calibration/test_protocols/view_aligned.yaml")
    spec = ProtocolSpecification.from_yaml(protocol_path)
    
    # Check vision change model
    print("1. Vision Change Model from Protocol:")
    for scenario, params in spec.vision_change_model.items():
        print(f"   {scenario}: mean={params['mean']}, std={params['std']}")
    
    print("\n2. Expected Vision Changes by State:")
    print("   NAIVE → STABLE (treated): 1.0 letters/visit")
    print("   NAIVE → ACTIVE (treated): 0.0 letters/visit")
    print("   STABLE (treated): 1.0 letters/visit")
    print("   ACTIVE (treated): -1.0 letters/visit")
    print("   HIGHLY_ACTIVE (treated): -2.0 letters/visit")
    
    # Run a longer simulation to see patterns
    print("\n3. Running 1-year simulation with 100 patients:")
    
    # Create clinical improvements
    improvements_config = spec.clinical_improvements.copy()
    improvements_config.pop('enabled', None)
    
    config_data = {
        'use_loading_phase': improvements_config.get('use_loading_phase', False),
        'use_time_based_discontinuation': improvements_config.get('use_time_based_discontinuation', False),
        'use_response_based_vision': improvements_config.get('use_response_based_vision', False),
        'use_baseline_distribution': improvements_config.get('use_baseline_distribution', False),
        'use_response_heterogeneity': improvements_config.get('use_response_heterogeneity', False)
    }
    
    if 'response_types' in improvements_config:
        config_data['response_types'] = improvements_config['response_types']
    if 'discontinuation_probabilities' in improvements_config:
        config_data['discontinuation_probabilities'] = improvements_config['discontinuation_probabilities']
        
    clinical_improvements = ClinicalImprovements(**config_data)
    
    # Create engine
    disease_model = DiseaseModel(
        transition_probabilities=spec.disease_transitions,
        treatment_effect_multipliers=spec.treatment_effect_on_transitions
    )
    protocol = StandardProtocol(
        min_interval_days=spec.min_interval_days,
        max_interval_days=spec.max_interval_days,
        extension_days=spec.extension_days,
        shortening_days=spec.shortening_days
    )
    
    engine = ABSEngineWithSpecs(
        disease_model=disease_model,
        protocol=protocol,
        protocol_spec=spec,
        n_patients=100,
        seed=42,
        clinical_improvements=clinical_improvements
    )
    
    results = engine.run(duration_years=1.0)
    
    # Analyze disease states over time
    print("\n4. Disease State Distribution Over Time:")
    
    # Collect visit data
    visit_data = []
    for pid, patient in results.patient_histories.items():
        response_type = getattr(patient, 'response_type', 'unknown')
        for i, visit in enumerate(patient.visit_history):
            # Convert disease state to string
            disease_state = visit.get('disease_state', 'unknown')
            if hasattr(disease_state, 'name'):
                disease_state = disease_state.name
            
            visit_data.append({
                'patient_id': pid,
                'visit_num': i,
                'month': i * 2,  # Approximate
                'disease_state': str(disease_state),
                'vision': visit['vision'],
                'treatment_given': visit['treatment_given'],
                'response_type': response_type
            })
    
    df = pd.DataFrame(visit_data)
    
    # State distribution
    print("\n   Disease state distribution:")
    state_dist = df.groupby('disease_state').size() / len(df)
    for state, pct in state_dist.items():
        print(f"     {state}: {pct:.1%}")
    
    # Response type distribution
    print("\n   Response type distribution:")
    response_dist = df.groupby('response_type').size() / len(df)
    for resp, pct in response_dist.items():
        print(f"     {resp}: {pct:.1%}")
    
    # Average vision by state
    print("\n   Average vision by disease state:")
    vision_by_state = df.groupby('disease_state')['vision'].mean()
    for state, vision in vision_by_state.items():
        print(f"     {state}: {vision:.1f} letters")
    
    # Vision changes over time
    print("\n5. Vision Changes Over Time:")
    
    # Calculate vision changes for each patient
    vision_changes = []
    for pid, patient in results.patient_histories.items():
        if len(patient.visit_history) > 0:
            baseline = patient.baseline_vision
            for month in [3, 6, 9, 12]:
                month_visits = [v for v in patient.visit_history 
                              if (v['date'] - patient.enrollment_date).days / 30.44 <= month]
                if month_visits:
                    last_vision = month_visits[-1]['vision']
                    vision_changes.append({
                        'month': month,
                        'patient_id': pid,
                        'vision_change': last_vision - baseline,
                        'response_type': getattr(patient, 'response_type', 'unknown')
                    })
    
    vc_df = pd.DataFrame(vision_changes)
    
    # Average vision change by month
    if not vc_df.empty:
        avg_by_month = vc_df.groupby('month')['vision_change'].agg(['mean', 'std', 'count'])
        print("\n   Average vision change from baseline:")
        for month, row in avg_by_month.iterrows():
            print(f"     Month {month}: {row['mean']:.1f} ± {row['std']:.1f} letters (n={row['count']})")
    
    # Check clinical improvements effect
    print("\n6. Clinical Improvements Effect:")
    
    # Compare response types
    if not vc_df.empty and 'response_type' in vc_df.columns:
        by_response = vc_df[vc_df['month'] == 12].groupby('response_type')['vision_change'].mean()
        print("\n   Vision change at 12 months by response type:")
        for resp, change in by_response.items():
            print(f"     {resp}: {change:.1f} letters")
    
    # Check if vision response improvements are actually being applied
    print("\n7. Checking if Vision Response Improvements are Applied:")
    sample_patients = list(results.patient_histories.items())[:5]
    for pid, patient in sample_patients:
        print(f"\n   Patient {pid}:")
        print(f"     Response type: {getattr(patient, 'response_type', 'unknown')}")
        if hasattr(patient, 'vision_response'):
            print(f"     Has vision response module: Yes")
        else:
            print(f"     Has vision response module: No")
            
    print("\n8. Treatment Patterns:")
    # Count injections per patient
    injection_counts = []
    for pid, patient in results.patient_histories.items():
        injection_counts.append(patient.injection_count)
    
    print(f"   Average injections per patient: {np.mean(injection_counts):.1f}")
    print(f"   Min/Max injections: {min(injection_counts)}/{max(injection_counts)}")
    
    # Check interval patterns
    print("\n   Visit intervals:")
    intervals = []
    for pid, patient in results.patient_histories.items():
        if len(patient.visit_history) > 1:
            for i in range(1, len(patient.visit_history)):
                interval = (patient.visit_history[i]['date'] - patient.visit_history[i-1]['date']).days
                intervals.append(interval)
    
    if intervals:
        print(f"     Average interval: {np.mean(intervals):.1f} days")
        print(f"     Min/Max interval: {min(intervals)}/{max(intervals)} days")


if __name__ == "__main__":
    analyze_vision_mechanics()