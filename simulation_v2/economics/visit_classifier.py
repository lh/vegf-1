"""
Visit classification logic for resource tracking.

Classifies visits based on protocol type and timing to determine
resource requirements.
"""

from typing import Optional


class VisitClassifier:
    """Classify visits based on protocol type and timing."""
    
    def __init__(self, protocol_type: str):
        """
        Initialize classifier.
        
        Args:
            protocol_type: 'T&E' or 'T&T'
        """
        if protocol_type not in ['T&E', 'T&T']:
            raise ValueError(f"Unknown protocol type: {protocol_type}")
        self.protocol_type = protocol_type
    
    def get_visit_type(self, visit_number: int, day: int, 
                      is_assessment: bool = False, is_annual: bool = False) -> str:
        """
        Determine visit type based on protocol and timing.
        
        Args:
            visit_number: Sequential visit number (1-based)
            day: Day since treatment start
            is_assessment: True if this is a post-loading assessment
            is_annual: True if this is an annual review
            
        Returns:
            Visit type: 'injection_only', 'decision_only', or 'decision_with_injection'
        """
        # Post-loading assessment (both protocols)
        if is_assessment and visit_number == 4:
            return 'decision_only'
        
        # Annual reviews (T&T only)
        if is_annual and self.protocol_type == 'T&T':
            return 'decision_only'
        
        # Loading phase (visits 1-3) - injection only for both
        if visit_number <= 3:
            return 'injection_only'
        
        # T&E Year 1 (visits 4-7) - same as T&T
        if self.protocol_type == 'T&E' and visit_number <= 7:
            # Visit 4 is assessment (handled above)
            # Visits 5-7 are injection only
            return 'injection_only'
        
        # T&E Year 2+ (visit 8 onwards) - all have decisions
        if self.protocol_type == 'T&E' and visit_number >= 8:
            return 'decision_with_injection'
        
        # T&T maintenance - injection only (except annuals)
        if self.protocol_type == 'T&T':
            return 'injection_only'
        
        raise ValueError(f"Unable to classify visit {visit_number} for {self.protocol_type}")