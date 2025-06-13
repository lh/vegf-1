"""Clinical Workload Analysis - Core data processing for workload attribution visualizations.

This module provides the shared data analysis core for multiple visualization approaches
showing how patient treatment intensity affects clinical workload distribution.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List


def calculate_clinical_workload_attribution(visits_df: pd.DataFrame) -> Dict:
    """
    Calculate clinical workload attribution by patient treatment intensity.
    
    This is the shared data core that feeds all three visualization approaches:
    - Dual bar chart (patient count vs visit volume)
    - Impact pyramid (visual flow representation) 
    - Bubble chart (detailed relationship analysis)
    
    Args:
        visits_df: DataFrame with patient visit data including time_days
        
    Returns:
        Dict containing processed data for workload analysis visualizations
    """
    # Get all unique patients
    all_patients = visits_df['patient_id'].unique()
    
    # Calculate intervals between visits if not already present
    if 'interval_days' not in visits_df.columns:
        visits_df = visits_df.copy()  # Don't modify original
        visits_df = visits_df.sort_values(['patient_id', 'time_days'])
        visits_df['prev_time_days'] = visits_df.groupby('patient_id')['time_days'].shift(1)
        visits_df['interval_days'] = visits_df['time_days'] - visits_df['prev_time_days']
    
    # Filter to only visits with valid intervals (exclude first visits)
    valid_intervals = visits_df[visits_df['interval_days'].notna()]
    
    if len(valid_intervals) == 0:
        # Handle case with no interval data
        return _create_empty_workload_data(len(all_patients))
    
    # Calculate patient treatment intensity profiles
    patient_profiles = _calculate_patient_intensity_profiles(valid_intervals, all_patients)
    
    # Categorize patients by treatment intensity
    intensity_categories = _categorize_treatment_intensity(patient_profiles)
    
    # Calculate visit volume contributions by category
    visit_contributions = _calculate_visit_contributions(visits_df, intensity_categories)
    
    # Generate summary statistics
    summary_stats = _calculate_workload_summary_stats(intensity_categories, visit_contributions)
    
    return {
        'patient_profiles': patient_profiles,
        'intensity_categories': intensity_categories,
        'visit_contributions': visit_contributions,
        'summary_stats': summary_stats,
        'total_patients': len(all_patients),
        'total_visits': len(visits_df),
        'category_definitions': _get_category_definitions()
    }


def _calculate_patient_intensity_profiles(valid_intervals: pd.DataFrame, all_patients: List) -> pd.DataFrame:
    """Calculate treatment intensity profiles for each patient."""
    
    # Calculate per-patient statistics
    patient_stats = valid_intervals.groupby('patient_id')['interval_days'].agg([
        'mean',      # Average interval between visits
        'median',    # Median interval
        'min',       # Shortest interval (most intensive period)
        'max',       # Longest interval (including any gaps)
        'count',     # Number of intervals (visits - 1)
        'std'        # Variability in treatment pattern
    ]).reset_index()
    
    patient_stats.columns = ['patient_id', 'mean_interval', 'median_interval', 
                           'min_interval', 'max_interval', 'interval_count', 'interval_std']
    
    # Add patients with only one visit (no intervals)
    patients_with_intervals = set(patient_stats['patient_id'])
    patients_without_intervals = set(all_patients) - patients_with_intervals
    
    if len(patients_without_intervals) > 0:
        single_visit_df = pd.DataFrame({
            'patient_id': list(patients_without_intervals),
            'mean_interval': np.nan,  # No intervals for single visits
            'median_interval': np.nan,
            'min_interval': np.nan,
            'max_interval': np.nan,
            'interval_count': 0,
            'interval_std': np.nan
        })
        patient_stats = pd.concat([patient_stats, single_visit_df], ignore_index=True)
    
    # Fill NaN std values with 0 for single-interval patients
    patient_stats['interval_std'] = patient_stats['interval_std'].fillna(0)
    
    return patient_stats


def _categorize_treatment_intensity(patient_profiles: pd.DataFrame) -> pd.DataFrame:
    """Categorize patients by treatment intensity using improved clinical categories."""
    
    def categorize_patient(row):
        """Categorize individual patient based on their treatment pattern."""
        if pd.isna(row['mean_interval']):
            return 'Single Visit'
        
        mean_interval = row['mean_interval']
        max_interval = row['max_interval']
        
        # Define categories based on mean interval with gap detection
        if mean_interval <= 42:  # ≤6 weeks average
            return 'Intensive'
        elif mean_interval <= 84:  # 6-12 weeks average  
            return 'Regular'
        elif mean_interval <= 112:  # 12-16 weeks average
            return 'Extended'
        elif max_interval > 180:  # Has gaps >6 months
            return 'Interrupted'
        else:
            return 'Sparse'
    
    # Apply categorization
    patient_profiles['intensity_category'] = patient_profiles.apply(categorize_patient, axis=1)
    
    return patient_profiles


def _calculate_visit_contributions(visits_df: pd.DataFrame, intensity_categories: pd.DataFrame) -> pd.DataFrame:
    """Calculate total visit contributions by intensity category."""
    
    # Count total visits per patient
    patient_visit_counts = visits_df.groupby('patient_id').size().reset_index(name='total_visits')
    
    # Merge with intensity categories
    visit_contributions = intensity_categories[['patient_id', 'intensity_category']].merge(
        patient_visit_counts, on='patient_id', how='left'
    )
    
    # Handle patients with no visits (shouldn't happen, but defensive)
    visit_contributions['total_visits'] = visit_contributions['total_visits'].fillna(0)
    
    # Aggregate by category
    category_contributions = visit_contributions.groupby('intensity_category').agg({
        'patient_id': 'count',  # Number of patients in category
        'total_visits': 'sum'   # Total visits from this category
    }).reset_index()
    
    category_contributions.columns = ['intensity_category', 'patient_count', 'visit_count']
    
    return category_contributions


def _calculate_workload_summary_stats(intensity_categories: pd.DataFrame, 
                                    visit_contributions: pd.DataFrame) -> Dict:
    """Calculate key summary statistics for workload attribution."""
    
    total_patients = len(intensity_categories)
    total_visits = visit_contributions['visit_count'].sum()
    
    # Calculate percentages for each category
    summary_stats = {}
    
    for _, row in visit_contributions.iterrows():
        category = row['intensity_category']
        patient_pct = (row['patient_count'] / total_patients * 100) if total_patients > 0 else 0
        visit_pct = (row['visit_count'] / total_visits * 100) if total_visits > 0 else 0
        
        summary_stats[category] = {
            'patient_count': row['patient_count'],
            'patient_percentage': patient_pct,
            'visit_count': row['visit_count'],
            'visit_percentage': visit_pct,
            'visits_per_patient': row['visit_count'] / row['patient_count'] if row['patient_count'] > 0 else 0,
            'workload_intensity': visit_pct / patient_pct if patient_pct > 0 else 0  # Visits per % of patients - higher = more intensive
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
            'color': colors.get('intensive_monthly', '#6B9DC7'),  # Semantic color for intensive treatment
            'clinical_note': 'Patients requiring close monitoring'
        },
        'Regular': {
            'description': 'Standard visit frequency (6-12 weeks)',
            'color': colors.get('regular_6_8_weeks', '#8FC15C'),  # Semantic color for regular treatment
            'clinical_note': 'Typical maintenance treatment'
        },
        'Extended': {
            'description': 'Extended intervals (12-16 weeks)',
            'color': colors.get('extended_12_weeks', '#6F9649'),  # Semantic color for extended treatment
            'clinical_note': 'Stable patients on extended intervals'
        },
        'Interrupted': {
            'description': 'Treatment gaps >6 months detected',
            'color': colors.get('extended_gap_6_12', '#E6A04D'),  # Semantic color for gaps
            'clinical_note': 'Patients with treatment interruptions'
        },
        'Sparse': {
            'description': 'Infrequent visits (>16 weeks)',
            'color': colors.get('long_gap_12_plus', '#D97A6B'),  # Semantic color for long gaps
            'clinical_note': 'Very stable or discontinuing patients'
        },
        'Single Visit': {
            'description': 'Only one visit recorded',
            'color': colors.get('no_further_visits', '#A6A6A6'),  # Semantic color for discontinued
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