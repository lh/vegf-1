from datetime import datetime
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import numpy as np
from analysis.patient_outcomes import PatientOutcomeAnalyzer, TimePoint

class OutcomeVisualizer:
    """Visualizes patient outcome data with statistical analysis"""
    
    def __init__(self, figsize=(12, 6)):
        """Initialize visualizer
        
        Args:
            figsize: Figure size in inches (width, height)
        """
        self.figsize = figsize
        self.analyzer = PatientOutcomeAnalyzer()
    
    def plot_mean_acuity(self, patient_data: Dict[str, List[Dict]], 
                        show: bool = True, save_path: Optional[str] = None,
                        title: str = "Mean Visual Acuity Over Time"):
        """Create a plot showing mean acuity with confidence intervals over time
        
        Args:
            patient_data: Dictionary of patient IDs to their visit histories
            show: Whether to display the plot
            save_path: Optional path to save the plot
            title: Title for the plot
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
        """Create a plot showing patient retention over time
        
        Args:
            patient_data: Dictionary of patient IDs to their visit histories
            show: Whether to display the plot
            save_path: Optional path to save the plot
            title: Title for the plot
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
