"""
Eylea Treatment Data Analysis

This script analyzes real-world data from intravitreal Eylea injections
to derive parameters for simulation models.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import seaborn as sns
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple, Set, Any, Union

# Set up logging with DEBUG statements
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EyleaDataAnalyzer:
    """Analyzer for Eylea treatment data to derive simulation parameters."""
    
    # Define expected column names and their possible alternatives
    COLUMN_MAPPINGS = {
        'UUID': ['UUID', 'Patient ID', 'PatientID', 'Patient_ID', 'ID'],
        'Injection Date': ['Injection Date', 'InjectionDate', 'Date of Injection', 'Treatment Date'],
        'VA Letter Score at Injection': ['VA Letter Score at Injection', 'VA Score', 'ETDRS Score', 
                                         'Visual Acuity', 'VA_Score', 'Letter Score'],
        'Baseline VA Letter Score': ['Baseline VA Letter Score', 'Baseline VA', 'BaselineVA', 
                                    'Initial VA', 'Starting VA'],
        'Baseline CRT': ['Baseline CRT', 'BaselineCRT', 'Initial CRT', 'Starting CRT'],
        'Date of 1st Injection': ['Date of 1st Injection', 'First Injection Date', 
                                  'Initial Treatment Date', 'First Treatment Date'],
        'Current Age': ['Current Age', 'Age', 'Patient Age'],
        'Gender': ['Gender', 'Sex'],
        'Eye': ['Eye', 'Treated Eye'],
        'Deceased': ['Deceased', 'Death', 'Mortality'],
        'CRT at Injection': ['CRT at Injection', 'CRT', 'Central Retinal Thickness'],
        'Days Since Last Injection': ['Days Since Last Injection', 'Interval', 'Treatment Interval', 
                                      'Days_Since_Last', 'Injection Interval']
    }
    
    # Define expected data types and validation ranges
    DATA_VALIDATION = {
        'UUID': {'type': str, 'required': True},
        'Injection Date': {'type': 'datetime', 'required': True},
        'VA Letter Score at Injection': {'type': float, 'min': 0, 'max': 100, 'required': True},
        'Baseline VA Letter Score': {'type': float, 'min': 0, 'max': 100, 'required': False},
        'Baseline CRT': {'type': float, 'min': 0, 'max': 1000, 'required': False},
        'Date of 1st Injection': {'type': 'datetime', 'required': False},
        'Current Age': {'type': float, 'min': 0, 'max': 120, 'required': False},
        'Days Since Last Injection': {'type': float, 'min': 0, 'max': 365, 'required': False},
        'CRT at Injection': {'type': float, 'min': 0, 'max': 1000, 'required': False}
    }
    
    def __init__(self, data_path, output_dir=None):
        """
        Initialize the analyzer with data path.
        
        Args:
            data_path: Path to the CSV data file
            output_dir: Directory to save outputs (default: creates 'output' dir)
        """
        self.data_path = data_path
        self.output_dir = output_dir or Path('output')
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.data = None
        self.patient_data = None
        self.injection_intervals = None
        self.va_trajectories = None
        
        # Debug flag to control verbose output - set to False to reduce output
        self.debug = False
        
        # Track column mapping used
        self.column_mapping_used = {}
        
        # Data quality report
        self.data_quality_report = {
            'validation_errors': [],
            'validation_warnings': [],
            'missing_values': {},
            'outliers': {},
            'temporal_anomalies': {},
            'column_mapping': {}
        }
    
    def load_data(self):
        """
        Load and perform initial cleaning of the data with enhanced validation.
        
        Returns:
            DataFrame: The loaded and validated data
            
        Raises:
            ValueError: If critical data validation fails
        """
        logger.info(f"Loading data from {self.data_path}")
        
        # Load the CSV file
        try:
            self.data = pd.read_csv(self.data_path)
            logger.info(f"Loaded {len(self.data)} rows with {len(self.data.columns)} columns")
        except Exception as e:
            logger.error(f"Failed to load data: {str(e)}")
            raise
        
        # Map column names to standardized names
        self.map_column_names()
        
        # Validate data structure
        self.validate_data_structure()
        
        # Clean and preprocess data
        self.clean_data()
        
        # Generate data quality report
        self.generate_data_quality_report()
        
        return self.data
    
    def map_column_names(self):
        """
        Map various possible column names to standardized names.
        Uses fuzzy matching for minor variations in column names.
        """
        logger.info("Mapping column names to standardized format")
        
        # Track original column names
        original_columns = set(self.data.columns)
        mapped_columns = set()
        
        # Create a new DataFrame with standardized column names
        new_data = pd.DataFrame()
        
        # For each standard column, check if any of its variations exist
        for std_col, alternatives in self.COLUMN_MAPPINGS.items():
            found = False
            
            # First try exact matches
            for alt in alternatives:
                if alt in self.data.columns:
                    new_data[std_col] = self.data[alt]
                    self.column_mapping_used[std_col] = alt
                    mapped_columns.add(alt)
                    found = True
                    logger.debug(f"Mapped column '{alt}' to '{std_col}'")
                    break
            
            # If no exact match, try fuzzy matching
            if not found:
                for col in self.data.columns:
                    # Skip already mapped columns
                    if col in mapped_columns:
                        continue
                    
                    # Check for fuzzy matches (case insensitive, ignoring spaces)
                    normalized_col = re.sub(r'\s+', '', col.lower())
                    for alt in alternatives:
                        normalized_alt = re.sub(r'\s+', '', alt.lower())
                        if normalized_col == normalized_alt:
                            new_data[std_col] = self.data[col]
                            self.column_mapping_used[std_col] = col
                            mapped_columns.add(col)
                            found = True
                            logger.debug(f"Fuzzy matched column '{col}' to '{std_col}'")
                            break
                    
                    if found:
                        break
            
            if not found:
                logger.warning(f"Could not find any match for standard column '{std_col}'")
        
        # Add any unmapped columns to the new DataFrame
        for col in original_columns:
            if col not in mapped_columns:
                new_data[col] = self.data[col]
                logger.debug(f"Kept unmapped column '{col}'")
        
        # Replace the original DataFrame with the new one
        self.data = new_data
        
        # Log column mapping results
        logger.info(f"Column mapping complete. Mapped {len(self.column_mapping_used)} columns.")
        for std_col, orig_col in self.column_mapping_used.items():
            logger.info(f"Using '{orig_col}' for '{std_col}'")
        
        # Store column mapping in data quality report
        self.data_quality_report['column_mapping'] = self.column_mapping_used
    
    def validate_data_structure(self):
        """
        Validate the data structure to ensure critical columns exist and have valid values.
        
        Raises:
            ValueError: If critical validation fails
        """
        logger.info("Validating data structure")
        
        validation_errors = []
        validation_warnings = []
        
        # Check for required columns
        for col, validation in self.DATA_VALIDATION.items():
            if validation.get('required', False) and col not in self.data.columns:
                error_msg = f"Required column '{col}' is missing"
                validation_errors.append(error_msg)
                logger.error(error_msg)
        
        # If critical columns are missing, raise error
        if validation_errors:
            raise ValueError(f"Data validation failed: {'; '.join(validation_errors)}")
        
        # Convert date columns to datetime
        date_columns = [col for col in self.data.columns if 'Date' in col]
        for col in date_columns:
            try:
                self.data[col] = pd.to_datetime(self.data[col], errors='coerce')
                # Check for NaT values after conversion
                nat_count = self.data[col].isna().sum()
                if nat_count > 0:
                    warning_msg = f"Found {nat_count} invalid date values in '{col}'"
                    validation_warnings.append(warning_msg)
                    logger.warning(warning_msg)
            except Exception as e:
                warning_msg = f"Error converting '{col}' to datetime: {str(e)}"
                validation_warnings.append(warning_msg)
                logger.warning(warning_msg)
        
        # Validate numeric columns
        for col, validation in self.DATA_VALIDATION.items():
            if col in self.data.columns and validation.get('type') not in ['datetime', str]:
                # Convert to numeric, coercing errors to NaN
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
                
                # Check for NaN values after conversion
                nan_count = self.data[col].isna().sum()
                if nan_count > 0:
                    warning_msg = f"Found {nan_count} non-numeric values in '{col}'"
                    validation_warnings.append(warning_msg)
                    logger.warning(warning_msg)
                
                # Check value ranges
                min_val = validation.get('min')
                max_val = validation.get('max')
                
                if min_val is not None and max_val is not None:
                    out_of_range = ((self.data[col] < min_val) | (self.data[col] > max_val)).sum()
                    if out_of_range > 0:
                        warning_msg = f"Found {out_of_range} values outside range [{min_val}, {max_val}] in '{col}'"
                        validation_warnings.append(warning_msg)
                        logger.warning(warning_msg)
                        
                        # Track outliers in data quality report
                        self.data_quality_report['outliers'][col] = {
                            'count': out_of_range,
                            'min': min_val,
                            'max': max_val
                        }
        
        # Check for duplicate records
        if 'UUID' in self.data.columns and 'Injection Date' in self.data.columns:
            dup_count = self.data.duplicated(subset=['UUID', 'Injection Date']).sum()
            if dup_count > 0:
                warning_msg = f"Found {dup_count} duplicate patient-date combinations"
                validation_warnings.append(warning_msg)
                logger.warning(warning_msg)
        
        # Check temporal sequence integrity
        if 'UUID' in self.data.columns and 'Injection Date' in self.data.columns:
            # Group by patient and check date ordering
            patient_groups = self.data.groupby('UUID')
            sequence_errors = 0
            
            for patient_id, group in patient_groups:
                sorted_group = group.sort_values('Injection Date')
                if not sorted_group['Injection Date'].equals(group['Injection Date']):
                    sequence_errors += 1
                    logger.warning(f"Patient {patient_id} has out-of-sequence injection dates")
            
            if sequence_errors > 0:
                warning_msg = f"Found {sequence_errors} patients with out-of-sequence injection dates"
                validation_warnings.append(warning_msg)
                logger.warning(warning_msg)
                
                # Track temporal anomalies in data quality report
                self.data_quality_report['temporal_anomalies']['sequence_errors'] = sequence_errors
        
        # Store validation results in data quality report
        self.data_quality_report['validation_errors'] = validation_errors
        self.data_quality_report['validation_warnings'] = validation_warnings
        
        logger.info(f"Data validation complete with {len(validation_errors)} errors and {len(validation_warnings)} warnings")
    
    def clean_data(self):
        """
        Clean the data by handling missing values, outliers, and other anomalies.
        """
        logger.info("Cleaning and preprocessing data")
        
        # Handle missing values in critical fields
        self.handle_missing_values()
        
        # Clean VA measurements
        self.clean_va_measurements()
        
        # Handle temporal anomalies
        self.handle_temporal_anomalies()
        
        # Create a unique patient identifier (if not already present)
        self.create_patient_id()
        
        logger.info("Data cleaning complete")
    
    def handle_missing_values(self):
        """
        Handle missing values in the dataset.
        """
        # Track missing value counts before cleaning
        missing_before = {col: self.data[col].isna().sum() for col in self.data.columns}
        self.data_quality_report['missing_values_before'] = missing_before
        
        # Handle missing baseline VA
        if 'Baseline VA Letter Score' in self.data.columns and 'VA Letter Score at Injection' in self.data.columns:
            missing_baseline = self.data['Baseline VA Letter Score'].isna()
            if missing_baseline.any():
                logger.info(f"Handling {missing_baseline.sum()} missing Baseline VA values")
                
                # For each patient with missing baseline, use their first available VA measurement
                for patient_id in self.data.loc[missing_baseline, 'UUID'].unique():
                    patient_data = self.data[self.data['UUID'] == patient_id].sort_values('Injection Date')
                    if not patient_data.empty and not patient_data['VA Letter Score at Injection'].isna().all():
                        first_va = patient_data['VA Letter Score at Injection'].iloc[0]
                        self.data.loc[(self.data['UUID'] == patient_id) & missing_baseline, 'Baseline VA Letter Score'] = first_va
                        logger.debug(f"Set Baseline VA for patient {patient_id} to {first_va}")
        
        # Handle missing Days Since Last Injection by calculating from dates
        if 'Injection Date' in self.data.columns and 'UUID' in self.data.columns:
            if 'Days Since Last Injection' not in self.data.columns:
                self.data['Days Since Last Injection'] = np.nan
                logger.info("Created 'Days Since Last Injection' column")
            
            # Calculate days since last injection for each patient
            for patient_id, group in self.data.groupby('UUID'):
                sorted_group = group.sort_values('Injection Date')
                if len(sorted_group) > 1:
                    # Calculate days between consecutive injections
                    dates = sorted_group['Injection Date'].values
                    indices = sorted_group.index[1:]  # Skip first injection (no previous)
                    
                    for i, idx in enumerate(indices):
                        days = (dates[i+1] - dates[i]).astype('timedelta64[D]').astype(int)
                        self.data.loc[idx, 'Days Since Last Injection'] = days
                        
            logger.debug("Calculated missing 'Days Since Last Injection' values")
        
        # Track missing value counts after cleaning
        missing_after = {col: self.data[col].isna().sum() for col in self.data.columns}
        self.data_quality_report['missing_values_after'] = missing_after
    
    def clean_va_measurements(self):
        """
        Validate and clean Visual Acuity measurements.
        """
        if 'VA Letter Score at Injection' in self.data.columns:
            va_col = 'VA Letter Score at Injection'
            
            # Count outliers before cleaning
            outliers_before = ((self.data[va_col] < 0) | (self.data[va_col] > 100)).sum()
            self.data_quality_report['va_outliers_before'] = outliers_before
            
            # Clip VA values to valid range
            if outliers_before > 0:
                logger.warning(f"Clipping {outliers_before} VA values to range [0, 100]")
                self.data[va_col] = self.data[va_col].clip(0, 100)
            
            # Handle implausible changes in VA
            if 'UUID' in self.data.columns:
                implausible_changes = 0
                
                for patient_id, group in self.data.groupby('UUID'):
                    sorted_group = group.sort_values('Injection Date')
                    va_values = sorted_group[va_col]
                    
                    # Check for large changes between consecutive measurements (>30 letters)
                    if len(va_values) > 1:
                        changes = va_values.diff().abs()
                        large_changes = changes > 30
                        
                        if large_changes.sum() > 0:
                            implausible_changes += large_changes.sum()
                            logger.warning(f"Patient {patient_id} has {large_changes.sum()} implausibly large VA changes")
                
                self.data_quality_report['va_implausible_changes'] = implausible_changes
    
    def handle_temporal_anomalies(self):
        """
        Handle anomalies related to dates and time intervals.
        """
        if 'Injection Date' not in self.data.columns or 'UUID' not in self.data.columns:
            return
        
        # Count patients with single injections
        patient_injection_counts = self.data.groupby('UUID').size()
        single_injection_patients = (patient_injection_counts == 1).sum()
        self.data_quality_report['single_injection_patients'] = single_injection_patients
        
        # Handle out-of-sequence dates
        sequence_fixes = 0
        
        for patient_id, group in self.data.groupby('UUID'):
            if len(group) <= 1:
                continue
                
            # Check if dates are already sorted
            if group['Injection Date'].equals(group.sort_values('Injection Date')['Injection Date']):
                continue
                
            # Fix by sorting and recalculating intervals
            logger.warning(f"Fixing out-of-sequence dates for patient {patient_id}")
            sequence_fixes += 1
            
            # Sort by date
            sorted_indices = group.sort_values('Injection Date').index
            
            # Update the original DataFrame to maintain the sorted order
            self.data.loc[sorted_indices, 'Injection Date'] = self.data.loc[sorted_indices, 'Injection Date'].values
        
        self.data_quality_report['sequence_fixes'] = sequence_fixes
        
        # Identify treatment gaps > 6 months (180 days)
        if 'Days Since Last Injection' in self.data.columns:
            long_gaps = (self.data['Days Since Last Injection'] > 180).sum()
            self.data_quality_report['long_treatment_gaps'] = long_gaps
            
            if long_gaps > 0:
                logger.info(f"Found {long_gaps} treatment gaps > 6 months")
                
                # Flag these gaps in the data
                self.data['Long_Gap'] = self.data['Days Since Last Injection'] > 180
    
    def create_patient_id(self):
        """
        Create a unique patient identifier if not already present.
        """
        # Create a unique patient identifier
        if 'UUID' in self.data.columns:
            # Use existing UUID if available
            self.data['patient_id'] = self.data['UUID']
            logger.debug("Using existing UUID as patient_id")
        else:
            # Create a composite ID from available fields
            id_components = []
            for field in ['Current Age', 'Gender', 'Eye', 'Date of 1st Injection']:
                if field in self.data.columns:
                    id_components.append(self.data[field].astype(str))
            
            if id_components:
                self.data['patient_id'] = pd.Series(['_'.join(row) for row in zip(*id_components)])
                logger.debug("Created composite patient_id")
            else:
                logger.warning("Could not create patient_id, no suitable columns found")
    
    def generate_data_quality_report(self):
        """
        Generate a comprehensive data quality report.
        """
        logger.info("Generating data quality report")
        
        # Calculate overall data quality metrics
        total_rows = len(self.data)
        total_cells = total_rows * len(self.data.columns)
        
        # Calculate missing values percentage
        missing_cells = sum(self.data[col].isna().sum() for col in self.data.columns)
        missing_percentage = (missing_cells / total_cells) * 100 if total_cells > 0 else 0
        
        # Add summary metrics to report
        self.data_quality_report['summary'] = {
            'total_rows': total_rows,
            'total_columns': len(self.data.columns),
            'missing_cells': missing_cells,
            'missing_percentage': missing_percentage,
            'mapped_columns': len(self.column_mapping_used),
            'validation_errors': len(self.data_quality_report['validation_errors']),
            'validation_warnings': len(self.data_quality_report['validation_warnings'])
        }
        
        # Save report to file
        report_path = os.path.join(self.output_dir, 'data_quality_report.txt')
        
        with open(report_path, 'w') as f:
            f.write("=== EYLEA DATA QUALITY REPORT ===\n\n")
            
            # Write summary
            f.write("SUMMARY:\n")
            f.write(f"Total rows: {total_rows}\n")
            f.write(f"Total columns: {len(self.data.columns)}\n")
            f.write(f"Missing cells: {missing_cells} ({missing_percentage:.2f}%)\n")
            f.write(f"Validation errors: {len(self.data_quality_report['validation_errors'])}\n")
            f.write(f"Validation warnings: {len(self.data_quality_report['validation_warnings'])}\n\n")
            
            # Write column mapping
            f.write("COLUMN MAPPING:\n")
            for std_col, orig_col in self.column_mapping_used.items():
                f.write(f"  {std_col} <- {orig_col}\n")
            f.write("\n")
            
            # Write validation errors
            if self.data_quality_report['validation_errors']:
                f.write("VALIDATION ERRORS:\n")
                for error in self.data_quality_report['validation_errors']:
                    f.write(f"  {error}\n")
                f.write("\n")
            
            # Write validation warnings
            if self.data_quality_report['validation_warnings']:
                f.write("VALIDATION WARNINGS:\n")
                for warning in self.data_quality_report['validation_warnings']:
                    f.write(f"  {warning}\n")
                f.write("\n")
            
            # Write missing values
            f.write("MISSING VALUES BY COLUMN:\n")
            for col, count in self.data_quality_report['missing_values_after'].items():
                if count > 0:
                    percentage = (count / total_rows) * 100
                    f.write(f"  {col}: {count} ({percentage:.2f}%)\n")
            f.write("\n")
            
            # Write temporal anomalies
            f.write("TEMPORAL ANOMALIES:\n")
            f.write(f"  Sequence errors: {self.data_quality_report.get('temporal_anomalies', {}).get('sequence_errors', 0)}\n")
            f.write(f"  Sequence fixes: {self.data_quality_report.get('sequence_fixes', 0)}\n")
            f.write(f"  Long treatment gaps (>6 months): {self.data_quality_report.get('long_treatment_gaps', 0)}\n")
            f.write(f"  Single injection patients: {self.data_quality_report.get('single_injection_patients', 0)}\n")
            f.write("\n")
            
            # Write VA anomalies
            f.write("VA MEASUREMENT ANOMALIES:\n")
            f.write(f"  VA outliers before cleaning: {self.data_quality_report.get('va_outliers_before', 0)}\n")
            f.write(f"  Implausible VA changes (>30 letters): {self.data_quality_report.get('va_implausible_changes', 0)}\n")
        
        logger.info(f"Data quality report saved to {report_path}")
        
        return self.data_quality_report
    
    def analyze_patient_cohort(self):
        """Analyze the patient cohort characteristics."""
        if self.data is None:
            self.load_data()
        
        logger.debug("Analyzing patient cohort")
        
        # Get unique patients
        patient_ids = self.data['patient_id'].unique()
        logger.debug(f"Found {len(patient_ids)} unique patients")
        
        # Create a dataframe with one row per patient
        patient_data = []
        
        for patient_id in patient_ids:
            patient_rows = self.data[self.data['patient_id'] == patient_id]
            
            # Get the first row for this patient
            first_row = patient_rows.iloc[0]
            
            # Extract patient characteristics
            patient_info = {
                'patient_id': patient_id,
                'age': first_row.get('Current Age', np.nan),
                'gender': first_row.get('Gender', 'Unknown'),
                'eye': first_row.get('Eye', 'Unknown'),
                'baseline_va': first_row.get('Baseline VA Letter Score', np.nan),
                'baseline_crt': first_row.get('Baseline CRT', np.nan),
                'first_injection_date': first_row.get('Date of 1st Injection', np.nan),
                'injection_count': len(patient_rows),
                'deceased': first_row.get('Deceased', 0)
            }
            
            # Calculate treatment duration if possible
            if 'Injection Date' in patient_rows.columns:
                injection_dates = pd.to_datetime(patient_rows['Injection Date'])
                if not injection_dates.empty:
                    patient_info['first_injection'] = injection_dates.min()
                    patient_info['last_injection'] = injection_dates.max()
                    patient_info['treatment_duration_days'] = (
                        patient_info['last_injection'] - patient_info['first_injection']
                    ).days
            
            patient_data.append(patient_info)
        
        self.patient_data = pd.DataFrame(patient_data)
        logger.debug(f"Created patient_data DataFrame with {len(self.patient_data)} rows")
        
        return self.patient_data
    
    def analyze_injection_intervals(self):
        """Analyze the intervals between injections."""
        if self.data is None:
            self.load_data()
        
        logger.debug("Analyzing injection intervals")
        
        # Create a list to store interval data
        intervals_data = []
        
        # Group by patient_id
        for patient_id, patient_rows in self.data.groupby('patient_id'):
            # Sort by injection date
            if 'Injection Date' in patient_rows.columns:
                patient_rows = patient_rows.sort_values('Injection Date')
                
                # Calculate intervals between consecutive injections
                injection_dates = pd.to_datetime(patient_rows['Injection Date'])
                
                if len(injection_dates) > 1:
                    for i in range(1, len(injection_dates)):
                        interval = (injection_dates.iloc[i] - injection_dates.iloc[i-1]).days
                        
                        intervals_data.append({
                            'patient_id': patient_id,
                            'injection_number': i,
                            'previous_date': injection_dates.iloc[i-1],
                            'current_date': injection_dates.iloc[i],
                            'interval_days': interval,
                            'long_gap': interval > 180  # Flag gaps > 6 months
                        })
        
        self.injection_intervals = pd.DataFrame(intervals_data)
        logger.debug(f"Created injection_intervals DataFrame with {len(self.injection_intervals)} rows")
        
        # Calculate summary statistics
        if not self.injection_intervals.empty:
            stats = {
                'mean_interval': self.injection_intervals['interval_days'].mean(),
                'median_interval': self.injection_intervals['interval_days'].median(),
                'min_interval': self.injection_intervals['interval_days'].min(),
                'max_interval': self.injection_intervals['interval_days'].max(),
                'std_interval': self.injection_intervals['interval_days'].std(),
                'long_gaps': self.injection_intervals['long_gap'].sum()
            }
            
            logger.debug(f"Injection interval statistics: {stats}")
        
        return self.injection_intervals
    
    def analyze_va_trajectories(self):
        """Analyze visual acuity trajectories over time."""
        if self.data is None:
            self.load_data()
        
        logger.debug("Analyzing visual acuity trajectories")
        
        # Create a list to store VA trajectory data
        va_data = []
        
        # Group by patient_id
        for patient_id, patient_rows in self.data.groupby('patient_id'):
            # Sort by injection date
            if 'Injection Date' in patient_rows.columns:
                patient_rows = patient_rows.sort_values('Injection Date')
                
                # Get baseline VA
                baseline_va = patient_rows.iloc[0].get('Baseline VA Letter Score', np.nan)
                
                # If baseline VA is missing, use first available VA measurement
                if pd.isna(baseline_va) and 'VA Letter Score at Injection' in patient_rows.columns:
                    first_va = patient_rows.iloc[0].get('VA Letter Score at Injection', np.nan)
                    if pd.notna(first_va):
                        baseline_va = first_va
                        logger.debug(f"Using first VA measurement as baseline for patient {patient_id}")
                
                # Extract VA at each injection
                for i, row in enumerate(patient_rows.itertuples()):
                    injection_date = getattr(row, 'Injection Date', None)
                    va_score = getattr(row, 'VA Letter Score at Injection', np.nan)
                    
                    if pd.notna(injection_date) and pd.notna(va_score):
                        # Calculate days from first injection
                        first_date = pd.to_datetime(patient_rows.iloc[0]['Injection Date'])
                        current_date = pd.to_datetime(injection_date)
                        days_from_first = (current_date - first_date).days
                        
                        va_data.append({
                            'patient_id': patient_id,
                            'injection_number': i,
                            'days_from_first': days_from_first,
                            'va_score': va_score,
                            'baseline_va': baseline_va,
                            'va_change': va_score - baseline_va if pd.notna(baseline_va) else np.nan
                        })
        
        self.va_trajectories = pd.DataFrame(va_data)
        logger.debug(f"Created va_trajectories DataFrame with {len(self.va_trajectories)} rows")
        
        return self.va_trajectories
    
    def plot_injection_intervals(self):
        """Plot the distribution of injection intervals."""
        if self.injection_intervals is None:
            self.analyze_injection_intervals()
        
        if self.injection_intervals.empty:
            logger.warning("No injection interval data available for plotting")
            return
        
        logger.debug("Plotting injection intervals")
        
        plt.figure(figsize=(10, 6))
        
        # Create a histogram of injection intervals
        sns.histplot(self.injection_intervals['interval_days'], bins=30, kde=True)
        
        plt.title('Distribution of Injection Intervals')
        plt.xlabel('Interval (days)')
        plt.ylabel('Frequency')
        
        # Add vertical lines for common intervals
        plt.axvline(x=28, color='r', linestyle='--', label='28 days (monthly)')
        plt.axvline(x=56, color='g', linestyle='--', label='56 days (bi-monthly)')
        plt.axvline(x=84, color='b', linestyle='--', label='84 days (quarterly)')
        
        plt.legend()
        
        # Save the plot
        output_path = os.path.join(self.output_dir, 'injection_intervals.png')
        plt.savefig(output_path)
        logger.debug(f"Saved injection intervals plot to {output_path}")
        
        plt.close()
        
        # Also plot intervals by injection sequence
        plt.figure(figsize=(12, 6))
        
        # Group by injection number and calculate statistics
        grouped = self.injection_intervals.groupby('injection_number')['interval_days'].agg(['mean', 'median', 'std']).reset_index()
        
        # Plot mean intervals with error bars
        plt.errorbar(grouped['injection_number'], grouped['mean'], yerr=grouped['std'], 
                     fmt='o-', capsize=5, label='Mean ± SD')
        plt.plot(grouped['injection_number'], grouped['median'], 's--', label='Median')
        
        plt.title('Injection Intervals by Sequence')
        plt.xlabel('Injection Number')
        plt.ylabel('Interval (days)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Save the plot
        output_path = os.path.join(self.output_dir, 'injection_intervals_by_sequence.png')
        plt.savefig(output_path)
        logger.debug(f"Saved injection intervals by sequence plot to {output_path}")
        
        plt.close()
    
    def plot_va_trajectories(self):
        """Plot visual acuity trajectories."""
        if self.va_trajectories is None:
            self.analyze_va_trajectories()
        
        if self.va_trajectories.empty:
            logger.warning("No VA trajectory data available for plotting")
            return
        
        logger.debug("Plotting VA trajectories")
        
        plt.figure(figsize=(12, 8))
        
        # Plot individual patient trajectories (limit to 20 patients for clarity)
        patient_ids = self.va_trajectories['patient_id'].unique()
        sample_patients = patient_ids[:min(20, len(patient_ids))]
        
        for patient_id in sample_patients:
            patient_data = self.va_trajectories[self.va_trajectories['patient_id'] == patient_id]
            plt.plot(patient_data['days_from_first'], patient_data['va_score'], 
                     'o-', alpha=0.5, linewidth=1)
        
        # Add a LOESS smoothed average line
        if len(self.va_trajectories) > 10:  # Only if we have enough data
            try:
                from statsmodels.nonparametric.smoothers_lowess import lowess
                
                # Group by days_from_first and calculate mean VA
                grouped = self.va_trajectories.groupby('days_from_first')['va_score'].mean().reset_index()
                
                # Apply LOWESS smoothing
                smoothed = lowess(grouped['va_score'], grouped['days_from_first'], frac=0.3)
                
                # Plot the smoothed line
                plt.plot(smoothed[:, 0], smoothed[:, 1], 'r-', linewidth=3, 
                         label='Population average (LOESS)')
                
            except ImportError:
                logger.warning("statsmodels not available, skipping LOESS smoothing")
                
                # Simple moving average as fallback
                grouped = self.va_trajectories.groupby('days_from_first')['va_score'].mean().reset_index()
                plt.plot(grouped['days_from_first'], grouped['va_score'], 'r-', linewidth=3,
                         label='Population average')
        
        plt.title('Visual Acuity Trajectories')
        plt.xlabel('Days from First Injection')
        plt.ylabel('VA Letter Score')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Save the plot
        output_path = os.path.join(self.output_dir, 'va_trajectories.png')
        plt.savefig(output_path)
        logger.debug(f"Saved VA trajectories plot to {output_path}")
        
        plt.close()
        
        # Also plot VA by injection number
        plt.figure(figsize=(12, 6))
        
        # Group by injection number and calculate statistics
        grouped = self.va_trajectories.groupby('injection_number')['va_score'].agg(['mean', 'median', 'std', 'count']).reset_index()
        
        # Plot mean VA with error bars
        plt.errorbar(grouped['injection_number'], grouped['mean'], yerr=grouped['std'], 
                     fmt='o-', capsize=5, label='Mean ± SD')
        
        # Add count labels
        for i, row in grouped.iterrows():
            plt.text(row['injection_number'], row['mean'] + row['std'] + 2, 
                     f"n={int(row['count'])}", ha='center')
        
        plt.title('Visual Acuity by Injection Number')
        plt.xlabel('Injection Number')
        plt.ylabel('VA Letter Score')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Save the plot
        output_path = os.path.join(self.output_dir, 'va_by_injection_number.png')
        plt.savefig(output_path)
        logger.debug(f"Saved VA by injection number plot to {output_path}")
        
        plt.close()
    
    def plot_va_change_distribution(self):
        """Plot the distribution of VA changes from baseline."""
        if self.va_trajectories is None:
            self.analyze_va_trajectories()
        
        if self.va_trajectories.empty:
            logger.warning("No VA trajectory data available for plotting")
            return
        
        logger.debug("Plotting VA change distribution")
        
        # Filter to last available VA measurement for each patient
        last_measurements = self.va_trajectories.loc[
            self.va_trajectories.groupby('patient_id')['injection_number'].idxmax()
        ]
        
        plt.figure(figsize=(10, 6))
        
        # Create a histogram of VA changes
        sns.histplot(last_measurements['va_change'].dropna(), bins=20, kde=True)
        
        plt.title('Distribution of VA Changes from Baseline (Last Available Measurement)')
        plt.xlabel('VA Change (letters)')
        plt.ylabel('Frequency')
        
        # Add vertical lines for clinically significant changes
        plt.axvline(x=0, color='k', linestyle='-', label='No change')
        plt.axvline(x=5, color='g', linestyle='--', label='+5 letters (gain)')
        plt.axvline(x=15, color='b', linestyle='--', label='+15 letters (significant gain)')
        plt.axvline(x=-5, color='r', linestyle='--', label='-5 letters (loss)')
        plt.axvline(x=-15, color='m', linestyle='--', label='-15 letters (significant loss)')
        
        plt.legend()
        
        # Save the plot
        output_path = os.path.join(self.output_dir, 'va_change_distribution.png')
        plt.savefig(output_path)
        logger.debug(f"Saved VA change distribution plot to {output_path}")
        
        plt.close()
        
        # Also create a categorical plot of VA outcomes
        plt.figure(figsize=(10, 6))
        
        # Create categories
        def categorize_va_change(change):
            if pd.isna(change):
                return 'Unknown'
            elif change >= 15:
                return '≥15 letter gain'
            elif change >= 5:
                return '5-14 letter gain'
            elif change > -5:
                return 'Stable (-4 to +4)'
            elif change >= -15:
                return '5-14 letter loss'
            else:
                return '≥15 letter loss'
        
        last_measurements['outcome_category'] = last_measurements['va_change'].apply(categorize_va_change)
        
        # Order categories
        category_order = ['≥15 letter gain', '5-14 letter gain', 'Stable (-4 to +4)', 
                          '5-14 letter loss', '≥15 letter loss', 'Unknown']
        
        # Count patients in each category
        outcome_counts = last_measurements['outcome_category'].value_counts().reindex(category_order).fillna(0)
        
        # Calculate percentages
        total = outcome_counts.sum()
        outcome_percentages = (outcome_counts / total * 100).round(1)
        
        # Create bar plot
        bars = plt.bar(outcome_counts.index, outcome_counts.values)
        
        # Add percentage labels
        for i, (count, percentage) in enumerate(zip(outcome_counts, outcome_percentages)):
            plt.text(i, count + 0.5, f"{percentage}%", ha='center')
        
        plt.title('Visual Acuity Outcomes (Last Available Measurement)')
        plt.ylabel('Number of Patients')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(self.output_dir, 'va_outcome_categories.png')
        plt.savefig(output_path)
        logger.debug(f"Saved VA outcome categories plot to {output_path}")
        
        plt.close()
    
    def run_analysis(self):
        """Run the complete analysis pipeline."""
        logger.info("Starting Eylea data analysis")
        
        # Load and clean data
        self.load_data()
        
        # Analyze patient cohort
        self.analyze_patient_cohort()
        
        # Analyze injection intervals
        self.analyze_injection_intervals()
        
        # Analyze VA trajectories
        self.analyze_va_trajectories()
        
        # Generate plots
        self.plot_injection_intervals()
        self.plot_va_trajectories()
        self.plot_va_change_distribution()
        
        logger.info("Analysis complete")
        
        # Return a summary of the analysis
        return {
            'patient_count': len(self.patient_data) if self.patient_data is not None else 0,
            'injection_count': len(self.data) if self.data is not None else 0,
            'mean_injection_interval': self.injection_intervals['interval_days'].mean() if self.injection_intervals is not None and not self.injection_intervals.empty else None,
            'median_injection_interval': self.injection_intervals['interval_days'].median() if self.injection_intervals is not None and not self.injection_intervals.empty else None,
            'output_dir': str(self.output_dir),
            'data_quality_report': self.data_quality_report.get('summary', {})
        }


def main():
    """Main function to run the analysis."""
    # Set up command line argument parsing
    import argparse
    parser = argparse.ArgumentParser(description='Analyze Eylea treatment data')
    parser.add_argument('--data', type=str, default='input_data/sample_raw.csv',
                        help='Path to the data CSV file')
    parser.add_argument('--output', type=str, default='output',
                        help='Directory to save output files')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug output')
    parser.add_argument('--validation-strictness', type=str, choices=['strict', 'moderate', 'lenient'], 
                        default='moderate', help='Validation strictness level')
    
    args = parser.parse_args()
    
    # Set logging level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    # Create and run the analyzer
    analyzer = EyleaDataAnalyzer(args.data, args.output)
    analyzer.debug = args.debug
    
    results = analyzer.run_analysis()
    
    # Print summary results
    print("\nAnalysis Results Summary:")
    print(f"Patient count: {results['patient_count']}")
    print(f"Injection count: {results['injection_count']}")
    
    if results['mean_injection_interval'] is not None:
        print(f"Mean injection interval: {results['mean_injection_interval']:.1f} days")
    if results['median_injection_interval'] is not None:
        print(f"Median injection interval: {results['median_injection_interval']:.1f} days")
    
    print(f"Output saved to: {results['output_dir']}")
    
    # Print data quality summary
    if 'data_quality_report' in results:
        quality = results['data_quality_report']
        print("\nData Quality Summary:")
        print(f"Total rows: {quality.get('total_rows', 'N/A')}")
        print(f"Missing data: {quality.get('missing_percentage', 'N/A'):.1f}%")
        print(f"Validation warnings: {quality.get('validation_warnings', 'N/A')}")
        print(f"Column mappings applied: {quality.get('mapped_columns', 'N/A')}")


if __name__ == "__main__":
    main()
