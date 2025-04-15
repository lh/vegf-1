"""Visualization tools for treatment protocols and patient outcomes.

This module provides matplotlib-based visualizations for:
- Patient treatment timelines showing visits and procedures
- Vision changes over time relative to baseline
- Protocol adherence patterns
"""
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from simulation.abs import Patient

class ProtocolVisualizer:
    """Static methods for visualizing patient treatment data.
    
    Provides visualization tools for analyzing treatment patterns and outcomes.
    All methods are static since they operate on patient data without state.
    """
    
    @staticmethod
    def plot_patient_timeline(patient: Patient, 
                            start_date: Optional[datetime] = None, 
                            end_date: Optional[datetime] = None) -> plt.Figure:
        """Create a matplotlib timeline visualization of treatment history.

        Parameters
        ----------
        patient : Patient
            Patient object containing treatment history in patient.history
        start_date : datetime, optional
            Start date for timeline (default: first event date)
        end_date : datetime, optional  
            End date for timeline (default: last event date)

        Returns
        -------
        plt.Figure
            Matplotlib figure object containing the timeline plot

        Raises
        ------
        ValueError
            If patient has no recorded history

        Examples
        --------
        >>> fig = ProtocolVisualizer.plot_patient_timeline(patient)
        >>> fig.savefig('patient_timeline.png')

        Notes
        -----
        The timeline shows different event types with distinct markers:
        - Red triangle: Injections
        - Blue circle: Vision tests  
        - Green square: OCT scans
        - Black x: Unknown/other events
        """
        if not patient.history:
            raise ValueError("Patient has no recorded history")
            
        # Set up the plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Extract events from patient history
        dates = []
        events = []
        for event in patient.history:
            event_date = event.get("date")
            if not event_date:
                continue
                
            if start_date and event_date < start_date:
                continue
            if end_date and event_date > end_date:
                continue
                
            dates.append(event_date)
            events.append(event.get("type", "unknown"))
        
        # Create event markers
        markers = {
            "injection": "r^",  # Red triangle for injections
            "vision_test": "bo",  # Blue circle for vision tests
            "oct_scan": "gs",  # Green square for OCT scans
        }
        
        # Plot events
        for date, event_type in zip(dates, events):
            marker = markers.get(event_type, "kx")  # Default to black x
            ax.plot(date, 1, marker, markersize=10, label=event_type)
        
        # Customize plot
        ax.yaxis.set_visible(False)  # Hide Y axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
        # Remove duplicate labels
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys())
        
        plt.title(f"Treatment Timeline for Patient {patient.patient_id}")
        plt.tight_layout()
        return fig

    @staticmethod
    def plot_vision_changes(patient: Patient) -> plt.Figure:
        """Plot vision changes over time with baseline reference.

        Parameters
        ----------
        patient : Patient
            Patient object containing vision records in patient.history

        Returns
        -------
        plt.Figure
            Matplotlib figure object containing the vision plot

        Raises
        ------
        ValueError
            If no vision records found in patient history

        Examples
        --------
        >>> fig = ProtocolVisualizer.plot_vision_changes(patient)
        >>> fig.savefig('vision_changes.png')

        Notes
        -----
        The plot includes:
        - Vision measurements over time (blue line)
        - Baseline vision (green dashed line)
        - Treatment stop threshold (red dashed line)
        """
        vision_records = [(event["date"], event["vision"]) 
                         for event in patient.history 
                         if "vision" in event]
        
        if not vision_records:
            raise ValueError("No vision records found")
            
        dates, vision_values = zip(*vision_records)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(dates, vision_values, 'b-o')
        
        # Add baseline reference if available
        if patient.state["baseline_vision"] is not None:
            ax.axhline(y=patient.state["baseline_vision"], 
                      color='g', linestyle='--', 
                      label='Baseline')
            ax.axhline(y=patient.state["baseline_vision"] - 15, 
                      color='r', linestyle='--', 
                      label='Treatment Stop Threshold')
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Vision (ETDRS letters)')
        ax.set_title(f'Vision Changes - Patient {patient.patient_id}')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        return fig
