"""
Validation script for the EnhancedTreatAndExtendDES implementation.

This script tests that the EnhancedTreatAndExtendDES implementation correctly
integrates with the enhanced DES framework and maintains the expected behavior
of the original TreatAndExtendDES class.
"""

import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from simulation.config import SimulationConfig
from enhanced_treat_and_extend_des import EnhancedTreatAndExtendDES, run_enhanced_treat_and_extend_des
from treat_and_extend_des import TreatAndExtendDES, run_treat_and_extend_des
from simulation.treat_and_extend_adapter import run_treat_and_extend_des_adapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_integrated_implementation():
    """
    Validate the integrated implementation against original and adapter implementations.
    
    This function runs the original TreatAndExtendDES, the adapter-based implementation,
    and the new integrated implementation with the same configuration and compares
    their results.
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
    
    # Run integrated implementation
    logger.info("Running integrated EnhancedTreatAndExtendDES implementation...")
    integrated_results = run_enhanced_treat_and_extend_des(config_name, verbose=False)
    
    # Extract patient histories
    integrated_patient_histories = integrated_results.get("patient_histories", {})
    
    # Compare results
    logger.info("Comparing results...")
    
    # Check patient counts
    original_patient_count = len(original_results)
    adapter_patient_count = len(adapter_results)
    integrated_patient_count = len(integrated_patient_histories)
    
    logger.info(f"Original patient count: {original_patient_count}")
    logger.info(f"Adapter patient count: {adapter_patient_count}")
    logger.info(f"Integrated patient count: {integrated_patient_count}")
    
    # Calculate metrics
    original_metrics = calculate_metrics(original_results)
    adapter_metrics = calculate_metrics(adapter_results)
    integrated_metrics = calculate_metrics(integrated_patient_histories)
    
    # Print comparison table
    logger.info("\nMetrics Comparison:")
    logger.info("-" * 60)
    logger.info(f"{'Metric':<25} {'Original':<12} {'Adapter':<12} {'Integrated':<12}")
    logger.info("-" * 60)
    
    for key in original_metrics:
        original_value = original_metrics.get(key, 0)
        adapter_value = adapter_metrics.get(key, 0)
        integrated_value = integrated_metrics.get(key, 0)
        
        # Format values based on type
        if isinstance(original_value, (int, float)):
            if abs(original_value) < 0.01:
                logger.info(f"{key:<25} {original_value:<12.2f} {adapter_value:<12.2f} {integrated_value:<12.2f}")
            else:
                logger.info(f"{key:<25} {original_value:<12.1f} {adapter_value:<12.1f} {integrated_value:<12.1f}")
        else:
            logger.info(f"{key:<25} {original_value!s:<12} {adapter_value!s:<12} {integrated_value!s:<12}")
    
    # Create comparison plot
    try:
        plot_comparison(original_metrics, adapter_metrics, integrated_metrics)
    except Exception as e:
        logger.error(f"Error creating plots: {str(e)}")
    
    logger.info("Validation complete.")
    return {
        "original_results": original_results,
        "adapter_results": adapter_results,
        "integrated_results": integrated_results
    }

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

def plot_comparison(original_metrics, adapter_metrics, integrated_metrics):
    """
    Create comparison plots between implementations.
    
    Parameters
    ----------
    original_metrics : Dict
        Metrics from original implementation
    adapter_metrics : Dict
        Metrics from adapter implementation
    integrated_metrics : Dict
        Metrics from integrated implementation
    """
    # Setup figure
    fig, axs = plt.subplots(2, 2, figsize=(14, 12))
    
    # Plot 1: Visit counts
    visit_types = ['regular_visits', 'monitoring_visits', 'loading_visits', 'maintenance_visits']
    original_values = [original_metrics.get(key, 0) for key in visit_types]
    adapter_values = [adapter_metrics.get(key, 0) for key in visit_types]
    integrated_values = [integrated_metrics.get(key, 0) for key in visit_types]
    
    x = np.arange(len(visit_types))
    width = 0.25
    
    axs[0, 0].bar(x - width, original_values, width, label='Original')
    axs[0, 0].bar(x, adapter_values, width, label='Adapter')
    axs[0, 0].bar(x + width, integrated_values, width, label='Integrated')
    axs[0, 0].set_xticks(x)
    axs[0, 0].set_xticklabels(visit_types)
    axs[0, 0].set_ylabel('Count')
    axs[0, 0].set_title('Visit Counts')
    axs[0, 0].legend()
    
    # Plot 2: Patient summary
    summary_metrics = ['total_patients', 'loading_completions', 'avg_visits_per_patient']
    original_values = [original_metrics.get(key, 0) for key in summary_metrics]
    adapter_values = [adapter_metrics.get(key, 0) for key in summary_metrics]
    integrated_values = [integrated_metrics.get(key, 0) for key in summary_metrics]
    
    x = np.arange(len(summary_metrics))
    
    axs[0, 1].bar(x - width, original_values, width, label='Original')
    axs[0, 1].bar(x, adapter_values, width, label='Adapter')
    axs[0, 1].bar(x + width, integrated_values, width, label='Integrated')
    axs[0, 1].set_xticks(x)
    axs[0, 1].set_xticklabels(summary_metrics)
    axs[0, 1].set_ylabel('Value')
    axs[0, 1].set_title('Patient Summary')
    axs[0, 1].legend()
    
    # Plot 3: Actions
    action_types = ['injections', 'oct_scans']
    original_values = [original_metrics.get(key, 0) for key in action_types]
    adapter_values = [adapter_metrics.get(key, 0) for key in action_types]
    integrated_values = [integrated_metrics.get(key, 0) for key in action_types]
    
    x = np.arange(len(action_types))
    
    axs[1, 0].bar(x - width, original_values, width, label='Original')
    axs[1, 0].bar(x, adapter_values, width, label='Adapter')
    axs[1, 0].bar(x + width, integrated_values, width, label='Integrated')
    axs[1, 0].set_xticks(x)
    axs[1, 0].set_xticklabels(action_types)
    axs[1, 0].set_ylabel('Count')
    axs[1, 0].set_title('Actions')
    axs[1, 0].legend()
    
    # Plot 4: Visit type breakdown (percentage)
    original_visit_sum = original_metrics.get('total_visits', 0)
    adapter_visit_sum = adapter_metrics.get('total_visits', 0)
    integrated_visit_sum = integrated_metrics.get('total_visits', 0)
    
    if original_visit_sum > 0:
        original_pct = [original_metrics.get(key, 0) / original_visit_sum * 100 for key in visit_types]
    else:
        original_pct = [0] * len(visit_types)
        
    if adapter_visit_sum > 0:
        adapter_pct = [adapter_metrics.get(key, 0) / adapter_visit_sum * 100 for key in visit_types]
    else:
        adapter_pct = [0] * len(visit_types)
        
    if integrated_visit_sum > 0:
        integrated_pct = [integrated_metrics.get(key, 0) / integrated_visit_sum * 100 for key in visit_types]
    else:
        integrated_pct = [0] * len(visit_types)
    
    x = np.arange(len(visit_types))
    
    axs[1, 1].bar(x - width, original_pct, width, label='Original')
    axs[1, 1].bar(x, adapter_pct, width, label='Adapter')
    axs[1, 1].bar(x + width, integrated_pct, width, label='Integrated')
    axs[1, 1].set_xticks(x)
    axs[1, 1].set_xticklabels(visit_types)
    axs[1, 1].set_ylabel('Percentage')
    axs[1, 1].set_title('Visit Type (% of total)')
    axs[1, 1].legend()
    
    plt.tight_layout()
    plt.savefig('integrated_implementation_comparison.png')
    logger.info("Comparison plots saved to integrated_implementation_comparison.png")

if __name__ == "__main__":
    validate_integrated_implementation()