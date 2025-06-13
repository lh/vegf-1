# Simulation Naming Improvement Proposal

## Current Format
`APE_sim_YYYYMMDD_HHMMSS_XXXXXXXX.zip`

Example: `APE_sim_20250607_120000_a1b2c3d4.zip`

## Proposed Format
`APE_sim_YYYYMMDD_HHMMSS_YY-FF_MEMORABLE-NAME.zip`

Where:
- `YY-FF` = Duration encoding (years-fractional)
  - `00-50` = 0.5 years
  - `02-00` = 2.0 years
  - `10-00` = 10.0 years
  - `05-50` = 5.5 years
- `MEMORABLE-NAME` = Human-friendly identifier

Examples:
- `APE_sim_20250607_120000_02-00_autumn-surf.zip` (2 year simulation)
- `APE_sim_20250607_143000_00-50_fluffy-rabbit.zip` (6 month simulation)
- `APE_sim_20250607_160000_10-00_gentle-breeze.zip` (10 year simulation)

## Benefits

1. **Duration Visibility**: Immediately see simulation duration without opening
2. **Comparison Ready**: Easy to identify simulations with matching durations
3. **Human Memorable**: Names like "autumn-surf" are easier to remember than hex codes
4. **Unique but Friendly**: Still unique but more approachable

## Implementation Options

### Option 1: Haikunator (Recommended)
```python
from haikunator import Haikunator

haikunator = Haikunator()
name = haikunator.haikunate(token_length=0)  # "autumn-surf"
```

**Pros**:
- Nature-themed, pleasant names
- Configurable format
- No numbers by default (cleaner)

### Option 2: Petname
```python
import petname

name = petname.generate(words=2, separator='-')  # "fluffy-rabbit"
```

**Pros**:
- Animal-themed, friendly names
- Simple API
- Consistent format

### Option 3: Custom Word Lists
```python
import random

adjectives = ['gentle', 'swift', 'bright', 'calm', 'eager']
nouns = ['wave', 'star', 'moon', 'river', 'mountain']
name = f"{random.choice(adjectives)}-{random.choice(nouns)}"
```

**Pros**:
- Full control over vocabulary
- Domain-specific terms possible
- No external dependencies

## Duration Encoding Function

```python
def encode_duration(duration_years: float) -> str:
    """
    Encode duration as YY-FF format.

    Examples:
        0.5 -> "00-50"
        2.0 -> "02-00"
        5.5 -> "05-50"
        10.0 -> "10-00"
    """
    years = int(duration_years)
    fraction = int((duration_years - years) * 100)
    return f"{years:02d}-{fraction:02d}"
```

## Updated Package Naming

```python
def generate_package_name(sim_id: str, duration_years: float) -> str:
    """Generate human-friendly package name with duration encoding."""
    # Extract timestamp from sim_id
    # sim_id format: sim_YYYYMMDD_HHMMSS_XXXXXXXX
    parts = sim_id.split('_')
    date_part = parts[1]
    time_part = parts[2]

    # Encode duration
    duration_code = encode_duration(duration_years)

    # Generate memorable name
    haikunator = Haikunator()
    memorable_name = haikunator.haikunate(token_length=0)

    # Construct filename
    return f"APE_sim_{date_part}_{time_part}_{duration_code}_{memorable_name}.zip"
```

## example implementation - would need names list so we don't duplicate

```python
from coolname import generate_slug
import time

used_names = set()

def get_unique_name(words=3):
    while True:
        name = generate_slug(words)
        if name not in used_names:
            used_names.add(name)
            return name
```

## Migration Path

1. **Phase 1**: Add duration encoding to existing hex format
   - `APE_sim_20250607_120000_02-00_a1b2c3d4.zip`

2. **Phase 2**: Replace hex with memorable names for new exports
   - Old simulations keep hex codes
   - New exports get memorable names

3. **Phase 3**: Optional rename tool for existing packages
   - Utility to rename old packages with memorable names

## Considerations

1. **Uniqueness**: While memorable names are less unique than UUIDs, the timestamp provides uniqueness
2. **Sorting**: Files still sort chronologically due to timestamp prefix
3. **Dependencies**: Requires adding `haikunator` or `petname` to requirements.txt
4. **Backwards Compatibility**: Parser should handle both old and new formats

## Example Implementation Location

In `utils/simulation_package.py`:

```python
def create_package(self, results: 'SimulationResults',
                  output_path: Optional[Path] = None) -> bytes:
    """Create simulation package from results"""
    sim_id = results.metadata.sim_id
    duration_years = results.metadata.duration_years

    # Generate new-style package name
    package_name = generate_package_name(sim_id, duration_years)

    # ... rest of implementation
```

## Testing

Add tests to verify:
- Duration encoding works correctly for various inputs
- Memorable names are generated
- Package names are unique (timestamp + name combination)
- Parser handles both old and new formats