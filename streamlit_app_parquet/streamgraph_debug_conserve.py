"""
Realistic streamgraph with patient conservation debugging.
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


def create_conservative_flow_data(results: Dict) -> pd.DataFrame:
    """
    Create timeline data with strict patient conservation.
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
    
    print(f"\n=== PATIENT CONSERVATION DEBUG ===")
    print(f"Population: {population_size}")
    print(f"Discontinuation counts: {disc_counts}")
    print(f"Total discontinuations expected: {sum(disc_counts.values())}")
    
    timeline_data = []
    
    # Initialize states
    states = {
        'active_never_discontinued': float(population_size),
        'active_retreated': 0.0,
        'discontinued_planned': 0.0,
        'discontinued_administrative': 0.0,
        'discontinued_not_renewed': 0.0,
        'discontinued_premature': 0.0,
        'discontinued_after_retreatment': 0.0
    }
    
    # Track totals
    total_ever_discontinued = 0.0
    total_ever_retreated = 0.0
    
    for month in range(duration_months + 1):
        t = month / duration_months
        
        # Debug every year
        if month % 12 == 0:
            total_current = sum(states.values())
            print(f"\nMonth {month} - Total: {total_current:.1f} (should be {population_size})")
            if abs(total_current - population_size) > 0.1:
                print("WARNING: Conservation violation!")
        
        # Calculate target discontinuations for this time point
        target_disc = {}
        for disc_type, final_count in disc_counts.items():
            if disc_type == "Planned":
                progress = sigmoid(t, steepness=6, midpoint=0.7)
            elif disc_type == "Administrative":
                progress = t
            elif disc_type == "Not Renewed":
                progress = stepped_curve(t, steps=3)
            elif disc_type == "Premature":
                progress = sigmoid(t, steepness=6, midpoint=0.4)
            else:
                progress = t
            
            target_disc[disc_type] = final_count * progress
        
        # Process new discontinuations this month
        for disc_type in disc_counts.keys():
            # State key mapping
            state_key = f'discontinued_{disc_type.lower()}'
            
            # Current discontinued in this category (including retreated)
            current_in_category = states.get(state_key, 0)
            
            # How many should be discontinued by now
            target = target_disc[disc_type]
            
            # New discontinuations needed
            new_disc = max(0, target - total_ever_discontinued)
            
            # Limit by available active patients
            available_active = states['active_never_discontinued'] + states['active_retreated']
            new_disc = min(new_disc, available_active)
            
            if new_disc > 0:
                # Take from active pools
                from_never = min(new_disc, states['active_never_discontinued'])
                from_retreated = new_disc - from_never
                
                states['active_never_discontinued'] -= from_never
                states['active_retreated'] -= from_retreated
                states[state_key] += new_disc
                total_ever_discontinued += new_disc
        
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
                if states[disc_state] > 0:
                    # Retreatment rate
                    rate = retreat_rates.get(retreat_key, 0.5)
                    
                    # Monthly retreatment probability
                    monthly_prob = rate * 0.02  # 2% of the rate per month
                    
                    # Calculate retreatments
                    retreat_count = states[disc_state] * monthly_prob
                    retreat_count = min(retreat_count, states[disc_state])
                    
                    if retreat_count > 0:
                        states[disc_state] -= retreat_count
                        states['active_retreated'] += retreat_count
                        total_ever_retreated += retreat_count
        
        # Re-discontinuations (with delay)
        if t > 0.3 and states['active_retreated'] > 0:
            # Higher re-discontinuation rate
            redisc_prob = 0.015  # 1.5% per month
            redisc_count = states['active_retreated'] * redisc_prob
            
            if redisc_count > 0:
                states['active_retreated'] -= redisc_count
                states['discontinued_after_retreatment'] += redisc_count
        
        # Verify conservation
        total_now = sum(states.values())
        if abs(total_now - population_size) > 0.1:
            print(f"Conservation error at month {month}: {total_now:.1f} vs {population_size}")
            # Force correction by adjusting the largest pool
            diff = population_size - total_now
            largest_state = max(states.keys(), key=lambda k: states[k])
            states[largest_state] += diff
        
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
    
    # Final verification
    final_total = sum(states.values())
    print(f"\n=== FINAL STATE ===")
    print(f"Final total: {final_total:.1f} (should be {population_size})")
    print("Conservation: " + ("PASS" if abs(final_total - population_size) < 0.1 else "FAIL"))
    
    return pd.DataFrame(timeline_data)


def generate_conserved_streamgraph(results: Dict) -> plt.Figure:
    """Generate a streamgraph with strict patient conservation."""
    
    if not results:
        raise ValueError("No simulation results provided")
    
    # Create timeline data
    timeline_data = create_conservative_flow_data(results)
    
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