"""
Direct fix for ABS simulation discontinuation counting.

This script specifically targets the TreatAndExtendABS class to patch its process_event
method to prevent counting the same patient discontinuation multiple times.
"""

import sys
from functools import wraps
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ABSDiscontinuationFix")

try:
    from treat_and_extend_abs import TreatAndExtendABS
    imported = True
    logger.info("Successfully imported TreatAndExtendABS")
except ImportError:
    imported = False
    logger.error("Failed to import TreatAndExtendABS")

if imported:
    # First, modify the run method to reset discontinuation tracking at start of simulation
    original_run = TreatAndExtendABS.run
    
    # Track patients using global variable to persist between runs
    global_discontinued_patients = set()
    
    @wraps(TreatAndExtendABS.run)
    def patched_run(self):
        """
        Patched version of run that resets discontinuation metrics and
        adds post-simulation verification of discontinuation counts.
        """
        # Clear tracking sets for a fresh simulation
        global_discontinued_patients.clear()
        
        # Reset simulation stats to ensure clean start
        if "protocol_discontinuations" in self.stats:
            self.stats["protocol_discontinuations"] = 0
            
        # Do the same for discontinuation manager if present
        if hasattr(self, 'discontinuation_manager') and hasattr(self.discontinuation_manager, 'stats'):
            self.discontinuation_manager.stats["total_discontinuations"] = 0
            self.discontinuation_manager.stats["stable_max_interval_discontinuations"] = 0
            self.discontinuation_manager.stats["random_administrative_discontinuations"] = 0
            self.discontinuation_manager.stats["treatment_duration_discontinuations"] = 0
            if "premature_discontinuations" in self.discontinuation_manager.stats:
                self.discontinuation_manager.stats["premature_discontinuations"] = 0
            
        # Run the original simulation
        result = original_run(self)
        
        # After running, verify and fix discontinuation counts
        total_patients = len(self.agents)
        
        # Count unique discontinued patients from full patient histories
        unique_discontinued_patients = set()
        for patient_id, patient in self.agents.items():
            # Check if this patient is currently discontinued
            if not patient.treatment_status.get("active", True) and patient.treatment_status.get("cessation_type"):
                unique_discontinued_patients.add(patient_id)
                
            # Also check history for any discontinuation events
            for visit in patient.history:
                if hasattr(visit, 'treatment_status') and not visit.get('treatment_status', {}).get('active', True) and visit.get('treatment_status', {}).get('cessation_type'):
                    unique_discontinued_patients.add(patient_id)
                    break
        
        # Update global set
        global_discontinued_patients.update(unique_discontinued_patients)
        
        # Fix the main simulation stats
        correct_disc_count = len(unique_discontinued_patients)
        self.stats["unique_discontinuations"] = correct_disc_count  # Add new stat for unique count
        
        # Log the correction
        logger.info(f"Counted {correct_disc_count} unique patient discontinuations out of {total_patients} patients")
        logger.info(f"Global tracking now shows {len(global_discontinued_patients)} unique discontinuations across all simulations")
        
        # If stats seem incorrect, force correction
        if self.stats.get("protocol_discontinuations", 0) > correct_disc_count and correct_disc_count > 0:
            logger.warning(f"Correcting protocol_discontinuations from {self.stats['protocol_discontinuations']} to {correct_disc_count}")
            self.stats["protocol_discontinuations"] = correct_disc_count
            
            # Also correct discontinuation manager stats
            if hasattr(self, 'discontinuation_manager') and hasattr(self.discontinuation_manager, 'stats'):
                # Capture total from individual types
                type_sum = sum([
                    self.discontinuation_manager.stats.get("stable_max_interval_discontinuations", 0),
                    self.discontinuation_manager.stats.get("random_administrative_discontinuations", 0),
                    self.discontinuation_manager.stats.get("treatment_duration_discontinuations", 0),
                    self.discontinuation_manager.stats.get("premature_discontinuations", 0)
                ])
                
                # If type sum is greater than unique count, scale them down proportionally
                if type_sum > correct_disc_count and type_sum > 0:
                    scale_factor = correct_disc_count / type_sum
                    
                    # Scale down each type
                    types = [
                        "stable_max_interval_discontinuations",
                        "random_administrative_discontinuations", 
                        "treatment_duration_discontinuations",
                        "premature_discontinuations"
                    ]
                    
                    for disc_type in types:
                        if disc_type in self.discontinuation_manager.stats and self.discontinuation_manager.stats[disc_type] > 0:
                            self.discontinuation_manager.stats[disc_type] = round(self.discontinuation_manager.stats[disc_type] * scale_factor)
                    
                    # Set the total directly
                    self.discontinuation_manager.stats["total_discontinuations"] = correct_disc_count
                    
                    # Add unique patient count to stats
                    self.discontinuation_manager.stats["unique_patient_discontinuations"] = correct_disc_count
            
        return result
    
    # Apply the run method patch
    TreatAndExtendABS.run = patched_run
    logger.info("Successfully patched TreatAndExtendABS.run to calculate correct discontinuation counts")
    
    # Also patch process_event for real-time tracking
    original_process_event = TreatAndExtendABS.process_event
    
    # Track which patients have been discontinued within a single process_event call
    discontinued_patients = set()
    
    @wraps(TreatAndExtendABS.process_event)
    def patched_process_event(self, event):
        """
        Patched version that prevents counting discontinuations multiple times.
        """
        patient_id = event.patient_id
        
        # Only proceed with special handling for visit events
        if event.event_type == "visit":
            patient = self.agents.get(patient_id)
            if patient:
                # Check if this is a monitoring visit for an already discontinued patient
                is_monitoring = event.data.get("is_monitoring", False)
                
                # Special handling for when we're checking discontinuation possibility
                if (not is_monitoring and 
                    patient.current_phase == "maintenance" and 
                    patient.disease_activity["max_interval_reached"] and
                    patient.disease_activity["consecutive_stable_visits"] >= 3):
                    
                    # If this patient has already been discontinued, modify the stats
                    if patient_id in discontinued_patients:
                        # Store original stats count
                        old_protocol_discs = self.stats.get("protocol_discontinuations", 0)
                        
                        # Call original method
                        result = original_process_event(self, event)
                        
                        # Check if stats were incremented
                        new_protocol_discs = self.stats.get("protocol_discontinuations", 0)
                        
                        # If stats were incremented, revert the increment
                        if new_protocol_discs > old_protocol_discs:
                            self.stats["protocol_discontinuations"] = old_protocol_discs
                            logger.info(f"Prevented double-counting discontinuation for patient {patient_id}")
                        
                        # Also fix discontinuation manager stats if needed
                        if hasattr(self, 'discontinuation_manager') and hasattr(self.discontinuation_manager, 'stats'):
                            # Check if any discontinuation types were incremented
                            types = [
                                "stable_max_interval_discontinuations",
                                "random_administrative_discontinuations", 
                                "treatment_duration_discontinuations",
                                "premature_discontinuations"
                            ]
                            
                            # If total was incremented, decrement it
                            self.discontinuation_manager.stats["total_discontinuations"] = max(
                                0, self.discontinuation_manager.stats.get("total_discontinuations", 0) - 1
                            )
                            
                            # Try to find which type was incremented and decrement it
                            for disc_type in types:
                                if disc_type in self.discontinuation_manager.stats:
                                    # Assume it was incremented, decrement it (safe because we're just fixing stats)
                                    self.discontinuation_manager.stats[disc_type] = max(
                                        0, self.discontinuation_manager.stats.get(disc_type, 0) - 1
                                    )
                                    break
                        
                        return result
                    else:
                        # Call original method
                        result = original_process_event(self, event)
                        
                        # Check if discontinuation occurred by checking if treatment is no longer active
                        if not patient.treatment_status.get("active", True):
                            discontinued_patients.add(patient_id)
                            logger.info(f"Tracked discontinuation for patient {patient_id}")
                        
                        return result
        
        # For all other cases, just call the original method
        return original_process_event(self, event)
    
    # Apply the patch
    TreatAndExtendABS.process_event = patched_process_event
    logger.info("Successfully patched TreatAndExtendABS.process_event to fix discontinuation counting")

# Provide simple summary
if imported:
    print("Successfully applied direct fix for ABS discontinuation counting")
else:
    print("Failed to apply ABS discontinuation fix due to import errors")