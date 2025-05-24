"""
Force ABS Discontinuation Fix

This script applies a minimal, direct fix to correct ABS discontinuation counting.
"""

import logging
import sys
from functools import partial

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ForceABSFix")

try:
    # Import the necessary modules
    from treat_and_extend_abs import TreatAndExtendABS
    
    # Get the original print_statistics method
    original_print_statistics = TreatAndExtendABS._print_statistics
    
    # Create a replacement that fixes the discontinuation stats directly
    def fixed_print_statistics(self):
        """
        Fixed version that corrects discontinuation statistics before printing.
        """
        # Find unique discontinued patients
        unique_patients = set()
        for patient_id, patient in self.agents.items():
            if hasattr(patient, 'treatment_status') and not patient.treatment_status.get('active', True):
                unique_patients.add(patient_id)
        
        # Correct the stats
        corrected_count = len(unique_patients)
        original_count = self.stats.get("protocol_discontinuations", 0)
        
        if original_count > corrected_count:
            logger.info(f"⚠️ Correcting discontinuation count from {original_count} to {corrected_count}")
            self.stats["protocol_discontinuations"] = corrected_count
            
            # Also fix discontinuation manager stats if available
            if hasattr(self, 'discontinuation_manager'):
                if hasattr(self.discontinuation_manager, 'stats'):
                    dm_stats = self.discontinuation_manager.stats
                    
                    # Fix the total discontinuations
                    dm_stats["total_discontinuations"] = corrected_count
                    
                    # Also add the unique count for clarity
                    dm_stats["unique_patient_discontinuations"] = corrected_count
                    
                    # Calculate the reduction factor if we need to scale down type counts
                    original_total = dm_stats.get("total_discontinuations", 0)
                    if original_total > corrected_count and original_total > 0:
                        scale_factor = corrected_count / original_total
                        
                        # Scale down each type count
                        for disc_type in [
                            "stable_max_interval_discontinuations",
                            "random_administrative_discontinuations", 
                            "treatment_duration_discontinuations",
                            "premature_discontinuations"
                        ]:
                            if disc_type in dm_stats and dm_stats[disc_type] > 0:
                                dm_stats[disc_type] = int(dm_stats[disc_type] * scale_factor)
        
        # Call the original method
        return original_print_statistics(self)
    
    # Apply the patch
    TreatAndExtendABS._print_statistics = fixed_print_statistics
    logger.info("Applied direct fix to ABS discontinuation counting")
    
    # Also prevent future discontinuations by patching the evaluate_discontinuation method
    # Use a partial function to access both the original method and track already discontinued patients
    from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
    original_evaluate = EnhancedDiscontinuationManager.evaluate_discontinuation
    
    # Keep track of discontinued patients
    already_discontinued = set()
    
    def prevent_repeat_discontinuations(self, patient_state, current_time, clinician_id=None, treatment_start_time=None, clinician=None, 
                                       _original_method=original_evaluate, _discontinued_set=already_discontinued):
        """
        Prevent patients from being discontinued more than once.
        """
        # Try to get patient ID
        patient_id = None
        if isinstance(patient_state, dict):
            if "id" in patient_state:
                patient_id = patient_state["id"]
            elif "patient_id" in patient_state:
                patient_id = patient_state["patient_id"]
        
        # If already discontinued, prevent another discontinuation
        if patient_id and patient_id in _discontinued_set:
            return False, "", 0.0, ""
        
        # Call the original method
        result = _original_method(self, patient_state, current_time, clinician_id, treatment_start_time, clinician)
        
        # If discontinuing and we have an ID, track it
        should_discontinue, reason, prob, cessation = result
        if should_discontinue and patient_id:
            _discontinued_set.add(patient_id)
            logger.info(f"Tracked discontinuation for patient {patient_id} with reason {reason}")
        
        return result
    
    # Apply the patch using partial function to retain references
    EnhancedDiscontinuationManager.evaluate_discontinuation = prevent_repeat_discontinuations
    logger.info("Applied prevention for repeat discontinuations")
    
    print("✅ Force ABS Discontinuation Fix applied successfully")
    
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    print(f"❌ Force ABS Discontinuation Fix failed: {e}")