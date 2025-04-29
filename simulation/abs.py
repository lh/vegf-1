"""Agent-Based Simulation (ABS) implementation for modeling AMD treatment pathways.

This module implements an agent-based simulation approach where each patient is modeled
as an autonomous agent following a treatment protocol. The simulation handles patient
visits, treatment decisions, and disease progression over time.

Notes
-----
Key Features:
- Individual patient agents with unique states
- Protocol-driven treatment decisions
- Vision progression modeling
- Clinic scheduling constraints
- Detailed visit history tracking
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from .base import BaseSimulation, Event
from .patient_state import PatientState
from .clinical_model import ClinicalModel
from .scheduler import ClinicScheduler

class Patient:
    """Patient agent in the simulation.
    
    Represents a single patient in the agent-based simulation, maintaining their
    current state and history of visits and treatments.

    Parameters
    ----------
    patient_id : str
        Unique identifier for the patient
    initial_state : PatientState
        Initial clinical and treatment state including:
        - current_vision: ETDRS letters
        - disease_state: AMD stage
        - treatment_history: List of previous treatments
        - protocol_name: Treatment protocol being followed

    Attributes
    ----------
    patient_id : str
        Unique identifier for the patient
    state : PatientState
        Current state of the patient including:
        - vision: Current visual acuity
        - disease_state: Current AMD stage
        - next_visit_interval: Weeks until next visit
        - treatment_history: List of treatments received
    history : list
        List of historical visit records containing:
        - date: Visit date
        - type: Visit type
        - actions: Procedures performed
        - vision: Visual acuity at visit
        - disease_state: AMD stage at visit

    Examples
    --------
    >>> patient = Patient(
    ...     patient_id="pat123",
    ...     initial_state=PatientState(...)
    ... )
    """

    def __init__(self, patient_id: str, initial_state: PatientState):
        self.patient_id = patient_id
        self.state = initial_state
        self.history = []

    def get_state_dict(self) -> Dict[str, Any]:
        """Get the current state as a dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing:
            - 'patient_id': str
            - 'current_vision': float
            - 'disease_state': str
            - 'treatment_history': List[Dict]
            - 'next_visit_interval': int
            - 'last_visit_date': datetime

        Notes
        -----
        The returned dictionary is suitable for serialization and analysis.
        """
        return self.state.state

from .base import BaseSimulation, Event, SimulationClock

class AgentBasedSimulation(BaseSimulation):
    """Agent-based simulation for AMD treatment pathways.

    Implements a discrete-event simulation where patients are modeled as individual
    agents following treatment protocols. The simulation handles scheduling of visits,
    treatment decisions, and disease progression.

    Parameters
    ----------
    config : Any
        Configuration object containing:
        - protocol_parameters: Treatment protocol definitions
        - clinical_model_params: Disease progression parameters
        - des_params: Scheduling constraints
    start_date : datetime
        Start date for the simulation

    Attributes
    ----------
    start_date : datetime
        Start date of the simulation
    agents : Dict[str, Patient]
        Dictionary mapping patient IDs to Patient agents
    clinical_model : ClinicalModel
        Model for disease progression and treatment effects
    scheduler : ClinicScheduler
        Scheduler for clinic visits with attributes:
        - daily_capacity: Max patients per day
        - days_per_week: Clinic operating days
    clock : SimulationClock
        Simulation clock managing event queue

    Examples
    --------
    >>> sim = AgentBasedSimulation(
    ...     config=load_config(),
    ...     start_date=datetime(2023, 1, 1)
    ... )
    >>> sim.add_patient("pat123", "treat_and_extend")
    >>> sim.run(datetime(2024, 1, 1))
    """

    def __init__(self, config, start_date: datetime):
        super().__init__(config)
        self.start_date = start_date
        self.agents: Dict[str, Patient] = {}
        self.clinical_model = ClinicalModel(config)
        # Default scheduler parameters for ABS
        self.scheduler = ClinicScheduler(20, 5)  # 20 patients per day, 5 days per week
        self.clock = SimulationClock(start_date)
        sim_params = config.get_simulation_params()
        if 'end_date' in sim_params:
            self.clock.end_date = sim_params['end_date']

    def add_patient(self, patient_id: str, protocol_name: str):
        """
        Add a new patient to the simulation.

        Parameters
        ----------
        patient_id : str
            Unique identifier for the patient
        protocol_name : str
            Name of the treatment protocol to follow

        Notes
        -----
        Creates a new patient agent with initial state and adds them to the simulation.
        """
        initial_state = PatientState(patient_id, protocol_name, self.clinical_model.get_initial_vision(), self.start_date)
        self.agents[patient_id] = Patient(patient_id, initial_state)

    def run(self, end_date: datetime):
        """
        Run the simulation until the specified end date.

        Parameters
        ----------
        end_date : datetime
            Date to end the simulation

        Notes
        -----
        Processes events chronologically until reaching the end date or running out of events.
        """
        while self.clock.current_time <= end_date:
            event = self.clock.get_next_event()
            if event is None:
                break
            self.process_event(event)
        print(f"Simulation completed. End time: {self.clock.current_time}")

    def process_event(self, event: Event):
        """
        Process a simulation event.

        Parameters
        ----------
        event : Event
            Event to process

        Notes
        -----
        Handles visit events by updating patient state, recording visit data,
        and scheduling the next visit according to the protocol.
        """
        if event.event_type == "visit":
            patient = self.agents[event.patient_id]
            visit_data = patient.state.process_visit(event.time, event.data['actions'], self.clinical_model)
            
            visit_record = {
                'date': event.time,
                'type': visit_data['visit_type'],
                'actions': event.data['actions'],
                'baseline_vision': visit_data['baseline_vision'],
                'vision': visit_data['new_vision'],
                'disease_state': visit_data['disease_state']
            }
            patient.history.append(visit_record)
            
            # Schedule next visit based on protocol
            next_visit = self.schedule_next_visit(event.patient_id, event.time)
            if next_visit:
                self.clock.schedule_event(next_visit)

    def schedule_next_visit(self, patient_id: str, current_date: datetime) -> Event:
        """
        Schedule the next visit for a patient.

        Parameters
        ----------
        patient_id : str
            ID of the patient to schedule
        current_date : datetime
            Current date in the simulation

        Returns
        -------
        Event
            Next visit event for the patient

        Notes
        -----
        Uses a fixed schedule for the first year (weeks 0, 4, 9, 18, 27, 36, 44, 52)
        and then switches to intervals based on the patient's state.
        """
        patient = self.agents[patient_id]
        treatment_start = patient.state.state['treatment_start']
        weeks_since_start = (current_date - treatment_start).days // 7
        
        fixed_schedule = [0, 4, 9, 18, 27, 36, 44, 52]
        if weeks_since_start < 52:
            next_week = next(week for week in fixed_schedule if week > weeks_since_start)
            next_visit_date = treatment_start + timedelta(weeks=next_week)
        else:
            next_visit_interval = patient.state.next_visit_interval
            next_visit_date = current_date + timedelta(weeks=next_visit_interval)
        
        return Event(
            time=next_visit_date,
            event_type="visit",
            patient_id=patient_id,
            data={
                "visit_type": "injection_visit",
                "actions": ["vision_test", "oct_scan", "injection"],
                "decisions": ["nurse_vision_check", "doctor_treatment_decision"]
            },
            priority=1
        )

    def get_results(self):
        """
        Get the simulation results.

        Returns
        -------
        dict
            Dictionary containing patient agents and event history

        Notes
        -----
        Returns all patient data and the complete event history for analysis.
        """
        return {
            'patients': self.agents,
            'events': self.clock.event_history
        }
