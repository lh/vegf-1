"""
Central style constants and principles for V2 visualizations.

This module defines all styling rules to ensure consistency across the application.
No individual visualization should override these without explicit justification.

Vision Measurement Note:
- We use ETDRS letter count (0-100) as our standard
- logMAR could be added as an alternative display (0.0 = 85 letters, 1.0 = 35 letters)
- Individual letter counts are ALWAYS integers
- Statistical measures (means, SD) may have one decimal place
"""

import numpy as np
from typing import Dict, List, Tuple, Optional


class StyleConstants:
    """Central repository for all styling constants."""
    
    # Vision scale rules
    VISION_SCALE = {
        'min': 0,
        'max': 100,
        'major_ticks': [0, 20, 40, 60, 80, 100],
        'minor_ticks': [10, 30, 50, 70, 90],
        'clinical_thresholds': {
            'legal_blindness': 35,  # 1.0 logMAR
            'driving_standard': 70,  # 0.3 logMAR
            'normal': 85,  # 0.0 logMAR
        }
    }
    
    # Vision change scale (symmetric around 0)
    VISION_CHANGE_SCALE = {
        'max_change': 30,  # ±30 letters is extreme
        'major_ticks': [-30, -20, -10, 0, 10, 20, 30],
        'minor_ticks': [-25, -15, -5, 5, 15, 25],
    }
    
    # Time axes configurations
    TIME_SCALES = {
        'days': {
            'week_based': [0, 28, 56, 84, 112, 140, 168],  # 0, 4, 8, 12, 16, 20, 24 weeks
            'month_based': [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360],
            'quarter_based': [0, 90, 180, 270, 360, 450, 540, 630, 720],  # 0, 3, 6, 9... months
        },
        'months': {
            'standard': [0, 3, 6, 9, 12, 18, 24, 30, 36, 42, 48, 54, 60],
            'quarterly': [0, 3, 6, 12, 24, 36, 48, 60],
        },
        'years': {
            'standard': [0, 1, 2, 3, 4, 5],
            'detailed': [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5],
        }
    }
    
    # Axis range rules
    AXIS_RULES = {
        'counts': {
            'start_at_zero': True,  # Patient counts, injection counts, etc.
            'integer_ticks': True,
            'pad_percentage': 0.05,  # 5% padding above max
        },
        'rates': {
            'start_at_zero': True,  # Percentages, rates
            'max_at_one': True,  # For proportions
            'pad_percentage': 0.05,
        },
        'measurements': {
            'start_at_zero': False,  # Use data range
            'pad_percentage': 0.1,  # 10% padding on each side
        },
        'changes': {
            'center_on_zero': True,  # Vision change, etc.
            'symmetric': True,  # Same range above and below zero
            'pad_percentage': 0.1,
        }
    }
    
    # Spine visibility rules
    SPINE_RULES = {
        'analysis': {
            'top': False,
            'right': False,
            'left': False,   # Tufte: remove non-data ink
            'bottom': False,  # Tufte: remove non-data ink
            'alpha': 0.0,
            'linewidth': 0.0,
        },
        'presentation': {
            'top': False,
            'right': False,
            'left': True,    # Keep for Zoom orientation
            'bottom': True,   # Keep for Zoom orientation
            'alpha': 0.5,     # Subtle, not dominant
            'linewidth': 1.0,
        }
    }
    
    # Number formatting rules
    PRECISION_RULES = {
        'patient_counts': 0,  # No decimals ever
        'injection_counts': 0,  # No decimals ever
        'visit_counts': 0,  # No decimals ever
        'vision_individual': 0,  # Individual vision is always integer
        'vision_mean': 1,  # Statistical measures get 1 decimal
        'vision_sd': 1,  # Statistical measures get 1 decimal
        'percentages': 1,  # 1 decimal for percentages
        'rates': 2,  # 2 decimals for rates (e.g., 0.85)
        'days': 0,  # No fractional days
        'months': 1,  # Can have fractional months
        'years': 1,  # Can have fractional years
    }
    
    # Special formatting functions
    @staticmethod
    def format_vision(value: float, is_statistical: bool = False) -> str:
        """Format vision values according to rules."""
        if is_statistical:
            return f"{value:.1f}"
        else:
            return f"{int(value)}"
    
    @staticmethod
    def format_count(value: float, count_type: str = 'patient') -> str:
        """Format count values - always integers."""
        return f"{int(value)}"
    
    @staticmethod
    def format_percentage(value: float, include_sign: bool = True) -> str:
        """Format percentage with one decimal.
        
        Assumes value is a decimal (0.85 = 85%) unless it's > 1 (then assumes it's already a percentage).
        """
        # If value is > 1, assume it's already a percentage (e.g., 85 for 85%)
        if value > 1:
            percentage = value
        else:
            percentage = value * 100
            
        if include_sign:
            return f"{percentage:.1f}%"
        else:
            return f"{percentage:.1f}"
    
    @staticmethod
    def format_statistic(value: float) -> str:
        """Format general statistics with one decimal."""
        return f"{value:.1f}"
    
    @staticmethod
    def get_vision_ticks(data_min: float = None, data_max: float = None) -> List[int]:
        """Get appropriate vision tick marks.
        
        If no bounds provided, returns all standard ticks.
        If bounds provided, returns only ticks within range.
        """
        if data_min is None or data_max is None:
            # Return all standard vision ticks
            return StyleConstants.VISION_SCALE['major_ticks']
        else:
            # Return only ticks within the data range (with small buffer)
            return [t for t in StyleConstants.VISION_SCALE['major_ticks'] 
                    if data_min - 5 <= t <= data_max + 5]
    
    @staticmethod
    def get_time_ticks(days: int, preferred_unit: str = 'weeks') -> List[int]:
        """Get appropriate time tick marks based on duration.
        
        Returns clean intervals:
        - Weeks: Every 4 weeks
        - Months: Every 3 months (quarterly) or 6 months depending on duration
        - Years: Annual markers
        """
        if preferred_unit == 'weeks' and days <= 168:  # Up to 24 weeks
            # Use 4-week intervals
            return [i * 28 for i in range(int(days / 28) + 2)]
        elif preferred_unit == 'months':
            # For months, use clean intervals
            if days <= 365:  # Up to 1 year: quarterly (0, 3, 6, 9, 12)
                months_total = int(days / 30.44)
                tick_months = []
                for m in range(0, months_total + 1, 3):
                    tick_months.append(m)
                if tick_months[-1] < months_total:
                    tick_months.append(months_total)
                # Convert back to days for consistency
                return [int(m * 30.44) for m in tick_months]
            elif days <= 730:  # Up to 2 years: every 6 months
                months_total = int(days / 30.44)
                tick_months = []
                for m in range(0, months_total + 1, 6):
                    tick_months.append(m)
                if tick_months[-1] < months_total:
                    tick_months.append(months_total)
                return [int(m * 30.44) for m in tick_months]
            else:  # More than 2 years: annual
                years_total = int(days / 365.25)
                return [i * 365 for i in range(years_total + 1)]
        else:
            # Default to quarterly intervals
            return [i * 90 for i in range(int(days / 90) + 2)]
    
    @staticmethod
    def get_month_ticks(total_months: int) -> List[int]:
        """Get clean month tick marks (0, 3, 6, 9... or 0, 6, 12, 18...)."""
        if total_months <= 12:
            # Quarterly for up to 1 year
            return list(range(0, total_months + 1, 3))
        elif total_months <= 24:
            # Every 6 months for up to 2 years
            return list(range(0, total_months + 1, 6))
        else:
            # Annual for longer periods
            return list(range(0, total_months + 1, 12))
    
    @staticmethod
    def get_count_ticks(data_max: float, target_ticks: int = 6) -> List[int]:
        """Get integer tick marks for count data."""
        # Find a nice round interval
        raw_interval = data_max / target_ticks
        
        # Round to nice numbers
        if raw_interval <= 1:
            interval = 1
        elif raw_interval <= 2:
            interval = 2
        elif raw_interval <= 5:
            interval = 5
        elif raw_interval <= 10:
            interval = 10
        elif raw_interval <= 20:
            interval = 20
        elif raw_interval <= 25:
            interval = 25
        elif raw_interval <= 50:
            interval = 50
        elif raw_interval <= 100:
            interval = 100
        else:
            # For large numbers, use multiples of 100
            interval = int(np.ceil(raw_interval / 100) * 100)
        
        return list(range(0, int(data_max) + interval, interval))
    
    @staticmethod
    def apply_spine_rules(ax, mode: str = 'analysis'):
        """Apply spine visibility rules to an axis."""
        rules = StyleConstants.SPINE_RULES.get(mode, StyleConstants.SPINE_RULES['analysis'])
        
        for spine_name, visible in [('top', rules['top']), 
                                    ('right', rules['right']),
                                    ('left', rules['left']), 
                                    ('bottom', rules['bottom'])]:
            spine = ax.spines[spine_name]
            spine.set_visible(visible)
            if visible:
                spine.set_alpha(rules['alpha'])
                spine.set_linewidth(rules['linewidth'])
    
    @staticmethod
    def apply_axis_rules(ax, data_type: str, data_min: float, data_max: float):
        """Apply axis range rules based on data type."""
        rules = StyleConstants.AXIS_RULES.get(data_type, StyleConstants.AXIS_RULES['measurements'])
        
        if rules['start_at_zero']:
            y_min = 0
        elif rules.get('center_on_zero'):
            # For change data, make symmetric around zero
            max_abs = max(abs(data_min), abs(data_max))
            y_min = -max_abs * (1 + rules['pad_percentage'])
            data_max = max_abs
        else:
            y_min = data_min - (data_max - data_min) * rules['pad_percentage']
        
        y_max = data_max + (data_max - data_min) * rules['pad_percentage']
        
        if rules.get('max_at_one'):
            y_max = min(y_max, 1.0)
        
        ax.set_ylim(y_min, y_max)
    
    # logMAR conversion utilities (for future use)
    @staticmethod
    def letters_to_logmar(letters: int) -> float:
        """Convert ETDRS letters to logMAR."""
        return -0.02 * (letters - 85)
    
    @staticmethod
    def logmar_to_letters(logmar: float) -> int:
        """Convert logMAR to ETDRS letters."""
        return int(85 - (logmar * 50))