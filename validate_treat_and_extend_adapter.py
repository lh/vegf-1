"""
Validation script for the TreatAndExtendAdapter.

This script tests that the TreatAndExtendAdapter correctly implements the
functionality of the original TreatAndExtendDES class using the new EnhancedDES
framework.
"""

import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from simulation.config import SimulationConfig
from simulation.treat_and_extend_adapter import TreatAndExtendAdapter, run_treat_and_extend_des_adapter
from treat_and_extend_des import TreatAndExtendDES, run_treat_and_extend_des

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_adapter():
    """
    Validate that TreatAndExtendAdapter produces similar results to TreatAndExtendDES.
    
    This function runs both the original TreatAndExtendDES and the new
    TreatAndExtendAdapter with the same configuration and compares their results.
    """
    # Configuration
    config_name = "eylea_literature_based"
    logger.info(f"Running validation with config: {config_name}")
    
    # Run original implementation
    logger.info("Running original TreatAndExtendDES implementation...")
    original_results = run_treat_and_extend_des(config_name, verbose=False)
    
    # Run adapter implementation
    logger.info("Running TreatAndExtendAdapter implementation...")
    adapter_results = run_treat_and_extend_des_adapter(config_name, verbose=False)
    
    # Compare results
    logger.info("Comparing results...")
    
    # Check patient counts
    original_patient_count = len(original_results)
    adapter_patient_count = len(adapter_results)
    logger.info(f"Original patient count: {original_patient_count}")
    logger.info(f"Adapter patient count: {adapter_patient_count}")
    
    # Get common patients
    common_patients = set(original_results.keys()) & set(adapter_results.keys())
    logger.info(f"Common patients: {len(common_patients)}")
    
    if common_patients:
        # Sample a patient to compare visits
        sample_patient_id = next(iter(common_patients))
        
        # Compare visits for sample patient
        original_visits = original_results[sample_patient_id]
        adapter_visits = adapter_results[sample_patient_id]
        
        logger.info(f"Sample patient {sample_patient_id}:")
        logger.info(f"  Original visits: {len(original_visits)}")
        logger.info(f"  Adapter visits: {len(adapter_visits)}")
        
        # Check key metrics
        compare_metrics(original_results, adapter_results)
    
    logger.info("Validation complete.")
    return {
        "original_results": original_results,
        "adapter_results": adapter_results
    }

def compare_metrics(original_results, adapter_results):
    """
    Compare key metrics between original and adapter results.
    
    Parameters
    ----------
    original_results : Dict
        Results from original TreatAndExtendDES
    adapter_results : Dict
        Results from TreatAndExtendAdapter
    """
    # Calculate key metrics
    original_metrics = calculate_metrics(original_results)
    adapter_metrics = calculate_metrics(adapter_results)
    
    # Print comparisons
    logger.info("\nMetrics Comparison:")
    logger.info("-" * 20)
    
    for key in original_metrics:
        original_value = original_metrics[key]
        adapter_value = adapter_metrics.get(key, 0)
        
        # Calculate difference and percent difference
        if isinstance(original_value, (int, float)) and original_value != 0:
            diff = adapter_value - original_value
            percent_diff = (diff / original_value) * 100
            logger.info(f"{key}:")
            logger.info(f"  Original: {original_value}")
            logger.info(f"  Adapter:  {adapter_value}")
            logger.info(f"  Diff:     {diff} ({percent_diff:.1f}%)")
        else:
            logger.info(f"{key}:")
            logger.info(f"  Original: {original_value}")
            logger.info(f"  Adapter:  {adapter_value}")

def calculate_metrics(results):
    """
    Calculate key metrics from simulation results.
    
    Parameters
    ----------
    results : Dict
        Simulation results
        
    Returns
    -------
    Dict
        Dictionary of metrics
    """
    metrics = {}
    
    # Total patients
    metrics["total_patients"] = len(results)
    
    # Total visits
    total_visits = sum(len(visits) for visits in results.values())
    metrics["total_visits"] = total_visits
    
    # Average visits per patient
    avg_visits = total_visits / max(1, len(results))
    metrics["avg_visits_per_patient"] = avg_visits
    
    # Count visit types
    regular_visits = 0
    monitoring_visits = 0
    total_loading_visits = 0
    total_maintenance_visits = 0
    
    # Count actions
    injection_count = 0
    oct_scan_count = 0
    
    # Count phases
    loading_completion_count = 0
    
    # Track last phase per patient
    patient_last_phase = {}
    
    # Process all visits
    for patient_id, visits in results.items():
        # Sort visits by date
        sorted_visits = sorted(visits, key=lambda v: v.get('date', datetime.min))
        
        # Track last phase
        if sorted_visits:
            patient_last_phase[patient_id] = sorted_visits[-1].get('phase', '')
            
            # Check if patient completed loading phase
            if any(v.get('phase') == 'maintenance' for v in sorted_visits):
                loading_completion_count += 1
        
        # Count visit types and actions
        for visit in visits:
            visit_type = visit.get('type', '')
            phase = visit.get('phase', '')
            actions = visit.get('actions', [])
            
            if visit_type == 'regular_visit':
                regular_visits += 1
            elif visit_type == 'monitoring_visit':
                monitoring_visits += 1
            
            if phase == 'loading':
                total_loading_visits += 1
            elif phase == 'maintenance':
                total_maintenance_visits += 1
            
            if 'injection' in actions:
                injection_count += 1
            if 'oct_scan' in actions:
                oct_scan_count += 1
    
    # Add to metrics
    metrics["regular_visits"] = regular_visits
    metrics["monitoring_visits"] = monitoring_visits
    metrics["loading_visits"] = total_loading_visits
    metrics["maintenance_visits"] = total_maintenance_visits
    metrics["injections"] = injection_count
    metrics["oct_scans"] = oct_scan_count
    metrics["loading_completions"] = loading_completion_count
    
    # Calculate loading completion rate
    loading_completion_rate = (loading_completion_count / max(1, len(results))) * 100
    metrics["loading_completion_rate"] = loading_completion_rate
    
    return metrics

def plot_comparison(original_results, adapter_results):
    """
    Create comparison plots between original and adapter results.
    
    Parameters
    ----------
    original_results : Dict
        Results from original TreatAndExtendDES
    adapter_results : Dict
        Results from TreatAndExtendAdapter
    """
    # Setup figure
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    
    # Calculate metrics
    original_metrics = calculate_metrics(original_results)
    adapter_metrics = calculate_metrics(adapter_results)
    
    # Plot 1: Visit counts
    visit_types = ['regular_visits', 'monitoring_visits', 'loading_visits', 'maintenance_visits']
    original_values = [original_metrics.get(key, 0) for key in visit_types]
    adapter_values = [adapter_metrics.get(key, 0) for key in visit_types]
    
    x = np.arange(len(visit_types))
    width = 0.35
    
    axs[0, 0].bar(x - width/2, original_values, width, label='Original')
    axs[0, 0].bar(x + width/2, adapter_values, width, label='Adapter')
    axs[0, 0].set_xticks(x)
    axs[0, 0].set_xticklabels(visit_types)
    axs[0, 0].set_ylabel('Count')
    axs[0, 0].set_title('Visit Counts')
    axs[0, 0].legend()
    
    # Plot 2: Patient summary
    summary_metrics = ['total_patients', 'loading_completions', 'avg_visits_per_patient']
    original_values = [original_metrics.get(key, 0) for key in summary_metrics]
    adapter_values = [adapter_metrics.get(key, 0) for key in summary_metrics]
    
    x = np.arange(len(summary_metrics))
    
    axs[0, 1].bar(x - width/2, original_values, width, label='Original')
    axs[0, 1].bar(x + width/2, adapter_values, width, label='Adapter')
    axs[0, 1].set_xticks(x)
    axs[0, 1].set_xticklabels(summary_metrics)
    axs[0, 1].set_ylabel('Value')
    axs[0, 1].set_title('Patient Summary')
    axs[0, 1].legend()
    
    # Plot 3: Actions
    action_types = ['injections', 'oct_scans']
    original_values = [original_metrics.get(key, 0) for key in action_types]
    adapter_values = [adapter_metrics.get(key, 0) for key in action_types]
    
    x = np.arange(len(action_types))
    
    axs[1, 0].bar(x - width/2, original_values, width, label='Original')
    axs[1, 0].bar(x + width/2, adapter_values, width, label='Adapter')
    axs[1, 0].set_xticks(x)
    axs[1, 0].set_xticklabels(action_types)
    axs[1, 0].set_ylabel('Count')
    axs[1, 0].set_title('Actions')
    axs[1, 0].legend()
    
    # Plot 4: Visit type breakdown
    original_visit_sum = original_metrics.get('total_visits', 0)
    adapter_visit_sum = adapter_metrics.get('total_visits', 0)
    
    if original_visit_sum > 0:
        original_pct = [original_metrics.get(key, 0) / original_visit_sum * 100 for key in visit_types]
    else:
        original_pct = [0] * len(visit_types)
        
    if adapter_visit_sum > 0:
        adapter_pct = [adapter_metrics.get(key, 0) / adapter_visit_sum * 100 for key in visit_types]
    else:
        adapter_pct = [0] * len(visit_types)
    
    x = np.arange(len(visit_types))
    
    axs[1, 1].bar(x - width/2, original_pct, width, label='Original')
    axs[1, 1].bar(x + width/2, adapter_pct, width, label='Adapter')
    axs[1, 1].set_xticks(x)
    axs[1, 1].set_xticklabels(visit_types)
    axs[1, 1].set_ylabel('Percentage')
    axs[1, 1].set_title('Visit Type (% of total)')
    axs[1, 1].legend()
    
    plt.tight_layout()
    plt.savefig('adapter_comparison_plots.png')
    logger.info("Comparison plots saved to adapter_comparison_plots.png")

if __name__ == "__main__":
    # Run validation
    results = validate_adapter()
    
    # Plot comparison if both implementations returned results
    if results["original_results"] and results["adapter_results"]:
        try:
            plot_comparison(results["original_results"], results["adapter_results"])
        except Exception as e:
            logger.error(f"Error creating plots: {str(e)}")
    
    logger.info("Validation script completed successfully.")