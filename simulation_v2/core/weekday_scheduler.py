"""
Weekday-aware scheduling utilities.

Ensures visits are scheduled on weekdays (Monday-Friday) with
appropriate flexibility for different visit types.
"""

from datetime import datetime, timedelta
from typing import Tuple


class WeekdayScheduler:
    """Handle weekend-aware visit scheduling."""
    
    def __init__(self, allow_saturday: bool = False, allow_sunday: bool = False):
        """
        Initialize scheduler with weekend working configuration.
        
        Args:
            allow_saturday: Whether Saturday visits are allowed
            allow_sunday: Whether Sunday visits are allowed
        """
        self.allow_saturday = allow_saturday
        self.allow_sunday = allow_sunday
    
    def adjust_to_weekday(self, date: datetime, prefer_earlier: bool = True) -> datetime:
        """
        Adjust a date to the nearest allowed working day.
        
        Args:
            date: Original scheduled date
            prefer_earlier: If True, prefer Friday over Monday for adjustments
            
        Returns:
            Adjusted date on an allowed working day
        """
        weekday = date.weekday()
        
        # Check if current day is allowed
        if weekday < 5:  # Monday (0) to Friday (4)
            return date
        elif weekday == 5:  # Saturday
            if self.allow_saturday:
                return date
            elif prefer_earlier:
                # Move to Friday
                return date - timedelta(days=1)
            else:
                # Move to Monday (or Sunday if allowed)
                if self.allow_sunday:
                    return date + timedelta(days=1)  # Sunday
                else:
                    return date + timedelta(days=2)  # Monday
        else:  # Sunday (6)
            if self.allow_sunday:
                return date
            elif prefer_earlier:
                # Move to Saturday (if allowed) or Friday
                if self.allow_saturday:
                    return date - timedelta(days=1)  # Saturday
                else:
                    return date - timedelta(days=2)  # Friday
            else:
                # Move to Monday
                return date + timedelta(days=1)
    
    @staticmethod
    def get_interval_flexibility(visit_number: int, target_interval_weeks: int) -> Tuple[int, int]:
        """
        Get allowed flexibility for a visit interval.
        
        Args:
            visit_number: Visit number (1-based)
            target_interval_weeks: Target interval in weeks
            
        Returns:
            Tuple of (min_days, max_days) for the interval
        """
        if visit_number <= 3:
            # Loading phase: 4-5 week flexibility
            return (28, 35)  # 4-5 weeks
        elif target_interval_weeks == 8:
            # Standard 8-week visits: 8-9 week flexibility
            return (56, 63)  # 8-9 weeks
        elif target_interval_weeks == 12:
            # 12-week visits: 11-13 week flexibility
            return (77, 91)  # 11-13 weeks
        elif target_interval_weeks == 16:
            # 16-week visits: 15-17 week flexibility
            return (105, 119)  # 15-17 weeks
        else:
            # Default: ±1 week flexibility
            target_days = target_interval_weeks * 7
            return (target_days - 7, target_days + 7)
    
    def schedule_next_visit(
        self,
        current_date: datetime,
        target_interval_days: int,
        visit_number: int,
        prefer_earlier: bool = True
    ) -> datetime:
        """
        Schedule next visit on a weekday with appropriate flexibility.
        
        Args:
            current_date: Current visit date
            target_interval_days: Target interval in days
            visit_number: Current visit number
            prefer_earlier: Whether to prefer earlier dates when adjusting
            
        Returns:
            Next visit date (guaranteed to be on a weekday)
        """
        # Calculate target date
        target_date = current_date + timedelta(days=target_interval_days)
        
        # Get flexibility range
        target_weeks = round(target_interval_days / 7)
        min_days, max_days = self.get_interval_flexibility(visit_number, target_weeks)
        
        # Adjust to weekday
        adjusted_date = self.adjust_to_weekday(target_date, prefer_earlier)
        
        # Check if adjustment is within flexibility range
        actual_interval = (adjusted_date - current_date).days
        
        if min_days <= actual_interval <= max_days:
            return adjusted_date
        elif actual_interval < min_days:
            # Too early, try the other direction
            adjusted_date = self.adjust_to_weekday(target_date, prefer_earlier=False)
            actual_interval = (adjusted_date - current_date).days
            
            if actual_interval <= max_days:
                return adjusted_date
            else:
                # Still outside range, use minimum allowed
                min_date = current_date + timedelta(days=min_days)
                return self.adjust_to_weekday(min_date, prefer_earlier=False)
        else:
            # Too late, use maximum allowed
            max_date = current_date + timedelta(days=max_days)
            return self.adjust_to_weekday(max_date, prefer_earlier=True)
    
    def is_working_day(self, date: datetime) -> bool:
        """Check if a date is an allowed working day."""
        weekday = date.weekday()
        if weekday < 5:  # Monday-Friday
            return True
        elif weekday == 5:  # Saturday
            return self.allow_saturday
        else:  # Sunday
            return self.allow_sunday