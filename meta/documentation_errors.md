# Documentation Build Errors

## Last Build: 2025-04-22

### Critical Errors:
1. Import errors in simulation modules (clinical_model, config, patient_state, scheduler):
   - Error: "No module named 'protocol_parser'"
   - Likely need to update imports after moving protocol_parser.py

### Warnings:
1. Title underline too short in:
   - docs/analysis/eylea_data_analysis.rst
   - docs/analysis/eylea_intervals_analysis.rst  
   - docs/analysis/index.rst
   - docs/index.rst (Visualization Modules section)
   - docs/protocols/visit_types.rst
   - docs/simulation/clinical_model.rst
   - docs/simulation/config.rst
   - docs/simulation/index.rst

2. Duplicate object descriptions in:
   - analysis/eylea_data_analysis.py
   - analysis/eylea_intervals_analysis.py
   - protocols/config_parser.py
   - protocols/protocol_parser.py

3. Unexpected indentation in docstrings:
   - analysis/eylea_data_analysis.py (plot_injection_intervals, plot_va_change_distribution)

### Next Steps:
1. Fix protocol_parser import errors
2. Extend title underlines in RST files
3. Add :no-index: to duplicate object descriptions
4. Fix docstring indentation

## OCT Scan Implementation Note
- OCT scans are performed but results are not currently available in the simulation
- Future implementation should:
  - Add time/cost for OCT scans
  - Include OCT results in visit data
  - Use OCT results to inform treatment decisions
