"""Visual acuity plotting utilities for clinical trial data visualization.

This module provides matplotlib-based visualizations for analyzing visual acuity data
from clinical trials and simulations. All visualizations use ETDRS letter scores (0-100 scale).

Key Features
------------
- Individual patient acuity trajectories with treatment markers
- Multi-patient comparative plots
- Population-level mean acuity with confidence intervals
- Dual timeframe support (calendar time and patient time)
- Sample size awareness with weighted smoothing
- Standardized formatting for clinical publications

Notes
-----
- All visual acuity values should be in ETDRS letters (0-100 scale)
- Dates should be datetime objects for proper axis formatting
- Patient time can be represented in days or weeks since enrollment
- Plots are designed for 12x6 inch figures suitable for publications
- Sample size visualization helps interpret validity of means
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Union, Callable
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MonthLocator, WeekdayLocator
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd
from collections import defaultdict

# Import the central color system
try:
    from visualization.color_system import COLORS, SEMANTIC_COLORS, ALPHAS
except ImportError:
    # Fallback if the central color system is not available
    COLORS = {
        'primary': '#4682B4',    # Steel Blue - for visual acuity data
        'secondary': '#B22222',  # Firebrick - for critical information
        'patient_counts': '#8FAD91',  # Muted Sage Green - for patient counts
    }
    ALPHAS = {
        'high': 0.8,        # High opacity for primary elements
        'medium': 0.5,      # Medium opacity for standard elements
        'low': 0.2,         # Low opacity for background elements
        'very_low': 0.1,    # Very low opacity for subtle elements
        'patient_counts': 0.5  # Consistent opacity for all patient/sample count visualizations
    }
    SEMANTIC_COLORS = {
        'acuity_data': COLORS['primary'],
        'patient_counts': COLORS['patient_counts'],
        'critical_info': COLORS['secondary'],
    }

def plot_patient_acuity(patient_id: str, history: List[Dict], 
                       start_date: datetime, end_date: datetime,
                       show: bool = True, save_path: Optional[str] = None):
    """Plot single patient's visual acuity trajectory with treatment markers.
    
    Creates a line plot of visual acuity over time, with markers indicating
    injection visits and other clinical visits. The y-axis shows ETDRS letter
    scores (0-100 scale).

    Parameters
    ----------
    patient_id : str
        Unique identifier for the patient
    history : List[Dict]
        List of visit dictionaries containing:
        - date: datetime of visit
        - vision: ETDRS letter score (0-100)
        - actions: List of actions taken (e.g. ['injection'])
    start_date : datetime
        Start date of the observation period
    end_date : datetime
        End date of the observation period  
    show : bool, optional
        Whether to display the plot (default True)
    save_path : str, optional
        If provided, save plot to this file path

    Returns
    -------
    None
        Displays or saves plot but returns nothing

    Examples
    --------
    >>> plot_patient_acuity('123', visits, start, end, save_path='acuity.png')
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
    """Plot comparative visual acuity trajectories for multiple patients.
    
    Creates a line plot showing visual acuity over time for multiple patients
    on the same axes, with unique colors for each patient and markers for
    treatment visits.

    Parameters
    ----------
    patient_data : Dict[str, List[Dict]]
        Dictionary mapping patient IDs to their visit histories
    start_date : datetime
        Start date of the observation period
    end_date : datetime 
        End date of the observation period
    show : bool, optional
        Whether to display the plot (default True)
    save_path : str, optional
        If provided, save plot to this file path
    title : str, optional
        Custom title for the plot

    Returns
    -------
    None
        Displays or saves plot but returns nothing
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

def plot_mean_acuity(patient_data: Dict[str, List[Dict]], 
                    start_date: datetime, end_date: datetime,
                    show: bool = True, save_path: Optional[str] = None,
                    title: str = "Mean Visual Acuity Over Time"):
    """Plot mean visual acuity with confidence intervals over time.
    
    Creates a plot showing the mean visual acuity trajectory across patients
    with 95% confidence intervals. Uses linear interpolation between visits
    to calculate weekly acuity values.

    Parameters
    ----------
    patient_data : Dict[str, List[Dict]]
        Dictionary mapping patient IDs to their visit histories
    start_date : datetime
        Start date of the observation period
    end_date : datetime
        End date of the observation period
    show : bool, optional
        Whether to display the plot (default True)
    save_path : str, optional
        If provided, save plot to this file path
    title : str, optional
        Custom title for the plot

    Returns
    -------
    None
        Displays or saves plot but returns nothing

    Notes
    -----
    - Uses linear interpolation between visits to estimate weekly values
    - Requires at least 2 visits per patient for interpolation
    - Confidence intervals assume normal distribution
    - Missing values are handled via linear extrapolation
    - Weekly interpolation provides smoother trajectories than raw visit data
    - For small sample sizes (<30), consider using t-distribution instead
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

def plot_patient_acuity_by_patient_time(patient_id: str, 
                                       history: List[Dict],
                                       enrollment_date: datetime,
                                       max_weeks: int = 52,
                                       show: bool = True, 
                                       save_path: Optional[str] = None):
    """Plot a single patient's visual acuity by time since enrollment.
    
    Creates a line plot showing visual acuity trajectory with patient time
    (weeks since enrollment) on the x-axis instead of calendar dates.
    
    Parameters
    ----------
    patient_id : str
        Unique identifier for the patient
    history : List[Dict]
        List of visit dictionaries containing:
        - date: datetime of visit
        - vision: ETDRS letter score (0-100)
        - actions: List of actions taken (e.g. ['injection'])
    enrollment_date : datetime
        Date when the patient was enrolled in the treatment program
    max_weeks : int, optional
        Maximum number of weeks to display (default 52)
    show : bool, optional
        Whether to display the plot (default True)
    save_path : str, optional
        If provided, save plot to this file path
        
    Returns
    -------
    None
        Displays or saves plot but returns nothing
        
    Notes
    -----
    - Patient time is measured in weeks since enrollment
    - This visualization is useful for comparing patients enrolled at different times
    - Patient time removes calendar time bias from the analysis
    """
    # Extract dates, convert to weeks since enrollment, and vision values
    weeks_since_enrollment = []
    vision_values = []
    injection_weeks = []
    other_visit_weeks = []
    
    for visit in history:
        if 'date' in visit:
            # Calculate weeks since enrollment
            weeks = (visit['date'] - enrollment_date).days / 7
            if weeks > max_weeks:
                continue  # Skip visits beyond max_weeks
                
            weeks_since_enrollment.append(weeks)
            
            if 'vision' in visit:
                vision_values.append(visit['vision'])
            else:
                # If no vision test this visit, use last known value
                vision_values.append(vision_values[-1] if vision_values else None)
                
            if 'injection' in visit.get('actions', []):
                injection_weeks.append(weeks)
            else:
                other_visit_weeks.append(weeks)
    
    # Create the plot
    plt.figure(figsize=(12, 6))
    
    # Plot vision values
    plt.plot(weeks_since_enrollment, vision_values, 'b-', label='Visual Acuity')
    
    # Add injection markers
    if injection_weeks:
        vision_at_injection = [vision_values[weeks_since_enrollment.index(w)] for w in injection_weeks]
        plt.plot(injection_weeks, vision_at_injection, 'rx', markersize=10, 
                label='Injection', markeredgewidth=2)
    
    # Add other visit markers
    if other_visit_weeks:
        vision_at_visit = [vision_values[weeks_since_enrollment.index(w)] for w in other_visit_weeks]
        plt.plot(other_visit_weeks, vision_at_visit, 'ko', markersize=8,
                label='Visit (no injection)', markerfacecolor='none')
    
    # Customize the plot
    plt.title(f'Visual Acuity by Patient Time - Patient {patient_id}')
    plt.xlabel('Weeks Since Enrollment')
    plt.ylabel('Visual Acuity (ETDRS letters)')
    
    # Format x-axis with week markers
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
    
    # Add vertical lines for key timepoints
    for week in [4, 12, 24, 36, 48]:
        if week <= max_weeks:
            plt.axvline(x=week, color='gray', linestyle='--', alpha=0.5)
    
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Set y-axis range explicitly to 0-85
    plt.ylim(0, 85)
    plt.xlim(0, max_weeks)
    
    plt.legend()
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
    
    if show:
        plt.show()
    else:
        plt.close()

def plot_mean_acuity_with_sample_size(patient_data: Dict[str, List[Dict]],
                                     enrollment_dates: Dict[str, datetime],
                                     start_date: datetime,
                                     end_date: datetime,
                                     time_unit: str = 'calendar',
                                     show: bool = True,
                                     save_path: Optional[str] = None,
                                     title: Optional[str] = None):
    """Plot mean visual acuity with confidence intervals and sample size indicators.
    
    Creates a plot showing mean visual acuity with 95% confidence intervals and a
    secondary axis showing the sample size at each time point. Can plot by calendar
    time or patient time (weeks since enrollment).
    
    Parameters
    ----------
    patient_data : Dict[str, List[Dict]]
        Dictionary mapping patient IDs to their visit histories
    enrollment_dates : Dict[str, datetime]
        Dictionary mapping patient IDs to their enrollment dates
    start_date : datetime
        Start date of the observation period (for calendar time)
    end_date : datetime
        End date of the observation period (for calendar time)
    time_unit : str, optional
        'calendar' for real-world dates or 'patient' for weeks since enrollment
        (default 'calendar')
    show : bool, optional
        Whether to display the plot (default True)
    save_path : str, optional
        If provided, save plot to this file path
    title : str, optional
        Custom title for the plot
        
    Returns
    -------
    None
        Displays or saves plot but returns nothing
        
    Notes
    -----
    - Sample size visualization is critical for interpreting confidence intervals
    - Smaller sample sizes result in wider confidence intervals
    - Patient time analysis requires enrollment dates for all patients
    - For calendar time, dates outside the simulation period are excluded
    - For patient time, weeks beyond 52 are excluded by default
    """
    import numpy as np
    from scipy import interpolate
    
    # Set default title based on time unit
    if title is None:
        title = f"Mean Visual Acuity by {'Calendar Time' if time_unit == 'calendar' else 'Patient Time'}"
    
    # For calendar time, we use weekly bins
    if time_unit == 'calendar':
        # Create weekly timeline
        total_weeks = int((end_date - start_date).days / 7) + 1
        time_points = [start_date + timedelta(weeks=w) for w in range(total_weeks)]
        x_label = 'Calendar Date'
        max_time = total_weeks
    else:  # patient time
        # Use weeks since enrollment (0-52)
        max_time = 52  # Maximum number of weeks to track for patient time
        time_points = list(range(max_time + 1))
        x_label = 'Weeks Since Enrollment'
    
    # Data structures for weekly statistics
    acuity_values = [[] for _ in range(max_time + 1)]  # List of acuity values for each time point
    
    # Process each patient's data
    for patient_id, history in patient_data.items():
        # Get enrollment date for this patient
        if time_unit == 'patient' and patient_id not in enrollment_dates:
            continue  # Skip if we don't have enrollment date for patient time
            
        enrollment_date = enrollment_dates.get(patient_id, start_date)
        
        # Extract dates and vision values
        visit_dates = []
        vision_values = []
        
        for visit in history:
            if 'date' in visit and 'vision' in visit:
                visit_dates.append(visit['date'])
                vision_values.append(float(visit['vision']))
        
        if not visit_dates:  # Skip if no data
            continue
            
        # Convert dates to appropriate time unit
        if time_unit == 'calendar':
            # Weeks from simulation start
            visit_time_points = [(d - start_date).days // 7 for d in visit_dates]
        else:  # patient time
            # Weeks from enrollment
            visit_time_points = [(d - enrollment_date).days // 7 for d in visit_dates]
            
        # Filter out visits outside our timeline
        valid_indices = [i for i, tp in enumerate(visit_time_points) if 0 <= tp <= max_time]
        visit_time_points = [visit_time_points[i] for i in valid_indices]
        visit_vision_values = [vision_values[i] for i in valid_indices]
        
        # Add vision values to the appropriate time point bins
        for time_point, vision in zip(visit_time_points, visit_vision_values):
            acuity_values[time_point].append(vision)
    
    # Calculate statistics for each time point
    mean_acuity = []
    lower_bound = []
    upper_bound = []
    sample_sizes = []

    for values in acuity_values:
        if values:  # If we have data for this time point
            mean = np.mean(values)
            std = np.std(values)
            n = len(values)
            conf_interval = 1.96 * std / np.sqrt(n)  # 95% CI

            mean_acuity.append(mean)
            lower_bound.append(max(0, mean - conf_interval))  # Floor at 0
            upper_bound.append(min(85, mean + conf_interval))  # Ceiling at 85
            sample_sizes.append(n)
        else:  # No data
            mean_acuity.append(np.nan)
            lower_bound.append(np.nan)
            upper_bound.append(np.nan)
            sample_sizes.append(0)

    # Create the plot with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot mean acuity line on primary axis
    color = 'tab:blue'
    ax1.set_xlabel(x_label)
    ax1.set_ylabel('Visual Acuity (ETDRS letters)', color=color)

    # Convert time_points for plotting and ensure consistent lengths
    if time_unit == 'calendar':
        # Create a range matching the length of mean_acuity
        # This ensures x and y have the same dimensions
        plot_x = time_points[:len(mean_acuity)]

        # If mean_acuity is longer than time_points, truncate to match
        if len(mean_acuity) > len(plot_x):
            mean_acuity = mean_acuity[:len(plot_x)]
            lower_bound = lower_bound[:len(plot_x)]
            upper_bound = upper_bound[:len(plot_x)]
            sample_sizes = sample_sizes[:len(plot_x)]
    else:
        # Use week numbers and ensure length matches
        plot_x = list(range(len(mean_acuity)))  # Use week numbers

    # Double-check that arrays have matching dimensions
    if len(plot_x) != len(mean_acuity):
        # Force them to be the same length by taking the shorter length
        min_len = min(len(plot_x), len(mean_acuity))
        plot_x = plot_x[:min_len]
        mean_acuity = mean_acuity[:min_len]
        lower_bound = lower_bound[:min_len]
        upper_bound = upper_bound[:min_len]
        sample_sizes = sample_sizes[:min_len]

    # Plot mean line and CI
    line1 = ax1.plot(plot_x, mean_acuity, color=color, linewidth=2, label='Mean Acuity')
    ax1.fill_between(plot_x, lower_bound, upper_bound, color=color, alpha=0.2, label='95% CI')
    ax1.set_ylim(0, 85)
    ax1.tick_params(axis='y', labelcolor=color)
    
    # Create second axis for sample size
    ax2 = ax1.twinx()
    patient_counts_color = SEMANTIC_COLORS['patient_counts']
    ax2.set_ylabel('Sample Size', color=patient_counts_color)
    line2 = ax2.bar(plot_x, sample_sizes, alpha=ALPHAS['patient_counts'], color=patient_counts_color, width=0.7, label='Sample Size')
    ax2.tick_params(axis='y', labelcolor=patient_counts_color)
    
    # Format x-axis based on time unit
    if time_unit == 'calendar':
        ax1.xaxis.set_major_formatter(DateFormatter('%b %Y'))
        plt.gcf().autofmt_xdate()
    else:
        ax1.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    # Set title and grid
    plt.title(title)
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Create a joint legend
    lines = line1 + [line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='best')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path)
    
    if show:
        plt.show()
    else:
        plt.close()

def plot_dual_timeframe_acuity(patient_data: Dict[str, List[Dict]],
                              enrollment_dates: Dict[str, datetime],
                              start_date: datetime,
                              end_date: datetime,
                              show: bool = True,
                              save_path: Optional[str] = None):
    """Create a comparative dual timeframe visualization of mean visual acuity.

    Generates a two-panel figure showing mean visual acuity by calendar time
    (left panel) and patient time (right panel). This visualization helps analyze
    the impact of staggered enrollment on treatment outcomes.

    Parameters
    ----------
    patient_data : Dict[str, List[Dict]]
        Dictionary mapping patient IDs to their visit histories
    enrollment_dates : Dict[str, datetime]
        Dictionary mapping patient IDs to their enrollment dates
    start_date : datetime
        Start date of the observation period
    end_date : datetime
        End date of the observation period
    show : bool, optional
        Whether to display the plot (default True)
    save_path : str, optional
        If provided, save plot to this file path

    Returns
    -------
    None
        Displays or saves plot but returns nothing

    Notes
    -----
    - Calendar time shows the real-world timeline from the start of the simulation
    - Patient time shows time since each patient's enrollment
    - Comparing both timeframes helps distinguish time-based from enrollment effects
    - Sample size indicators help interpret the reliability of mean estimates
    - Confidence intervals are wider early in calendar time and later in patient time
      due to smaller sample sizes at those points
    """
    try:
        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Create separate figures for each panel (avoids dimension mismatch issues)
        # First panel - Calendar time
        fig1 = plt.figure(figsize=(8, 6))
        cal_ax = fig1.add_subplot(111)

        # Call plot_mean_acuity_with_sample_size on separate figure
        plot_mean_acuity_with_sample_size(
            patient_data=patient_data,
            enrollment_dates=enrollment_dates,
            start_date=start_date,
            end_date=end_date,
            time_unit='calendar',
            show=False,
            title="Mean Visual Acuity by Calendar Time"
        )

        # Capture and close the figure
        calendar_img = fig1.canvas.renderer._renderer
        plt.close(fig1)

        # Second panel - Patient time
        fig2 = plt.figure(figsize=(8, 6))
        pat_ax = fig2.add_subplot(111)

        plot_mean_acuity_with_sample_size(
            patient_data=patient_data,
            enrollment_dates=enrollment_dates,
            start_date=start_date,
            end_date=end_date,
            time_unit='patient',
            show=False,
            title="Mean Visual Acuity by Patient Time"
        )

        # Capture and close the figure
        patient_img = fig2.canvas.renderer._renderer
        plt.close(fig2)

        # Now create the main dual figure
        fig_dual = plt.figure(figsize=(16, 6))

        # Create two subplot axes
        ax_cal = fig_dual.add_subplot(121)
        ax_pat = fig_dual.add_subplot(122)

        # Plot calendar acuity directly using plot_mean_acuity_with_sample_size
        plt.sca(ax_cal)
        plot_mean_acuity_with_sample_size(
            patient_data=patient_data,
            enrollment_dates=enrollment_dates,
            start_date=start_date,
            end_date=end_date,
            time_unit='calendar',
            show=False,
            title="Mean Visual Acuity by Calendar Time"
        )

        # Plot patient time acuity directly
        plt.sca(ax_pat)
        plot_mean_acuity_with_sample_size(
            patient_data=patient_data,
            enrollment_dates=enrollment_dates,
            start_date=start_date,
            end_date=end_date,
            time_unit='patient',
            show=False,
            title="Mean Visual Acuity by Patient Time"
        )

        # Add a common title
        plt.suptitle("Dual Timeframe Analysis of Visual Acuity", fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust for the suptitle

        if save_path:
            plt.savefig(save_path)

        if show:
            plt.show()
        else:
            plt.close(fig_dual)

    except Exception as e:
        import traceback
        print(f"Error in plot_dual_timeframe_acuity: {e}")
        print(traceback.format_exc())
        # Create a simple error figure
        fig = plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, f"Error creating visualization:\n{str(e)}",
                 ha='center', va='center', fontsize=12)
        if save_path:
            plt.savefig(save_path)
        plt.close()