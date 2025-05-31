# Discontinuation Profiles

This directory contains discontinuation profile configurations for the V2 AMD simulation.

## Available Profiles

### ideal.yaml
- Perfect world scenario with no administrative errors
- Only includes clinically-driven discontinuations
- Lower premature discontinuation rate (5% vs 14.5%)
- No system failures or funding lapses

### nhs_1.yaml
- Real-world UK NHS unit parameters
- Includes all discontinuation types
- Based on clinical data and real-world experience
- 14.5% premature discontinuation rate (from Eylea analysis)
- 5% annual administrative loss rate
- 10% reauthorization failure rate after 1 year

## Profile Structure

Each profile contains:

1. **Categories**: The 6 discontinuation types
   - `stable_max_interval`: Protocol-based discontinuation
   - `poor_response`: Treatment failure (VA < 15 letters)
   - `premature`: Patient-initiated discontinuation
   - `system_discontinuation`: Administrative loss to follow-up
   - `reauthorization_failure`: Funding renewal failure
   - `mortality`: Patient death

2. **Monitoring Schedules**: Post-discontinuation follow-up
   - `planned`: Standard monitoring (12, 24, 36 weeks)
   - `unplanned`: Frequent monitoring (8, 16, 24 weeks)
   - `poor_response`: No monitoring (discharged)
   - `mortality`: No monitoring
   - `system`: No monitoring (lost to follow-up)

3. **Retreatment Criteria**: When to restart treatment
   - Fluid detection required
   - Minimum 5 letter vision loss
   - 95% probability when criteria met
   - 87% detection probability

4. **Recurrence Rates**: Disease recurrence probabilities
   - Based on clinical literature (Arendt, Aslanis, Artiaga studies)
   - Time-dependent rates at 1, 3, and 5 years
   - Varies by discontinuation type

## Creating Custom Profiles

To create a custom profile:

1. Copy an existing profile as a template
2. Modify the parameters as needed
3. Ensure all required categories are present
4. Validate using `DiscontinuationProfile.validate()`

Example:
```python
from simulation_v2.core.discontinuation_profile import DiscontinuationProfile
from pathlib import Path

# Load custom profile
profile = DiscontinuationProfile.from_yaml(Path("custom.yaml"))

# Validate
errors = profile.validate()
if errors:
    print("Validation errors:", errors)
```

## Usage in Simulation

```python
from simulation_v2.core.discontinuation_manager import V2DiscontinuationManager
from simulation_v2.core.discontinuation_profile import DiscontinuationProfile
from pathlib import Path

# Load a specific profile
profile = DiscontinuationProfile.from_yaml(
    Path("simulation_v2/profiles/discontinuation/nhs_1.yaml")
)

# Create manager with profile
manager = V2DiscontinuationManager(profile)

# Use in simulation...
```

## Parameter Sources

- **Arendt study**: Protocol-based discontinuation outcomes
- **Aslanis study**: Premature discontinuation and PED impact
- **Artiaga study**: Long-term (5yr) recurrence data
- **Eylea analysis**: Real-world premature discontinuation patterns (14.5% rate)
- **Clinical experience**: Administrative loss and reauthorization failure rates
- **Mortality**: Placeholder 20/1000 annual rate pending analysis