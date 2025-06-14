# Research Directory

Active development and analysis work that is not part of the deployed application.

## Structure

- `data_analysis/` - Analysis of real clinical data
  - VEGF treatment outcomes
  - Patient cohort analysis  
  - Statistical modeling
  - Real-world evidence extraction

- `experiments/` - Experimental features and prototypes
  - New visualization approaches
  - Alternative simulation methods
  - Performance experiments
  - UI/UX experiments

- `test_scripts/` - Development and debugging scripts
  - Data validation scripts
  - Performance testing
  - Debug utilities
  - One-off analysis scripts

## Usage Guidelines

1. **Experimental code lives here** until proven and ready for production
2. **Document your experiments** - include README files in subdirectories
3. **Clean up regularly** - move successful experiments to production, failed ones to archive
4. **No production dependencies** - Production code should never import from research/

## Promoting Code to Production

When research code is ready for production:
1. Clean and refactor the code
2. Add proper tests in `/tests`
3. Move to appropriate location in `/ape` or `/visualization`
4. Update imports and documentation
5. Delete or archive the research version

## Current Active Research

- Real patient data analysis for model calibration
- Performance optimization experiments
- New visualization techniques