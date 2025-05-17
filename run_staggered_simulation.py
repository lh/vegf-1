"""Run staggered patient enrollment simulation and compare with standard approach.

This script executes both standard and staggered agent-based simulations using the
same configuration, compares their results, and generates visualizations showing:

1. Patient enrollment distribution over time (staggered only)
2. Mean visual acuity by calendar time (both methods)
3. Mean visual acuity by patient time (staggered only)
4. Dual timeframe visualization (staggered only)
5. Comparison of resource utilization patterns

The staggered simulation uses a Poisson process to model patient arrivals over time,
providing a more realistic model of how patient populations grow in clinical settings.

The script also analyzes the dual timeframe aspects of the simulation, showing how
calendar time (real-world elapsed time) and patient time (time since individual enrollment)
metrics differ in important ways.

Example Usage:
    python run_staggered_simulation.py                     # Uses default test_simulation.yaml
    python run_staggered_simulation.py eylea_literature_based  # Uses specified configuration
"""

import os
import sys
import argparse
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set matplotlib style for better visualization
plt.style.use('ggplot')

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# Import simulation components
from simulation.config import SimulationConfig
from simulation.abs import AgentBasedSimulation
from simulation.staggered_abs import StaggeredABS, run_staggered_abs
from treat_and_extend_abs import run_treat_and_extend_abs as run_standard_abs
from visualization.acuity_viz import (
    plot_mean_acuity_with_sample_size,
    plot_dual_timeframe_acuity,
    plot_patient_acuity_by_patient_time
)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Run staggered patient enrollment simulation and compare with standard approach.')
    parser.add_argument('config_name', nargs='?', default='test_simulation',
                       help='Name of the configuration file (without .yaml extension)')
    parser.add_argument('--arrival-rate', type=float, default=10.0,
                       help='Average number of new patients per week for staggered simulation')
    parser.add_argument('--random-seed', type=int, default=None,
                       help='Random seed for reproducibility')
    parser.add_argument('--duration-years', type=float, default=1.0,
                       help='Simulation duration in years')
    return parser.parse_args()

def prepare_simulation_data(config_name, patient_arrival_rate, random_seed, duration_years):
    """Prepare simulation configuration and parameters."""
    # Load configuration
    config = SimulationConfig.from_yaml(config_name)
    
    # Set simulation start date
    start_date = datetime(2023, 1, 1)
    
    # Calculate end date from duration
    end_date = start_date + timedelta(days=int(duration_years * 365))
    
    # Set population size for standard simulation
    # We need to match the expected total population of staggered simulation
    # In a Poisson process, the expected number of arrivals = rate * time period
    # If rate is in patients/week and we want X years, the formula is:
    # patients = rate_per_week * 52 * years
    total_patients = int(patient_arrival_rate * 52 * duration_years)
    
    # Set population size in config
    config.num_patients = total_patients
    
    # Set duration in config
    config.duration_days = int(duration_years * 365)
    
    # Set end date
    config.end_date = end_date
    
    return config, start_date, end_date

def run_standard_simulation(config, verbose=True):
    """Run standard ABS simulation with all patients at start."""
    if verbose:
        print(f"Running standard ABS simulation with {config.num_patients} patients...")
    
    # Run simulation
    patient_histories = run_standard_abs(config=config, verbose=verbose)
    
    return patient_histories

def run_staggered_simulation(config, start_date, arrival_rate, random_seed, verbose=True):
    """Run staggered ABS simulation with Poisson patient arrivals."""
    if verbose:
        print(f"Running staggered ABS simulation with arrival rate {arrival_rate} patients/week...")
    
    # Run simulation
    simulation_results = run_staggered_abs(
        config=config,
        start_date=start_date,
        patient_arrival_rate=arrival_rate,
        random_seed=random_seed,
        verbose=verbose
    )
    
    # Extract patient histories and enrollment dates
    patient_histories = {}

    if isinstance(simulation_results, dict):
        if 'patient_histories' in simulation_results:
            patient_histories = simulation_results.get('patient_histories', {})
        else:
            # If run_staggered_abs already returned just the patient histories
            patient_histories = simulation_results

    if verbose:
        print(f"Staggered simulation returned {len(patient_histories)} patient histories")
        if patient_histories and len(patient_histories) > 0:
            first_id = next(iter(patient_histories))
            visits = patient_histories.get(first_id, [])
            print(f"First patient: {first_id} with {len(visits)} visits")
    
    return patient_histories

def extract_vision_data(patient_histories):
    """Extract visual acuity data from patient histories."""
    # Process patient histories into DataFrame
    vision_data = []
    
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            # Extract relevant data
            visit_date = visit.get('date', None)
            if not visit_date:
                continue
                
            vision = visit.get('vision', None)
            if vision is None:
                continue
                
            # Extract calendar and patient times if available
            calendar_time = visit.get('calendar_time', visit_date)
            days_since_enrollment = visit.get('days_since_enrollment', None)
            weeks_since_enrollment = visit.get('weeks_since_enrollment', None)
            
            # Create record
            record = {
                'patient_id': patient_id,
                'date': visit_date,
                'vision': vision,
                'calendar_time': calendar_time
            }
            
            # Add patient time if available
            if days_since_enrollment is not None:
                record['days_since_enrollment'] = days_since_enrollment
                
            if weeks_since_enrollment is not None:
                record['weeks_since_enrollment'] = weeks_since_enrollment
                
            vision_data.append(record)
    
    # Convert to DataFrame
    df = pd.DataFrame(vision_data)
    
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        
    return df

def plot_enrollment_distribution(patient_histories, output_file="enrollment_distribution.png"):
    """Plot patient enrollment distribution for staggered simulation."""
    # Extract enrollment dates
    enrollment_dates = []
    
    for patient_id, visits in patient_histories.items():
        if visits:
            # First visit is enrollment date
            enrollment_dates.append(visits[0].get('date'))
    
    # Convert to pandas Series for easier handling
    enrollment_series = pd.Series(enrollment_dates)
    
    # Create histogram by month
    enrollment_by_month = enrollment_series.dt.to_period('M').value_counts().sort_index()
    
    # Plot
    plt.figure(figsize=(12, 6))
    enrollment_by_month.plot(kind='bar', color='skyblue')
    plt.title('Patient Enrollment Distribution by Month')
    plt.xlabel('Month')
    plt.ylabel('Number of Patients')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    
    print(f"Saved enrollment distribution to {output_file}")
    
    return enrollment_by_month

def calculate_mean_vision_by_calendar_time(df, freq='M'):
    """Calculate mean vision by calendar time with specified frequency."""
    # Convert date to period with the specified frequency
    df['period'] = df['date'].dt.to_period(freq)
    
    # Group by period and calculate mean
    vision_by_period = df.groupby('period')['vision'].agg(['mean', 'count', 'std']).reset_index()
    
    # Convert period to datetime for plotting
    vision_by_period['date'] = vision_by_period['period'].dt.to_timestamp()
    
    return vision_by_period

def calculate_mean_vision_by_patient_time(df, bin_width=4):
    """Calculate mean vision by patient time (weeks since enrollment)."""
    # Check if patient time is available
    if 'weeks_since_enrollment' not in df.columns:
        return None
    
    # Create bins based on weeks since enrollment
    df['week_bin'] = (df['weeks_since_enrollment'] // bin_width) * bin_width
    
    # Group by bins and calculate metrics
    vision_by_week = df.groupby('week_bin')['vision'].agg(['mean', 'count', 'std']).reset_index()
    
    return vision_by_week

def plot_vision_comparison(standard_vision, staggered_vision, output_file="vision_comparison.png"):
    """Plot comparison of mean vision between standard and staggered simulations."""
    plt.figure(figsize=(12, 6))
    
    # Plot standard simulation results
    plt.plot(standard_vision['date'], standard_vision['mean'], 
             label='Standard (All patients at start)', marker='o', color='blue')
    
    # Add confidence interval
    plt.fill_between(
        standard_vision['date'],
        standard_vision['mean'] - 1.96 * standard_vision['std'] / np.sqrt(standard_vision['count']),
        standard_vision['mean'] + 1.96 * standard_vision['std'] / np.sqrt(standard_vision['count']),
        alpha=0.2, color='blue'
    )
    
    # Plot staggered simulation results
    plt.plot(staggered_vision['date'], staggered_vision['mean'], 
             label='Staggered (Poisson arrivals)', marker='s', color='green')
    
    # Add confidence interval
    plt.fill_between(
        staggered_vision['date'],
        staggered_vision['mean'] - 1.96 * staggered_vision['std'] / np.sqrt(staggered_vision['count']),
        staggered_vision['mean'] + 1.96 * staggered_vision['std'] / np.sqrt(staggered_vision['count']),
        alpha=0.2, color='green'
    )
    
    # Add sample size information
    ax1 = plt.gca()
    ax2 = ax1.twinx()
    
    # Plot number of patients in each time bin
    ax2.plot(standard_vision['date'], standard_vision['count'], 
             linestyle='--', color='darkblue', alpha=0.5, label='Standard patient count')
    ax2.plot(staggered_vision['date'], staggered_vision['count'], 
             linestyle='--', color='darkgreen', alpha=0.5, label='Staggered patient count')
    
    # Customize plot
    plt.title('Mean Visual Acuity Over Calendar Time: Standard vs. Staggered')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Mean Visual Acuity (ETDRS Letters)')
    ax2.set_ylabel('Number of Patients')
    
    # Add legend for both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower right')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    
    print(f"Saved vision comparison to {output_file}")

def plot_patient_time_vision(vision_by_patient_time, output_file="vision_by_patient_time.png"):
    """Plot mean vision by patient time (weeks since enrollment)."""
    if vision_by_patient_time is None:
        print("Patient time data not available - skipping patient time vision plot")
        return
    
    plt.figure(figsize=(12, 6))
    
    # Plot mean vision
    plt.plot(vision_by_patient_time['week_bin'], vision_by_patient_time['mean'], 
             marker='o', color='purple')
    
    # Add confidence interval
    plt.fill_between(
        vision_by_patient_time['week_bin'],
        vision_by_patient_time['mean'] - 1.96 * vision_by_patient_time['std'] / np.sqrt(vision_by_patient_time['count']),
        vision_by_patient_time['mean'] + 1.96 * vision_by_patient_time['std'] / np.sqrt(vision_by_patient_time['count']),
        alpha=0.2, color='purple'
    )
    
    # Add sample size information
    ax1 = plt.gca()
    ax2 = ax1.twinx()
    
    # Plot number of patients in each week bin
    ax2.bar(vision_by_patient_time['week_bin'], vision_by_patient_time['count'], 
            alpha=0.2, color='purple', width=3)
    
    # Customize plot
    plt.title('Mean Visual Acuity by Patient Time (Weeks Since Enrollment)')
    ax1.set_xlabel('Weeks Since Enrollment')
    ax1.set_ylabel('Mean Visual Acuity (ETDRS Letters)')
    ax2.set_ylabel('Number of Patients')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    
    print(f"Saved patient time vision plot to {output_file}")

def calculate_resource_utilization(patient_histories, bin_width='W'):
    """Calculate resource utilization by calendar time."""
    # Extract visit dates and actions
    visit_data = []
    
    for patient_id, visits in patient_histories.items():
        for visit in visits:
            visit_date = visit.get('date', None)
            if not visit_date:
                continue
                
            actions = visit.get('actions', [])
            if isinstance(actions, str):
                try:
                    # Try to parse string representation of list
                    actions = eval(actions)
                except:
                    actions = [actions]
            
            # Create record with visit date and actions
            record = {
                'patient_id': patient_id,
                'date': visit_date,
                'visit': 1,
                'injection': 1 if 'injection' in actions else 0,
                'oct_scan': 1 if 'oct_scan' in actions else 0,
                'vision_test': 1 if 'vision_test' in actions else 0
            }
            
            visit_data.append(record)
    
    # Convert to DataFrame
    df = pd.DataFrame(visit_data)
    
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # Resample to bin width
    df['date_bin'] = df['date'].dt.to_period(bin_width)
    
    # Group by date bin and aggregate
    utilization = df.groupby('date_bin').agg({
        'visit': 'sum',
        'injection': 'sum',
        'oct_scan': 'sum',
        'vision_test': 'sum'
    }).reset_index()
    
    # Convert period to datetime for plotting
    utilization['date'] = utilization['date_bin'].dt.to_timestamp()
    
    return utilization

def plot_resource_utilization_comparison(standard_util, staggered_util, output_file="resource_utilization.png"):
    """Plot comparison of resource utilization between standard and staggered simulations."""
    plt.figure(figsize=(15, 10))
    
    # Create 2x2 grid of subplots
    resources = ['visit', 'injection', 'oct_scan', 'vision_test']
    titles = ['Total Visits', 'Injections', 'OCT Scans', 'Vision Tests']
    
    for i, (resource, title) in enumerate(zip(resources, titles)):
        plt.subplot(2, 2, i+1)
        
        # Plot standard simulation
        plt.plot(standard_util['date'], standard_util[resource], 
                 label='Standard', marker='o', color='blue', alpha=0.7)
        
        # Plot staggered simulation
        plt.plot(staggered_util['date'], staggered_util[resource], 
                 label='Staggered', marker='s', color='green', alpha=0.7)
        
        plt.title(title)
        plt.xlabel('Date')
        plt.ylabel('Count')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    
    print(f"Saved resource utilization comparison to {output_file}")

def calculate_summary_statistics(standard_histories, staggered_histories):
    """Calculate summary statistics for both simulation approaches."""
    # Function to calculate stats for a set of patient histories
    def get_stats(histories):
        total_patients = len(histories)
        total_visits = sum(len(history) for history in histories.values())
        avg_visits_per_patient = total_visits / max(1, total_patients)
        
        # Count injections
        total_injections = 0
        for patient_id, visits in histories.items():
            for visit in visits:
                actions = visit.get('actions', [])
                if isinstance(actions, str):
                    try:
                        actions = eval(actions)
                    except:
                        actions = [actions]
                
                if 'injection' in actions:
                    total_injections += 1
        
        avg_injections_per_patient = total_injections / max(1, total_patients)
        
        return {
            'total_patients': total_patients,
            'total_visits': total_visits,
            'avg_visits_per_patient': avg_visits_per_patient,
            'total_injections': total_injections,
            'avg_injections_per_patient': avg_injections_per_patient
        }
    
    # Calculate stats for both approaches
    standard_stats = get_stats(standard_histories)
    staggered_stats = get_stats(staggered_histories)
    
    return {
        'standard': standard_stats,
        'staggered': staggered_stats
    }

def extract_enrollment_dates(patient_histories):
    """Extract enrollment dates from patient visit histories."""
    enrollment_dates = {}
    
    for patient_id, visits in patient_histories.items():
        if visits:
            # First visit is considered enrollment date
            first_visit = visits[0]
            if 'date' in first_visit:
                enrollment_dates[patient_id] = first_visit['date']
    
    return enrollment_dates

def plot_enhanced_visualizations(staggered_histories, staggered_df, start_date, end_date, output_dir):
    """Create enhanced visualizations using new acuity_viz functions."""
    # Extract enrollment dates
    enrollment_dates = extract_enrollment_dates(staggered_histories)
    
    # Convert patient data to format expected by visualization functions
    patient_data = {}
    for patient_id, visits in staggered_histories.items():
        patient_data[patient_id] = []
        for visit in visits:
            visit_dict = {
                'date': visit.get('date'),
                'vision': visit.get('vision')
            }
            # Add actions if available
            if 'actions' in visit:
                visit_dict['actions'] = visit.get('actions')
            patient_data[patient_id].append(visit_dict)
    
    # 1. Plot dual timeframe visualization
    plot_dual_timeframe_acuity(
        patient_data=patient_data,
        enrollment_dates=enrollment_dates,
        start_date=start_date,
        end_date=end_date,
        show=False,
        save_path=os.path.join(output_dir, "dual_timeframe_acuity.png")
    )
    print(f"Saved dual timeframe visualization to {output_dir}/dual_timeframe_acuity.png")
    
    # 2. Plot mean acuity with sample size for calendar time
    plot_mean_acuity_with_sample_size(
        patient_data=patient_data,
        enrollment_dates=enrollment_dates,
        start_date=start_date,
        end_date=end_date,
        time_unit='calendar',
        show=False,
        save_path=os.path.join(output_dir, "mean_acuity_calendar_time.png"),
        title="Mean Visual Acuity by Calendar Time with Sample Size"
    )
    print(f"Saved enhanced calendar time plot to {output_dir}/mean_acuity_calendar_time.png")
    
    # 3. Plot mean acuity with sample size for patient time
    plot_mean_acuity_with_sample_size(
        patient_data=patient_data,
        enrollment_dates=enrollment_dates,
        start_date=start_date,
        end_date=end_date,
        time_unit='patient',
        show=False,
        save_path=os.path.join(output_dir, "mean_acuity_patient_time.png"),
        title="Mean Visual Acuity by Patient Time with Sample Size"
    )
    print(f"Saved enhanced patient time plot to {output_dir}/mean_acuity_patient_time.png")
    
    # 4. Plot individual patient trajectories by patient time
    # Select a few representative patients
    patient_ids = list(patient_data.keys())
    if len(patient_ids) > 5:
        sample_patients = patient_ids[:5]  # Take first 5 patients for example
    else:
        sample_patients = patient_ids
    
    for patient_id in sample_patients:
        if patient_id in enrollment_dates:
            plot_patient_acuity_by_patient_time(
                patient_id=patient_id,
                history=patient_data[patient_id],
                enrollment_date=enrollment_dates[patient_id],
                max_weeks=52,
                show=False,
                save_path=os.path.join(output_dir, f"patient_{patient_id}_by_time.png")
            )
    
    print(f"Saved individual patient trajectories for {len(sample_patients)} sample patients")

def main():
    """Main execution function."""
    # Parse arguments
    args = parse_args()
    
    # Prepare simulation configuration
    config, start_date, end_date = prepare_simulation_data(
        args.config_name, 
        args.arrival_rate, 
        args.random_seed, 
        args.duration_years
    )
    
    # Print simulation parameters
    print("\n=== Simulation Parameters ===")
    print(f"Configuration: {args.config_name}")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    print(f"Duration: {args.duration_years} years")
    print(f"Patient arrival rate: {args.arrival_rate} patients/week")
    print(f"Expected total patients: {int(args.arrival_rate * 52 * args.duration_years)}")
    print(f"Random seed: {args.random_seed}")
    
    # Run standard simulation (all patients at start)
    standard_histories = run_standard_simulation(config)
    
    # Run staggered simulation (Poisson arrivals)
    print("Running staggered simulation with Poisson patient arrivals...")
    staggered_histories = run_staggered_simulation(
        config,
        start_date,
        args.arrival_rate,
        args.random_seed
    )
    print(f"Staggered simulation completed. Got {len(staggered_histories)} patient histories.")
    
    # Extract vision data
    standard_df = extract_vision_data(standard_histories)
    staggered_df = extract_vision_data(staggered_histories)
    
    # Create output directory
    output_dir = Path("output/staggered_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Debug information
    print(f"\nDebug Information:")
    print(f"Standard histories: {len(standard_histories)} patients")
    if len(standard_histories) > 0:
        first_id = next(iter(standard_histories))
        print(f"  First standard patient: {first_id} with {len(standard_histories[first_id])} visits")

    print(f"Staggered histories: {len(staggered_histories)} patients")
    if len(staggered_histories) > 0:
        first_id = next(iter(staggered_histories))
        print(f"  First staggered patient: {first_id} with {len(staggered_histories[first_id])} visits")
    
    # Plot enrollment distribution (staggered only)
    enrollment_by_month = plot_enrollment_distribution(
        staggered_histories, 
        output_file=output_dir / "enrollment_distribution.png"
    )
    
    # Calculate mean vision by calendar time
    standard_vision_by_month = calculate_mean_vision_by_calendar_time(standard_df, freq='M')
    staggered_vision_by_month = calculate_mean_vision_by_calendar_time(staggered_df, freq='M')
    
    # Plot vision comparison
    plot_vision_comparison(
        standard_vision_by_month,
        staggered_vision_by_month,
        output_file=output_dir / "vision_comparison.png"
    )
    
    # Calculate and plot mean vision by patient time (staggered only)
    staggered_vision_by_patient_time = calculate_mean_vision_by_patient_time(staggered_df, bin_width=4)
    plot_patient_time_vision(
        staggered_vision_by_patient_time,
        output_file=output_dir / "vision_by_patient_time.png"
    )
    
    # Calculate resource utilization
    standard_util = calculate_resource_utilization(standard_histories, bin_width='W')
    staggered_util = calculate_resource_utilization(staggered_histories, bin_width='W')
    
    # Plot resource utilization comparison
    plot_resource_utilization_comparison(
        standard_util,
        staggered_util,
        output_file=output_dir / "resource_utilization.png"
    )
    
    # Calculate summary statistics
    stats = calculate_summary_statistics(standard_histories, staggered_histories)
    
    # Create enhanced visualizations with new acuity_viz functions
    plot_enhanced_visualizations(
        staggered_histories,
        staggered_df,
        start_date,
        end_date,
        output_dir
    )
    
    # Print summary statistics
    print("\n=== Summary Statistics ===")
    print("Standard Simulation:")
    for key, value in stats['standard'].items():
        if isinstance(value, (int, np.integer)):
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value:.2f}")
    
    print("\nStaggered Simulation:")
    for key, value in stats['staggered'].items():
        if isinstance(value, (int, np.integer)):
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value:.2f}")
    
    print("\n=== Analysis Complete ===")
    print(f"Output files saved to: {output_dir}")
    print("Enhanced visualizations include:")
    print("  - Dual timeframe comparison (calendar time vs. patient time)")
    print("  - Mean acuity with sample size indicators")
    print("  - Individual patient trajectories by patient time")

if __name__ == "__main__":
    main()