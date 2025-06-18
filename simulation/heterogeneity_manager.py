"""Manager for patient heterogeneity parameters and assignment.

This module handles the parsing of heterogeneity configuration, assignment of
patients to trajectory classes, and generation of patient-specific characteristics
based on configured distributions.

It implements performance optimizations including distribution pre-sampling and
separate random number streams for reproducibility.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class HeterogeneityManager:
    """
    Manages heterogeneity parameters and patient assignment.
    
    Responsible for parsing heterogeneity configuration, assigning patients
    to trajectory classes, and generating correlated patient characteristics.
    Uses separate RNG streams and pre-sampling for performance.
    """
    
    def __init__(self, heterogeneity_config: Dict[str, Any], seed: int):
        """
        Initialize heterogeneity manager with configuration.
        
        Parameters
        ----------
        heterogeneity_config : Dict[str, Any]
            Heterogeneity section from protocol configuration
        seed : int
            Random seed for reproducibility
        """
        self.config = heterogeneity_config
        self.seed = seed
        
        # Parse configuration sections
        self.trajectory_classes = heterogeneity_config.get('trajectory_classes', {})
        self.patient_parameters = heterogeneity_config.get('patient_parameters', {})
        self.catastrophic_events = heterogeneity_config.get('catastrophic_events', {})
        self.variance_components = heterogeneity_config.get('variance_components', {
            'between_patient': 0.65,
            'within_patient': 0.25,
            'measurement': 0.10
        })
        
        # Debug settings
        self.debug = heterogeneity_config.get('debug', False)
        self.debug_output = heterogeneity_config.get('debug_output', [])
        
        # Create separate RNG streams for reproducibility
        self.trajectory_rng = np.random.RandomState(seed)
        self.parameter_rng = np.random.RandomState(seed + 1)
        self.event_rng = np.random.RandomState(seed + 2)
        
        # Pre-compute samples for performance
        self.sample_cache_size = 10000
        self.sample_indices = defaultdict(int)
        self._precompute_samples()
        
        # Prepare trajectory class selection
        self._prepare_trajectory_selection()
        
        logger.info(f"HeterogeneityManager initialized with {len(self.trajectory_classes)} trajectory classes")
    
    def _prepare_trajectory_selection(self):
        """Prepare arrays for efficient trajectory class selection."""
        self.class_names = list(self.trajectory_classes.keys())
        self.class_proportions = [
            self.trajectory_classes[name]['proportion'] 
            for name in self.class_names
        ]
        
        # Normalize proportions (should already sum to 1, but be safe)
        total = sum(self.class_proportions)
        self.class_proportions = [p / total for p in self.class_proportions]
    
    def _precompute_samples(self):
        """Pre-generate samples from all distributions for efficiency."""
        self.samples = {}
        
        # Pre-sample trajectory class parameters
        for class_name, class_config in self.trajectory_classes.items():
            for param_name, param_config in class_config.get('parameters', {}).items():
                cache_key = f"{class_name}_{param_name}"
                self.samples[cache_key] = self._generate_samples(
                    param_config, self.sample_cache_size, self.parameter_rng
                )
        
        # Pre-sample patient parameters
        for param_name, param_config in self.patient_parameters.items():
            self.samples[param_name] = self._generate_samples(
                param_config, self.sample_cache_size, self.parameter_rng
            )
        
        logger.debug(f"Pre-computed {len(self.samples)} parameter distributions")
    
    def _generate_samples(self, config: Dict[str, Any], n_samples: int, 
                         rng: np.random.RandomState) -> np.ndarray:
        """
        Generate samples from a distribution configuration.
        
        Parameters
        ----------
        config : Dict[str, Any]
            Distribution configuration with 'distribution' key and parameters
        n_samples : int
            Number of samples to generate
        rng : np.random.RandomState
            Random number generator to use
            
        Returns
        -------
        np.ndarray
            Array of samples
        """
        dist_type = config.get('distribution', 'normal')
        
        if dist_type == 'normal':
            mean = config.get('mean', 0)
            std = config.get('std', 1)
            return rng.normal(mean, std, n_samples)
            
        elif dist_type == 'lognormal':
            mean = config.get('mean', 1)
            std = config.get('std', 0.3)
            # Convert to lognormal parameters
            variance = std ** 2
            mu = np.log(mean / np.sqrt(1 + variance / mean**2))
            sigma = np.sqrt(np.log(1 + variance / mean**2))
            return rng.lognormal(mu, sigma, n_samples)
            
        elif dist_type == 'beta':
            alpha = config.get('alpha', 2)
            beta = config.get('beta', 5)
            return rng.beta(alpha, beta, n_samples)
            
        elif dist_type == 'uniform':
            min_val = config.get('min', 0)
            max_val = config.get('max', 1)
            return rng.uniform(min_val, max_val, n_samples)
            
        else:
            logger.warning(f"Unknown distribution type: {dist_type}, using normal")
            return rng.normal(0, 1, n_samples)
    
    def assign_trajectory_class(self) -> str:
        """
        Randomly assign a patient to a trajectory class.
        
        Uses pre-computed proportions for efficiency.
        
        Returns
        -------
        str
            Name of assigned trajectory class
        """
        class_idx = self.trajectory_rng.choice(
            len(self.class_names), 
            p=self.class_proportions
        )
        selected_class = self.class_names[class_idx]
        
        if self.debug and 'patient_assignments' in self.debug_output:
            logger.debug(f"Assigned patient to trajectory class: {selected_class}")
        
        return selected_class
    
    def get_sample(self, param_key: str) -> float:
        """
        Get next pre-computed sample for a parameter.
        
        Uses circular buffer approach for efficiency.
        
        Parameters
        ----------
        param_key : str
            Parameter key in samples cache
            
        Returns
        -------
        float
            Next sample value
        """
        if param_key not in self.samples:
            logger.warning(f"No pre-computed samples for {param_key}, generating on demand")
            return self.parameter_rng.normal(0, 1)
        
        idx = self.sample_indices[param_key]
        value = self.samples[param_key][idx]
        self.sample_indices[param_key] = (idx + 1) % self.sample_cache_size
        
        return value
    
    def generate_patient_characteristics(self, trajectory_class: str, 
                                       baseline_va: float) -> Dict[str, Any]:
        """
        Generate correlated patient characteristics.
        
        Creates patient-specific parameters based on trajectory class and
        baseline visual acuity correlations.
        
        Parameters
        ----------
        trajectory_class : str
            Assigned trajectory class
        baseline_va : float
            Patient's baseline visual acuity
            
        Returns
        -------
        Dict[str, Any]
            Dictionary of patient characteristics including:
            - trajectory_class
            - treatment_effect_multiplier
            - disease_progression_multiplier
            - max_achievable_va
            - resistance_rate
            - Other configured parameters
        """
        characteristics = {
            'trajectory_class': trajectory_class,
            'treatments_received': 0
        }
        
        # Get class-specific parameters
        class_params = self.trajectory_classes[trajectory_class].get('parameters', {})
        
        # Generate values from class distributions
        for param_name, param_config in class_params.items():
            cache_key = f"{trajectory_class}_{param_name}"
            value = self.get_sample(cache_key)
            characteristics[param_name] = value
        
        # Apply baseline VA correlations
        # High baseline patients tend to respond better
        if baseline_va > 70:
            if 'treatment_effect_multiplier' in characteristics:
                characteristics['treatment_effect_multiplier'] *= 1.3
            if 'disease_progression_multiplier' in characteristics:
                characteristics['disease_progression_multiplier'] *= 0.7
        elif baseline_va < 40:
            if 'treatment_effect_multiplier' in characteristics:
                characteristics['treatment_effect_multiplier'] *= 0.8
            if 'disease_progression_multiplier' in characteristics:
                characteristics['disease_progression_multiplier'] *= 1.2
        
        # Generate patient-specific parameters
        for param_name, param_config in self.patient_parameters.items():
            if param_name == 'max_achievable_va_offset':
                # Special handling for VA ceiling
                offset = self.get_sample(param_name)
                characteristics['max_achievable_va'] = min(85, baseline_va + offset)
            elif param_name not in characteristics:
                # Don't override class-specific values
                characteristics[param_name] = self.get_sample(param_name)
        
        # Add default resistance rate if not specified
        if 'resistance_rate' not in characteristics:
            if 'resistance_rate' in self.patient_parameters:
                characteristics['resistance_rate'] = self.get_sample('resistance_rate')
            else:
                # Default beta(2, 5) gives most patients low resistance
                characteristics['resistance_rate'] = self.parameter_rng.beta(2, 5)
        
        if self.debug and 'patient_assignments' in self.debug_output:
            logger.debug(f"Generated characteristics: {characteristics}")
        
        return characteristics
    
    def should_catastrophic_event_occur(self, event_type: str, 
                                       weeks_elapsed: float) -> Tuple[bool, Optional[Dict]]:
        """
        Check if a catastrophic event should occur.
        
        Parameters
        ----------
        event_type : str
            Type of catastrophic event
        weeks_elapsed : float
            Time elapsed since last check
            
        Returns
        -------
        Tuple[bool, Optional[Dict]]
            (should_occur, event_details) where event_details contains
            impact distribution parameters if event should occur
        """
        if event_type not in self.catastrophic_events:
            return False, None
        
        event_config = self.catastrophic_events[event_type]
        prob_per_month = event_config.get('probability_per_month', 0)
        prob_per_week = prob_per_month / 4.33  # Convert to weekly
        
        # Check if event occurs
        if self.event_rng.random() < prob_per_week * weeks_elapsed:
            return True, event_config
        
        return False, None
    
    def get_validation_targets(self) -> Dict[str, Any]:
        """
        Get validation targets from configuration.
        
        Returns
        -------
        Dict[str, Any]
            Validation targets for Seven-UP comparison
        """
        return self.config.get('validation', {})