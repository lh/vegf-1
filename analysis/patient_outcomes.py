from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, NamedTuple
import numpy as np
from scipy import interpolate

class TimePoint(NamedTuple):
    """Data for a specific time point in the analysis"""
    week: int
    mean: float
    std: float
    ci_lower: float
    ci_upper: float
    n_patients: int

class PatientOutcomeAnalyzer:
    """Analyzes patient outcomes and computes statistics"""
    
    def __init__(self, max_weeks: int = 156):  # 3 years
        """Initialize analyzer with maximum follow-up period
        
        Args:
            max_weeks: Maximum number of weeks to analyze
        """
        self.max_weeks = max_weeks
        self.week_points = list(range(max_weeks + 1))
    
    def analyze_visual_acuity(self, patient_data: Dict[str, List[Dict]]) -> List[TimePoint]:
        """Analyze visual acuity outcomes aligned by treatment start
        
        Args:
            patient_data: Dictionary of patient IDs to their visit histories
                Each visit should have 'date' and 'vision' fields
                
        Returns:
            List of TimePoint objects containing statistics for each week
        """
        # Initialize data structures
        weekly_values: Dict[int, List[float]] = {week: [] for week in self.week_points}
        
        # Process each patient's data
        for patient_id, history in patient_data.items():
            patient_weeks, patient_values = self._process_patient_timeline(history)
            if not patient_weeks:  # Skip if no valid data
                continue
                
            # Interpolate to weekly points
            interpolated = self._interpolate_patient_values(
                patient_weeks, patient_values)
            
            # Add to weekly aggregates
            for week, value in enumerate(interpolated):
                if week <= self.max_weeks and not np.isnan(value):
                    weekly_values[week].append(value)
        
        # Calculate statistics for each week
        time_points = []
        for week in self.week_points:
            values = weekly_values[week]
            if not values:  # Skip weeks with no data
                continue
                
            stats = self._calculate_statistics(values)
            time_points.append(TimePoint(
                week=week,
                mean=stats['mean'],
                std=stats['std'],
                ci_lower=stats['ci_lower'],
                ci_upper=stats['ci_upper'],
                n_patients=len(values)
            ))
        
        return time_points
    
    def _process_patient_timeline(self, history: List[Dict]) -> Tuple[List[float], List[float]]:
        """Extract and align patient's timeline to treatment start
        
        Args:
            history: List of visit dictionaries with date and vision values
            
        Returns:
            Tuple of (weeks_since_start, vision_values)
        """
        if not history:
            return [], []
            
        # Get treatment start date (first visit)
        treatment_start = history[0]['date']
        
        # Extract dates and vision values
        weeks_since_start = []
        vision_values = []
        
        for visit in history:
            if 'date' in visit and 'vision' in visit:
                weeks = (visit['date'] - treatment_start).days / 7
                if 0 <= weeks <= self.max_weeks:  # Only include valid range
                    weeks_since_start.append(weeks)
                    vision_values.append(float(visit['vision']))
        
        return weeks_since_start, vision_values
    
    def _interpolate_patient_values(self, weeks: List[float], 
                                  values: List[float]) -> np.ndarray:
        """Interpolate patient values to weekly points
        
        Args:
            weeks: List of week numbers for actual measurements
            values: List of measured values
            
        Returns:
            Array of interpolated values for each week
        """
        if len(weeks) < 2:  # Need at least 2 points for interpolation
            return np.full(self.max_weeks + 1, np.nan)
            
        # Create interpolation function
        f = interpolate.interp1d(
            weeks, values,
            bounds_error=False,    # Return nan outside bounds
            fill_value=np.nan      # Use nan for extrapolation
        )
        
        # Interpolate to weekly points
        return f(self.week_points)
    
    def _calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """Calculate statistics for a set of values
        
        Args:
            values: List of values to analyze
            
        Returns:
            Dict containing mean, std, and confidence interval bounds
        """
        values_array = np.array(values)
        n = len(values)
        mean = np.mean(values_array)
        std = np.std(values_array, ddof=1)  # Use n-1 for sample std
        
        # 95% confidence interval
        ci_width = 1.96 * std / np.sqrt(n)
        
        return {
            'mean': mean,
            'std': std,
            'ci_lower': mean - ci_width,
            'ci_upper': mean + ci_width
        }
    
    def get_median_followup(self, patient_data: Dict[str, List[Dict]]) -> float:
        """Calculate median follow-up time in weeks
        
        Args:
            patient_data: Dictionary of patient IDs to their visit histories
            
        Returns:
            Median follow-up time in weeks
        """
        followup_times = []
        
        for history in patient_data.values():
            if not history:
                continue
                
            treatment_start = history[0]['date']
            last_visit = history[-1]['date']
            weeks = (last_visit - treatment_start).days / 7
            followup_times.append(weeks)
        
        if not followup_times:
            return 0
            
        return float(np.median(followup_times))
