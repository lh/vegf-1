"""Enhanced discontinuation management for treatment simulations.

This module extends the base discontinuation manager to provide a more sophisticated
framework for managing treatment discontinuation in both Agent-Based Simulation (ABS)
and Discrete Event Simulation (DES) models. It handles multiple discontinuation types,
time-dependent recurrence probabilities, and clinician variation.

Key Features
------------
- Multiple discontinuation types (protocol-based, administrative, time-based, premature)
- Type-specific monitoring schedules
- Time-dependent recurrence probabilities based on clinical data
- Clinician variation in protocol adherence
- Enhanced statistics tracking

Classes
-------
EnhancedDiscontinuationManager
    Enhanced manager for treatment discontinuation with multiple discontinuation types
"""

from datetime import datetime, timedelta
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

from simulation.discontinuation_manager import DiscontinuationManager
from simulation.clinician import Clinician

logger = logging.getLogger(__name__)

class EnhancedDiscontinuationManager(DiscontinuationManager):
    """Enhanced manager for treatment discontinuation with multiple discontinuation types.
    
    Extends the base DiscontinuationManager to provide:
    1. Multiple discontinuation types (protocol-based, administrative, time-based, premature)
    2. Type-specific monitoring schedules
    3. Time-dependent recurrence probabilities based on clinical data
    4. Tracking of discontinuation type in patient state
    
    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary containing enhanced discontinuation parameters
    
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
    recurrence_models : Dict[str, Any]
        Recurrence models by cessation type
    stats : Dict[str, Any]
        Enhanced statistics tracking discontinuation events
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the enhanced discontinuation manager with configuration.
        
        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary containing enhanced discontinuation parameters
        """
        # Call parent initialization
        super().__init__(config)
        
        # Extract enhanced configuration
        discontinuation_config = config.get("discontinuation", {})
        self.recurrence_models = discontinuation_config.get("recurrence", {})
        
        # Enhanced statistics
        self.stats.update({
            "premature_discontinuations": 0,
            "retreatments_by_type": {
                "stable_max_interval": 0,  # Protocol-based
                "premature": 0,            # Non-protocol based
                "random_administrative": 0, # Administrative
                "treatment_duration": 0    # Time-based
            }
        })
        
        logger.info("Initialized EnhancedDiscontinuationManager")
    
    def evaluate_discontinuation(self, 
                                patient_state: Dict[str, Any], 
                                current_time: datetime,
                                clinician_id: Optional[str] = None,
                                treatment_start_time: Optional[datetime] = None,
                                clinician: Optional[Clinician] = None) -> Tuple[bool, str, float, str]:
        """Evaluate whether a patient should discontinue treatment.
        
        Enhanced to include multiple discontinuation types and return the cessation type.
        Also supports clinician-specific decision modifications.
        
        Parameters
        ----------
        patient_state : Dict[str, Any]
            Current patient state including disease activity and treatment history
        current_time : datetime
            Current simulation time
        clinician_id : Optional[str], optional
            ID of clinician making the decision, by default None
        treatment_start_time : Optional[datetime], optional
            Time when treatment started, by default None
        clinician : Optional[Clinician], optional
            Clinician object making the decision, by default None
            
        Returns
        -------
        Tuple[bool, str, float, str]
            Tuple containing:
            - discontinue: Whether to discontinue treatment
            - reason: Reason for discontinuation (if applicable)
            - probability: Probability that was used for the decision
            - cessation_type: Type of discontinuation (for recurrence calculations)
        """
        if not self.enabled:
            return False, "", 0.0, ""
        
        # Call the base method first to get the protocol decision
        protocol_decision, reason, protocol_probability = super().evaluate_discontinuation(
            patient_state, current_time, treatment_start_time
        )
        
        # Apply clinician-specific modifications if a clinician is provided
        if clinician:
            # Let the clinician modify the protocol decision
            modified_decision, modified_probability = clinician.evaluate_discontinuation(
                patient_state, protocol_decision, protocol_probability
            )
            
            # If the clinician modified the decision
            if modified_decision != protocol_decision:
                if modified_decision:
                    # Clinician decided to discontinue against protocol (premature)
                    self.stats["premature_discontinuations"] += 1
                    self.stats["total_discontinuations"] += 1
                    return True, "premature", modified_probability, "premature"
                else:
                    # Clinician decided to continue against protocol
                    return False, "", 0.0, ""
        
        # If protocol says to discontinue and no clinician override
        if protocol_decision:
            # Use reason as the cessation type - this covers the standard types
            return True, reason, protocol_probability, reason
        
        # Check for premature discontinuation (non-protocol based)
        disease_activity = patient_state.get("disease_activity", {})
        current_interval = disease_activity.get("current_interval", 0)
        
        premature_criteria = self.criteria.get("premature", {})
        min_interval_weeks = premature_criteria.get("min_interval_weeks", 8)
        probability_factor = premature_criteria.get("probability_factor", 2.0)
        
        # Only consider premature if interval is at least the minimum
        if current_interval >= min_interval_weeks:
            # Use base probability from stable_max_interval and multiply by factor
            base_probability = self.criteria.get("stable_max_interval", {}).get("probability", 0.2)
            premature_probability = base_probability * probability_factor
            
            # Check if discontinuation occurs
            if np.random.random() < premature_probability:
                self.stats["premature_discontinuations"] += 1
                self.stats["total_discontinuations"] += 1
                return True, "premature", premature_probability, "premature"
        
        # Default: no discontinuation
        return False, "", 0.0, ""
    
    def schedule_monitoring(self, 
                           discontinuation_time: datetime,
                           cessation_type: str = "stable_max_interval") -> List[Dict[str, Any]]:
        """Schedule post-discontinuation monitoring visits based on cessation type.
        
        Parameters
        ----------
        discontinuation_time : datetime
            Time when treatment was discontinued
        cessation_type : str, optional
            Type of discontinuation, by default "stable_max_interval"
        
        Returns
        -------
        List[Dict[str, Any]]
            List of monitoring visit events to schedule
        """
        if not self.enabled:
            return []
        
        # Get the appropriate follow-up schedule based on cessation type
        # Default to planned schedule if not found
        if cessation_type in ["premature", "random_administrative", "treatment_duration"]:
            follow_up_schedule = self.monitoring.get("unplanned", {}).get(
                "follow_up_schedule", 
                self.monitoring.get("planned", {}).get("follow_up_schedule", [12, 24, 36])
            )
        else:
            follow_up_schedule = self.monitoring.get("planned", {}).get("follow_up_schedule", [12, 24, 36])
        
        monitoring_events = []
        
        for weeks in follow_up_schedule:
            visit_time = discontinuation_time + timedelta(weeks=weeks)
            
            monitoring_events.append({
                "time": visit_time,
                "type": "monitoring_visit",
                "actions": ["vision_test", "oct_scan"],
                "is_monitoring": True,
                "cessation_type": cessation_type  # Store cessation type for reference
            })
        
        return monitoring_events
    
    def calculate_recurrence_probability(self, 
                                        weeks_since_discontinuation: float,
                                        cessation_type: str = "stable_max_interval",
                                        has_PED: bool = False) -> float:
        """Calculate disease recurrence probability based on time and cessation type.
        
        Uses clinical data from Artiaga et al. and Aslanis et al. to determine
        time-dependent recurrence probabilities.
        
        Parameters
        ----------
        weeks_since_discontinuation : float
            Weeks since treatment was discontinued
        cessation_type : str, optional
            Type of discontinuation, by default "stable_max_interval"
        has_PED : bool, optional
            Whether patient has PED, which increases recurrence risk, by default False
            
        Returns
        -------
        float
            Probability of disease recurrence at the given time point
        """
        # Get the appropriate recurrence model based on cessation type
        # Default to planned if not found
        recurrence_model = self.recurrence_models.get(
            cessation_type, 
            self.recurrence_models.get("planned", {})
        )
        
        # Get cumulative rates at key time points (using Artiaga data as defaults)
        # Convert to weeks for calculations
        weeks_in_year = 52
        year_1 = weeks_in_year
        year_3 = 3 * weeks_in_year
        year_5 = 5 * weeks_in_year
        
        # Get rates from configuration (with Artiaga data as defaults)
        cumulative_rates = recurrence_model.get("cumulative_rates", {})
        rate_year_1 = cumulative_rates.get("year_1", 0.207)  # 20.7% at 1 year
        rate_year_3 = cumulative_rates.get("year_3", 0.739)  # 73.9% at 3 years
        rate_year_5 = cumulative_rates.get("year_5", 0.880)  # 88.0% at 5 years
        
        # Calculate time-dependent rate using piecewise linear interpolation
        if weeks_since_discontinuation <= year_1:
            # Linear from 0 to year_1 rate
            rate = (weeks_since_discontinuation / year_1) * rate_year_1
        elif weeks_since_discontinuation <= year_3:
            # Linear from year_1 to year_3 rate
            progress = (weeks_since_discontinuation - year_1) / (year_3 - year_1)
            rate = rate_year_1 + progress * (rate_year_3 - rate_year_1)
        elif weeks_since_discontinuation <= year_5:
            # Linear from year_3 to year_5 rate
            progress = (weeks_since_discontinuation - year_3) / (year_5 - year_3)
            rate = rate_year_3 + progress * (rate_year_5 - rate_year_3)
        else:
            # Cap at year_5 rate
            rate = rate_year_5
        
        # Apply risk modifiers for PED (from Aslanis study)
        if has_PED:
            # 74% vs 48% with/without PED - factor of ~1.54
            PED_multiplier = self.recurrence_models.get("risk_modifiers", {}).get("with_PED", 1.54)
            rate = min(1.0, rate * PED_multiplier)  # Cap at 100%
        
        return rate
    
    def process_monitoring_visit(self, 
                                patient_state: Dict[str, Any],
                                actions: List[str],
                                clinician: Optional[Clinician] = None) -> Tuple[bool, Dict[str, Any]]:
        """Process a monitoring visit for a discontinued patient.
        
        Enhanced to use time-dependent recurrence probabilities based on cessation type.
        Also supports clinician-specific decision modifications.
        
        Parameters
        ----------
        patient_state : Dict[str, Any]
            Current patient state
        actions : List[str]
            Actions performed during the visit
        clinician : Optional[Clinician], optional
            Clinician object making the decision, by default None
        
        Returns
        -------
        Tuple[bool, Dict[str, Any]]
            Tuple containing:
            - retreatment: Whether to restart treatment
            - updated_state: Updated patient state
        """
        if not self.enabled:
            return False, patient_state
        
        # Get cessation type and time since discontinuation
        treatment_status = patient_state.get("treatment_status", {})
        cessation_type = treatment_status.get("cessation_type", "stable_max_interval")
        discontinuation_date = treatment_status.get("discontinuation_date")
        
        if discontinuation_date:
            # Calculate weeks since discontinuation
            weeks_since_discontinuation = (datetime.now() - discontinuation_date).days / 7
            
            # Get PED status (if available)
            disease_characteristics = patient_state.get("disease_characteristics", {})
            has_PED = disease_characteristics.get("has_PED", False)
            
            # Calculate recurrence probability for this visit
            recurrence_probability = self.calculate_recurrence_probability(
                weeks_since_discontinuation, cessation_type, has_PED
            )
            
            # Determine if disease has recurred
            disease_recurred = np.random.random() < recurrence_probability
            
            if disease_recurred:
                # Update patient's disease activity
                disease_activity = patient_state.get("disease_activity", {})
                disease_activity["fluid_detected"] = True
                
                # Apply detection probability
                recurrence_detection_probability = self.monitoring.get("recurrence_detection_probability", 0.87)
                recurrence_detected = np.random.random() < recurrence_detection_probability
                
                if recurrence_detected and "oct_scan" in actions:
                    # Get the protocol retreatment decision
                    protocol_retreatment, protocol_probability = self.evaluate_retreatment(patient_state)
                    
                    # Apply clinician-specific modifications if a clinician is provided
                    if clinician and protocol_retreatment:
                        retreatment, probability = clinician.evaluate_retreatment(
                            patient_state, protocol_retreatment, protocol_probability
                        )
                    else:
                        retreatment, probability = protocol_retreatment, protocol_probability
                    
                    if retreatment:
                        # Update retreatment statistics by cessation type
                        self.stats["retreatments"] += 1
                        self.stats["retreatments_by_type"][cessation_type] += 1
                        
                        # Update patient state for retreatment
                        treatment_status["active"] = True
                        treatment_status["recurrence_detected"] = True
                        
                        return True, patient_state
        
        return False, patient_state
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get enhanced discontinuation statistics.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary of enhanced discontinuation statistics
        """
        stats = self.stats.copy()
        
        # Calculate additional metrics
        if stats["total_discontinuations"] > 0:
            stats["retreatment_rate"] = stats["retreatments"] / stats["total_discontinuations"]
            
            # Retreatment rates by cessation type
            stats["retreatment_rates_by_type"] = {}
            for cessation_type, count in stats["retreatments_by_type"].items():
                type_count = stats.get(f"{cessation_type}_discontinuations", 0)
                if type_count > 0:
                    stats["retreatment_rates_by_type"][cessation_type] = count / type_count
                else:
                    stats["retreatment_rates_by_type"][cessation_type] = 0.0
        else:
            stats["retreatment_rate"] = 0.0
        
        return stats
