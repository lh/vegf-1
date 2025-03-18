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

# Set up logging with ERROR level to minimize output
import logging
logging.basicConfig(
    level=logging.ERROR,  # Set to ERROR to minimize output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress matplotlib and PIL debug messages
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

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
        'Age at Death': ['Age at Death', 'Death Age', 'Age When Deceased', 'Deceased Age'],
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
        'Age at Death': {'type': float, 'min': 0, 'max': 120, 'required': False},
        'Deceased': {'type': int, 'min': 0, 'max': 1, 'required': False},
        'Days Since Last Injection': {'type': float, 'min': 0, 'max': 365, 'required': False},
        'CRT at Injection': {'type': float, 'min': 0, 'max': 1000, 'required': False}
    }
    
    def __init__(self, data_path, output_dir=None):
        """
        Initialize the analyzer with data path.
        
        Parameters
        ----------
        data_path : str
            Path to the CSV data file containing Eylea treatment data
        output_dir : str, optional
            Directory to save outputs. If None, creates an 'output' directory
            in the current working directory.
            
        Notes
        -----
        This initializes the analyzer but does not load or process the data.
        Call `load_data()` to load and validate the data, or `run_analysis()`
        to perform the complete analysis pipeline.
        """
        self.data_path = data_path
        self.output_dir = output_dir or Path('output')
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.data = None
        self.patient_data = None
        self.injection_intervals = None
        self.va_trajectories = None
        self.treatment_courses = None
        
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
            'column_mapping': {},
            'age_adjustments': {}
        }
    
    def load_data(self):
        """
        Load and perform initial cleaning of the data with enhanced validation.
        
        Returns
        -------
        pandas.DataFrame
            The loaded and validated data
            
        Raises
        ------
        ValueError
            If critical data validation fails, such as missing required columns
            
        Notes
        -----
        This method performs several operations:
        1. Loads the CSV file specified in `data_path`
        2. Maps column names to standardized format
        3. Validates data structure and types
        4. Cleans and preprocesses the data
        5. Generates a data quality report
        
        The processed data is stored in the `data` attribute and also returned.
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
        
        This method handles variations in column naming conventions by mapping
        them to a standardized set of column names defined in COLUMN_MAPPINGS.
        It uses both exact matching and fuzzy matching for minor variations.
        
        Returns
        -------
        None
            Modifies the `data` attribute in-place
            
        Notes
        -----
        The mapping results are stored in:
        - `column_mapping_used` attribute: Dictionary mapping standard names to original names
        - `data_quality_report['column_mapping']`: Same mapping for reporting
        
        Columns that cannot be mapped to standard names are kept unchanged.
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
        
        This method performs comprehensive validation of the dataset structure and content,
        including checking for required columns, converting data types, validating value ranges,
        and identifying temporal anomalies.
        
        Returns
        -------
        None
            Modifies the `data` attribute in-place
            
        Raises
        ------
        ValueError
            If critical validation fails, such as missing required columns
            
        Notes
        -----
        Validation steps include:
        1. Checking for required columns defined in DATA_VALIDATION
        2. Converting date columns to datetime format
        3. Converting and validating numeric columns
        4. Checking for duplicate records
        5. Validating deceased status and age fields
        6. Checking temporal sequence integrity
        
        Validation results are stored in:
        - `data_quality_report['validation_errors']`: List of critical errors
        - `data_quality_report['validation_warnings']`: List of non-critical warnings
        
        For patients with out-of-sequence injection dates, information is saved to
        a CSV file in the output directory.
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
        
        # Validate deceased status and age fields
        if 'Deceased' in self.data.columns:
            # Convert to numeric if not already
            self.data['Deceased'] = pd.to_numeric(self.data['Deceased'], errors='coerce')
            
            # Check deceased=1 cases
            deceased_true = self.data['Deceased'] == 1
            if deceased_true.any():
                if 'Age at Death' not in self.data.columns:
                    error_msg = "'Age at Death' column required when Deceased=1"
                    validation_errors.append(error_msg)
                    logger.error(error_msg)
                elif self.data.loc[deceased_true, 'Age at Death'].isna().any():
                    warning_msg = "Some deceased patients are missing Age at Death"
                    validation_warnings.append(warning_msg)
                    logger.warning(warning_msg)
                
                # Check if deceased patients have Current Age (they shouldn't)
                if 'Current Age' in self.data.columns and self.data.loc[deceased_true, 'Current Age'].notna().any():
                    warning_msg = "Deceased patients should not have Current Age"
                    validation_warnings.append(warning_msg)
                    logger.warning(warning_msg)
            
            # Check deceased=0 cases
            deceased_false = self.data['Deceased'] == 0
            if deceased_false.any():
                if 'Current Age' in self.data.columns and self.data.loc[deceased_false, 'Current Age'].isna().any():
                    warning_msg = "Some living patients are missing Current Age"
                    validation_warnings.append(warning_msg)
                    logger.warning(warning_msg)
                
                # Check if living patients have Age at Death (they shouldn't)
                if 'Age at Death' in self.data.columns and self.data.loc[deceased_false, 'Age at Death'].notna().any():
                    warning_msg = "Living patients should not have Age at Death"
                    validation_warnings.append(warning_msg)
                    logger.warning(warning_msg)
        
        # Check temporal sequence integrity
        if 'UUID' in self.data.columns and 'Injection Date' in self.data.columns:
            # Group by patient and check date ordering
            patient_groups = self.data.groupby('UUID')
            sequence_errors = 0
            patients_with_sequence_errors = []
            
            for patient_id, group in patient_groups:
                sorted_group = group.sort_values('Injection Date')
                if not sorted_group['Injection Date'].equals(group['Injection Date']):
                    sequence_errors += 1
                    # Store patient info instead of logging a warning
                    patients_with_sequence_errors.append({
                        'patient_id': patient_id,
                        'injection_count': len(group),
                        'date_range': f"{group['Injection Date'].min().strftime('%Y-%m-%d')} to {group['Injection Date'].max().strftime('%Y-%m-%d')}"
                    })
            
            if sequence_errors > 0:
                warning_msg = f"Found {sequence_errors} patients with out-of-sequence injection dates"
                validation_warnings.append(warning_msg)
                logger.warning(warning_msg)
                
                # Track temporal anomalies in data quality report
                self.data_quality_report['temporal_anomalies']['sequence_errors'] = sequence_errors
                self.data_quality_report['patients_with_sequence_errors'] = patients_with_sequence_errors
                
                # Save the list of patients with sequence errors to a CSV file
                if self.output_dir:
                    sequence_errors_path = os.path.join(self.output_dir, 'sequence_errors.csv')
                    pd.DataFrame(patients_with_sequence_errors).to_csv(sequence_errors_path, index=False)
                    logger.info(f"Saved list of patients with out-of-sequence injection dates to {sequence_errors_path}")
        
        # Store validation results in data quality report
        self.data_quality_report['validation_errors'] = validation_errors
        self.data_quality_report['validation_warnings'] = validation_warnings
        
        logger.info(f"Data validation complete with {len(validation_errors)} errors and {len(validation_warnings)} warnings")
    
    def clean_data(self):
        """
        Clean the data by handling missing values, outliers, and other anomalies.
        
        This method performs several data cleaning operations to prepare the dataset
        for analysis, including handling missing values, cleaning measurements,
        fixing temporal anomalies, and creating identifiers.
        
        Returns
        -------
        None
            Modifies the `data` attribute in-place
            
        Notes
        -----
        Cleaning operations include:
        1. Handling missing values in critical fields
        2. Cleaning Visual Acuity measurements
        3. Handling temporal anomalies (e.g., out-of-sequence dates)
        4. Creating unique patient and eye identifiers
        
        The cleaning process is tracked in the data_quality_report attribute.
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
        
        This method identifies and handles missing values in various columns,
        with special attention to baseline VA, age data, and injection intervals.
        
        Returns
        -------
        None
            Modifies the `data` attribute in-place
            
        Notes
        -----
        Missing value handling includes:
        1. For missing baseline VA: Use first available VA measurement
        2. For age data: Handle deceased patients differently
        3. For current age: Add 0.5 years to account for temporal alignment
        4. For missing injection intervals: Calculate from dates
        
        Missing value counts before and after cleaning are stored in:
        - `data_quality_report['missing_values_before']`
        - `data_quality_report['missing_values_after']`
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
        
        # Handle age data based on deceased status
        if 'Deceased' in self.data.columns:
            # For deceased patients, ensure Age at Death is used
            deceased_patients = self.data['Deceased'] == 1
            if deceased_patients.any() and 'Age at Death' in self.data.columns:
                logger.info(f"Processing age data for {deceased_patients.sum()} deceased patients")
                
                # Remove Current Age for deceased patients if present
                if 'Current Age' in self.data.columns:
                    self.data.loc[deceased_patients, 'Current Age'] = np.nan
                    logger.debug("Removed Current Age for deceased patients")
        
        # Adjust Current Age by adding 0.5 years
        if 'Current Age' in self.data.columns:
            # Only adjust for non-deceased patients
            if 'Deceased' in self.data.columns:
                living_patients = (self.data['Deceased'] != 1) | self.data['Deceased'].isna()
                self.data.loc[living_patients, 'Adjusted Age'] = self.data.loc[living_patients, 'Current Age'] + 0.5
            else:
                self.data['Adjusted Age'] = self.data['Current Age'] + 0.5
                
            logger.info("Added 'Adjusted Age' column (+0.5 years to Current Age)")
            
            # Track age adjustments in data quality report
            self.data_quality_report['age_adjustments'] = {
                'adjustment_factor': 0.5,
                'adjusted_records': len(self.data[self.data['Adjusted Age'].notna()]),
                'description': "Added 0.5 years to Current Age to account for temporal alignment"
            }
            
            # Calculate estimated birth date if injection dates exist
            if 'Injection Date' in self.data.columns:
                # Convert age in years to days
                age_in_days = self.data['Adjusted Age'] * 365.25
                
                # Subtract from injection date to get estimated birth date
                self.data['Estimated Birth Date'] = self.data['Injection Date'] - pd.to_timedelta(age_in_days, unit='D')
                logger.info("Added 'Estimated Birth Date' based on Adjusted Age and Injection Date")
        
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
        
        This method identifies and handles outliers and implausible changes
        in Visual Acuity (VA) measurements.
        
        Returns
        -------
        None
            Modifies the `data` attribute in-place
            
        Notes
        -----
        VA cleaning operations include:
        1. Clipping VA values to valid range [0, 100]
        2. Identifying implausibly large changes between consecutive measurements (>30 letters)
        
        Information about implausible VA changes is saved to a CSV file in the output directory.
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
                patients_with_implausible_changes = []
                
                for patient_id, group in self.data.groupby('UUID'):
                    sorted_group = group.sort_values('Injection Date')
                    va_values = sorted_group[va_col]
                    
                    # Check for large changes between consecutive measurements (>30 letters)
                    if len(va_values) > 1:
                        changes = va_values.diff().abs()
                        large_changes = changes > 30
                        
                        if large_changes.sum() > 0:
                            change_count = large_changes.sum()
                            implausible_changes += change_count
                            
                            # Store patient info instead of logging a warning
                            patients_with_implausible_changes.append({
                                'patient_id': patient_id,
                                'implausible_change_count': int(change_count),
                                'max_change': float(changes[large_changes].max())
                            })
                
                # Store in data quality report
                self.data_quality_report['va_implausible_changes'] = implausible_changes
                self.data_quality_report['patients_with_implausible_changes'] = patients_with_implausible_changes
                
                # Log a summary instead of individual warnings
                if implausible_changes > 0:
                    logger.warning(f"Found {implausible_changes} implausibly large VA changes across {len(patients_with_implausible_changes)} patients")
                    
                    # Save the list of patients with implausible changes to a CSV file
                    if self.output_dir:
                        implausible_changes_path = os.path.join(self.output_dir, 'implausible_va_changes.csv')
                        pd.DataFrame(patients_with_implausible_changes).to_csv(implausible_changes_path, index=False)
                        logger.info(f"Saved list of patients with implausible VA changes to {implausible_changes_path}")
    
    def handle_temporal_anomalies(self):
        """
        Handle anomalies related to dates and time intervals.
        
        This method identifies and fixes temporal anomalies such as out-of-sequence
        injection dates and long treatment gaps.
        
        Returns
        -------
        None
            Modifies the `data` attribute in-place
            
        Notes
        -----
        Temporal anomaly handling includes:
        1. Identifying patients with single injections
        2. Fixing out-of-sequence injection dates by sorting
        3. Identifying treatment gaps > 6 months (180 days)
        
        Information about fixed sequence errors is saved to a CSV file in the output directory.
        """
        if 'Injection Date' not in self.data.columns or 'UUID' not in self.data.columns:
            return
        
        # Count patients with single injections
        patient_injection_counts = self.data.groupby('UUID').size()
        single_injection_patients = (patient_injection_counts == 1).sum()
        self.data_quality_report['single_injection_patients'] = single_injection_patients
        
        # Handle out-of-sequence dates
        sequence_fixes = 0
        patients_fixed = []
        
        for patient_id, group in self.data.groupby('UUID'):
            if len(group) <= 1:
                continue
                
            # Check if dates are already sorted
            if group['Injection Date'].equals(group.sort_values('Injection Date')['Injection Date']):
                continue
                
            # Fix by sorting and recalculating intervals
            sequence_fixes += 1
            
            # Store patient info instead of logging a warning
            patients_fixed.append({
                'patient_id': patient_id,
                'injection_count': len(group),
                'date_range': f"{group['Injection Date'].min().strftime('%Y-%m-%d')} to {group['Injection Date'].max().strftime('%Y-%m-%d')}"
            })
            
            # Sort by date
            sorted_indices = group.sort_values('Injection Date').index
            
            # Update the original DataFrame to maintain the sorted order
            self.data.loc[sorted_indices, 'Injection Date'] = self.data.loc[sorted_indices, 'Injection Date'].values
        
        self.data_quality_report['sequence_fixes'] = sequence_fixes
        
        # Log a summary instead of individual warnings
        if sequence_fixes > 0:
            logger.warning(f"Fixed out-of-sequence dates for {sequence_fixes} patients")
            
            # Save the list of patients with fixed sequence errors to a CSV file
            if self.output_dir:
                sequence_fixes_path = os.path.join(self.output_dir, 'sequence_fixes.csv')
                pd.DataFrame(patients_fixed).to_csv(sequence_fixes_path, index=False)
                logger.info(f"Saved list of patients with fixed sequence errors to {sequence_fixes_path}")
        
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
        
        This method ensures each patient has a unique identifier and creates
        an eye-specific key to track treatments per eye.
        
        Returns
        -------
        None
            Modifies the `data` attribute in-place
            
        Notes
        -----
        Identifier creation includes:
        1. Using existing UUID if available
        2. Creating a composite ID from available fields if UUID is not present
        3. Creating an eye-specific key by combining patient ID and eye information
        4. Sorting data by eye_key and injection date for chronological ordering
        """
        # Create a unique patient identifier
        if 'UUID' in self.data.columns:
            # Use existing UUID if available
            self.data['patient_id'] = self.data['UUID']
            logger.debug("Using existing UUID as patient_id")
            
            # Create an eye-specific key for tracking treatments per eye
            if 'Eye' in self.data.columns:
                # Standardize eye values (uppercase, remove spaces)
                self.data['eye_standardized'] = self.data['Eye'].str.upper().str.replace(' ', '_')
                # Create composite key: UUID_EYE
                self.data['eye_key'] = self.data['UUID'] + '_' + self.data['eye_standardized']
                logger.info(f"Created eye-specific key for tracking treatments per eye")
            else:
                logger.warning("Eye column not found, cannot create eye-specific key")
                # Fall back to using UUID as eye_key
                self.data['eye_key'] = self.data['UUID']
        else:
            # Create a composite ID from available fields
            id_components = []
            for field in ['Current Age', 'Gender', 'Eye', 'Date of 1st Injection']:
                if field in self.data.columns:
                    id_components.append(self.data[field].astype(str))
            
            if id_components:
                self.data['patient_id'] = pd.Series(['_'.join(row) for row in zip(*id_components)])
                logger.debug("Created composite patient_id")
                
                # Also create eye_key if Eye column is available
                if 'Eye' in self.data.columns:
                    self.data['eye_standardized'] = self.data['Eye'].str.upper().str.replace(' ', '_')
                    self.data['eye_key'] = self.data['patient_id'] + '_' + self.data['eye_standardized']
                else:
                    self.data['eye_key'] = self.data['patient_id']
            else:
                logger.warning("Could not create patient_id, no suitable columns found")
                # Create a sequential ID as fallback
                self.data['patient_id'] = [f"P{i:06d}" for i in range(len(self.data))]
                self.data['eye_key'] = self.data['patient_id']
        
        # Sort data by eye_key and injection date to ensure chronological ordering
        if 'Injection Date' in self.data.columns:
            self.data = self.data.sort_values(['eye_key', 'Injection Date'])
            logger.debug("Sorted data by eye_key and injection date")
    
    def generate_data_quality_report(self):
        """
        Generate a comprehensive data quality report.
        
        This method calculates various data quality metrics and saves them
        to a text file in the output directory.
        
        Returns
        -------
        dict
            The data quality report as a dictionary
            
        Notes
        -----
        The report includes:
        1. Summary metrics (rows, columns, missing data percentage)
        2. Column mapping information
        3. Validation errors and warnings
        4. Missing values by column
        5. Age data processing details
        6. Temporal anomalies
        7. VA measurement anomalies
        
        The report is saved to 'data_quality_report.txt' in the output directory.
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
            
            # Write age adjustments
            if 'age_adjustments' in self.data_quality_report:
                f.write("AGE DATA PROCESSING:\n")
                age_adj = self.data_quality_report['age_adjustments']
                f.write(f"  Adjustment factor: +{age_adj.get('adjustment_factor', 0.5)} years\n")
                f.write(f"  Adjusted records: {age_adj.get('adjusted_records', 0)}\n")
                f.write(f"  Description: {age_adj.get('description', 'Age adjustment applied')}\n")
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
        """
        Analyze the patient cohort characteristics.
        
        This method creates a DataFrame with one row per patient, containing
        demographic and treatment information.
        
        Returns
        -------
        pandas.DataFrame
            DataFrame with patient-level information
            
        Notes
        -----
        The patient data includes:
        - Demographics (age, gender)
        - Eye information
        - Baseline measurements (VA, CRT)
        - Treatment information (injection count, dates)
        - Mortality information (deceased status, age at death)
        
        If the data has not been loaded yet, this method will call `load_data()` first.
        """
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
                'adjusted_age': first_row.get('Adjusted Age', np.nan),
                'gender': first_row.get('Gender', 'Unknown'),
                'eye': first_row.get('Eye', 'Unknown'),
                'baseline_va': first_row.get('Baseline VA Letter Score', np.nan),
                'baseline_crt': first_row.get('Baseline CRT', np.nan),
                'first_injection_date': first_row.get('Date of 1st Injection', np.nan),
                'injection_count': len(patient_rows),
                # Handle potential non-numeric values in Deceased column
                'deceased': int(float(first_row.get('Deceased', 0))) if pd.notna(first_row.get('Deceased', 0)) and str(first_row.get('Deceased', 0)).strip() != '' else 0,
                'age_at_death': first_row.get('Age at Death', np.nan)
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
        """
        Analyze the intervals between injections, grouped by eye.
        
        This method calculates the time intervals between consecutive injections
        for each eye and creates a DataFrame with interval information.
        
        Returns
        -------
        pandas.DataFrame
            DataFrame with injection interval information
            
        Notes
        -----
        The interval data includes:
        - Patient and eye identifiers
        - Injection sequence information
        - Dates of consecutive injections
        - Interval in days between injections
        - VA measurements at consecutive injections
        - Flags for long gaps (>180 days) and very long gaps (>365 days)
        
        If the data has not been loaded yet, this method will call `load_data()` first.
        """
        if self.data is None:
            self.load_data()
        
        logger.info("Analyzing injection intervals by eye")
        
        # Create a list to store interval data
        intervals_data = []
        
        # Log the number of unique eye_keys
        unique_eye_keys = self.data['eye_key'].unique()
        logger.info(f"Found {len(unique_eye_keys)} unique eye_keys")
        
        # Group by eye_key instead of patient_id to track treatments per eye
        for eye_key, eye_rows in self.data.groupby('eye_key'):
            # Extract patient_id and eye from eye_key
            patient_id = eye_rows['patient_id'].iloc[0]
            uuid = eye_rows['UUID'].iloc[0] if 'UUID' in eye_rows.columns else patient_id
            eye = eye_rows['Eye'].iloc[0] if 'Eye' in eye_rows.columns else 'Unknown'
            
            # Log the number of injections for this eye (at DEBUG level instead of INFO)
            logger.debug(f"Processing eye_key {eye_key} with {len(eye_rows)} injections")
            
            # Sort by injection date
            if 'Injection Date' in eye_rows.columns:
                eye_rows = eye_rows.sort_values('Injection Date')
                
                # Calculate intervals between consecutive injections
                injection_dates = pd.to_datetime(eye_rows['Injection Date'])
                
                if len(injection_dates) > 1:
                    logger.debug(f"Eye {eye_key} has {len(injection_dates)} injection dates, calculating intervals")
                    for i in range(1, len(injection_dates)):
                        interval = (injection_dates.iloc[i] - injection_dates.iloc[i-1]).days
                        
                        # Flag very large gaps (>365 days) as potential new treatment course
                        very_long_gap = interval > 365
                        
                        # Extract VA scores if available
                        prev_va = None
                        current_va = None
                        
                        if 'VA Letter Score at Injection' in eye_rows.columns:
                            prev_va = eye_rows.iloc[i-1]['VA Letter Score at Injection']
                            current_va = eye_rows.iloc[i]['VA Letter Score at Injection']
                        
                        # Removed redundant interval logging
                        
                        intervals_data.append({
                            'uuid': uuid,
                            'patient_id': patient_id,
                            'eye': eye,
                            'eye_key': eye_key,
                            'injection_number': i,
                            'previous_date': injection_dates.iloc[i-1],
                            'current_date': injection_dates.iloc[i],
                            'interval_days': interval,
                            'prev_va': prev_va,
                            'current_va': current_va,
                            'long_gap': interval > 180,  # Flag gaps > 6 months
                            'very_long_gap': very_long_gap,  # Flag gaps > 12 months
                            'potential_new_course': very_long_gap  # Flag as potential new course
                        })
                else:
                    logger.debug(f"Eye {eye_key} has only {len(injection_dates)} injection date(s), skipping interval calculation")
        
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
        """
        Analyze visual acuity trajectories over time, grouped by eye.
        
        This method tracks changes in Visual Acuity (VA) over time for each eye
        and creates a DataFrame with trajectory information.
        
        Returns
        -------
        pandas.DataFrame
            DataFrame with VA trajectory information
            
        Notes
        -----
        The VA trajectory data includes:
        - Patient and eye identifiers
        - Injection sequence information
        - Days from first injection
        - VA score at each injection
        - Baseline VA
        - VA change from baseline
        
        If the data has not been loaded yet, this method will call `load_data()` first.
        """
        if self.data is None:
            self.load_data()
        
        logger.debug("Analyzing visual acuity trajectories by eye")
        
        # Create a list to store VA trajectory data
        va_data = []
        
        # Group by eye_key instead of patient_id to track VA trajectories per eye
        for eye_key, eye_rows in self.data.groupby('eye_key'):
            # Extract patient_id and eye from eye_key
            patient_id = eye_rows['patient_id'].iloc[0]
            eye = eye_rows['Eye'].iloc[0] if 'Eye' in eye_rows.columns else 'Unknown'
            
            # Sort by injection date
            if 'Injection Date' in eye_rows.columns:
                eye_rows = eye_rows.sort_values('Injection Date')
                
                # Get baseline VA
                baseline_va = eye_rows.iloc[0].get('Baseline VA Letter Score', np.nan)
                
                # If baseline VA is missing, use first available VA measurement
                if pd.isna(baseline_va) and 'VA Letter Score at Injection' in eye_rows.columns:
                    first_va = eye_rows.iloc[0].get('VA Letter Score at Injection', np.nan)
                    if pd.notna(first_va):
                        baseline_va = first_va
                        logger.debug(f"Using first VA measurement as baseline for eye {eye_key}")
                
                # Extract VA at each injection
                for i, row in enumerate(eye_rows.itertuples()):
                    # Get injection date - handle different column name formats in namedtuples
                    injection_date = None
                    try:
                        # Try direct attribute access first
                        if hasattr(row, 'Injection Date'):
                            injection_date = getattr(row, 'Injection Date')
                        # Try underscore version next
                        elif hasattr(row, 'Injection_Date'):
                            injection_date = row.Injection_Date
                        # If still not found, try index-based access using the original DataFrame
                        else:
                            row_idx = row.Index if hasattr(row, 'Index') else i
                            if 'Injection Date' in eye_rows.columns:
                                injection_date = eye_rows.iloc[i]['Injection Date']
                    except Exception as e:
                        logger.warning(f"Error accessing injection date for patient {patient_id}: {str(e)}")
                        injection_date = None
                    
                    # Get VA score - handle different column name formats
                    va_score = np.nan
                    try:
                        # Try direct attribute access first
                        if hasattr(row, 'VA Letter Score at Injection'):
                            va_score = getattr(row, 'VA Letter Score at Injection')
                        # Try underscore version next
                        elif hasattr(row, 'VA_Letter_Score_at_Injection'):
                            va_score = row.VA_Letter_Score_at_Injection
                        # If still not found, try index-based access using the original DataFrame
                        else:
                            row_idx = row.Index if hasattr(row, 'Index') else i
                            if 'VA Letter Score at Injection' in eye_rows.columns:
                                va_score = eye_rows.iloc[i]['VA Letter Score at Injection']
                    except Exception as e:
                        logger.warning(f"Error accessing VA score for patient {patient_id}: {str(e)}")
                        va_score = np.nan
                    
                    # Only add valid data points
                    if pd.notna(injection_date) and pd.notna(va_score):
                        try:
                            # Calculate days from first injection
                            first_date = pd.to_datetime(eye_rows.iloc[0]['Injection Date'])
                            current_date = pd.to_datetime(injection_date)
                            days_from_first = (current_date - first_date).days
                            
                            va_data.append({
                                'patient_id': patient_id,
                                'eye': eye,
                                'eye_key': eye_key,
                                'injection_number': i,
                                'days_from_first': days_from_first,
                                'va_score': float(va_score),  # Ensure numeric type
                                'baseline_va': baseline_va,
                                'va_change': float(va_score) - baseline_va if pd.notna(baseline_va) else np.nan
                            })
                        except Exception as e:
                            logger.warning(f"Error processing VA trajectory for patient {patient_id}: {str(e)}")
        
        self.va_trajectories = pd.DataFrame(va_data)
        logger.debug(f"Created va_trajectories DataFrame with {len(self.va_trajectories)} rows")
        
        return self.va_trajectories
    
    def plot_injection_intervals(self):
        """
        Plot the distribution of injection intervals.
        
        This method creates and saves two plots:
        1. A histogram of injection intervals
        2. A plot of intervals by injection sequence
        
        Returns
        -------
        None
            Saves plots to the output directory
            
        Notes
        -----
        The histogram includes vertical lines for common intervals:
        - 28 days (monthly)
        - 56 days (bi-monthly)
        - 84 days (quarterly)
        
        The sequence plot shows mean and median intervals by injection number.
        
        If injection intervals have not been analyzed yet, this method will call
        `analyze_injection_intervals()` first.
        """
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
        """
        Plot visual acuity trajectories by eye.
        
        This method creates and saves two plots:
        1. VA trajectories over time for a sample of eyes
        2. VA by injection number
        
        Returns
        -------
        None
            Saves plots to the output directory
            
        Notes
        -----
        The trajectory plot includes:
        - Individual eye trajectories (limited to 20 eyes for clarity)
        - A population average line (LOESS smoothed if statsmodels is available)
        
        The injection number plot shows mean VA with error bars by injection number.
        
        If VA trajectories have not been analyzed yet, this method will call
        `analyze_va_trajectories()` first.
        """
        if self.va_trajectories is None:
            self.analyze_va_trajectories()
        
        if self.va_trajectories.empty:
            logger.warning("No VA trajectory data available for plotting")
            return
        
        logger.debug("Plotting VA trajectories by eye")
        
        plt.figure(figsize=(12, 8))
        
        # Plot individual eye trajectories (limit to 20 eyes for clarity)
        eye_keys = self.va_trajectories['eye_key'].unique()
        sample_eyes = eye_keys[:min(20, len(eye_keys))]
        
        for eye_key in sample_eyes:
            eye_data = self.va_trajectories[self.va_trajectories['eye_key'] == eye_key]
            plt.plot(eye_data['days_from_first'], eye_data['va_score'], 
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
        
        plt.title('Visual Acuity Trajectories by Eye')
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
        """
        Plot the distribution of VA changes from baseline.
        
        This method creates and saves two plots:
        1. A histogram of VA changes from baseline
        2. A categorical plot of VA outcomes
        
        Returns
        -------
        None
            Saves plots to the output directory
            
        Notes
        -----
        The histogram includes vertical lines for clinically significant changes:
        - No change (0)
        - +5 letters (gain)
        - +15 letters (significant gain)
        - -5 letters (loss)
        - -15 letters (significant loss)
        
        The categorical plot groups outcomes into categories:
        - ≥15 letter gain
        - 5-14 letter gain
        - Stable (-4 to +4)
        - 5-14 letter loss
        - ≥15 letter loss
        - Unknown
        
        If VA trajectories have not been analyzed yet, this method will call
        `analyze_va_trajectories()` first.
        """
        if self.va_trajectories is None:
            self.analyze_va_trajectories()
        
        if self.va_trajectories.empty:
            logger.warning("No VA trajectory data available for plotting")
            return
        
        logger.debug("Plotting VA change distribution")
        
        # Filter to last available VA measurement for each eye
        last_measurements = self.va_trajectories.loc[
            self.va_trajectories.groupby('eye_key')['injection_number'].idxmax()
        ]
        
        plt.figure(figsize=(10, 6))
        
        # Create a histogram of VA changes
        sns.histplot(last_measurements['va_change'].dropna(), bins=20, kde=True)
        
        plt.title('Distribution of VA Changes from Baseline by Eye (Last Available Measurement)')
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
        
        # Count eyes in each category
        outcome_counts = last_measurements['outcome_category'].value_counts().reindex(category_order).fillna(0)
        
        # Calculate percentages
        total = outcome_counts.sum()
        outcome_percentages = (outcome_counts / total * 100).round(1)
        
        # Create bar plot
        bars = plt.bar(outcome_counts.index, outcome_counts.values)
        
        # Add percentage labels
        for i, (count, percentage) in enumerate(zip(outcome_counts, outcome_percentages)):
            plt.text(i, count + 0.5, f"{percentage}%", ha='center')
        
        plt.title('Visual Acuity Outcomes by Eye (Last Available Measurement)')
        plt.ylabel('Number of Eyes')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(self.output_dir, 'va_outcome_categories.png')
        plt.savefig(output_path)
        logger.debug(f"Saved VA outcome categories plot to {output_path}")
        
        plt.close()
    
    def analyze_treatment_courses(self):
        """
        Analyze treatment courses by identifying potential breaks in treatment.
        
        This method identifies treatment courses for each eye and flags potential
        breaks in treatment based on long gaps between injections.
        
        Returns
        -------
        pandas.DataFrame
            DataFrame with treatment course information
            
        Notes
        -----
        In this implementation, all injections for an eye are considered part of a single course,
        but long gaps (>365 days) are flagged for potential separate analysis.
        
        The treatment course data includes:
        - Patient and eye identifiers
        - Course start and end dates
        - Duration in days
        - Injection count
        - Flags for long pauses
        - Information about potential separate courses
        
        If injection intervals have not been analyzed yet, this method will call
        `analyze_injection_intervals()` first.
        """
        if self.injection_intervals is None:
            self.analyze_injection_intervals()
        
        if self.injection_intervals.empty:
            logger.warning("No injection interval data available for course analysis")
            self.treatment_courses = pd.DataFrame()
            return self.treatment_courses
        
        logger.debug("Analyzing treatment courses")
        
        # Create a list to store course data
        course_data = []
        
        # Group by eye_key
        for eye_key, eye_intervals in self.injection_intervals.groupby('eye_key'):
            # Sort by injection number
            eye_intervals = eye_intervals.sort_values('injection_number')
            
            # Extract patient_id and eye
            patient_id = eye_intervals['patient_id'].iloc[0]
            eye = eye_intervals['eye'].iloc[0]
            
            # Get first and last injection dates
            first_injection_date = eye_intervals['previous_date'].iloc[0]
            last_injection_date = eye_intervals['current_date'].iloc[-1]
            
            # Count total injections (intervals + 1)
            total_injections = len(eye_intervals) + 1
            
            # Check for long pauses
            has_long_pause = eye_intervals['very_long_gap'].any()
            
            # If we wanted to split into multiple courses (keeping for reference)
            potential_courses = []
            if has_long_pause:
                # Track potential separate courses for future analysis
                current_course = 1
                course_start_date = first_injection_date
                course_injections = 1
                
                # Process each interval to identify potential separate courses
                for i, interval in eye_intervals.iterrows():
                    if interval['very_long_gap']:
                        # End previous potential course
                        potential_courses.append({
                            'potential_course_number': current_course,
                            'start_date': course_start_date,
                            'end_date': interval['previous_date'],
                            'duration_days': (interval['previous_date'] - course_start_date).days,
                            'injection_count': course_injections,
                            'gap_to_next_course': interval['interval_days']
                        })
                        
                        # Start new potential course
                        current_course += 1
                        course_start_date = interval['current_date']
                        course_injections = 1
                    else:
                        # Continue current potential course
                        course_injections += 1
                
                # Add the last potential course
                if course_start_date != last_injection_date:
                    potential_courses.append({
                        'potential_course_number': current_course,
                        'start_date': course_start_date,
                        'end_date': last_injection_date,
                        'duration_days': (last_injection_date - course_start_date).days,
                        'injection_count': course_injections,
                        'gap_to_next_course': None
                    })
            
            # Add a single course for this eye
            course_data.append({
                'patient_id': patient_id,
                'eye': eye,
                'eye_key': eye_key,
                'course_number': 1,
                'start_date': first_injection_date,
                'end_date': last_injection_date,
                'duration_days': (last_injection_date - first_injection_date).days,
                'injection_count': total_injections,
                'has_long_pause': has_long_pause,
                'potential_separate_courses': len(potential_courses) if has_long_pause else 1,
                'potential_courses_detail': str(potential_courses) if has_long_pause else None
            })
        
        self.treatment_courses = pd.DataFrame(course_data)
        logger.debug(f"Created treatment_courses DataFrame with {len(self.treatment_courses)} rows")
        
        return self.treatment_courses
    
    def plot_treatment_courses(self):
        """
        Plot treatment courses by eye.
        
        This method creates and saves two plots:
        1. A histogram of treatment course durations
        2. A histogram of injections per course
        
        Returns
        -------
        None
            Saves plots to the output directory
            
        Notes
        -----
        The duration histogram shows the distribution of treatment course durations in days.
        
        The injections histogram shows the distribution of injection counts per course.
        
        If treatment courses have not been analyzed yet, this method will call
        `analyze_treatment_courses()` first.
        """
        if self.treatment_courses is None:
            self.analyze_treatment_courses()
        
        if self.treatment_courses.empty:
            logger.warning("No treatment course data available for plotting")
            return
        
        logger.debug("Plotting treatment courses")
        
        plt.figure(figsize=(12, 8))
        
        # Create a histogram of course durations
        sns.histplot(self.treatment_courses['duration_days'], bins=30, kde=True)
        
        plt.title('Distribution of Treatment Course Durations')
        plt.xlabel('Duration (days)')
        plt.ylabel('Frequency')
        
        # Save the plot
        output_path = os.path.join(self.output_dir, 'treatment_course_durations.png')
        plt.savefig(output_path)
        logger.debug(f"Saved treatment course durations plot to {output_path}")
        
        plt.close()
        
        # Also plot injection count per course
        plt.figure(figsize=(10, 6))
        
        # Create a histogram of injection counts
        sns.histplot(self.treatment_courses['injection_count'], bins=range(1, 21), kde=False, discrete=True)
        
        plt.title('Injections per Treatment Course')
        plt.xlabel('Number of Injections')
        plt.ylabel('Frequency')
        plt.xticks(range(1, 21))
        
        # Save the plot
        output_path = os.path.join(self.output_dir, 'injections_per_course.png')
        plt.savefig(output_path)
        logger.debug(f"Saved injections per course plot to {output_path}")
        
        plt.close()
    
    def export_interval_va_data(self, format='csv', db_path=None):
        """
        Export the interval and VA data to CSV and optionally to SQLite.
        
        Parameters
        ----------
        format : str, optional
            Output format, one of 'csv', 'sqlite', or 'both'. Default is 'csv'.
        db_path : str, optional
            Path to SQLite database. If None, uses default path in the output directory.
        
        Returns
        -------
        dict
            Dictionary with paths to the exported files
            
        Notes
        -----
        This method exports two types of data:
        1. Detailed interval and VA data for each injection
        2. Summary data with intervals and VA changes for each patient
        
        For CSV export:
        - Detailed data is saved to 'interval_va_data.csv'
        - Summary data is saved to 'interval_va_summary.csv'
        
        For SQLite export:
        - Detailed data is saved to 'interval_va_data' table
        - Summary data is saved to 'interval_summary' table
        
        If injection intervals have not been analyzed yet, this method will call
        `analyze_injection_intervals()` first.
        """
        if self.injection_intervals is None:
            self.analyze_injection_intervals()
        
        if self.injection_intervals.empty:
            logger.warning("No injection interval data available for export")
            return {}
        
        logger.info("Exporting interval and VA data")
        
        # Create a DataFrame with the required columns
        export_data = self.injection_intervals[['uuid', 'eye', 'interval_days', 
                                               'prev_va', 'current_va', 
                                               'previous_date', 'current_date']].copy()
        
        # Convert dates to string format for easier export
        export_data['previous_date'] = export_data['previous_date'].dt.strftime('%Y-%m-%d')
        export_data['current_date'] = export_data['current_date'].dt.strftime('%Y-%m-%d')
        
        # Create a list column with all intervals for each UUID
        uuid_intervals = {}
        
        for uuid, group in export_data.groupby('uuid'):
            intervals = group['interval_days'].tolist()
            uuid_intervals[uuid] = intervals
        
        # Create a summary DataFrame with UUID and intervals list
        summary_data = pd.DataFrame({
            'uuid': list(uuid_intervals.keys()),
            'intervals': list(uuid_intervals.values())
        })
        
        # Add VA data to summary
        uuid_va_data = {}
        for uuid, group in export_data.groupby('uuid'):
            va_data = []
            for _, row in group.iterrows():
                if pd.notna(row['prev_va']) and pd.notna(row['current_va']):
                    va_data.append({
                        'interval': row['interval_days'],
                        'prev_va': row['prev_va'],
                        'current_va': row['current_va']
                    })
            uuid_va_data[uuid] = va_data
        
        summary_data['va_data'] = [uuid_va_data.get(uuid, []) for uuid in summary_data['uuid']]
        
        # Export paths
        export_paths = {}
        
        # Export to CSV
        if format in ['csv', 'both']:
            # Export detailed data
            csv_path = os.path.join(self.output_dir, 'interval_va_data.csv')
            export_data.to_csv(csv_path, index=False)
            export_paths['csv'] = csv_path
            logger.info(f"Exported interval and VA data to {csv_path}")
            
            # Export summary data (convert lists to strings for CSV)
            summary_csv_path = os.path.join(self.output_dir, 'interval_va_summary.csv')
            
            # Convert lists to strings for CSV export
            summary_data_csv = summary_data.copy()
            summary_data_csv['intervals'] = summary_data_csv['intervals'].apply(lambda x: ','.join(map(str, x)))
            summary_data_csv['va_data'] = summary_data_csv['va_data'].apply(lambda x: str(x))
            
            summary_data_csv.to_csv(summary_csv_path, index=False)
            export_paths['summary_csv'] = summary_csv_path
            logger.info(f"Exported interval and VA summary to {summary_csv_path}")
        
        # Export to SQLite
        if format in ['sqlite', 'both']:
            try:
                import sqlite3
                
                # Use default path if not provided
                if db_path is None:
                    db_path = os.path.join(self.output_dir, 'eylea_intervals.db')
                
                # Connect to SQLite database
                conn = sqlite3.connect(db_path)
                
                # Export detailed data
                export_data.to_sql('interval_va_data', conn, if_exists='replace', index=False)
                
                # For the summary table with list data, we need to create it manually
                cursor = conn.cursor()
                
                # Create summary table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS interval_summary (
                    uuid TEXT PRIMARY KEY,
                    intervals TEXT,
                    va_data TEXT
                )
                ''')
                
                # Clear existing data
                cursor.execute('DELETE FROM interval_summary')
                
                # Insert summary data
                for _, row in summary_data.iterrows():
                    cursor.execute(
                        'INSERT INTO interval_summary VALUES (?, ?, ?)',
                        (
                            row['uuid'],
                            str(row['intervals']),
                            str(row['va_data'])
                        )
                    )
                
                # Commit changes and close connection
                conn.commit()
                conn.close()
                
                export_paths['sqlite'] = db_path
                logger.info(f"Exported interval and VA data to SQLite database: {db_path}")
                
            except ImportError:
                logger.warning("SQLite support not available, skipping SQLite export")
            except Exception as e:
                logger.error(f"Error exporting to SQLite: {str(e)}")
        
        return export_paths
    
    def run_analysis(self):
        """
        Run the complete analysis pipeline.
        
        This method executes the full analysis workflow, including data loading,
        cleaning, analysis, visualization, and export.
        
        Returns
        -------
        dict
            Dictionary with summary results of the analysis
            
        Notes
        -----
        The analysis pipeline includes:
        1. Loading and cleaning data
        2. Analyzing patient cohort
        3. Analyzing injection intervals
        4. Analyzing VA trajectories
        5. Analyzing treatment courses
        6. Generating plots
        7. Exporting data
        
        The returned summary includes:
        - Patient count
        - Eye count
        - Injection count
        - Course count
        - Mean and median injection intervals
        - Output directory
        - Data quality report
        - Export paths
        """
        # Reduce debug output
        import logging
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        logger.info("Starting Eylea data analysis")
        
        # Load and clean data
        self.load_data()
        
        # Analyze patient cohort
        self.analyze_patient_cohort()
        
        # Analyze injection intervals
        self.analyze_injection_intervals()
        
        # Analyze VA trajectories
        self.analyze_va_trajectories()
        
        # Analyze treatment courses
        self.analyze_treatment_courses()
        
        # Generate plots
        self.plot_injection_intervals()
        self.plot_va_trajectories()
        self.plot_va_change_distribution()
        self.plot_treatment_courses()
        
        # Export interval and VA data
        export_paths = self.export_interval_va_data(format='both')
        
        logger.info("Analysis complete")
        
        # Count unique eyes
        eye_count = len(self.data['eye_key'].unique()) if 'eye_key' in self.data.columns else 0
        
        # Return a summary of the analysis
        return {
            'patient_count': len(self.patient_data) if self.patient_data is not None else 0,
            'eye_count': eye_count,
            'injection_count': len(self.data) if self.data is not None else 0,
            'course_count': len(self.treatment_courses) if self.treatment_courses is not None else 0,
            'mean_injection_interval': self.injection_intervals['interval_days'].mean() if self.injection_intervals is not None and not self.injection_intervals.empty else None,
            'median_injection_interval': self.injection_intervals['interval_days'].median() if self.injection_intervals is not None and not self.injection_intervals.empty else None,
            'output_dir': str(self.output_dir),
            'data_quality_report': self.data_quality_report.get('summary', {}),
            'export_paths': export_paths
        }


def main():
    """
    Main function to run the analysis.
    
    This function parses command-line arguments, creates an EyleaDataAnalyzer instance,
    runs the analysis, and prints summary results.
    
    Returns
    -------
    None
        Prints summary results to stdout
        
    Notes
    -----
    Command-line arguments:
    --data : Path to the data CSV file (default: 'input_data/sample_raw.csv')
    --output : Directory to save output files (default: 'output')
    --debug : Enable debug output
    --validation-strictness : Validation strictness level ('strict', 'moderate', 'lenient')
    
    Example usage:
    python eylea_data_analysis.py --data input_data/my_data.csv --output my_results
    """
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
