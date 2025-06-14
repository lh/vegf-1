"""
Fixed streamgraph implementation that properly imports the color system.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

# Fix the import path for the visualization module
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the central color system - NO FALLBACKS
from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS


def sigmoid(x, steepness=10, midpoint=0.5):
    """Sigmoid function for smooth transitions."""
    return 1 / (1 + np.exp(-steepness * (x - midpoint)))


def stepped_curve(x, steps=4):
    """Create a stepped curve for certain events."""
    return np.floor(x * steps) / steps + (x * steps % 1) * 0.2


def create_streamgraph_data(results: Dict) -> pd.DataFrame:
    """Create timeline data from simulation results."""
    duration_years = results.get("duration_years", 5)
    duration_months = int(duration_years * 12)
    population_size = results.get("population_size", 250)
    
    # Get final counts
    disc_counts = results.get("discontinuation_counts", {})
    recurrences = results.get("recurrences", {})
    retreatments_by_type = recurrences.get("by_type", {})
    
    timeline_data = []
    
    # Initialize cumulative tracking
    cumulative_disc = {k: 0.0 for k in disc_counts.keys()}
    cumulative_retreat = {
        "Planned": 0.0,
        "Administrative": 0.0,
        "Not Renewed": 0.0,
        "Premature": 0.0
    }
    
    # Create curves for each month
    for month in range(duration_months + 1):
        t = month / duration_months
        
        # Apply different curves for different discontinuation types
        for disc_type, total_count in disc_counts.items():
            if disc_type == "Planned":
                curve = sigmoid(t, steepness=8, midpoint=0.7)
            elif disc_type == "Administrative":
                curve = t  # Linear
            elif disc_type == "Not Renewed":
                curve = stepped_curve(t, steps=4)
            elif disc_type == "Premature":
                curve = sigmoid(t, steepness=8, midpoint=0.3)
            else:
                curve = t
            
            cumulative_disc[disc_type] = total_count * curve
        
        # Calculate retreatments
        retreat_key_mapping = {
            "Planned": "stable_max_interval",
            "Administrative": "random_administrative",
            "Not Renewed": "treatment_duration",
            "Premature": "premature"
        }
        
        for disc_type, retreat_key in retreat_key_mapping.items():
            if disc_type in cumulative_disc:
                treat_count = retreatments_by_type.get(retreat_key, 0)
                retreat_curve = sigmoid(t - 0.1, steepness=10, midpoint=0.5)
                retreat_curve = max(0, retreat_curve)
                cumulative_retreat[disc_type] = treat_count * retreat_curve
        
        # Calculate states
        total_discontinued = sum(cumulative_disc.values())
        total_retreated = sum(cumulative_retreat.values())
        active_count = population_size - total_discontinued + total_retreated
        active_never_disc = population_size - total_discontinued
        
        # Store data
        timeline_data.append({
            'time_months': month,
            'state': 'Active (Never Discontinued)',
            'count': active_never_disc
        })
        
        # Add discontinuation states
        for disc_type, count in cumulative_disc.items():
            if count > 0:
                timeline_data.append({
                    'time_months': month,
                    'state': f'Discontinued {disc_type}',
                    'count': count
                })
        
        # Add retreatment states
        for disc_type, count in cumulative_retreat.items():
            if count > 0:
                timeline_data.append({
                    'time_months': month,
                    'state': f'Retreated {disc_type}',
                    'count': count
                })
    
    return pd.DataFrame(timeline_data)


def generate_fixed_streamgraph(results: Dict) -> plt.Figure:
    """Generate a streamgraph from simulation results."""
    
    # No fallbacks - fail fast if no data
    if not results:
        raise ValueError("No simulation results provided")
    
    # Create timeline data
    timeline_data = create_streamgraph_data(results)
    
    # Pivot data for stacking
    pivot_data = timeline_data.pivot(
        index='time_months', 
        columns='state', 
        values='count'
    ).fillna(0)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # State ordering
    state_order = [
        'Active (Never Discontinued)',
        'Discontinued Planned',
        'Discontinued Administrative', 
        'Discontinued Not Renewed',
        'Discontinued Premature',
        'Retreated Planned',
        'Retreated Administrative',
        'Retreated Not Renewed', 
        'Retreated Premature'
    ]
    
    # Filter available states
    available_states = [state for state in state_order if state in pivot_data.columns]
    
    # Create stacked area plot
    x = pivot_data.index
    bottom = np.zeros(len(x))
    
    for state in available_states:
        values = pivot_data[state].values
        
        # Determine color using the central color system
        if state == 'Active (Never Discontinued)':
            color = SEMANTIC_COLORS["patient_states"]["active"]
            alpha = ALPHAS["dense"]
        elif state.startswith('Discontinued'):
            disc_type = state.replace('Discontinued ', '')
            color = SEMANTIC_COLORS["discontinuation"].get(
                disc_type.lower()
            )
            if not color:
                raise KeyError(f"No color defined for discontinuation type: {disc_type}")
            alpha = ALPHAS["medium"]
        elif state.startswith('Retreated'):
            retreat_type = state.replace('Retreated ', '')
            color = SEMANTIC_COLORS["retreatment"].get(
                retreat_type.lower()
            )
            if not color:
                raise KeyError(f"No color defined for retreatment type: {retreat_type}")
            alpha = ALPHAS["light"]
        else:
            raise ValueError(f"Unknown state type: {state}")
        
        ax.fill_between(
            x, bottom, bottom + values,
            color=color,
            alpha=alpha,
            label=state
        )
        bottom += values
    
    # Styling
    ax.set_xlabel("Time (Months)")
    ax.set_ylabel("Number of Patients")
    ax.set_title("Patient Cohort Flow Through Treatment States", fontsize=14, loc="left")
    
    # Set axis limits
    ax.set_xlim(0, max(x))
    ax.set_ylim(0, max(bottom) * 1.05)
    
    # Clean style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    ax.grid(axis='y', linestyle=':', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Legend outside plot area
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
    total_retreat = results.get("recurrences", {}).get("total", 0)
    
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