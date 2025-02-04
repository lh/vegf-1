from datetime import datetime
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import numpy as np

def plot_patient_acuity(patient_id: str, history: List[Dict], 
                       start_date: datetime, end_date: datetime,
                       show: bool = True, save_path: Optional[str] = None):
    """Create a line plot of visual acuity over time with treatment markers
    
    Args:
        patient_id: Identifier for the patient
        history: List of visit dictionaries containing date, vision, and actions
        start_date: Start date of simulation
        end_date: End date of simulation
        show: Whether to display the plot
        save_path: Optional path to save the plot
    """
    # Extract dates and vision values, and also non-injection visits
    dates = []
    vision_values = []
    injection_dates = []
    other_visit_dates = []
    
    for visit in history:
        if 'date' in visit:
            dates.append(visit['date'])
            if 'vision' in visit:
                vision_values.append(visit['vision'])
            else:
                # If no vision test this visit, use last known value
                vision_values.append(vision_values[-1] if vision_values else None)
                
            if 'injection' in visit.get('actions', []):
                injection_dates.append(visit['date'])
            else:
                other_visit_dates.append(visit['date'])
    
    # Create the plot
    plt.figure(figsize=(12, 6))
    
    # Plot vision values
    plt.plot(dates, vision_values, 'b-', label='Visual Acuity')
    
    # Add injection markers
    if injection_dates:
        vision_at_injection = [vision_values[dates.index(d)] for d in injection_dates]
        plt.plot(injection_dates, vision_at_injection, 'rx', markersize=10, 
                label='Injection', markeredgewidth=2)
    
    # Add other visit markers
    if other_visit_dates:
        vision_at_visit = [vision_values[dates.index(d)] for d in other_visit_dates]
        plt.plot(other_visit_dates, vision_at_visit, 'ko', markersize=8,
                label='Visit (no injection)', markerfacecolor='none')
    
    # Customize the plot
    plt.title(f'Visual Acuity Over Time - Patient {patient_id}')
    plt.xlabel('Date')
    plt.ylabel('Visual Acuity (ETDRS letters)')
    
    # Format x-axis
    plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    plt.gcf().autofmt_xdate()  # Rotate and align the tick labels
    
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Set y-axis range explicitly to 0-85
    plt.ylim(0, 85)
    
    plt.legend()
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save if requested
    if save_path:
        plt.savefig(save_path)
    
    if show:
        plt.show()
    else:
        plt.close()

def plot_multiple_patients(patient_data: Dict[str, List[Dict]], 
                         start_date: datetime, end_date: datetime,
                         show: bool = True, save_path: Optional[str] = None,
                         title: str = "Visual Acuity Over Time - Multiple Patients"):
    """Create a comparative plot of multiple patients' visual acuity
    
    Args:
        patient_data: Dictionary of patient IDs to their visit histories
        start_date: Start date of simulation
        end_date: End date of simulation
        show: Whether to display the plot
        save_path: Optional path to save the plot
    """
    plt.figure(figsize=(12, 6))
    
    for patient_id, history in patient_data.items():
        # Extract dates and vision values
        dates = []
        vision_values = []
        injection_dates = []
        other_visit_dates = []
        
        for visit in history:
            if 'date' in visit and 'vision' in visit:
                dates.append(visit['date'])
                vision_values.append(visit['vision'])
                
                if 'injection' in visit.get('actions', []):
                    injection_dates.append(visit['date'])
                else:
                    other_visit_dates.append(visit['date'])
        
        # Plot vision values with different color for each patient
        line = plt.plot(dates, vision_values, '-', label=f'Patient {patient_id}')
        color = line[0].get_color()
        
        # Add injection markers in same color
        if injection_dates:
            vision_at_injection = [vision_values[dates.index(d)] for d in injection_dates]
            plt.plot(injection_dates, vision_at_injection, 'x', color=color,
                    markersize=8, markeredgewidth=2)
        
        # Add other visit markers
        if other_visit_dates:
            vision_at_visit = [vision_values[dates.index(d)] for d in other_visit_dates]
            plt.plot(other_visit_dates, vision_at_visit, 'o', color=color,
                    markersize=6, markerfacecolor='none')
    
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Visual Acuity (ETDRS letters)')
    
    # Set y-axis range explicitly to 0-85
    plt.ylim(0, 85)
    
    plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    plt.gcf().autofmt_xdate()
    
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
    
    if show:
        plt.show()
    else:
        plt.close()
