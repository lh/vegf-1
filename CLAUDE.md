# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
APE (AMD Protocol Explorer) is a scientific simulation platform for Age-related Macular Degeneration treatment protocols. It uses Agent-Based Simulation (ABS) and Discrete Event Simulation (DES) to model patient pathways through anti-VEGF treatments.

## Key Commands

### Running the Application
```bash
# Main Streamlit application
streamlit run APE.py

# Development server with hot reload
streamlit run APE.py --server.runOnSave true
```

### Testing
```bash
# Run all tests except known failures
./scripts/run_tests.sh

# Run all tests including known failures
python -m pytest tests/

# Run specific test file
python -m pytest tests/unit/test_clinical_model.py

# Run tests with coverage
python -m pytest --cov=simulation --cov=ape tests/

# Run UI tests
cd tests/ui && ./run_ui_tests.sh
```

### Code Quality
```bash
# Format code with black
black .

# Sort imports
isort .

# Lint with flake8
flake8 .

# Type checking
mypy simulation/ ape/

# Run all quality checks
black . && isort . && flake8 . && mypy simulation/ ape/
```

### Development Tools
```bash
# Check root cleanliness (should be < 30 files)
./scripts/check_root_cleanliness.sh

# Git worktree status
./scripts/dev/worktree-status.sh

# Create new worktree for feature
git worktree add ../CC-feature-name -b feature/branch-name
```

## Architecture Overview

### Simulation Engines
The project supports two simulation paradigms:

1. **Agent-Based Simulation (ABS)** - `simulation/abs.py`
   - Each patient is an autonomous agent
   - Individual state tracking and decision making
   - Protocol-driven visit scheduling
   - Key classes: `Patient`, `AgentBasedSimulation`

2. **Discrete Event Simulation (DES)** - `simulation/des.py`
   - Event queue-driven simulation
   - Efficient for large populations
   - Same protocol compatibility as ABS

### Core Components

#### Patient State Management
- `simulation/patient_state.py` - Core patient state tracking
- `simulation/patient_state_enhanced.py` - Enhanced state with discontinuation flags
- Tracks: vision, disease state, treatment history, discontinuation status

#### Clinical Models
- `simulation/clinical_model.py` - Treatment decision logic
- `simulation/vision_models.py` - Vision progression modeling
- `simulation/discontinuation_manager.py` - Discontinuation criteria

#### Protocol System
- `protocols/protocol_models.py` - Protocol phase definitions
- `protocols/config_parser.py` - YAML protocol parsing
- Protocol phases: Loading → Maintenance → Extension → Discontinuation

#### Economics Integration
- `simulation/economics/` - Cost tracking and analysis
- `simulation_v2/economics/` - Enhanced v2 economics
- Tracks: drug costs, visit costs, monitoring costs

### Streamlit UI Structure
```
APE.py                    # Main entry point
pages/
├── 1_Protocol_Manager.py # Protocol CRUD operations
├── 2_Simulations.py      # Run simulations
├── 3_Analysis.py         # Analyze results
└── 4_Simulation_Comparison.py # Compare protocols

ape/
├── components/           # UI components
│   ├── simulation_ui.py  # Simulation runner UI
│   └── simulation_io.py  # Import/export functionality
├── utils/               # UI utilities
│   ├── chart_builder.py # Visualization builder
│   └── style_constants.py # Consistent styling
└── visualizations/      # Streamgraph implementations
```

### Data Flow
1. **Protocol Definition** → YAML files in `protocols/`
2. **Patient Generation** → Based on distribution parameters
3. **Simulation Run** → ABS/DES engine processes patients
4. **Results Storage** → Parquet format with metadata
5. **Visualization** → Tufte-style charts and streamgraphs

## Critical Development Principles

### Scientific Integrity
- **NEVER generate synthetic data** - fail fast on missing data
- **No silent fallbacks** - explicit errors over hidden issues
- **Data conservation** - patient counts must remain constant
- **Real data only** - no mock/fake/dummy data in production

### File Organization
- **Use `workspace/`** for temporary development
- **Never clutter root** - use appropriate subdirectories
- **Output goes to `output/`** - this directory is gitignored
- See `WHERE_TO_PUT_THINGS.md` for complete guide

### Testing Requirements
- All new features need tests
- Use `@pytest.mark.known_failure` for WIP tests
- Verify both ABS and DES compatibility
- Check visualizations produce real data

### Memory and Performance
- Use vectorized pandas operations for large datasets
- Session state persistence across Streamlit pages
- Efficient parquet storage for simulation results
- Progress indicators for long-running operations

## Current Feature: ABS Engine Heterogeneity

You are on branch `feature/abs-engine-heterogeneity` to implement patient heterogeneity in the ABS engine.

Key areas to consider:
- `simulation/abs.py` - Core ABS implementation
- `simulation/patient_state.py` - Patient state definitions
- `simulation/patient_generator.py` - Patient generation logic
- `protocols/distributions/` - Population distribution configs

Heterogeneity dimensions might include:
- Vision response variability
- Treatment adherence patterns
- Disease progression rates
- Discontinuation thresholds
- Geographic/demographic factors

## Visualization Standards
- Y-axis for VA plots: 0-85 ETDRS letters
- X-axis: yearly intervals (0, 12, 24, 36, 48, 60 months)
- Follow Tufte principles (see `meta/visualization_templates.md`)
- Use central color system (`visualization/color_system.py`)
- No synthetic smoothing - show real data patterns

## Git Workflow
- Commit frequently with clear messages
- No attribution in commits (no "Generated with Claude")
- Use PR templates when creating pull requests
- Include issue numbers in commit messages
- Push changes regularly in development environment

## Troubleshooting
- Port conflicts: Use alternate ports (8503, 8504) for testing
- Playwright debugging: `node playwright_debug_configurable.js [port]`
- Memory issues: Check `output/` directory size
- Slow performance: Use vectorized operations, not loops

## Documentation
- API docs: https://lh.github.io/vegf-1/
- Deployment guide: `docs/deployment/DEPLOYMENT_GUIDE.md`
- Clinical summaries: `meta/clinical_summaries/`
- Planning docs: `meta/planning/`