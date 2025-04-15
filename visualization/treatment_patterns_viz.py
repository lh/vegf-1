"""Visualization tools for analyzing intravitreal injection treatment patterns.

This module provides functions to generate publication-quality visualizations of
treatment patterns in patients receiving intravitreal injections.

Key Features
------------
- Injection frequency heatmaps by month/year
- Treatment duration waterfall plots
- Injection interval analysis by sequence number
- Kaplan-Meier treatment persistence curves
- Visual acuity outcomes by injection count

Dependencies
------------
- pandas: For data manipulation
- matplotlib: For figure generation
- seaborn: For enhanced visualizations
- lifelines: For survival analysis (optional)

Examples
--------
>>> from visualization import treatment_patterns_viz
>>> df = pd.read_csv('injection_data.csv')
>>> fig = treatment_patterns_viz.plot_injection_frequency_heatmap(df)
>>> fig.show()

Notes
-----
- All visual acuity values in ETDRS letters (0-100 scale)
- Time units in days unless specified
- Figures include statistical annotations and reference lines
- Automatic figure saving supported
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime, timedelta

# Set up logging
import logging
logger = logging.getLogger(__name__)


def plot_injection_frequency_heatmap(data, output_path=None):
    """Create a heatmap of injection frequency by month and year.
    
    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame containing injection records with required columns:
        - 'patient_id': Unique patient identifier (str or int)
        - 'Injection Date': Date of each injection (datetime or parsable string)
    output_path : str, optional
        File path to save the plot image. If None, plot is not saved.
        Supported formats: .png, .jpg, .pdf, .svg
    
    Returns
    -------
    matplotlib.figure.Figure
        The generated figure object. Can be displayed with fig.show()
        or saved with fig.savefig().

    Examples
    --------
    >>> df = pd.read_csv('injection_data.csv')
    >>> fig = plot_injection_frequency_heatmap(df, output_path='output/heatmap.png')
    >>> fig.show()

    Notes
    -----
    - Automatically handles date parsing from strings
    - Uses YlGnBu color palette by default
    - Includes month names on x-axis
    - Logs warnings if required columns are missing
    """
    logger.debug("Creating injection frequency heatmap")
    
    # Convert injection dates to datetime if needed
    if 'Injection Date' in data.columns:
        data = data.copy()
        data['Injection Date'] = pd.to_datetime(data['Injection Date'])
        
        # Extract year and month
        data['year'] = data['Injection Date'].dt.year
        data['month'] = data['Injection Date'].dt.month
        
        # Count injections by year and month
        injection_counts = data.groupby(['year', 'month']).size().reset_index(name='count')
        
        # Create a pivot table for the heatmap
        pivot_data = injection_counts.pivot(index='year', columns='month', values='count')
        
        # Create the heatmap
        plt.figure(figsize=(12, 8))
        ax = sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='YlGnBu')
        
        # Set labels and title
        ax.set_xlabel('Month')
        ax.set_ylabel('Year')
        ax.set_title('Injection Frequency by Month and Year')
        
        # Set month names as x-axis labels
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ax.set_xticklabels(month_names)
        
        # Save the plot if output_path is provided
        if output_path:
            plt.savefig(output_path)
            logger.debug(f"Saved injection frequency heatmap to {output_path}")
        
        return plt.gcf()
    else:
        logger.warning("No 'Injection Date' column found in data")
        return None


def plot_treatment_duration_waterfall(patient_data, output_path=None):
    """Create waterfall plot of treatment durations across patients.
    
    Parameters
    ----------
    patient_data : pandas.DataFrame
        DataFrame containing treatment duration data with required columns:
        - 'patient_id': Unique patient identifier (str or int)
        - 'treatment_duration_days': Numeric duration in days
    output_path : str, optional
        File path to save the plot image. If None, plot is not saved.
    
    Returns
    -------
    matplotlib.figure.Figure
        The generated figure object with waterfall plot
    
    Examples
    --------
    >>> df = pd.read_csv('treatment_durations.csv')
    >>> fig = plot_treatment_duration_waterfall(df)
    >>> fig.savefig('output/duration_waterfall.png')

    Notes
    -----
    - Patients are sorted by treatment duration
    - Includes reference lines at 1, 2 and 3 year durations
    - Uses steelblue color for bars
    - Logs warnings if required columns are missing
    """
    logger.debug("Creating treatment duration waterfall plot")
    
    if 'treatment_duration_days' in patient_data.columns:
        # Sort by treatment duration
        sorted_data = patient_data.sort_values('treatment_duration_days')
        
        # Create the waterfall plot
        plt.figure(figsize=(12, 6))
        
        # Plot bars
        plt.bar(range(len(sorted_data)), sorted_data['treatment_duration_days'], 
                width=0.8, color='steelblue')
        
        # Set labels and title
        plt.xlabel('Patients (sorted by treatment duration)')
        plt.ylabel('Treatment Duration (days)')
        plt.title('Treatment Duration Waterfall Plot')
        
        # Add reference lines for common durations
        plt.axhline(y=365, color='r', linestyle='--', label='1 year')
        plt.axhline(y=730, color='g', linestyle='--', label='2 years')
        plt.axhline(y=1095, color='b', linestyle='--', label='3 years')
        
        plt.legend()
        
        # Save the plot if output_path is provided
        if output_path:
            plt.savefig(output_path)
            logger.debug(f"Saved treatment duration waterfall plot to {output_path}")
        
        return plt.gcf()
    else:
        logger.warning("No 'treatment_duration_days' column found in patient_data")
        return None


def plot_injection_interval_by_sequence(intervals_data, output_path=None):
    """Plot injection intervals by sequence number with statistics.
    
    Parameters
    ----------
    intervals_data : pandas.DataFrame
        DataFrame containing interval data with required columns:
        - 'injection_number': Integer sequence number (1st, 2nd, etc.)
        - 'interval_days': Numeric days since previous injection
    output_path : str, optional
        File path to save the plot image. If None, plot is not saved.
    
    Returns
    -------
    matplotlib.figure.Figure
        The generated figure object with interval statistics
    
    Examples
    --------
    >>> df = pd.read_csv('injection_intervals.csv')
    >>> fig = plot_injection_interval_by_sequence(df)
    >>> fig.show()

    Notes
    -----
    - Only includes injection numbers with ≥5 patients (configurable)
    - Shows mean ± SD and median intervals
    - Includes reference lines for monthly (28d), bi-monthly (56d), quarterly (84d)
    - Annotates each point with patient count
    - Logs warnings if required columns are missing
    """
    logger.debug("Creating injection interval by sequence plot")
    
    if 'injection_number' in intervals_data.columns and 'interval_days' in intervals_data.columns:
        # Group by injection number and calculate statistics
        grouped = intervals_data.groupby('injection_number')['interval_days'].agg(
            ['mean', 'median', 'std', 'count']
        ).reset_index()
        
        # Filter to injection numbers with sufficient data
        min_count = 5  # Minimum number of patients for each injection number
        grouped = grouped[grouped['count'] >= min_count]
        
        # Create the plot
        plt.figure(figsize=(12, 6))
        
        # Plot mean intervals with error bars
        plt.errorbar(grouped['injection_number'], grouped['mean'], 
                     yerr=grouped['std'], fmt='o-', capsize=5, 
                     label='Mean ± SD', color='steelblue')
        
        # Plot median intervals
        plt.plot(grouped['injection_number'], grouped['median'], 's--', 
                 label='Median', color='darkorange')
        
        # Set labels and title
        plt.xlabel('Injection Sequence Number')
        plt.ylabel('Interval (days)')
        plt.title('Injection Intervals by Sequence Number')
        
        # Add reference lines for common intervals
        plt.axhline(y=28, color='r', linestyle=':', label='28 days (monthly)')
        plt.axhline(y=56, color='g', linestyle=':', label='56 days (bi-monthly)')
        plt.axhline(y=84, color='b', linestyle=':', label='84 days (quarterly)')
        
        # Add sample size annotations
        for i, row in grouped.iterrows():
            plt.annotate(f"n={int(row['count'])}", 
                         (row['injection_number'], row['mean']),
                         textcoords="offset points", 
                         xytext=(0, 10), 
                         ha='center')
        
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Save the plot if output_path is provided
        if output_path:
            plt.savefig(output_path)
            logger.debug(f"Saved injection interval by sequence plot to {output_path}")
        
        return plt.gcf()
    else:
        logger.warning("Required columns not found in intervals_data")
        return None


def plot_treatment_persistence(patient_data, output_path=None):
    """Create Kaplan-Meier plot of treatment persistence over time.
    
    Parameters
    ----------
    patient_data : pandas.DataFrame
        DataFrame containing treatment duration data with columns:
        - 'treatment_duration_days': Days from first to last injection
        - 'event': 1 if discontinued, 0 if still in treatment (optional)
    output_path : str, optional
        File path to save the plot image
    
    Returns
    -------
    matplotlib.figure.Figure
        The generated figure object
    
    Notes
    -----
    - Falls back to simple histogram if lifelines package not available
    - Includes reference lines at 1, 2 and 3 years
    - Requires 'treatment_duration_days' column
    """
    logger.debug("Creating treatment persistence plot")
    
    try:
        from lifelines import KaplanMeierFitter
        
        if 'treatment_duration_days' in patient_data.columns:
            # Create a copy of the data
            data = patient_data.copy()
            
            # Create an event indicator (all 1 for now, assuming all patients discontinued)
            # In a real analysis, you would use actual discontinuation status
            data['event'] = 1
            
            # For patients still in treatment, set event to 0
            # This is a placeholder - in real analysis, you would use actual status
            # data.loc[data['still_in_treatment'] == True, 'event'] = 0
            
            # Fit the Kaplan-Meier model
            kmf = KaplanMeierFitter()
            kmf.fit(data['treatment_duration_days'], event_observed=data['event'])
            
            # Create the plot
            plt.figure(figsize=(10, 6))
            
            # Plot the survival curve
            kmf.plot_survival_function(label='Treatment Persistence')
            
            # Add reference lines for common timepoints
            plt.axvline(x=365, color='r', linestyle='--', label='1 year')
            plt.axvline(x=730, color='g', linestyle='--', label='2 years')
            plt.axvline(x=1095, color='b', linestyle='--', label='3 years')
            
            # Set labels and title
            plt.xlabel('Days from First Injection')
            plt.ylabel('Proportion Remaining in Treatment')
            plt.title('Kaplan-Meier Estimate of Treatment Persistence')
            
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Save the plot if output_path is provided
            if output_path:
                plt.savefig(output_path)
                logger.debug(f"Saved treatment persistence plot to {output_path}")
            
            return plt.gcf()
        else:
            logger.warning("No 'treatment_duration_days' column found in patient_data")
            return None
    
    except ImportError:
        logger.warning("lifelines package not available, skipping Kaplan-Meier plot")
        
        # Create a simple histogram as fallback
        if 'treatment_duration_days' in patient_data.columns:
            plt.figure(figsize=(10, 6))
            
            sns.histplot(patient_data['treatment_duration_days'], bins=20, kde=True)
            
            plt.xlabel('Treatment Duration (days)')
            plt.ylabel('Frequency')
            plt.title('Distribution of Treatment Durations')
            
            # Add reference lines for common timepoints
            plt.axvline(x=365, color='r', linestyle='--', label='1 year')
            plt.axvline(x=730, color='g', linestyle='--', label='2 years')
            plt.axvline(x=1095, color='b', linestyle='--', label='3 years')
            
            plt.legend()
            
            # Save the plot if output_path is provided
            if output_path:
                plt.savefig(output_path)
                logger.debug(f"Saved treatment duration histogram to {output_path}")
            
            return plt.gcf()
        else:
            logger.warning("No 'treatment_duration_days' column found in patient_data")
            return None


def plot_va_by_injection_count(data, output_path=None):
    """Plot visual acuity outcomes by number of injections received.
    
    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame containing visual acuity and injection data with columns:
        - 'injection_count': Total number of injections received
        - 'va_change': Change in visual acuity from baseline (ETDRS letters)
    output_path : str, optional
        File path to save the plot image
    
    Returns
    -------
    matplotlib.figure.Figure
        The generated figure object
    
    Notes
    -----
    - Only includes injection counts with at least 3 patients
    - Shows both mean (with SD) and median VA change
    - Includes reference line at zero change
    """
    logger.debug("Creating VA by injection count plot")
    
    if 'injection_count' in data.columns and 'va_change' in data.columns:
        # Group by injection count
        grouped = data.groupby('injection_count')['va_change'].agg(
            ['mean', 'median', 'std', 'count']
        ).reset_index()
        
        # Filter to counts with sufficient data
        min_count = 3  # Minimum number of patients for each injection count
        grouped = grouped[grouped['count'] >= min_count]
        
        # Create the plot
        plt.figure(figsize=(12, 6))
        
        # Plot mean VA change with error bars
        plt.errorbar(grouped['injection_count'], grouped['mean'], 
                     yerr=grouped['std'], fmt='o-', capsize=5, 
                     label='Mean ± SD', color='steelblue')
        
        # Plot median VA change
        plt.plot(grouped['injection_count'], grouped['median'], 's--', 
                 label='Median', color='darkorange')
        
        # Set labels and title
        plt.xlabel('Number of Injections')
        plt.ylabel('VA Change from Baseline (letters)')
        plt.title('Visual Acuity Change by Number of Injections')
        
        # Add reference line for no change
        plt.axhline(y=0, color='k', linestyle='-', label='No change')
        
        # Add sample size annotations
        for i, row in grouped.iterrows():
            plt.annotate(f"n={int(row['count'])}", 
                         (row['injection_count'], row['mean']),
                         textcoords="offset points", 
                         xytext=(0, 10), 
                         ha='center')
        
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Save the plot if output_path is provided
        if output_path:
            plt.savefig(output_path)
            logger.debug(f"Saved VA by injection count plot to {output_path}")
        
        return plt.gcf()
    else:
        logger.warning("Required columns not found in data")
        return None
