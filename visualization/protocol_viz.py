from typing import Dict, List
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from simulation.abs import Patient

class ProtocolVisualizer:
    """Visualization tools for treatment protocols and patient timelines"""
    
    @staticmethod
    def plot_patient_timeline(patient: Patient, start_date: datetime = None, end_date: datetime = None):
        """
        Create a timeline visualization of a patient's treatment history
        
        Args:
            patient: Patient object containing treatment history
            start_date: Optional start date for timeline
            end_date: Optional end date for timeline
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
    def plot_vision_changes(patient: Patient):
        """Plot vision changes over time for a patient"""
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
