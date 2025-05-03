"""Discontinuation management for treatment simulations.

This module provides a configurable framework for managing treatment discontinuation
in both Agent-Based Simulation (ABS) and Discrete Event Simulation (DES) models.
It handles various discontinuation criteria, post-discontinuation monitoring,
and treatment re-entry based on disease recurrence.

Key Features
------------
- Configuration-driven discontinuation criteria
- Multiple discontinuation types (stable at max interval, administrative, time-based)
- Post-discontinuation monitoring
- Treatment re-entry based on disease recurrence
- Consistent implementation across simulation types

Classes
-------
DiscontinuationManager
    Main class for managing treatment discontinuation logic
"""

from datetime import datetime, timedelta
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

logger = logging.getLogger(__name__)

class DiscontinuationManager:
    """Manager for treatment discontinuation decisions and monitoring.
    
    This class encapsulates all discontinuation-related logic, providing a consistent
    interface for both ABS and DES simulations. It evaluates different discontinuation
    criteria, handles patient monitoring after discontinuation, and manages re-entry
    into treatment when eligible.
    
    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary containing discontinuation parameters
    
    Attributes
    ----------
    enabled : bool
        Whether discontinuation is enabled
    config : Dict[str, Any]
        Configuration dictionary
    criteria : Dict[str, Any]
        Discontinuation criteria configuration
    monitoring : Dict[str, Any]
        Post-discontinuation monitoring configuration
    retreatment : Dict[str, Any]
        Treatment re-entry configuration
    stats : Dict[str, int]
        Statistics tracking discontinuation events
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the discontinuation manager with configuration.
        
        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary containing discontinuation parameters
        """
        self.config = config
        
        # Extract discontinuation configuration
        discontinuation_config = config.get("discontinuation", {})
        
        # Set default values if configuration is missing
        self.enabled = discontinuation_config.get("enabled", False)
        self.criteria = discontinuation_config.get("criteria", {})
        self.monitoring = discontinuation_config.get("monitoring", {})
        self.retreatment = discontinuation_config.get("retreatment", {})
        
        # Initialize statistics
        self.stats = {
            "stable_max_interval_discontinuations": 0,
            "random_administrative_discontinuations": 0,
            "treatment_duration_discontinuations": 0,
            "total_discontinuations": 0,
            "retreatments": 0
        }
        
        logger.info(f"Initialized DiscontinuationManager with enabled={self.enabled}")
        if self.enabled:
            logger.info(f"Discontinuation criteria: {self.criteria}")
    
    def evaluate_discontinuation(self, 
                                patient_state: Dict[str, Any], 
                                current_time: datetime,
                                treatment_start_time: Optional[datetime] = None) -> Tuple[bool, str, float]:
        """Evaluate whether a patient should discontinue treatment.
        
        Parameters
        ----------
        patient_state : Dict[str, Any]
            Current patient state including disease activity and treatment history
        current_time : datetime
            Current simulation time
        treatment_start_time : Optional[datetime], optional
            Time when treatment started, by default None
        
        Returns
        -------
        Tuple[bool, str, float]
            Tuple containing:
            - discontinue: Whether to discontinue treatment
            - reason: Reason for discontinuation (if applicable)
            - probability: Probability that was used for the decision
        """
        if not self.enabled:
            return False, "", 0.0
        
        # Extract relevant patient state
        disease_activity = patient_state.get("disease_activity", {})
        consecutive_stable_visits = disease_activity.get("consecutive_stable_visits", 0)
        max_interval_reached = disease_activity.get("max_interval_reached", False)
        
        # Check stable at max interval criterion
        stable_max_interval = self.criteria.get("stable_max_interval", {})
        if (max_interval_reached and 
            consecutive_stable_visits >= stable_max_interval.get("consecutive_visits", 3)):
            
            probability = stable_max_interval.get("probability", 0.2)
            if np.random.random() < probability:
                self.stats["stable_max_interval_discontinuations"] += 1
                self.stats["total_discontinuations"] += 1
                return True, "stable_max_interval", probability
        
        # Check random administrative criterion
        random_administrative = self.criteria.get("random_administrative", {})
        annual_probability = random_administrative.get("annual_probability", 0.0)
        
        # Convert annual probability to per-visit probability (assuming ~8 visits per year on average)
        per_visit_probability = 1 - (1 - annual_probability) ** (1/8)
        
        if np.random.random() < per_visit_probability:
            self.stats["random_administrative_discontinuations"] += 1
            self.stats["total_discontinuations"] += 1
            return True, "random_administrative", per_visit_probability
        
        # Check treatment duration criterion (only if enabled with a non-zero probability)
        if treatment_start_time is not None:
            treatment_duration = self.criteria.get("treatment_duration", {})
            threshold_weeks = treatment_duration.get("threshold_weeks", 52)
            probability = treatment_duration.get("probability", 0.0)
            
            # Only proceed if probability is greater than 0 (i.e., criterion is enabled)
            if probability > 0:
                treatment_weeks = (current_time - treatment_start_time).days / 7
                
                if treatment_weeks > threshold_weeks:  # Only discontinue if strictly greater
                    # Convert annual probability to per-visit probability after threshold
                    per_visit_probability = 1 - (1 - probability) ** (1/4)  # Assuming quarterly evaluation
                    
                    if np.random.random() < per_visit_probability:
                        self.stats["treatment_duration_discontinuations"] += 1
                        self.stats["total_discontinuations"] += 1
                        return True, "treatment_duration", per_visit_probability
        
        return False, "", 0.0
    
    def schedule_monitoring(self, 
                           discontinuation_time: datetime) -> List[Dict[str, Any]]:
        """Schedule post-discontinuation monitoring visits.
        
        Parameters
        ----------
        discontinuation_time : datetime
            Time when treatment was discontinued
        
        Returns
        -------
        List[Dict[str, Any]]
            List of monitoring visit events to schedule
        """
        if not self.enabled:
            return []
        
        follow_up_schedule = self.monitoring.get("follow_up_schedule", [12, 24, 36])
        monitoring_events = []
        
        for weeks in follow_up_schedule:
            visit_time = discontinuation_time + timedelta(weeks=weeks)
            
            monitoring_events.append({
                "time": visit_time,
                "type": "monitoring_visit",
                "actions": ["vision_test", "oct_scan"],
                "is_monitoring": True
            })
        
        return monitoring_events
    
    def evaluate_retreatment(self, 
                            patient_state: Dict[str, Any]) -> Tuple[bool, float]:
        """Evaluate whether a discontinued patient should re-enter treatment.
        
        Parameters
        ----------
        patient_state : Dict[str, Any]
            Current patient state including disease activity and vision
        
        Returns
        -------
        Tuple[bool, float]
            Tuple containing:
            - retreatment: Whether to restart treatment
            - probability: Probability that was used for the decision
        """
        if not self.enabled:
            return False, 0.0
        
        # Extract relevant patient state
        disease_activity = patient_state.get("disease_activity", {})
        fluid_detected = disease_activity.get("fluid_detected", False)
        
        # Check eligibility criteria
        eligibility_criteria = self.retreatment.get("eligibility_criteria", {})
        retreatment_probability = self.retreatment.get("probability", 0.95)
        
        # Simple implementation: if fluid is detected, consider retreatment
        if fluid_detected:
            if np.random.random() < retreatment_probability:
                self.stats["retreatments"] += 1
                return True, retreatment_probability
        
        return False, 0.0
    
    def process_monitoring_visit(self, 
                                patient_state: Dict[str, Any],
                                actions: List[str]) -> Tuple[bool, Dict[str, Any]]:
        """Process a monitoring visit for a discontinued patient.
        
        Parameters
        ----------
        patient_state : Dict[str, Any]
            Current patient state
        actions : List[str]
            Actions performed during the visit
        
        Returns
        -------
        Tuple[bool, Dict[str, Any]]
            Tuple containing:
            - retreatment: Whether to restart treatment
            - updated_state: Updated patient state
        """
        if not self.enabled:
            return False, patient_state
        
        # Check for disease recurrence detection
        recurrence_detection_probability = self.monitoring.get("recurrence_detection_probability", 0.87)
        
        # If OCT scan was performed, check for fluid detection
        if "oct_scan" in actions:
            # Use the patient's actual fluid status, but apply detection probability
            disease_activity = patient_state.get("disease_activity", {})
            actual_fluid = disease_activity.get("fluid_detected", False)
            
            if actual_fluid and np.random.random() < recurrence_detection_probability:
                # Fluid detected, evaluate retreatment
                retreatment, probability = self.evaluate_retreatment(patient_state)
                
                if retreatment:
                    # Update patient state for retreatment
                    treatment_status = patient_state.get("treatment_status", {})
                    treatment_status["active"] = True
                    treatment_status["recurrence_detected"] = True
                    
                    return True, patient_state
        
        return False, patient_state
    
    def get_statistics(self) -> Dict[str, int]:
        """Get discontinuation statistics.
        
        Returns
        -------
        Dict[str, int]
            Dictionary of discontinuation statistics
        """
        return self.stats
