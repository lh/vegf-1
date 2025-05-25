"""
Staggered patient enrollment for treat-and-extend protocol with DES implementation.

This module extends the fixed DES implementation with staggered patient enrollment,
where patients arrive according to a Poisson process over time, providing a more
realistic model of real-world clinical settings.

The implementation:
1. Uses Poisson arrival process to generate patient enrollment over time
2. Maintains protocol accuracy with proper loading and maintenance phases
3. Ensures correct discontinuation handling
4. Produces output compatible with existing analysis and visualization tools

The module is designed to be used in conjunction with the standard simulation runner
or with the specialized staggered simulation runner.

Classes
-------
StaggeredTreatAndExtendDES
    Implementation of staggered patient enrollment for DES simulations
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
from simulation.config import SimulationConfig
from treat_and_extend_des_fixed import TreatAndExtendDES

# Set up logger
logger = logging.getLogger(__name__)

class StaggeredTreatAndExtendDES(TreatAndExtendDES):
    """Staggered patient enrollment for DES treat-and-extend protocol.
    
    This class extends the fixed TreatAndExtendDES implementation to support
    staggered patient enrollment using a Poisson process, providing a more
    realistic model of real-world clinical settings.
    
    Parameters
    ----------
    config : SimulationConfig or str
        Simulation configuration or name of configuration file
    start_date : datetime, optional
        Simulation start date, by default None (uses config start_date)
    patient_arrival_rate : float, optional
        Average number of new patients per week, by default 10.0
    random_seed : int, optional
        Random seed for reproducibility, by default None
        
    Attributes
    ----------
    config : SimulationConfig
        Simulation configuration
    start_date : datetime
        Start date of the simulation
    end_date : datetime
        End date of the simulation
    patient_arrival_rate : float
        Average number of new patients per week
    patients : dict
        Dictionary mapping patient IDs to patient states
    stats : dict
        Simulation statistics
    events : list
        Event queue
    discontinued_patients : set
        Set of discontinued patient IDs
    retreated_patients : set
        Set of retreated patient IDs
    enrollment_dates : dict
        Dictionary mapping patient IDs to enrollment dates
    """
    
    def __init__(self, config=None, start_date=None, patient_arrival_rate=10.0, random_seed=None):
        """Initialize the staggered simulation.
        
        Parameters
        ----------
        config : SimulationConfig or str, optional
            Simulation configuration or name, by default None (uses "eylea_literature_based")
        start_date : datetime, optional
            Simulation start date, by default None (uses config start_date)
        patient_arrival_rate : float, optional
            Average number of new patients per week, by default 10.0
        random_seed : int, optional
            Random seed for reproducibility, by default None
        """
        # Initialize the base class
        super().__init__(config)
        
        # Store arrival rate
        self.patient_arrival_rate = patient_arrival_rate
        
        # Set random seed if provided
        if random_seed is not None:
            np.random.seed(random_seed)
        
        # Override start date if provided
        if start_date is not None:
            self.start_date = start_date
            # Recalculate end date
            self.end_date = self.start_date + timedelta(days=self.config.duration_days)
        
        # Additional tracking for staggered simulation
        self.enrollment_dates = {}  # Map patient_id -> enrollment_date
    
    def _generate_patients(self):
        """Generate patients with staggered arrival times using a Poisson process.
        
        This method overrides the base implementation to use a Poisson process
        for patient arrivals, spreading them throughout the simulation period
        rather than all at the beginning.
        """
        # Calculate simulation duration in weeks
        simulation_weeks = self.config.duration_days / 7
        
        # Use a Poisson process to generate arrival times
        arrival_times = []
        week = 0
        patient_num = 1
        
        # Generate arrivals throughout the simulation period
        while week < simulation_weeks:
            # Poisson distribution for patients arriving this week
            patients_this_week = np.random.poisson(self.patient_arrival_rate)
            
            # Skip if no patients this week
            if patients_this_week == 0:
                week += 1
                continue
            
            # Generate arrival times within the week
            for i in range(patients_this_week):
                # Random time within the week
                day_offset = np.random.uniform(0, 7)
                arrival_time = self.start_date + timedelta(days=week*7 + day_offset)
                
                # Only schedule if within simulation period
                if arrival_time < self.end_date:
                    arrival_times.append((arrival_time, patient_num))
                    patient_num += 1
            
            week += 1
        
        # Sort arrival times
        arrival_times.sort()
        
        # Log the total arrivals
        logger.info(f"Generated {len(arrival_times)} staggered patient arrivals over {simulation_weeks:.1f} weeks")
        
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
                "id": patient_id,  # Store ID in the patient dict for tracking
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
                    "weeks_since_discontinuation": 0,
                    "cessation_type": None,
                    "discontinuation_date": None,  # Track date for statistics
                },
                "disease_characteristics": {
                    "has_PED": np.random.random() < 0.3,  # 30% of patients have PED
                },
                "visit_history": [],
                "treatment_start": arrival_time  # Store treatment start date for duration calculations
            }
            
            # Store enrollment date
            self.enrollment_dates[patient_id] = arrival_time
            
            # Schedule initial visit
            self.events.append({
                "time": arrival_time,
                "type": "visit",
                "patient_id": patient_id,
                "actions": ["vision_test", "oct_scan", "injection"]
            })
    
    def _process_visit(self, event):
        """Process patient visit with staggered enrollment considerations.
        
        This method overrides the base implementation to handle staggered enrollments
        and ensure proper recording of calendar time and patient time.
        
        Parameters
        ----------
        event : dict
            Event containing:
            - time: datetime - Visit time
            - patient_id: str - Patient ID
            - actions: list - Actions to perform
        """
        # Use base class to process the visit
        super()._process_visit(event)
        
        # After processing, update the visit history with additional time information
        patient_id = event.get("patient_id")
        if patient_id in self.patients and self.patients[patient_id]["visit_history"]:
            # Get enrollment date
            enrollment_date = self.enrollment_dates.get(patient_id)
            if enrollment_date:
                # Calculate time since enrollment
                visit_date = event.get("time")
                if visit_date:
                    # Add time information to the most recent visit
                    most_recent_visit = self.patients[patient_id]["visit_history"][-1]
                    
                    # Add calendar time (absolute date)
                    most_recent_visit["calendar_time"] = visit_date
                    
                    # Add patient time (relative to enrollment)
                    days_since_enrollment = (visit_date - enrollment_date).days
                    weeks_since_enrollment = days_since_enrollment / 7
                    
                    most_recent_visit["days_since_enrollment"] = days_since_enrollment
                    most_recent_visit["weeks_since_enrollment"] = weeks_since_enrollment

def run_staggered_treat_and_extend_des(config=None, start_date=None, patient_arrival_rate=10.0, random_seed=None, verbose=False):
    """Run a staggered DES simulation with the treat-and-extend protocol.
    
    Parameters
    ----------
    config : SimulationConfig or str, optional
        Simulation configuration or name, by default None
    start_date : datetime, optional
        Simulation start date, by default None
    patient_arrival_rate : float, optional
        Average number of new patients per week, by default 10.0
    random_seed : int, optional
        Random seed for reproducibility, by default None
    verbose : bool, optional
        Whether to print verbose output, by default False
        
    Returns
    -------
    dict
        Dictionary containing:
        - patient_histories: Dictionary mapping patient IDs to visit histories
        - enrollment_dates: Dictionary mapping patient IDs to enrollment dates
    """
    # Create and run simulation
    sim = StaggeredTreatAndExtendDES(
        config=config,
        start_date=start_date,
        patient_arrival_rate=patient_arrival_rate,
        random_seed=random_seed
    )
    
    # Run the simulation
    patient_histories = sim.run()
    
    # Get enrollment dates
    enrollment_dates = sim.enrollment_dates
    
    # Convert enrollment dates to dictionary of datetime objects
    enrollment_dates_dict = {pid: date for pid, date in enrollment_dates.items()}
    
    # Convert patient histories to DataFrame for analysis if verbose
    if verbose:
        all_data = []
        for patient_id, visits in patient_histories.items():
            for visit in visits:
                # Extract key data from visit
                visit_data = {
                    'patient_id': patient_id,
                    'date': visit.get('date', ''),
                    'calendar_time': visit.get('calendar_time', visit.get('date', '')),
                    'days_since_enrollment': visit.get('days_since_enrollment', None),
                    'weeks_since_enrollment': visit.get('weeks_since_enrollment', None),
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
        
        # Plot enrollment distribution
        plt.figure(figsize=(10, 6))
        enrollment_dates_list = list(enrollment_dates_dict.values())
        plt.hist(enrollment_dates_list, bins=20, alpha=0.7, color='skyblue')
        plt.title('Patient Enrollment Distribution')
        plt.xlabel('Date')
        plt.ylabel('Number of Patients')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('staggered_des_enrollment.png')
        plt.close()
        print("Saved enrollment distribution to staggered_des_enrollment.png")
    
    # Return results with enrollment dates
    return {
        'patient_histories': patient_histories,
        'enrollment_dates': enrollment_dates_dict
    }

if __name__ == "__main__":
    # Run a test simulation
    from datetime import datetime
    
    # Create test configuration
    config = SimulationConfig(
        config_name="staggered_des_test",
        num_patients=100,  # This is just an approximation, actual count depends on arrival rate
        duration_days=365,
        start_date="2023-01-01",
        random_seed=42,
        parameters={
            "vision_model_type": "realistic",
            "vision": {
                "baseline_mean": 65,
                "baseline_std": 10,
                "max_letters": 85,
                "min_letters": 0,
                "headroom_factor": 0.5
            },
            "discontinuation": {
                "enabled": True,
                "criteria": {
                    "stable_max_interval": {
                        "probability": 0.2,
                        "consecutive_visits": 3,
                        "interval_weeks": 16
                    }
                }
            }
        }
    )
    
    # Run simulation
    results = run_staggered_treat_and_extend_des(
        config=config,
        patient_arrival_rate=5.0,  # ~5 new patients per week on average
        verbose=True
    )
    
    # Print summary
    patient_histories = results['patient_histories']
    enrollment_dates = results['enrollment_dates']
    
    print(f"Simulation completed with {len(patient_histories)} patients")
    print(f"First enrollment: {min(enrollment_dates.values())}")
    print(f"Last enrollment: {max(enrollment_dates.values())}")