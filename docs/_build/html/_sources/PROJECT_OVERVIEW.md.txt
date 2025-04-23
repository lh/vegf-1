# Macular Degeneration Treatment Simulation Project

## What is this project?

This project simulates and analyzes treatment pathways for macular degeneration, with a focus on the drug Eylea (aflibercept). It helps researchers understand:

- How different treatment protocols affect patient outcomes
- The relationship between treatment intervals and vision outcomes
- Resource utilization in eye clinics

## Key Concepts

### Simulation Approaches
1. **Agent-Based Simulation (ABS):** Models individual patients and their disease progression
2. **Discrete Event Simulation (DES):** Models clinic operations and resource constraints

### Treatment Protocols
- Pre-defined treatment schedules (loading phase, maintenance phase)
- Rules for adjusting treatment intervals based on patient response

### Data Analysis
- Examines real-world treatment patterns
- Analyzes visual acuity outcomes
- Identifies clusters of similar treatment approaches

## How It Works

1. **Configuration:** Define treatment protocols and simulation parameters in YAML files
2. **Simulation:** Run `run_simulation.py` to generate patient trajectories
3. **Analysis:** Use `run_eylea_analysis.py` to examine treatment patterns and outcomes
4. **Visualization:** Generate plots showing treatment intervals, vision changes, etc.

## Project Structure

- `simulation/`: Core simulation logic (ABS and DES implementations)
- `protocols/`: Treatment protocol definitions
- `analysis/`: Data analysis scripts
- `visualization/`: Plot generation scripts
- `docs/`: Project documentation
- `meta/`: Project planning and documentation notes

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Run a simulation: `python run_simulation.py protocols/simulation_configs/test_simulation.yaml`
3. Analyze results: `python run_eylea_analysis.py`

## Where to Learn More

- Check the [full documentation](docs/_build/html/index.html) for technical details
- See `TESTING.md` for how to run tests
- Examine example config files in `protocols/simulation_configs/`
