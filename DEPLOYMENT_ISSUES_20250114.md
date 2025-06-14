# Deployment Issues - January 14, 2025

## Current Status
- **Branch**: deployment (commit e583c02)
- **Environment**: Streamlit Cloud
- **Status**: Working but with issues

## Issues to Address

### 1. Entry Point Problem
**Issue**: Application never opens at the front page (APE.py), always opens at Analysis page
- **Expected**: Should open at the main landing page
- **Actual**: Automatically redirects to pages/3_Analysis.py
- **Impact**: Users miss the main navigation and context
- **Possible causes**:
  - Streamlit Cloud configuration
  - Session state persistence
  - URL routing issue
  - Page navigation logic in APE.py

### 2. Altair Visualization Quality
**Issue**: The new Altair graph in Clinical Workload Analysis is ugly
- **Location**: Tab 6 (Clinical Workload Analysis) in Analysis page
- **Problems**:
  - Poor aesthetics compared to Plotly version
  - Possible issues: colors, spacing, labels, or overall layout
  - May need to apply proper Tufte styling
  - Legend positioning might be off
- **File**: `ape/components/treatment_patterns/workload_visualizations_altair.py`

## TODO
- [ ] Debug why Streamlit Cloud starts at Analysis instead of main page
- [ ] Improve Altair visualization aesthetics
- [ ] Consider A/B testing between Plotly and Altair once both are polished
- [ ] Test performance difference between Plotly and Altair versions

## Notes
- Deployment branch is functional but needs these refinements
- Performance improvement from Altair may not be worth aesthetic trade-off
- Consider keeping both implementations with a feature flag