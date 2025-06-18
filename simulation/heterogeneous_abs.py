"""Heterogeneous Agent-Based Simulation for AMD treatment pathways.

This module extends the standard ABS engine to model patient heterogeneity based
on real-world outcome variability observed in studies like Seven-UP. Each patient
has individual characteristics that affect their treatment response and disease
progression throughout the simulation.

The heterogeneity is "baked in" from patient initialization rather than accumulated
through random walks, matching clinical observations.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import logging

from .abs import AgentBasedSimulation, Patient
from .patient_state import PatientState
from .heterogeneity_manager import HeterogeneityManager
from .base import Event

logger = logging.getLogger(__name__)


class HeterogeneousPatient(Patient):
    """
    Patient with heterogeneous characteristics.
    
    Extends base Patient class with individual response parameters that
    affect treatment outcomes and disease progression.
    """
    
    def __init__(self, patient_id: str, initial_state: PatientState, 
                 characteristics: Dict[str, Any], event_rng: np.random.RandomState):
        """
        Initialize heterogeneous patient.
        
        Parameters
        ----------
        patient_id : str
            Unique patient identifier
        initial_state : PatientState
            Initial clinical state
        characteristics : Dict[str, Any]
            Individual patient characteristics from HeterogeneityManager
        event_rng : np.random.RandomState
            RNG for catastrophic events
        """
        super().__init__(patient_id, initial_state)
        
        # Store heterogeneous characteristics
        self.characteristics = characteristics
        self.treatments_received = characteristics.get('treatments_received', 0)
        self.catastrophic_event_history = []
        self.event_rng = event_rng
        
        # Store baseline for correlation tracking
        self.baseline_va = initial_state.vision
        
        logger.debug(f"Created heterogeneous patient {patient_id} with trajectory class: "
                    f"{characteristics.get('trajectory_class')}")
    
    def update_vision(self, treatment_given: bool, weeks_elapsed: float,
                     catastrophic_events: Dict[str, Any]) -> float:
        """
        Update vision with heterogeneous response.
        
        Implements the heterogeneous vision change model incorporating
        individual patient characteristics, treatment resistance, and
        catastrophic events.
        
        Parameters
        ----------
        treatment_given : bool
            Whether treatment was administered
        weeks_elapsed : float
            Time since last vision update
        catastrophic_events : Dict[str, Any]
            Catastrophic event configurations
            
        Returns
        -------
        float
            New vision value (ETDRS letters)
        """
        current_va = self.state.vision
        
        # 1. Treatment effect with multiplier and resistance
        treatment_benefit = 0
        if treatment_given:
            # Base effect with individual multiplier
            base_effect = 5.0  # Base ETDRS letter gain
            treatment_multiplier = self.characteristics.get('treatment_effect_multiplier', 1.0)
            
            # Ceiling effect - reduced benefit as vision approaches maximum
            max_va = self.characteristics.get('max_achievable_va', 85)
            ceiling_factor = max(0, 1 - (current_va / max_va))
            
            treatment_benefit = base_effect * treatment_multiplier * ceiling_factor
            
            # Apply treatment resistance (tachyphylaxis)
            self.treatments_received += 1
            resistance_rate = self.characteristics.get('resistance_rate', 0.1)
            resistance_factor = np.exp(-resistance_rate * self.treatments_received)
            treatment_benefit *= resistance_factor
            
            logger.debug(f"Treatment benefit: {treatment_benefit:.2f} "
                        f"(multiplier={treatment_multiplier:.2f}, "
                        f"resistance={resistance_factor:.2f})")
        
        # 2. Disease progression with multiplier
        base_progression = -0.5  # Base letters lost per week
        progression_multiplier = self.characteristics.get('disease_progression_multiplier', 1.0)
        progression = base_progression * progression_multiplier * weeks_elapsed
        
        # 3. Measurement noise
        noise = self.event_rng.normal(0, 2)
        
        # 4. Check for catastrophic events
        catastrophic_drop = 0
        for event_type, event_config in catastrophic_events.items():
            prob_per_month = event_config.get('probability_per_month', 0)
            prob_per_week = prob_per_month / 4.33
            
            if self.event_rng.random() < prob_per_week * weeks_elapsed:
                # Event occurred - sample impact
                impact_dist = event_config.get('vision_impact', {})
                
                if impact_dist.get('distribution') == 'uniform':
                    impact = self.event_rng.uniform(
                        impact_dist.get('min', -30),
                        impact_dist.get('max', -10)
                    )
                elif impact_dist.get('distribution') == 'normal':
                    impact = self.event_rng.normal(
                        impact_dist.get('mean', -20),
                        impact_dist.get('std', 5)
                    )
                else:
                    impact = -20  # Default impact
                
                catastrophic_drop += impact
                
                # Record event
                self.catastrophic_event_history.append({
                    'time': self.state.current_time,
                    'event': event_type,
                    'impact': impact
                })
                
                logger.info(f"Catastrophic event '{event_type}' for patient {self.patient_id}: "
                           f"impact={impact:.1f}")
                
                # Update max achievable VA if specified
                if event_config.get('permanent') and 'max_va_reduction' in event_config:
                    reduction = event_config['max_va_reduction']
                    self.characteristics['max_achievable_va'] = max(
                        0,
                        self.characteristics.get('max_achievable_va', 85) - reduction
                    )
        
        # 5. Apply all changes
        new_va = current_va + treatment_benefit + progression + noise + catastrophic_drop
        
        # 6. Enforce bounds
        new_va = np.clip(new_va, 0, 85)
        
        # Update state
        self.state.vision = new_va
        
        return new_va
    
    def get_state_dict(self) -> Dict[str, Any]:
        """
        Get current state including heterogeneous characteristics.
        
        Returns
        -------
        Dict[str, Any]
            State dictionary with standard fields plus patient_characteristics
        """
        state_dict = super().get_state_dict()
        
        # Add heterogeneous characteristics for persistence
        state_dict['patient_characteristics'] = {
            'trajectory_class': self.characteristics.get('trajectory_class'),
            'treatment_effect_multiplier': self.characteristics.get('treatment_effect_multiplier'),
            'disease_progression_multiplier': self.characteristics.get('disease_progression_multiplier'),
            'max_achievable_va': self.characteristics.get('max_achievable_va'),
            'resistance_rate': self.characteristics.get('resistance_rate'),
            'treatments_received': self.treatments_received
        }
        
        return state_dict


class HeterogeneousABS(AgentBasedSimulation):
    """
    Agent-based simulation with patient heterogeneity.
    
    Extends the base ABS to model individual patient characteristics
    that affect treatment response and disease progression.
    """
    
    def __init__(self, config, start_date: datetime):
        """
        Initialize heterogeneous ABS.
        
        Parameters
        ----------
        config : SimulationConfig
            Configuration with heterogeneity section
        start_date : datetime
            Simulation start date
        """
        # Initialize base simulation
        super().__init__(config, start_date)
        
        # Extract heterogeneity configuration
        protocol_dict = self._get_protocol_dict(config)
        heterogeneity_config = protocol_dict.get('heterogeneity', {})
        
        # Create heterogeneity manager
        seed = getattr(config, 'random_seed', 42)
        self.heterogeneity_manager = HeterogeneityManager(heterogeneity_config, seed)
        
        # Store catastrophic events config for patient updates
        self.catastrophic_events = heterogeneity_config.get('catastrophic_events', {})
        
        # Validation tracking
        self.validation_metrics = {
            'patient_outcomes': [],
            'trajectory_assignments': {},
            'catastrophic_events': []
        }
        
        logger.info("HeterogeneousABS initialized with heterogeneity enabled")
    
    def _get_protocol_dict(self, config) -> Dict[str, Any]:
        """Extract protocol dictionary from configuration."""
        # Similar logic to factory
        if hasattr(config, 'protocol'):
            protocol = config.protocol
            if hasattr(protocol, 'to_dict'):
                return protocol.to_dict()
            elif hasattr(protocol, '__dict__'):
                return protocol.__dict__
            elif isinstance(protocol, dict):
                return protocol
        
        if hasattr(config, 'parameters'):
            params = config.parameters
            if isinstance(params, dict) and 'protocol' in params:
                return params['protocol']
        
        return {}
    
    def add_patient(self, patient_id: str, protocol_name: str):
        """
        Add a heterogeneous patient to the simulation.
        
        Creates a patient with individual characteristics that affect
        their treatment response throughout the simulation.
        
        Parameters
        ----------
        patient_id : str
            Unique patient identifier
        protocol_name : str
            Treatment protocol name
        """
        # Generate baseline VA from clinical model
        baseline_va = self.clinical_model.get_initial_vision()
        
        # Assign trajectory class
        trajectory_class = self.heterogeneity_manager.assign_trajectory_class()
        
        # Generate patient characteristics
        characteristics = self.heterogeneity_manager.generate_patient_characteristics(
            trajectory_class, baseline_va
        )
        
        # Create initial state
        initial_state = PatientState(patient_id, protocol_name, baseline_va, self.start_date)
        
        # Create heterogeneous patient with event RNG
        patient = HeterogeneousPatient(
            patient_id, initial_state, characteristics, 
            self.heterogeneity_manager.event_rng
        )
        
        # Store in agents
        self.agents[patient_id] = patient
        
        # Track for validation
        self.validation_metrics['trajectory_assignments'][patient_id] = trajectory_class
        
        logger.debug(f"Added heterogeneous patient {patient_id} with baseline VA={baseline_va:.1f}")
    
    def process_event(self, event: Event):
        """
        Process simulation event with heterogeneous vision updates.
        
        Overrides base method to use heterogeneous vision change model.
        
        Parameters
        ----------
        event : Event
            Event to process
        """
        if event.event_type == "visit":
            patient = self.agents[event.patient_id]
            
            # Check if treatment is given
            treatment_given = 'injection' in event.data.get('actions', [])
            
            # Calculate weeks since last visit
            if hasattr(patient, 'last_visit_time'):
                weeks_elapsed = (event.time - patient.last_visit_time).days / 7.0
            else:
                weeks_elapsed = 4.0  # Default for first visit
            
            patient.last_visit_time = event.time
            
            # Store old vision
            old_vision = patient.state.vision
            
            # Update vision with heterogeneous model
            new_vision = patient.update_vision(
                treatment_given, weeks_elapsed, self.catastrophic_events
            )
            
            # Process visit through standard state update
            visit_data = patient.state.process_visit(
                event.time, event.data['actions'], self.clinical_model
            )
            
            # Override vision with heterogeneous calculation
            visit_data['new_vision'] = new_vision
            patient.state.vision = new_vision
            
            # Create visit record with heterogeneous data
            visit_record = {
                'date': event.time,
                'type': visit_data['visit_type'],
                'actions': event.data['actions'],
                'baseline_vision': old_vision,
                'vision': new_vision,
                'disease_state': visit_data['disease_state'],
                'patient_characteristics': patient.get_state_dict()['patient_characteristics']
            }
            
            # Check for discontinuation (from base implementation)
            if len(patient.state.visit_history) > 0:
                last_state_visit = patient.state.visit_history[-1]
                if 'is_discontinuation_visit' in last_state_visit:
                    visit_record['is_discontinuation_visit'] = last_state_visit['is_discontinuation_visit']
                    visit_record['discontinuation_reason'] = last_state_visit.get('discontinuation_reason')
            
            patient.history.append(visit_record)
            
            # Schedule next visit
            next_visit = self.schedule_next_visit(event.patient_id, event.time)
            if next_visit:
                self.clock.schedule_event(next_visit)
    
    def get_results(self):
        """
        Get simulation results with validation metrics.
        
        Returns
        -------
        dict
            Standard results plus heterogeneity validation data
        """
        results = super().get_results()
        
        # Add validation metrics
        results['heterogeneity_validation'] = self._calculate_validation_metrics()
        
        return results
    
    def _calculate_validation_metrics(self) -> Dict[str, Any]:
        """Calculate metrics for Seven-UP validation."""
        metrics = {}
        
        # Collect final outcomes by patient
        outcomes = []
        for patient_id, patient in self.agents.items():
            if len(patient.history) > 0:
                initial_va = patient.baseline_va
                final_va = patient.state.vision
                change = final_va - initial_va
                
                outcomes.append({
                    'patient_id': patient_id,
                    'trajectory_class': patient.characteristics['trajectory_class'],
                    'initial_va': initial_va,
                    'final_va': final_va,
                    'change': change,
                    'treatments': patient.treatments_received,
                    'catastrophic_events': len(patient.catastrophic_event_history)
                })
        
        if outcomes:
            changes = [o['change'] for o in outcomes]
            metrics['mean_change'] = np.mean(changes)
            metrics['std_change'] = np.std(changes)
            metrics['n_patients'] = len(outcomes)
            
            # Proportion maintaining good vision
            final_vas = [o['final_va'] for o in outcomes]
            metrics['proportion_above_70'] = sum(v > 70 for v in final_vas) / len(final_vas)
            metrics['proportion_below_35'] = sum(v < 35 for v in final_vas) / len(final_vas)
            
            # Trajectory class distribution
            class_counts = {}
            for o in outcomes:
                tc = o['trajectory_class']
                class_counts[tc] = class_counts.get(tc, 0) + 1
            metrics['trajectory_distribution'] = {
                k: v/len(outcomes) for k, v in class_counts.items()
            }
        
        return metrics