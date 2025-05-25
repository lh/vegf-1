"""
Staggered treat-and-extend DES implementation with enhanced framework.

This module provides an integrated implementation of the staggered treat-and-extend
protocol using the enhanced DES framework with proper discontinuation handling.
It combines realistic patient enrollment patterns with the treat-and-extend
protocol logic and discontinuation handling.

Classes
-------
StaggeredTreatAndExtendDES
    Integrated implementation of staggered treat-and-extend protocol
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging
import numpy as np
import pandas as pd

from simulation.config import SimulationConfig
from simulation.staggered_enhanced_des import StaggeredEnhancedDES, Event
from enhanced_treat_and_extend_des import EnhancedTreatAndExtendDES
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
from simulation.vision_models import create_vision_model
from simulation.clinician import ClinicianManager

# Configure logging
logger = logging.getLogger(__name__)

class StaggeredTreatAndExtendDES(EnhancedTreatAndExtendDES, StaggeredEnhancedDES):
    """
    Staggered treat-and-extend DES implementation with enhanced framework.
    
    This class combines the EnhancedTreatAndExtendDES and StaggeredEnhancedDES
    classes to provide a complete implementation of the staggered treat-and-extend
    protocol with proper discontinuation handling.
    
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
        Initialize staggered treat-and-extend DES with configuration.
        
        Parameters
        ----------
        config : SimulationConfig or str
            Simulation configuration or name of config to load
        environment : Optional[SimulationEnvironment], optional
            Shared simulation environment, by default None
        staggered_params : Optional[Dict[str, Any]], optional
            Additional parameters for staggered enrollment, by default None
        """
        # Handle different types of config parameter
        if isinstance(config, str):
            config = SimulationConfig.from_yaml(config)
        
        # Initialize base classes
        # Note: we call StaggeredEnhancedDES.__init__ instead of super().__init__
        # to avoid calling EnhancedDES.__init__ twice (diamond inheritance)
        StaggeredEnhancedDES.__init__(self, config, environment, staggered_params)
        
        # Initialize vision model
        vision_model_type = self.config.parameters.get('vision_model_type', 'realistic')
        self.vision_model = create_vision_model(vision_model_type, self.config)
        
        # Initialize clinician manager
        clinician_config = self.config.parameters.get("clinicians", {})
        clinician_enabled = clinician_config.get("enabled", False)
        self.clinician_manager = ClinicianManager(self.config.parameters, enabled=clinician_enabled)
        
        # Initialize discontinuation manager
        self._initialize_discontinuation_manager()
        
        # Additional statistics
        self.stats = {
            "protocol_completions": 0,
            "protocol_discontinuations": 0,
            "monitoring_visits": 0,
            "retreatments": 0,
            "clinician_decisions": {
                "protocol_followed": 0,
                "protocol_overridden": 0
            }
        }
        
        # Track discontinued patients and retreated patients
        self.discontinued_patients = set()
        self.retreated_patients = set()
        
        # Register custom event handlers for staggered treat-and-extend
        self.register_event_handler("visit", self._handle_visit)
        self.register_event_handler("treatment_decision", self._handle_treatment_decision)
        # Note: We don't override _handle_add_patient as the staggered version already extends it
    
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
        print("Running staggered treat-and-extend enhanced DES simulation...")
        
        # Set end date if not provided
        if until is None:
            until = self.config.start_date + timedelta(days=self.config.duration_days)
        
        # Run simulation using StaggeredEnhancedDES run method
        # This ensures we get the staggered enrollment statistics
        results = StaggeredEnhancedDES.run(self, until)
        
        # Add protocol-specific statistics to results
        combined_stats = {**results.get("statistics", {}), **self.stats}
        
        # Print statistics
        self._print_statistics(combined_stats, results.get("patient_histories", {}))
        
        # Return enhanced results
        return {
            "patient_histories": results.get("patient_histories", {}),
            "statistics": combined_stats,
            "discontinuation_stats": self.discontinuation_manager.get_statistics(),
            "enrollment_stats": self.enrollment_stats
        }
    
    def process_event(self, event: Event):
        """
        Process event with staggered enrollment time tracking.
        
        Updates patient-specific time tracking before processing the event.
        
        Parameters
        ----------
        event : Event
            Event to process
        """
        # Update patient relative time (from StaggeredEnhancedDES)
        if event.patient_id and event.patient_id in self.patients:
            relative_time = self._get_patient_relative_time(event.patient_id, event.time)
            self.patients[event.patient_id].state["time_since_enrollment"] = relative_time
        
        # Process event using event handler registry (from EnhancedDES)
        event_type = event.event_type
        
        if event_type in self.event_handlers:
            self.event_handlers[event_type](event)
        else:
            logger.warning(f"No handler registered for event type: {event_type}")
    
    def _handle_treatment_decision(self, event: Event):
        """
        Handle treatment decision event with staggered time tracking.
        
        This implementation extends the treat-and-extend version to include
        patient-specific time tracking for staggered enrollment.
        
        Parameters
        ----------
        event : Event
            Treatment decision event
        """
        # Standard treatment decision handling from EnhancedTreatAndExtendDES
        # is sufficient, but we need to ensure scheduling uses patient-specific time
        super()._handle_treatment_decision(event)
        
        # Additional time tracking for staggered enrollment
        patient_id = event.patient_id
        patient = self.patients.get(patient_id)
        
        if patient and self.relative_time_tracking:
            # Update patient-specific time tracking
            enrollment_date = patient.state.get("enrollment_date")
            if enrollment_date:
                time_since_enrollment = event.time - enrollment_date
                patient.state["time_since_enrollment"] = time_since_enrollment
                
                # Add relative time to most recent visit record
                if "visit_history" in patient.state and patient.state["visit_history"]:
                    latest_visit = patient.state["visit_history"][-1]
                    latest_visit["time_since_enrollment"] = time_since_enrollment.days

# Entry point function for running the staggered integrated implementation
def run_staggered_treat_and_extend_des(config="eylea_literature_based", verbose=False, staggered_params=None):
    """
    Run a simulation with the staggered treat-and-extend DES implementation.
    
    Parameters
    ----------
    config : str or SimulationConfig, optional
        Name of the configuration file or configuration object, by default "eylea_literature_based"
    verbose : bool, optional
        Whether to print verbose output, by default False
    staggered_params : Optional[Dict[str, Any]], optional
        Additional parameters for staggered enrollment, by default None
        
    Returns
    -------
    Dict[str, Any]
        Simulation results including patient histories and statistics
    """
    # Default staggered parameters if none provided
    if staggered_params is None:
        staggered_params = {
            "enrollment_duration_days": 90,  # 3 months enrollment
            "relative_time_tracking": True   # Track patient-specific time
        }
    
    # Create and run simulation
    print(f"Running staggered treat-and-extend DES simulation with config: {config}")
    sim = StaggeredTreatAndExtendDES(config, staggered_params=staggered_params)
    results = sim.run()
    
    # Extract patient histories and format results
    patient_histories = results.get("patient_histories", {})
    enrollment_stats = results.get("enrollment_stats", {})
    
    # Print enrollment statistics if verbose
    if verbose:
        print("\nEnrollment Statistics:")
        print("-" * 20)
        for key, value in enrollment_stats.items():
            print(f"{key}: {value}")
        
        # Convert patient histories to DataFrame for analysis
        all_data = []
        for patient_id, visits in patient_histories.items():
            for visit in visits:
                # Extract key data from visit
                visit_data = {
                    'patient_id': patient_id,
                    'date': visit.get('date', ''),
                    'time_since_enrollment': visit.get('time_since_enrollment', 0),
                    'vision': visit.get('vision', None),
                    'baseline_vision': visit.get('baseline_vision', None),
                    'phase': visit.get('phase', ''),
                    'type': visit.get('type', ''),
                    'actions': str(visit.get('actions', [])),
                    'disease_state': str(visit.get('disease_state', '')),
                    'treatment_status': str(visit.get('treatment_status', {}))
                }
                all_data.append(visit_data)
        
        # Create DataFrame
        df = pd.DataFrame(all_data)
        
        # Save all data to CSV
        df.to_csv('staggered_treat_and_extend_des_data.csv', index=False)
        print(f"Saved data for {len(patient_histories)} patients to staggered_treat_and_extend_des_data.csv")
        
        # Sample a few patients to check their visit patterns
        sample_patients = np.random.choice(list(patient_histories.keys()), min(3, len(patient_histories)))
        
        for patient_id in sample_patients:
            patient_data = [visit for visit in patient_histories[patient_id]]
            patient_data.sort(key=lambda v: v['date'])
            
            print(f"\nPatient {patient_id} visits:")
            for visit in patient_data:
                time_since_enrollment = visit.get('time_since_enrollment', '?')
                print(f"  {visit['date']} (Day {time_since_enrollment}) - Phase: {visit['phase']} - Actions: {visit['actions']}")
    
    return results

if __name__ == "__main__":
    run_staggered_treat_and_extend_des(verbose=True)