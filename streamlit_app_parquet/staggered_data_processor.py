"""
Staggered Data Processor - Transform patient-relative time data to calendar time view.

This module processes existing Parquet simulation data to create a calendar-time
perspective for clinic activity analysis and visualization.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def transform_to_calendar_view(
    visits_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    enrollment_pattern: str = "uniform",
    enrollment_months: int = 12,
    start_date: Optional[datetime] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transform patient-relative time data to calendar time view.
    
    Args:
        visits_df: Visits DataFrame with patient-relative times
        metadata_df: Metadata DataFrame with patient information
        enrollment_pattern: Pattern for patient enrollment ("uniform", "front_loaded", "gradual")
        enrollment_months: Number of months over which to spread enrollment
        start_date: Start date for the simulation (defaults to today - 5 years)
    
    Returns:
        Tuple of (calendar_visits_df, clinic_metrics_df)
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=5*365)
    
    # Get unique patients
    patients = visits_df['patient_id'].unique()
    n_patients = len(patients)
    
    # Generate enrollment dates based on pattern
    enrollment_dates = generate_enrollment_dates(
        n_patients, start_date, enrollment_months, enrollment_pattern
    )
    
    # Create patient enrollment mapping
    patient_enrollment = dict(zip(patients, enrollment_dates))
    
    # Transform visits to calendar time
    calendar_visits = []
    
    for patient_id in patients:
        patient_visits = visits_df[visits_df['patient_id'] == patient_id].copy()
        enrollment_date = patient_enrollment[patient_id]
        
        # Convert relative months to actual dates
        patient_visits['calendar_date'] = patient_visits['time'].apply(
            lambda months: enrollment_date + timedelta(days=int(months * 30.44))
        )
        
        # Add enrollment info
        patient_visits['enrollment_date'] = enrollment_date
        patient_visits['months_since_enrollment'] = patient_visits['time']
        
        calendar_visits.append(patient_visits)
    
    # Combine all visits
    calendar_visits_df = pd.concat(calendar_visits, ignore_index=True)
    
    # Sort by calendar date
    calendar_visits_df = calendar_visits_df.sort_values('calendar_date')
    
    # Generate clinic metrics
    clinic_metrics_df = generate_clinic_metrics(calendar_visits_df, start_date)
    
    return calendar_visits_df, clinic_metrics_df


def generate_enrollment_dates(
    n_patients: int,
    start_date: datetime,
    enrollment_months: int,
    pattern: str = "uniform"
) -> List[datetime]:
    """
    Generate enrollment dates for patients based on specified pattern.
    
    Args:
        n_patients: Number of patients to enroll
        start_date: First enrollment date
        enrollment_months: Period over which to enroll patients
        pattern: Enrollment pattern type
    
    Returns:
        List of enrollment dates
    """
    enrollment_days = enrollment_months * 30
    
    if pattern == "uniform":
        # Evenly distributed enrollment
        intervals = np.linspace(0, enrollment_days, n_patients)
        
    elif pattern == "front_loaded":
        # More patients early, fewer later (exponential decay)
        x = np.linspace(0, 5, n_patients)
        y = np.exp(-x)
        intervals = (y - y.min()) / (y.max() - y.min()) * enrollment_days
        
    elif pattern == "gradual":
        # Slow start, peak in middle, taper off (bell curve)
        x = np.linspace(-3, 3, n_patients)
        y = np.exp(-0.5 * x**2)
        cumulative = np.cumsum(y)
        intervals = (cumulative - cumulative.min()) / (cumulative.max() - cumulative.min()) * enrollment_days
        
    else:
        raise ValueError(f"Unknown enrollment pattern: {pattern}")
    
    # Convert intervals to dates
    enrollment_dates = [
        start_date + timedelta(days=int(interval))
        for interval in intervals
    ]
    
    return enrollment_dates


def generate_clinic_metrics(
    calendar_visits_df: pd.DataFrame,
    start_date: datetime,
    end_date: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Generate monthly clinic activity metrics from calendar visits.
    
    Args:
        calendar_visits_df: DataFrame with calendar-time visits
        start_date: Start date for metrics
        end_date: End date for metrics (defaults to last visit date)
    
    Returns:
        DataFrame with monthly clinic metrics
    """
    if end_date is None:
        end_date = calendar_visits_df['calendar_date'].max()
    
    # Create monthly bins
    date_range = pd.date_range(start=start_date, end=end_date, freq='M')
    
    metrics = []
    
    for i in range(len(date_range) - 1):
        month_start = date_range[i]
        month_end = date_range[i + 1]
        
        # Filter visits for this month
        month_visits = calendar_visits_df[
            (calendar_visits_df['calendar_date'] >= month_start) &
            (calendar_visits_df['calendar_date'] < month_end)
        ]
        
        # Calculate metrics
        metric = {
            'month': month_start,
            'total_visits': len(month_visits),
            'unique_patients': month_visits['patient_id'].nunique(),
            'injection_visits': len(month_visits[month_visits['received_injection'] == True]),
            'monitoring_visits': len(month_visits[month_visits['received_injection'] == False]),
            'new_patients': len(month_visits[month_visits['visit_number'] == 1]),
            'avg_vision': month_visits['vision'].mean() if 'vision' in month_visits.columns else None,
            'retreatment_visits': len(month_visits[month_visits.get('is_retreatment_visit', False) == True]),
        }
        
        # Add phase-specific counts
        if 'phase' in month_visits.columns:
            phase_counts = month_visits['phase'].value_counts().to_dict()
            metric.update({
                f'phase_{phase}_visits': count
                for phase, count in phase_counts.items()
            })
        
        metrics.append(metric)
    
    return pd.DataFrame(metrics)


def calculate_resource_requirements(
    clinic_metrics_df: pd.DataFrame,
    visits_per_clinician_per_day: int = 20,
    injection_time_minutes: int = 30,
    monitoring_time_minutes: int = 15
) -> pd.DataFrame:
    """
    Calculate resource requirements based on clinic metrics.
    
    Args:
        clinic_metrics_df: DataFrame with monthly clinic metrics
        visits_per_clinician_per_day: Capacity per clinician
        injection_time_minutes: Time for injection visit
        monitoring_time_minutes: Time for monitoring visit
    
    Returns:
        DataFrame with resource calculations
    """
    resources = clinic_metrics_df.copy()
    
    # Assuming 20 working days per month
    working_days_per_month = 20
    
    # Calculate total visit time in hours
    resources['total_hours'] = (
        (resources['injection_visits'] * injection_time_minutes +
         resources['monitoring_visits'] * monitoring_time_minutes) / 60
    )
    
    # Calculate required clinician days
    resources['clinician_days_needed'] = (
        resources['total_visits'] / visits_per_clinician_per_day
    )
    
    # Calculate required FTE clinicians
    resources['fte_clinicians_needed'] = (
        resources['clinician_days_needed'] / working_days_per_month
    )
    
    # Calculate capacity utilization if we have a fixed number of clinicians
    # This would be compared against actual clinic capacity
    
    return resources


def aggregate_patient_outcomes_by_enrollment_cohort(
    calendar_visits_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    cohort_months: int = 3
) -> pd.DataFrame:
    """
    Aggregate patient outcomes by enrollment cohort.
    
    Args:
        calendar_visits_df: DataFrame with calendar-time visits
        metadata_df: Patient metadata
        cohort_months: Number of months to group into cohorts
    
    Returns:
        DataFrame with cohort-based outcomes
    """
    # Create enrollment cohorts
    calendar_visits_df['enrollment_cohort'] = pd.to_datetime(
        calendar_visits_df['enrollment_date']
    ).dt.to_period(f'{cohort_months}M')
    
    # Get final outcomes per patient
    patient_outcomes = []
    
    for patient_id in calendar_visits_df['patient_id'].unique():
        patient_data = calendar_visits_df[calendar_visits_df['patient_id'] == patient_id]
        patient_meta = metadata_df[metadata_df['patient_id'] == patient_id].iloc[0]
        
        outcome = {
            'patient_id': patient_id,
            'enrollment_cohort': patient_data['enrollment_cohort'].iloc[0],
            'baseline_vision': patient_meta.get('baseline_vision', None),
            'final_vision': patient_data['vision'].iloc[-1] if 'vision' in patient_data.columns else None,
            'total_visits': len(patient_data),
            'total_injections': patient_data['received_injection'].sum(),
            'discontinued': patient_meta.get('discontinued', False),
            'months_followed': patient_data['months_since_enrollment'].max()
        }
        
        patient_outcomes.append(outcome)
    
    outcomes_df = pd.DataFrame(patient_outcomes)
    
    # Aggregate by cohort
    cohort_summary = outcomes_df.groupby('enrollment_cohort').agg({
        'patient_id': 'count',
        'baseline_vision': 'mean',
        'final_vision': 'mean',
        'total_visits': 'mean',
        'total_injections': 'mean',
        'discontinued': 'mean',
        'months_followed': 'mean'
    }).rename(columns={'patient_id': 'n_patients', 'discontinued': 'discontinuation_rate'})
    
    # Calculate vision change
    cohort_summary['mean_vision_change'] = (
        cohort_summary['final_vision'] - cohort_summary['baseline_vision']
    )
    
    return cohort_summary