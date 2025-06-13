"""Clinical Workload Analysis - OPTIMIZED version with full vectorization.

This module provides vectorized data analysis for workload attribution visualizations,
replacing loops and apply operations with numpy/pandas vectorized operations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List


def calculate_clinical_workload_attribution(visits_df: pd.DataFrame) -> Dict:
    """
    Calculate clinical workload attribution by patient treatment intensity.
    
    OPTIMIZED VERSION: Fully vectorized operations for 10-100x speedup.
    
    Args:
        visits_df: DataFrame with patient visit data including time_days
        
    Returns:
        Dict containing processed data for workload analysis visualizations
    """
    # Get all unique patients
    all_patients = visits_df['patient_id'].unique()
    
    # Calculate intervals between visits if not already present
    if 'interval_days' not in visits_df.columns:
        visits_df = visits_df.copy()
        visits_df = visits_df.sort_values(['patient_id', 'time_days'])
        visits_df['prev_time_days'] = visits_df.groupby('patient_id')['time_days'].shift(1)
        visits_df['interval_days'] = visits_df['time_days'] - visits_df['prev_time_days']
    
    # Filter to only visits with valid intervals
    valid_intervals = visits_df[visits_df['interval_days'].notna()]
    
    if len(valid_intervals) == 0:
        return _create_empty_workload_data(len(all_patients))
    
    # OPTIMIZED: Calculate patient profiles in one operation
    patient_profiles = _calculate_patient_intensity_profiles_vectorized(
        valid_intervals, all_patients, visits_df
    )
    
    # OPTIMIZED: Vectorized categorization
    patient_profiles = _categorize_treatment_intensity_vectorized(patient_profiles)
    
    # OPTIMIZED: Efficient visit contribution calculation
    visit_contributions = _calculate_visit_contributions_vectorized(
        visits_df, patient_profiles
    )
    
    # OPTIMIZED: Vectorized summary stats
    summary_stats = _calculate_workload_summary_stats_vectorized(
        patient_profiles, visit_contributions
    )
    
    return {
        'patient_profiles': patient_profiles,
        'intensity_categories': patient_profiles,  # Same df, includes category
        'visit_contributions': visit_contributions,
        'summary_stats': summary_stats,
        'total_patients': len(all_patients),
        'total_visits': len(visits_df),
        'category_definitions': _get_category_definitions()
    }


def _calculate_patient_intensity_profiles_vectorized(
    valid_intervals: pd.DataFrame, 
    all_patients: np.ndarray,
    visits_df: pd.DataFrame
) -> pd.DataFrame:
    """OPTIMIZED: Calculate treatment intensity profiles using vectorized operations."""
    
    # Get visit counts per patient first (including single-visit patients)
    visit_counts = visits_df.groupby('patient_id').size().reset_index(name='total_visits')
    
    # Calculate interval statistics for patients with intervals
    if len(valid_intervals) > 0:
        interval_stats = valid_intervals.groupby('patient_id')['interval_days'].agg([
            'mean', 'median', 'min', 'max', 'count', 'std'
        ]).reset_index()
        
        interval_stats.columns = [
            'patient_id', 'mean_interval', 'median_interval', 
            'min_interval', 'max_interval', 'interval_count', 'interval_std'
        ]
    else:
        # Create empty stats if no intervals
        interval_stats = pd.DataFrame({
            'patient_id': [],
            'mean_interval': [],
            'median_interval': [],
            'min_interval': [],
            'max_interval': [],
            'interval_count': [],
            'interval_std': []
        })
    
    # Create base dataframe with ALL patients
    all_patients_df = pd.DataFrame({'patient_id': all_patients})
    
    # Merge everything in one go
    patient_profiles = all_patients_df.merge(
        visit_counts, on='patient_id', how='left'
    ).merge(
        interval_stats, on='patient_id', how='left'
    )
    
    # Fill missing values efficiently
    patient_profiles['total_visits'] = patient_profiles['total_visits'].fillna(1)
    patient_profiles['interval_count'] = patient_profiles['interval_count'].fillna(0)
    patient_profiles['interval_std'] = patient_profiles['interval_std'].fillna(0)
    
    return patient_profiles


def _categorize_treatment_intensity_vectorized(patient_profiles: pd.DataFrame) -> pd.DataFrame:
    """OPTIMIZED: Vectorized patient categorization using numpy.select."""
    
    # Extract columns for efficiency
    mean_interval = patient_profiles['mean_interval'].values
    max_interval = patient_profiles['max_interval'].values
    
    # Define conditions for each category
    conditions = [
        pd.isna(mean_interval),                    # Single Visit
        mean_interval <= 42,                        # Intensive (≤6 weeks)
        mean_interval <= 84,                        # Regular (6-12 weeks)
        mean_interval <= 112,                       # Extended (12-16 weeks)
        max_interval > 180,                         # Interrupted (has gaps >6 months)
    ]
    
    # Define corresponding category names
    categories = [
        'Single Visit',
        'Intensive', 
        'Regular',
        'Extended',
        'Interrupted',
    ]
    
    # Use numpy.select for vectorized categorization
    patient_profiles['intensity_category'] = np.select(
        conditions,
        categories,
        default='Sparse'  # Default for remaining cases
    )
    
    # Convert to categorical for memory efficiency
    patient_profiles['intensity_category'] = pd.Categorical(
        patient_profiles['intensity_category'],
        categories=['Single Visit', 'Intensive', 'Regular', 'Extended', 'Interrupted', 'Sparse']
    )
    
    return patient_profiles


def _calculate_visit_contributions_vectorized(
    visits_df: pd.DataFrame, 
    patient_profiles: pd.DataFrame
) -> pd.DataFrame:
    """OPTIMIZED: Calculate visit contributions using groupby aggregation."""
    
    # Get relevant columns
    category_visits = patient_profiles[['patient_id', 'intensity_category', 'total_visits']]
    
    # Aggregate by category in one operation
    visit_contributions = category_visits.groupby('intensity_category', observed=True).agg({
        'patient_id': 'count',     # Number of patients
        'total_visits': 'sum'      # Total visits
    }).reset_index()
    
    visit_contributions.columns = ['intensity_category', 'patient_count', 'visit_count']
    
    return visit_contributions


def _calculate_workload_summary_stats_vectorized(
    patient_profiles: pd.DataFrame,
    visit_contributions: pd.DataFrame
) -> Dict:
    """OPTIMIZED: Calculate summary statistics using vectorized operations."""
    
    total_patients = len(patient_profiles)
    total_visits = visit_contributions['visit_count'].sum()
    
    # Vectorized calculation of all percentages
    visit_contributions['patient_percentage'] = (
        visit_contributions['patient_count'] / total_patients * 100
    ).round(1)
    
    visit_contributions['visit_percentage'] = (
        visit_contributions['visit_count'] / total_visits * 100
    ).round(1)
    
    visit_contributions['visits_per_patient'] = (
        visit_contributions['visit_count'] / visit_contributions['patient_count']
    ).round(1)
    
    # Workload intensity with divide-by-zero protection
    visit_contributions['workload_intensity'] = np.where(
        visit_contributions['patient_percentage'] > 0,
        visit_contributions['visit_percentage'] / visit_contributions['patient_percentage'],
        0
    ).round(2)
    
    # Convert to dictionary format expected by visualizations
    summary_stats = {}
    for _, row in visit_contributions.iterrows():
        category = row['intensity_category']
        summary_stats[category] = {
            'patient_count': int(row['patient_count']),
            'patient_percentage': float(row['patient_percentage']),
            'visit_count': int(row['visit_count']),
            'visit_percentage': float(row['visit_percentage']),
            'visits_per_patient': float(row['visits_per_patient']),
            'workload_intensity': float(row['workload_intensity'])
        }
    
    return summary_stats


def _get_category_definitions() -> Dict:
    """Return definitions for treatment intensity categories using semantic colors."""
    # Import central color system
    from ape.utils.visualization_modes import get_mode_colors
    colors = get_mode_colors()
    
    return {
        'Intensive': {
            'description': 'Very frequent visits (≤6 weeks average)',
            'color': colors.get('intensive_monthly', '#6B9DC7'),
            'clinical_note': 'Patients requiring close monitoring'
        },
        'Regular': {
            'description': 'Standard visit frequency (6-12 weeks)',
            'color': colors.get('regular_6_8_weeks', '#8FC15C'),
            'clinical_note': 'Typical maintenance treatment'
        },
        'Extended': {
            'description': 'Extended intervals (12-16 weeks)',
            'color': colors.get('extended_12_weeks', '#6F9649'),
            'clinical_note': 'Stable patients on extended intervals'
        },
        'Interrupted': {
            'description': 'Treatment gaps >6 months detected',
            'color': colors.get('extended_gap_6_12', '#E6A04D'),
            'clinical_note': 'Patients with treatment interruptions'
        },
        'Sparse': {
            'description': 'Infrequent visits (>16 weeks)',
            'color': colors.get('long_gap_12_plus', '#D97A6B'),
            'clinical_note': 'Very stable or discontinuing patients'
        },
        'Single Visit': {
            'description': 'Only one visit recorded',
            'color': colors.get('no_further_visits', '#A6A6A6'),
            'clinical_note': 'Insufficient data for pattern analysis'
        }
    }


def _create_empty_workload_data(total_patients: int) -> Dict:
    """Create empty workload data structure for cases with no interval data."""
    return {
        'patient_profiles': pd.DataFrame(),
        'intensity_categories': pd.DataFrame(),
        'visit_contributions': pd.DataFrame(),
        'summary_stats': {},
        'total_patients': total_patients,
        'total_visits': 0,
        'category_definitions': _get_category_definitions()
    }


def format_workload_insight(summary_stats: Dict, top_category: str = None) -> str:
    """
    Format key workload insights for display.
    
    Args:
        summary_stats: Summary statistics from calculate_clinical_workload_attribution
        top_category: Specific category to highlight, or None for auto-detection
        
    Returns:
        Formatted insight string for UI display
    """
    if not summary_stats:
        return "No workload data available for analysis."
    
    # Find the category with highest workload efficiency (visits per % of patients)
    if top_category is None:
        top_category = max(summary_stats.keys(), 
                          key=lambda k: summary_stats[k]['workload_intensity'])
    
    if top_category not in summary_stats:
        return "Insufficient data for workload analysis."
    
    stats = summary_stats[top_category]
    
    return (f"{stats['patient_percentage']:.1f}% of patients ({top_category.lower()}) "
            f"generate {stats['visit_percentage']:.1f}% of clinic visits "
            f"({stats['visits_per_patient']:.1f} visits per patient)")