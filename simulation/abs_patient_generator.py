"""Generate realistic patient agents for Agent-Based Simulation (ABS).

This module provides specialized patient generation for ABS models, with:
- Realistic arrival time distributions
- Detailed initial state generation
- Risk factor modeling
- Vision and disease activity initialization

Classes
-------
ABSPatientGenerator
    Generates patients with complete initial states for ABS

Key Features
------------
- Poisson process for patient arrivals
- Normal distributions for baseline vision
- Risk factor modeling (age, diabetes, hypertension, smoking)
- Disease activity based on risk factors

Examples
--------
>>> generator = ABSPatientGenerator(
...     rate_per_week=5,
...     start_date=datetime(2023,1,1),
...     end_date=datetime(2023,12,31)
... )
>>> agents = generator.generate_agents()

Notes
-----
- Vision values are in logMAR units (lower is better)
- Disease activity is on 0-1 scale (higher is worse)
- Risk factors influence disease progression
"""

from datetime import datetime
from typing import List, Tuple, Dict, Optional
from simulation.patient_generator import PatientGenerator

class ABSPatientGenerator(PatientGenerator):
    """Enhanced patient generator for Agent-Based Simulation with improved state initialization."""
    
    def __init__(self, rate_per_week: float, start_date: datetime, 
                 end_date: datetime, random_seed: Optional[int] = None):
        """
        Initialize the ABS patient generator.
        
        Args:
            rate_per_week: Average number of patients to generate per week
            start_date: Start date for patient generation
            end_date: End date for patient generation
            random_seed: Optional random seed for reproducibility
        """
        super().__init__(rate_per_week, start_date, end_date, random_seed)
        
    def generate_agents(self) -> List[Tuple[datetime, Dict]]:
        """
        Generate agents with initial states.
        
        Returns:
            List of tuples containing (arrival_time, initial_state)
        """
        arrivals = self.generate_arrival_times()
        return [(time, self._create_initial_state(patient_num)) 
                for time, patient_num in arrivals]
                
    def _create_initial_state(self, patient_num: int) -> Dict:
        """
        Create initial agent state with proper initialization.
        
        Args:
            patient_num: Unique patient number for ID generation
            
        Returns:
            Dictionary containing initial agent state
        """
        baseline_vision = self._generate_baseline_vision()
        risk_factors = self._generate_risk_factors()
        
        return {
            "patient_id": f"P{patient_num}",
            "baseline_vision": baseline_vision,
            "current_vision": baseline_vision,
            "treatment_naive": True,
            "risk_factors": risk_factors,
            "disease_activity": self._generate_initial_disease_activity(risk_factors),
            "treatment_history": [],
            "visit_history": []
        }
    
    def _generate_risk_factors(self) -> Dict:
        """
        Generate risk factors for a new agent.
        
        Returns:
            Dictionary of risk factors and their values
        """
        return {
            "age": self.rng.normal(75, 10),  # Age normally distributed around 75
            "diabetes": self.rng.random() < 0.2,  # 20% chance of diabetes
            "hypertension": self.rng.random() < 0.5,  # 50% chance of hypertension
            "smoking": self.rng.random() < 0.15  # 15% chance of smoking
        }
    
    def _generate_initial_disease_activity(self, risk_factors: Dict) -> float:
        """
        Generate initial disease activity based on risk factors.
        
        Args:
            risk_factors: Dictionary of patient risk factors
            
        Returns:
            Float representing initial disease activity (0-1 scale)
        """
        base_activity = self.rng.random() * 0.5 + 0.25  # Base activity between 0.25-0.75
        
        # Adjust based on risk factors
        if risk_factors["diabetes"]:
            base_activity += 0.1
        if risk_factors["smoking"]:
            base_activity += 0.15
        if risk_factors["hypertension"]:
            base_activity += 0.05
        
        # Age impact (higher risk with age)
        age_factor = (risk_factors["age"] - 65) / 100
        base_activity += max(0, age_factor)
        
        return min(1.0, max(0.0, base_activity))  # Ensure value is between 0 and 1
        
    def _generate_baseline_vision(self) -> float:
        """
        Generate baseline visual acuity score.
        
        Returns:
            Float representing LogMAR visual acuity score
            Typical range: 0.0 (20/20) to 1.0 (20/200)
            Lower values indicate better vision
        """
        # Generate from truncated normal distribution
        # Mean around 0.5 (moderate vision loss)
        # SD of 0.2 to cover range of initial presentations
        vision = self.rng.normal(0.5, 0.2)
        
        # Truncate to realistic range [0.0, 1.0]
        return min(1.0, max(0.0, vision))
