"""Clinician modeling for treatment simulations.

This module provides classes for modeling individual clinician behavior and managing
clinician assignments in treatment simulations. It allows for variation in protocol
adherence, risk tolerance, and treatment decisions.

Key Features
------------
- Configurable clinician profiles with different adherence characteristics
- Decision modification logic for discontinuation and retreatment
- Patient assignment with continuity of care modeling

Classes
-------
Clinician
    Model of an individual clinician with characteristic behaviors
ClinicianManager
    Manages a pool of clinicians and handles patient assignment
"""

import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional, Union

logger = logging.getLogger(__name__)

class Clinician:
    """Model of an individual clinician with characteristic behaviors.
    
    This class represents a clinician with specific adherence characteristics
    that affect treatment decisions. The default "perfect" clinician follows
    protocol perfectly.
    
    Parameters
    ----------
    profile_name : str, optional
        Name of the clinician profile, by default "perfect"
    profile_config : Dict[str, Any], optional
        Configuration for this clinician profile, by default None
    
    Attributes
    ----------
    profile_name : str
        Name of the clinician profile
    adherence_rate : float
        Rate of protocol adherence (0.0-1.0)
    risk_tolerance : str
        Risk tolerance level ("low", "medium", "high")
    conservative_retreatment : bool
        Whether clinician is conservative with retreatment decisions
    stability_threshold : int
        Number of consecutive stable visits required for stability
    interval_preferences : Dict[str, Any]
        Preferences for treatment intervals
    """
    
    def __init__(self, profile_name: str = "perfect", profile_config: Optional[Dict[str, Any]] = None):
        """Initialize a clinician with the specified profile.
        
        Parameters
        ----------
        profile_name : str, optional
            Name of the clinician profile, by default "perfect"
        profile_config : Optional[Dict[str, Any]], optional
            Configuration for this clinician profile, by default None
        """
        # Use empty dict if no config provided
        profile_config = profile_config or {}
        
        self.profile_name = profile_name
        self.adherence_rate = profile_config.get("protocol_adherence_rate", 1.0)  # Perfect adherence by default
        self.risk_tolerance = profile_config.get("characteristics", {}).get("risk_tolerance", "low")
        self.conservative_retreatment = profile_config.get("characteristics", {}).get("conservative_retreatment", True)
        
        # Default stability threshold and interval preferences for the "perfect" clinician
        self.stability_threshold = profile_config.get("stability_threshold", 3)
        self.interval_preferences = profile_config.get("interval_preferences", {
            "min_interval": 8,
            "max_interval": 16,
            "extension_threshold": 2  # Letters of improvement needed to extend
        })
        
        logger.info(f"Initialized clinician with profile '{profile_name}'")
    
    def follows_protocol(self) -> bool:
        """Determine if the clinician follows protocol for this decision.
        
        Returns
        -------
        bool
            Whether the clinician follows protocol
        """
        return np.random.random() < self.adherence_rate
    
    def evaluate_discontinuation(self, 
                                patient_state: Dict[str, Any], 
                                protocol_decision: bool, 
                                protocol_probability: float) -> Tuple[bool, float]:
        """Apply clinician-specific modification to discontinuation decisions.
        
        Parameters
        ----------
        patient_state : Dict[str, Any]
            Current patient state
        protocol_decision : bool
            Decision according to protocol
        protocol_probability : float
            Probability used for protocol decision
        
        Returns
        -------
        Tuple[bool, float]
            Tuple containing:
            - decision: Modified decision
            - probability: Modified probability
        """
        # Perfect clinician always follows protocol
        if self.profile_name == "perfect":
            return protocol_decision, protocol_probability
        
        # If protocol says to discontinue
        if protocol_decision:
            # High risk tolerance clinicians almost always agree to discontinue
            if self.risk_tolerance == "high":
                return True, min(1.0, protocol_probability * 1.3)
            # Low risk tolerance clinicians sometimes override to continue
            elif self.risk_tolerance == "low":
                override_chance = 0.3  # 30% chance of overriding discontinuation
                if np.random.random() < override_chance:
                    return False, 0.0
            
            # Default: follow protocol decision
            return True, protocol_probability
        
        # If protocol says to continue
        else:
            # High risk tolerance clinicians sometimes discontinue anyway
            if self.risk_tolerance == "high":
                premature_chance = 0.15  # 15% chance of premature discontinuation
                if np.random.random() < premature_chance:
                    return True, 0.15
            
            # Default: follow protocol decision
            return False, 0.0
    
    def evaluate_retreatment(self, 
                            patient_state: Dict[str, Any], 
                            protocol_decision: bool, 
                            protocol_probability: float) -> Tuple[bool, float]:
        """Apply clinician-specific modification to retreatment decisions.
        
        Parameters
        ----------
        patient_state : Dict[str, Any]
            Current patient state
        protocol_decision : bool
            Decision according to protocol
        protocol_probability : float
            Probability used for protocol decision
        
        Returns
        -------
        Tuple[bool, float]
            Tuple containing:
            - decision: Modified decision
            - probability: Modified probability
        """
        # Perfect clinician always follows protocol
        if self.profile_name == "perfect":
            return protocol_decision, protocol_probability
        
        # Conservative clinicians almost always retreat
        if self.conservative_retreatment:
            return protocol_decision, min(1.0, protocol_probability * 1.2)
        
        # Risk-taking clinicians might decide against retreatment
        if self.risk_tolerance == "high" and protocol_decision:
            skip_chance = 0.2  # 20% chance of skipping retreatment
            if np.random.random() < skip_chance:
                return False, 0.0
        
        # Default: follow protocol decision
        return protocol_decision, protocol_probability


class ClinicianManager:
    """Manages a pool of clinicians and handles patient assignment.
    
    When enabled, creates a pool of clinicians with different profiles and
    assigns them to patients. When disabled, uses a single "perfect" clinician.
    
    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary containing clinician parameters
    enabled : bool, optional
        Whether clinician variation is enabled, by default False
    
    Attributes
    ----------
    config : Dict[str, Any]
        Configuration dictionary
    enabled : bool
        Whether clinician variation is enabled
    clinicians : Dict[str, Clinician]
        Dictionary mapping clinician IDs to Clinician objects
    patient_assignments : Dict[str, str]
        Dictionary mapping patient IDs to clinician IDs
    mode : str
        Patient assignment mode ("fixed", "random_per_visit", "weighted")
    continuity : float
        Probability of seeing the same clinician in weighted mode
    """
    
    def __init__(self, config: Dict[str, Any], enabled: bool = False):
        """Initialize the clinician manager with configuration.
        
        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary containing clinician parameters
        enabled : bool, optional
            Whether clinician variation is enabled, by default False
        """
        self.config = config
        self.enabled = enabled
        self.clinicians = {}
        self.patient_assignments = {}  # Maps patient_id to clinician_id
        
        if not enabled:
            # Just create one perfect clinician
            self.clinicians["PERFECT"] = Clinician()
            logger.info("Initialized ClinicianManager with a single perfect clinician")
            return
            
        # Initialize from configuration if enabled
        self.mode = config.get("clinicians", {}).get("patient_assignment", {}).get("mode", "fixed")
        self.continuity = config.get("clinicians", {}).get("patient_assignment", {}).get("continuity_of_care", 0.9)
        self._initialize_clinicians()
        
        logger.info(f"Initialized ClinicianManager with {len(self.clinicians)} clinicians in {self.mode} mode")
    
    def _initialize_clinicians(self):
        """Create the pool of clinicians based on configuration."""
        profiles = self.config.get("clinicians", {}).get("profiles", {})
        biases = self.config.get("clinicians", {}).get("decision_biases", {})
        
        # Calculate how many of each type to create (for a pool of 10 clinicians)
        total_clinicians = 10
        clinician_counts = {}
        
        for profile_name, profile in profiles.items():
            probability = profile.get("probability", 0.0)
            count = max(1, round(probability * total_clinicians))
            clinician_counts[profile_name] = count
        
        # Create the clinicians
        clinician_id = 1
        for profile_name, count in clinician_counts.items():
            for i in range(count):
                # Create clinician with this profile
                clinician = Clinician(profile_name, profiles[profile_name])
                
                # Set decision thresholds
                clinician.stability_threshold = biases.get("stability_thresholds", {}).get(profile_name, 2)
                clinician.interval_preferences = biases.get("interval_preferences", {}).get(profile_name, {})
                
                # Add to pool
                self.clinicians[f"CLINICIAN{clinician_id:03d}"] = clinician
                clinician_id += 1
    
    def assign_clinician(self, patient_id: str, visit_time: datetime) -> str:
        """Assign a clinician to a patient for this visit.
        
        Parameters
        ----------
        patient_id : str
            ID of the patient
        visit_time : datetime
            Time of the visit
        
        Returns
        -------
        str
            ID of the assigned clinician
        """
        if not self.enabled:
            return "PERFECT"  # Always use the perfect clinician if disabled
        
        # If mode is fixed and patient already has an assignment, keep it
        if self.mode == "fixed" and patient_id in self.patient_assignments:
            return self.patient_assignments[patient_id]
        
        # If mode is random_per_visit, always pick a random clinician
        if self.mode == "random_per_visit":
            clinician_id = np.random.choice(list(self.clinicians.keys()))
            return clinician_id
        
        # If mode is weighted or this is the first visit for a fixed assignment
        if self.mode == "weighted" and patient_id in self.patient_assignments:
            # Check continuity of care
            if np.random.random() < self.continuity:
                return self.patient_assignments[patient_id]
            else:
                # Assign to a new clinician
                current = self.patient_assignments[patient_id]
                options = [cid for cid in self.clinicians.keys() if cid != current]
                clinician_id = np.random.choice(options)
                self.patient_assignments[patient_id] = clinician_id
                return clinician_id
        
        # Default: new random assignment
        clinician_id = np.random.choice(list(self.clinicians.keys()))
        self.patient_assignments[patient_id] = clinician_id
        return clinician_id
    
    def get_clinician(self, clinician_id: str) -> Clinician:
        """Get a clinician by ID.
        
        Parameters
        ----------
        clinician_id : str
            ID of the clinician
        
        Returns
        -------
        Clinician
            Clinician object, or the perfect clinician if not found
        """
        return self.clinicians.get(clinician_id, self.clinicians.get("PERFECT"))
    
    def get_performance_metrics(self) -> Dict[str, Dict[str, int]]:
        """Get clinician performance metrics.
        
        Returns
        -------
        Dict[str, Dict[str, int]]
            Dictionary of performance metrics by clinician profile
        """
        metrics = {
            "profile_counts": {},
            "patient_counts": {},
            "discontinuation_rates": {},
            "retreatment_rates": {}
        }
        
        # Count clinicians by profile
        for clinician in self.clinicians.values():
            metrics["profile_counts"][clinician.profile_name] = metrics["profile_counts"].get(clinician.profile_name, 0) + 1
        
        # Count patients by assigned clinician profile
        for patient_id, clinician_id in self.patient_assignments.items():
            clinician = self.clinicians.get(clinician_id)
            if clinician:
                metrics["patient_counts"][clinician.profile_name] = metrics["patient_counts"].get(clinician.profile_name, 0) + 1
        
        return metrics
