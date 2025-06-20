"""
Simulation runner with full parameter audit trail.

NO DEFAULTS - all parameters must come from protocol specification.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.core.disease_model import DiseaseModel
from simulation_v2.core.disease_model_time_based import DiseaseModelTimeBased
from simulation_v2.core.protocol import StandardProtocol
from simulation_v2.core.patient import Patient
from simulation_v2.engines.abs_engine import ABSEngine, SimulationResults
from simulation_v2.engines.des_engine import DESEngine
from simulation_v2.engines.abs_engine_time_based_with_specs import ABSEngineTimeBasedWithSpecs
from simulation_v2.models.baseline_vision_distributions import DistributionFactory
from simulation_v2.serialization.parquet_writer import serialize_patient_visits
from simulation_v2.clinical_improvements import ClinicalImprovements


class SimulationRunner:
    """Run simulation with full parameter audit trail."""
    
    def __init__(self, protocol_spec: ProtocolSpecification):
        """
        Initialize runner with protocol specification.
        
        Args:
            protocol_spec: Complete protocol specification
        """
        self.spec = protocol_spec
        self.audit_log: List[Dict[str, Any]] = []
        
        # Initialize clinical improvements if specified and enabled
        self.clinical_improvements = None
        if (hasattr(self.spec, 'clinical_improvements') and 
            self.spec.clinical_improvements and 
            self.spec.clinical_improvements.get('enabled')):
            # Import here to avoid circular dependency
            from simulation_v2.clinical_improvements import ClinicalImprovements
            
            # Create improvements config from protocol
            improvements_data = self.spec.clinical_improvements.copy()
            # Remove the 'enabled' flag as it's not part of the config class
            improvements_data.pop('enabled', None)
            
            # Create config with protocol parameters
            self.clinical_improvements = ClinicalImprovements()
            # Update with protocol-specific settings
            for key, value in improvements_data.items():
                if hasattr(self.clinical_improvements, key):
                    setattr(self.clinical_improvements, key, value)
            
            # Log that improvements are enabled
            self.audit_log.append({
                'event': 'clinical_improvements_enabled',
                'timestamp': datetime.now().isoformat(),
                'improvements': improvements_data
            })
        
        # Log specification load
        self.audit_log.append({
            'event': 'protocol_loaded',
            'timestamp': datetime.now().isoformat(),
            'protocol': self.spec.to_audit_log()
        })
        
    def run(
        self, 
        engine_type: str,
        n_patients: int, 
        duration_years: float, 
        seed: int
    ) -> SimulationResults:
        """
        Run simulation with complete logging.
        
        Args:
            engine_type: 'abs' or 'des'
            n_patients: Number of patients to simulate
            duration_years: Simulation duration in years
            seed: Random seed for reproducibility
            
        Returns:
            SimulationResults with patient histories and statistics
        """
        # Validate parameters
        if n_patients < 0:
            raise ValueError(f"Number of patients must be non-negative, got {n_patients}")
        if duration_years <= 0:
            raise ValueError(f"Duration must be positive, got {duration_years}")
            
        # Log simulation start
        self.audit_log.append({
            'event': 'simulation_start',
            'timestamp': datetime.now().isoformat(),
            'engine_type': engine_type,
            'n_patients': n_patients,
            'duration_years': duration_years,
            'seed': seed,
            'protocol_name': self.spec.name,
            'protocol_version': self.spec.version,
            'protocol_checksum': self.spec.checksum
        })
        
        # Check if this is a time-based model
        is_time_based = False
        if hasattr(self.spec, 'model_type'):
            is_time_based = self.spec.model_type == 'time_based'
        elif hasattr(self.spec, 'transition_model'):
            is_time_based = self.spec.transition_model == 'fortnightly'
        
        # Create components from spec (NO DEFAULTS)
        if is_time_based:
            # Create time-based disease model
            params_dir = Path(self.spec.source_file).parent / 'parameters'
            disease_model = DiseaseModelTimeBased.from_parameter_files(
                params_dir=params_dir,
                seed=seed
            )
        else:
            # Create standard per-visit model
            disease_model = DiseaseModel(
                transition_probabilities=self.spec.disease_transitions,
                treatment_effect_multipliers=self.spec.treatment_effect_on_transitions,
                seed=seed
            )
        
        protocol = StandardProtocol(
            min_interval_days=self.spec.min_interval_days,
            max_interval_days=self.spec.max_interval_days,
            extension_days=self.spec.extension_days,
            shortening_days=self.spec.shortening_days
        )
        
        # Create appropriate engine with clinical improvements
        if engine_type.lower() == 'abs':
            if is_time_based:
                engine = ABSEngineTimeBasedWithSpecs(
                    disease_model=disease_model,
                    protocol=protocol,
                    protocol_spec=self.spec,
                    n_patients=n_patients,
                    seed=seed,
                    clinical_improvements=self.clinical_improvements
                )
            else:
                engine = ABSEngineWithSpecs(
                    disease_model=disease_model,
                    protocol=protocol,
                    protocol_spec=self.spec,
                    n_patients=n_patients,
                    seed=seed,
                    clinical_improvements=self.clinical_improvements
                )
        elif engine_type.lower() == 'des':
            if is_time_based:
                raise NotImplementedError("DES engine not yet implemented for time-based models")
            else:
                engine = DESEngineWithSpecs(
                    disease_model=disease_model,
                    protocol=protocol,
                    protocol_spec=self.spec,
                    n_patients=n_patients,
                    seed=seed,
                    clinical_improvements=self.clinical_improvements
                )
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
            
        # Run simulation
        results = engine.run(duration_years)
        
        # Log completion
        self.audit_log.append({
            'event': 'simulation_complete',
            'timestamp': datetime.now().isoformat(),
            'total_injections': results.total_injections,
            'final_vision_mean': results.final_vision_mean,
            'final_vision_std': results.final_vision_std,
            'discontinuation_rate': results.discontinuation_rate,
            'patient_count': results.patient_count
        })
        
        return results
    
    def save_audit_trail(self, filepath: Path) -> None:
        """
        Save complete audit trail to JSON file.
        
        Args:
            filepath: Path to save audit trail
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.audit_log, f, indent=2)
            
        # Log save event
        self.audit_log.append({
            'event': 'audit_trail_saved',
            'timestamp': datetime.now().isoformat(),
            'filepath': str(filepath)
        })


class ABSEngineWithSpecs(ABSEngine):
    """ABS engine that uses protocol specifications."""
    
    def __init__(
        self,
        disease_model: DiseaseModel,
        protocol: StandardProtocol,
        protocol_spec: ProtocolSpecification,
        n_patients: int,
        seed: Optional[int] = None,
        clinical_improvements: Optional[ClinicalImprovements] = None
    ):
        """Initialize with protocol spec for parameters."""
        self.protocol_spec = protocol_spec
        self.clinical_improvements = clinical_improvements
        
        # Create baseline vision distribution from spec
        baseline_vision_distribution = DistributionFactory.create_from_protocol_spec(protocol_spec)
        
        # Call parent init with n_patients (Fixed Total Mode)
        super().__init__(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=n_patients,
            seed=seed,
            baseline_vision_distribution=baseline_vision_distribution
        )
        
    # Note: _sample_baseline_vision is now handled by parent class using baseline_vision_distribution
    
    def _create_patient_with_improvements(self, patient_id: str, baseline_vision: int, 
                                         enrollment_date: datetime = None) -> Patient:
        """Create patient with optional clinical improvements wrapper."""
        # Create base patient
        patient = Patient(
            patient_id=patient_id,
            baseline_vision=baseline_vision,
            visit_metadata_enhancer=self.visit_metadata_enhancer,
            enrollment_date=enrollment_date
        )
        
        # Apply clinical improvements wrapper if enabled
        if self.clinical_improvements:
            from ..clinical_improvements import ImprovedPatientWrapper
            patient = ImprovedPatientWrapper(patient, self.clinical_improvements)
            
        return patient
        
    def _calculate_vision_change(
        self, 
        old_state: 'DiseaseState',
        new_state: 'DiseaseState',
        treated: bool
    ) -> int:
        """Calculate vision change based on protocol spec."""
        # Build scenario key
        state_name = new_state.name.lower()
        treatment_status = 'treated' if treated else 'untreated'
        scenario_key = f"{state_name}_{treatment_status}"
        
        # Get parameters from spec
        if scenario_key in self.protocol_spec.vision_change_model:
            params = self.protocol_spec.vision_change_model[scenario_key]
            change = int(random.gauss(params['mean'], params['std']))
            return change
        else:
            # This should never happen if spec is validated properly
            raise ValueError(f"Vision change scenario not defined: {scenario_key}")
            
    def _should_discontinue(self, patient: Patient, current_date: datetime) -> bool:
        """Discontinuation logic based on protocol spec."""
        rules = self.protocol_spec.discontinuation_rules
        
        # Poor vision check
        if patient.current_vision < rules['poor_vision_threshold']:
            if random.random() < rules['poor_vision_probability']:
                return True
                
        # High injection count check
        if patient.injection_count > rules['high_injection_count']:
            if random.random() < rules['high_injection_probability']:
                return True
                
        # Long treatment duration check
        if len(patient.visit_history) > 0:
            first_visit = patient.visit_history[0]['date']
            months_treated = (current_date - first_visit).days / 30.44
            if months_treated > rules['long_treatment_months']:
                if random.random() < rules['long_treatment_probability']:
                    return True
                    
        return False
    
    def run(self, duration_years: float, start_date: Optional[datetime] = None) -> SimulationResults:
        """
        Override run to use clinical improvements for patient creation.
        
        This is a minimal override that just replaces the patient creation line.
        """
        if start_date is None:
            start_date = datetime(2024, 1, 1)
            
        end_date = start_date + timedelta(days=int(duration_years * 365.25))
        
        # Generate patient arrival schedule
        self.patient_arrival_schedule = self._generate_arrival_schedule(start_date, end_date)
        
        # Schedule visits for existing and arriving patients
        visit_schedule: Dict[str, datetime] = {}
            
        # Run simulation
        current_date = start_date
        total_injections = 0
        arrival_index = 0  # Track position in arrival schedule
        
        while current_date <= end_date:
            # Process new patient arrivals for today
            while (arrival_index < len(self.patient_arrival_schedule) and 
                   self.patient_arrival_schedule[arrival_index][0].date() <= current_date.date()):
                arrival_date, patient_id = self.patient_arrival_schedule[arrival_index]
                
                # Create new patient WITH IMPROVEMENTS
                baseline_vision = self._sample_baseline_vision()
                patient = self._create_patient_with_improvements(
                    patient_id,
                    baseline_vision,
                    enrollment_date=arrival_date
                )
                self.patients[patient_id] = patient
                self.enrollment_dates[patient_id] = arrival_date
                
                # Schedule initial visit for start of next day after enrollment
                next_day = arrival_date.date() + timedelta(days=1)
                visit_schedule[patient_id] = datetime.combine(next_day, datetime.min.time())
                
                arrival_index += 1
            
            # Process patients scheduled for today
            patients_today = [
                pid for pid, visit_date in visit_schedule.items()
                if visit_date.date() == current_date.date()
            ]
            
            for patient_id in patients_today:
                patient = self.patients[patient_id]
                
                if patient.is_discontinued:
                    # Skip discontinued patients
                    continue
                    
                # Disease progression
                new_state = self.disease_model.progress(
                    patient.current_state,
                    days_since_injection=patient.days_since_last_injection_at(current_date)
                )
                
                # Treatment decision
                should_treat = self.protocol.should_treat(patient, current_date)
                
                # Vision change (simplified model)
                vision_change = self._calculate_vision_change(
                    patient.current_state,
                    new_state,
                    should_treat
                )
                new_vision = max(0, min(100, patient.current_vision + vision_change))
                
                # Record visit
                patient.record_visit(
                    date=current_date,
                    disease_state=new_state,
                    treatment_given=should_treat,
                    vision=new_vision
                )
                
                if should_treat:
                    total_injections += 1
                    
                # Schedule next visit
                next_visit = self.protocol.next_visit_date(patient, current_date, should_treat)
                visit_schedule[patient_id] = next_visit
                
                # Check for discontinuation (simplified)
                if self._should_discontinue(patient, current_date):
                    patient.discontinue(current_date, "planned")
                    
            # Advance time
            current_date += timedelta(days=1)
            
        # Calculate final statistics
        final_visions = [p.current_vision for p in self.patients.values()]
        discontinued = sum(1 for p in self.patients.values() if p.is_discontinued)
        actual_patient_count = len(self.patients)
        
        # Handle edge case of zero patients
        if actual_patient_count == 0:
            final_vision_mean = 0.0
            final_vision_std = 0.0
            discontinuation_rate = 0.0
        else:
            final_vision_mean = sum(final_visions) / len(final_visions)
            final_vision_std = self._calculate_std(final_visions)
            discontinuation_rate = discontinued / actual_patient_count
        
        return SimulationResults(
            total_injections=total_injections,
            patient_histories=self.patients,
            final_vision_mean=final_vision_mean,
            final_vision_std=final_vision_std,
            discontinuation_rate=discontinuation_rate
        )


class DESEngineWithSpecs(DESEngine):
    """DES engine that uses protocol specifications."""
    
    def __init__(
        self,
        disease_model: DiseaseModel,
        protocol: StandardProtocol,
        protocol_spec: ProtocolSpecification,
        n_patients: int,
        seed: Optional[int] = None,
        clinical_improvements: Optional[ClinicalImprovements] = None
    ):
        """Initialize with protocol spec for parameters."""
        self.protocol_spec = protocol_spec
        self.clinical_improvements = clinical_improvements
        
        # Create baseline vision distribution from spec
        baseline_vision_distribution = DistributionFactory.create_from_protocol_spec(protocol_spec)
        
        # Initialize parent with n_patients (Fixed Total Mode)
        super().__init__(
            disease_model=disease_model,
            protocol=protocol,
            n_patients=n_patients,
            seed=seed,
            baseline_vision_distribution=baseline_vision_distribution
        )
        
    # Note: _sample_baseline_vision is now handled by parent class using baseline_vision_distribution
        
    def _calculate_vision_change(
        self, 
        old_state: 'DiseaseState',
        new_state: 'DiseaseState',
        treated: bool
    ) -> int:
        """Calculate vision change based on protocol spec."""
        # Build scenario key
        state_name = new_state.name.lower()
        treatment_status = 'treated' if treated else 'untreated'
        scenario_key = f"{state_name}_{treatment_status}"
        
        # Get parameters from spec
        if scenario_key in self.protocol_spec.vision_change_model:
            params = self.protocol_spec.vision_change_model[scenario_key]
            change = int(random.gauss(params['mean'], params['std']))
            return change
        else:
            raise ValueError(f"Vision change scenario not defined: {scenario_key}")
            
    def _should_discontinue(self, patient: Patient, current_date: datetime) -> bool:
        """Discontinuation logic based on protocol spec."""
        rules = self.protocol_spec.discontinuation_rules
        
        # Same logic as ABS engine
        if patient.current_vision < rules['poor_vision_threshold']:
            if random.random() < rules['poor_vision_probability']:
                return True
                
        if patient.injection_count > rules['high_injection_count']:
            if random.random() < rules['high_injection_probability']:
                return True
                
        if len(patient.visit_history) > 0:
            first_visit = patient.visit_history[0]['date']
            months_treated = (current_date - first_visit).days / 30.44
            if months_treated > rules['long_treatment_months']:
                if random.random() < rules['long_treatment_probability']:
                    return True
                    
        return False