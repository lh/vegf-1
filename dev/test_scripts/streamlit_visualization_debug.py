"""
Debug script to verify discontinuation data is properly passed to visualization.

This script simulates how the Streamlit app processes the discontinuation stats
and how they should be displayed in the UI.
"""

from simulation.config import SimulationConfig
from simulation.enhanced_discontinuation_manager import EnhancedDiscontinuationManager
import numpy as np
from datetime import datetime, timedelta
import yaml
import json
import matplotlib.pyplot as plt
import pandas as pd

# Ensure reproducibility
np.random.seed(42)

def generate_discontinuation_plot(results):
    """Generate a plot of discontinuation types."""
    # Check if we have valid data
    if "discontinuation_counts" not in results:
        print("No discontinuation data available in results")
        return None
    
    # Create the plot from actual data
    disc_counts = results["discontinuation_counts"]
    types = list(disc_counts.keys())
    counts = list(disc_counts.values())
    
    # Check if we have any non-zero counts
    if sum(counts) == 0:
        print("All discontinuation counts are zero")
        return None
    
    # Create plot with actual data
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Use a colormap to make the bars more visually appealing
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(types)))
    bars = ax.bar(types, counts, color=colors)
    
    # Add percentages on top of bars
    total = sum(counts)
    for bar, count, color in zip(bars, counts, colors):
        if count > 0:  # Only add text if count is non-zero
            percentage = count / total * 100 if total > 0 else 0
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.1,  # Small offset
                f"{percentage:.1f}%",
                ha='center',
                va='bottom',
                fontweight='bold',
                color='black'
            )
            
            # Add count inside bar if it's tall enough
            if count > total * 0.05:  # If at least 5% of total
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() / 2,
                    str(count),
                    ha='center',
                    va='center',
                    color='white',
                    fontweight='bold'
                )
    
    ax.set_xlabel("Discontinuation Type")
    ax.set_ylabel("Count")
    ax.set_title("Treatment Discontinuation by Type")
    ax.grid(True, linestyle='--', alpha=0.3, axis='y')
    
    # Add total discontinuations as a footer
    fig.text(0.5, 0.01, f"Total Discontinuations: {total}", ha='center')
    
    # Ensure y-axis starts at zero
    ax.set_ylim(bottom=0)
    
    # Display plot stats
    print(f"Discontinuation counts: {disc_counts}")
    print(f"Total discontinuations: {total}")
    
    # Save the plot to verify it's working
    plt.savefig("discontinuation_plot_test.png")
    print("Saved plot to discontinuation_plot_test.png")
    
    return fig

# Simulate how the Streamlit app processes discontinuation manager stats

# Create a discontinuation manager with our fix
print("Creating discontinuation manager...")
with open('protocols/parameter_sets/eylea/discontinuation_parameters.yaml', 'r') as f:
    file_params = yaml.safe_load(f)

# Get the discontinuation config section
disc_config = file_params.get("discontinuation", {})
print(f"Loaded discontinuation config: {disc_config['enabled'] if 'enabled' in disc_config else 'enabled flag missing'}")

# Create discontinuation manager
manager = EnhancedDiscontinuationManager(file_params)
print(f"Discontinuation manager enabled: {manager.enabled}")

# Simulate discontinuations happening (fill stats)
manager.stats["stable_max_interval_discontinuations"] = 250
manager.stats["random_administrative_discontinuations"] = 120
manager.stats["treatment_duration_discontinuations"] = 180
manager.stats["premature_discontinuations"] = 80
manager.stats["total_discontinuations"] = 630

# Create sample results that would be passed to visualization
simulation_results = {
    "simulation_type": "ABS",
    "population_size": 1000,
    "duration_years": 5,
    "enable_clinician_variation": True,
    "planned_discontinue_prob": 0.2,
    "admin_discontinue_prob": 0.05,
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "patient_count": 1000
}

# Add discontinuation counts to results the same way simulation_runner.py does
discontinuation_counts = {
    "Planned": 0,
    "Administrative": 0,
    "Time-based": 0,
    "Premature": 0
}

if hasattr(manager, 'stats'):
    stats = manager.stats
    
    # Extract values from the stats dictionary
    discontinuation_counts["Planned"] = stats.get("stable_max_interval_discontinuations", 0)
    discontinuation_counts["Administrative"] = stats.get("random_administrative_discontinuations", 0)
    discontinuation_counts["Time-based"] = stats.get("treatment_duration_discontinuations", 0)
    discontinuation_counts["Premature"] = stats.get("premature_discontinuations", 0)

simulation_results["discontinuation_counts"] = discontinuation_counts
simulation_results["total_discontinuations"] = sum(discontinuation_counts.values())

# Display simulation results that would be used for visualization
print("\nSimulation results for visualization:")
for key, value in simulation_results.items():
    if key not in ["discontinuation_counts"]:
        print(f"{key}: {value}")

print("\nDiscontinuation counts:")
for disc_type, count in simulation_results["discontinuation_counts"].items():
    print(f"{disc_type}: {count}")

# Create and display a data frame like the Streamlit app does
disc_counts = simulation_results["discontinuation_counts"]
total = sum(disc_counts.values())

data = []
for disc_type, count in disc_counts.items():
    percentage = (count / total * 100) if total > 0 else 0
    data.append({
        "Type": disc_type,
        "Count": count,
        "Percentage": f"{percentage:.1f}%"
    })

df = pd.DataFrame(data)
print("\nDataFrame that would be displayed in Streamlit:")
print(df)

# Generate the discontinuation plot
print("\nGenerating discontinuation plot...")
generate_discontinuation_plot(simulation_results)

print("\nSTREAMLIT SIMULATION")
print("Now let's simulate how the Streamlit app would create the results from scratch")

# Create simulation parameters like those set in the UI
params = {
    "simulation_type": "ABS",
    "duration_years": 5,
    "population_size": 1000,
    "enable_clinician_variation": True,
    "planned_discontinue_prob": 0.2,
    "admin_discontinue_prob": 0.05,
    "consecutive_stable_visits": 3,
    "monitoring_schedule": [12, 24, 36],
    "no_monitoring_for_admin": True,
    "recurrence_risk_multiplier": 1.0
}

# Create a configuration like the Streamlit app would
config = SimulationConfig.from_yaml('test_simulation')

# Configure like simulation_runner.py does
config.num_patients = params["population_size"]
config.duration_days = params["duration_years"] * 365
config.simulation_type = params["simulation_type"].lower()

# Update discontinuation settings - create the structure if it doesn't exist
if not hasattr(config, 'parameters'):
    config.parameters = {}

# Ensure the discontinuation structure exists with correct fields
if 'discontinuation' not in config.parameters:
    config.parameters['discontinuation'] = {
        'enabled': True,
        'criteria': {
            'stable_max_interval': {
                'consecutive_visits': 3,
                'probability': 0.2
            },
            'random_administrative': {
                'annual_probability': 0.05
            },
            'treatment_duration': {
                'threshold_weeks': 52,
                'probability': 0.1
            }
        },
        'monitoring': {
            'follow_up_schedule': [12, 24, 36],
            'recurrence_detection_probability': 0.87
        },
        'retreatment': {
            'eligibility_criteria': {
                'detected_fluid': True,
                'vision_loss_letters': 5
            },
            'probability': 0.95
        }
    }
    print("Created default discontinuation settings")
else:
    # Make sure 'enabled' is True
    config.parameters['discontinuation']['enabled'] = True
    print("Ensured discontinuation is enabled")

# Manually create a discontinuation manager with this config
discontinuation_params = config.get_treatment_discontinuation_params()
print("\nDiscontinuation params from config:")
print(f"Enabled flag present: {'enabled' in discontinuation_params}")
if "enabled" not in discontinuation_params:
    discontinuation_params["enabled"] = True
    print("Added enabled flag")

stream_manager = EnhancedDiscontinuationManager({"discontinuation": discontinuation_params})
print(f"Stream discontinuation manager enabled: {stream_manager.enabled}")

# Add stats (simulate what would happen during a run)
stream_manager.stats["stable_max_interval_discontinuations"] = 250
stream_manager.stats["random_administrative_discontinuations"] = 120
stream_manager.stats["treatment_duration_discontinuations"] = 180
stream_manager.stats["premature_discontinuations"] = 80
stream_manager.stats["total_discontinuations"] = 630

# Simulate what the Streamlit app would do with this manager
streamed_results = {
    "simulation_type": params["simulation_type"],
    "population_size": params["population_size"],
    "duration_years": params["duration_years"],
    "enable_clinician_variation": params["enable_clinician_variation"],
    "planned_discontinue_prob": params["planned_discontinue_prob"],
    "admin_discontinue_prob": params["admin_discontinue_prob"],
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "patient_count": params["population_size"]
}

# Extract stats the same way as simulation_runner.py
stream_discontinuation_counts = {
    "Planned": 0,
    "Administrative": 0,
    "Time-based": 0,
    "Premature": 0
}

if hasattr(stream_manager, 'stats'):
    stats = stream_manager.stats
    
    # Extract values from the stats dictionary
    stream_discontinuation_counts["Planned"] = stats.get("stable_max_interval_discontinuations", 0)
    stream_discontinuation_counts["Administrative"] = stats.get("random_administrative_discontinuations", 0)
    stream_discontinuation_counts["Time-based"] = stats.get("treatment_duration_discontinuations", 0)
    stream_discontinuation_counts["Premature"] = stats.get("premature_discontinuations", 0)

streamed_results["discontinuation_counts"] = stream_discontinuation_counts
streamed_results["total_discontinuations"] = sum(stream_discontinuation_counts.values())

# Create a data frame like the Streamlit app would
stream_disc_counts = streamed_results["discontinuation_counts"]
stream_total = sum(stream_disc_counts.values())

stream_data = []
for disc_type, count in stream_disc_counts.items():
    percentage = (count / stream_total * 100) if stream_total > 0 else 0
    stream_data.append({
        "Type": disc_type,
        "Count": count,
        "Percentage": f"{percentage:.1f}%"
    })

stream_df = pd.DataFrame(stream_data)
print("\nDataFrame from streamed results:")
print(stream_df)

# Generate the discontinuation plot
print("\nGenerating streamed discontinuation plot...")
generated_plot = generate_discontinuation_plot(streamed_results)

print("\nVerification complete. If the Streamlit app is still not displaying the discontinuation chart:")
print("1. Check if debug statements in the app show discontinuation counts > 0")
print("2. Verify that the dataframe is being displayed")
print("3. Confirm that the generate_discontinuation_plot function is called")