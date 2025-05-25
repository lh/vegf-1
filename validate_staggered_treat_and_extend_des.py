"""
Validation script for the StaggeredTreatAndExtendDES implementation.

This script tests that the StaggeredTreatAndExtendDES implementation correctly
integrates staggered enrollment with proper discontinuation handling and
maintains the expected behavior of the treat-and-extend protocol.
"""

import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from simulation.config import SimulationConfig
from staggered_treat_and_extend_enhanced_des import StaggeredTreatAndExtendDES, run_staggered_treat_and_extend_des
from enhanced_treat_and_extend_des import run_enhanced_treat_and_extend_des

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_staggered_implementation():
    """
    Validate the staggered implementation against regular implementation.
    
    This function runs both the regular EnhancedTreatAndExtendDES and the new
    StaggeredTreatAndExtendDES with the same configuration and compares their results,
    focusing on the enrollment patterns and time tracking.
    """
    # Configuration
    config_name = "eylea_literature_based"
    logger.info(f"Running validation with config: {config_name}")
    
    # Run regular implementation
    logger.info("Running regular EnhancedTreatAndExtendDES implementation...")
    regular_results = run_enhanced_treat_and_extend_des(config_name, verbose=False)
    
    # Set up staggered parameters for testing
    staggered_params = {
        "enrollment_duration_days": 90,  # 3 months enrollment
        "relative_time_tracking": True,   # Track patient-specific time
        "rate_per_week": 10  # Expect about 120 patients over 3 months
    }
    
    # Run staggered implementation
    logger.info("Running StaggeredTreatAndExtendDES implementation...")
    staggered_results = run_staggered_treat_and_extend_des(
        config_name, 
        verbose=False,
        staggered_params=staggered_params
    )
    
    # Extract patient histories
    regular_patient_histories = regular_results.get("patient_histories", {})
    staggered_patient_histories = staggered_results.get("patient_histories", {})
    
    # Extract enrollment statistics
    enrollment_stats = staggered_results.get("enrollment_stats", {})
    logger.info("\nEnrollment Statistics:")
    for key, value in enrollment_stats.items():
        logger.info(f"  {key}: {value}")
    
    # Compare results
    logger.info("\nComparing results...")
    
    # Check patient counts
    regular_patient_count = len(regular_patient_histories)
    staggered_patient_count = len(staggered_patient_histories)
    
    logger.info(f"Regular patient count: {regular_patient_count}")
    logger.info(f"Staggered patient count: {staggered_patient_count}")
    
    # Analyze enrollment pattern
    analyze_enrollment_pattern(staggered_patient_histories)
    
    # Analyze protocol behavior
    compare_protocol_behavior(regular_patient_histories, staggered_patient_histories)
    
    # Analyze discontinuation handling
    validate_discontinuation_handling(staggered_results)
    
    # Create comparison plots
    try:
        plot_staggered_comparison(regular_patient_histories, staggered_patient_histories, enrollment_stats)
    except Exception as e:
        logger.error(f"Error creating plots: {str(e)}")
    
    logger.info("Validation complete.")
    return {
        "regular_results": regular_results,
        "staggered_results": staggered_results
    }

def analyze_enrollment_pattern(patient_histories):
    """
    Analyze the enrollment pattern from staggered implementation.
    
    Parameters
    ----------
    patient_histories : Dict
        Patient histories from staggered implementation
    """
    # Extract enrollment dates
    enrollment_dates = []
    
    for patient_id, visits in patient_histories.items():
        if visits:
            # Find first visit date for each patient
            first_visit = min(visits, key=lambda v: v.get('date', datetime.max))
            first_date = first_visit.get('date')
            if first_date:
                enrollment_dates.append(first_date)
    
    if not enrollment_dates:
        logger.warning("No enrollment dates found in patient histories")
        return
    
    # Sort dates
    enrollment_dates.sort()
    
    # Calculate statistics
    min_date = min(enrollment_dates)
    max_date = max(enrollment_dates)
    duration_days = (max_date - min_date).days
    
    logger.info("\nEnrollment Pattern Analysis:")
    logger.info(f"First enrollment: {min_date}")
    logger.info(f"Last enrollment: {max_date}")
    logger.info(f"Enrollment duration: {duration_days} days")
    
    # Analyze distribution by week
    weeks = {}
    for date in enrollment_dates:
        week_num = int((date - min_date).days / 7)
        weeks[week_num] = weeks.get(week_num, 0) + 1
    
    logger.info("\nEnrollment by week:")
    for week, count in sorted(weeks.items()):
        logger.info(f"Week {week}: {count} patients")
    
    # Check if the pattern resembles Poisson distribution
    mean_per_week = np.mean(list(weeks.values()))
    variance_per_week = np.var(list(weeks.values()))
    logger.info(f"\nMean patients per week: {mean_per_week:.2f}")
    logger.info(f"Variance patients per week: {variance_per_week:.2f}")
    logger.info(f"Ratio (variance/mean): {variance_per_week/mean_per_week:.2f}")
    
    # For Poisson distribution, variance/mean should be close to 1
    if 0.7 <= variance_per_week/mean_per_week <= 1.3:
        logger.info("✅ Enrollment pattern resembles Poisson distribution")
    else:
        logger.warning("❌ Enrollment pattern does not resemble Poisson distribution")

def compare_protocol_behavior(regular_histories, staggered_histories):
    """
    Compare protocol behavior between regular and staggered implementations.
    
    Parameters
    ----------
    regular_histories : Dict
        Patient histories from regular implementation
    staggered_histories : Dict
        Patient histories from staggered implementation
    """
    # Analyze phases and transitions
    regular_phases = analyze_phases(regular_histories)
    staggered_phases = analyze_phases(staggered_histories)
    
    logger.info("\nProtocol Behavior Comparison:")
    logger.info("-" * 40)
    logger.info(f"{'Metric':<30} {'Regular':<12} {'Staggered':<12}")
    logger.info("-" * 40)
    
    # Compare loading phase visits
    regular_loading = regular_phases.get("loading", {})
    staggered_loading = staggered_phases.get("loading", {})
    
    reg_avg_loading = regular_loading.get("avg_visits", 0)
    stag_avg_loading = staggered_loading.get("avg_visits", 0)
    
    logger.info(f"{'Average loading phase visits':<30} {reg_avg_loading:<12.2f} {stag_avg_loading:<12.2f}")
    
    # Compare maintenance phase transition
    reg_pct_maintenance = regular_phases.get("maintenance", {}).get("percent_patients", 0)
    stag_pct_maintenance = staggered_phases.get("maintenance", {}).get("percent_patients", 0)
    
    logger.info(f"{'Patients reaching maintenance':<30} {reg_pct_maintenance:<12.1f}% {stag_pct_maintenance:<12.1f}%")
    
    # Compare discontinuation rates
    reg_pct_discontinued = regular_phases.get("discontinued", {}).get("percent_patients", 0)
    stag_pct_discontinued = staggered_phases.get("discontinued", {}).get("percent_patients", 0)
    
    logger.info(f"{'Discontinued patients':<30} {reg_pct_discontinued:<12.1f}% {stag_pct_discontinued:<12.1f}%")
    
    # Compare retreatment rates
    reg_pct_retreated = regular_phases.get("retreated", {}).get("percent_patients", 0)
    stag_pct_retreated = staggered_phases.get("retreated", {}).get("percent_patients", 0)
    
    logger.info(f"{'Retreated patients':<30} {reg_pct_retreated:<12.1f}% {stag_pct_retreated:<12.1f}%")
    
    # Check if the protocol behaviors are similar
    tolerance = 15  # Allow 15% difference
    
    similar_loading = abs(reg_avg_loading - stag_avg_loading) / max(1, reg_avg_loading) * 100 <= tolerance
    similar_maintenance = abs(reg_pct_maintenance - stag_pct_maintenance) <= tolerance
    similar_discontinued = abs(reg_pct_discontinued - stag_pct_discontinued) <= tolerance
    
    if similar_loading and similar_maintenance and similar_discontinued:
        logger.info("\n✅ Protocol behaviors are similar between implementations")
    else:
        logger.warning("\n❌ Protocol behaviors differ significantly between implementations")

def analyze_phases(patient_histories):
    """
    Analyze phases and transitions in patient histories.
    
    Parameters
    ----------
    patient_histories : Dict
        Patient histories to analyze
        
    Returns
    -------
    Dict
        Analysis of phases and transitions
    """
    # Count patients in each phase
    total_patients = len(patient_histories)
    if total_patients == 0:
        return {}
    
    loading_patients = 0
    maintenance_patients = 0
    discontinued_patients = 0
    retreated_patients = 0
    
    # Count visits per phase
    loading_visits = 0
    maintenance_visits = 0
    monitoring_visits = 0
    
    for patient_id, visits in patient_histories.items():
        # Track patient phases
        in_loading = False
        in_maintenance = False
        discontinued = False
        retreated = False
        
        # Count visits by phase
        patient_loading_visits = 0
        patient_maintenance_visits = 0
        patient_monitoring_visits = 0
        
        for visit in visits:
            phase = visit.get('phase', '')
            visit_type = visit.get('type', '')
            treatment_status = visit.get('treatment_status', {})
            
            if phase == 'loading':
                in_loading = True
                patient_loading_visits += 1
            elif phase == 'maintenance':
                in_maintenance = True
                patient_maintenance_visits += 1
            
            if visit_type == 'monitoring_visit':
                patient_monitoring_visits += 1
            
            # Check discontinuation status
            if isinstance(treatment_status, dict) and not treatment_status.get('active', True):
                discontinued = True
            
            # Check retreatment status (discontinued but later active)
            if discontinued and isinstance(treatment_status, dict) and treatment_status.get('active', False):
                retreated = True
        
        # Update patient counts
        if in_loading:
            loading_patients += 1
        if in_maintenance:
            maintenance_patients += 1
        if discontinued:
            discontinued_patients += 1
        if retreated:
            retreated_patients += 1
        
        # Update visit counts
        loading_visits += patient_loading_visits
        maintenance_visits += patient_maintenance_visits
        monitoring_visits += patient_monitoring_visits
    
    # Calculate percentages and averages
    pct_loading = (loading_patients / total_patients) * 100
    pct_maintenance = (maintenance_patients / total_patients) * 100
    pct_discontinued = (discontinued_patients / total_patients) * 100
    pct_retreated = (retreated_patients / total_patients) * 100
    
    avg_loading_visits = loading_visits / max(1, loading_patients)
    avg_maintenance_visits = maintenance_visits / max(1, maintenance_patients)
    avg_monitoring_visits = monitoring_visits / max(1, discontinued_patients)
    
    return {
        "loading": {
            "count": loading_patients,
            "percent_patients": pct_loading,
            "total_visits": loading_visits,
            "avg_visits": avg_loading_visits
        },
        "maintenance": {
            "count": maintenance_patients,
            "percent_patients": pct_maintenance,
            "total_visits": maintenance_visits,
            "avg_visits": avg_maintenance_visits
        },
        "discontinued": {
            "count": discontinued_patients,
            "percent_patients": pct_discontinued,
            "monitoring_visits": monitoring_visits,
            "avg_monitoring_visits": avg_monitoring_visits
        },
        "retreated": {
            "count": retreated_patients,
            "percent_patients": pct_retreated
        }
    }

def validate_discontinuation_handling(staggered_results):
    """
    Validate discontinuation handling in staggered implementation.
    
    Parameters
    ----------
    staggered_results : Dict
        Results from staggered implementation
    """
    # Extract discontinuation statistics
    discontinuation_stats = staggered_results.get("discontinuation_stats", {})
    
    logger.info("\nDiscontinuation Handling Validation:")
    logger.info("-" * 40)
    
    # Check if statistics are present
    if not discontinuation_stats:
        logger.warning("No discontinuation statistics found")
        return
    
    # Extract key metrics
    unique_discontinued = discontinuation_stats.get("unique_discontinued_patients", 0)
    unique_retreated = discontinuation_stats.get("unique_retreated_patients", 0)
    
    logger.info(f"Unique discontinued patients: {unique_discontinued}")
    logger.info(f"Unique retreated patients: {unique_retreated}")
    
    # Check for monitoring visits after discontinuation
    patient_histories = staggered_results.get("patient_histories", {})
    
    monitoring_visits_found = False
    for patient_id, visits in patient_histories.items():
        discontinued = False
        monitoring_after_discontinuation = False
        
        for visit in visits:
            treatment_status = visit.get('treatment_status', {})
            visit_type = visit.get('type', '')
            
            # Check if patient is discontinued
            if isinstance(treatment_status, dict) and not treatment_status.get('active', True):
                discontinued = True
            
            # Check for monitoring visits after discontinuation
            if discontinued and visit_type == 'monitoring_visit':
                monitoring_after_discontinuation = True
        
        if monitoring_after_discontinuation:
            monitoring_visits_found = True
            break
    
    if monitoring_visits_found:
        logger.info("✅ Monitoring visits found after discontinuation")
    else:
        logger.warning("❌ No monitoring visits found after discontinuation")
    
    # Check for retreatment after monitoring
    retreatment_after_monitoring = False
    for patient_id, visits in patient_histories.items():
        discontinued = False
        monitoring = False
        retreated_after_monitoring = False
        
        for visit in visits:
            treatment_status = visit.get('treatment_status', {})
            visit_type = visit.get('type', '')
            
            # Track discontinuation
            if isinstance(treatment_status, dict) and not treatment_status.get('active', True):
                discontinued = True
            
            # Track monitoring visits
            if discontinued and visit_type == 'monitoring_visit':
                monitoring = True
            
            # Track retreatment after monitoring
            if monitoring and isinstance(treatment_status, dict) and treatment_status.get('active', False):
                retreated_after_monitoring = True
        
        if retreated_after_monitoring:
            retreatment_after_monitoring = True
            break
    
    if retreatment_after_monitoring:
        logger.info("✅ Retreatment found after monitoring visits")
    else:
        logger.warning("❌ No retreatment found after monitoring visits")

def plot_staggered_comparison(regular_histories, staggered_histories, enrollment_stats):
    """
    Create comparison plots between regular and staggered implementations.
    
    Parameters
    ----------
    regular_histories : Dict
        Patient histories from regular implementation
    staggered_histories : Dict
        Patient histories from staggered implementation
    enrollment_stats : Dict
        Enrollment statistics from staggered implementation
    """
    # Setup figure
    fig, axs = plt.subplots(2, 2, figsize=(14, 12))
    
    # Plot 1: Patient enrollment over time
    first_enrollment = None
    enrollment_dates = []
    
    for patient_id, visits in staggered_histories.items():
        if visits:
            # Find first visit date for each patient
            first_visit = min(visits, key=lambda v: v.get('date', datetime.max))
            first_date = first_visit.get('date')
            if first_date:
                if first_enrollment is None or first_date < first_enrollment:
                    first_enrollment = first_date
                enrollment_dates.append(first_date)
    
    if enrollment_dates and first_enrollment:
        # Sort dates
        enrollment_dates.sort()
        
        # Count cumulative enrollments
        days = []
        cumulative = []
        count = 0
        
        for date in enrollment_dates:
            day = (date - first_enrollment).days
            count += 1
            days.append(day)
            cumulative.append(count)
        
        axs[0, 0].plot(days, cumulative)
        axs[0, 0].set_xlabel('Days from first enrollment')
        axs[0, 0].set_ylabel('Cumulative patients')
        axs[0, 0].set_title('Staggered Enrollment Pattern')
        
        # Add annotation for enrollment duration
        enrollment_duration = enrollment_stats.get("enrollment_duration_days", 0)
        axs[0, 0].axvline(x=enrollment_duration, color='r', linestyle='--')
        axs[0, 0].text(enrollment_duration + 1, count / 2, f'Enrollment period: {enrollment_duration} days',
                 rotation=90, verticalalignment='center')
    
    # Plot 2: Phase distribution comparison
    regular_phases = analyze_phases(regular_histories)
    staggered_phases = analyze_phases(staggered_histories)
    
    phases = ['loading', 'maintenance', 'discontinued', 'retreated']
    regular_pcts = [regular_phases.get(phase, {}).get("percent_patients", 0) for phase in phases]
    staggered_pcts = [staggered_phases.get(phase, {}).get("percent_patients", 0) for phase in phases]
    
    x = np.arange(len(phases))
    width = 0.35
    
    axs[0, 1].bar(x - width/2, regular_pcts, width, label='Regular')
    axs[0, 1].bar(x + width/2, staggered_pcts, width, label='Staggered')
    axs[0, 1].set_xticks(x)
    axs[0, 1].set_xticklabels(phases)
    axs[0, 1].set_ylabel('Percentage of patients')
    axs[0, 1].set_title('Patient Phase Distribution')
    axs[0, 1].legend()
    
    # Plot 3: Visit distribution over time for staggered implementation
    if staggered_histories:
        # Extract visit dates
        all_visits = []
        for patient_id, visits in staggered_histories.items():
            for visit in visits:
                visit_date = visit.get('date')
                if visit_date:
                    all_visits.append(visit_date)
        
        # Sort visits
        all_visits.sort()
        
        if all_visits and first_enrollment:
            # Group by week
            weeks = {}
            for date in all_visits:
                week_num = int((date - first_enrollment).days / 7)
                weeks[week_num] = weeks.get(week_num, 0) + 1
            
            # Create plot
            week_nums = sorted(weeks.keys())
            visit_counts = [weeks[week] for week in week_nums]
            
            axs[1, 0].bar(week_nums, visit_counts)
            axs[1, 0].set_xlabel('Week from first enrollment')
            axs[1, 0].set_ylabel('Number of visits')
            axs[1, 0].set_title('Visit Distribution Over Time (Staggered)')
    
    # Plot 4: Patient-specific time tracking
    if staggered_histories:
        # Extract time since enrollment
        relative_times = []
        for patient_id, visits in staggered_histories.items():
            for visit in visits:
                relative_time = visit.get('time_since_enrollment')
                if relative_time is not None:
                    relative_times.append(relative_time)
        
        if relative_times:
            # Group by 30-day periods
            months = {}
            for days in relative_times:
                month_num = int(days / 30)
                months[month_num] = months.get(month_num, 0) + 1
            
            # Create plot
            month_nums = sorted(months.keys())
            month_counts = [months[month] for month in month_nums]
            
            axs[1, 1].bar(month_nums, month_counts)
            axs[1, 1].set_xlabel('Months since enrollment (patient-specific time)')
            axs[1, 1].set_ylabel('Number of visits')
            axs[1, 1].set_title('Visit Distribution by Patient-Specific Time')
    
    plt.tight_layout()
    plt.savefig('staggered_implementation_validation.png')
    logger.info("Comparison plots saved to staggered_implementation_validation.png")

if __name__ == "__main__":
    validate_staggered_implementation()