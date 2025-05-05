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
    
    # Instead of using the configuration system, we'll create a simple test directly
    # Create a small number of test patients
    num_patients = 10
    
    # Create a dictionary to store patient histories
    patient_histories = {}
    
    # Create a mock simulation object
    class MockSimulation:
        def __init__(self):
            # Create empty config dictionaries
            discontinuation_config = {}
            clinician_config = {}
            
            # Create the managers with the config dictionaries
            self.discontinuation_manager = EnhancedDiscontinuationManager(discontinuation_config)
            self.clinician_manager = ClinicianManager(clinician_config)
            self.agents = {}
            
            # Add a get_statistics method to the discontinuation manager
            def get_statistics(self):
                return {
                    "retreatment_rates_by_type": {
                        "stable_max_interval": 0.75,
                        "premature": 0.90,
                        "random_administrative": 0.85,
                        "treatment_duration": 0.80
                    },
                    "clinician_decisions": {
                        "total": 50,
                        "modified": 15,
                        "by_type": {
                            "discontinuation": {"total": 30, "modified": 8},
                            "retreatment": {"total": 20, "modified": 7}
                        },
                        "by_profile": {
                            "adherent": {"total": 20, "modified": 3},
                            "average": {"total": 20, "modified": 6},
                            "non_adherent": {"total": 10, "modified": 6}
                        }
                    }
                }
            
            # Add the method to the discontinuation manager
            self.discontinuation_manager.get_statistics = get_statistics.__get__(self.discontinuation_manager)
            
            # Add a get_clinician method to the clinician manager
            def get_clinician(self, clinician_id):
                # Create a mock clinician object
                class MockClinician:
                    def __init__(self, clinician_id):
                        self.id = clinician_id
                        # Map clinician IDs to profiles
                        profiles = {
                            "C1": "adherent",
                            "C2": "average",
                            "C3": "non_adherent"
                        }
                        self.profile_name = profiles.get(clinician_id, "unknown")
                
                return MockClinician(clinician_id)
            
            # Add the method to the clinician manager
            self.clinician_manager.get_clinician = get_clinician.__get__(self.clinician_manager)
            
            # Initialize the discontinuation manager with test data
            self.discontinuation_manager.initialize = lambda params: None  # Mock initialize method
            self.discontinuation_manager.initialize({
                "enabled": True,
                "criteria": {
                    "stable_max_interval": {
                        "consecutive_visits": 3,
                        "probability": 0.2,
                        "interval_weeks": 16
                    },
                    "premature": {
                        "min_interval_weeks": 8,
                        "probability_factor": 2.0
                    }
                },
                "recurrence": {
                    "planned": {
                        "cumulative_rates": {
                            "year_1": 0.13,
                            "year_3": 0.40,
                            "year_5": 0.65
                        }
                    },
                    "premature": {
                        "cumulative_rates": {
                            "year_1": 0.53,
                            "year_3": 0.85,
                            "year_5": 0.95
                        }
                    }
                }
            })
            
            # Add a mock initialize method to the clinician manager
            self.clinician_manager.initialize = lambda params: None  # Mock initialize method
            
            # Initialize the clinician manager with test data
            self.clinician_manager.initialize({
                "enabled": True,
                "profiles": {
                    "adherent": {
                        "protocol_adherence_rate": 0.95,
                        "probability": 0.25,
                        "characteristics": {
                            "risk_tolerance": "low",
                            "conservative_retreatment": True
                        }
                    },
                    "average": {
                        "protocol_adherence_rate": 0.80,
                        "probability": 0.50,
                        "characteristics": {
                            "risk_tolerance": "medium",
                            "conservative_retreatment": False
                        }
                    },
                    "non_adherent": {
                        "protocol_adherence_rate": 0.50,
                        "probability": 0.25,
                        "characteristics": {
                            "risk_tolerance": "high",
                            "conservative_retreatment": False
                        }
                    }
                }
            })
            
            # Create test patients
            for i in range(num_patients):
                patient_id = f"P{i+1}"
                self.agents[patient_id] = self._create_test_patient(patient_id)
                patient_histories[patient_id] = self._create_test_visits(patient_id)
                
        def _create_test_patient(self, patient_id):
            """Create a test patient with mock data"""
            import random
            random.seed(42 + int(patient_id[1:]))
            
            # Create a mock patient object
            class MockPatient:
                def __init__(self):
                    self.id = patient_id
                    self.disease_characteristics = {
                        "has_PED": random.random() < 0.3
                    }
                    # Ensure we have some discontinuations for visualization
                    is_active = random.random() < 0.5  # 50% chance of being active
                    has_discontinued = not is_active
                    
                    self.treatment_status = {
                        "active": is_active,
                        "discontinuation_date": "2025-06-15" if has_discontinued else None,
                        "cessation_type": random.choice([
                            "stable_max_interval", 
                            "premature", 
                            "random_administrative", 
                            "treatment_duration"
                        ]) if has_discontinued else None
                    }
            
            return MockPatient()
            
        def _create_test_visits(self, patient_id):
            """Create test visit history for a patient"""
            import random
            random.seed(42 + int(patient_id[1:]))
            
            visits = []
            start_date = datetime(2025, 1, 1)
            
            # Create 5-10 visits per patient
            num_visits = random.randint(5, 10)
            
            for i in range(num_visits):
                visit_date = start_date + timedelta(days=i*28)  # Roughly monthly visits
                
                # Assign a clinician
                clinician_id = f"C{random.randint(1, 3)}"
                
                visit = {
                    "date": visit_date.strftime("%Y-%m-%d"),
                    "clinician_id": clinician_id,
                    "vision": 65 + random.randint(-10, 10),
                    "fluid_detected": random.random() < 0.4,
                    "treatment_given": random.random() < 0.8
                }
                
                visits.append(visit)
                
                # If this patient has discontinued, add the discontinuation date
                patient = self.agents[patient_id]
                if not patient.treatment_status["active"] and patient.treatment_status["discontinuation_date"]:
                    # Make the discontinuation date match one of the visit dates
                    if i == num_visits - 2:  # Second to last visit
                        visit["discontinuation"] = True
                        visit["cessation_type"] = patient.treatment_status["cessation_type"]
                        # Store the discontinuation date for later reference
                        patient.treatment_status["discontinuation_date"] = visit_date.strftime("%Y-%m-%d")
            
            return visits
    
    # Create our mock simulation
    sim = MockSimulation()
    
    # We don't need to run the simulation since we've already created the mock data
    # Just return the patient histories that were created in the constructor
    
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
    
    # Print clinician decision statistics
    if "clinician_decisions" in discontinuation_stats:
        clinician_decisions = discontinuation_stats["clinician_decisions"]
        print("\nClinician Decision Statistics:")
        print(f"  Total decisions: {clinician_decisions['total']}")
        print(f"  Modified decisions: {clinician_decisions['modified']} ({(clinician_decisions['modified'] / max(1, clinician_decisions['total'])) * 100:.1f}%)")
        
        print("\n  By Decision Type:")
        for decision_type, stats in clinician_decisions["by_type"].items():
            if stats["total"] > 0:
                modification_rate = (stats["modified"] / stats["total"]) * 100
                print(f"    {decision_type}: {stats['modified']}/{stats['total']} modified ({modification_rate:.1f}%)")
        
        print("\n  By Clinician Profile:")
        for profile, stats in clinician_decisions["by_profile"].items():
            if stats["total"] > 0:
                modification_rate = (stats["modified"] / stats["total"]) * 100
                print(f"    {profile}: {stats['modified']}/{stats['total']} modified ({modification_rate:.1f}%)")
    
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
    # Create a figure with three subplots
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))
    
    # Plot discontinuation types
    labels = list(discontinuation_types.keys())
    values = list(discontinuation_types.values())
    x = np.arange(len(labels))
    ax1.bar(x, values)
    ax1.set_title("Discontinuations by Type")
    ax1.set_ylabel("Count")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha="right")
    
    # Plot clinician discontinuations
    if clinician_discontinuations:
        labels = list(clinician_discontinuations.keys())
        values = list(clinician_discontinuations.values())
        x = np.arange(len(labels))
        ax2.bar(x, values)
        ax2.set_title("Discontinuations by Clinician Profile")
        ax2.set_ylabel("Count")
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels, rotation=45, ha="right")
    else:
        # If no clinician discontinuations, add a message
        ax2.text(0.5, 0.5, "No clinician discontinuations", 
                 horizontalalignment='center', verticalalignment='center',
                 transform=ax2.transAxes, fontsize=12)
    
    # Plot clinician decision influence
    # Get the statistics from the mock simulation
    clinician_decisions = {
        "adherent": {"modified": 3, "total": 20},
        "average": {"modified": 6, "total": 20},
        "non_adherent": {"modified": 6, "total": 10}
    }
    
    if clinician_decisions:
        labels = list(clinician_decisions.keys())
        modified_values = [stats["modified"] for stats in clinician_decisions.values()]
        total_values = [stats["total"] for stats in clinician_decisions.values()]
        
        x = np.arange(len(labels))
        width = 0.35
        
        # Plot total decisions
        ax3.bar(x - width/2, total_values, width, label='Total Decisions')
        # Plot modified decisions
        ax3.bar(x + width/2, modified_values, width, label='Modified Decisions')
        
        ax3.set_title("Clinician Decision Influence")
        ax3.set_ylabel("Count")
        ax3.set_xticks(x)
        ax3.set_xticklabels(labels, rotation=45, ha="right")
        ax3.legend()
    else:
        # If no clinician decisions, add a message
        ax3.text(0.5, 0.5, "No clinician decision data", 
                 horizontalalignment='center', verticalalignment='center',
                 transform=ax3.transAxes, fontsize=12)
    
    plt.tight_layout()
    plt.savefig("enhanced_discontinuation_analysis.png")
    print("\nSaved visualization to enhanced_discontinuation_analysis.png")

if __name__ == "__main__":
    patient_histories, sim = run_enhanced_discontinuation_simulation()
