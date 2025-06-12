# 📋 IMPLEMENTATION INSTRUCTIONS

**IMPORTANT**: This is the active implementation plan. Always refer to this document when working on the current feature.

## 🚀 Current Phase: Treatment State Streamgraph

### Overview
We are implementing a streamgraph visualization showing patient flow through treatment states over time. This includes pre-calculating treatment pattern data when simulations load for better performance across all treatment visualizations.

**Current Task**: Implement treatment state streamgraph with pre-calculation  
**Timeline**: 4-5 days  
**Approach**: Phased implementation with backward compatibility

### 📍 Key Documents
- **Implementation Plan**: [STREAMGRAPH_IMPLEMENTATION_PLAN_V2.md](STREAMGRAPH_IMPLEMENTATION_PLAN_V2.md) - Complete consolidated guide
- **Original Concept**: [STREAMGRAPH_PLAN.md](STREAMGRAPH_PLAN.md) - Initial requirements
- **Pattern Analyzer**: `components/treatment_patterns/pattern_analyzer.py` - Existing treatment state logic
- **Visualization Modes**: `utils/visualization_modes.py` - Semantic color system

### Current Status
- ✅ Plan created and reviewed
- ✅ Pre-calculation strategy decided (Option 2)
- ✅ Backward compatibility approach defined
- 🔄 Ready to start Phase 0: Verify Existing Functionality

### Implementation Phases

#### Phase 0: Verify Existing Functionality (Day 0)
- [ ] Run baseline test of Sankey diagram
- [ ] Create verification script
- [ ] Document current behavior
- [ ] Set up feature branch

#### Phase 1: Data Infrastructure (Day 1)
- [ ] Implement pre-calculation in `get_active_simulation()`
- [ ] Create backward-compatible caching
- [ ] Test Sankey still works
- [ ] Create data_manager module

#### Phase 2: Time Series Generation (Day 2)
- [ ] Build time_series_generator
- [ ] Implement patient state tracking
- [ ] Validate against Sankey data
- [ ] Test data conservation

#### Phase 3: Visualization (Day 3)
- [ ] Create streamgraph component
- [ ] Apply semantic colors
- [ ] Add interactivity
- [ ] Test with various data sizes

#### Phase 4: Integration & Testing (Day 4)
- [ ] Replace existing streamgraph
- [ ] Performance optimization
- [ ] Full regression testing
- [ ] Documentation update

## 🧪 Testing Protocol

### Before ANY changes:
1. Ask user to run simulation (e.g., 1000 patients, 2 years)
2. Check Patient Journey Visualisation tab
3. Screenshot working Sankey
4. Note load times

### After EACH phase:
1. Run fresh simulation
2. Verify Sankey works identically
3. Check for performance changes
4. Look for console errors

### Red Flags:
- Different data in Sankey
- Longer load times
- Missing states or colors
- Console errors
- Empty visualizations

## 📏 Implementation Rules

1. **Backward Compatibility** - Sankey must work identically throughout
2. **Real Data Only** - No synthetic curves or smoothing
3. **Test Continuously** - Verify after each change
4. **Performance Matters** - Pre-calc should be <3s for 10k patients
5. **Semantic Colors** - Use existing color system

## 🔧 Key Code Locations

### Files to Modify:
- `utils/state_helpers.py` - Add pre-calculation
- `pages/3_Analysis_Overview.py` - Update tab4 for new streamgraph
- `components/treatment_patterns/` - Add new modules

### Files to Create:
- `components/treatment_patterns/data_manager.py`
- `components/treatment_patterns/time_series_generator.py`
- `visualizations/streamgraph_treatment_states.py`
- `verify_sankey_works.py` (test script)

## ✅ Previous Phases Complete

### Phase 1: Export/Import Functionality
- ✅ Complete and working
- ✅ Security hardened
- ✅ UI integrated

### Phase 2: State Management (Deferred)
- Identified issues with simulation switching
- Planned fixes in STATE_REFACTORING_PLAN.md
- To be addressed after streamgraph

## 📊 Success Metrics

### Streamgraph Implementation:
- [ ] Patient counts conserved at all time points
- [ ] States match Sankey diagram exactly
- [ ] Pre-calculation <3 seconds
- [ ] Smooth interaction with 10k patients
- [ ] All existing visualizations still work

---

**Remember**: The Sankey diagram is critical functionality. Test thoroughly at each step to ensure we don't break it while implementing the streamgraph.