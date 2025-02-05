from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from matplotlib.dates import DateFormatter
import seaborn as sns
from analysis.simulation_results import SimulationResults

class PopulationVisualizer:
    """Visualization tools for population-level analysis"""
    
    @staticmethod
    def plot_vision_distribution(results: SimulationResults,
                               time_points: Optional[List[datetime]] = None,
                               show: bool = True,
                               save_path: Optional[str] = None):
        """Plot vision distribution across population at different timepoints
        
        Args:
            results: SimulationResults object containing patient histories
            time_points: Optional list of timepoints to analyze (default: start, middle, end)
            show: Whether to display the plot
            save_path: Optional path to save the plot
        """
        if not time_points:
            # Default to start, middle, and end points
            total_days = (results.end_date - results.start_date).days
            time_points = [
                results.start_date,
                results.start_date + timedelta(days=total_days//2),
                results.end_date
            ]
            
        fig, axes = plt.subplots(1, len(time_points), figsize=(15, 5))
        if len(time_points) == 1:
            axes = [axes]
            
        for ax, time_point in zip(axes, time_points):
            # Get vision values near this time point (within 2 weeks)
            vision_values = []
            window = timedelta(weeks=2)
            
            for history in results.patient_histories.values():
                # Find closest vision measurement
                closest_vision = None
                min_diff = window
                
                for visit in history:
                    if 'vision' not in visit or 'date' not in visit:
                        continue
                    time_diff = abs(visit['date'] - time_point)
                    if time_diff < min_diff:
                        min_diff = time_diff
                        closest_vision = visit['vision']
                
                if closest_vision is not None:
                    vision_values.append(closest_vision)
            
            if vision_values:
                # Create violin plot
                sns.violinplot(data=vision_values, ax=ax)
                ax.set_title(f'Vision Distribution\n{time_point.strftime("%Y-%m-%d")}')
                ax.set_ylim(0, 85)
                ax.set_ylabel('Visual Acuity (ETDRS letters)')
            
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        if show:
            plt.show()
        else:
            plt.close()

    @staticmethod
    def plot_treatment_patterns(results: SimulationResults,
                              show: bool = True,
                              save_path: Optional[str] = None):
        """Plot treatment patterns across the population
        
        Shows:
        - Distribution of intervals between treatments
        - Treatment frequency over time
        - Loading phase completion rate
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Collect treatment intervals
        intervals = []
        monthly_treatments = {}
        
        for history in results.patient_histories.values():
            last_treatment = None
            
            for visit in history:
                if 'injection' not in visit.get('actions', []):
                    continue
                    
                # Record treatment date
                treatment_date = visit['date']
                month_key = treatment_date.strftime('%Y-%m')
                monthly_treatments[month_key] = monthly_treatments.get(month_key, 0) + 1
                
                # Calculate interval if not first treatment
                if last_treatment:
                    interval_weeks = (treatment_date - last_treatment).days / 7
                    intervals.append(interval_weeks)
                    
                last_treatment = treatment_date
        
        # Plot interval distribution
        if intervals:
            sns.histplot(intervals, bins=20, ax=ax1)
            ax1.set_title('Treatment Interval Distribution')
            ax1.set_xlabel('Weeks Between Treatments')
            ax1.set_ylabel('Frequency')
        
        # Plot monthly treatment frequency
        if monthly_treatments:
            months = sorted(monthly_treatments.keys())
            treatments = [monthly_treatments[m] for m in months]
            x_pos = np.arange(len(months))
            
            ax2.bar(x_pos, treatments)
            ax2.set_title('Monthly Treatment Frequency')
            ax2.set_xlabel('Month')
            ax2.set_ylabel('Number of Treatments')
            ax2.set_xticks(x_pos[::2])  # Show every other month
            ax2.set_xticklabels([m.split('-')[1] for m in months[::2]], rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        if show:
            plt.show()
        else:
            plt.close()

    @staticmethod
    def plot_response_categories(results: SimulationResults,
                               show: bool = True,
                               save_path: Optional[str] = None):
        """Plot distribution of treatment responses across population
        
        Categories:
        - Strong improvement (>15 letters)
        - Moderate improvement (5-15 letters)
        - Stable (±5 letters)
        - Decline (>5 letters loss)
        """
        # Calculate vision changes from baseline
        changes = []
        for history in results.patient_histories.values():
            baseline = next((v['vision'] for v in history if 'vision' in v), None)
            final = next((v['vision'] for v in reversed(history) if 'vision' in v), None)
            
            if baseline is not None and final is not None:
                changes.append(final - baseline)
        
        if not changes:
            return
            
        # Categorize changes
        categories = {
            'Strong improvement (>15)': len([c for c in changes if c > 15]),
            'Moderate improvement (5-15)': len([c for c in changes if 5 < c <= 15]),
            'Stable (±5)': len([c for c in changes if -5 <= c <= 5]),
            'Decline (>5)': len([c for c in changes if c < -5])
        }
        
        # Create pie chart
        plt.figure(figsize=(10, 8))
        colors = ['#2ecc71', '#3498db', '#f1c40f', '#e74c3c']
        
        plt.pie(categories.values(), labels=categories.keys(), colors=colors,
                autopct='%1.1f%%', startangle=90)
        plt.title('Distribution of Treatment Responses')
        
        if save_path:
            plt.savefig(save_path)
        if show:
            plt.show()
        else:
            plt.close()

    @staticmethod
    def create_population_summary(results: SimulationResults) -> Dict:
        """Create a comprehensive summary of population outcomes
        
        Returns dictionary with key statistics and metrics
        """
        summary = {
            'total_patients': len(results.patient_histories),
            'mean_visits': 0,
            'mean_treatments': 0,
            'mean_vision_change': 0,
            'vision_improved_percent': 0,
            'vision_stable_percent': 0,
            'vision_declined_percent': 0,
            'loading_phase_completion': 0,
            'mean_treatment_interval': 0
        }
        
        vision_changes = []
        treatment_counts = []
        visit_counts = []
        treatment_intervals = []
        loading_completions = 0
        
        for history in results.patient_histories.values():
            # Count visits and treatments
            visits = len(history)
            treatments = len([v for v in history if 'injection' in v.get('actions', [])])
            visit_counts.append(visits)
            treatment_counts.append(treatments)
            
            # Calculate vision change
            baseline = next((v['vision'] for v in history if 'vision' in v), None)
            final = next((v['vision'] for v in reversed(history) if 'vision' in v), None)
            if baseline is not None and final is not None:
                vision_changes.append(final - baseline)
            
            # Check loading phase completion (3 initial treatments)
            if treatments >= 3:
                loading_completions += 1
            
            # Calculate treatment intervals
            last_treatment = None
            for visit in history:
                if 'injection' not in visit.get('actions', []):
                    continue
                if last_treatment:
                    interval = (visit['date'] - last_treatment).days / 7
                    treatment_intervals.append(interval)
                last_treatment = visit['date']
        
        # Calculate summary statistics
        if vision_changes:
            summary['mean_vision_change'] = np.mean(vision_changes)
            total = len(vision_changes)
            summary['vision_improved_percent'] = len([c for c in vision_changes if c > 5]) / total * 100
            summary['vision_stable_percent'] = len([c for c in vision_changes if -5 <= c <= 5]) / total * 100
            summary['vision_declined_percent'] = len([c for c in vision_changes if c < -5]) / total * 100
        
        if treatment_intervals:
            summary['mean_treatment_interval'] = np.mean(treatment_intervals)
        
        if summary['total_patients'] > 0:
            summary['mean_visits'] = np.mean(visit_counts)
            summary['mean_treatments'] = np.mean(treatment_counts)
            summary['loading_phase_completion'] = loading_completions / summary['total_patients'] * 100
        
        return summary
