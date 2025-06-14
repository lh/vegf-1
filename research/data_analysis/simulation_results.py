"""Analyze and visualize simulation results with statistical methods.

This module provides tools for analyzing and visualizing the results of clinical
simulations, with a focus on visual acuity outcomes and treatment patterns.

Key Changes:
- Renamed local 'stats' dictionary to 'summary_data' to avoid naming conflict
- Explicitly use scipy.stats module for statistical functions
- Added proper handling for confidence interval calculations with small sample sizes

Classes
-------
SimulationResults
    Main class containing simulation data and analysis methods

Key Functionality
----------------
- Time-series analysis of visual acuity outcomes
- Statistical comparison between patient groups
- Survival analysis for treatment response
- Regression modeling of outcome predictors
- Comprehensive summary statistics

Examples
--------
>>> results = SimulationResults(start_date, end_date, patient_histories)
>>> stats = results.get_summary_statistics()
>>> times, means, ci_lower, ci_upper = results.calculate_mean_vision_over_time()
>>> results.plot_mean_vision()

Notes
-----
- All visual acuity values should be in ETDRS letters
- Time values are in weeks from simulation start
- Statistical tests include t-tests, chi-square, and linear regression
- Confidence intervals are calculated at 95% level
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from scipy import stats
from scipy.stats import ttest_ind, chi2_contingency
from sklearn.linear_model import LinearRegression

@dataclass
class SimulationResults:
    start_date: datetime
    end_date: datetime
    patient_histories: Dict[str, List[Dict]]
    
    def calculate_mean_vision_over_time(self, window_weeks: int = 4) -> tuple:
        """Calculate mean vision over time with confidence intervals
        
        Uses relative time from each patient's first visit to align treatment journeys.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Create relative time bins (weeks from first visit)
        max_weeks = 52  # One year of follow-up
        week_points = list(range(max_weeks + 1))
        
        # Collect vision values for each week since first visit
        vision_values = {w: [] for w in week_points}
        
        # Track how many patients have valid data
        patients_with_data = 0
        
        for patient_id, history in self.patient_histories.items():
            if not history:
                logger.debug(f"Patient {patient_id} has no history")
                continue
                
            # Check if history has the expected structure
            if not isinstance(history[0], dict):
                logger.warning(f"Patient {patient_id} has invalid history format: {type(history[0])}")
                continue
                
            # Get first visit date - ensure it has a date field
            if 'date' not in history[0]:
                logger.warning(f"Patient {patient_id} first visit missing date field")
                continue
                
            first_visit = history[0]['date']
            has_vision_data = False
            
            # Record vision at each visit relative to first visit
            for visit in history:
                if 'vision' in visit and 'date' in visit:
                    has_vision_data = True
                    # Calculate weeks since start, handling different date formats
                    if isinstance(visit['date'], datetime) and isinstance(first_visit, datetime):
                        weeks_since_start = (visit['date'] - first_visit).days // 7
                    else:
                        # Try to parse string dates if needed
                        logger.warning(f"Date format issue: {type(visit['date'])} vs {type(first_visit)}")
                        continue
                        
                    if weeks_since_start <= max_weeks:  # Only include up to max_weeks
                        vision_values[weeks_since_start].append(visit['vision'])
            
            if has_vision_data:
                patients_with_data += 1
        
        logger.debug(f"Found {patients_with_data} patients with valid vision data")
        
        # Calculate statistics for each week
        means = []
        ci_lower = []
        ci_upper = []
        valid_weeks = []
        
        for week in week_points:
            if vision_values[week]:  # If we have data for this week
                values = vision_values[week]
                mean = np.mean(values)
                std = np.std(values)
                # Avoid division by zero for small samples
                if len(values) > 1:
                    ci = 1.96 * std / np.sqrt(len(values))  # 95% confidence interval
                else:
                    ci = 0  # No confidence interval for single data point
                
                means.append(mean)
                ci_lower.append(mean - ci)
                ci_upper.append(mean + ci)
                valid_weeks.append(week)
        
        logger.debug(f"Generated {len(valid_weeks)} valid data points for plotting")
        
        # If we have no valid data, create a dummy point to avoid empty plots
        if not valid_weeks:
            logger.warning("No valid vision data found for plotting")
            # Create a single dummy point at week 0 with baseline vision
            valid_weeks = [0]
            means = [70]  # Default baseline vision
            ci_lower = [70]
            ci_upper = [70]
        
        return valid_weeks, means, ci_lower, ci_upper
    
    def plot_mean_vision(self, title: str = "Mean Visual Acuity Over Time"):
        """Plot mean vision with confidence intervals"""
        weeks, means, ci_lower, ci_upper = self.calculate_mean_vision_over_time()

        # Use logging instead of print statements
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Plotting data points: {len(weeks)}")
        if means:
            logger.debug(f"Mean values range: {min(means)} to {max(means)}")
        logger.debug(f"Number of patients with data: {len(self.patient_histories)}")
        
        if not weeks or not means:
            logger.warning("No data points to plot!")
            return None

        fig = plt.figure(figsize=(12, 6))
        plt.plot(weeks, means, 'b-', label='Mean Vision')
        plt.fill_between(weeks, ci_lower, ci_upper, color='b', alpha=0.2,
                        label='95% Confidence Interval')

        plt.title(title)
        plt.xlabel('Weeks from First Visit')
        plt.ylabel('Visual Acuity (ETDRS letters)')
        plt.ylim(0, 85)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        return fig

    def get_mean_vision_over_time(self) -> List[float]:
        """Get mean vision over time for comparison visualization"""
        _, means, _, _ = self.calculate_mean_vision_over_time()
        return means
    
    def get_summary_statistics(self) -> Dict:
        """Calculate comprehensive summary statistics for the simulation
        
        Returns:
            Dictionary containing:
            - num_patients: Total number of patients
            - mean_visits_per_patient: Average visits per patient
            - mean_injections_per_patient: Average injections per patient
            - mean_vision_change: Mean change in visual acuity (ETDRS letters)
            - vision_improved_percent: % patients with >5 letter improvement
            - vision_stable_percent: % patients with -5 to +5 letter change
            - vision_declined_percent: % patients with >5 letter decline
            - vision_baseline_mean: Mean baseline visual acuity
            - vision_baseline_std: Std dev of baseline visual acuity
            - vision_final_mean: Mean final visual acuity
            - vision_final_std: Std dev of final visual acuity
            - treatment_interval_mean: Mean interval between treatments (weeks)
            - treatment_interval_std: Std dev of treatment intervals
            - loading_phase_completion_rate: % completing loading phase (3+ injections)
            - time_to_first_improvement: Median weeks to first >5 letter improvement
            - vision_change_confidence_interval: 95% CI for mean vision change

        Notes:
            - Uses scipy.stats for all statistical calculations
            - Handles edge cases for small sample sizes
            - Returns None for confidence intervals when insufficient data exists
        """
        summary_data = {
            "num_patients": len(self.patient_histories),
            "mean_visits_per_patient": 0,
            "mean_injections_per_patient": 0,
            "mean_vision_change": 0,
            "vision_improved_percent": 0,
            "vision_stable_percent": 0,
            "vision_declined_percent": 0,
            "vision_baseline_mean": 0,
            "vision_baseline_std": 0,
            "vision_final_mean": 0,
            "vision_final_std": 0,
            "treatment_interval_mean": 0,
            "treatment_interval_std": 0,
            "loading_phase_completion_rate": 0,
            "time_to_first_improvement": None,
            "vision_change_confidence_interval": (0, 0)
        }
        
        vision_changes = []
        baseline_visions = []
        final_visions = []
        treatment_intervals = []
        improvement_times = []
        loading_phase_completed = 0
        
        for history in self.patient_histories.values():
            if not history:
                continue
                
            # Count visits and injections
            summary_data["mean_visits_per_patient"] += len(history)
            injections = sum(1 for v in history if 'injection' in v.get('actions', []))
            summary_data["mean_injections_per_patient"] += injections
            
            # Track loading phase completion (3+ injections)
            if injections >= 3:
                loading_phase_completed += 1
                
            # Get injection dates for interval calculation
            injection_dates = [v['date'] for v in history 
                             if 'injection' in v.get('actions', []) and 'date' in v]
            
            # Calculate treatment intervals
            for i in range(1, len(injection_dates)):
                interval = (injection_dates[i] - injection_dates[i-1]).days / 7
                treatment_intervals.append(interval)
                
            # Get vision data
            first_vision = next((v['vision'] for v in history if 'vision' in v), None)
            last_vision = next((v['vision'] for v in reversed(history) if 'vision' in v), None)
            
            if first_vision is not None:
                baseline_visions.append(first_vision)
            if last_vision is not None:
                final_visions.append(last_vision)
                
            if first_vision is not None and last_vision is not None:
                change = last_vision - first_vision
                vision_changes.append(change)
                
                # Track time to first improvement
                for visit in history:
                    if 'vision' in visit and 'date' in visit:
                        weeks = (visit['date'] - history[0]['date']).days / 7
                        if visit['vision'] - first_vision > 5:
                            improvement_times.append(weeks)
                            break
        
        # Calculate means and standard deviations
        summary_data["mean_visits_per_patient"] /= summary_data["num_patients"]
        summary_data["mean_injections_per_patient"] /= summary_data["num_patients"]
        summary_data["loading_phase_completion_rate"] = (loading_phase_completed / summary_data["num_patients"]) * 100
        
        if vision_changes:
            summary_data["mean_vision_change"] = np.mean(vision_changes)
            total = len(vision_changes)
            summary_data["vision_improved_percent"] = sum(1 for c in vision_changes if c > 5) / total * 100
            summary_data["vision_stable_percent"] = sum(1 for c in vision_changes if -5 <= c <= 5) / total * 100
            summary_data["vision_declined_percent"] = sum(1 for c in vision_changes if c < -5) / total * 100
            
            # Calculate confidence interval for mean vision change
            if len(vision_changes) > 1:
                sem = stats.sem(vision_changes)
                ci = stats.t.interval(0.95, len(vision_changes)-1, 
                                    loc=np.mean(vision_changes), 
                                    scale=sem)
                summary_data["vision_change_confidence_interval"] = (ci[0], ci[1])
            else:
                # With one or zero samples, we can't calculate SEM/CI - use None to indicate missing data
                summary_data["vision_change_confidence_interval"] = (None, None)
        
        if baseline_visions:
            summary_data["vision_baseline_mean"] = np.mean(baseline_visions)
            summary_data["vision_baseline_std"] = np.std(baseline_visions)
            
        if final_visions:
            summary_data["vision_final_mean"] = np.mean(final_visions)
            summary_data["vision_final_std"] = np.std(final_visions)
            
        if treatment_intervals:
            summary_data["treatment_interval_mean"] = np.mean(treatment_intervals)
            summary_data["treatment_interval_std"] = np.std(treatment_intervals)
            
        if improvement_times:
            summary_data["time_to_first_improvement"] = np.median(improvement_times)
        
        return summary_data

    def analyze_treatment_response(self, min_followup_weeks: int = 12) -> Dict:
        """Analyze treatment response patterns
        
        Args:
            min_followup_weeks: Minimum weeks of follow-up required
            
        Returns:
            Dictionary containing response analysis results
        """
        results = {
            "early_responders": 0,  # Improvement by week 12
            "late_responders": 0,   # Improvement after week 12
            "non_responders": 0,    # No improvement
            "response_time_mean": 0,
            "response_time_median": 0,
            "response_sustainability": 0  # Percentage maintaining improvement
        }
        
        response_times = []
        
        for history in self.patient_histories.values():
            if not history:
                continue
                
            baseline = next((v['vision'] for v in history if 'vision' in v), None)
            if baseline is None:
                continue
            
            # Track vision changes over time
            max_improvement = 0
            time_to_response = None
            sustained_improvement = False
            
            for visit in history:
                if 'vision' not in visit or 'date' not in visit:
                    continue
                    
                weeks = (visit['date'] - history[0]['date']).days / 7
                change = visit['vision'] - baseline
                
                if change > 5:  # Clinically significant improvement
                    if time_to_response is None:
                        time_to_response = weeks
                        response_times.append(weeks)
                        
                    if weeks <= 12:
                        results["early_responders"] += 1
                        break
                    else:
                        results["late_responders"] += 1
                        break
                        
                max_improvement = max(max_improvement, change)
            
            if time_to_response is None:
                results["non_responders"] += 1
        
        total_patients = len(self.patient_histories)
        if total_patients > 0:
            results["early_responders"] /= total_patients
            results["late_responders"] /= total_patients
            results["non_responders"] /= total_patients
            
        if response_times:
            results["response_time_mean"] = np.mean(response_times)
            results["response_time_median"] = np.median(response_times)
            
        return results

    def time_to_event_analysis(self, event_type: str = 'vision_improvement') -> Dict:
        """Perform time-to-event analysis for specified outcome
        
        Args:
            event_type: Type of event to analyze ('vision_improvement', 
                       'vision_loss', 'treatment_discontinuation')
                       
        Returns:
            Dictionary containing survival analysis results
        """
        results = {
            "median_time": None,
            "event_rate": 0,
            "censored_rate": 0,
            "hazard_ratio": None,
            "survival_times": [],
            "censored": [],
            "event_type": None,  # Record which criterion triggered the event
            "event_details": []  # Track all events for debugging
        }
        
        for history in self.patient_histories.values():
            if not history:
                continue
                
            baseline = next((v['vision'] for v in history if 'vision' in v), None)
            if baseline is None:
                continue
                
            event_occurred = False
            for visit in history:
                if 'vision' not in visit or 'date' not in visit:
                    continue
                    
                weeks = (visit['date'] - history[0]['date']).days / 7
                
                change = visit['vision'] - baseline
                if event_type == 'vision_improvement' and change > 5:
                    results["survival_times"].append(weeks)
                    results["censored"].append(0)  # Event occurred
                    results["event_type"] = "improvement"
                    results["event_details"].append({
                        "type": "improvement",
                        "week": weeks,
                        "change": change
                    })
                    event_occurred = True
                    break
                elif event_type == 'vision_loss' and change <= -5:
                    results["survival_times"].append(weeks)
                    results["censored"].append(0)
                    results["event_type"] = "vision_loss"
                    results["event_details"].append({
                        "type": "vision_loss",
                        "week": weeks,
                        "change": change
                    })
                    event_occurred = True
                    break
                    
            if not event_occurred:
                # Censored observation
                last_week = (history[-1]['date'] - history[0]['date']).days / 7
                results["survival_times"].append(last_week)
                results["censored"].append(1)
        
        if results["survival_times"]:
            event_times = [t for t, c in zip(results["survival_times"], results["censored"]) if c == 0]
            if event_times:
                # Handle single events and multiple events differently
                results["median_time"] = event_times[0] if len(event_times) == 1 else np.median(event_times)
            if len(results["censored"]) > 0:
                results["event_rate"] = 1 - (sum(results["censored"]) / len(results["censored"]))
                results["censored_rate"] = sum(results["censored"]) / len(results["censored"])
            
        return results

    def compare_groups(self, group_a: List[str], group_b: List[str], 
                      metric: str = 'vision_change') -> Dict:
        """Compare outcomes between two patient groups
        
        Args:
            group_a: List of patient IDs for first group
            group_b: List of patient IDs for second group
            metric: Outcome metric to compare
            
        Returns:
            Dictionary containing statistical comparison results
        """
        results = {
            "mean_diff": 0,
            "p_value": None,
            "confidence_interval": (0, 0),
            "effect_size": 0
        }
        
        values_a = []
        values_b = []
        
        for patient_id in group_a:
            history = self.patient_histories.get(patient_id)
            if not history:
                continue
                
            if metric == 'vision_change':
                first = next((v['vision'] for v in history if 'vision' in v), None)
                last = next((v['vision'] for v in reversed(history) if 'vision' in v), None)
                if first is not None and last is not None:
                    values_a.append(last - first)
                    
        for patient_id in group_b:
            history = self.patient_histories.get(patient_id)
            if not history:
                continue
                
            if metric == 'vision_change':
                first = next((v['vision'] for v in history if 'vision' in v), None)
                last = next((v['vision'] for v in reversed(history) if 'vision' in v), None)
                if first is not None and last is not None:
                    values_b.append(last - first)
        
        if values_a and values_b:
            # Perform statistical tests
            t_stat, p_value = ttest_ind(values_a, values_b)
            results["mean_diff"] = np.mean(values_a) - np.mean(values_b)
            results["p_value"] = p_value
            
            # Calculate confidence interval
            se = np.sqrt(np.var(values_a)/len(values_a) + np.var(values_b)/len(values_b))
            ci = stats.t.interval(0.95, len(values_a) + len(values_b) - 2)
            results["confidence_interval"] = (
                results["mean_diff"] + ci[0]*se,
                results["mean_diff"] + ci[1]*se
            )
            
            # Calculate effect size (Cohen's d)
            pooled_std = np.sqrt(((len(values_a) - 1) * np.var(values_a) + 
                                (len(values_b) - 1) * np.var(values_b)) / 
                               (len(values_a) + len(values_b) - 2))
            results["effect_size"] = results["mean_diff"] / pooled_std
            
        return results

    def regression_analysis(self, outcome: str = 'vision_change') -> Dict:
        """Perform regression analysis to identify predictors of outcomes
        
        Args:
            outcome: Outcome variable to analyze
            
        Returns:
            Dictionary containing regression analysis results
        """
        results = {
            "r_squared": 0,
            "coefficients": {},
            "p_values": {},
            "confidence_intervals": {}
        }
        
        X = []  # Predictors
        y = []  # Outcome
        
        for history in self.patient_histories.values():
            if not history:
                continue
                
            # Extract outcome
            if outcome == 'vision_change':
                first = next((v['vision'] for v in history if 'vision' in v), None)
                last = next((v['vision'] for v in reversed(history) if 'vision' in v), None)
                if first is None or last is None:
                    continue
                y.append(last - first)
                
                # Extract predictors
                predictors = []
                predictors.append(first)  # Baseline vision
                predictors.append(len([v for v in history if 'injection' in v.get('actions', [])]))
                predictors.append(len(history))  # Number of visits
                
                X.append(predictors)
        
        if X and y:
            # Fit regression model
            model = LinearRegression()
            model.fit(X, y)
            
            # Calculate statistics
            results["r_squared"] = model.score(X, y)
            
            # Store coefficients and their statistics
            predictor_names = ['baseline_vision', 'num_injections', 'num_visits']
            for name, coef in zip(predictor_names, model.coef_):
                results["coefficients"][name] = coef
                
            # Calculate p-values and confidence intervals
            n = len(y)
            p = len(predictor_names)
            y_pred = model.predict(X)
            mse = np.sum((y - y_pred) ** 2) / (n - p - 1)
            var_b = mse * np.linalg.inv(np.dot(np.array(X).T, np.array(X))).diagonal()
            var_b = np.maximum(var_b, 0)  # Ensure non-negative values
            sd_b = np.sqrt(var_b)
            t = model.coef_ / np.maximum(sd_b, np.finfo(float).eps)  # Avoid division by zero
            
            for name, t_val, sd in zip(predictor_names, t, sd_b):
                results["p_values"][name] = 2 * (1 - stats.t.cdf(np.abs(t_val), n - p - 1))
                ci = stats.t.interval(0.95, n - p - 1)
                results["confidence_intervals"][name] = (
                    results["coefficients"][name] + ci[0]*sd,
                    results["coefficients"][name] + ci[1]*sd
                )
                
        return results
