"""Staggered Agent-Based Simulation (ABS) for AMD treatment pathways.

This module enhances the ABS implementation by adding staggered patient enrollment,
where patients are added to the simulation gradually over time following a
Poisson distribution rather than all at once at the beginning.

This helps model more realistic scenarios where new patients present continuously
over time, and enables proper analysis of calendar time (simulation time) vs.
patient time (time since individual enrollment).

Notes
-----
Key Features:
- Staggered patient arrivals using Poisson process
- Dual timeframe tracking (calendar time and patient time)
- Enhanced visualization capabilities for patient cohorts
- More accurate resource utilization projections
- Improved analysis of treatment patterns over time
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import logging

from simulation.abs import AgentBasedSimulation
from simulation.patient_generator import PatientGenerator
from simulation.abs_patient_generator import ABSPatientGenerator
from simulation.base import Event
from simulation.patient_state import PatientState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StaggeredABS(AgentBasedSimulation):
    """Enhanced Agent-Based Simulation with staggered patient enrollment.
    
    Extends the standard ABS by implementing staggered patient arrivals using a
    Poisson process, enabling more realistic modeling of patient populations over time.
    
    Parameters
    ----------
    config : Any
        Configuration object containing simulation parameters
    start_date : datetime
        Start date for the simulation
    patient_arrival_rate : float, optional
        Average number of new patients per week, by default 10.0
    random_seed : Optional[int], optional
        Random seed for reproducibility, by default None
    
    Attributes
    ----------
    start_date : datetime
        Start date of the simulation
    agents : Dict[str, Patient]
        Dictionary mapping patient IDs to Patient agents
    patient_generator : ABSPatientGenerator
        Generator for patient arrivals and initial states
    patient_arrival_rate : float
        Average number of new patients per week
    enrollment_dates : Dict[str, datetime]
        Dictionary mapping patient IDs to their enrollment dates
    """
    
    def __init__(self, config, start_date: datetime, patient_arrival_rate: float = 10.0, 
                 random_seed: Optional[int] = None):
        """Initialize the staggered simulation with specified parameters."""
        super().__init__(config, start_date)
        
        # Store the configuration
        self.simulation_config = config
        
        # Store the end date for calculating the total simulation duration
        sim_params = config.get_simulation_params()
        self.end_date = self.clock.end_date if hasattr(self.clock, 'end_date') else None
        if 'end_date' in sim_params:
            self.end_date = sim_params['end_date']
        elif 'duration_days' in sim_params:
            self.end_date = self.start_date + timedelta(days=sim_params['duration_days'])
        else:
            # Default to one year if not specified
            self.end_date = self.start_date + timedelta(days=365)
        
        # Set up patient arrival rate
        self.patient_arrival_rate = patient_arrival_rate
        self.random_seed = random_seed
        
        # Initialize patient generator
        self.patient_generator = ABSPatientGenerator(
            rate_per_week=patient_arrival_rate,
            start_date=start_date,
            end_date=self.end_date,
            random_seed=random_seed
        )
        
        # Initialize enrollment tracking
        self.enrollment_dates = {}
        
        # Track patient time (time since enrollment) separately from calendar time
        self.patient_time = {}
        
        logger.info(f"Initialized StaggeredABS with arrival rate {patient_arrival_rate} patients/week")
        logger.info(f"Simulation period: {start_date} to {self.end_date}")
    
    def initialize_simulation(self):
        """Initialize the simulation by generating patient arrival schedule.
        
        This method generates the complete patient arrival schedule at the beginning
        of the simulation but doesn't create all patients immediately - they are
        created only when their arrival time is reached during simulation execution.
        """
        # Generate arrival schedule
        self.patient_arrival_schedule = self.patient_generator.generate_arrival_times()
        
        # Log the arrival schedule
        logger.info(f"Generated arrival schedule for {len(self.patient_arrival_schedule)} patients")
        
        # Schedule arrival events for each patient
        for i, (arrival_time, patient_num) in enumerate(self.patient_arrival_schedule):
            patient_id = f"P{patient_num:04d}"
            
            # Create arrival event
            self.clock.schedule_event(Event(
                time=arrival_time,
                event_type="patient_arrival",
                patient_id=patient_id,
                data={
                    "patient_num": patient_num,
                    "arrival_index": i
                },
                priority=1  # High priority for patient arrivals
            ))
        
        logger.info(f"Scheduled {len(self.patient_arrival_schedule)} patient arrival events")
    
    def process_event(self, event: Event):
        """Process simulation events including patient arrivals.
        
        Parameters
        ----------
        event : Event
            Event to process
        """
        # Handle patient arrival events
        if event.event_type == "patient_arrival":
            self._process_patient_arrival(event)
        else:
            # For all other events, use the parent class implementation
            super().process_event(event)
    
    def _process_patient_arrival(self, event: Event):
        """Process a patient arrival event.
        
        Parameters
        ----------
        event : Event
            Patient arrival event to process
        """
        patient_id = event.patient_id
        patient_num = event.data.get("patient_num")
        arrival_time = event.time
        
        # Log the arrival
        logger.info(f"Patient {patient_id} arrived at {arrival_time}")
        
        # Create initial patient state
        initial_patient_state = self._create_initial_patient_state(patient_id, arrival_time)

        # Add patient to the simulation
        # Use the protocol name from the state dictionary since it's not directly accessible as an attribute
        protocol_name = initial_patient_state.state["protocol"]
        super().add_patient(patient_id, protocol_name)
        
        # Store enrollment date
        self.enrollment_dates[patient_id] = arrival_time
        
        # Initialize patient time as 0 (time since enrollment)
        self.patient_time[patient_id] = 0
        
        # Schedule initial visit
        initial_visit_time = arrival_time
        self.clock.schedule_event(Event(
            time=initial_visit_time,
            event_type="visit",
            patient_id=patient_id,
            data={
                "visit_type": "initial_visit",
                "actions": ["vision_test", "oct_scan", "injection"],
                "decisions": ["nurse_vision_check", "doctor_treatment_decision"],
                "is_initial": True
            },
            priority=1
        ))
    
    def _create_initial_patient_state(self, patient_id: str, enrollment_date: datetime) -> PatientState:
        """Create initial state for a new patient.
        
        Parameters
        ----------
        patient_id : str
            Unique identifier for the patient
        enrollment_date : datetime
            Date when the patient enrolled in the simulation
            
        Returns
        -------
        PatientState
            Initial state for the patient
        """
        # Generate baseline vision from configuration
        vision_params = self.simulation_config.get_vision_params()
        initial_vision = vision_params.get("baseline_mean", 65)
        
        # Add randomness to initial vision
        if vision_params.get("baseline_std"):
            initial_vision = np.random.normal(
                initial_vision, 
                vision_params.get("baseline_std", 10)
            )
            # Clamp vision between 0-85 ETDRS letters
            initial_vision = min(max(initial_vision, 0), 85)
        
        # Extract protocol name directly from the protocol attribute
        # This is more reliable than using get_protocol_info()
        protocol = getattr(self.simulation_config, 'protocol', None)
        if protocol and hasattr(protocol, 'protocol_name'):
            protocol_name = protocol.protocol_name
        else:
            # Fallback to a default protocol name if not found
            protocol_name = "treat_and_extend"
        
        # Create and return patient state
        return PatientState(
            patient_id=patient_id,
            protocol_name=protocol_name,
            initial_vision=initial_vision,
            start_time=enrollment_date
        )
    
    def run(self, end_date: Optional[datetime] = None):
        """Run the simulation until the specified end date.
        
        Parameters
        ----------
        end_date : Optional[datetime], optional
            Date to end the simulation, by default None (uses config end_date)
            
        Returns
        -------
        Dict[str, List[Dict]]
            Dictionary mapping patient IDs to their visit histories
        """
        # Set end date if provided
        if end_date:
            self.end_date = end_date
            self.clock.end_date = end_date
        
        # Initialize patient arrival schedule
        self.initialize_simulation()
        
        # Process events chronologically
        logger.info("Starting simulation execution...")
        event_count = 0
        
        while self.clock.current_time <= self.end_date:
            event = self.clock.get_next_event()
            if event is None:
                break
                
            # Update calendar time
            self.clock.current_time = event.time
            
            # Update patient times (time since enrollment)
            for pid in self.enrollment_dates:
                if pid in self.patient_time:
                    enrollment_date = self.enrollment_dates[pid]
                    self.patient_time[pid] = (self.clock.current_time - enrollment_date).days
            
            # Process this event
            self.process_event(event)
            
            # Update progress counter
            event_count += 1
            if event_count % 1000 == 0:
                logger.info(f"Processed {event_count} events... Current time: {self.clock.current_time}")
        
        logger.info(f"Simulation complete at {self.clock.current_time} after {event_count} events")
        
        # Return patient histories
        return self.get_results()
    
    def get_results(self):
        """Get the simulation results with enhanced time information.
        
        Returns
        -------
        Dict
            Enhanced result dictionary containing:
            - patients: Dict mapping patient IDs to Patient objects
            - events: List of processed events
            - enrollment_dates: Dict mapping patient IDs to enrollment dates
        """
        results = super().get_results()
        
        # Add enrollment dates to results
        results['enrollment_dates'] = self.enrollment_dates
        
        # Process patient histories to add calendar time and patient time
        patient_histories = {}
        
        for patient_id, patient in self.agents.items():
            # Get enrollment date for this patient
            enrollment_date = self.enrollment_dates.get(patient_id, self.start_date)
            
            # Process visit history
            processed_history = []
            for visit in patient.history:
                # Make a copy of the visit data
                visit_data = visit.copy()
                
                # Add calendar time and patient time
                if 'date' in visit_data:
                    visit_date = visit_data['date']
                    days_since_enrollment = (visit_date - enrollment_date).days
                    weeks_since_enrollment = days_since_enrollment / 7
                    
                    # Add time information
                    visit_data['calendar_time'] = visit_date
                    visit_data['days_since_enrollment'] = days_since_enrollment
                    visit_data['weeks_since_enrollment'] = weeks_since_enrollment
                
                processed_history.append(visit_data)
            
            patient_histories[patient_id] = processed_history
        
        # Return enhanced results
        return {
            'patients': self.agents,
            'events': self.clock.event_list if hasattr(self.clock, 'event_list') else [],
            'enrollment_dates': self.enrollment_dates,
            'patient_histories': patient_histories
        }

def run_staggered_abs(config, start_date=None, patient_arrival_rate=10.0, random_seed=None, verbose=False):
    """Run an Agent-Based Simulation with staggered patient enrollment.
    
    Parameters
    ----------
    config : Any
        Simulation configuration
    start_date : Optional[datetime], optional
        Start date for the simulation, by default None (uses config start_date)
    patient_arrival_rate : float, optional
        Average number of new patients per week, by default 10.0
    random_seed : Optional[int], optional
        Random seed for reproducibility, by default None
    verbose : bool, optional
        Whether to print verbose output, by default False
        
    Returns
    -------
    Dict
        Simulation results
    """
    # Set up logging based on verbosity
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Get start date from config if not provided
    if start_date is None:
        if hasattr(config, 'start_date'):
            start_date = config.start_date
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            # Default to current date if not specified
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Create and run simulation
    sim = StaggeredABS(
        config=config,
        start_date=start_date,
        patient_arrival_rate=patient_arrival_rate,
        random_seed=random_seed
    )
    
    # Run simulation
    if verbose:
        print(f"Running staggered ABS with arrival rate {patient_arrival_rate} patients/week...")
    
    results = sim.run()
    
    if verbose:
        # Calculate some statistics
        total_patients = len(results.get('patient_histories', {}))
        patient_visits = sum(len(history) for history in results.get('patient_histories', {}).values())
        
        print("\nSimulation Results:")
        print(f"Total Patients: {total_patients}")
        print(f"Total Visits: {patient_visits}")
        print(f"Average Visits per Patient: {patient_visits / max(1, total_patients):.1f}")
        
        # Show enrollment distribution
        if 'enrollment_dates' in results:
            from collections import Counter
            import matplotlib.pyplot as plt
            
            # Convert to month for histogram
            enrollment_months = [date.strftime('%Y-%m') for date in results['enrollment_dates'].values()]
            month_counts = Counter(enrollment_months)
            
            # Generate quick histogram
            months = sorted(month_counts.keys())
            counts = [month_counts[month] for month in months]
            
            if verbose:
                plt.figure(figsize=(10, 5))
                plt.bar(months, counts)
                plt.xticks(rotation=45)
                plt.title('Patient Enrollment by Month')
                plt.ylabel('Number of Patients')
                plt.tight_layout()
                plt.savefig('patient_enrollment_histogram.png')
                print("Saved enrollment histogram to patient_enrollment_histogram.png")
    
    # Return processed patient histories for analysis
    patient_histories = {}

    if isinstance(results, dict):
        if 'patient_histories' in results:
            patient_histories = results['patient_histories']
            print(f"Found {len(patient_histories)} patient histories in 'patient_histories' key")
        else:
            # Get patient histories directly from results
            patient_histories = results
            print(f"Using {len(patient_histories)} patient histories directly from results")

    if verbose:
        print(f"Returning {len(patient_histories)} patient histories with {sum(len(visits) for visits in patient_histories.values())} total visits")

    return patient_histories

if __name__ == "__main__":
    # Test the staggered ABS implementation
    from simulation.config import SimulationConfig
    
    # Load configuration
    config = SimulationConfig.from_yaml("test_simulation")
    
    # Run simulation
    run_staggered_abs(config, patient_arrival_rate=20.0, verbose=True)