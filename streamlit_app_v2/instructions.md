# 📋 IMPLEMENTATION INSTRUCTIONS

**IMPORTANT**: This is the active implementation plan. Always refer to this document when working on the current feature.

## 🚀 Current Phase: State Management Fixes

### Overview
We have discovered critical bugs in the state management that are causing:
- KeyError 'spec' when viewing treatment patterns
- Parameters not updating when switching simulations
- Audit trail showing wrong simulation data

**Next Implementation**: Simple state fixes to enable multi-simulation support  
**Timeline**: 2-3 days  
**Approach**: Minimal patches, no architectural changes

### 📍 Key Documents
- **Detailed Plan**: [instructions_phase2.md](instructions_phase2.md) - Step-by-step implementation guide
- **Strategy**: [SIMPLE_STATE_FIX_PLAN.md](SIMPLE_STATE_FIX_PLAN.md) - High-level approach
- **Architecture Analysis**: [docs/STATE_REFACTORING_PLAN.md](docs/STATE_REFACTORING_PLAN.md) - Future vision (not for this phase)
- **Pragmatic Approach**: [docs/PRAGMATIC_REFACTORING_PLAN.md](docs/PRAGMATIC_REFACTORING_PLAN.md) - Why we're keeping it simple

## ✅ Phase 1 Complete: Export/Import Functionality

### Status: COMPLETE - Ready to merge to main
- ✅ All 41 tests passing (security, data integrity, round-trip)
- ✅ Export/Import fully integrated in UI
- ✅ Parquet-only storage refactor complete
- ✅ Components properly organized in `components/` directory

### Key Achievements:
- Bidirectional package functionality working
- Security hardened against all attack vectors
- Data integrity preserved through round-trip
- UI integration complete with progress indicators

## 🔧 Phase 2: State Management Fixes

### Problems to Fix:
1. **Duplicate audit_trail** - Exists in session state twice
2. **Protocol spec not loading** - Using wrong method (from_yaml vs from_dict)
3. **No multi-simulation support** - Can't compare simulations

### Solution Overview:
```python
# Add simple registry for multiple simulations
st.session_state.simulation_registry = {
    'sim_1': {...},  # Max 5 simulations
    'sim_2': {...}
}

# Simple helper functions (no services or classes)
def get_active_simulation():
    return st.session_state.simulation_registry.get(
        st.session_state.active_sim_id
    )
```

### Implementation Steps:
1. Merge Phase 1 to main
2. Create `feature/simple-state-fix` branch
3. Follow [instructions_phase2.md](instructions_phase2.md) task by task
4. Test thoroughly
5. Merge and move to Phase 3

## 📏 Golden Rules

1. **Keep it simple** - No over-engineering for a pre-beta tool
2. **Test first** - Write tests before implementation
3. **One fix at a time** - Atomic commits for each change
4. **No synthetic data** - This is a scientific tool
5. **Fail fast** - No graceful degradation in pre-beta

## 🧪 Testing Commands

```bash
# Before starting any work
python scripts/run_tests.py --all

# During development
python -m pytest tests/integration/test_simulation_selection_sync.py -v

# UI testing
streamlit run APE.py

# Before committing
python scripts/run_tests.py --all
```

## 📊 Success Metrics

### Phase 2 (State Fixes):
- [ ] No KeyError 'spec' in treatment patterns
- [ ] Audit trail shows correct simulation
- [ ] Parameters update when switching simulations
- [ ] Can hold 5 simulations in registry
- [ ] All existing tests still pass

### Future Phases:
- Phase 3: Basic 2-simulation comparison
- Phase 4: Polish and documentation
- Phase 5: Performance optimization (if needed)

---

**Remember**: We're building for dozens of users on Streamlit's free tier, not thousands of enterprise users. Keep solutions pragmatic and maintainable.