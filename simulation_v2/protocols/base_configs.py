"""
Base configurations for protocol calibration.

These configurations ensure that different protocols using the same drug
have identical underlying disease and vision models, allowing fair comparison
of treatment strategies.
"""

# Aflibercept base configuration
# Calibrated to achieve realistic outcomes based on literature review
AFLIBERCEPT_BASE_CONFIG = {
    'disease_transitions': {
        'NAIVE': {
            'NAIVE': 0.0,
            'STABLE': 0.45,      # 45% achieve stability after loading
            'ACTIVE': 0.45,      # 45% remain active
            'HIGHLY_ACTIVE': 0.10
        },
        'STABLE': {
            'NAIVE': 0.0,
            'STABLE': 0.88,      # High retention when stable
            'ACTIVE': 0.12,      # Some recurrence
            'HIGHLY_ACTIVE': 0.0
        },
        'ACTIVE': {
            'NAIVE': 0.0,
            'STABLE': 0.35,      # Can improve with treatment
            'ACTIVE': 0.55,      # Many remain active
            'HIGHLY_ACTIVE': 0.10
        },
        'HIGHLY_ACTIVE': {
            'NAIVE': 0.0,
            'STABLE': 0.10,
            'ACTIVE': 0.30,
            'HIGHLY_ACTIVE': 0.60
        }
    },
    
    'treatment_effect_on_transitions': {
        'NAIVE': {
            'multipliers': {}
        },
        'STABLE': {
            'multipliers': {
                'STABLE': 1.2,      # 20% more likely to stay stable
                'ACTIVE': 0.8       # 20% less likely to become active
            }
        },
        'ACTIVE': {
            'multipliers': {
                'STABLE': 2.5,      # 2.5x more likely to become stable
                'ACTIVE': 0.7,      # 30% less likely to stay active
                'HIGHLY_ACTIVE': 0.5  # 50% less likely to worsen
            }
        },
        'HIGHLY_ACTIVE': {
            'multipliers': {
                'STABLE': 2.0,      # Twice as likely to improve dramatically
                'ACTIVE': 1.8,      # 80% more likely to improve
                'HIGHLY_ACTIVE': 0.6  # 40% less likely to remain severe
            }
        }
    },
    
    'vision_change_model': {
        'naive_treated': {
            'mean': 3.0,
            'std': 2.0
        },
        'naive_untreated': {
            'mean': -3.0,
            'std': 2.0
        },
        'stable_treated': {
            'mean': 1.5,
            'std': 1.5
        },
        'stable_untreated': {
            'mean': -0.5,
            'std': 1.0
        },
        'active_treated': {
            'mean': 0.5,
            'std': 2.0
        },
        'active_untreated': {
            'mean': -3.0,
            'std': 2.0
        },
        'highly_active_treated': {
            'mean': -0.5,
            'std': 2.0
        },
        'highly_active_untreated': {
            'mean': -5.0,
            'std': 3.0
        }
    },
    
    'baseline_vision_distribution': {
        'type': 'normal',
        'mean': 55,
        'std': 15,
        'min': 20,
        'max': 85
    },
    
    'discontinuation_rules': {
        'poor_vision_threshold': 35,
        'poor_vision_probability': 0.05,
        'high_injection_count': 25,
        'high_injection_probability': 0.02,
        'long_treatment_months': 60,
        'long_treatment_probability': 0.02,
        'discontinuation_types': ['planned', 'adverse', 'ineffective']
    },
    
    'clinical_improvements': {
        'enabled': True,
        'use_loading_phase': True,
        'use_time_based_discontinuation': True,
        'use_response_based_vision': True,
        'use_baseline_distribution': False,  # Use protocol's distribution
        'use_response_heterogeneity': True,
        
        'response_types': {
            'good': {
                'probability': 0.30,    # 30% good responders
                'multiplier': 1.8       # 80% better vision gains
            },
            'average': {
                'probability': 0.50,    # 50% average responders
                'multiplier': 1.0       # Normal vision gains
            },
            'poor': {
                'probability': 0.20,    # 20% poor responders
                'multiplier': 0.5       # 50% worse vision gains
            }
        },
        
        'discontinuation_probabilities': {
            1: 0.10,   # 10% Year 1
            2: 0.15,   # 15% Year 2 
            3: 0.12,   # 12% Year 3
            4: 0.08,   # 8% Year 4
            5: 0.075   # 7.5% Year 5+
        },
        
        'vision_response_params': {
            'loading': {
                'mean': 4.0,
                'std': 1.5
            },
            'year1': {
                'mean': 1.0,
                'std': 1.0
            },
            'year2': {
                'mean': 0.0,
                'std': 1.0
            },
            'year3plus': {
                'mean': -0.3,
                'std': 1.0
            }
        }
    }
}


def get_base_config(drug_name='aflibercept'):
    """
    Get base configuration for a specific drug.
    
    Args:
        drug_name: Name of the drug ('aflibercept', 'ranibizumab', etc.)
        
    Returns:
        dict: Base configuration dictionary
    """
    if drug_name.lower() == 'aflibercept':
        return AFLIBERCEPT_BASE_CONFIG
    else:
        raise ValueError(f"No base configuration available for {drug_name}")


def merge_configs(base_config, protocol_specific):
    """
    Merge base configuration with protocol-specific settings.
    
    Args:
        base_config: Base configuration dictionary
        protocol_specific: Protocol-specific overrides
        
    Returns:
        dict: Merged configuration
    """
    import copy
    
    # Deep copy base config
    merged = copy.deepcopy(base_config)
    
    # Deep merge function
    def deep_merge(target, source):
        """Recursively merge source into target."""
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                # Recursively merge nested dictionaries
                deep_merge(target[key], value)
            else:
                # Replace value
                target[key] = value
    
    # Apply protocol-specific settings
    deep_merge(merged, protocol_specific)
    
    return merged