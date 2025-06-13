# Carbon Button Migration Tracker

## Status Legend
- 🟢 Complete
- 🟡 In Progress
- 🔴 Not Started
- ⚠️ Needs Review

## Migration Progress

### Day 0: Test Infrastructure Setup ✅
- [x] Create feature branch: `feature/carbon-buttons`
- [x] Install Playwright and set up test configuration
- [x] Create baseline tests for ALL existing buttons
- [x] Verify Carbon button compatibility (Streamlit 1.45.1 ✓)
- [x] Test Carbon button installation in isolated environment
- [ ] Run baseline tests and save screenshots
- [ ] Document all existing button locations and types
- [ ] Create button inventory spreadsheet

### Day 1: Baseline Test Creation
- [ ] Set up Playwright test infrastructure
- [ ] Create baseline tests for navigation buttons
- [ ] Create baseline tests for form actions
- [ ] Run all tests and save baseline screenshots
- [ ] Create performance baseline tests
- [ ] Create accessibility baseline tests
- [ ] Document all button behaviors in test reports
- [ ] Commit all tests to version control

## File Status

### Main Application
| File | Status | Notes | Reviewer |
|------|--------|-------|----------|
| APE.py | 🔴 | Main navigation | - |
| requirements.txt | 🔴 | Add carbon dependency | - |

### Pages
| File | Status | Notes | Reviewer |
|------|--------|-------|----------|
| pages/1_Protocol_Manager.py | 🔴 | Complex forms | - |
| pages/2_Run_Simulation.py | 🔴 | Primary actions | - |
| pages/3_Analysis_Overview.py | 🔴 | Export buttons | - |
| pages/4_Experiments.py | 🔴 | If exists | - |

### Components
| File | Status | Notes | Reviewer |
|------|--------|-------|----------|
| components/treatment_patterns/enhanced_tab.py | 🔴 | Export actions | - |
| components/treatment_patterns/interval_analyzer.py | 🔴 | Check for buttons | - |
| components/treatment_patterns/pattern_analyzer.py | 🔴 | Check for buttons | - |
| components/treatment_patterns/sankey_builder.py | 🔴 | Check for buttons | - |

### Utilities
| File | Status | Notes | Reviewer |
|------|--------|-------|----------|
| utils/carbon_button_helpers.py | 🔴 | To be created | - |
| utils/button_styling.py | 🔴 | To be removed | - |
| utils/export_config.py | 🔴 | Export buttons | - |
| utils/style_constants.py | 🔴 | Remove button styles | - |

### Test Infrastructure
| File | Status | Notes | Reviewer |
|------|--------|-------|----------|
| package.json | 🟢 | Created | - |
| playwright.config.ts | 🟢 | Created | - |
| tests/playwright/helpers/streamlit-page.ts | 🟢 | Created | - |
| tests/playwright/helpers/button-inventory.ts | 🟢 | Created | - |
| tests/playwright/baseline/* | 🟢 | Tests created | - |
| tests/playwright/visual/* | 🟢 | Tests created | - |
| tests/playwright/accessibility/* | 🟢 | Tests created | - |
| tests/playwright/performance/* | 🟢 | Tests created | - |

## Button Inventory

### Navigation Buttons
- [ ] Home (all pages)
- [ ] Protocol Manager nav
- [ ] Run Simulation nav
- [ ] Analysis Overview nav
- [ ] Back/Forward buttons

### Action Buttons
- [ ] Save Protocol (primary)
- [ ] Load Protocol
- [ ] Delete Protocol (danger)
- [ ] Run Simulation (primary, full-width)
- [ ] Reset Parameters
- [ ] Stop Simulation

### Export Buttons
- [ ] Export PNG
- [ ] Export SVG
- [ ] Export JPEG
- [ ] Export WebP
- [ ] Export Data (CSV)

### Form Buttons
- [ ] Submit forms
- [ ] Cancel actions
- [ ] Reset forms

## Testing Checklist
- [ ] All buttons have unique keys
- [ ] Icon-only buttons have aria-labels
- [ ] Session state preserved
- [ ] No visual regressions
- [ ] Performance acceptable
- [ ] Accessibility improved

## Test Results Summary
- Baseline Tests: Not yet run
- Visual Tests: Not yet run
- Accessibility Tests: Not yet run
- Performance Tests: Not yet run

## Notes
- Carbon button compatibility verified with Streamlit 1.45.1
- Test infrastructure created and ready for baseline capture
- Next step: Run baseline tests to document current behavior