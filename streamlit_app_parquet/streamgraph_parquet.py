"""
Patient state tracking streamgraph for Parquet-based data.
Tracks patient states based on visits DataFrame.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict
from datetime import datetime


# Define patient states with colors
PATIENT_STATES = {
    'active': '#2E7D32',                          # Forest Green - Active treatment
    'discontinued_stable_max_interval': '#8BC34A', # Light Green - Good outcome
    'discontinued_random_administrative': '#FF9800', # Orange - Administrative
    'discontinued_course_complete_but_not_renewed': '#4CAF50', # Green - Course complete
    'discontinued_premature': '#F44336',          # Red - Poor outcome
    'discontinued_poor_outcome': '#B71C1C',       # Dark Red - Poor outcome
    'retreatment': '#9C27B0',                     # Purple - Retreatment
    'lost_to_followup': '#757575',                # Grey - Lost
    'other': '#BDBDBD'                            # Light Grey - Other/Unknown
}


def create_streamgraph_from_parquet(results: Dict) -> plt.Figure:
    """
    Create streamgraph visualization from Parquet-based simulation results.
    
    Args:
        results: Dictionary containing:
            - visits_df: DataFrame with visit data
            - simulation_parameters: Dict with simulation metadata
        
    Returns:
        Matplotlib figure
    """
    # Extract DataFrames
    visits_df = results.get("visits_df")
    if visits_df is None or len(visits_df) == 0:
        raise ValueError("No visits data in results")
    
    # Get simulation parameters
    sim_params = results.get("simulation_parameters", {})
    duration_years = sim_params.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    
    # Convert date to time if needed
    if 'time' not in visits_df.columns and 'date' in visits_df.columns:
        visits_df = visits_df.copy()
        visits_df['date'] = pd.to_datetime(visits_df['date'])
        min_date = visits_df['date'].min()
        visits_df['time'] = (visits_df['date'] - min_date).dt.days / 30.44  # Average days per month
    
    # Round time to months
    visits_df['time_month'] = visits_df['time'].round().astype(int)
    
    # Determine patient state at each time point
    # We'll track the latest state for each patient at each month
    state_data = []
    
    # Group by patient to process their history
    for patient_id, patient_visits in visits_df.groupby('patient_id'):
        patient_visits = patient_visits.sort_values('time')
        
        # Track patient state over time
        current_state = 'active'
        has_been_discontinued = False
        is_in_retreatment = False
        
        # Create state entries for each month
        for month in range(duration_months + 1):
            # Find visits up to this month
            visits_to_date = patient_visits[patient_visits['time_month'] <= month]
            
            if len(visits_to_date) == 0:
                # No visits yet - patient not started
                continue
            
            # Check latest visit status
            latest_visit = visits_to_date.iloc[-1]
            
            # Determine state based on visit data
            if latest_visit.get('is_retreatment_visit', False):
                current_state = 'retreatment'
                is_in_retreatment = True
            elif latest_visit.get('is_discontinuation', False) or latest_visit.get('is_discontinuation_visit', False):
                disc_type = latest_visit.get('discontinuation_type', 'other')
                if disc_type == 'stable_max_interval':
                    current_state = 'discontinued_stable_max_interval'
                elif disc_type == 'random_administrative':
                    current_state = 'discontinued_random_administrative'
                elif disc_type == 'course_complete_but_not_renewed':
                    current_state = 'discontinued_course_complete_but_not_renewed'
                elif disc_type == 'premature':
                    current_state = 'discontinued_premature'
                elif disc_type == 'poor_outcome':
                    current_state = 'discontinued_poor_outcome'
                else:
                    current_state = 'other'
                has_been_discontinued = True
            elif has_been_discontinued and not is_in_retreatment:
                # Patient was discontinued but not marked for retreatment
                # Keep their discontinued state
                pass
            else:
                # Patient is active
                current_state = 'active'
            
            state_data.append({
                'patient_id': patient_id,
                'time_month': month,
                'state': current_state
            })
    
    # Convert to DataFrame
    state_df = pd.DataFrame(state_data)
    
    # Aggregate counts by month and state
    monthly_counts = state_df.groupby(['time_month', 'state']).size().reset_index(name='count')
    
    # Pivot for stacking
    pivot_data = monthly_counts.pivot(
        index='time_month',
        columns='state',
        values='count'
    ).fillna(0)
    
    # Ensure all states are present
    for state in PATIENT_STATES.keys():
        if state not in pivot_data.columns:
            pivot_data[state] = 0
    
    # Order states for consistent stacking
    state_order = [
        'active',
        'retreatment',
        'discontinued_stable_max_interval',
        'discontinued_course_complete_but_not_renewed',
        'discontinued_random_administrative',
        'discontinued_premature',
        'discontinued_poor_outcome',
        'lost_to_followup',
        'other'
    ]
    
    # Filter to existing columns
    state_order = [s for s in state_order if s in pivot_data.columns]
    pivot_data = pivot_data[state_order]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Create the streamgraph
    ax.stackplot(
        pivot_data.index,
        *[pivot_data[state].values for state in state_order],
        labels=state_order,
        colors=[PATIENT_STATES.get(state, '#BDBDBD') for state in state_order],
        alpha=0.85
    )
    
    # Styling
    ax.set_xlabel('Time (months)', fontsize=12)
    ax.set_ylabel('Number of Patients', fontsize=12)
    ax.set_title('Patient States Over Time', fontsize=14, fontweight='bold')
    
    # Set x-axis limits
    ax.set_xlim(0, duration_months)
    
    # Set x-axis ticks at yearly intervals
    year_ticks = list(range(0, duration_months + 1, 12))
    ax.set_xticks(year_ticks)
    ax.set_xticklabels([f'{y//12}' for y in year_ticks])
    ax.set_xlabel('Time (years)', fontsize=12)
    
    # Add grid
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Legend
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), 
             frameon=True, fancybox=True, shadow=True)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    return fig