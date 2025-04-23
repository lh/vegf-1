"""Patient generation module for ophthalmic simulation models.

This module provides functionality for generating patient arrival times using a
Poisson process, which models random arrivals with a known average rate.

The main class `PatientGenerator` creates patient arrival schedules between
specified dates with configurable arrival rates.

Notes
-----
The Poisson process is implemented using exponentially distributed inter-arrival
times, which is mathematically equivalent to a Poisson process for arrivals.

Examples
--------
>>> generator = PatientGenerator(rate_per_week=10,
...                            start_date=datetime(2023,1,1),
...                            end_date=datetime(2023,12,31))
>>> arrivals = generator.generate_arrival_times()
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import numpy as np

class PatientGenerator:
    """Generates patient arrival times using a Poisson process"""
    def __init__(self, rate_per_week: float, start_date: datetime, end_date: datetime, random_seed: Optional[int] = None):
        """
        Args:
            rate_per_week: Average number of new patients per week
            start_date: Start date for patient generation
            end_date: End date for patient generation
            random_seed: Optional random seed for reproducibility
        """
        self.rate_per_week = rate_per_week
        self.start_date = start_date
        self.end_date = end_date
        self.total_weeks = (end_date - start_date).days / 7
        
        # Initialize random state
        if random_seed is not None:
            self.rng = np.random.RandomState(random_seed)
        else:
            self.rng = np.random
            
    def generate_arrival_times(self) -> List[Tuple[datetime, int]]:
        """Generate arrival times for all patients using a Poisson process
        
        Returns:
            List of (arrival_time, patient_number) tuples
        """
        # Calculate expected total patients
        expected_patients = int(self.rate_per_week * self.total_weeks)
        
        # Generate inter-arrival times from exponential distribution
        mean_interarrival_days = 7 / self.rate_per_week  # Convert weekly rate to daily
        interarrival_times = self.rng.exponential(mean_interarrival_days, size=expected_patients)
        
        # Convert to arrival times
        arrival_times = []
        current_time = self.start_date
        patient_num = 1
        
        for interval in interarrival_times:
            current_time += timedelta(days=interval)
            if current_time >= self.end_date:
                break
            arrival_times.append((current_time, patient_num))
            patient_num += 1
            
        return arrival_times
