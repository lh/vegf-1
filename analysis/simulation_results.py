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
        """Calculate mean vision over time with confidence intervals"""
        # Create time bins
        total_weeks = (self.end_date - self.start_date).days // 7
        time_points = [self.start_date + timedelta(weeks=w) for w in range(total_weeks)]
        
        # Collect vision values for each time bin
        vision_values = {t: [] for t in time_points}
        
        for history in self.patient_histories.values():
            for visit in history:
                if 'vision' in visit and 'date' in visit:
                    # Find nearest time point
                    visit_time = visit['date']
                    nearest_point = min(time_points, 
                                     key=lambda t: abs((visit_time - t).total_seconds()))
                    vision_values[nearest_point].append(visit['vision'])
        
        # Calculate statistics
        means = []
        ci_lower = []
        ci_upper = []
        valid_times = []
        
        for t in time_points:
            if vision_values[t]:
                values = vision_values[t]
                mean = np.mean(values)
                std = np.std(values)
                ci = 1.96 * std / np.sqrt(len(values))  # 95% confidence interval
                
                means.append(mean)
                ci_lower.append(mean - ci)
                ci_upper.append(mean + ci)
                valid_times.append(t)
        
        return valid_times, means, ci_lower, ci_upper
    
    def plot_mean_vision(self, title: str = "Mean Visual Acuity Over Time"):
        """Plot mean vision with confidence intervals"""
        times, means, ci_lower, ci_upper = self.calculate_mean_vision_over_time()
        
        plt.figure(figsize=(12, 6))
        plt.plot(times, means, 'b-', label='Mean Vision')
        plt.fill_between(times, ci_lower, ci_upper, color='b', alpha=0.2, 
                        label='95% Confidence Interval')
        
        plt.title(title)
        plt.xlabel('Date')
        plt.ylabel('Visual Acuity (ETDRS letters)')
        plt.ylim(0, 85)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        plt.show()
    
    def get_summary_statistics(self) -> Dict:
        """Calculate comprehensive summary statistics for the simulation"""
        stats = {
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
        
        for history in self.patient_histories.values():
            # Count visits and injections
            stats["mean_visits_per_patient"] += len(history)
            injections = sum(1 for v in history if 'injection' in v.get('actions', []))
            stats["mean_injections_per_patient"] += injections
            
            # Calculate vision change
            first_vision = next((v['vision'] for v in history if 'vision' in v), None)
            last_vision = next((v['vision'] for v in reversed(history) if 'vision' in v), None)
            
            if first_vision is not None and last_vision is not None:
                change = last_vision - first_vision
                vision_changes.append(change)
        
        # Calculate means
        stats["mean_visits_per_patient"] /= stats["num_patients"]
        stats["mean_injections_per_patient"] /= stats["num_patients"]
        
        if vision_changes:
            stats["mean_vision_change"] = np.mean(vision_changes)
            total = len(vision_changes)
            stats["vision_improved_percent"] = sum(1 for c in vision_changes if c > 5) / total * 100
            stats["vision_stable_percent"] = sum(1 for c in vision_changes if -5 <= c <= 5) / total * 100
            stats["vision_declined_percent"] = sum(1 for c in vision_changes if c < -5) / total * 100
        
        return stats

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
