# Batch Simulation Design and Random Seed Strategy

## Overview

The batch simulation system allows running multiple treatment protocol simulations for comparison. This document explains the statistical design choices, particularly regarding random seed management.

## Random Seed Strategy: Paired Comparison Design

### Current Implementation

**All protocols in a batch use the SAME random seed.**

For example, if batch parameters specify `seed=42`:
- Protocol A runs with `seed=42`
- Protocol B runs with `seed=42`
- Protocol C runs with `seed=42` (future)

### Rationale

This implements a **paired comparison design** where each protocol is tested on identical patient populations.

#### Advantages

1. **Reduced Variance**: Patient characteristics are held constant across protocols
2. **Increased Statistical Power**: Differences are easier to detect
3. **Isolates Protocol Effect**: Removes patient population as a confounding variable
4. **Smaller Sample Sizes**: Fewer patients needed to achieve significance
5. **Clearer Interpretation**: Differences are purely due to protocol, not population

#### What This Means

When `seed=42` is used:
```python
# Protocol A with seed=42 generates:
Patient_1: baseline_vision=65, age=72, progression_rate=0.8
Patient_2: baseline_vision=58, age=68, progression_rate=1.2
Patient_3: baseline_vision=70, age=75, progression_rate=0.9
...

# Protocol B with seed=42 generates THE SAME patients:
Patient_1: baseline_vision=65, age=72, progression_rate=0.8  # Same!
Patient_2: baseline_vision=58, age=68, progression_rate=1.2  # Same!
Patient_3: baseline_vision=70, age=75, progression_rate=0.9  # Same!
...
```

**This is intentional and correct.**

### Statistical Analysis

The paired design enables more powerful statistical tests:

```python
# Instead of independent t-test:
t_test_ind(protocol_a_outcomes, protocol_b_outcomes)  # Less power

# Use paired t-test:
t_test_rel(protocol_a_outcomes, protocol_b_outcomes)  # More power!
```

Or for each patient:
```python
difference = protocol_a_outcome[patient_i] - protocol_b_outcome[patient_i]
# Analyze distribution of differences
```

## Alternative Design: Independent Populations

### When to Use Different Seeds

If you want to test protocol **robustness** across different patient populations:

```python
# Protocol A: seed=42
# Protocol B: seed=43  # Different population
```

#### Trade-offs

**Advantages:**
- Tests generalizability across populations
- More realistic representation of real-world uncertainty
- Better for regulatory submissions

**Disadvantages:**
- Higher variance in outcomes
- Requires larger sample sizes (typically 2-3× more patients)
- Harder to detect small but meaningful differences
- Results may be due to population differences, not protocol

### Not Currently Implemented

The current batch system does NOT support this mode because:
1. Paired comparison is more appropriate for protocol optimization
2. Independent comparison requires multiple replications (N > 1)
3. Statistical analysis is more complex

## Future Enhancement: Multiple Replications

When the system supports running N replications per protocol, the recommended strategy is:

```python
# Run each protocol N times with different seeds
# BUT use the same seed sequence across protocols

Protocol A replications:
  Run 1: seed = 42
  Run 2: seed = 43
  Run 3: seed = 44

Protocol B replications:
  Run 1: seed = 42  # Same patients as Protocol A Run 1
  Run 2: seed = 43  # Same patients as Protocol A Run 2
  Run 3: seed = 44  # Same patients as Protocol A Run 3
```

This gives you **both**:
1. Paired comparisons within each replication (low variance)
2. Variance estimates across replications (robustness)
3. Best of both worlds!

## Random Number Generator Quality

### Current Implementation

The system uses Python's standard random number generators:
- `random.seed(seed)` - Mersenne Twister (MT19937), period 2^19937-1
- `np.random.seed(seed)` - NumPy's MT19937 implementation

### Is This Adequate?

**Yes, for medical simulations this is more than adequate.**

The Mersenne Twister:
- Has excellent statistical properties
- Very long period (2^19937-1)
- Passes stringent randomness tests
- Industry standard for simulation studies

### When Would You Need More?

You would only need a more robust generator if:
1. Cryptographic security is required (NOT the case here)
2. Simulations run for periods approaching 2^19937 samples (impossible)
3. You're doing specialized Monte Carlo work requiring specific properties

### If You Want Overkill

If you want even more robustness, you could use:

```python
# Instead of:
random.seed(seed)
np.random.seed(seed)

# Use:
rng = np.random.Generator(np.random.PCG64(seed))
```

PCG64 is a newer generator with:
- Faster performance
- Better statistical properties
- Longer period (2^128)

**But this is not necessary for your use case.**

## Implementation Details

### Where Seeds Are Set

1. **Batch Runner** (`ape/batch/runner.py`):
   - Takes single seed from command line args
   - Passes same seed to each protocol simulation

2. **Simulation Runner** (`simulation_v2/core/simulation_runner.py`):
   - Receives seed parameter
   - Passes to engine

3. **Engine** (`simulation_v2/engines/abs_engine.py`):
   ```python
   if seed is not None:
       random.seed(seed)
       np.random.seed(seed)
   ```

4. **Disease Model** (`simulation_v2/core/disease_model.py`):
   ```python
   if seed is not None:
       random.seed(seed)
   ```

### Seed Reset Behavior

**Each simulation DOES reset the global random state.**

This means:
- Simulation 1 with seed=42 → reproducible results
- Simulation 2 with seed=42 → identical results to Simulation 1
- This is correct and desired behavior

## Recommendations

### For Current Batch System

✅ **Keep current implementation** - same seed for all protocols is correct

### For Future Development

When adding multiple replications:

```python
def run_batch(protocols, n_patients, duration, base_seed, n_replications=1):
    results = {}

    for rep in range(n_replications):
        seed = base_seed + rep

        for protocol in protocols:
            # Same seed for all protocols in this replication
            sim_results = run_simulation(protocol, n_patients, duration, seed)
            results[(protocol, rep)] = sim_results

    return results
```

### For Documentation

✅ Document the paired comparison design clearly (this file)
✅ Explain why same seed is used (this file)
✅ Add inline comments in code (completed)

## References

### Paired Comparison Design

- Rosner B. Fundamentals of Biostatistics. 8th ed. Chapter 8: Hypothesis Testing: Two-Sample Inference
- Montgomery DC. Design and Analysis of Experiments. 9th ed. Chapter 5: Introduction to Factorial Designs

### Random Number Generation

- Matsumoto M, Nishimura T. "Mersenne Twister: A 623-dimensionally equidistributed uniform pseudo-random number generator." ACM TOMACS 1998.
- O'Neill ME. "PCG: A Family of Simple Fast Space-Efficient Statistically Good Algorithms for Random Number Generation." 2014.

## Summary

The current batch simulation system correctly implements a paired comparison design by using the same random seed for all protocols. This is:

1. ✅ Statistically sound
2. ✅ Increases statistical power
3. ✅ Standard practice for controlled comparisons
4. ✅ Uses adequate random number generators
5. ✅ Well-documented

No changes are needed to the random seed strategy.
