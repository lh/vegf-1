"""Pattern analysis functions for treatment data."""

import pandas as pd
import time
import streamlit as st


# Color scheme for treatment-based states
TREATMENT_STATE_COLORS = {
    # Treatment intensity states (based on intervals alone)
    "Initial Treatment": "#e6f2ff",
    "Intensive (Monthly)": "#4a90e2",
    "Regular (6-8 weeks)": "#7fba00", 
    "Extended (12+ weeks)": "#5c8a00",
    "Maximum Extension (16 weeks)": "#2d5016",
    
    # Gap-based states (inferred from treatment patterns)
    "Treatment Gap (3-6 months)": "#ffd700",
    "Extended Gap (6-12 months)": "#ff9500",
    "Long Gap (12+ months)": "#ff6347",
    
    # Discontinuation (inferred from no further visits)
    "No Further Visits": "#999999",
    
    # Special patterns
    "Restarted After Gap": "#ff1493",
    "Irregular Pattern": "#dda0dd"
}


def extract_treatment_patterns_vectorized(results):
    """
    Extract patient transitions based ONLY on treatment patterns.
    
    This uses only information available in real-world data:
    - Visit timing
    - Treatment intervals
    - Gaps in treatment
    
    Returns: (transitions_df, visits_df_with_intervals)
    """
    DAYS_PER_MONTH = 365.25 / 12
    
    if hasattr(results, 'get_visits_df'):
        st.info("Extracting treatment patterns from visit data...")
        start_time = time.time()
        
        # Get all visits as DataFrame
        visits_df = results.get_visits_df()
        
        # Sort by patient and time
        visits_df = visits_df.sort_values(['patient_id', 'time_days'])
        
        # Add visit number for each patient
        visits_df['visit_num'] = visits_df.groupby('patient_id').cumcount()
        
        # Calculate intervals
        visits_df['prev_time_days'] = visits_df.groupby('patient_id')['time_days'].shift(1)
        visits_df['interval_days'] = visits_df['time_days'] - visits_df['prev_time_days']
        
        # Determine treatment state based on intervals alone
        visits_df['treatment_state'] = determine_treatment_state_vectorized(visits_df)
        
        # Create previous state column
        visits_df['prev_treatment_state'] = visits_df.groupby('patient_id')['treatment_state'].shift(1)
        
        # First visit handling
        first_visits = visits_df['visit_num'] == 0
        visits_df.loc[first_visits, 'prev_treatment_state'] = 'Pre-Treatment'
        visits_df.loc[first_visits, 'prev_time_days'] = 0
        
        # Filter to only state changes
        state_changes = visits_df[visits_df['treatment_state'] != visits_df['prev_treatment_state']].copy()
        
        # Create transitions DataFrame
        transitions_df = pd.DataFrame({
            'patient_id': state_changes['patient_id'],
            'from_state': state_changes['prev_treatment_state'],
            'to_state': state_changes['treatment_state'],
            'from_time_days': state_changes['prev_time_days'],
            'to_time_days': state_changes['time_days'],
            'from_time': state_changes['prev_time_days'] / DAYS_PER_MONTH,
            'to_time': state_changes['time_days'] / DAYS_PER_MONTH,
            'duration_days': state_changes['time_days'] - state_changes['prev_time_days'],
            'duration': (state_changes['time_days'] - state_changes['prev_time_days']) / DAYS_PER_MONTH,
            'interval_days': state_changes['interval_days']
        })
        
        # Add final state transitions
        last_visits = visits_df.groupby('patient_id').last().reset_index()
        
        # Determine if patients have stopped treatment (no further visits)
        # In real data, we'd define this as no visit for > 6 months from simulation end
        sim_end_days = visits_df['time_days'].max()
        last_visits['time_since_last'] = sim_end_days - last_visits['time_days']
        
        # Create final transitions for patients who appear to have stopped
        stopped_mask = last_visits['time_since_last'] > 180  # 6+ months
        stopped_patients = last_visits[stopped_mask]
        
        if len(stopped_patients) > 0:
            final_transitions = pd.DataFrame({
                'patient_id': stopped_patients['patient_id'],
                'from_state': stopped_patients['treatment_state'],
                'to_state': 'No Further Visits',
                'from_time_days': stopped_patients['time_days'],
                'to_time_days': stopped_patients['time_days'],
                'from_time': stopped_patients['time_days'] / DAYS_PER_MONTH,
                'to_time': stopped_patients['time_days'] / DAYS_PER_MONTH,
                'duration_days': 0,
                'duration': 0,
                'interval_days': 0
            })
            
            transitions_df = pd.concat([transitions_df, final_transitions], ignore_index=True)
        
        elapsed = time.time() - start_time
        st.success(f"Extracted {len(transitions_df)} treatment pattern transitions in {elapsed:.1f} seconds")
        
        return transitions_df, visits_df
    else:
        st.error("This visualization requires visit data")
        return pd.DataFrame(), pd.DataFrame()


def determine_treatment_state_vectorized(visits_df):
    """
    Determine treatment state based ONLY on visit intervals.
    
    This mirrors what we can infer from real-world treatment data.
    """
    states = pd.Series('Initial Treatment', index=visits_df.index)
    
    # For visits after the first one, categorize by interval
    has_interval = visits_df['interval_days'].notna()
    
    # Intensive treatment (monthly - up to 5 weeks)
    intensive_mask = has_interval & (visits_df['interval_days'] <= 35)
    states[intensive_mask] = 'Intensive (Monthly)'
    
    # Regular treatment (6-8 weeks)
    regular_mask = has_interval & (visits_df['interval_days'] > 35) & (visits_df['interval_days'] <= 63)
    states[regular_mask] = 'Regular (6-8 weeks)'
    
    # Extended treatment (12-15 weeks)
    extended_mask = has_interval & (visits_df['interval_days'] > 63) & (visits_df['interval_days'] < 112)
    states[extended_mask] = 'Extended (12+ weeks)'
    
    # Maximum extension (16 weeks)
    max_mask = has_interval & (visits_df['interval_days'] >= 112) & (visits_df['interval_days'] <= 119)
    states[max_mask] = 'Maximum Extension (16 weeks)'
    
    # Treatment gaps
    gap_3_6_mask = has_interval & (visits_df['interval_days'] > 119) & (visits_df['interval_days'] <= 180)
    states[gap_3_6_mask] = 'Treatment Gap (3-6 months)'
    
    gap_6_12_mask = has_interval & (visits_df['interval_days'] > 180) & (visits_df['interval_days'] <= 365)
    states[gap_6_12_mask] = 'Extended Gap (6-12 months)'
    
    gap_12plus_mask = has_interval & (visits_df['interval_days'] > 365)
    states[gap_12plus_mask] = 'Long Gap (12+ months)'
    
    # Mark visits after long gaps as restarted - FULLY VECTORIZED
    # Identify visits that follow a long gap
    visits_df['had_long_gap'] = visits_df['interval_days'] > 180
    
    # Within each patient, mark visits that come after a long gap
    # Use shift to look at previous visit's gap status
    # Create a boolean column explicitly to avoid downcasting warnings
    visits_df['after_gap'] = visits_df.groupby('patient_id')['had_long_gap'].shift(1)
    visits_df['after_gap'] = visits_df['after_gap'].fillna(False)
    visits_df['after_gap'] = visits_df['after_gap'].astype('bool')
    
    # Create restart groups - increment when we see a new gap
    visits_df['gap_group'] = visits_df.groupby('patient_id')['had_long_gap'].cumsum()
    
    # Count visits within each gap group for each patient
    visits_df['visits_in_gap_group'] = visits_df.groupby(['patient_id', 'gap_group']).cumcount()
    
    # Mark as restarted if:
    # 1. We're after a gap (gap_group > 0)
    # 2. We're in the first 3 visits of the new group (visits_in_gap_group < 3) 
    # 3. The interval is reasonable (not another gap)
    restart_mask = (
        (visits_df['gap_group'] > 0) & 
        (visits_df['visits_in_gap_group'] < 3) & 
        (visits_df['interval_days'] <= 63) &
        has_interval
    )
    
    states[restart_mask] = 'Restarted After Gap'
    
    return states