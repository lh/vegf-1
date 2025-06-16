"""
Mortality model for AMD cohort simulations with demographic adjustments.

This module provides functions to calculate mortality risk for patients with wet AMD
based on UK population mortality rates, AMD-specific hazard ratios, and demographic
distributions that change with age.

Key features:
- Individual patient mortality calculations
- Population-weighted mortality accounting for age-dependent gender distribution
- Survival bias adjustments for elderly populations
- Clinical trial vs real-world population adjustments

Example usage:
    from simulation_v2.models.mortality import MortalityModel, PopulationMortalityModel
    
    # Individual patient mortality
    mortality = MortalityModel()
    prob = mortality.get_annual_mortality_probability(age=70, sex='male', has_wet_amd=True)
    
    # Population-weighted mortality
    pop_mortality = PopulationMortalityModel()
    avg_risk = pop_mortality.get_population_mortality(age=80, population_type='real_world')
"""

import yaml
from pathlib import Path
from typing import Dict, Literal, Optional, Union, Tuple
import numpy as np


class MortalityModel:
    """Model for calculating mortality risk in AMD patients."""
    
    def __init__(self, data_file: Optional[Path] = None):
        """
        Initialize the mortality model.
        
        Args:
            data_file: Path to mortality data YAML file. If None, uses default location.
        """
        if data_file is None:
            data_file = Path(__file__).parent.parent.parent / "protocols" / "v2_time_based" / "parameters" / "uk_mortality_wet_amd.yaml"
        
        with open(data_file, 'r') as f:
            self.data = yaml.safe_load(f)
        
        self.mortality_rates = self.data['mortality_rates']
        self.wet_amd_rates = self.data['wet_amd_mortality_rates']
        self.hazard_ratios = self.data['hazard_ratios']
    
    def get_annual_mortality_probability(
        self,
        age: int,
        sex: Literal['male', 'female'],
        has_wet_amd: bool = False,
        hazard_ratio: Union[Literal['primary', 'conservative', 'high'], float] = 'primary'
    ) -> float:
        """
        Get annual mortality probability for a patient.
        
        Args:
            age: Patient age (50-100)
            sex: Patient sex ('male' or 'female')
            has_wet_amd: Whether patient has wet AMD
            hazard_ratio: Which HR to use ('primary', 'conservative', 'high') or custom float
        
        Returns:
            Annual probability of death (0-1)
        
        Raises:
            ValueError: If age is outside valid range or sex is invalid
        """
        if age < 50 or age > 100:
            raise ValueError(f"Age {age} outside valid range (50-100)")
        
        if sex not in ['male', 'female']:
            raise ValueError(f"Invalid sex: {sex}")
        
        # Get base mortality rate
        base_rate = self.mortality_rates[sex].get(age)
        
        # If age not in table, interpolate
        if base_rate is None:
            base_rate = self._interpolate_rate(age, sex)
        
        if not has_wet_amd:
            return base_rate
        
        # Apply hazard ratio for wet AMD
        if isinstance(hazard_ratio, str):
            hr = self.hazard_ratios[hazard_ratio]
        else:
            hr = hazard_ratio
        
        # Calculate adjusted probability
        # Convert to hazard, apply HR, convert back to probability
        hazard = -np.log(1 - base_rate)
        adjusted_hazard = hazard * hr
        adjusted_prob = 1 - np.exp(-adjusted_hazard)
        
        # Cap at 1.0
        return min(adjusted_prob, 1.0)
    
    def get_monthly_mortality_probability(
        self,
        age: int,
        sex: Literal['male', 'female'],
        has_wet_amd: bool = False,
        hazard_ratio: Union[Literal['primary', 'conservative', 'high'], float] = 'primary'
    ) -> float:
        """
        Get monthly mortality probability (useful for monthly timestep simulations).
        
        Converts annual probability to monthly using: p_monthly = 1 - (1 - p_annual)^(1/12)
        """
        annual_prob = self.get_annual_mortality_probability(age, sex, has_wet_amd, hazard_ratio)
        monthly_prob = 1 - (1 - annual_prob) ** (1/12)
        return monthly_prob
    
    def get_survival_probability(
        self,
        age: int,
        sex: Literal['male', 'female'],
        years: float,
        has_wet_amd: bool = False,
        hazard_ratio: Union[Literal['primary', 'conservative', 'high'], float] = 'primary'
    ) -> float:
        """
        Get probability of surviving for a given number of years.
        
        Args:
            age: Starting age
            sex: Patient sex
            years: Number of years to project
            has_wet_amd: Whether patient has wet AMD
            hazard_ratio: Which HR to use
        
        Returns:
            Probability of surviving the full period (0-1)
        """
        survival_prob = 1.0
        
        for year in range(int(years)):
            current_age = min(age + year, 100)  # Cap at 100
            annual_mort = self.get_annual_mortality_probability(
                current_age, sex, has_wet_amd, hazard_ratio
            )
            survival_prob *= (1 - annual_mort)
        
        # Handle fractional year
        if years % 1 > 0:
            current_age = min(age + int(years), 100)
            annual_mort = self.get_annual_mortality_probability(
                current_age, sex, has_wet_amd, hazard_ratio
            )
            fractional_mort = 1 - (1 - annual_mort) ** (years % 1)
            survival_prob *= (1 - fractional_mort)
        
        return survival_prob
    
    def get_life_expectancy_impact(self, age: int, sex: Literal['male', 'female']) -> float:
        """
        Get the impact of wet AMD on life expectancy (years lost).
        
        Args:
            age: Age at diagnosis
            sex: Patient sex
        
        Returns:
            Expected years of life lost due to wet AMD
        """
        impact_data = self.data['life_expectancy_impact'][sex]
        
        # Find closest age
        ages = sorted(impact_data.keys())
        if age <= ages[0]:
            return impact_data[ages[0]]
        if age >= ages[-1]:
            return impact_data[ages[-1]]
        
        # Interpolate between nearest ages
        for i in range(len(ages) - 1):
            if ages[i] <= age <= ages[i + 1]:
                # Linear interpolation
                weight = (age - ages[i]) / (ages[i + 1] - ages[i])
                impact = (1 - weight) * impact_data[ages[i]] + weight * impact_data[ages[i + 1]]
                return impact
        
        return 0.0  # Should not reach here
    
    def _interpolate_rate(self, age: int, sex: Literal['male', 'female']) -> float:
        """Interpolate mortality rate for ages not in table."""
        rates = self.mortality_rates[sex]
        ages = sorted(rates.keys())
        
        # Handle edge cases
        if age <= ages[0]:
            return rates[ages[0]]
        if age >= ages[-1]:
            return rates[ages[-1]]
        
        # Find surrounding ages and interpolate
        for i in range(len(ages) - 1):
            if ages[i] <= age <= ages[i + 1]:
                # Linear interpolation in log space (more appropriate for mortality)
                log_rate1 = np.log(rates[ages[i]])
                log_rate2 = np.log(rates[ages[i + 1]])
                weight = (age - ages[i]) / (ages[i + 1] - ages[i])
                log_rate = (1 - weight) * log_rate1 + weight * log_rate2
                return np.exp(log_rate)
        
        return rates[ages[-1]]  # Fallback


class PopulationMortalityModel:
    """
    Model for calculating population-level mortality accounting for demographics.
    
    This model accounts for:
    - Age-dependent gender distribution in wet AMD
    - Survival bias at extreme ages
    - Different population types (clinical trial vs real-world)
    """
    
    def __init__(
        self, 
        mortality_data_file: Optional[Path] = None,
        demographics_file: Optional[Path] = None
    ):
        """Initialize population mortality model with demographics."""
        self.mortality_model = MortalityModel(mortality_data_file)
        
        if demographics_file is None:
            demographics_file = Path(__file__).parent.parent.parent / "protocols" / "v2_time_based" / "parameters" / "demographics.yaml"
        
        with open(demographics_file, 'r') as f:
            self.demographics = yaml.safe_load(f)
    
    def get_female_proportion(self, age: int) -> float:
        """
        Get proportion of females at a given age in wet AMD population.
        
        Uses sigmoid function for smooth transitions between age groups.
        """
        params = self.demographics['gender_distribution_function']
        
        # Sigmoid function for smooth transition
        x = (age - params['midpoint_age']) / params['scale_factor']
        sigmoid = 1 / (1 + np.exp(-x))
        
        female_prop = params['base_female_proportion'] + \
                     (params['max_female_proportion'] - params['base_female_proportion']) * sigmoid
        
        return np.clip(female_prop, 0.0, 1.0)
    
    def get_population_mortality(
        self,
        age: int,
        population_type: Literal['clinical_trial', 'real_world', 'frail_elderly'] = 'real_world',
        hazard_ratio: Union[Literal['primary', 'conservative', 'high'], float] = 'primary',
        apply_survival_bias: bool = True
    ) -> Dict[str, float]:
        """
        Get population-weighted mortality statistics for wet AMD patients.
        
        Args:
            age: Age of interest
            population_type: Type of population
            hazard_ratio: AMD hazard ratio to apply
            apply_survival_bias: Whether to apply survival bias adjustment
        
        Returns:
            Dictionary with:
            - weighted_annual_mortality: Population-weighted mortality rate
            - female_proportion: Proportion of females at this age
            - male_mortality: Male-specific mortality rate
            - female_mortality: Female-specific mortality rate
        """
        # Get population adjustments
        pop_adj = self.demographics['population_type_adjustments'][population_type]
        adjusted_age = age + pop_adj['age_shift']
        
        # Get gender distribution
        female_prop = self.get_female_proportion(adjusted_age)
        female_prop += pop_adj['female_proportion_adjustment']
        female_prop = np.clip(female_prop, 0.0, 1.0)
        male_prop = 1.0 - female_prop
        
        # Get base mortality rates
        male_mort = self.mortality_model.get_annual_mortality_probability(
            age=int(adjusted_age), sex='male', has_wet_amd=True, hazard_ratio=hazard_ratio
        )
        female_mort = self.mortality_model.get_annual_mortality_probability(
            age=int(adjusted_age), sex='female', has_wet_amd=True, hazard_ratio=hazard_ratio
        )
        
        # Apply population type mortality modifier
        mortality_mult = pop_adj['mortality_risk_multiplier']
        male_mort *= mortality_mult
        female_mort *= mortality_mult
        
        # Apply survival bias for very old patients
        if apply_survival_bias and age >= 80:
            bias_factor = self._get_survival_bias_factor(age)
            male_mort *= bias_factor
            female_mort *= bias_factor
        
        # Calculate weighted average
        weighted_mortality = male_prop * male_mort + female_prop * female_mort
        
        return {
            'weighted_annual_mortality': weighted_mortality,
            'female_proportion': female_prop,
            'male_mortality': male_mort,
            'female_mortality': female_mort,
            'effective_age': adjusted_age
        }
    
    def get_cohort_mortality_profile(
        self,
        starting_age: int = 70,
        years: int = 10,
        population_type: Literal['clinical_trial', 'real_world', 'frail_elderly'] = 'real_world'
    ) -> Dict[int, Dict[str, float]]:
        """
        Get mortality profile for a cohort over time.
        
        Returns mortality statistics for each year of follow-up.
        """
        profile = {}
        
        for year in range(years):
            current_age = starting_age + year
            profile[year] = self.get_population_mortality(
                age=current_age,
                population_type=population_type
            )
        
        return profile
    
    def _get_survival_bias_factor(self, age: int) -> float:
        """Get survival bias adjustment factor for elderly patients."""
        bias_factors = self.demographics['survival_bias_factors']
        
        if age >= 95:
            return bias_factors['95+']
        elif age >= 90:
            return bias_factors['90-94']
        elif age >= 85:
            return bias_factors['85-89']
        elif age >= 80:
            return bias_factors['80-84']
        else:
            return 1.0
    
    def estimate_population_survival(
        self,
        starting_age: int,
        years: int,
        population_type: Literal['clinical_trial', 'real_world', 'frail_elderly'] = 'real_world',
        n_simulations: int = 1000
    ) -> Tuple[float, float]:
        """
        Estimate population survival accounting for changing demographics.
        
        Returns:
            Tuple of (mean_survival_rate, std_survival_rate)
        """
        survivals = []
        
        for _ in range(n_simulations):
            # Randomly assign gender based on starting age distribution
            female_prop = self.get_female_proportion(starting_age)
            is_female = np.random.random() < female_prop
            sex = 'female' if is_female else 'male'
            
            # Calculate individual survival
            survival = self.mortality_model.get_survival_probability(
                age=starting_age,
                sex=sex,
                years=years,
                has_wet_amd=True
            )
            
            # Apply population adjustments
            pop_adj = self.demographics['population_type_adjustments'][population_type]
            survival *= pop_adj['mortality_risk_multiplier']
            
            survivals.append(survival)
        
        return np.mean(survivals), np.std(survivals)


# Convenience functions for quick access
def get_uk_mortality(age: int, sex: Literal['male', 'female']) -> float:
    """Get UK general population mortality rate."""
    model = MortalityModel()
    return model.get_annual_mortality_probability(age, sex, has_wet_amd=False)


def get_wet_amd_mortality(
    age: int, 
    sex: Literal['male', 'female'],
    hazard_ratio: Union[Literal['primary', 'conservative', 'high'], float] = 'primary'
) -> float:
    """Get mortality rate for wet AMD patient."""
    model = MortalityModel()
    return model.get_annual_mortality_probability(age, sex, has_wet_amd=True, hazard_ratio=hazard_ratio)


def get_population_weighted_mortality(
    age: int,
    population_type: Literal['clinical_trial', 'real_world', 'frail_elderly'] = 'real_world'
) -> float:
    """Get population-weighted mortality rate for wet AMD patients at given age."""
    pop_model = PopulationMortalityModel()
    result = pop_model.get_population_mortality(age, population_type)
    return result['weighted_annual_mortality']