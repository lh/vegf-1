# Phase 4 UI Testing Plan: Recruitment Modes

## Overview
This document provides a structured testing plan for manually verifying the Phase 4 UI implementation of recruitment modes in the Simulations page.

## Test Environment Setup
1. Start the Streamlit app: `streamlit run APE.py`
2. Navigate to Protocol Manager and ensure a protocol is loaded
3. Navigate to Simulations page

## Test Cases

### 1. Initial State Verification
- [ ] Verify "Fixed Total" is selected by default
- [ ] Verify default values: 1000 patients, 2.0 years
- [ ] Verify calculated rates are displayed in the info box
- [ ] Verify the info box shows rates per month and per week

### 2. Fixed Total Mode Testing
- [ ] Change patient count to 500
  - [ ] Verify rates update automatically
  - [ ] Verify calculation is correct (500 / 24 months ≈ 20.8 patients/month)
- [ ] Change duration to 5 years
  - [ ] Verify rates update automatically
  - [ ] Verify calculation is correct (500 / 60 months ≈ 8.3 patients/month)
- [ ] Test extreme values:
  - [ ] Minimum (10 patients)
  - [ ] Maximum (50,000 patients)
  - [ ] Very short duration (0.5 years)
  - [ ] Very long duration (20 years)

### 3. Constant Rate Mode Testing
- [ ] Click "Constant Rate" radio button
- [ ] Verify UI changes:
  - [ ] "Total Patients" input disappears
  - [ ] "Rate Unit" dropdown appears
  - [ ] "Patients per week" input appears
  - [ ] Info box shows "Expected total" instead of "Calculated rates"
- [ ] Test with "per week" unit:
  - [ ] Default should be 20 patients/week
  - [ ] Verify expected total calculation (20 × 52.14 × 2 ≈ 2,085)
  - [ ] Change rate to 50/week, verify total updates
- [ ] Test with "per month" unit:
  - [ ] Switch dropdown to "per month"
  - [ ] Verify input changes to appropriate default (80/month)
  - [ ] Verify expected total calculation
  - [ ] Note mentions actual count will vary

### 4. Preset Button Testing
- [ ] Click "Small Trial" preset
  - [ ] Verify switches to Fixed Total mode
  - [ ] Verify sets 100 patients, 2 years
- [ ] Click "Medium Trial" preset
  - [ ] Verify switches to Fixed Total mode
  - [ ] Verify sets 500 patients, 3 years
- [ ] Click "Large Trial" preset
  - [ ] Verify switches to Fixed Total mode
  - [ ] Verify sets 2000 patients, 5 years
- [ ] Click "Real-World" preset
  - [ ] Verify switches to Constant Rate mode
  - [ ] Verify sets 20 patients/week, 5 years
  - [ ] Verify shows expected total

### 5. Mode Switching Behavior
- [ ] Start in Fixed Total with custom values
- [ ] Switch to Constant Rate
  - [ ] Verify duration is preserved
  - [ ] Verify reasonable defaults for rate
- [ ] Switch back to Fixed Total
  - [ ] Verify duration is preserved
  - [ ] Verify patient count returns to previous or default

### 6. Running Simulations
- [ ] In Fixed Total mode:
  - [ ] Set 100 patients, 1 year
  - [ ] Run simulation
  - [ ] Verify simulation completes successfully
  - [ ] Check saved parameters include recruitment_mode: "Fixed Total"
- [ ] In Constant Rate mode:
  - [ ] Set 10 patients/week, 1 year
  - [ ] Run simulation
  - [ ] Verify simulation completes successfully
  - [ ] Check saved parameters include:
    - recruitment_mode: "Constant Rate"
    - recruitment_rate: 10
    - rate_unit: "per week"
    - expected_total: ~521

### 7. Edge Cases & Error Handling
- [ ] Try to set negative values (should be prevented)
- [ ] Try to set zero patients (should show minimum)
- [ ] Verify help tooltips appear on hover
- [ ] Check layout on different screen sizes
- [ ] Verify no console errors in browser

### 8. Visual/UX Checks
- [ ] Info boxes are clearly visible and readable
- [ ] Calculated values update smoothly without flicker
- [ ] Radio button selection is clear
- [ ] Input fields align properly
- [ ] Help text is informative and grammatically correct
- [ ] British English spelling is used throughout

### 9. Integration with Analysis
After running simulations in both modes:
- [ ] Navigate to Analysis page
- [ ] Verify streamgraph shows wedge shape (growing enrollment)
- [ ] Check that patient counts grow over time
- [ ] Verify final patient count matches expectations

## Known Issues to Watch For
1. Layout issues with columns overlapping
2. Calculated values not updating immediately
3. Mode switching losing user input
4. Preset buttons not updating all fields
5. Runtime estimates being incorrect for Constant Rate mode

## Screenshots to Capture
Please take screenshots of:
1. Fixed Total mode with default values
2. Constant Rate mode with both unit options
3. The UI after clicking each preset button
4. Any layout issues or visual glitches
5. The streamgraph showing proper wedge shape

## Feedback Needed
- Is the distinction between modes clear?
- Are the calculated values helpful?
- Is the help text sufficient?
- Any confusing aspects of the UI?
- Suggestions for improvement?

---

**Testing Duration**: Approximately 20-30 minutes
**Critical Path**: Fixed Total → Run Simulation → Verify Wedge Shape in Analysis