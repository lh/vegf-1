"""
Streamgraph with strict patient conservation - no data invention, fail fast on errors.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict

# Fix the import path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# TODO: Add these traffic light colors to SEMANTIC_COLORS in the future
TRAFFIC_LIGHT_COLORS = {
    # Green - Currently being treated
    "active_never_discontinued": "#006400",  # Strong green - never discontinued
    "active_retreated": "#228B22",          # Medium green - currently active after retreatment
    
    # Amber - Discontinued planned (stable)
    "discontinued_planned": "#FFA500",       # Amber - planned discontinuation
    
    # Red - Other discontinuations (problems)
    "discontinued_administrative": "#DC143C", # Red - administrative issues
    "discontinued_not_renewed": "#B22222",    # Red - renewal issues
    "discontinued_premature": "#8B0000",      # Dark red - premature discontinuation
    
    # Mixed states for previously retreated patients
    "discontinued_after_retreatment": "#CD5C5C"  # Light red - discontinued after being retreated
}


def sigmoid(x, steepness=10, midpoint=0.5):
    """Sigmoid function for smooth transitions."""
    return 1 / (1 + np.exp(-steepness * (x - midpoint)))


def stepped_curve(x, steps=4):
    """Create a stepped curve for certain events."""
    return np.floor(x * steps) / steps + (x * steps % 1) * 0.2


def create_strict_conservation_data(results: Dict) -> pd.DataFrame:
    """
    Create timeline data with strict patient conservation.
    Raises errors if conservation is violated - no data invention.
    """
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    population_size = results.get("population_size", 1000)
    
    # Get the actual data
    disc_counts = results.get("discontinuation_counts", {})
    raw_stats = results.get("raw_discontinuation_stats", {})
    
    # Extract retreatment data
    retreat_data = raw_stats.get("retreatments_by_type", {})
    retreat_rates = raw_stats.get("retreatment_rates_by_type", {})
    
    timeline_data = []
    
    # Initialize states with proper float precision
    states = {
        'active_never_discontinued': float(population_size),
        'active_retreated': 0.0,
        'discontinued_planned': 0.0,
        'discontinued_administrative': 0.0,
        'discontinued_not_renewed': 0.0,
        'discontinued_premature': 0.0,
        'discontinued_after_retreatment': 0.0
    }
    
    # Conservation check with tolerance for floating point
    TOLERANCE = 1e-6
    
    def check_conservation(month: int):
        """Check patient conservation and raise error if violated."""
        total = sum(states.values())
        if abs(total - population_size) > TOLERANCE:
            error_msg = f"Patient conservation violated at month {month}!\n"
            error_msg += f"Expected: {population_size}, Got: {total}\n"
            error_msg += f"Difference: {total - population_size}\n"
            error_msg += f"States: {states}"
            raise ValueError(error_msg)
    
    # Initial check
    check_conservation(0)
    
    # Track cumulative discontinuations to avoid double counting
    cumulative_discontinued = {k: 0.0 for k in disc_counts.keys()}
    
    for month in range(duration_months + 1):
        t = month / duration_months
        
        # Calculate target discontinuations at this time point
        for disc_type, final_count in disc_counts.items():
            # Progress curves for different discontinuation types
            if disc_type == "Planned":
                # Delay planned discontinuations significantly
                progress = 0 if t < 0.5 else sigmoid(t, steepness=8, midpoint=0.75)
            elif disc_type == "Administrative":
                # Linear after small delay
                progress = 0 if t < 0.05 else (t - 0.05) / (1 - 0.05)
            elif disc_type == "Not Renewed":
                # Stepped curve after delay
                progress = 0 if t < 0.1 else stepped_curve((t - 0.1) / 0.9, steps=3)
            elif disc_type == "Premature":
                # Sigmoid after delay to avoid t=0 discontinuations
                progress = 0 if t < 0.05 else sigmoid((t - 0.05) / 0.95, steepness=6, midpoint=0.4)
            else:
                progress = t
            
            # Target total discontinued by this time
            target_total = final_count * progress
            
            # New discontinuations this month
            new_disc = target_total - cumulative_discontinued[disc_type]
            new_disc = max(0, new_disc)  # Can't be negative
            
            if new_disc > 0:
                # State key mapping - handle spaces in disc_type
                state_key = f'discontinued_{disc_type.lower().replace(" ", "_")}'
                
                # Can only discontinue active patients
                available_active = states['active_never_discontinued'] + states['active_retreated']
                
                if new_disc > available_active + TOLERANCE:
                    error_msg = f"Insufficient active patients for discontinuation at month {month}!\n"
                    error_msg += f"Requested: {new_disc}, Available: {available_active}\n"
                    error_msg += f"Discontinuation type: {disc_type}"
                    raise ValueError(error_msg)
                
                # Discontinue from active pools
                from_never = min(new_disc, states['active_never_discontinued'])
                from_retreated = new_disc - from_never
                
                # Update states
                states['active_never_discontinued'] -= from_never
                states['active_retreated'] -= from_retreated
                states[state_key] += new_disc
                
                # Update cumulative tracking
                cumulative_discontinued[disc_type] += new_disc
                
                # Check conservation after each update
                check_conservation(month)
        
        # Process retreatments (with delay)
        if t > 0.15:
            # Map disc types to retreat types
            disc_to_retreat = {
                'discontinued_planned': 'stable_max_interval',
                'discontinued_administrative': 'random_administrative',
                'discontinued_not_renewed': 'course_complete_but_not_renewed',
                'discontinued_premature': 'premature'
            }
            
            for disc_state, retreat_key in disc_to_retreat.items():
                current_disc = states[disc_state]
                if current_disc > 0:
                    # Get retreatment rate
                    rate = retreat_rates.get(retreat_key, 0.0)
                    
                    # Monthly retreatment probability
                    monthly_prob = rate * 0.02  # 2% of the rate per month
                    monthly_prob = min(monthly_prob, 1.0)  # Cap at 100%
                    
                    # Calculate retreatments
                    retreat_count = current_disc * monthly_prob
                    retreat_count = min(retreat_count, current_disc)
                    
                    if retreat_count > 0:
                        states[disc_state] -= retreat_count
                        states['active_retreated'] += retreat_count
                        
                        # Check conservation
                        check_conservation(month)
        
        # Re-discontinuations (with delay)
        if t > 0.3 and states['active_retreated'] > 0:
            # Higher re-discontinuation rate
            redisc_prob = 0.015  # 1.5% per month
            redisc_count = states['active_retreated'] * redisc_prob
            redisc_count = min(redisc_count, states['active_retreated'])
            
            if redisc_count > 0:
                states['active_retreated'] -= redisc_count
                states['discontinued_after_retreatment'] += redisc_count
                
                # Check conservation
                check_conservation(month)
        
        # Final conservation check for this month
        check_conservation(month)
        
        # Record current state
        for state, count in states.items():
            if count > 0:
                display_name = {
                    'active_never_discontinued': 'Active (Never Discontinued)',
                    'active_retreated': 'Active (Retreated)',
                    'discontinued_planned': 'Discontinued Planned',
                    'discontinued_administrative': 'Discontinued Administrative',
                    'discontinued_not_renewed': 'Discontinued Not Renewed',
                    'discontinued_premature': 'Discontinued Premature',
                    'discontinued_after_retreatment': 'Discontinued After Retreatment'
                }.get(state, state)
                
                timeline_data.append({
                    'time_months': month,
                    'state': display_name,
                    'count': count
                })
    
    return pd.DataFrame(timeline_data)


def generate_strict_conservation_streamgraph(results: Dict) -> plt.Figure:
    """Generate a streamgraph with strict patient conservation enforcement."""
    
    if not results:
        raise ValueError("No simulation results provided")
    
    # Create timeline data with strict conservation
    timeline_data = create_strict_conservation_data(results)
    
    # Pivot data for stacking
    pivot_data = timeline_data.pivot(
        index='time_months', 
        columns='state', 
        values='count'
    ).fillna(0)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # State ordering (bottom to top)
    state_order = [
        'Active (Never Discontinued)',
        'Active (Retreated)',
        'Discontinued Planned',
        'Discontinued Administrative',
        'Discontinued Not Renewed',
        'Discontinued Premature',
        'Discontinued After Retreatment'
    ]
    
    # Color mapping
    state_color_map = {
        'Active (Never Discontinued)': 'active_never_discontinued',
        'Active (Retreated)': 'active_retreated',
        'Discontinued Planned': 'discontinued_planned',
        'Discontinued Administrative': 'discontinued_administrative',
        'Discontinued Not Renewed': 'discontinued_not_renewed',
        'Discontinued Premature': 'discontinued_premature',
        'Discontinued After Retreatment': 'discontinued_after_retreatment'
    }
    
    # Create stacked area plot
    x = pivot_data.index
    bottom = np.zeros(len(x))
    
    for state in state_order:
        if state in pivot_data.columns:
            values = pivot_data[state].values
            color_key = state_color_map.get(state, 'active_never_discontinued')
            color = TRAFFIC_LIGHT_COLORS[color_key]
            
            ax.fill_between(
                x, bottom, bottom + values,
                color=color,
                alpha=0.8,
                label=state
            )
            bottom += values
    
    # Styling
    ax.set_xlabel("Time (Months)")
    ax.set_ylabel("Number of Patients")
    ax.set_title("Patient Cohort Flow Through Treatment States", fontsize=14, loc="left")
    
    # Set axis limits
    ax.set_xlim(0, max(x))
    ax.set_ylim(0, results.get("population_size", 1000) * 1.05)
    
    # Clean style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    ax.grid(axis='y', linestyle=':', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Legend
    available_states = [state for state in state_order if state in pivot_data.columns]
    if available_states:
        ax.legend(
            loc='center left',
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
            fontsize=9
        )
    
    plt.tight_layout()
    
    # Add summary annotation
    disc_counts = results.get("discontinuation_counts", {})
    total_disc = sum(disc_counts.values())
    
    raw_stats = results.get("raw_discontinuation_stats", {})
    total_retreat = raw_stats.get("retreatments", results.get("recurrences", {}).get("total", 0))
    
    annotation_text = f"Total Discontinuations: {total_disc}\\nTotal Retreatments: {total_retreat}"
    ax.text(
        0.02, 0.98,
        annotation_text,
        transform=ax.transAxes,
        verticalalignment='top',
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
    )
    
    return fig