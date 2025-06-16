# Simulation Results Summary

## Key Findings

### Time-Based vs Standard Model Comparison

#### 1. Vision Outcomes
- **Time-based model shows worse vision outcomes in longer simulations**
  - 1 year: Time-based 60.6 vs Standard 67.3 letters
  - 2 years: Time-based 55.9 vs Standard 64.4 letters  
  - 3 years: Time-based 51.4 vs Standard 61.7 letters
- The gap widens with longer duration due to continuous disease progression

#### 2. Injection Burden
- **Time-based model requires MORE injections due to loading dose**
  - 1 year: Time-based 437 vs Standard 368 injections
  - 2 years: Time-based 3,074 vs Standard 2,842 injections
  - 3 years: Time-based 7,635 vs Standard 7,300 injections
- Loading dose adds ~3 injections per patient upfront

#### 3. Discontinuation Rates
- **Time-based model shows lower discontinuation in shorter trials**
  - 1 year: Both 0%
  - 2 years: Time-based 0% vs Standard 1.01%
  - 3 years: Time-based 1.52% vs Standard 3.05%
- Poor vision threshold not being reached as quickly in time-based

## Available Simulations for Visualization

### Small (100 patients, 1 year)
- **Time-based**: `sim_20250616_131154_01-00_silent-mode`
- **Standard**: `sim_20250616_131154_01-00_sparkling-sunset`

### Medium (500 patients, 2 years)
- **Time-based**: `sim_20250616_131154_02-00_rough-flower`
- **Standard**: `sim_20250616_131154_02-00_tight-block`

### Large (1000 patients, 3 years)
- **Time-based**: `sim_20250616_131154_03-00_wispy-cell`
- **Standard**: `sim_20250616_131154_03-00_frosty-block`

## Key Differences to Look For

1. **Calendar-Time Analysis**
   - Loading dose phase clearly visible in first 3 months
   - Different treatment interval patterns after loading

2. **Patient Explorer**
   - Individual vision trajectories show more gradual decline
   - Fortnightly updates create smoother curves

3. **State Distributions**
   - Disease states evolve more gradually in time-based
   - Less correlation with visit frequency

4. **Treatment Patterns**
   - Front-loaded injection schedule in time-based
   - Different extension patterns after loading phase

## Model Characteristics

### Time-Based Model
- Disease updates every 14 days for ALL patients
- Vision changes continuously between visits
- Loading dose: 3 monthly injections
- Vision measured with ±5 letter noise at visits
- Treatment decisions based on last measured vision

### Standard Model  
- Disease updates only at visits
- Vision changes only at visits
- No loading dose requirement
- Direct vision-disease state correlation
- Visit frequency affects progression rate