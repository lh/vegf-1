"""
Enhanced treat-and-extend DES implementation with integrated core components.

This module provides an integrated implementation of the treat-and-extend protocol
using the enhanced DES framework. It combines the flexibility of configuration-driven
parameters with the robustness of standardized event handling, while maintaining
the protocol-specific behavior of the original implementation.

Classes
-------
EnhancedTreatAndExtendDES
    Integrated implementation of treat-and-extend protocol using enhanced DES framework
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging
import numpy as np
import pandas as pd

from simulation.config import SimulationConfig
from simulation.enhanced_des import EnhancedDES, Event, EventHandler
from simulation.patient_state import PatientState
from simulation.clinical_model import ClinicalModel
from simulation.vision_models import create_vision_model
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
from simulation.clinician import ClinicianManager

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedTreatAndExtendDES(EnhancedDES):
    """
    Enhanced treat-and-extend DES implementation with integrated core components.
    
    This class extends the EnhancedDES framework with protocol-specific behavior
    for the treat-and-extend protocol. It maintains compatibility with the original
    implementation while leveraging the enhanced framework's capabilities.
    
    Parameters
    ----------
    config : SimulationConfig or str
        Simulation configuration or name of config to load
    environment : Optional[SimulationEnvironment], optional
        Shared simulation environment, by default None
    """
    
    def __init__(self, config, environment=None):
        """
        Initialize the enhanced treat-and-extend DES with configuration.
        
        Parameters
        ----------
        config : SimulationConfig or str
            Simulation configuration or name of config to load
        environment : Optional[SimulationEnvironment], optional
            Shared simulation environment, by default None
        """
        # Handle different types of config parameter
        if isinstance(config, str):
            config = SimulationConfig.from_yaml(config)
        
        # Initialize base class
        super().__init__(config, environment)
        
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
        
        # Register protocol-specific event handlers
        self.register_event_handler("visit", self._handle_visit)
        self.register_event_handler("treatment_decision", self._handle_treatment_decision)
        self.register_event_handler("add_patient", self._handle_add_patient)
    
    def _initialize_discontinuation_manager(self):
        """
        Initialize the discontinuation manager.
        
        Uses the configuration to determine discontinuation parameters and
        initializes the enhanced discontinuation manager.
        """
        # Get the parameter file path from the config
        discontinuation_config = self.config.parameters.get("discontinuation", {})
        parameter_file = discontinuation_config.get("parameter_file", "")
        
        if parameter_file:
            try:
                # Directly load the discontinuation parameters from the file
                with open(parameter_file, 'r') as f:
                    import yaml
                    discontinuation_params = yaml.safe_load(f)
                    self.discontinuation_manager = EnhancedDiscontinuationManager(discontinuation_params)
            except Exception as e:
                logger.error(f"Error loading discontinuation parameters: {str(e)}")
                # Fall back to empty dict with enabled=True
                self.discontinuation_manager = EnhancedDiscontinuationManager({"discontinuation": {"enabled": True}})
        else:
            # If no parameter file specified, use the discontinuation config from the parameters
            self.discontinuation_manager = EnhancedDiscontinuationManager({"discontinuation": {"enabled": True}})
    
    def run(self, until=None):
        """
        Run the simulation until the end date.
        
        Parameters
        ----------
        until : Optional[datetime], optional
            End date for the simulation, by default None (uses config end date)
            
        Returns
        -------
        Dict[str, Any]
            Simulation results including patient histories and statistics
        """
        print("Initializing enhanced treat-and-extend DES simulation...")
        
        # Set end date if not provided
        if until is None:
            until = self.config.start_date + timedelta(days=self.config.duration_days)
        
        # Run simulation using base class
        results = super().run(until)
        
        # Add protocol-specific statistics to results
        combined_stats = {**results.get("statistics", {}), **self.stats}
        
        # Print statistics
        self._print_statistics(combined_stats, results.get("patient_histories", {}))
        
        # Return enhanced results
        return {
            "patient_histories": results.get("patient_histories", {}),
            "statistics": combined_stats,
            "discontinuation_stats": self.discontinuation_manager.get_statistics()
        }
    
    def _handle_add_patient(self, event: Event):
        """
        Handle patient addition event.
        
        Parameters
        ----------
        event : Event
            Patient addition event
        """
        patient_id = event.patient_id
        
        # Get vision parameters from config
        vision_params = self.config.get_vision_params()
        initial_vision = vision_params.get("baseline_mean", 65)
        
        # Add randomness to initial vision
        if vision_params.get("baseline_std"):
            initial_vision = np.random.normal(
                initial_vision, 
                vision_params.get("baseline_std", 10)
            )
            # Clamp vision between 0-85 ETDRS letters
            initial_vision = min(max(initial_vision, 0), 85)
        
        # Get protocol parameters from config
        protocol_name = event.data.get("protocol_name", "treat_and_extend")
        protocol_config = self.config.parameters.get("protocols", {}).get(protocol_name, {})
        protocol_phases = protocol_config.get("treatment_phases", {})
        
        # Get loading phase parameters
        loading_phase = protocol_phases.get("initial_loading", {})
        loading_rules = loading_phase.get("rules", {})
        
        # Get interval settings with fallbacks
        loading_interval_weeks = loading_rules.get("interval_weeks", 4)  # Use 4 weeks as fallback
        
        # Create patient state with protocol information
        patient = PatientState(
            patient_id=patient_id,
            protocol_name=protocol_name,
            initial_vision=initial_vision,
            start_time=event.time
        )
        
        # Initialize additional state for treat-and-extend protocol
        patient.state.update({
            "current_phase": "loading",
            "treatments_in_phase": 0,
            "next_visit_interval": loading_interval_weeks,
            "disease_activity": {
                "fluid_detected": True,
                "consecutive_stable_visits": 0,
                "max_interval_reached": False,
                "current_interval": loading_interval_weeks
            },
            "treatment_status": {
                "active": True,
                "recurrence_detected": False,
                "weeks_since_discontinuation": 0,
                "cessation_type": None,
                "discontinuation_date": None
            },
            "disease_characteristics": {
                "has_PED": np.random.random() < 0.3,  # 30% of patients have PED
            },
            "visit_history": [],
            "treatment_start": event.time,
            "protocol": protocol_name  # Store protocol name for later reference
        })
        
        # Add patient to simulation
        self.patients[patient_id] = patient
        
        # Schedule initial visit
        initial_visit_data = {
            "visit_type": "injection_visit",
            "actions": ["vision_test", "oct_scan", "injection"],
            "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
        }
        
        self.clock.schedule_event(Event(
            time=event.time,
            event_type="visit",
            patient_id=patient_id,
            data=initial_visit_data,
            priority=1
        ))
    
    def _handle_visit(self, event: Event):
        """
        Handle patient visit event.
        
        Parameters
        ----------
        event : Event
            Visit event
        """
        patient_id = event.patient_id
        
        if patient_id not in self.patients:
            logger.warning(f"Visit event for unknown patient: {patient_id}")
            return
            
        patient = self.patients[patient_id]
        
        # Get assigned clinician
        clinician_id = self.clinician_manager.assign_clinician(patient_id, event.time)
        clinician = self.clinician_manager.get_clinician(clinician_id)
        
        # Check if this is a monitoring visit
        is_monitoring = event.data.get("is_monitoring", False)
        
        # Update statistics
        self.global_stats["total_visits"] += 1
        if is_monitoring:
            self.stats["monitoring_visits"] += 1
        
        # Extract actions
        actions = event.data.get("actions", [])
        
        # Update global stats for actions
        if "injection" in actions:
            self.global_stats["total_injections"] += 1
        if "oct_scan" in actions:
            self.global_stats["total_oct_scans"] += 1
        
        # Handle monitoring visit differently
        if is_monitoring and not patient.state["treatment_status"]["active"]:
            # Update fluid detection based on OCT scan
            if "oct_scan" in actions:
                # Create state dictionary for vision model
                state = {
                    "patient_id": patient_id,
                    "fluid_detected": patient.state["disease_activity"]["fluid_detected"],
                    "treatments_in_phase": 0,  # Not in treatment phase
                    "interval": 0,  # Not relevant for monitoring visits
                    "current_vision": patient.state.get("current_vision", patient.state.get("vision", {}).get("current_va", 0)),
                }
                
                # Use vision model to determine fluid status
                # Use 0 for vision change as we're only interested in fluid detection
                _, fluid_detected = self.vision_model.calculate_vision_change(
                    state=state,
                    actions=actions,
                    phase="monitoring"
                )
                
                # Update patient's disease activity with new fluid status
                patient.state["disease_activity"]["fluid_detected"] = fluid_detected
            
            # Evaluate retreatment using the discontinuation manager
            result = self.discontinuation_manager.evaluate_retreatment(
                patient_state=patient.state,
                patient_id=patient_id,
                clinician=clinician
            )
            
            # Handle different return types
            if isinstance(result, tuple) and len(result) >= 2:
                should_retreat, probability = result
            elif hasattr(result, 'should_retreat'):
                # RetreatmentDecision object
                should_retreat = result.should_retreat
                probability = result.probability
            else:
                # Unexpected return type, default to no retreatment
                logger.warning(f"Unexpected return type from evaluate_retreatment: {type(result)}")
                should_retreat = False
                probability = 0.0
            
            # Record monitoring visit
            visit_record = {
                'date': event.time,
                'actions': actions,
                'vision': patient.state.get("current_vision", patient.state.get("vision", {}).get("current_va", 0)),
                'baseline_vision': patient.state.get("baseline_vision", patient.initial_vision),
                'phase': "monitoring",
                'type': 'monitoring_visit',
                'disease_state': 'stable' if not patient.state["disease_activity"]["fluid_detected"] else 'active',
                'treatment_status': patient.state["treatment_status"].copy(),
                'clinician_id': clinician_id,
                'fluid_detected': patient.state["disease_activity"]["fluid_detected"]
            }
            patient.state["visit_history"].append(visit_record)
            
            # If retreatment is recommended, restart treatment
            if should_retreat:
                # Update statistics
                if patient_id not in self.retreated_patients:
                    self.stats["retreatments"] += 1
                    self.retreated_patients.add(patient_id)
                
                # Update patient state
                patient.state["treatment_status"]["active"] = True
                patient.state["treatment_status"]["recurrence_detected"] = True
                patient.state["current_phase"] = "loading"  # Restart with loading phase
                patient.state["treatments_in_phase"] = 0
                
                # Get loading phase parameters
                protocol_name = patient.state.get("protocol", "treat_and_extend")
                protocol_config = self.config.parameters.get("protocols", {}).get(protocol_name, {})
                protocol_phases = protocol_config.get("treatment_phases", {})
                loading_phase = protocol_phases.get("initial_loading", {})
                loading_rules = loading_phase.get("rules", {})
                loading_interval_weeks = loading_rules.get("interval_weeks", 4)  # Use 4 weeks as fallback
                
                patient.state["next_visit_interval"] = loading_interval_weeks
                patient.state["disease_activity"]["current_interval"] = loading_interval_weeks
                
                # Register the retreatment with the manager
                self.discontinuation_manager.register_retreatment(patient_id)
                
                # Schedule next treatment visit
                next_visit_time = event.time + timedelta(weeks=loading_interval_weeks)
                self.clock.schedule_event(Event(
                    time=next_visit_time,
                    event_type="visit",
                    patient_id=patient_id,
                    data={
                        "visit_type": "injection_visit",
                        "actions": ["vision_test", "oct_scan", "injection"]
                    },
                    priority=1
                ))
            
            return
        
        # Regular visit processing
        
        # Get current vision
        baseline_vision = patient.state.get("current_vision", patient.state.get("vision", {}).get("current_va", patient.initial_vision))
        
        # Create state dictionary for vision model
        state = {
            "fluid_detected": patient.state["disease_activity"]["fluid_detected"],
            "treatments_in_phase": patient.state["treatments_in_phase"],
            "interval": patient.state["disease_activity"]["current_interval"],
            "current_vision": baseline_vision,
            "treatment_status": patient.state["treatment_status"]
        }
        
        # Calculate vision change using vision model
        vision_change, fluid_detected = self.vision_model.calculate_vision_change(
            state=state,
            actions=actions,
            phase=patient.state["current_phase"]
        )
        
        # Update vision
        new_vision = min(max(baseline_vision + vision_change, 0), 85)
        patient.state["current_vision"] = new_vision
        
        # Update vision statistics
        if new_vision > baseline_vision:
            self.global_stats["vision_improvements"] += 1
        elif new_vision < baseline_vision:
            self.global_stats["vision_declines"] += 1
        
        # Update disease activity
        patient.state["disease_activity"]["fluid_detected"] = fluid_detected
        
        # Record visit
        visit_record = {
            'date': event.time,
            'actions': actions,
            'vision': new_vision,
            'baseline_vision': baseline_vision,
            'phase': patient.state["current_phase"],
            'type': 'regular_visit',
            'disease_state': 'stable' if not fluid_detected else 'active',
            'treatment_status': patient.state["treatment_status"].copy(),
            'clinician_id': clinician_id
        }
        patient.state["visit_history"].append(visit_record)
        
        # Schedule treatment decision for same day
        self.clock.schedule_event(Event(
            time=event.time,
            event_type="treatment_decision",
            patient_id=patient_id,
            data={
                "decision_type": "doctor_treatment_decision", 
                "visit_data": {
                    "new_vision": new_vision,
                    "baseline_vision": baseline_vision,
                    "fluid_detected": fluid_detected
                }
            },
            priority=2
        ))
    
    def _handle_treatment_decision(self, event: Event):
        """
        Handle treatment decision event.
        
        Parameters
        ----------
        event : Event
            Treatment decision event
        """
        patient_id = event.patient_id
        
        if patient_id not in self.patients:
            logger.warning(f"Treatment decision for unknown patient: {patient_id}")
            return
            
        patient = self.patients[patient_id]
        
        # Get clinician for this decision
        clinician_id = self.clinician_manager.assign_clinician(patient_id, event.time)
        clinician = self.clinician_manager.get_clinician(clinician_id)
        
        # Get protocol parameters from config
        protocol_name = patient.state.get("protocol", "treat_and_extend")
        protocol_config = self.config.parameters.get("protocols", {}).get(protocol_name, {})
        protocol_phases = protocol_config.get("treatment_phases", {})
        
        # Get phase parameters
        phase = patient.state.get("current_phase", "loading")
        treatments_in_phase = patient.state.get("treatments_in_phase", 0) + 1
        patient.state["treatments_in_phase"] = treatments_in_phase
        
        # Update treatment intervals based on phase
        disease_activity = patient.state.get("disease_activity", {})
        fluid_detected = disease_activity.get("fluid_detected", True)
        
        # Get loading phase parameters
        loading_phase = protocol_phases.get("initial_loading", {})
        loading_rules = loading_phase.get("rules", {})
        loading_interval_weeks = loading_rules.get("interval_weeks", 4)  # Use 4 weeks as fallback
        injections_required = loading_rules.get("injections_required", 3)  # Use 3 as fallback
        
        # Get maintenance phase parameters
        maintenance_phase = protocol_phases.get("maintenance", {})
        maintenance_rules = maintenance_phase.get("rules", {})
        initial_interval_weeks = maintenance_rules.get("initial_interval_weeks", 8)  # Use 8 weeks as fallback
        max_interval_weeks = maintenance_rules.get("max_interval_weeks", 16)  # Use 16 weeks as fallback
        extension_step = maintenance_rules.get("extension_step", 2)  # Use 2 weeks as fallback
        reduction_step = maintenance_rules.get("reduction_step", 2)  # Use 2 weeks as fallback
        
        if phase == "loading":
            # Fixed intervals during loading, from configuration
            patient.state["next_visit_interval"] = loading_interval_weeks
            disease_activity["current_interval"] = loading_interval_weeks
            
            # Check for phase completion (default 3 loading injections or from config)
            if treatments_in_phase >= injections_required:
                # Transition to maintenance phase
                patient.state["current_phase"] = "maintenance"
                patient.state["treatments_in_phase"] = 0
                
                # Set initial maintenance interval from config
                patient.state["next_visit_interval"] = initial_interval_weeks
                disease_activity["current_interval"] = initial_interval_weeks
                
                # Update statistics
                self.stats["protocol_completions"] += 1
            
        elif phase == "maintenance":
            current_interval = disease_activity.get("current_interval", initial_interval_weeks)
            
            if fluid_detected:
                # Decrease interval by reduction_step, but not below initial interval
                new_interval = max(initial_interval_weeks, current_interval - reduction_step)
                disease_activity["consecutive_stable_visits"] = 0
                disease_activity["max_interval_reached"] = False
            else:
                # Increase interval by extension_step, up to max interval
                new_interval = min(max_interval_weeks, current_interval + extension_step)
                disease_activity["consecutive_stable_visits"] += 1
                
                # Check if max interval reached
                if new_interval >= max_interval_weeks:
                    disease_activity["max_interval_reached"] = True
                    
                # Evaluate discontinuation using the discontinuation manager
                result = self.discontinuation_manager.evaluate_discontinuation(
                    patient_state=patient.state,
                    current_time=event.time,
                    patient_id=patient_id,
                    clinician_id=clinician_id,
                    treatment_start_time=patient.state.get("treatment_start", patient.start_time),
                    clinician=clinician
                )
                
                # Handle different return types
                if isinstance(result, tuple) and len(result) >= 4:
                    should_discontinue, reason, probability, cessation_type = result
                elif hasattr(result, 'should_discontinue'):
                    # DiscontinuationDecision object
                    should_discontinue = result.should_discontinue
                    reason = result.reason
                    probability = result.probability 
                    cessation_type = result.cessation_type
                else:
                    # Unexpected return type, default to no discontinuation
                    logger.warning(f"Unexpected return type from evaluate_discontinuation: {type(result)}")
                    should_discontinue = False
                    reason = ""
                    probability = 0.0
                    cessation_type = ""
                
                # If discontinuation is recommended
                if should_discontinue:
                    # Update patient state
                    patient.state["treatment_status"]["active"] = False
                    patient.state["treatment_status"]["discontinuation_date"] = event.time
                    patient.state["treatment_status"]["discontinuation_reason"] = reason
                    patient.state["treatment_status"]["cessation_type"] = cessation_type
                    
                    # Update statistics
                    if patient_id not in self.discontinued_patients:
                        self.stats["protocol_discontinuations"] += 1
                        self.discontinued_patients.add(patient_id)
                    
                    # Apply vision changes specific to this type of discontinuation
                    # Convert patient state to expected format for discontinuation manager
                    patient_state_for_manager = {
                        "disease_activity": patient.state["disease_activity"],
                        "treatment_status": patient.state["treatment_status"],
                        "disease_characteristics": patient.state["disease_characteristics"],
                        "vision": {
                            "current_va": patient.state["current_vision"]
                        }
                    }
                    
                    # Apply vision changes based on cessation type
                    if hasattr(self.discontinuation_manager, 'apply_vision_changes_after_discontinuation'):
                        updated_patient_state = self.discontinuation_manager.apply_vision_changes_after_discontinuation(
                            patient_state=patient_state_for_manager,
                            cessation_type=cessation_type
                        )
                        
                        # Update patient with any vision changes
                        if "vision" in updated_patient_state and "current_va" in updated_patient_state["vision"]:
                            patient.state["current_vision"] = updated_patient_state["vision"]["current_va"]
                    
                    # Register the discontinuation with the manager
                    self.discontinuation_manager.register_discontinuation(
                        patient_id, 
                        cessation_type
                    )
                    
                    # Schedule monitoring visits
                    monitoring_events = self.discontinuation_manager.schedule_monitoring(
                        event.time,
                        cessation_type=cessation_type,
                        clinician=clinician,
                        patient_id=patient_id
                    )
                    
                    for monitoring_event in monitoring_events:
                        if monitoring_event["time"] <= self.clock.end_date:
                            self.clock.schedule_event(Event(
                                time=monitoring_event["time"],
                                event_type="visit",
                                patient_id=patient_id,
                                data={
                                    "actions": monitoring_event["actions"],
                                    "is_monitoring": True,
                                    "cessation_type": monitoring_event.get("cessation_type")
                                },
                                priority=1
                            ))
                    
                    return  # No more regular visits
            
            # Update interval for next visit
            patient.state["next_visit_interval"] = new_interval
            disease_activity["current_interval"] = new_interval
        
        # Update disease activity
        patient.state["disease_activity"] = disease_activity
        
        # Schedule next visit
        next_interval = patient.state["next_visit_interval"]
        next_visit_time = event.time + timedelta(weeks=next_interval)
        
        # Only schedule next visit if treatment is active and we haven't reached the end date
        if patient.state["treatment_status"]["active"] and next_visit_time <= self.clock.end_date:
            # Always include injection in treat-and-extend protocol
            next_actions = ["vision_test", "oct_scan", "injection"]
            
            self.clock.schedule_event(Event(
                time=next_visit_time,
                event_type="visit",
                patient_id=patient_id,
                data={
                    "visit_type": "injection_visit",
                    "actions": next_actions
                },
                priority=1
            ))
    
    def _print_statistics(self, stats, patient_histories):
        """
        Print simulation statistics.
        
        Parameters
        ----------
        stats : Dict
            Statistics dictionary
        patient_histories : Dict
            Patient histories dictionary
        """
        print("\nSimulation Statistics:")
        print("-" * 20)
        
        # Print basic stats
        formatted_stats = {}
        for stat, value in stats.items():
            # Special handling for nested dictionary
            if isinstance(value, dict):
                print(f"{stat}: {value}")
            else:
                formatted_stats[stat] = value
                print(f"{stat}: {value}")
        
        # Add discontinuation manager statistics
        discontinuation_stats = self.discontinuation_manager.get_statistics()
        print("\nDiscontinuation Statistics:")
        print("-" * 20)
        
        # Ensure unique counts are correct
        unique_discontinued = len(self.discontinued_patients)
        unique_retreated = len(self.retreated_patients)
        
        # Print actual stats
        print(f"unique_discontinued_patients: {unique_discontinued}")
        print(f"unique_retreated_patients: {unique_retreated}")
        
        # If there's a discrepancy, show warning
        dm_unique = discontinuation_stats.get("unique_discontinued_patients", 0)
        if dm_unique != unique_discontinued:
            print(f"WARNING: Discrepancy in unique discontinued patients: simulation={unique_discontinued}, manager={dm_unique}")
        
        # Print other stats
        for stat, value in discontinuation_stats.items():
            if stat not in ["unique_discontinued_patients", "unique_retreated_patients"]:
                print(f"{stat}: {value}")
        
        # Calculate discontinuation rate
        total_patients = len(self.patients)
        disc_rate = unique_discontinued / total_patients if total_patients > 0 else 0
        print(f"Discontinuation rate: {disc_rate:.2%} ({unique_discontinued}/{total_patients} patients)")
        
        # Print patient summary
        print("\nPatient Summary:")
        print("-" * 20)
        total_visits = sum(len(patient.state.get("visit_history", [])) for patient in self.patients.values())
        avg_visits = total_visits / max(1, total_patients)
        print(f"Total Patients: {total_patients}")
        print(f"Total Visits: {total_visits}")
        print(f"Average Visits per Patient: {avg_visits:.1f}")
        
        # Calculate loading phase completion rate
        loading_completions = self.stats["protocol_completions"]
        loading_completion_rate = (loading_completions / max(1, total_patients)) * 100
        print(f"Loading Phase Completion Rate: {loading_completion_rate:.1f}%")

# Entry point function for running the integrated implementation
def run_enhanced_treat_and_extend_des(config="eylea_literature_based", verbose=False):
    """
    Run a simulation with the enhanced treat-and-extend DES implementation.
    
    Parameters
    ----------
    config : str or SimulationConfig, optional
        Name of the configuration file or configuration object, by default "eylea_literature_based"
    verbose : bool, optional
        Whether to print verbose output, by default False
        
    Returns
    -------
    Dict[str, Any]
        Simulation results including patient histories and statistics
    """
    # Create and run simulation
    print(f"Running enhanced treat-and-extend DES simulation with config: {config}")
    sim = EnhancedTreatAndExtendDES(config)
    results = sim.run()
    
    # Extract patient histories
    patient_histories = results.get("patient_histories", {})
    
    # Convert patient histories to DataFrame for analysis if verbose
    if verbose:
        all_data = []
        for patient_id, visits in patient_histories.items():
            for visit in visits:
                # Extract key data from visit
                visit_data = {
                    'patient_id': patient_id,
                    'date': visit.get('date', ''),
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
        df.to_csv('enhanced_treat_and_extend_des_data.csv', index=False)
        print(f"Saved data for {len(patient_histories)} patients to enhanced_treat_and_extend_des_data.csv")
        
        # Sample a few patients to check their visit patterns
        sample_patients = np.random.choice(list(patient_histories.keys()), min(3, len(patient_histories)))
        
        for patient_id in sample_patients:
            patient_data = [visit for visit in patient_histories[patient_id]]
            patient_data.sort(key=lambda v: v['date'])
            
            print(f"\nPatient {patient_id} visits:")
            for visit in patient_data:
                print(f"  {visit['date']} - Phase: {visit['phase']} - Actions: {visit['actions']}")
    
    return results

if __name__ == "__main__":
    run_enhanced_treat_and_extend_des(verbose=True)