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

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from analysis.eylea_data_analysis import EyleaDataAnalyzer

class TestEyleaDataAnalyzer(unittest.TestCase):
    """Test cases for the EyleaDataAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for output
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a small test dataset
        self.test_data = pd.DataFrame({
            'UUID': ['P001', 'P001', 'P001', 'P002', 'P002'],
            'Injection Date': ['2023-01-01', '2023-02-01', '2023-03-01', '2023-01-15', '2023-03-15'],
            'VA Letter Score at Injection': [60, 65, 70, 50, 55],
            'Baseline VA': [60, 60, 60, 50, 50],
            'Current Age': [75, 75, 75, 80, 80],
            'Gender': ['Female', 'Female', 'Female', 'Male', 'Male'],
            'Eye': ['Right Eye', 'Right Eye', 'Right Eye', 'Left Eye', 'Left Eye']
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
        test_data_anomaly['Injection Date'] = ['2023-03-01', '2023-01-01', '2023-02-01', 
                                              '2023-03-15', '2023-01-15']
        
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
    
    def test_run_analysis(self):
        """Test the complete analysis pipeline."""
        # Run analysis
        results = self.analyzer.run_analysis()
        
        # Check that analysis completed successfully
        self.assertEqual(results['patient_count'], 2)
        self.assertEqual(results['injection_count'], 5)
        
        # Check that output files were created
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'injection_intervals.png')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'va_trajectories.png')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'va_change_distribution.png')))


if __name__ == '__main__':
    unittest.main()
