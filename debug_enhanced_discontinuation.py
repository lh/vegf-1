"""
Debug script for testing the enhanced discontinuation model.

This script runs a simulation with the enhanced discontinuation model and clinician variation,
demonstrating the new features and providing a way to verify that everything is working correctly.

Usage:
    python debug_enhanced_discontinuation.py

The script will:
1. Run an ABS simulation with the enhanced discontinuation model
2. Print detailed statistics about discontinuation types and clinician decisions
3. Generate visualizations of discontinuation patterns
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Add the current directory to the path so we can import the simulation modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.config import SimulationConfig
from treat_and_extend_abs import TreatAndExtendABS, run_treat_and_extend_abs
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
from simulation.clinician import Clinician, ClinicianManager

def run_enhanced_discontinuation_simulation():
    """
    Run a simulation with the enhanced discontinuation model and clinician variation.
    """
    print("Running simulation with enhanced discontinuation model...")
    
    # Load the enhanced discontinuation configuration
    config = SimulationConfig.from_yaml("protocols/simulation_configs/enhanced_discontinuation.yaml")
    
    # Run the simulation
    sim = TreatAndExtendABS(config)
    patient_histories = sim.run()
    
    # Analyze the results
    analyze_discontinuation_patterns(patient_histories, sim)
    
    return patient_histories, sim

def analyze_discontinuation_patterns(patient_histories, sim):
    """
    Analyze discontinuation patterns from the simulation results.
    
    Parameters
    ----------
    patient_histories : dict
        Dictionary mapping patient IDs to their visit histories
    sim : TreatAndExtendABS
        Simulation object with statistics
    """
    print("\nAnalyzing discontinuation patterns...")
    
    # Get discontinuation statistics
    discontinuation_stats = sim.discontinuation_manager.get_statistics()
    
    # Print detailed statistics
    print("\nDetailed Discontinuation Statistics:")
    print("-" * 40)
    
    # Count discontinuations by type
    discontinuation_types = {
        "stable_max_interval": 0,
        "premature": 0,
        "random_administrative": 0,
        "treatment_duration": 0
    }
    
    # Count patients with PED
    patients_with_ped = 0
    patients_without_ped = 0
    
    # Count discontinuations by clinician profile
    clinician_discontinuations = {}
    
    # Analyze patient histories
    for patient_id, visits in patient_histories.items():
        patient = sim.agents[patient_id]
        
        # Check if patient has PED
        if patient.disease_characteristics.get("has_PED", False):
            patients_with_ped += 1
        else:
            patients_without_ped += 1
        
        # Check if patient discontinued treatment
        if not patient.treatment_status["active"] and patient.treatment_status["discontinuation_date"]:
            cessation_type = patient.treatment_status.get("cessation_type", "unknown")
            if cessation_type in discontinuation_types:
                discontinuation_types[cessation_type] += 1
            
            # Get clinician ID from the visit where discontinuation occurred
            discontinuation_date = patient.treatment_status["discontinuation_date"]
            for visit in visits:
                if visit.get("date") == discontinuation_date:
                    clinician_id = visit.get("clinician_id", "unknown")
                    if clinician_id != "unknown":
                        clinician = sim.clinician_manager.get_clinician(clinician_id)
                        profile = clinician.profile_name
                        clinician_discontinuations[profile] = clinician_discontinuations.get(profile, 0) + 1
                    break
    
    # Print discontinuation types
    print("Discontinuations by Type:")
    total_discontinuations = sum(discontinuation_types.values())
    for cessation_type, count in discontinuation_types.items():
        percentage = (count / max(1, total_discontinuations)) * 100
        print(f"  {cessation_type}: {count} ({percentage:.1f}%)")
    
    # Print PED statistics
    print("\nPatients with PED:")
    print(f"  With PED: {patients_with_ped} ({(patients_with_ped / (patients_with_ped + patients_without_ped)) * 100:.1f}%)")
    print(f"  Without PED: {patients_without_ped} ({(patients_without_ped / (patients_with_ped + patients_without_ped)) * 100:.1f}%)")
    
    # Print clinician discontinuations
    if clinician_discontinuations:
        print("\nDiscontinuations by Clinician Profile:")
        for profile, count in clinician_discontinuations.items():
            percentage = (count / max(1, total_discontinuations)) * 100
            print(f"  {profile}: {count} ({percentage:.1f}%)")
    
    # Print retreatment statistics
    if "retreatment_rates_by_type" in discontinuation_stats:
        print("\nRetreatment Rates by Discontinuation Type:")
        for cessation_type, rate in discontinuation_stats["retreatment_rates_by_type"].items():
            print(f"  {cessation_type}: {rate * 100:.1f}%")
    
    # Create visualizations
    create_discontinuation_visualizations(discontinuation_types, clinician_discontinuations)

def create_discontinuation_visualizations(discontinuation_types, clinician_discontinuations):
    """
    Create visualizations of discontinuation patterns.
    
    Parameters
    ----------
    discontinuation_types : dict
        Dictionary mapping discontinuation types to counts
    clinician_discontinuations : dict
        Dictionary mapping clinician profiles to discontinuation counts
    """
    # Create a figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot discontinuation types
    labels = list(discontinuation_types.keys())
    values = list(discontinuation_types.values())
    ax1.bar(labels, values)
    ax1.set_title("Discontinuations by Type")
    ax1.set_ylabel("Count")
    ax1.set_xticklabels(labels, rotation=45, ha="right")
    
    # Plot clinician discontinuations
    if clinician_discontinuations:
        labels = list(clinician_discontinuations.keys())
        values = list(clinician_discontinuations.values())
        ax2.bar(labels, values)
        ax2.set_title("Discontinuations by Clinician Profile")
        ax2.set_ylabel("Count")
        ax2.set_xticklabels(labels, rotation=45, ha="right")
    
    plt.tight_layout()
    plt.savefig("enhanced_discontinuation_analysis.png")
    print("\nSaved visualization to enhanced_discontinuation_analysis.png")

if __name__ == "__main__":
    patient_histories, sim = run_enhanced_discontinuation_simulation()
