"""
Monkey patching module for Streamlit app to use fixed implementations.

This module contains functions to patch the imports in the simulation_runner.py
module to use the fixed versions of the treat-and-extend implementations.
"""

import importlib
import sys
import os
import logging
import streamlit as st

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monkey_patch_discontinuation():
    """
    Monkey patch the discontinuation-related imports and functions
    to use the fixed implementations.
    """
    # Import the fixed implementations
    try:
        # Import the fixed modules
        from treat_and_extend_abs_fixed import TreatAndExtendABS as FixedABS
        from treat_and_extend_des_fixed import TreatAndExtendDES as FixedDES
        
        # Import the simulation runner module
        import streamlit_app.simulation_runner as sr
        
        # Replace the classes
        sr.TreatAndExtendABS = FixedABS
        sr.TreatAndExtendDES = FixedDES
        
        # Enhance the process_simulation_results function
        original_process_func = sr.process_simulation_results
        
        # Define a wrapper that enhances the processing
        def enhanced_process_simulation_results(sim, patient_histories, params):
            # Call the original function first
            results = original_process_func(sim, patient_histories, params)
            
            # Extract additional statistics that our fixed implementation provides
            if hasattr(sim, 'stats'):
                # Get the unique discontinuation count
                unique_discontinuations = sim.stats.get("unique_discontinuations", 0)
                if unique_discontinuations > 0:
                    # Store in results
                    if "raw_discontinuation_stats" not in results:
                        results["raw_discontinuation_stats"] = {}
                    
                    results["raw_discontinuation_stats"]["unique_patient_discontinuations"] = unique_discontinuations
                    
                    # Calculate the correct discontinuation rate
                    patient_count = results.get("patient_count", len(patient_histories))
                    if patient_count > 0:
                        correct_rate = (unique_discontinuations / patient_count) * 100
                        results["corrected_discontinuation_rate"] = correct_rate
                        
                    # Log the correction
                    logger.info(f"Using unique discontinuation count: {unique_discontinuations}")
                    logger.info(f"Corrected discontinuation rate: {results.get('corrected_discontinuation_rate', 0):.2f}%")
                
                # Get the unique retreatment count
                unique_retreatments = sim.stats.get("unique_retreatments", 0)
                if unique_retreatments > 0 and "raw_discontinuation_stats" in results:
                    results["raw_discontinuation_stats"]["unique_patient_retreatments"] = unique_retreatments
            
            # If the simulation has a refactored manager, get its statistics
            if hasattr(sim, 'refactored_manager'):
                refactored_stats = sim.refactored_manager.get_statistics()
                if refactored_stats:
                    # Extract and store unique counts
                    unique_discontinued = refactored_stats.get("unique_discontinued_patients", 0)
                    if unique_discontinued > 0:
                        if "raw_discontinuation_stats" not in results:
                            results["raw_discontinuation_stats"] = {}
                        
                        results["raw_discontinuation_stats"]["unique_patient_discontinuations"] = unique_discontinued
                        
                        # Calculate the correct discontinuation rate
                        patient_count = results.get("patient_count", len(patient_histories))
                        if patient_count > 0:
                            correct_rate = (unique_discontinued / patient_count) * 100
                            results["corrected_discontinuation_rate"] = correct_rate
            
            # Enhanced visualization function
            original_generate_func = sr.generate_discontinuation_plot
            
            def enhanced_generate_discontinuation_plot(results):
                # Call original function
                fig = original_generate_func(results)
                
                # Add unique count info if available
                if "raw_discontinuation_stats" in results and "unique_patient_discontinuations" in results["raw_discontinuation_stats"]:
                    unique_count = results["raw_discontinuation_stats"]["unique_patient_discontinuations"]
                    patient_count = results.get("patient_count", 0)
                    
                    if unique_count > 0 and patient_count > 0:
                        # Calculate the corrected rate
                        correct_rate = (unique_count / patient_count) * 100
                        
                        # Display the corrected rate
                        st.success(f"### Corrected Discontinuation Rate: {correct_rate:.1f}%")
                        st.info(f"Unique patients discontinued: {unique_count} out of {patient_count} patients")
                
                return fig
            
            # Replace the visualization function
            sr.generate_discontinuation_plot = enhanced_generate_discontinuation_plot
            
            return results
        
        # Replace the process function with our enhanced version
        sr.process_simulation_results = enhanced_process_simulation_results
        
        logger.info("Successfully patched Streamlit app to use fixed discontinuation implementations")
        return True
    
    except Exception as e:
        logger.error(f"Error patching discontinuation implementation: {e}")
        return False

def apply_all_patches():
    """Apply all patches and return success status."""
    try:
        discontinued_patched = monkey_patch_discontinuation()
        logger.info(f"Discontinuation patching status: {'Success' if discontinued_patched else 'Failed'}")
        return discontinued_patched
    except Exception as e:
        logger.error(f"Error applying patches: {e}")
        return False