"""Visualization of patient outcomes and treatment results.

This module provides tools for visualizing key metrics from ophthalmic treatment
protocols, including visual acuity trends, patient retention, and other outcomes.

Key Features
------------
- Mean visual acuity plotting with confidence intervals
- Patient retention curves
- Statistical annotations and reference lines
- Publication-quality figure formatting

Dependencies
------------
- matplotlib: For figure generation
- numpy: For numerical operations
- analysis.patient_outcomes: For statistical analysis

Examples
--------
>>> from visualization.outcome_viz import OutcomeVisualizer
>>> viz = OutcomeVisualizer()
>>> viz.plot_mean_acuity(patient_data)
>>> viz.plot_patient_retention(patient_data)

Notes
-----
- All visual acuity values in ETDRS letters
- Time units in weeks unless specified
- Figures automatically handle date formatting and labeling
"""

from datetime import datetime
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import numpy as np
from analysis.patient_outcomes import PatientOutcomeAnalyzer, TimePoint

class OutcomeVisualizer:
    """Visualizes patient outcome data with statistical analysis.

    This class provides methods to generate publication-quality visualizations
    of clinical trial outcomes, including visual acuity trends and patient retention.

    Attributes
    ----------
    figsize : tuple
        Default figure size (width, height) in inches
    analyzer : PatientOutcomeAnalyzer
        Statistical analysis helper class

    Examples
    --------
    >>> viz = OutcomeVisualizer(figsize=(10, 6))
    >>> viz.plot_mean_acuity(patient_data)
    >>> viz.plot_patient_retention(patient_data)

    Notes
    -----
    - All visualizations use ETDRS letter scores (0-100 scale)
    - Time units are in weeks unless specified
    - Figures include statistical annotations and reference lines
    """
    
    def __init__(self, figsize=(12, 6)):
        """Initialize the outcome visualizer with default figure size.

        Parameters
        ----------
        figsize : tuple, optional
            Default figure dimensions (width, height) in inches.
            Default is (12, 6) for landscape orientation.

        Examples
        --------
        >>> viz = OutcomeVisualizer(figsize=(10, 5))
        """
        self.figsize = figsize
        self.analyzer = PatientOutcomeAnalyzer()
    
    def plot_mean_acuity(self, patient_data: Dict[str, List[Dict]], 
                        show: bool = True, save_path: Optional[str] = None,
                        title: str = "Mean Visual Acuity Over Time"):
        """Plot mean visual acuity with confidence intervals over time.

        Parameters
        ----------
        patient_data : Dict[str, List[Dict]]
            Dictionary mapping patient IDs to lists of visit dictionaries.
            Each visit dict should contain:
            - 'date': datetime of visit
            - 'vision': ETDRS letter score (0-100)
        show : bool, optional
            Whether to display the plot (default True)
        save_path : str, optional
            File path to save the plot (default None)
        title : str, optional
            Plot title (default "Mean Visual Acuity Over Time")

        Returns
        -------
        None
            Displays or saves plot but returns nothing

        Notes
        -----
        - Uses 95% confidence intervals assuming normal distribution
        - Includes secondary axis showing number of patients
        - Automatically converts weeks to months on x-axis
        - Adds median follow-up annotation
        """
        # Analyze data
        time_points = self.analyzer.analyze_visual_acuity(patient_data)
        if not time_points:
            return
            
        # Extract data for plotting
        weeks = [tp.week for tp in time_points]
        means = [tp.mean for tp in time_points]
        ci_lower = [tp.ci_lower for tp in time_points]
        ci_upper = [tp.ci_upper for tp in time_points]
        n_patients = [tp.n_patients for tp in time_points]
        
        # Create figure with two y-axes
        fig, ax1 = plt.subplots(figsize=self.figsize)
        ax2 = ax1.twinx()
        
        # Plot mean acuity and CI on primary axis
        line = ax1.plot(weeks, means, 'b-', linewidth=2, label='Mean Acuity')
        ax1.fill_between(weeks, ci_lower, ci_upper, 
                        color='b', alpha=0.2, label='95% Confidence Interval')
        
        # Plot number of patients on secondary axis
        patient_line = ax2.plot(weeks, n_patients, 'r--', alpha=0.5, 
                              label='Number of Patients')
        
        # Customize primary axis (acuity)
        ax1.set_xlabel('Weeks Since Treatment Start')
        ax1.set_ylabel('Visual Acuity (ETDRS letters)')
        ax1.set_ylim(0, 85)
        
        # Customize secondary axis (patient count)
        ax2.set_ylabel('Number of Patients')
        ax2.set_ylim(0, max(n_patients) * 1.1)
        
        # Add grid aligned to primary axis
        ax1.grid(True, which='major', linestyle='-', alpha=0.3)
        ax1.grid(True, which='minor', linestyle=':', alpha=0.2)
        
        # Add month markers
        month_weeks = list(range(0, max(weeks) + 1, 4))  # Every 4 weeks
        ax1.set_xticks(month_weeks)
        ax1.set_xticklabels([f"{w//4:d}" if w % 12 == 0 else "" for w in month_weeks])
        ax1.set_xlabel("Months Since Treatment Start")
        
        # Add median follow-up annotation
        median_followup = self.analyzer.get_median_followup(patient_data)
        plt.figtext(0.99, 0.01, 
                   f"Median follow-up: {median_followup:.1f} weeks",
                   ha='right', va='bottom', 
                   fontsize=8, style='italic')
        
        # Combine legends from both axes
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, 
                  loc='upper right', bbox_to_anchor=(1, 1))
        
        plt.title(title)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def plot_patient_retention(self, patient_data: Dict[str, List[Dict]],
                             show: bool = True, save_path: Optional[str] = None,
                             title: str = "Patient Retention Over Time"):
        """Plot patient retention percentage over time.

        Parameters
        ----------
        patient_data : Dict[str, List[Dict]]
            Dictionary mapping patient IDs to lists of visit dictionaries.
            Each visit dict should contain:
            - 'date': datetime of visit
        show : bool, optional
            Whether to display the plot (default True)
        save_path : str, optional
            File path to save the plot (default None)
        title : str, optional
            Plot title (default "Patient Retention Over Time")

        Returns
        -------
        None
            Displays or saves plot but returns nothing

        Notes
        -----
        - Retention calculated as percentage of initial cohort
        - X-axis shows months since treatment start
        - Uses same patient data structure as plot_mean_acuity
        """
        # Analyze data
        time_points = self.analyzer.analyze_visual_acuity(patient_data)
        if not time_points:
            return
            
        # Extract patient counts
        weeks = [tp.week for tp in time_points]
        n_patients = [tp.n_patients for tp in time_points]
        
        # Calculate retention percentages
        initial_patients = n_patients[0] if n_patients else 0
        if initial_patients == 0:
            return
            
        retention = [n/initial_patients * 100 for n in n_patients]
        
        # Create plot
        plt.figure(figsize=self.figsize)
        plt.plot(weeks, retention, 'b-', linewidth=2)
        
        # Customize plot
        plt.xlabel('Weeks Since Treatment Start')
        plt.ylabel('Patient Retention (%)')
        plt.ylim(0, 100)
        
        # Add month markers
        month_weeks = list(range(0, max(weeks) + 1, 4))
        plt.xticks(month_weeks, 
                  [f"{w//4:d}" if w % 12 == 0 else "" for w in month_weeks])
        plt.xlabel("Months Since Treatment Start")
        
        # Add grid
        plt.grid(True, which='major', linestyle='-', alpha=0.3)
        plt.grid(True, which='minor', linestyle=':', alpha=0.2)
        
        plt.title(title)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
