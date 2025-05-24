"""
Enhanced DES with staggered patient enrollment.

This module provides an implementation of the enhanced DES framework with
staggered patient enrollment, ensuring proper discontinuation handling and
maintaining compatibility with the enhanced framework's event structure.

Classes
-------
StaggeredEnhancedDES
    Enhanced DES implementation with staggered patient enrollment
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging
import numpy as np

from .config import SimulationConfig
from .enhanced_des import EnhancedDES, Event, EventHandler
from .patient_state import PatientState
from .patient_generator import PatientGenerator

# Configure logging
logger = logging.getLogger(__name__)

class StaggeredEnhancedDES(EnhancedDES):
    """
    Enhanced DES implementation with staggered patient enrollment.
    
    This class extends EnhancedDES to implement staggered patient enrollment
    with proper discontinuation handling. It ensures that patients arrive at
    realistic intervals and maintains tracking of both simulation time and
    patient-specific time.
    
    Parameters
    ----------
    config : SimulationConfig or str
        Simulation configuration or name of config to load
    environment : Optional[SimulationEnvironment], optional
        Shared simulation environment, by default None
    staggered_params : Optional[Dict[str, Any]], optional
        Additional parameters for staggered enrollment, by default None
    """
    
    def __init__(self, config, environment=None, staggered_params=None):
        """
        Initialize staggered enhanced DES with configuration.
        
        Parameters
        ----------
        config : SimulationConfig or str
            Simulation configuration or name of config to load
        environment : Optional[SimulationEnvironment], optional
            Shared simulation environment, by default None
        staggered_params : Optional[Dict[str, Any]], optional
            Additional parameters for staggered enrollment, by default None
        """
        # Initialize base class
        super().__init__(config, environment)
        
        # Initialize staggered enrollment parameters
        self.staggered_params = staggered_params or {}
        
        # Override patient generator with staggered parameters
        self._initialize_staggered_patient_generator()
        
        # Additional tracking for staggered enrollment
        self.enrollment_stats = {
            "enrolled_patients": 0,
            "enrollment_duration_days": 0,
            "average_patients_per_week": 0,
            "final_enrollment_date": None
        }
        
        # Track patient time vs. simulation time
        self.relative_time_tracking = self.staggered_params.get("relative_time_tracking", True)
    
    def _initialize_staggered_patient_generator(self):
        """
        Initialize patient generator with staggered parameters.
        
        This method configures the patient generator to use staggered enrollment
        based on the provided parameters or configuration.
        """
        # Get staggered enrollment parameters
        enrollment_duration = self.staggered_params.get("enrollment_duration_days")
        if enrollment_duration is None:
            # Default to half of simulation duration if not specified
            enrollment_duration = self.config.duration_days / 2
        
        # Get patient arrival rate
        rate_per_week = self.staggered_params.get("rate_per_week")
        if rate_per_week is None:
            # Calculate based on number of patients and enrollment duration
            total_weeks = enrollment_duration / 7
            rate_per_week = self.config.num_patients / total_weeks
        
        # Update patient generator with staggered parameters
        des_params = self.config.get_des_params()
        patient_gen_params = des_params.get("patient_generation", {})
        
        # Override with staggered parameters
        patient_gen_params["rate_per_week"] = rate_per_week
        
        # Create patient generator
        self.patient_generator = PatientGenerator(
            rate_per_week=rate_per_week,
            start_date=self.config.start_date,
            end_date=self.config.start_date + timedelta(days=enrollment_duration),
            random_seed=patient_gen_params.get("random_seed") or self.config.random_seed
        )
        
        # Update enrollment stats
        self.enrollment_stats["enrollment_duration_days"] = enrollment_duration
        self.enrollment_stats["average_patients_per_week"] = rate_per_week
    
    def run(self, until=None):
        """
        Run the simulation with staggered enrollment until the end date.
        
        Parameters
        ----------
        until : Optional[datetime], optional
            End date for the simulation, by default None (uses config end date)
            
        Returns
        -------
        Dict[str, Any]
            Simulation results including patient histories and statistics
        """
        logger.info("Running staggered enhanced DES simulation...")
        
        # Set end date if not provided
        if until is None:
            until = self.config.start_date + timedelta(days=self.config.duration_days)
        
        # Run simulation
        results = super().run(until)
        
        # Add staggered enrollment statistics to results
        self.enrollment_stats["enrolled_patients"] = len(self.patients)
        
        # Find final enrollment date
        if self.patients:
            enrollment_dates = [patient.start_time for patient in self.patients.values()]
            self.enrollment_stats["final_enrollment_date"] = max(enrollment_dates)
        
        # Add to results
        combined_stats = {
            **results.get("statistics", {}),
            "enrollment": self.enrollment_stats
        }
        
        # Update results with enrollment stats
        results["statistics"] = combined_stats
        
        return results
    
    def _schedule_patient_arrivals(self):
        """
        Schedule patient arrival events with staggered enrollment.
        
        Uses Poisson process to generate realistic arrival times.
        Creates 'add_patient' events for each arrival.
        """
        # Get arrival times from patient generator
        arrival_times = self.patient_generator.generate_arrival_times()
        
        # Count enrolled patients for stats
        self.enrollment_stats["enrolled_patients"] = len(arrival_times)
        
        # Schedule events for each arrival
        for arrival_time, patient_num in arrival_times:
            patient_id = f"PATIENT{patient_num:03d}"
            
            # Get protocol type from config 
            protocol_type = self.config.parameters.get("protocol_type", "treat_and_extend")
            
            # Schedule add_patient event
            self.clock.schedule_event(Event(
                time=arrival_time,
                event_type="add_patient",
                patient_id=patient_id,
                data={
                    "protocol_name": protocol_type,
                    "enrollment_date": arrival_time
                },
                priority=1
            ))
            
            # Update final enrollment date for stats
            if self.enrollment_stats.get("final_enrollment_date") is None or arrival_time > self.enrollment_stats["final_enrollment_date"]:
                self.enrollment_stats["final_enrollment_date"] = arrival_time
    
    def _handle_add_patient(self, event: Event):
        """
        Handle patient addition with staggered enrollment.
        
        This method extends the base _handle_add_patient to track
        patient-specific time relative to enrollment date.
        
        Parameters
        ----------
        event : Event
            Patient addition event
        """
        # Store enrollment date
        enrollment_date = event.data.get("enrollment_date", event.time)
        
        # Call base implementation
        super()._handle_add_patient(event)
        
        # Update patient with enrollment date
        patient = self.patients.get(event.patient_id)
        if patient:
            # Add enrollment tracking data
            patient.state["enrollment_date"] = enrollment_date
            patient.state["time_since_enrollment"] = timedelta(0)
    
    def _get_patient_relative_time(self, patient_id: str, sim_time: datetime) -> timedelta:
        """
        Calculate patient-specific time relative to enrollment date.
        
        Parameters
        ----------
        patient_id : str
            Patient ID
        sim_time : datetime
            Current simulation time
            
        Returns
        -------
        timedelta
            Time since patient enrollment
        """
        if not self.relative_time_tracking:
            return timedelta(0)
            
        patient = self.patients.get(patient_id)
        if not patient:
            return timedelta(0)
            
        enrollment_date = patient.state.get("enrollment_date")
        if not enrollment_date:
            return timedelta(0)
            
        return sim_time - enrollment_date
    
    def process_event(self, event: Event):
        """
        Process event with staggered enrollment time tracking.
        
        Updates patient-specific time tracking before processing the event.
        
        Parameters
        ----------
        event : Event
            Event to process
        """
        # Update patient relative time
        if event.patient_id and event.patient_id in self.patients:
            relative_time = self._get_patient_relative_time(event.patient_id, event.time)
            self.patients[event.patient_id].state["time_since_enrollment"] = relative_time
        
        # Process event using standard handler
        super().process_event(event)
    
    def _get_patient_histories(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get patient histories with relative time information.
        
        Overrides the base method to include relative time in patient histories
        for analysis.
        
        Returns
        -------
        Dict[str, List[Dict[str, Any]]]
            Dictionary of patient histories with relative time
        """
        # Get base histories
        histories = super()._get_patient_histories()
        
        # Add relative time information if enabled
        if self.relative_time_tracking:
            for patient_id, visits in histories.items():
                patient = self.patients.get(patient_id)
                if not patient:
                    continue
                    
                enrollment_date = patient.state.get("enrollment_date")
                if not enrollment_date:
                    continue
                    
                # Add relative time to each visit
                for visit in visits:
                    visit_date = visit.get("date")
                    if visit_date:
                        time_since_enrollment = visit_date - enrollment_date
                        visit["time_since_enrollment"] = time_since_enrollment.days
        
        return histories