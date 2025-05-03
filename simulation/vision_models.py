"""Vision change models for AMD simulations.

This module provides different implementations of vision change models for
AMD disease progression simulations. It allows for consistent vision change
calculations across different simulation types (ABS and DES).

Classes:
    BaseVisionModel: Abstract base class for vision change models
    SimplifiedVisionModel: Simple normally distributed vision change model
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

def create_vision_model(model_type, config=None, clinical_model=None):
    """
    Factory function to create a vision model.
    
    Parameters
    ----------
    model_type : str
        Type of vision model to create:
        - 'simplified': SimplifiedVisionModel
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
    elif model_type == 'literature_based':
        if clinical_model is None:
            raise ValueError("clinical_model is required for literature_based vision model")
        return LiteratureBasedVisionModel(clinical_model)
    else:
        raise ValueError(f"Unknown vision model type: {model_type}")
