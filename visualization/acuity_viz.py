from datetime import datetime, timedelta
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MonthLocator
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
    """Create a comparative plot of multiple patients' visual acuity"""
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

def plot_mean_acuity(patient_data: Dict[str, List[Dict]], 
                    start_date: datetime, end_date: datetime,
                    show: bool = True, save_path: Optional[str] = None,
                    title: str = "Mean Visual Acuity Over Time"):
    """Create a plot showing mean acuity with confidence intervals over time
    
    Args:
        patient_data: Dictionary of patient IDs to their visit histories
        start_date: Start date of simulation
        end_date: End date of simulation
        show: Whether to display the plot
        save_path: Optional path to save the plot
        title: Title for the plot
    """
    import numpy as np
    from scipy import interpolate
    
    # Create weekly timeline
    total_weeks = int((end_date - start_date).days / 7) + 1
    week_dates = [start_date + timedelta(weeks=w) for w in range(total_weeks)]
    
    # Initialize arrays for weekly data
    all_acuities = []  # List of lists, each inner list contains one patient's weekly values
    
    # Process each patient's data
    for patient_id, history in patient_data.items():
        # Extract dates and vision values
        visit_dates = []
        vision_values = []
        
        for visit in history:
            if 'date' in visit and 'vision' in visit:
                visit_dates.append(visit['date'])
                vision_values.append(float(visit['vision']))
        
        if not visit_dates:  # Skip if no data
            continue
            
        # Convert dates to weeks from start
        visit_weeks = [(d - start_date).days / 7 for d in visit_dates]
        weeks = list(range(total_weeks))
        
        # Create interpolation function
        if len(visit_weeks) > 1:  # Need at least 2 points for interpolation
            f = interpolate.interp1d(visit_weeks, vision_values, 
                                   bounds_error=False, fill_value="extrapolate")
            weekly_values = f(weeks)
            all_acuities.append(weekly_values)
    
    if not all_acuities:  # No data to plot
        return
        
    # Convert to numpy array for calculations
    all_acuities = np.array(all_acuities)
    
    # Calculate statistics
    mean_acuity = np.mean(all_acuities, axis=0)
    std_acuity = np.std(all_acuities, axis=0)
    
    # Calculate 95% confidence interval
    n_patients = len(all_acuities)
    confidence_interval = 1.96 * std_acuity / np.sqrt(n_patients)
    upper_bound = mean_acuity + confidence_interval
    lower_bound = mean_acuity - confidence_interval
    
    # Create the plot
    plt.figure(figsize=(12, 6))
    
    # Plot mean line
    plt.plot(week_dates, mean_acuity, 'b-', linewidth=2, label='Mean Acuity')
    
    # Add shaded confidence interval
    plt.fill_between(week_dates, lower_bound, upper_bound, 
                    color='b', alpha=0.2, label='95% Confidence Interval')
    
    plt.title(title)
    plt.xlabel('Time from Treatment Start')
    plt.ylabel('Visual Acuity (ETDRS letters)')
    
    # Set y-axis range
    plt.ylim(0, 85)
    
    # Format x-axis with monthly grid
    ax = plt.gca()
    ax.xaxis.set_major_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%b %Y'))
    plt.gcf().autofmt_xdate()
    
    # Add grid
    plt.grid(True, which='major', linestyle='-', alpha=0.3)
    plt.grid(True, which='minor', linestyle=':', alpha=0.2)
    
    plt.legend()
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
    
    if show:
        plt.show()
    else:
        plt.close()
