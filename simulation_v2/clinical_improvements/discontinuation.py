"""
Time-Based Discontinuation Implementation

Implements realistic discontinuation patterns based on clinical data showing
12-15% Year 1, 45-50% by Year 5 discontinuation rates.
"""

import random
from datetime import datetime
from typing import Dict, Optional, Tuple


class TimeBasedDiscontinuationManager:
    """
    Manages time-based discontinuation logic.
    
    Real-world data shows cumulative discontinuation rates of:
    - Year 1: 12.5%
    - Year 2: 27.5% (12.5% + 15%)
    - Year 3: 39.5% (27.5% + 12%)
    - Year 4: 47.5% (39.5% + 8%)
    - Year 5+: 55% (47.5% + 7.5%)
    """
    
    def __init__(self, annual_probabilities: Optional[Dict[int, float]] = None):
        """
        Initialize discontinuation manager.
        
        Args:
            annual_probabilities: Annual discontinuation probabilities by year
                                (not cumulative). Defaults to clinical data.
        """
        self.annual_probabilities = annual_probabilities or {
            1: 0.125,   # 12.5% in Year 1
            2: 0.15,    # Additional 15% in Year 2
            3: 0.12,    # Additional 12% in Year 3
            4: 0.08,    # Additional 8% in Year 4
            5: 0.075    # Additional 7.5% in Year 5+
        }
        
        # Track discontinuation checks to avoid multiple checks per year
        self.last_check_year: Dict[str, int] = {}
    
    def should_discontinue(
        self, 
        patient_id: str,
        current_date: datetime,
        first_visit_date: Optional[datetime],
        is_already_discontinued: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if patient should discontinue based on time.
        
        Args:
            patient_id: Unique patient identifier
            current_date: Current simulation date
            first_visit_date: Date of patient's first visit
            is_already_discontinued: Whether patient is already discontinued
            
        Returns:
            Tuple of (should_discontinue, reason)
        """
        # Don't discontinue if already discontinued
        if is_already_discontinued:
            return False, None
        
        # Need first visit date to calculate time elapsed
        if not first_visit_date:
            return False, None
        
        # Calculate years since first visit
        years_elapsed = (current_date - first_visit_date).days / 365.25
        current_year = int(years_elapsed) + 1
        
        # Check if we've already checked this year for this patient
        if patient_id in self.last_check_year:
            if self.last_check_year[patient_id] >= current_year:
                return False, None
        
        # Get discontinuation probability for current year
        prob = self.annual_probabilities.get(
            min(current_year, 5),  # Cap at year 5 probability
            self.annual_probabilities[5]
        )
        
        # Perform discontinuation check
        if random.random() < prob:
            # Record that we've checked this year
            self.last_check_year[patient_id] = current_year
            
            reason = f"Time-based discontinuation in year {current_year} " \
                    f"(probability: {prob:.1%})"
            return True, reason
        
        # Record that we've checked this year
        self.last_check_year[patient_id] = current_year
        
        return False, None
    
    def get_cumulative_rate(self, year: int) -> float:
        """
        Get expected cumulative discontinuation rate by year.
        
        Args:
            year: Year number (1-based)
            
        Returns:
            Expected cumulative discontinuation rate
        """
        cumulative = 0.0
        for y in range(1, min(year + 1, 6)):
            annual_prob = self.annual_probabilities.get(y, self.annual_probabilities[5])
            # Probability of discontinuing this year given not discontinued yet
            cumulative = cumulative + (1 - cumulative) * annual_prob
        
        return cumulative
    
    def get_expected_rates(self) -> Dict[int, float]:
        """
        Get expected cumulative discontinuation rates for years 1-5.
        
        Returns:
            Dictionary of year: cumulative_rate
        """
        return {
            year: self.get_cumulative_rate(year)
            for year in range(1, 6)
        }