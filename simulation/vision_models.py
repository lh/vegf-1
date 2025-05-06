"""Vision change models for AMD simulations.

This module provides different implementations of vision change models for
AMD disease progression simulations. It allows for consistent vision change
calculations across different simulation types (ABS and DES).

Classes:
    BaseVisionModel: Abstract base class for vision change models
    SimplifiedVisionModel: Simple normally distributed vision change model
    RealisticVisionModel: More realistic vision change model with natural decline and fluctuations
    LiteratureBasedVisionModel: Vision change model based on literature data
    ClinicalTrialVisionModel: Vision change model based on clinical trial data

Notes:
    This module centralizes vision change logic to ensure consistency
    across different simulation implementations (ABS and DES).
"""

import numpy as np
from abc import ABC, abstractmethod
from simulation.clinical_model import DiseaseState

class BaseVisionModel(ABC):
    """Base class for vision change models.
    
    This abstract base class defines the interface for all vision change models.
    Concrete implementations must provide a calculate_vision_change method.
    """
    
    @abstractmethod
    def calculate_vision_change(self, state, actions, phase):
        """
        Calculate vision change based on patient state.
        
        Parameters
        ----------
        state : dict
            Patient state dictionary containing:
            - current_vision: Current visual acuity
            - fluid_detected: Whether fluid was detected at last visit
            - treatments_in_phase: Number of treatments in current phase
            - interval: Current treatment interval in weeks
            - treatment_status: Dictionary with treatment status information
        actions : list
            Actions performed during the visit (e.g., ["vision_test", "oct_scan", "injection"])
        phase : str
            Current treatment phase ('loading' or 'maintenance')
            
        Returns
        -------
        tuple
            (vision_change, fluid_detected)
            - vision_change: Change in visual acuity (ETDRS letters)
            - fluid_detected: Whether fluid was detected at this visit
        """
        pass

class SimplifiedVisionModel(BaseVisionModel):
    """Simple normally distributed vision change model.
    
    This model uses fixed normal distributions for vision change,
    with different parameters for loading and maintenance phases.
    This matches the model used in the original treat_and_extend_des.py.
    
    Parameters
    ----------
    config : simulation.config.SimulationConfig, optional
        Configuration object, by default None
        
    Attributes
    ----------
    loading_params : dict
        Parameters for loading phase vision change:
        - mean: Mean vision change in ETDRS letters
        - std: Standard deviation of vision change
    maintenance_params : dict
        Parameters for maintenance phase vision change:
        - mean: Mean vision change in ETDRS letters
        - std: Standard deviation of vision change
    fluid_detection_prob : float
        Probability of fluid detection (0.0-1.0)
    """
    
    def __init__(self, config=None):
        """
        Initialize the model with optional configuration.
        
        Parameters
        ----------
        config : simulation.config.SimulationConfig, optional
            Configuration object, by default None
        """
        self.config = config
        
        # Default parameters
        self.loading_params = {
            'mean': 6.0,  # Higher mean for loading phase
            'std': 1.5
        }
        
        self.maintenance_params = {
            'mean': 2.0,  # Lower mean for maintenance phase
            'std': 1.0
        }
        
        self.fluid_detection_prob = 0.3  # 30% chance of fluid detection
        
        # Override defaults with configuration if provided
        if config:
            vision_params = config.get_vision_params()
            if vision_params and 'vision_model' in vision_params:
                model_params = vision_params['vision_model']
                
                if 'loading_phase' in model_params:
                    self.loading_params = model_params['loading_phase']
                
                if 'maintenance_phase' in model_params:
                    self.maintenance_params = model_params['maintenance_phase']
                
                if 'fluid_detection_probability' in model_params:
                    self.fluid_detection_prob = model_params['fluid_detection_probability']
        
    def calculate_vision_change(self, state, actions, phase):
        """
        Calculate vision change based on patient state.
        
        Parameters
        ----------
        state : dict
            Patient state dictionary
        actions : list
            Actions performed during the visit
        phase : str
            Current treatment phase ('loading' or 'maintenance')
            
        Returns
        -------
        tuple
            (vision_change, fluid_detected)
        """
        # Only apply vision improvement if receiving an injection
        if "injection" not in actions:
            return 0.0, state.get("fluid_detected", True)
        
        # Select appropriate parameters based on phase
        if phase == "loading":
            params = self.loading_params
        else:
            params = self.maintenance_params
        
        # Calculate vision change
        vision_change = np.random.normal(params['mean'], params['std'])
        
        # Determine if fluid was detected
        fluid_detected = np.random.random() < self.fluid_detection_prob
        
        return vision_change, fluid_detected

class LiteratureBasedVisionModel(BaseVisionModel):
    """Vision change model based on literature data.
    
    This model uses the clinical_model's simulate_vision_change method,
    which implements a more complex vision change model based on 
    literature data and disease states.
    
    Parameters
    ----------
    clinical_model : simulation.clinical_model.ClinicalModel
        Clinical model for disease progression and treatment effects
        
    Attributes
    ----------
    clinical_model : simulation.clinical_model.ClinicalModel
        Clinical model used for vision change calculations
    """
    
    def __init__(self, clinical_model):
        """
        Initialize the model with a clinical model.
        
        Parameters
        ----------
        clinical_model : simulation.clinical_model.ClinicalModel
            Clinical model for disease progression and treatment effects
        """
        self.clinical_model = clinical_model
    
    def calculate_vision_change(self, state, actions, phase):
        """
        Calculate vision change based on patient state.
        
        Parameters
        ----------
        state : dict
            Patient state dictionary
        actions : list
            Actions performed during the visit
        phase : str
            Current treatment phase ('loading' or 'maintenance')
            
        Returns
        -------
        tuple
            (vision_change, fluid_detected)
        """
        # Create state dictionary for clinical model
        clinical_state = {
            "disease_state": "ACTIVE" if state.get("fluid_detected", True) else "STABLE",
            "injections": state.get("treatments_in_phase", 0) if "injection" in actions else 0,
            "last_recorded_injection": state.get("treatments_in_phase", 0) - 1 if "injection" in actions else state.get("treatments_in_phase", 0),
            "weeks_since_last_injection": 0 if "injection" in actions else state.get("interval", 4),
            "current_vision": state.get("current_vision", 65),
            "treatment_status": state.get("treatment_status", {"active": True})
        }
        
        # Simulate vision change using clinical model
        vision_change, new_disease_state = self.clinical_model.simulate_vision_change(clinical_state)
        
        # Determine if fluid was detected based on disease state
        fluid_detected = new_disease_state in [DiseaseState.ACTIVE, DiseaseState.HIGHLY_ACTIVE]
        
        return vision_change, fluid_detected

class RealisticVisionModel(BaseVisionModel):
    """Realistic vision change model with natural decline and fluctuations.
    
    This model improves upon SimplifiedVisionModel by adding:
    1. Natural vision decline over time (disease progression)
    2. Vision fluctuations (test-retest variability)
    3. Ceiling effects on vision improvement
    4. Patient-specific response factors
    5. Non-responder probability
    6. Vision decline between injections
    
    Parameters
    ----------
    config : simulation.config.SimulationConfig, optional
        Configuration object, by default None
        
    Attributes
    ----------
    loading_params : dict
        Parameters for loading phase vision change:
        - mean: Mean vision change in ETDRS letters
        - std: Standard deviation of vision change
    maintenance_params : dict
        Parameters for maintenance phase vision change:
        - mean: Mean vision change in ETDRS letters
        - std: Standard deviation of vision change
    non_responder_prob : float
        Probability that a patient is a non-responder to treatment
    natural_decline_rate : float
        Rate of vision decline per week without treatment
    vision_fluctuation : float
        Standard deviation of random vision fluctuations
    ceiling_vision : float
        Maximum vision level (acts as ceiling for improvements)
    patient_response_factors : dict
        Dictionary of patient-specific response factors
    fluid_detection_prob : float
        Probability of fluid detection (0.0-1.0)
    """
    
    def __init__(self, config=None):
        """
        Initialize the model with optional configuration.
        
        Parameters
        ----------
        config : simulation.config.SimulationConfig, optional
            Configuration object, by default None
        """
        self.config = config
        
        # Default parameters with more realistic values
        self.loading_params = {
            'mean': 5.0,  # Slightly lower loading phase improvement
            'std': 2.5    # Higher variability
        }
        
        self.maintenance_params = {
            'mean': 1.2,  # Lower maintenance phase improvement
            'std': 1.5    # Higher variability
        }
        
        # Add new parameters for realism
        self.non_responder_prob = 0.15  # 15% of patients don't respond well
        self.natural_decline_rate = 0.15  # Letters lost per week without treatment
        self.vision_fluctuation = 1.0   # Random fluctuation in vision measurements
        self.ceiling_vision = 85.0      # Maximum possible vision
        self.patient_response_factors = {}  # Will be initialized per patient
        self.fluid_detection_prob = 0.3  # 30% chance of fluid detection
        
        # Override defaults with configuration if provided
        if config:
            vision_params = config.get_vision_params()
            if vision_params and 'vision_model' in vision_params:
                model_params = vision_params['vision_model']
                
                if 'loading_phase' in model_params:
                    self.loading_params = model_params['loading_phase']
                
                if 'maintenance_phase' in model_params:
                    self.maintenance_params = model_params['maintenance_phase']
                
                if 'non_responder_probability' in model_params:
                    self.non_responder_prob = model_params['non_responder_probability']
                
                if 'natural_decline_rate' in model_params:
                    self.natural_decline_rate = model_params['natural_decline_rate']
                
                if 'vision_fluctuation' in model_params:
                    self.vision_fluctuation = model_params['vision_fluctuation']
                
                if 'ceiling_vision' in model_params:
                    self.ceiling_vision = model_params['ceiling_vision']
                
                if 'fluid_detection_probability' in model_params:
                    self.fluid_detection_prob = model_params['fluid_detection_probability']
    
    def _get_patient_response_factor(self, patient_id):
        """
        Get patient-specific response factor, creating it if it doesn't exist.
        
        Parameters
        ----------
        patient_id : str
            Patient identifier
            
        Returns
        -------
        float
            Patient-specific response factor (0.2-1.5)
        """
        if patient_id not in self.patient_response_factors:
            # Determine if patient is a non-responder
            is_non_responder = np.random.random() < self.non_responder_prob
            
            if is_non_responder:
                # Non-responders have low response factors (0.2-0.5)
                factor = np.random.uniform(0.2, 0.5)
            else:
                # Normal responders have factors from 0.6-1.5
                factor = np.random.uniform(0.6, 1.5)
            
            self.patient_response_factors[patient_id] = factor
        
        return self.patient_response_factors[patient_id]
    
    def calculate_vision_change(self, state, actions, phase):
        """
        Calculate vision change based on patient state with realistic dynamics.
        
        Parameters
        ----------
        state : dict
            Patient state dictionary with these required keys:
            - current_vision: Current visual acuity
            - fluid_detected: Whether fluid was detected at last visit
            - treatments_in_phase: Number of treatments in current phase
            - interval: Current treatment interval in weeks
            - treatment_status: Dictionary with treatment status information
            - patient_id: Patient identifier (if missing, will use random response factor)
        actions : list
            Actions performed during the visit
        phase : str
            Current treatment phase ('loading' or 'maintenance')
            
        Returns
        -------
        tuple
            (vision_change, fluid_detected)
        """
        # Extract current vision and patient ID
        current_vision = state.get("current_vision", 65)
        patient_id = state.get("patient_id", "default")
        interval = state.get("interval", 4)  # Weeks since last visit
        
        # Add random fluctuation (measurement noise)
        fluctuation = np.random.normal(0, self.vision_fluctuation)
        
        # Calculate natural disease progression (vision decline)
        # Only apply in maintenance phase and if no injection given
        natural_decline = 0.0
        if phase == "maintenance" and "injection" not in actions:
            natural_decline = -self.natural_decline_rate * interval
        
        # If receiving an injection, calculate treatment effect
        treatment_effect = 0.0
        if "injection" in actions:
            # Select appropriate parameters based on phase
            if phase == "loading":
                params = self.loading_params
            else:
                params = self.maintenance_params
            
            # Get patient-specific response factor
            response_factor = self._get_patient_response_factor(patient_id)
            
            # Calculate base treatment effect
            base_effect = np.random.normal(params['mean'], params['std'])
            
            # Apply patient response factor
            base_effect *= response_factor
            
            # Apply ceiling effect
            # As vision approaches ceiling, improvement diminishes
            ceiling_factor = max(0, 1 - (current_vision / self.ceiling_vision))
            treatment_effect = base_effect * ceiling_factor
        
        # Calculate total vision change
        vision_change = treatment_effect + natural_decline + fluctuation
        
        # Determine if fluid was detected
        # Higher probability if there was no injection or in maintenance phase
        base_fluid_prob = self.fluid_detection_prob
        if "injection" not in actions:
            base_fluid_prob *= 1.5  # Higher chance without injection
        if phase == "maintenance":
            base_fluid_prob *= 1.2  # Higher chance in maintenance
        
        fluid_detected = np.random.random() < min(0.9, base_fluid_prob)
        
        return vision_change, fluid_detected

def create_vision_model(model_type, config=None, clinical_model=None):
    """
    Factory function to create a vision model.
    
    Parameters
    ----------
    model_type : str
        Type of vision model to create:
        - 'simplified': SimplifiedVisionModel
        - 'realistic': RealisticVisionModel
        - 'literature_based': LiteratureBasedVisionModel
    config : simulation.config.SimulationConfig, optional
        Configuration object, by default None
    clinical_model : simulation.clinical_model.ClinicalModel, optional
        Clinical model for disease progression, by default None
        
    Returns
    -------
    BaseVisionModel
        Vision model instance
        
    Raises
    ------
    ValueError
        If model_type is not recognized
    """
    if model_type == 'simplified':
        return SimplifiedVisionModel(config)
    elif model_type == 'realistic':
        return RealisticVisionModel(config)
    elif model_type == 'literature_based':
        if clinical_model is None:
            raise ValueError("clinical_model is required for literature_based vision model")
        return LiteratureBasedVisionModel(clinical_model)
    else:
        raise ValueError(f"Unknown vision model type: {model_type}")
