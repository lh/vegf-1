from typing import Dict, Any
from datetime import datetime, timedelta
from .base import BaseSimulation, Event
from .patient_state import PatientState
from .clinical_model import ClinicalModel
from .scheduler import ClinicScheduler

class Patient:
    def __init__(self, patient_id: str, initial_state: PatientState):
        self.patient_id = patient_id
        self.state = initial_state
        self.history = []

    def get_state_dict(self):
        return self.state.state

from .base import BaseSimulation, Event, SimulationClock

class AgentBasedSimulation(BaseSimulation):
    def __init__(self, config, start_date: datetime):
        super().__init__(config)
        self.start_date = start_date
        self.agents: Dict[str, Patient] = {}
        self.clinical_model = ClinicalModel(config)
        des_params = config.get_des_params()
        self.scheduler = ClinicScheduler(des_params['daily_capacity'], des_params['days_per_week'])
        self.clock = SimulationClock(start_date)

    def add_patient(self, patient_id: str, protocol_name: str):
        initial_state = PatientState(patient_id, protocol_name, self.clinical_model.get_initial_vision(), self.start_date)
        self.agents[patient_id] = Patient(patient_id, initial_state)

    def run(self, end_date: datetime):
        while self.clock.current_time <= end_date:
            event = self.clock.get_next_event()
            if event is None:
                break
            self.process_event(event)
        print(f"Simulation completed. End time: {self.clock.current_time}")

    def process_event(self, event: Event):
        if event.event_type == "visit":
            patient = self.agents[event.patient_id]
            visit_data = patient.state.process_visit(event.time, event.data['actions'], self.clinical_model)
            visit_record = {
                'date': event.time,
                'type': event.data.get('visit_type', 'regular_visit'),
                'actions': event.data['actions'],
                'vision': patient.state.current_vision,
                'disease_state': patient.state.state['disease_state']
            }
            patient.history.append(visit_record)
            # Schedule next visit based on protocol
            next_visit = self.schedule_next_visit(event.patient_id, event.time)
            if next_visit:
                self.clock.schedule_event(next_visit)

    def schedule_next_visit(self, patient_id: str, current_date: datetime) -> Event:
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
        return {
            'patients': self.agents,
            'events': self.clock.event_history
        }
