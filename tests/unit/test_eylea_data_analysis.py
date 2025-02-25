"""
Unit tests for the enhanced Eylea data analysis module.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from analysis.eylea_data_analysis import EyleaDataAnalyzer

class TestEyleaDataAnalyzer(unittest.TestCase):
    """Test cases for the EyleaDataAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for output
        self.temp_dir = tempfile.mkdtemp()
        
        # Create an enhanced test dataset with more data points for better visualization
        self.test_data = pd.DataFrame({
            'UUID': ['P001']*6 + ['P002']*4,
            'Injection Date': [
                '2023-01-01', '2023-02-01', '2023-03-01', 
                '2023-04-01', '2023-05-01', '2023-06-01',
                '2023-01-15', '2023-03-15', '2023-05-15', '2023-07-15'
            ],
            'VA Letter Score at Injection': [60, 65, 70, 75, 80, 85, 50, 55, 60, 65],
            'Baseline VA': [60, 60, 60, 60, 60, 60, 50, 50, 50, 50],
            'Current Age': [75, 75, 75, 75, 75, 75, 80, 80, 80, 80],
            'Gender': ['Female', 'Female', 'Female', 'Female', 'Female', 'Female', 
                      'Male', 'Male', 'Male', 'Male'],
            'Eye': ['Right Eye', 'Right Eye', 'Right Eye', 'Right Eye', 'Right Eye', 'Right Eye',
                   'Left Eye', 'Left Eye', 'Left Eye', 'Left Eye']
        })
        
        # Save test data to a temporary CSV file
        self.test_csv_path = os.path.join(self.temp_dir, 'test_data.csv')
        self.test_data.to_csv(self.test_csv_path, index=False)
        
        # Create analyzer instance
        self.analyzer = EyleaDataAnalyzer(self.test_csv_path, self.temp_dir)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_column_mapping(self):
        """Test column name mapping functionality."""
        # Load data
        self.analyzer.load_data()
        
        # Check that column mapping worked
        self.assertIn('Baseline VA Letter Score', self.analyzer.data.columns)
        self.assertEqual(self.analyzer.column_mapping_used['Baseline VA Letter Score'], 'Baseline VA')
    
    def test_data_validation(self):
        """Test data validation functionality."""
        # Load data
        self.analyzer.load_data()
        
        # Check that validation report was generated
        self.assertIn('validation_warnings', self.analyzer.data_quality_report)
        
        # Check that data quality report file was created
        report_path = os.path.join(self.temp_dir, 'data_quality_report.txt')
        self.assertTrue(os.path.exists(report_path))
    
    def test_missing_value_handling(self):
        """Test handling of missing values."""
        # Create data with missing values
        test_data_missing = self.test_data.copy()
        test_data_missing.loc[0, 'Baseline VA'] = np.nan
        
        # Save to CSV
        missing_csv_path = os.path.join(self.temp_dir, 'test_missing.csv')
        test_data_missing.to_csv(missing_csv_path, index=False)
        
        # Create analyzer and load data
        analyzer_missing = EyleaDataAnalyzer(missing_csv_path, self.temp_dir)
        analyzer_missing.load_data()
        
        # Check that missing baseline VA was handled
        self.assertFalse(analyzer_missing.data['Baseline VA Letter Score'].isna().any())
    
    def test_temporal_anomaly_handling(self):
        """Test handling of temporal anomalies."""
        # Create data with out-of-sequence dates
        test_data_anomaly = self.test_data.copy()
        test_data_anomaly['Injection Date'] = [
            '2023-03-01', '2023-01-01', '2023-02-01', '2023-06-01', '2023-04-01', '2023-05-01',
            '2023-03-15', '2023-01-15', '2023-07-15', '2023-05-15'
        ]
        
        # Save to CSV
        anomaly_csv_path = os.path.join(self.temp_dir, 'test_anomaly.csv')
        test_data_anomaly.to_csv(anomaly_csv_path, index=False)
        
        # Create analyzer and load data
        analyzer_anomaly = EyleaDataAnalyzer(anomaly_csv_path, self.temp_dir)
        analyzer_anomaly.load_data()
        
        # Check that sequence errors were detected and fixed
        self.assertGreater(analyzer_anomaly.data_quality_report.get('sequence_fixes', 0), 0)
    
    def test_va_cleaning(self):
        """Test cleaning of VA measurements."""
        # Create data with VA outliers
        test_data_outliers = self.test_data.copy()
        test_data_outliers.loc[0, 'VA Letter Score at Injection'] = 120  # Above max
        test_data_outliers.loc[1, 'VA Letter Score at Injection'] = -10  # Below min
        
        # Save to CSV
        outliers_csv_path = os.path.join(self.temp_dir, 'test_outliers.csv')
        test_data_outliers.to_csv(outliers_csv_path, index=False)
        
        # Create analyzer and load data
        analyzer_outliers = EyleaDataAnalyzer(outliers_csv_path, self.temp_dir)
        analyzer_outliers.load_data()
        
        # Check that VA values were clipped to valid range
        self.assertLessEqual(analyzer_outliers.data['VA Letter Score at Injection'].max(), 100)
        self.assertGreaterEqual(analyzer_outliers.data['VA Letter Score at Injection'].min(), 0)
    
    def test_deceased_status_validation(self):
        """Test validation of deceased status and related age fields."""
        # Create data with deceased patients
        test_data_deceased = self.test_data.copy()
        test_data_deceased['Deceased'] = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]
        test_data_deceased['Age at Death'] = [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 82, 82]
        
        # Save to CSV
        deceased_csv_path = os.path.join(self.temp_dir, 'test_deceased.csv')
        test_data_deceased.to_csv(deceased_csv_path, index=False)
        
        # Create analyzer and load data
        analyzer_deceased = EyleaDataAnalyzer(deceased_csv_path, self.temp_dir)
        analyzer_deceased.load_data()
        
        # Check that Current Age is removed for deceased patients
        deceased_rows = analyzer_deceased.data['Deceased'] == 1
        self.assertTrue(analyzer_deceased.data.loc[deceased_rows, 'Current Age'].isna().all())
        
        # Check that Age at Death is preserved for deceased patients
        self.assertFalse(analyzer_deceased.data.loc[deceased_rows, 'Age at Death'].isna().any())
    
    def test_invalid_deceased_status(self):
        """Test validation warnings for invalid deceased status data."""
        # Create data with inconsistent deceased status
        test_data_invalid = self.test_data.copy()
        test_data_invalid['Deceased'] = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]
        # Missing Age at Death for deceased patient
        test_data_invalid['Age at Death'] = [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 82]
        
        # Save to CSV
        invalid_csv_path = os.path.join(self.temp_dir, 'test_invalid_deceased.csv')
        test_data_invalid.to_csv(invalid_csv_path, index=False)
        
        # Create analyzer and load data
        analyzer_invalid = EyleaDataAnalyzer(invalid_csv_path, self.temp_dir)
        analyzer_invalid.load_data()
        
        # Check that validation warning was generated
        warnings = analyzer_invalid.data_quality_report['validation_warnings']
        self.assertTrue(any('deceased patients are missing Age at Death' in warning for warning in warnings))
    
    def test_age_adjustment(self):
        """Test age adjustment functionality."""
        # Load data
        self.analyzer.load_data()
        
        # Check that Adjusted Age column was created
        self.assertIn('Adjusted Age', self.analyzer.data.columns)
        
        # Check that adjustment was applied correctly (+0.5 years)
        for i, row in self.analyzer.data.iterrows():
            if pd.notna(row['Current Age']):
                self.assertEqual(row['Adjusted Age'], row['Current Age'] + 0.5)
        
        # Check that age adjustment was recorded in data quality report
        self.assertIn('age_adjustments', self.analyzer.data_quality_report)
        self.assertEqual(self.analyzer.data_quality_report['age_adjustments']['adjustment_factor'], 0.5)
    
    def test_birth_date_estimation(self):
        """Test birth date estimation from adjusted age and injection date."""
        # Load data
        self.analyzer.load_data()
        
        # Check that Estimated Birth Date column was created
        self.assertIn('Estimated Birth Date', self.analyzer.data.columns)
        
        # Check that birth date estimation is correct
        for i, row in self.analyzer.data.iterrows():
            if pd.notna(row['Adjusted Age']) and pd.notna(row['Injection Date']):
                injection_date = pd.to_datetime(row['Injection Date'])
                expected_birth_date = injection_date - pd.Timedelta(days=int(row['Adjusted Age'] * 365.25))
                # Allow for small rounding differences
                diff = abs((row['Estimated Birth Date'] - expected_birth_date).total_seconds())
                self.assertLess(diff, 86400)  # Less than 1 day difference
    
    def test_patient_cohort_analysis_with_age_data(self):
        """Test patient cohort analysis with age data."""
        # Create data with deceased patients - make sure P002 is deceased
        test_data_cohort = self.test_data.copy()
        # Set all P002 rows to deceased=1 (last 4 rows)
        test_data_cohort['Deceased'] = [0, 0, 0, 0, 0, 0, 1, 1, 1, 1]
        test_data_cohort['Age at Death'] = [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 82, 82, 82, 82]
        
        # Save to CSV
        cohort_csv_path = os.path.join(self.temp_dir, 'test_cohort.csv')
        test_data_cohort.to_csv(cohort_csv_path, index=False)
        
        # Create analyzer and run analysis
        analyzer_cohort = EyleaDataAnalyzer(cohort_csv_path, self.temp_dir)
        analyzer_cohort.load_data()
        patient_data = analyzer_cohort.analyze_patient_cohort()
        
        # Check that patient data includes both age fields
        self.assertIn('adjusted_age', patient_data.columns)
        self.assertIn('age_at_death', patient_data.columns)
        
        # Check that deceased patients have age_at_death
        deceased_patients = patient_data['deceased'] == 1
        self.assertFalse(patient_data.loc[deceased_patients, 'age_at_death'].isna().any())
        
        # Verify we have the expected number of patients
        self.assertEqual(len(patient_data), 2)  # Should have 2 patients (P001 and P002)
        
        # Verify one patient is deceased and one is not
        self.assertEqual(patient_data['deceased'].sum(), 1)  # One deceased patient
    
    def test_run_analysis(self):
        """Test the complete analysis pipeline."""
        # Run analysis
        results = self.analyzer.run_analysis()
        
        # Check that analysis completed successfully
        self.assertEqual(results['patient_count'], 2)
        self.assertEqual(results['injection_count'], 10)
        
        # Check that output files were created
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'injection_intervals.png')))
        
        # Now we should check for va_trajectories.png since we've fixed the attribute access issues
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'va_trajectories.png')))
        
        # Check for other output files
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'injection_intervals_by_sequence.png')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'va_by_injection_number.png')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'va_change_distribution.png')))


if __name__ == '__main__':
    unittest.main()
