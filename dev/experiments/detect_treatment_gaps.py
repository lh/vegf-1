#!/usr/bin/env python3
"""
Detect de facto treatment discontinuation and retreatment based on visit gaps.

This approach infers discontinuation when the gap between visits exceeds the 
maximum protocol interval, making it applicable to both simulated and real-world data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import json


# Protocol maximum intervals (in days)
PROTOCOL_MAX_INTERVALS = {
    'eylea_treat_and_extend': 112,  # 16 weeks
    'default': 112  # Use Eylea as default
}

# Additional buffer to account for scheduling flexibility
SCHEDULING_BUFFER_DAYS = 14  # 2 weeks

# Minimum gap to consider as de facto discontinuation
MIN_DISCONTINUATION_GAP_DAYS = 180  # 6 months (conservative)


def detect_treatment_gaps(patient_visits, protocol='eylea_treat_and_extend'):
    """
    Detect de facto discontinuation and retreatment based on visit gaps.
    
    Args:
        patient_visits: List of visit records with 'date' or 'visit_day' field
        protocol: Protocol name to determine max interval
        
    Returns:
        Enhanced visit list with gap-based discontinuation/retreatment flags
    """
    if len(patient_visits) < 2:
        return patient_visits
    
    # Get protocol max interval
    max_interval = PROTOCOL_MAX_INTERVALS.get(protocol, PROTOCOL_MAX_INTERVALS['default'])
    discontinuation_threshold = max_interval + SCHEDULING_BUFFER_DAYS
    
    enhanced_visits = []
    treatment_periods = []
    current_period = {'start': 0, 'end': None, 'visits': []}
    in_treatment_gap = False
    gap_start_idx = None
    
    for i, visit in enumerate(patient_visits):
        visit_copy = visit.copy()
        
        if i == 0:
            # First visit
            visit_copy['gap_days'] = 0
            visit_copy['gap_detected'] = False
            current_period['visits'].append(i)
        else:
            # Calculate gap from previous visit
            if 'date' in visit and 'date' in patient_visits[i-1]:
                gap_days = (visit['date'] - patient_visits[i-1]['date']).days
            else:
                # Use visit_day or time field
                current_day = visit.get('visit_day', visit.get('time', i * 30))
                prev_day = patient_visits[i-1].get('visit_day', 
                          patient_visits[i-1].get('time', (i-1) * 30))
                gap_days = current_day - prev_day
            
            visit_copy['gap_days'] = gap_days
            
            # Detect gaps exceeding protocol maximum
            if gap_days > discontinuation_threshold:
                visit_copy['gap_detected'] = True
                visit_copy['gap_type'] = 'exceeds_protocol_max'
                
                # Check if this is a significant gap (de facto discontinuation)
                if gap_days >= MIN_DISCONTINUATION_GAP_DAYS:
                    if not in_treatment_gap:
                        # Start of treatment gap
                        in_treatment_gap = True
                        gap_start_idx = i - 1
                        
                        # Mark previous visit as de facto discontinuation
                        enhanced_visits[-1]['de_facto_discontinuation'] = True
                        enhanced_visits[-1]['gap_until_next_visit'] = gap_days
                        
                        # End current treatment period
                        current_period['end'] = i - 1
                        treatment_periods.append(current_period)
                        
                    # This visit is a de facto retreatment
                    visit_copy['de_facto_retreatment'] = True
                    visit_copy['months_off_treatment'] = gap_days / 30.44
                    visit_copy['treatment_period'] = len(treatment_periods) + 1
                    
                    # Start new treatment period
                    current_period = {
                        'start': i, 
                        'end': None, 
                        'visits': [i],
                        'retreatment': True,
                        'gap_days': gap_days
                    }
                    in_treatment_gap = False
                else:
                    # Protocol violation but not full discontinuation
                    visit_copy['protocol_violation'] = True
                    visit_copy['violation_type'] = 'interval_exceeded'
                    current_period['visits'].append(i)
            else:
                visit_copy['gap_detected'] = False
                current_period['visits'].append(i)
                
                # Check if returning to regular intervals after violation
                if i > 1 and enhanced_visits[-1].get('protocol_violation'):
                    visit_copy['post_violation_visit'] = True
        
        enhanced_visits.append(visit_copy)
    
    # Close final treatment period
    if current_period['end'] is None:
        current_period['end'] = len(enhanced_visits) - 1
        treatment_periods.append(current_period)
    
    # Add treatment period summary
    for visit in enhanced_visits:
        visit['total_treatment_periods'] = len(treatment_periods)
    
    return enhanced_visits, treatment_periods


def analyze_gap_patterns(results, protocol='eylea_treat_and_extend'):
    """
    Analyze treatment gap patterns across all patients.
    
    Returns detailed statistics about de facto discontinuations and retreatments.
    """
    gap_analysis = {
        'total_patients': 0,
        'patients_with_gaps': 0,
        'total_gaps_detected': 0,
        'de_facto_discontinuations': 0,
        'de_facto_retreatments': 0,
        'gap_durations': [],
        'retreatment_success': [],
        'multiple_gap_patients': 0,
        'gap_reasons': defaultdict(int),
        'gaps_by_month': defaultdict(int)
    }
    
    transitions = []
    DAYS_PER_MONTH = 365.25 / 12
    
    # Handle ParquetResults format
    if hasattr(results, 'iterate_patients'):
        # Process patients in batches
        for patient_batch in results.iterate_patients(batch_size=100):
            for patient_data in patient_batch:
                patient_id = patient_data['patient_id']
                process_patient_gaps(patient_id, patient_data, gap_analysis, transitions, 
                                   protocol, DAYS_PER_MONTH)
    else:
        # Handle dict-based format
        if hasattr(results, 'raw_results'):
            patient_histories = results.raw_results.get('patient_histories', {})
        else:
            patient_histories = results.get('patient_histories', {})
            
        for patient_id, patient_data in patient_histories.items():
            process_patient_gaps(patient_id, patient_data, gap_analysis, transitions, 
                               protocol, DAYS_PER_MONTH)
    
    # Calculate summary statistics
    if gap_analysis['gap_durations']:
        gap_analysis['avg_gap_duration_days'] = np.mean(gap_analysis['gap_durations'])
        gap_analysis['median_gap_duration_days'] = np.median(gap_analysis['gap_durations'])
        gap_analysis['max_gap_duration_days'] = np.max(gap_analysis['gap_durations'])
    
    if gap_analysis['retreatment_success']:
        gap_analysis['retreatment_success_rate'] = np.mean(gap_analysis['retreatment_success'])
    
    return pd.DataFrame(transitions), gap_analysis


def process_patient_gaps(patient_id, patient_data, gap_analysis, transitions, protocol, DAYS_PER_MONTH):
    """Process gap analysis for a single patient."""
    visits = patient_data['visits']
    enhanced_visits, treatment_periods = detect_treatment_gaps(visits, protocol)
    
    gap_analysis['total_patients'] += 1
    patient_had_gap = False
    patient_gap_count = 0
    
    # Track state transitions including gap-based discontinuations
    prev_state = "Initial"
    prev_time_days = 0
    
    for i, visit in enumerate(enhanced_visits):
        # Determine current state
        if visit.get('de_facto_discontinuation'):
            current_state = "Off Treatment (Gap)"
        elif visit.get('de_facto_retreatment'):
            current_state = f"Retreatment (Period {visit.get('treatment_period', 1)})"
        elif visit.get('is_discontinuation_visit'):
            # Formal discontinuation
            disc_type = visit.get('discontinuation_type', 'unknown')
            current_state = f"Discontinued ({disc_type})"
        elif visit.get('gap_detected') and visit.get('gap_days', 0) >= MIN_DISCONTINUATION_GAP_DAYS:
            current_state = "Treatment Gap"
        elif visit.get('protocol_violation'):
            current_state = "Extended Interval"
        else:
            # Regular treatment states
            interval = visit.get('current_interval_days', 28)
            if interval >= 112:
                current_state = "Stable (Max Interval)"
            elif interval >= 84:
                current_state = "Stable"
            else:
                current_state = "Active"
        
        # Calculate time
        if 'date' in visit and isinstance(visit['date'], datetime):
            if i == 0:
                time_days = 0
            else:
                time_days = (visit['date'] - enhanced_visits[0]['date']).days
        else:
            time_days = visit.get('visit_day', visit.get('time', i * 30))
        
        # Record transition
        if current_state != prev_state:
            transitions.append({
                'patient_id': patient_id,
                'from_state': prev_state,
                'to_state': current_state,
                'from_time_days': prev_time_days,
                'to_time_days': time_days,
                'from_time': prev_time_days / DAYS_PER_MONTH,
                'to_time': time_days / DAYS_PER_MONTH,
                'is_gap_transition': 'Gap' in current_state or 'Gap' in prev_state,
                'gap_days': visit.get('gap_days', 0)
            })
            prev_state = current_state
            prev_time_days = time_days
        
        # Collect gap statistics
        if visit.get('de_facto_discontinuation'):
            gap_analysis['de_facto_discontinuations'] += 1
            patient_had_gap = True
            patient_gap_count += 1
            gap_duration = visit.get('gap_until_next_visit', 0)
            gap_analysis['gap_durations'].append(gap_duration)
            
            # Categorize gap timing
            gap_month = int(time_days / DAYS_PER_MONTH)
            gap_analysis['gaps_by_month'][gap_month] += 1
            
        if visit.get('de_facto_retreatment'):
            gap_analysis['de_facto_retreatments'] += 1
            
            # Check if retreatment was successful (patient reached stable state again)
            success = False
            for j in range(i+1, len(enhanced_visits)):
                if enhanced_visits[j].get('current_interval_days', 0) >= 84:
                    success = True
                    break
                elif enhanced_visits[j].get('de_facto_discontinuation'):
                    break
            
            gap_analysis['retreatment_success'].append(success)
    
    if patient_had_gap:
        gap_analysis['patients_with_gaps'] += 1
        
    if patient_gap_count > 1:
        gap_analysis['multiple_gap_patients'] += 1
    
    gap_analysis['total_gaps_detected'] += patient_gap_count


def create_gap_based_transitions(data_file, protocol='eylea_treat_and_extend'):
    """
    Process existing simulation data to detect gap-based transitions.
    """
    # Load existing data
    if data_file.endswith('.parquet'):
        # Load from streamlit results
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from core.results.factory import ResultsFactory
        
        results = ResultsFactory.load_results(data_file)
    else:
        # Load from JSON
        with open(data_file, 'r') as f:
            results = json.load(f)
    
    # Analyze gaps
    transitions_df, gap_analysis = analyze_gap_patterns(results, protocol)
    
    return transitions_df, gap_analysis, results


def main():
    """Analyze simulation data for treatment gaps."""
    import argparse
    sys.path.append(str(Path(__file__).parent.parent))
    sys.path.append(str(Path(__file__).parent.parent.parent))
    
    from core.results.factory import ResultsManagerFactory
    
    parser = argparse.ArgumentParser(description='Detect treatment gaps in simulation data')
    parser.add_argument('--simulation', type=str, help='Simulation ID (e.g., sim_20250126_123456_abc123)')
    parser.add_argument('--protocol', type=str, default='eylea_treat_and_extend',
                       help='Protocol name for max interval')
    
    args = parser.parse_args()
    
    # Find simulation results
    results_dir = Path(__file__).parent.parent / "simulation_results"
    
    if args.simulation:
        sim_path = results_dir / args.simulation
        if not sim_path.exists():
            print(f"Simulation {args.simulation} not found")
            return
        sim_dirs = [sim_path]
    else:
        # Process all available simulations
        sim_dirs = [d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith("sim_")]
        if not sim_dirs:
            print("No simulation results found!")
            print("Run a simulation first using the main Streamlit app")
            return
    
    for sim_dir in sim_dirs:
        print(f"\nProcessing simulation: {sim_dir.name}")
        
        try:
            # Load simulation results
            results = ResultsFactory.load_results(sim_dir)
            
            # Analyze gaps
            transitions_df, gap_analysis = analyze_gap_patterns(results, args.protocol)
            
            if len(transitions_df) == 0:
                print(f"  No transitions found in {sim_dir.name}")
                continue
            
            # Save gap analysis alongside simulation results
            gap_analysis_file = sim_dir / "gap_analysis.json"
            with open(gap_analysis_file, 'w') as f:
                json.dump(gap_analysis, f, indent=2, default=str)
            
            # Save gap-based transitions
            gap_transitions_file = sim_dir / "gap_transitions.parquet"
            transitions_df.to_parquet(gap_transitions_file)
            
            # Print summary
            print(f"\nGap Analysis Summary:")
            print(f"  Total patients: {gap_analysis['total_patients']}")
            print(f"  Patients with gaps: {gap_analysis['patients_with_gaps']}")
            print(f"  De facto discontinuations: {gap_analysis['de_facto_discontinuations']}")
            print(f"  De facto retreatments: {gap_analysis['de_facto_retreatments']}")
            if 'avg_gap_duration_days' in gap_analysis:
                print(f"  Average gap duration: {gap_analysis['avg_gap_duration_days']:.1f} days")
            if 'retreatment_success_rate' in gap_analysis:
                print(f"  Retreatment success rate: {gap_analysis['retreatment_success_rate']:.1%}")
            
            print(f"\nResults saved to {sim_dir.name}/")
            
        except Exception as e:
            print(f"  Error processing {sim_dir.name}: {str(e)}")
            continue


if __name__ == "__main__":
    main()