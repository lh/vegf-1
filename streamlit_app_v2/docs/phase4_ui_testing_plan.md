# Phase 4 UI Testing Plan: Recruitment Modes

## Overview
This document provides a structured testing plan for manually verifying the Phase 4 UI implementation of recruitment modes in the Simulations page.

## Test Environment Setup
1. Start the Streamlit app: `streamlit run APE.py`
2. Navigate to Protocol Manager and ensure a protocol is loaded
3. Navigate to Simulations page

## Test Cases

### 1. Initial State Verification
- [x] Verify "Fixed Total" is selected by default
- [x] Verify default values: 1000 patients, 2.0 years
- [x] Verify calculated rates are displayed in the info box
- [x] Verify the info box shows rates per month and per week

### 2. Fixed Total Mode Testing
- [x] Change patient count to 500
  - [x] Verify rates update automatically
  - [x] Verify calculation is correct (500 / 24 months ≈ 20.8 patients/month)
- [x] Change duration to 5 years
  - [x] Verify rates update automatically
  - [x] Verify calculation is correct (500 / 60 months ≈ 8.3 patients/month)
- [x] Test extreme values:
  - [x] Minimum (10 patients)
  - [x] Maximum (50,000 patients)
  - [x] Very short duration (0.5 years)
  - [x] Very long duration (20 years)

### 3. Constant Rate Mode Testing
- [x] Click "Constant Rate" radio button
- [x] Verify UI changes:
  - [x] "Total Patients" input disappears
  - [x] "Rate Unit" dropdown appears
  - [x] "Patients per week" input appears
  - [x] Info box shows "Expected total" instead of "Calculated rates"
- [x] Test with "per week" unit:
  - [x] Default should be 20 patients/week
  - [x] Verify expected total calculation (20 × 52.14 × 2 ≈ 2,085)
  - [x] Change rate to 50/week, verify total updates
- [x] Test with "per month" unit:
  - [x] Switch dropdown to "per month"
  - [x] Verify input changes to appropriate default (80/month)
  - [x] Verify expected total calculation
  - [x] Note mentions actual count will vary

### 4. Preset Button Testing
- [x] Click "Small Trial" preset
  - [x] Verify switches to Fixed Total mode
  - [x] Verify sets 100 patients, 2 years
- [x] Click "Medium Trial" preset
  - [x] Verify switches to Fixed Total mode
  - [x] Verify sets 500 patients, 3 years
- [x] Click "Large Trial" preset
  - [x] Verify switches to Fixed Total mode
  - [x] Verify sets 2000 patients, 5 years
- [ ] Click "Real-World" preset
  - [ ] Verify switches to Constant Rate mode
  - [ ] Verify sets 20 patients/week, 5 years
  - [ ] Verify shows expected total

### 5. Mode Switching Behavior
- [x] Start in Fixed Total with custom values
- [x] Switch to Constant Rate
  - [ ] Verify duration is preserved BUT interface changes the position of the years column - should be the same. Put the units dropdown below the number of patient, not to the left of it. Also, the number of patients should default to roughly whatever it was when the Fixed total was being used.
  - [ ] Verify reasonable defaults for rate BUT the number of patients should default to roughly whatever it was when the Fixed total was being used.
- [x] Switch back to Fixed Total
  - [x] Verify duration is preserved
  - [ ] Verify patient count returns to previous or default BUT again it should reflect whatever was calculated from the Constant Rate if available

### 6. Running Simulations
- [x] In Fixed Total mode:
  - [x] Set 100 patients, 1 year
  - [x] Run simulation
  - [x] Verify simulation completes successfully
  - [x] Check saved parameters include recruitment_mode: "Fixed Total"
- [ ] In Constant Rate mode: FAILING
  - [x] Set 10 patients/week, 1 year
  - [x] Run simulation
  - [ ] Verify simulation completes successfully FAILING
  - [x] Check saved parameters include:
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