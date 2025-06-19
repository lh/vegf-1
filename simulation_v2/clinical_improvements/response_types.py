"""
Response Type Heterogeneity Implementation

Implements patient heterogeneity by assigning patients to different
response categories (good/average/poor responders).
"""

import random
from typing import Dict, Optional, Tuple


class ResponseTypeManager:
    """
    Manages patient response type assignment and characteristics.
    
    Based on clinical data showing variability in patient response:
    - Good responders (30%): 120% of mean response
    - Average responders (50%): 100% of mean response
    - Poor responders (20%): 60% of mean response
    """
    
    def __init__(self, response_types: Optional[Dict[str, Dict[str, float]]] = None):
        """
        Initialize response type manager.
        
        Args:
            response_types: Dictionary defining response types with
                          probability and multiplier for each type
        """
        self.response_types = response_types or {
            'good': {'probability': 0.3, 'multiplier': 1.2},
            'average': {'probability': 0.5, 'multiplier': 1.0},
            'poor': {'probability': 0.2, 'multiplier': 0.6}
        }
        
        # Validate probabilities sum to 1.0
        total_prob = sum(rt['probability'] for rt in self.response_types.values())
        if abs(total_prob - 1.0) > 0.001:
            raise ValueError(f"Response type probabilities must sum to 1.0, got {total_prob}")
    
    def assign_response_type(self) -> Tuple[str, float]:
        """
        Randomly assign a response type to a patient.
        
        Returns:
            Tuple of (response_type, response_multiplier)
        """
        rand = random.random()
        cumulative = 0.0
        
        for resp_type, params in self.response_types.items():
            cumulative += params['probability']
            if rand < cumulative:
                return resp_type, params['multiplier']
        
        # Fallback (should not reach here if probabilities sum to 1)
        return 'average', 1.0
    
    def get_response_characteristics(self, response_type: str) -> Dict[str, any]:
        """
        Get detailed characteristics for a response type.
        
        Args:
            response_type: Type of responder
            
        Returns:
            Dictionary with response characteristics
        """
        if response_type not in self.response_types:
            raise ValueError(f"Unknown response type: {response_type}")
        
        params = self.response_types[response_type]
        
        # Define additional characteristics based on response type
        if response_type == 'good':
            characteristics = {
                'vision_gain_potential': 'High',
                'treatment_burden_tolerance': 'High',
                'discontinuation_risk': 'Low',
                'expected_year1_gain': '10-15 letters',
                'long_term_stability': 'Good'
            }
        elif response_type == 'poor':
            characteristics = {
                'vision_gain_potential': 'Low',
                'treatment_burden_tolerance': 'Low',
                'discontinuation_risk': 'High',
                'expected_year1_gain': '0-5 letters',
                'long_term_stability': 'Poor'
            }
        else:  # average
            characteristics = {
                'vision_gain_potential': 'Moderate',
                'treatment_burden_tolerance': 'Moderate',
                'discontinuation_risk': 'Moderate',
                'expected_year1_gain': '5-10 letters',
                'long_term_stability': 'Fair'
            }
        
        return {
            'type': response_type,
            'multiplier': params['multiplier'],
            'population_percentage': params['probability'] * 100,
            **characteristics
        }
    
    def adjust_discontinuation_probability(
        self,
        base_probability: float,
        response_type: str
    ) -> float:
        """
        Adjust discontinuation probability based on response type.
        
        Args:
            base_probability: Base discontinuation probability
            response_type: Patient's response type
            
        Returns:
            Adjusted discontinuation probability
        """
        # Good responders less likely to discontinue
        if response_type == 'good':
            return base_probability * 0.7
        # Poor responders more likely to discontinue
        elif response_type == 'poor':
            return base_probability * 1.5
        # Average responders use base probability
        else:
            return base_probability
    
    def get_population_distribution(self) -> Dict[str, float]:
        """
        Get the population distribution of response types.
        
        Returns:
            Dictionary of response_type: percentage
        """
        return {
            resp_type: params['probability'] * 100
            for resp_type, params in self.response_types.items()
        }
    
    def calculate_expected_sd_growth(self, months: int) -> float:
        """
        Calculate expected standard deviation growth over time.
        
        The heterogeneity in response types causes SD to increase
        over time as good/poor responders diverge.
        
        Args:
            months: Months since treatment start
            
        Returns:
            Expected standard deviation multiplier
        """
        # SD grows approximately as square root of time
        # due to accumulating differences between response types
        base_sd_growth = (months / 12) ** 0.5
        
        # Additional growth due to response heterogeneity
        heterogeneity_factor = 1.2
        
        return 1.0 + (base_sd_growth - 1.0) * heterogeneity_factor