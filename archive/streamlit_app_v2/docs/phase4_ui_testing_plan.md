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
  - [x] Verify duration is preserved
  - [x] Verify reasonable defaults for rate
- [x] Switch back to Fixed Total
  - [x] Verify duration is preserved
  - [x] Verify patient count returns to previous or default

### 6. Running Simulations
- [x] In Fixed Total mode:
  - [x] Set 100 patients, 1 year
  - [x] Run simulation
  - [x] Verify simulation completes successfully
  - [x] Check saved parameters include recruitment_mode: "Fixed Total"
- [x] In Constant Rate mode:
  - [x] Set 10 patients/week, 1 year
  - [x] Run simulation
  - [x] Verify simulation completes successfully
  - [x] Check saved parameters include:
    - recruitment_mode: "Constant Rate"
    - recruitment_rate: 10
    - rate_unit: "per week"
    - expected_total: ~521

### 7. Edge Cases & Error Handling
- [x] Try to set negative values (should be prevented)
- [x] Try to set zero patients (should show minimum)
- [ ] Verify help tooltips appear on hover  - tooltips above the preset buttons only - is that correct?
- [x] Check layout on different screen sizes
- [x] Verify no console errors in browser - there is often on startup an error "2025-06-13 12:54:06.371 MediaFileHandler: Missing file 74eeb109de3008c033c3b9d64d774d683bf84842d8e315e0bfef76b7.png" but I don't think it is important. There are some javascript errorts in the console related tostreamlit I think - I can show you a screenshot if you want.

### 8. Visual/UX Checks
- [x] Info boxes are clearly visible and readable
- [x] Calculated values update smoothly without flicker
- [x] Radio button selection is clear
- [x] Input fields align properly
- [x] Help text is informative and grammatically correct
- [x] British English spelling is used throughout

### 9. Integration with Analysis
After running simulations in both modes:
- [x] Navigate to Analysis page
- [x] Verify streamgraph shows wedge shape (growing enrollment)
- [x] Check that patient counts grow over time
- [x] Verify final patient count matches expectations

## Known Issues to Watch For
1. Layout issues with columns overlapping
2. Calculated values not updating immediately
3. Mode switching losing user input
4. Preset buttons not updating all fields
5. Runtime estimates being incorrect for Constant Rate mode

## Screenshots to Capture
Please take screenshots of:
1. Fixed Total mode with default values![alt text](<Screenshot 2025-06-13 at 13.21.13.png>)

2. Constant Rate mode with both unit options ![alt text](<Screenshot 2025-06-13 at 13.23.12.png>)
3. The UI after clicking each preset button ![alt text](<Screenshot 2025-06-13 at 13.24.04.png>) ![alt text](<Screenshot 2025-06-13 at 13.23.54.png>) ![alt text](<Screenshot 2025-06-13 at 13.23.50.png>) ![alt text](<Screenshot 2025-06-13 at 13.23.43.png>) ![alt text](<Screenshot 2025-06-13 at 13.24.58.png>)
4. Any layout issues or visual glitches
5. The streamgraph showing proper wedge shape ![alt text](<Screenshot 2025-06-13 at 13.25.40.png>)

## Feedback Needed
- Is the distinction between modes clear? Yes
- Are the calculated values helpful? Yes
- Is the help text sufficient? Yes
- Any confusing aspects of the UI? No
- Suggestions for improvement? It would be useful for all visualisations to have a very basic n patients  t duration somewhere on the page so we can easily se what is what.

---

**Testing Duration**: Approximately 20-30 minutes
**Critical Path**: Fixed Total → Run Simulation → Verify Wedge Shape in Analysis