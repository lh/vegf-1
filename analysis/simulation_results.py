from typing import List, Dict
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass

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
        """Calculate summary statistics for the simulation"""
        stats = {
            "num_patients": len(self.patient_histories),
            "mean_visits_per_patient": 0,
            "mean_injections_per_patient": 0,
            "mean_vision_change": 0,
            "vision_improved_percent": 0,
            "vision_stable_percent": 0,
            "vision_declined_percent": 0
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
