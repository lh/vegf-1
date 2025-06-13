"""
Fix for discontinuation tracking to prevent multiple counting of the same patient.

This script applies direct patches to the discontinuation manager to ensure that:
1. Patients can only be discontinued once in their lifetime
2. Statistics correctly track unique patients rather than discontinuation events
3. Visualization reflects this accurate tracking

Usage:
Import this module at the start of your simulation to apply the patches:

```python
import fix_discontinuation_tracking
```
"""

import logging
from functools import wraps

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DiscontinuationFix")

# Try to import the necessary module
try:
    from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
    module_imported = True
    logger.info("Successfully imported EnhancedDiscontinuationManager for patching")
except ImportError:
    module_imported = False
    logger.error("Failed to import EnhancedDiscontinuationManager. Patches will not be applied.")

if module_imported:
    # Save original methods before patching
    original_evaluate = EnhancedDiscontinuationManager.evaluate_discontinuation
    original_stats = EnhancedDiscontinuationManager.get_statistics
    
    # Global registry of discontinued patients
    # This persists across manager instances for the session
    discontinued_patients = set()
    
    @wraps(EnhancedDiscontinuationManager.evaluate_discontinuation)
    def patched_evaluate_discontinuation(self, patient_state, current_time, clinician_id=None, treatment_start_time=None, clinician=None):
        """
        Patched version that prevents a patient from being discontinued more than once.
        """
        # First, try to get patient ID
        patient_id = None
        if isinstance(patient_state, dict):
            # Check common fields where patient ID might be stored
            if "id" in patient_state:
                patient_id = patient_state["id"]
            elif "patient_id" in patient_state:
                patient_id = patient_state["patient_id"]
        
        # If this patient has already been discontinued, prevent another discontinuation
        if patient_id and patient_id in discontinued_patients:
            # Patient already discontinued before, don't discontinue again
            logger.info(f"Preventing re-discontinuation of patient {patient_id}")
            return False, "", 0.0, ""
        
        # Call original method
        should_discontinue, reason, probability, cessation_type = original_evaluate(
            self, patient_state, current_time, clinician_id, treatment_start_time, clinician
        )
        
        # If discontinuing, register this patient
        if should_discontinue and patient_id:
            discontinued_patients.add(patient_id)
            logger.info(f"Patient {patient_id} discontinued with reason {reason}")
        
        return should_discontinue, reason, probability, cessation_type
    
    @wraps(EnhancedDiscontinuationManager.get_statistics)
    def patched_get_statistics(self):
        """
        Patched version that adds unique patient discontinuation count.
        """
        # Get original stats
        stats = original_stats(self)
        
        # Add unique patient info
        stats["unique_patient_discontinuations"] = len(discontinued_patients)
        
        # If we have discontinuations tracked, add percentage
        total_discontinuations = stats.get("total_discontinuations", 0)
        if total_discontinuations > 0 and len(discontinued_patients) > 0:
            stats["unique_percentage"] = (len(discontinued_patients) / total_discontinuations) * 100
        
        return stats
    
    # Apply patches
    EnhancedDiscontinuationManager.evaluate_discontinuation = patched_evaluate_discontinuation
    EnhancedDiscontinuationManager.get_statistics = patched_get_statistics
    
    logger.info("Successfully patched EnhancedDiscontinuationManager to prevent multiple discontinuations")
    logger.info("Also patched statistics to include unique patient discontinuation count")
else:
    logger.warning("No patches applied due to import errors")

print("Applied fix for discontinuation tracking")