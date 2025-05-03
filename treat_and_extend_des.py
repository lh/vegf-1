"""
Treat-and-extend protocol implementation for Discrete Event Simulation (DES).

This module provides a production-ready implementation of the treat-and-extend protocol
for AMD treatment modeling using Discrete Event Simulation. It ensures patients receive
injections at every visit as required by the protocol and follows the Veeramani pathway
for interval adjustments.

Key Features
-----------
- Complete implementation of treat-and-extend protocol
- Injections at every visit (loading and maintenance phases)
- Proper phase transitions (loading → maintenance)
- Interval adjustments based on disease activity (8→10→12→14→16 weeks)
- Accurate patient generation based on configuration

Functions
---------
run_treat_and_extend_des
    Main entry point for running a DES simulation with the treat-and-extend protocol
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from simulation.config import SimulationConfig
from simulation import DiscreteEventSimulation, Event
from simulation.patient_state import PatientState
from simulation.clinical_model import ClinicalModel
from simulation.scheduler import ClinicScheduler

class TreatAndExtendDES:
    """
    Treat-and-extend protocol implementation for Discrete Event Simulation.
    
    This class implements the treat-and-extend protocol according to the
    Veeramani pathway diagram, ensuring that patients receive injections
    at every visit.
    """
    
    def __init__(self, config_name="eylea_literature_based"):
        """
        Initialize the simulation with the specified configuration.
        
        Parameters
        ----------
        config_name : str, optional
            Name of the configuration file, by default "eylea_literature_based"
        """
        self.config = SimulationConfig.from_yaml(config_name)
        self.start_date = datetime.strptime(self.config.start_date, "%Y-%m-%d") if isinstance(self.config.start_date, str) else self.config.start_date
        self.end_date = self.start_date + timedelta(days=self.config.duration_days)
        
        # Initialize components
        self.scheduler = ClinicScheduler(
            daily_capacity=20,
            days_per_week=5
        )
        
        # Patient state management
        self.patients = {}
        
        # Statistics
        self.stats = {
            "total_visits": 0,
            "total_injections": 0,
            "total_oct_scans": 0,
            "vision_improvements": 0,
            "vision_declines": 0,
            "protocol_completions": 0,
            "protocol_discontinuations": 0
        }
        
        # Event queue
        self.events = []
        self.current_time = self.start_date
        
    def run(self):
        """
        Run the simulation.
        """
        print("Initializing treat-and-extend DES simulation...")
        
        # Generate patients
        self._generate_patients()
        
        # Process events
        print("Processing events...")
        event_count = 0
        while self.events:
            # Sort events by time
            self.events.sort(key=lambda e: e["time"])
            
            # Get next event
            event = self.events.pop(0)
            
            # Update current time
            self.current_time = event["time"]
            
            # Process event
            if event["type"] == "visit":
                self._process_visit(event)
            
            # Print progress
            event_count += 1
            if event_count % 1000 == 0:
                print(f"Processed {event_count} events...")
        
        print(f"Simulation complete after {event_count} events")
        
        # Print statistics
        self._print_statistics()
        
        # Return patient histories
        return {pid: patient["visit_history"] for pid, patient in self.patients.items()}
    
    def _generate_patients(self):
        """
        Generate patients and schedule their initial visits.
        """
        num_patients = self.config.num_patients
        print(f"Generating {num_patients} patients...")
        
        # Calculate arrival rate to distribute patients over simulation period
        simulation_weeks = self.config.duration_days / 7
        distribution_weeks = max(1, simulation_weeks / 2)
        rate_per_week = num_patients / distribution_weeks
        
        # Generate arrival times
        arrival_times = []
        week = 0
        patient_num = 1
        
        while patient_num <= num_patients and week < simulation_weeks:
            # Determine patients this week using Poisson distribution
            patients_this_week = min(
                np.random.poisson(rate_per_week),
                num_patients - patient_num + 1
            )
            
            # Distribute patients throughout the week
            for i in range(patients_this_week):
                # Random time within the week
                day_offset = np.random.uniform(0, 7)
                arrival_time = self.start_date + timedelta(days=week*7 + day_offset)
                
                # Ensure arrival time is before end date
                if arrival_time < self.end_date:
                    arrival_times.append((arrival_time, patient_num))
                    patient_num += 1
            
            week += 1
        
        # Create patients and schedule initial visits
        for arrival_time, patient_num in arrival_times:
            patient_id = f"PATIENT{patient_num:03d}"
            
            # Initialize patient
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
            
            # Create patient
            self.patients[patient_id] = {
                "id": patient_id,
                "current_vision": initial_vision,
                "baseline_vision": initial_vision,
                "current_phase": "loading",
                "treatments_in_phase": 0,
                "next_visit_interval": 4,  # Initial loading phase interval
                "disease_activity": {
                    "fluid_detected": True,  # Start with fluid detected (active disease)
                    "consecutive_stable_visits": 0,
                    "max_interval_reached": False,
                    "current_interval": 4  # Start with loading phase interval
                },
                "treatment_status": {
                    "active": True,
                    "recurrence_detected": False,
                    "weeks_since_discontinuation": 0
                },
                "visit_history": []
            }
            
            # Schedule initial visit
            self.events.append({
                "time": arrival_time,
                "type": "visit",
                "patient_id": patient_id,
                "actions": ["vision_test", "oct_scan", "injection"]
            })
    
    def _process_visit(self, event):
        """
        Process a patient visit.
        
        Parameters
        ----------
        event : dict
            Event containing:
            - time: datetime - Visit time
            - patient_id: str - Patient ID
            - actions: list - Actions to perform
        """
        patient_id = event["patient_id"]
        if patient_id not in self.patients:
            return
        
        patient = self.patients[patient_id]
        
        # Update statistics
        self.stats["total_visits"] += 1
        if "injection" in event["actions"]:
            self.stats["total_injections"] += 1
        if "oct_scan" in event["actions"]:
            self.stats["total_oct_scans"] += 1
        
        # Simulate vision change
        baseline_vision = patient["current_vision"]
        vision_change = np.random.normal(2, 1)  # Simplified vision change model
        new_vision = min(max(baseline_vision + vision_change, 0), 85)
        
        # Update patient vision
        patient["current_vision"] = new_vision
        
        # Update vision statistics
        if new_vision > baseline_vision:
            self.stats["vision_improvements"] += 1
        elif new_vision < baseline_vision:
            self.stats["vision_declines"] += 1
        
        # Determine if fluid was detected (simplified)
        fluid_detected = np.random.random() < 0.3  # 30% chance of fluid detection
        
        # Update disease activity
        patient["disease_activity"]["fluid_detected"] = fluid_detected
        
        # Record visit
        visit_record = {
            'date': event["time"],
            'actions': event["actions"],
            'vision': new_vision,
            'baseline_vision': baseline_vision,
            'phase': patient["current_phase"],
            'type': 'regular_visit',
            'disease_state': 'stable' if not fluid_detected else 'active',
            'treatment_status': patient["treatment_status"].copy()
        }
        patient["visit_history"].append(visit_record)
        
        # Process based on current phase
        current_phase = patient["current_phase"]
        treatments_in_phase = patient["treatments_in_phase"] + 1
        patient["treatments_in_phase"] = treatments_in_phase
        
        if current_phase == "loading":
            # Check if loading phase is complete (3 injections)
            if treatments_in_phase >= 3:
                # Transition to maintenance phase
                patient["current_phase"] = "maintenance"
                patient["treatments_in_phase"] = 0
                
                # Set initial maintenance interval to 8 weeks per Veeramani pathway
                patient["next_visit_interval"] = 8
                patient["disease_activity"]["current_interval"] = 8
                
                # Update statistics
                self.stats["protocol_completions"] += 1
            else:
                # Continue loading phase with 4-week intervals
                patient["next_visit_interval"] = 4
                patient["disease_activity"]["current_interval"] = 4
        
        elif current_phase == "maintenance":
            current_interval = patient["disease_activity"]["current_interval"]
            
            if fluid_detected:
                # Decrease interval by 2 weeks, but not below 8 weeks
                new_interval = max(8, current_interval - 2)
                patient["disease_activity"]["consecutive_stable_visits"] = 0
                patient["disease_activity"]["max_interval_reached"] = False
            else:
                # Increase interval by 2 weeks, up to 16 weeks maximum
                new_interval = min(16, current_interval + 2)
                patient["disease_activity"]["consecutive_stable_visits"] += 1
                
                # Check if max interval reached
                if new_interval >= 16:
                    patient["disease_activity"]["max_interval_reached"] = True
                    
                    # Check for potential discontinuation
                    if patient["disease_activity"]["consecutive_stable_visits"] >= 3:
                        # Consider discontinuation after 3 stable visits at max interval
                        if np.random.random() < 0.2:  # 20% chance of discontinuation
                            patient["treatment_status"]["active"] = False
                            patient["treatment_status"]["discontinuation_date"] = event["time"]
                            self.stats["protocol_discontinuations"] += 1
                            return  # No more visits
            
            # Update interval for next visit
            patient["next_visit_interval"] = new_interval
            patient["disease_activity"]["current_interval"] = new_interval
        
        # Schedule next visit
        next_interval = patient["next_visit_interval"]
        next_visit_time = event["time"] + timedelta(weeks=next_interval)
        
        # Only schedule next visit if treatment is active and we haven't reached the end date
        if patient["treatment_status"]["active"] and next_visit_time <= self.end_date:
            # Always include injection in treat-and-extend protocol
            next_actions = ["vision_test", "oct_scan", "injection"]
            
            self.events.append({
                "time": next_visit_time,
                "type": "visit",
                "patient_id": patient_id,
                "actions": next_actions
            })
    
    def _print_statistics(self):
        """
        Print simulation statistics.
        """
        print("\nSimulation Statistics:")
        print("-" * 20)
        for stat, value in self.stats.items():
            print(f"{stat}: {value}")
        
        # Print patient summary
        print("\nPatient Summary:")
        print("-" * 20)
        total_patients = len(self.patients)
        total_visits = sum(len(patient["visit_history"]) for patient in self.patients.values())
        avg_visits = total_visits / max(1, total_patients)
        print(f"Total Patients: {total_patients}")
        print(f"Total Visits: {total_visits}")
        print(f"Average Visits per Patient: {avg_visits:.1f}")
        
        # Calculate loading phase completion rate
        loading_completions = self.stats["protocol_completions"]
        loading_completion_rate = (loading_completions / max(1, total_patients)) * 100
        print(f"Loading Phase Completion Rate: {loading_completion_rate:.1f}%")
        
        # Calculate maintenance phase injection rate
        maintenance_visits = 0
        maintenance_injections = 0
        for patient in self.patients.values():
            for visit in patient["visit_history"]:
                if visit["phase"] == "maintenance":
                    maintenance_visits += 1
                    if "injection" in visit["actions"]:
                        maintenance_injections += 1
        
        if maintenance_visits > 0:
            maintenance_injection_rate = (maintenance_injections / maintenance_visits) * 100
            print(f"Maintenance Phase Injection Rate: {maintenance_injection_rate:.1f}%")

def run_treat_and_extend_des(config=None, verbose=False):
    """
    Run a DES simulation with the treat-and-extend protocol.
    
    Parameters
    ----------
    config : SimulationConfig, optional
        Simulation configuration, by default None
    verbose : bool, optional
        Whether to print verbose output, by default False
        
    Returns
    -------
    Dict[str, List[Dict]]
        Dictionary mapping patient IDs to their visit histories
    """
    # Create and run simulation
    config_name = config.config_name if config and hasattr(config, 'config_name') else "eylea_literature_based"
    sim = TreatAndExtendDES(config_name)
    patient_histories = sim.run()
    
    # Convert patient histories to DataFrame for analysis
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
    df.to_csv('treat_and_extend_des_data.csv', index=False)
    print(f"Saved data for {len(patient_histories)} patients to treat_and_extend_des_data.csv")
    
    # Sample a few patients to check their visit patterns
    if verbose:
        sample_patients = np.random.choice(list(patient_histories.keys()), 3)
        
        for patient_id in sample_patients:
            patient_data = [visit for visit in patient_histories[patient_id]]
            patient_data.sort(key=lambda v: v['date'])
            
            print(f"\nPatient {patient_id} visits:")
            for visit in patient_data:
                print(f"  {visit['date']} - Phase: {visit['phase']} - Actions: {visit['actions']}")
    
    return patient_histories

if __name__ == "__main__":
    run_treat_and_extend_des(verbose=True)
