# Simulation Import/Export Implementation Plan

## Current State (2025-01-26)

### What's Been Done
- ✅ Core functionality implemented (`utils/simulation_package.py`)
- ✅ Security measures in place (zip bomb protection, path traversal prevention)
- ✅ Tests written for package manager functionality
- ✅ UI components created but misplaced in `pages/` directory

### What's Broken
- ❌ Export shows "No simulation selected" despite simulation being displayed
- ❌ Component files in `pages/` create blank routes (`/analysis_overview_export`, `/protocol_manager_import`)
- ❌ Export functionality in wrong location (Analysis Overview → Audit Trail)
- ❌ Import functionality in wrong location (Protocol Manager)
- ❌ No end-to-end testing of actual UI integration

## Implementation Plan

### Phase 1: File Structure Cleanup
1. **Create proper component structure**
   ```
   components/
   ├── export.py      # Export simulation functionality
   └── import.py      # Import simulation functionality
   ```

2. **Remove misplaced files**
   - Delete `pages/analysis_overview_export.py`
   - Delete `pages/protocol_manager_import.py`

### Phase 2: Update UI Consistency
1. **Protocol Manager**: Change Manage button icon from `settings` to `save` (floppy disk)
2. **Button strategy**:
   - Carbon buttons for: Manage button, Run Simulation, navigation
   - Streamlit native for: Download button (export), File uploader (import)
   - Style native buttons to match minimal aesthetic

### Phase 3: Create Unified Simulations Page

#### Page Structure
```
Simulations (renamed from "Run Simulation")
├── Recent Simulations List
│   └── Shows local simulation results with timestamps
├── Simulation Parameters (existing)
│   ├── Quick Presets
│   └── Parameter inputs
└── Action Buttons
    ├── [💾 Manage] (Carbon button with floppy disk)
    └── [▶️ Run Simulation] (Carbon button)
    
Manage Section (collapsible):
├── 📤 Export Current Simulation
│   └── st.download_button (styled)
└── 📥 Import Simulation Package
    └── st.file_uploader (styled)
```

#### Recent Simulations Component
- List simulations from `simulation_results/` directory
- Show: ID, timestamp, patient count, duration
- Click to select and set `current_sim_id`
- Highlight currently selected simulation

### Phase 4: Fix Session State Flow

1. **Export functionality**
   ```python
   # Check for current simulation
   if 'current_sim_id' in st.session_state:
       # Load simulation details
       # Show export UI
   else:
       st.info("Select a simulation from the list above to export")
   ```

2. **Import functionality**
   ```python
   # On successful import:
   # 1. Save to simulation_results/
   # 2. Set st.session_state.current_sim_id
   # 3. Show success message with navigation option
   ```

3. **Session state keys**:
   - `current_sim_id`: Selected simulation ID
   - `show_manage`: Toggle for Manage section
   - `imported_simulations`: Set of imported sim IDs (for badges)

### Phase 5: Remove Old Integration Points

1. **In `pages/3_Analysis_Overview.py`**:
   - Remove import of `analysis_overview_export`
   - Remove export section from Audit Trail tab

2. **In `pages/1_Protocol_Manager.py`**:
   - Remove import of `protocol_manager_import`
   - Remove import section

### Phase 6: Testing Strategy

1. **Manual Testing Checklist**:
   - [ ] Run a simulation
   - [ ] See it in Recent Simulations list
   - [ ] Click Manage → Export
   - [ ] Download package successfully
   - [ ] Import the package
   - [ ] See it marked as imported
   - [ ] Navigate to Analysis Overview
   - [ ] Verify imported data displays correctly

2. **Component Testing**:
   - Test export with missing session state
   - Test import with invalid files
   - Test Recent Simulations with empty directory

3. **Integration Testing**:
   - Full workflow from run → export → import → analyze
   - Test with multiple simulations
   - Test with large simulations

## Design Principles

1. **One button, one task**: Each action has exactly one trigger point
2. **Logical grouping**: All simulation I/O operations in Simulations page
3. **Visual consistency**: Floppy disk icon = file operations
4. **Progressive disclosure**: Manage section hidden by default
5. **Clear navigation**: Each page has a single, focused purpose

## Implementation Order

1. Create `components/` directory and move files
2. Fix session state issue in export ("No simulation selected")
3. Update Protocol Manager's Manage button icon
4. Rename page to "Simulations"
5. Add Recent Simulations list component
6. Integrate Manage button with Export/Import
7. Remove old integration points
8. Test complete workflow
9. Update documentation

## Success Criteria

- No blank pages in navigation
- Export works with current simulation
- Import sets up simulation for analysis
- UI is consistent and intuitive
- All tests pass
- Full workflow documented