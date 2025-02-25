"""
Treatment Patterns Visualization

This module provides visualization functions for analyzing treatment patterns
in intravitreal injection data.
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
    """
    Create a heatmap showing injection frequency over time.
    
    Args:
        data: DataFrame with 'patient_id' and 'Injection Date' columns
        output_path: Path to save the plot (optional)
    
    Returns:
        matplotlib figure
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
    """
    Create a waterfall plot of treatment durations.
    
    Args:
        patient_data: DataFrame with 'patient_id' and 'treatment_duration_days' columns
        output_path: Path to save the plot (optional)
    
    Returns:
        matplotlib figure
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
    """
    Plot injection intervals by sequence number.
    
    Args:
        intervals_data: DataFrame with 'injection_number' and 'interval_days' columns
        output_path: Path to save the plot (optional)
    
    Returns:
        matplotlib figure
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
    """
    Create a Kaplan-Meier plot of treatment persistence.
    
    Args:
        patient_data: DataFrame with treatment duration information
        output_path: Path to save the plot (optional)
    
    Returns:
        matplotlib figure
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
    """
    Plot visual acuity outcomes by number of injections received.
    
    Args:
        data: DataFrame with patient data including VA and injection counts
        output_path: Path to save the plot (optional)
    
    Returns:
        matplotlib figure
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
