"""
Parameter Estimation for Eylea Simulation

This module estimates parameters for the Eylea simulation model
based on real-world treatment data.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json
from scipy import stats
import logging

logger = logging.getLogger(__name__)


class ParameterEstimator:
    """Estimates parameters for simulation from real-world data."""
    
    def __init__(self, data=None, patient_data=None, injection_intervals=None, va_trajectories=None):
        """
        Initialize the parameter estimator.
        
        Args:
            data: Full DataFrame with all injection data
            patient_data: DataFrame with one row per patient
            injection_intervals: DataFrame with injection intervals
            va_trajectories: DataFrame with VA trajectories
        """
        self.data = data
        self.patient_data = patient_data
        self.injection_intervals = injection_intervals
        self.va_trajectories = va_trajectories
        
        self.parameters = {}
    
    def estimate_injection_interval_parameters(self):
        """Estimate parameters related to injection intervals."""
        logger.info("Estimating injection interval parameters")
        
        if self.injection_intervals is None or self.injection_intervals.empty:
            logger.warning("No injection interval data available")
            return {}
        
        # Calculate basic statistics
        interval_params = {
            'mean_interval_days': float(self.injection_intervals['interval_days'].mean()),
            'median_interval_days': float(self.injection_intervals['interval_days'].median()),
            'std_interval_days': float(self.injection_intervals['interval_days'].std()),
            'min_interval_days': float(self.injection_intervals['interval_days'].min()),
            'max_interval_days': float(self.injection_intervals['interval_days'].max()),
        }
        
        # Fit distributions to the data
        try:
            # Try fitting a gamma distribution
            gamma_params = stats.gamma.fit(self.injection_intervals['interval_days'])
            interval_params['gamma_shape'] = float(gamma_params[0])
            interval_params['gamma_loc'] = float(gamma_params[1])
            interval_params['gamma_scale'] = float(gamma_params[2])
            
            # Try fitting a lognormal distribution
            lognorm_params = stats.lognorm.fit(self.injection_intervals['interval_days'])
            interval_params['lognorm_shape'] = float(lognorm_params[0])
            interval_params['lognorm_loc'] = float(lognorm_params[1])
            interval_params['lognorm_scale'] = float(lognorm_params[2])
            
            logger.debug("Successfully fit distributions to injection intervals")
        except Exception as e:
            logger.warning(f"Error fitting distributions to injection intervals: {e}")
        
        # Calculate frequency of common intervals
        interval_counts = self.injection_intervals['interval_days'].value_counts()
        total_intervals = len(self.injection_intervals)
        
        # Monthly (28 ± 7 days)
        monthly_count = interval_counts[(interval_counts.index >= 21) & (interval_counts.index <= 35)].sum()
        interval_params['monthly_frequency'] = float(monthly_count / total_intervals if total_intervals > 0 else 0)
        
        # Bimonthly (56 ± 7 days)
        bimonthly_count = interval_counts[(interval_counts.index >= 49) & (interval_counts.index <= 63)].sum()
        interval_params['bimonthly_frequency'] = float(bimonthly_count / total_intervals if total_intervals > 0 else 0)
        
        # Quarterly (84 ± 7 days)
        quarterly_count = interval_counts[(interval_counts.index >= 77) & (interval_counts.index <= 91)].sum()
        interval_params['quarterly_frequency'] = float(quarterly_count / total_intervals if total_intervals > 0 else 0)
        
        # Store the parameters
        self.parameters['injection_intervals'] = interval_params
        
        return interval_params
    
    def estimate_va_response_parameters(self):
        """Estimate parameters related to visual acuity response."""
        logger.info("Estimating VA response parameters")
        
        if self.va_trajectories is None or self.va_trajectories.empty:
            logger.warning("No VA trajectory data available")
            return {}
        
        va_params = {}
        
        # Calculate VA change from baseline at different timepoints
        try:
            # Group by days from first injection
            grouped = self.va_trajectories.groupby('days_from_first')
            
            # Calculate statistics for each timepoint
            timepoints = {}
            
            # Define timepoints of interest (days)
            for days in [30, 60, 90, 180, 365]:
                # Find the closest available timepoint
                closest_days = min(grouped.groups.keys(), key=lambda x: abs(x - days))
                
                if abs(closest_days - days) <= 30:  # Within 30 days of target
                    timepoint_data = grouped.get_group(closest_days)
                    
                    timepoints[f'day_{days}'] = {
                        'actual_day': float(closest_days),
                        'n': int(len(timepoint_data)),
                        'mean_va': float(timepoint_data['va_score'].mean()),
                        'mean_va_change': float(timepoint_data['va_change'].mean()),
                        'std_va_change': float(timepoint_data['va_change'].std()),
                        'median_va_change': float(timepoint_data['va_change'].median()),
                        'pct_improved_5plus': float((timepoint_data['va_change'] >= 5).mean()),
                        'pct_improved_15plus': float((timepoint_data['va_change'] >= 15).mean()),
                        'pct_worsened_5plus': float((timepoint_data['va_change'] <= -5).mean()),
                        'pct_worsened_15plus': float((timepoint_data['va_change'] <= -15).mean()),
                    }
            
            va_params['timepoints'] = timepoints
            logger.debug(f"Calculated VA parameters at {len(timepoints)} timepoints")
            
        except Exception as e:
            logger.warning(f"Error calculating VA timepoint parameters: {e}")
        
        # Classify patients as responders/non-responders
        try:
            # Get the last VA measurement for each patient
            last_measurements = self.va_trajectories.loc[
                self.va_trajectories.groupby('patient_id')['injection_number'].idxmax()
            ]
            
            # Define responders as those with ≥5 letter gain at last measurement
            responders = last_measurements[last_measurements['va_change'] >= 5]
            non_responders = last_measurements[last_measurements['va_change'] < 5]
            
            va_params['responder_rate'] = float(len(responders) / len(last_measurements) if len(last_measurements) > 0 else 0)
            
            # Calculate parameters for responders and non-responders
            if len(responders) > 0:
                va_params['responders'] = {
                    'n': int(len(responders)),
                    'mean_va_change': float(responders['va_change'].mean()),
                    'std_va_change': float(responders['va_change'].std()),
                    'mean_injections': float(responders['injection_number'].mean() + 1),  # Add 1 because injection_number is 0-indexed
                }
            
            if len(non_responders) > 0:
                va_params['non_responders'] = {
                    'n': int(len(non_responders)),
                    'mean_va_change': float(non_responders['va_change'].mean()),
                    'std_va_change': float(non_responders['va_change'].std()),
                    'mean_injections': float(non_responders['injection_number'].mean() + 1),  # Add 1 because injection_number is 0-indexed
                }
            
            logger.debug(f"Classified patients into {len(responders)} responders and {len(non_responders)} non-responders")
            
        except Exception as e:
            logger.warning(f"Error classifying responders/non-responders: {e}")
        
        # Store the parameters
        self.parameters['va_response'] = va_params
        
        return va_params
    
    def estimate_treatment_duration_parameters(self):
        """Estimate parameters related to treatment duration."""
        logger.info("Estimating treatment duration parameters")
        
        if self.patient_data is None or self.patient_data.empty:
            logger.warning("No patient data available")
            return {}
        
        duration_params = {}
        
        # Calculate basic statistics
        if 'treatment_duration_days' in self.patient_data.columns:
            duration_data = self.patient_data['treatment_duration_days'].dropna()
            
            duration_params.update({
                'mean_duration_days': float(duration_data.mean()),
                'median_duration_days': float(duration_data.median()),
                'std_duration_days': float(duration_data.std()),
                'min_duration_days': float(duration_data.min()),
                'max_duration_days': float(duration_data.max()),
            })
            
            # Calculate percentiles
            for p in [25, 50, 75, 90]:
                duration_params[f'p{p}_duration_days'] = float(np.percentile(duration_data, p))
            
            # Calculate proportion of patients with treatment duration > X years
            for years in [1, 2, 3]:
                days = years * 365
                prop = (duration_data > days).mean()
                duration_params[f'prop_gt_{years}yr'] = float(prop)
            
            logger.debug(f"Calculated treatment duration parameters from {len(duration_data)} patients")
        else:
            logger.warning("No 'treatment_duration_days' column found in patient_data")
        
        # Calculate injection frequency (injections per year)
        if 'injection_count' in self.patient_data.columns and 'treatment_duration_days' in self.patient_data.columns:
            # Filter to patients with duration > 0
            valid_data = self.patient_data[self.patient_data['treatment_duration_days'] > 0].copy()
            
            if len(valid_data) > 0:
                # Calculate injections per year
                valid_data['injections_per_year'] = valid_data['injection_count'] / (valid_data['treatment_duration_days'] / 365)
                
                duration_params.update({
                    'mean_injections_per_year': float(valid_data['injections_per_year'].mean()),
                    'median_injections_per_year': float(valid_data['injections_per_year'].median()),
                    'std_injections_per_year': float(valid_data['injections_per_year'].std()),
                })
                
                logger.debug(f"Calculated injection frequency parameters from {len(valid_data)} patients")
        
        # Store the parameters
        self.parameters['treatment_duration'] = duration_params
        
        return duration_params
    
    def estimate_all_parameters(self):
        """Estimate all parameters."""
        logger.info("Estimating all parameters")
        
        # Estimate injection interval parameters
        self.estimate_injection_interval_parameters()
        
        # Estimate VA response parameters
        self.estimate_va_response_parameters()
        
        # Estimate treatment duration parameters
        self.estimate_treatment_duration_parameters()
        
        return self.parameters
    
    def save_parameters(self, output_path):
        """
        Save parameters to a JSON file.
        
        Args:
            output_path: Path to save the parameters
        """
        logger.info(f"Saving parameters to {output_path}")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert numpy types to Python types for JSON serialization
        def convert_to_serializable(obj):
            if isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(i) for i in obj]
            else:
                return obj
        
        serializable_params = convert_to_serializable(self.parameters)
        
        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(serializable_params, f, indent=2)
        
        logger.info(f"Parameters saved to {output_path}")
    
    def generate_parameter_report(self, output_path=None):
        """
        Generate a report of the estimated parameters.
        
        Args:
            output_path: Path to save the report (optional)
        
        Returns:
            str: The report text
        """
        logger.info("Generating parameter report")
        
        # Ensure parameters have been estimated
        if not self.parameters:
            self.estimate_all_parameters()
        
        # Generate the report
        report = []
        report.append("# Eylea Treatment Parameter Estimation Report")
        report.append("")
        
        # Injection intervals
        if 'injection_intervals' in self.parameters:
            report.append("## Injection Interval Parameters")
            report.append("")
            params = self.parameters['injection_intervals']
            report.append(f"- Mean interval: {params.get('mean_interval_days', 'N/A'):.1f} days")
            report.append(f"- Median interval: {params.get('median_interval_days', 'N/A'):.1f} days")
            report.append(f"- Standard deviation: {params.get('std_interval_days', 'N/A'):.1f} days")
            report.append("")
            report.append("### Interval Frequencies")
            report.append(f"- Monthly (28±7 days): {params.get('monthly_frequency', 'N/A'):.1%}")
            report.append(f"- Bimonthly (56±7 days): {params.get('bimonthly_frequency', 'N/A'):.1%}")
            report.append(f"- Quarterly (84±7 days): {params.get('quarterly_frequency', 'N/A'):.1%}")
            report.append("")
        
        # VA response
        if 'va_response' in self.parameters:
            report.append("## Visual Acuity Response Parameters")
            report.append("")
            params = self.parameters['va_response']
            
            if 'responder_rate' in params:
                report.append(f"- Responder rate (≥5 letter gain): {params.get('responder_rate', 'N/A'):.1%}")
                report.append("")
            
            if 'timepoints' in params:
                report.append("### VA Change by Timepoint")
                report.append("")
                report.append("| Timepoint | N | Mean VA Change | % ≥5 Letters | % ≥15 Letters |")
                report.append("|-----------|---|---------------|--------------|---------------|")
                
                for timepoint, tp_params in params['timepoints'].items():
                    report.append(f"| {timepoint} | {tp_params.get('n', 'N/A')} | {tp_params.get('mean_va_change', 'N/A'):.1f} | {tp_params.get('pct_improved_5plus', 'N/A'):.1%} | {tp_params.get('pct_improved_15plus', 'N/A'):.1%} |")
                
                report.append("")
            
            if 'responders' in params and 'non_responders' in params:
                report.append("### Responder vs Non-Responder Characteristics")
                report.append("")
                report.append("| Group | N | Mean VA Change | Mean Injections |")
                report.append("|-------|---|---------------|-----------------|")
                
                resp = params['responders']
                non_resp = params['non_responders']
                
                report.append(f"| Responders | {resp.get('n', 'N/A')} | {resp.get('mean_va_change', 'N/A'):.1f} | {resp.get('mean_injections', 'N/A'):.1f} |")
                report.append(f"| Non-Responders | {non_resp.get('n', 'N/A')} | {non_resp.get('mean_va_change', 'N/A'):.1f} | {non_resp.get('mean_injections', 'N/A'):.1f} |")
                
                report.append("")
        
        # Treatment duration
        if 'treatment_duration' in self.parameters:
            report.append("## Treatment Duration Parameters")
            report.append("")
            params = self.parameters['treatment_duration']
            
            report.append(f"- Mean duration: {params.get('mean_duration_days', 'N/A'):.1f} days ({params.get('mean_duration_days', 0)/365:.1f} years)")
            report.append(f"- Median duration: {params.get('median_duration_days', 'N/A'):.1f} days ({params.get('median_duration_days', 0)/365:.1f} years)")
            report.append("")
            
            if 'mean_injections_per_year' in params:
                report.append(f"- Mean injections per year: {params.get('mean_injections_per_year', 'N/A'):.1f}")
                report.append(f"- Median injections per year: {params.get('median_injections_per_year', 'N/A'):.1f}")
                report.append("")
            
            report.append("### Treatment Persistence")
            report.append("")
            for years in [1, 2, 3]:
                key = f'prop_gt_{years}yr'
                if key in params:
                    report.append(f"- Proportion still in treatment after {years} year(s): {params.get(key, 'N/A'):.1%}")
            
            report.append("")
        
        # Join the report lines
        report_text = "\n".join(report)
        
        # Save the report if output_path is provided
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report_text)
            logger.info(f"Parameter report saved to {output_path}")
        
        return report_text


def main():
    """Main function to run parameter estimation."""
    import argparse
    
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Estimate parameters for Eylea simulation')
    parser.add_argument('--analyzer-output', type=str, required=True,
                        help='Path to the analyzer output directory')
    parser.add_argument('--output', type=str, default='output/parameters',
                        help='Directory to save parameter outputs')
    
    args = parser.parse_args()
    
    # Set up output directory
    output_dir = Path(args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    # Load analyzer data
    analyzer_dir = Path(args.analyzer_output)
    
    data = None
    patient_data = None
    injection_intervals = None
    va_trajectories = None
    
    try:
        # Try to load the data files
        data_path = analyzer_dir / 'data.csv'
        if data_path.exists():
            data = pd.read_csv(data_path)
            logger.info(f"Loaded data from {data_path}")
        
        patient_data_path = analyzer_dir / 'patient_data.csv'
        if patient_data_path.exists():
            patient_data = pd.read_csv(patient_data_path)
            logger.info(f"Loaded patient data from {patient_data_path}")
        
        intervals_path = analyzer_dir / 'injection_intervals.csv'
        if intervals_path.exists():
            injection_intervals = pd.read_csv(intervals_path)
            logger.info(f"Loaded injection intervals from {intervals_path}")
        
        va_path = analyzer_dir / 'va_trajectories.csv'
        if va_path.exists():
            va_trajectories = pd.read_csv(va_path)
            logger.info(f"Loaded VA trajectories from {va_path}")
        
    except Exception as e:
        logger.error(f"Error loading analyzer data: {e}")
        return 1
    
    # Create parameter estimator
    estimator = ParameterEstimator(
        data=data,
        patient_data=patient_data,
        injection_intervals=injection_intervals,
        va_trajectories=va_trajectories
    )
    
    # Estimate parameters
    params = estimator.estimate_all_parameters()
    
    # Save parameters
    params_path = output_dir / 'eylea_parameters.json'
    estimator.save_parameters(params_path)
    
    # Generate parameter report
    report_path = output_dir / 'parameter_report.md'
    estimator.generate_parameter_report(report_path)
    
    logger.info(f"Parameter estimation complete. Results saved to {output_dir}")
    
    return 0


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    sys.exit(main())
