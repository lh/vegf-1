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
    # Check if metadata contains recruitment information
    if 'recruitment_mode' in metadata_df.columns:
        recruitment_mode = metadata_df['recruitment_mode'].iloc[0]
        if recruitment_mode == "Constant Rate" and 'recruitment_rate' in metadata_df.columns:
            # Use the actual recruitment rate from simulation
            recruitment_rate = metadata_df['recruitment_rate'].iloc[0]
            duration_years = metadata_df['duration_years'].iloc[0] if 'duration_years' in metadata_df.columns else 5
            # For constant rate, enrollment extends throughout simulation
            enrollment_months = int(duration_years * 12)
            logger.info(f"Using simulation recruitment rate: {recruitment_rate:.2f} patients/month over {enrollment_months} months")
    
    if start_date is None:
        # Use simulation start date from metadata if available
        if 'start_date' in metadata_df.columns:
            start_date = pd.to_datetime(metadata_df['start_date'].iloc[0])
            logger.info(f"Using simulation start date from metadata: {start_date}")
        else:
            # For constant rate simulations, use the earliest visit date
            if preserve_original_enrollment or (
                'recruitment_mode' in metadata_df.columns and 
                metadata_df['recruitment_mode'].iloc[0] == "Constant Rate"
            ):
                start_date = visits_df['date'].min()
                logger.info(f"Using earliest visit date as start: {start_date}")
            else:
                # Default to a reasonable past date
                start_date = datetime(2020, 1, 1)
                logger.info(f"Using default start date: {start_date}")
    
    # Get unique patients
    patients = visits_df['patient_id'].unique()
    n_patients = len(patients)
    
    # Check if we should use actual enrollment times from the simulation
    preserve_original_enrollment = False
    if 'recruitment_mode' in metadata_df.columns and metadata_df['recruitment_mode'].iloc[0] == "Constant Rate":
        # For constant rate simulations, preserve the original enrollment pattern
        preserve_original_enrollment = True
        logger.info("Preserving original constant-rate enrollment pattern")
    
    # Also check if enrollment_pattern is set to "preserved" from the UI
    if enrollment_pattern == "preserved":
        preserve_original_enrollment = True
        logger.info("UI requested to preserve original enrollment pattern")
    
    if preserve_original_enrollment:
        # Extract actual enrollment dates from first visit of each patient
        patient_first_visits = visits_df.groupby('patient_id')['date'].min().reset_index()
        patient_first_visits.columns = ['patient_id', 'first_visit_date']
        
        # Use actual first visit dates as enrollment dates
        patient_enrollment = dict(zip(
            patient_first_visits['patient_id'],
            patient_first_visits['first_visit_date']
        ))
    else:
        # Generate enrollment dates based on pattern
        enrollment_dates = generate_enrollment_dates(
            n_patients, start_date, enrollment_months, enrollment_pattern
        )
        
        # Create patient enrollment mapping
        patient_enrollment = dict(zip(patients, enrollment_dates))
    
    # Transform visits to calendar time using vectorized operations
    logger.info(f"Transforming {len(visits_df)} visits for {n_patients} patients to calendar time...")
    
    # Create a copy to avoid modifying original
    calendar_visits_df = visits_df.copy()
    
    if preserve_original_enrollment:
        # For constant rate simulations, the dates are already correct
        # Just copy the date column to calendar_date
        calendar_visits_df['calendar_date'] = calendar_visits_df['date']
        calendar_visits_df['enrollment_date'] = calendar_visits_df['patient_id'].map(patient_enrollment)
        
        # Calculate months since enrollment for consistency
        first_visits = calendar_visits_df.groupby('patient_id')['date'].min().reset_index()
        first_visits.columns = ['patient_id', 'first_visit_date']
        calendar_visits_df = calendar_visits_df.merge(first_visits, on='patient_id', how='left')
        calendar_visits_df['months_since_enrollment'] = (
            (calendar_visits_df['date'] - calendar_visits_df['first_visit_date']).dt.days / 30.44
        )
    else:
        # Add enrollment dates for all patients at once
        calendar_visits_df['enrollment_date'] = calendar_visits_df['patient_id'].map(patient_enrollment)
        
        # Get first visit date for each patient (vectorized)
        first_visits = calendar_visits_df.groupby('patient_id')['date'].min().reset_index()
        first_visits.columns = ['patient_id', 'first_visit_date']
        
        # Merge first visit dates back to main dataframe
        calendar_visits_df = calendar_visits_df.merge(first_visits, on='patient_id', how='left')
        
        # Calculate months since enrollment (vectorized)
        calendar_visits_df['months_since_enrollment'] = (
            (calendar_visits_df['date'] - calendar_visits_df['first_visit_date']).dt.days / 30.44
        )
        
        # Convert to calendar dates (vectorized)
        calendar_visits_df['calendar_date'] = (
            calendar_visits_df['enrollment_date'] + 
            pd.to_timedelta(calendar_visits_df['months_since_enrollment'] * 30.44, unit='days')
        )
    
    logger.info("Calendar transformation complete")
    
    # Sort by calendar date
    calendar_visits_df = calendar_visits_df.sort_values('calendar_date')
    
    # Generate clinic metrics - limit to actual data range
    actual_end_date = calendar_visits_df['calendar_date'].max()
    clinic_metrics_df = generate_clinic_metrics(calendar_visits_df, start_date, actual_end_date)
    
    # Log the actual time range
    logger.info(f"Calendar view spans from {start_date.strftime('%Y-%m-%d')} to {actual_end_date.strftime('%Y-%m-%d')}")
    
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
    logger.info("Generating clinic metrics...")
    
    if end_date is None:
        end_date = calendar_visits_df['calendar_date'].max()
    
    # Create a copy and add month column for grouping
    visits_df = calendar_visits_df.copy()
    visits_df['month'] = pd.to_datetime(visits_df['calendar_date']).dt.to_period('M')
    
    # Pre-calculate injection visits (vectorized)
    if 'actions' in visits_df.columns:
        def has_injection(actions):
            try:
                if actions is None:
                    return False
                if hasattr(actions, '__iter__') and not isinstance(actions, str):
                    return any('injection' in str(action).lower() for action in actions)
                return 'injection' in str(actions).lower()
            except:
                return False
        
        visits_df['has_injection'] = visits_df['actions'].apply(has_injection)
    else:
        visits_df['has_injection'] = False
    
    # Identify first visits for each patient (vectorized)
    first_visits = visits_df.groupby('patient_id')['calendar_date'].min().reset_index()
    first_visits.columns = ['patient_id', 'first_visit_date']
    first_visits['first_visit_month'] = pd.to_datetime(first_visits['first_visit_date']).dt.to_period('M')
    
    # Group by month and calculate metrics
    monthly_metrics = visits_df.groupby('month').agg({
        'patient_id': ['count', 'nunique'],
        'has_injection': 'sum',
        'vision': 'mean' if 'vision' in visits_df.columns else lambda x: None,
        'is_retreatment_visit': 'sum' if 'is_retreatment_visit' in visits_df.columns else lambda x: 0
    }).reset_index()
    
    # Flatten column names
    monthly_metrics.columns = ['month', 'total_visits', 'unique_patients', 'injection_visits', 'avg_vision', 'retreatment_visits']
    
    # Calculate monitoring visits
    monthly_metrics['monitoring_visits'] = monthly_metrics['total_visits'] - monthly_metrics['injection_visits']
    
    # Count new patients per month
    new_patients_per_month = first_visits.groupby('first_visit_month').size().reset_index(name='new_patients')
    
    # Merge new patients data
    monthly_metrics = monthly_metrics.merge(
        new_patients_per_month,
        left_on='month',
        right_on='first_visit_month',
        how='left'
    ).fillna({'new_patients': 0})
    
    # Convert period back to timestamp
    monthly_metrics['month'] = monthly_metrics['month'].dt.to_timestamp()
    
    # Drop the extra column
    if 'first_visit_month' in monthly_metrics.columns:
        monthly_metrics = monthly_metrics.drop('first_visit_month', axis=1)
    
    # Add phase-specific counts if phase column exists
    if 'phase' in visits_df.columns:
        phase_counts = visits_df.pivot_table(
            index='month',
            columns='phase',
            values='patient_id',
            aggfunc='count',
            fill_value=0
        ).add_prefix('phase_').add_suffix('_visits')
        
        # Convert index to column and merge
        phase_counts = phase_counts.reset_index()
        phase_counts['month'] = phase_counts['month'].dt.to_timestamp()
        monthly_metrics = monthly_metrics.merge(phase_counts, on='month', how='left')
    
    logger.info(f"Generated metrics for {len(monthly_metrics)} months")
    
    return monthly_metrics


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
    logger.info("Aggregating patient outcomes by enrollment cohort...")
    
    # Create a copy and add enrollment cohorts
    visits_df = calendar_visits_df.copy()
    visits_df['enrollment_cohort'] = pd.to_datetime(
        visits_df['enrollment_date']
    ).dt.to_period(f'{cohort_months}M')
    
    # Pre-calculate injection status for all visits
    if 'actions' in visits_df.columns:
        def has_injection(actions):
            try:
                if actions is None:
                    return False
                if hasattr(actions, '__iter__') and not isinstance(actions, str):
                    return any('injection' in str(action).lower() for action in actions)
                return 'injection' in str(actions).lower()
            except:
                return False
        visits_df['has_injection'] = visits_df['actions'].apply(has_injection)
    else:
        visits_df['has_injection'] = False
    
    # Get first and last visits per patient (vectorized)
    patient_first_last = visits_df.groupby('patient_id').agg({
        'baseline_vision': 'first',
        'vision': 'last',
        'enrollment_cohort': 'first',
        'months_since_enrollment': 'max',
        'calendar_date': ['count'],
        'has_injection': 'sum'
    }).reset_index()
    
    # Flatten column names
    patient_first_last.columns = ['patient_id', 'baseline_vision', 'final_vision', 
                                   'enrollment_cohort', 'months_followed', 
                                   'total_visits', 'total_injections']
    
    # Get discontinuation status per patient
    if 'has_been_discontinued' in visits_df.columns:
        # Get the last discontinuation status per patient
        patient_disc = visits_df.groupby('patient_id')['has_been_discontinued'].last().reset_index()
        patient_disc.columns = ['patient_id', 'discontinued']
    elif 'is_discontinuation' in visits_df.columns:
        # Check if any visit was a discontinuation
        patient_disc = visits_df.groupby('patient_id')['is_discontinuation'].any().reset_index()
        patient_disc.columns = ['patient_id', 'discontinued']
    else:
        # No discontinuation data
        patient_first_last['discontinued'] = False
        patient_disc = None
    
    # Merge discontinuation data if it exists
    if patient_disc is not None:
        patient_outcomes = patient_first_last.merge(patient_disc, on='patient_id', how='left')
    else:
        patient_outcomes = patient_first_last
    
    # Aggregate by cohort
    cohort_summary = patient_outcomes.groupby('enrollment_cohort').agg({
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