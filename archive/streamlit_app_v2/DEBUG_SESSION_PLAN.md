# Debug Session Plan - Export/Import Integration Issues

## 🔴 Critical Issues Found

### 1. Import Doesn't Update Current Simulation (HIGH PRIORITY)
**Symptom**: Import completes successfully but app continues using old simulation data
**Expected**: After import, the imported simulation should become the current simulation
**Where to check**:
- `components/import_component.py` line 108: `st.session_state.current_sim_id = sim_id`
- Check if session state is actually being updated
- Check if rerun is needed after setting session state

### 2. Analysis Overview Shows Stale Data (HIGH PRIORITY)
**Symptom**: After import, Analysis Overview still shows previous simulation's data
**Expected**: Should show imported simulation's data
**Where to check**:
- `pages/3_Analysis_Overview.py` - how it loads the current simulation
- Session state key used for loading data
- Whether the page needs to be refreshed/rerun after import

### 3. Selected ✓ Doesn't Update Audit Tab (HIGH PRIORITY)
**Symptom**: Visual indicator shows selection but audit tab shows old data
**Expected**: Selecting a simulation should update all tabs to show that simulation
**Where to check**:
- `pages/2_Simulations.py` - selection mechanism
- How audit tab loads its data
- Session state synchronization between selection and data loading

## 🟡 Medium Priority Issues

### 4. Manage Button Visibility
**Symptom**: Manage button only appears after running a simulation
**Expected**: Should always be visible (even if disabled when no simulations exist)
**Where to check**:
- `pages/2_Simulations.py` - condition for showing Manage button
- Should check if ANY simulations exist, not just current_sim_id

## 🟢 Low Priority Features

### 5. IMPORTED Badge Not Implemented
**Symptom**: No visual indicator for imported simulations
**Expected**: Shows "IMPORTED" badge in Recent Simulations list
**Where to check**:
- `pages/2_Simulations.py` - Recent Simulations list rendering
- Need to track which simulations were imported (already have `st.session_state.imported_simulations`)

## 🔍 Debugging Approach

### Step 1: Trace Session State Flow
```python
# Add debugging prints to understand session state
print(f"Current sim_id: {st.session_state.get('current_sim_id', 'None')}")
print(f"Selected sim: {st.session_state.get('selected_simulation', 'None')}")
print(f"Imported sims: {st.session_state.get('imported_simulations', set())}")
```

### Step 2: Check Data Loading Logic
1. How does Analysis Overview determine which simulation to show?
2. Is it using `current_sim_id` or something else?
3. Does it need explicit refresh after import?

### Step 3: Fix Import Flow
The import should:
1. Import the package ✅ (working)
2. Set `current_sim_id` in session state ❓ (check if working)
3. Force refresh of all dependent data ❌ (likely missing)
4. Navigate or rerun to reflect changes ❓ (partially working)

### Step 4: Fix Selection Flow
When selecting a simulation:
1. Update visual indicator ✅ (working)
2. Update `current_sim_id` ❌ (not working)
3. Refresh all tabs that depend on current simulation ❌ (not working)

## 📋 Test Plan After Fixes

1. **Import Test**:
   - Run a simulation (note its data)
   - Export it
   - Run a different simulation (different parameters)
   - Import the first simulation
   - Verify ALL tabs show the imported simulation's data

2. **Selection Test**:
   - Have multiple simulations in the list
   - Select different ones
   - Verify audit tab updates each time

3. **Fresh Start Test**:
   - Clear all simulations
   - Verify Manage button is still visible
   - Import a simulation as the first action
   - Verify it works correctly

## 🛠️ Implementation Order

1. **First**: Fix import setting current simulation (core functionality)
2. **Second**: Fix selection updating all tabs (core functionality)
3. **Third**: Fix Manage button visibility (UX improvement)
4. **Fourth**: Add IMPORTED badge (nice to have)

## 📝 Key Files to Review

1. `components/import_component.py` - Import logic
2. `pages/2_Simulations.py` - Selection and Manage button
3. `pages/3_Analysis_Overview.py` - How it loads current simulation
4. Session state keys used across the app

## 🎯 Success Criteria

- [ ] Import makes the imported simulation the current one
- [ ] All tabs reflect the current simulation
- [ ] Selection in Recent Simulations updates all views
- [ ] Manage button always visible
- [ ] IMPORTED badge shows for imported simulations
- [ ] Documentation updated to reflect actual behavior