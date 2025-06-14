# APE: AMD Protocol Explorer

🦍 **APE** (AMD Protocol Explorer) is a comprehensive simulation and analysis platform for Age-related Macular Degeneration (AMD) treatment protocols, focusing on anti-VEGF therapies. This scientific tool enables researchers and clinicians to model disease progression, analyze treatment outcomes, and visualize results through an intuitive Streamlit interface.

## Key Features

### 🔬 Simulation Engine
- **Dual Simulation Modes**: Agent-based (ABS) and Discrete Event Simulation (DES) models
- **Realistic Patient Modeling**: Individual patient trajectories with disease progression
- **Protocol Flexibility**: YAML-based configuration for any treatment protocol
- **Stochastic Modeling**: Captures real-world variability in treatment response

### 📊 Analysis & Visualization
- **Comprehensive Analytics**: Treatment intervals, visual acuity outcomes, discontinuation patterns
- **Tufte-Inspired Visualizations**: Clean, data-focused charts following best practices
- **Interactive Explorations**: Patient-level and population-level insights
- **Export Capabilities**: Multiple formats (PNG, SVG, WebP) with configurable quality

### 🚀 User Interface
- **Streamlit Dashboard**: Modern, responsive web interface
- **Protocol Manager**: Create and manage treatment protocols
- **Real-time Simulations**: Run and monitor simulations with progress tracking
- **Memory Management**: Automatic caching and efficient data handling

## Development

### Project Organization
The repository uses a hybrid structure with production code at the root and research/development work in dedicated directories. See `docs/development/WHERE_TO_PUT_THINGS.md` for detailed guidelines on file placement.

### Git Worktrees for Parallel Development
Work on multiple features simultaneously:
```bash
git worktree add ../CC-feature -b feature/new-feature
./scripts/dev/worktree-status.sh  # Check all worktrees
```

### Testing
```bash
# Run tests
pytest tests/

# Run pre-commit checks
./scripts/check_root_cleanliness.sh
```

## Documentation

Comprehensive documentation is available at: [https://lh.github.io/vegf-1/](https://lh.github.io/vegf-1/)

Includes:
- Detailed simulation model descriptions
- Protocol configuration guides
- API reference
- Analysis examples

## Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/vegf-1.git
cd vegf-1

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run APE.py
```

### Docker Deployment
```bash
# Build and run with Docker
docker build -t ape-app .
docker run -p 8501:8501 ape-app
```

## Repository Structure

This repository uses a hybrid structure that separates production code from research and development:

### Production Code (Deployed)
```
├── APE.py                    # Main application entry point
├── pages/                    # Streamlit pages
│   ├── 1_Protocol_Manager.py # Protocol creation and management
│   ├── 2_Simulations.py      # Run and monitor simulations
│   └── 3_Analysis.py         # Analyze and visualize results
├── ape/                      # Core application modules
│   ├── components/           # UI components and simulation I/O
│   ├── core/                 # Simulation engines (ABS/DES)
│   ├── utils/                # Utilities and helpers
│   └── visualizations/       # Visualization modules
├── protocols/                # Treatment protocol configurations (YAML)
├── visualization/            # Visualization system
│   └── color_system.py       # Centralized color definitions
├── assets/                   # Images and static files
└── .streamlit/              # Streamlit configuration
```

### Research & Development (Not Deployed)
```
├── research/                 # Active research work
│   ├── data_analysis/        # Real patient data analysis
│   ├── experiments/          # Prototype features
│   └── test_scripts/         # Development utilities
├── tests/                    # Comprehensive test suite
├── paper/                    # Academic paper materials
├── archive/                  # Historical/deprecated code
│   ├── legacy_apps/          # Old Streamlit implementations
│   └── old_docs/             # Outdated documentation
├── meta/                     # Project metadata
│   ├── planning/             # Design documents
│   └── postmortems/          # Learning documentation
└── docs/                     # Current documentation
```

The `.streamlitignore` file ensures only production code is deployed to Streamlit Cloud.

## Important: Scientific Integrity

**This is a scientific analysis tool, not a demo.** The following principles are non-negotiable:

- **No Synthetic Data**: All visualizations use only real simulation data
- **Data Conservation**: Patient counts and states are rigorously tracked
- **Transparent Calculations**: All transformations are documented and verifiable
- **Fail Fast**: Missing data causes clear errors, never silent substitution

See `CLAUDE.md` for detailed development principles.

## Contributing

Contributions are welcome! Please:
1. Read `WHERE_TO_PUT_THINGS.md` before adding files
2. Run tests before committing: `pytest tests/`
3. Follow the scientific integrity principles in `CLAUDE.md`
4. Use git worktrees for feature development

## Available Protocols

- **Eylea 2mg**: Standard treat-and-extend protocol
- **Eylea 8mg**: High-dose formulation with extended intervals
- **Aflibercept 2mg**: Flexible dosing schedules
- **Treat & Extend**: Adaptive interval management

Protocols are defined in YAML format in the `protocols/` directory.

## Related Documentation

- `docs/deployment/DEPLOYMENT_GUIDE.md` - Production deployment instructions
- `docs/development/WHERE_TO_PUT_THINGS.md` - Directory organization guide  
- `meta/planning/GIT_WORKTREE_STRATEGY.md` - Parallel development workflow
- `CLAUDE.md` - AI assistant instructions and development principles
- API Documentation: [https://lh.github.io/vegf-1/](https://lh.github.io/vegf-1/)

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
