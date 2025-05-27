"""
Discontinuation profile management for V2 simulation.

This module provides configurable discontinuation profiles that can be 
loaded, saved, and applied to simulations. Profiles define the criteria
and probabilities for different types of treatment discontinuation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import json


@dataclass
class CategoryConfig:
    """Configuration for a single discontinuation category."""
    enabled: bool = True
    
    # Common fields
    probability: Optional[float] = None
    annual_probability: Optional[float] = None
    annual_rate: Optional[float] = None
    
    # Stable max interval
    consecutive_visits: Optional[int] = None
    required_interval_weeks: Optional[int] = None
    
    # Poor response
    vision_threshold_letters: Optional[int] = None
    
    # Premature
    target_rate: Optional[float] = None
    min_interval_weeks: Optional[int] = None
    min_vision_letters: Optional[int] = None
    va_impact: Optional[Dict[str, float]] = None
    
    # Reauthorization failure
    threshold_weeks: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CategoryConfig':
        """Create CategoryConfig from dictionary."""
        return cls(**data)


@dataclass
class DiscontinuationProfile:
    """
    Complete discontinuation profile configuration.
    
    Defines all parameters for discontinuation behavior including
    categories, monitoring schedules, and retreatment criteria.
    """
    name: str
    description: str = ""
    
    # Category configurations
    categories: Dict[str, CategoryConfig] = field(default_factory=dict)
    
    # Monitoring schedules (weeks after discontinuation)
    monitoring_schedules: Dict[str, List[int]] = field(default_factory=lambda: {
        'planned': [12, 24, 36],
        'unplanned': [8, 16, 24],
        'poor_response': [],
        'mortality': [],
        'system': []
    })
    
    # Retreatment criteria
    retreatment: Dict[str, Any] = field(default_factory=lambda: {
        'fluid_detection_required': True,
        'min_vision_loss_letters': 5,
        'probability': 0.95,
        'detection_probability': 0.87
    })
    
    # Recurrence rates by discontinuation type
    recurrence_rates: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'stable_max_interval': {
            'year_1': 0.13,
            'year_3': 0.40,
            'year_5': 0.65
        },
        'premature': {
            'year_1': 0.53,
            'year_3': 0.85,
            'year_5': 0.95
        },
        'system_discontinuation': {
            'year_1': 0.30,
            'year_3': 0.70,
            'year_5': 0.85
        },
        'reauthorization_failure': {
            'year_1': 0.21,
            'year_3': 0.74,
            'year_5': 0.88
        },
        'poor_response': {
            'year_1': 0.0,  # No recurrence if treatment failed
            'year_3': 0.0,
            'year_5': 0.0
        },
        'mortality': {
            'year_1': 0.0,  # No recurrence after death
            'year_3': 0.0,
            'year_5': 0.0
        }
    })
    
    @classmethod
    def from_yaml(cls, path: Path) -> 'DiscontinuationProfile':
        """Load profile from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Parse categories
        categories = {}
        for cat_name, cat_data in data.get('categories', {}).items():
            categories[cat_name] = CategoryConfig.from_dict(cat_data)
        
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            categories=categories,
            monitoring_schedules=data.get('monitoring_schedules', cls.__dataclass_fields__['monitoring_schedules'].default_factory()),
            retreatment=data.get('retreatment', cls.__dataclass_fields__['retreatment'].default_factory()),
            recurrence_rates=data.get('recurrence_rates', cls.__dataclass_fields__['recurrence_rates'].default_factory())
        )
    
    def to_yaml(self, path: Path) -> None:
        """Save profile to YAML file."""
        data = {
            'name': self.name,
            'description': self.description,
            'categories': {},
            'monitoring_schedules': self.monitoring_schedules,
            'retreatment': self.retreatment,
            'recurrence_rates': self.recurrence_rates
        }
        
        # Convert categories to dict
        for cat_name, cat_config in self.categories.items():
            cat_dict = {}
            for field_name, field_value in cat_config.__dict__.items():
                if field_value is not None:
                    cat_dict[field_name] = field_value
            data['categories'][cat_name] = cat_dict
        
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'categories': {
                name: {k: v for k, v in cat.__dict__.items() if v is not None}
                for name, cat in self.categories.items()
            },
            'monitoring_schedules': self.monitoring_schedules,
            'retreatment': self.retreatment,
            'recurrence_rates': self.recurrence_rates
        }
    
    def validate(self) -> List[str]:
        """
        Validate profile configuration.
        
        Returns list of validation errors, empty if valid.
        """
        errors = []
        
        # Check required categories
        required_categories = [
            'stable_max_interval', 'system_discontinuation', 
            'reauthorization_failure', 'premature', 
            'poor_response', 'mortality'
        ]
        
        for cat in required_categories:
            if cat not in self.categories:
                errors.append(f"Missing required category: {cat}")
        
        # Validate probabilities
        for cat_name, cat_config in self.categories.items():
            if cat_config.enabled:
                if cat_name == 'mortality' and cat_config.annual_rate is None:
                    errors.append(f"{cat_name}: missing annual_rate")
                elif cat_name == 'system_discontinuation' and cat_config.annual_probability is None:
                    errors.append(f"{cat_name}: missing annual_probability")
                elif cat_name in ['stable_max_interval', 'reauthorization_failure'] and cat_config.probability is None:
                    errors.append(f"{cat_name}: missing probability")
        
        # Validate monitoring schedules
        for schedule_name, weeks in self.monitoring_schedules.items():
            if not isinstance(weeks, list):
                errors.append(f"Monitoring schedule {schedule_name} must be a list")
            elif any(not isinstance(w, (int, float)) for w in weeks):
                errors.append(f"Monitoring schedule {schedule_name} contains non-numeric values")
        
        return errors


# Default profiles
def create_ideal_profile() -> DiscontinuationProfile:
    """Create the 'Ideal' profile with no administrative errors."""
    return DiscontinuationProfile(
        name="Ideal",
        description="Perfect world scenario with no system failures",
        categories={
            'stable_max_interval': CategoryConfig(
                enabled=True,
                consecutive_visits=3,
                required_interval_weeks=16,
                probability=0.20
            ),
            'poor_response': CategoryConfig(
                enabled=True,
                vision_threshold_letters=15,
                consecutive_visits=2
            ),
            'premature': CategoryConfig(
                enabled=True,
                target_rate=0.05,  # Lower in ideal world
                min_interval_weeks=8,
                min_vision_letters=20,
                va_impact={'mean': -9.4, 'std': 5.0}
            ),
            'system_discontinuation': CategoryConfig(
                enabled=False  # No admin errors in ideal world
            ),
            'reauthorization_failure': CategoryConfig(
                enabled=False  # No funding lapses in ideal world
            ),
            'mortality': CategoryConfig(
                enabled=True,
                annual_rate=0.02  # 20/1000
            )
        }
    )


def create_nhs1_profile() -> DiscontinuationProfile:
    """Create the 'NHS_1' profile based on real-world UK unit."""
    return DiscontinuationProfile(
        name="NHS_1",
        description="Real-world UK NHS unit parameters",
        categories={
            'stable_max_interval': CategoryConfig(
                enabled=True,
                consecutive_visits=3,
                required_interval_weeks=16,
                probability=0.20
            ),
            'poor_response': CategoryConfig(
                enabled=True,
                vision_threshold_letters=15,
                consecutive_visits=2
            ),
            'premature': CategoryConfig(
                enabled=True,
                target_rate=0.145,
                min_interval_weeks=8,
                min_vision_letters=20,
                va_impact={'mean': -9.4, 'std': 5.0}
            ),
            'system_discontinuation': CategoryConfig(
                enabled=True,
                annual_probability=0.05
            ),
            'reauthorization_failure': CategoryConfig(
                enabled=True,
                threshold_weeks=52,
                probability=0.10
            ),
            'mortality': CategoryConfig(
                enabled=True,
                annual_rate=0.02  # 20/1000, configurable
            )
        }
    )


def get_default_profiles() -> Dict[str, DiscontinuationProfile]:
    """Get all default profiles."""
    return {
        'ideal': create_ideal_profile(),
        'nhs_1': create_nhs1_profile()
    }