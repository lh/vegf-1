"""
Run Eylea Data Analysis

This script runs the analysis on the Eylea treatment data and estimates
parameters for simulation models.
"""

import os
import sys
from pathlib import Path
import logging
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the analyzer and parameter estimator
from analysis.eylea_data_analysis import EyleaDataAnalyzer
from analysis.parameter_estimation import ParameterEstimator
import visualization.treatment_patterns_viz as viz

def main():
    """Main function to run the analysis."""
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Run Eylea data analysis')
    parser.add_argument('--data', type=str, default='input_data/sample_raw.csv',
                        help='Path to the data CSV file')
    parser.add_argument('--output', type=str, default='output',
                        help='Directory to save output files')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug output')
    parser.add_argument('--validation-strictness', type=str, 
                        choices=['strict', 'moderate', 'lenient'], 
                        default='moderate', 
                        help='Validation strictness level')
    
    args = parser.parse_args()
    
    # Set logging level based on debug flag
    if args.debug:
        # Use INFO level instead of DEBUG to reduce output volume
        logging.getLogger().setLevel(logging.INFO)
    
    # Set up output directory
    output_dir = Path(args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    # Create and run the analyzer
    analyzer = EyleaDataAnalyzer(args.data, output_dir)
    analyzer.debug = args.debug
    
    # Run the basic analysis
    logger.info("Running basic analysis...")
    results = analyzer.run_analysis()
    
    # Print data quality summary
    if 'data_quality_report' in results:
        quality = results.get('data_quality_report', {})
        logger.info("\nData Quality Summary:")
        logger.info(f"Total rows: {quality.get('total_rows', 'N/A')}")
        logger.info(f"Missing data: {quality.get('missing_percentage', 'N/A'):.1f}%")
        logger.info(f"Validation warnings: {quality.get('validation_warnings', 'N/A')}")
        logger.info(f"Column mappings applied: {quality.get('mapped_columns', 'N/A')}")
    
    # Save the data for parameter estimation
    logger.info("Saving data for parameter estimation...")
    if analyzer.data is not None:
        analyzer.data.to_csv(output_dir / 'data.csv', index=False)
    if analyzer.patient_data is not None:
        analyzer.patient_data.to_csv(output_dir / 'patient_data.csv', index=False)
    if analyzer.injection_intervals is not None:
        analyzer.injection_intervals.to_csv(output_dir / 'injection_intervals.csv', index=False)
    if analyzer.va_trajectories is not None:
        analyzer.va_trajectories.to_csv(output_dir / 'va_trajectories.csv', index=False)
    
    # Print summary results
    print("\nAnalysis Results Summary:")
    print(f"Patient count: {results['patient_count']}")
    print(f"Injection count: {results['injection_count']}")
    
    if results['mean_injection_interval'] is not None:
        print(f"Mean injection interval: {results['mean_injection_interval']:.1f} days")
    if results['median_injection_interval'] is not None:
        print(f"Median injection interval: {results['median_injection_interval']:.1f} days")
    
    # Run additional visualizations
    logger.info("Creating additional visualizations...")
    
    # Injection frequency heatmap
    if analyzer.data is not None:
        heatmap_path = output_dir / 'injection_frequency_heatmap.png'
        viz.plot_injection_frequency_heatmap(analyzer.data, heatmap_path)
    
    # Treatment duration waterfall
    if analyzer.patient_data is not None:
        waterfall_path = output_dir / 'treatment_duration_waterfall.png'
        viz.plot_treatment_duration_waterfall(analyzer.patient_data, waterfall_path)
    
    # Injection interval by sequence
    if analyzer.injection_intervals is not None:
        interval_seq_path = output_dir / 'injection_interval_by_sequence.png'
        viz.plot_injection_interval_by_sequence(analyzer.injection_intervals, interval_seq_path)
    
    # Treatment persistence
    if analyzer.patient_data is not None:
        persistence_path = output_dir / 'treatment_persistence.png'
        viz.plot_treatment_persistence(analyzer.patient_data, persistence_path)
    
    # VA by injection count
    if analyzer.patient_data is not None and 'va_change' in analyzer.patient_data.columns:
        va_inj_path = output_dir / 'va_by_injection_count.png'
        viz.plot_va_by_injection_count(analyzer.patient_data, va_inj_path)
    
    # Run parameter estimation
    logger.info("Running parameter estimation...")
    params_dir = output_dir / 'parameters'
    os.makedirs(params_dir, exist_ok=True)
    
    # Create parameter estimator
    estimator = ParameterEstimator(
        data=analyzer.data,
        patient_data=analyzer.patient_data,
        injection_intervals=analyzer.injection_intervals,
        va_trajectories=analyzer.va_trajectories
    )
    
    # Estimate parameters
    params = estimator.estimate_all_parameters()
    
    # Save parameters
    params_path = params_dir / 'eylea_parameters.json'
    estimator.save_parameters(params_path)
    
    # Generate parameter report
    report_path = params_dir / 'parameter_report.md'
    report = estimator.generate_parameter_report(report_path)
    
    logger.info(f"Analysis and parameter estimation complete. Results saved to {output_dir}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
