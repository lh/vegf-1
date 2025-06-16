# Time-Based Transition Plan Review

## Strengths
1. Clear problem statement and rationale
2. Good architectural decision to create new engines rather than modify existing
3. Fortnightly (14-day) updates are well justified
4. Proper identification of production engine architecture (WithSpecs wrappers)
5. Good test-first approach

## Weaknesses and Areas Needing More Detail

### 1. Vision Change Model Integration
**Issue**: The plan mentions vision changes should happen fortnightly but doesn't detail how.
**Missing Details**:
- Should vision changes accumulate continuously or only at visits?
- How do we convert per-visit vision change parameters to fortnightly?
- What happens to vision between visits vs at visits?

**Recommendation**: Add explicit vision change strategy:
```python
# Option 1: Vision changes only at visits (current behavior)
# Option 2: Vision deteriorates fortnightly, improves at treatment
# Option 3: Continuous vision change based on disease state
```

### 2. Discontinuation Logic
**Issue**: Unclear how discontinuation checks change from per-visit to time-based.
**Missing Details**:
- When are discontinuation checks performed? Every fortnight? Only at visits?
- How to convert per-visit discontinuation probabilities?
- What about treatment burden discontinuation over time?

**Recommendation**: Clarify discontinuation strategy.

### 3. Patient State Tracking
**Issue**: No clear data structure for tracking fortnightly updates.
**Missing Details**:
- How do we store disease state history between visits?
- Do we need to track all fortnightly updates or just current state?
- Impact on memory and serialization?

**Recommendation**: Define state tracking approach:
```python
class Patient:
    # Current approach: only visit history
    visit_history: List[VisitRecord]
    
    # Time-based approach options:
    # Option 1: Separate state update history
    state_update_history: List[StateUpdate]
    
    # Option 2: Unified timeline with event types
    timeline: List[TimelineEvent]  # visits, state updates, etc.
```

### 4. DES Engine Specifics
**Issue**: Plan focuses on ABS but DES has different architecture.
**Missing Details**:
- How do fortnightly updates work with event-driven simulation?
- Do we schedule state update events every 14 days?
- How does this interact with the event queue?

### 5. Backward Compatibility
**Issue**: No clear migration strategy for existing protocols.
**Missing Details**:
- How do users run old protocols with new engine?
- Automatic parameter conversion or manual migration?
- How to validate converted parameters give similar results?

### 6. Treatment Effect Decay
**Issue**: Half-life parameter mentioned but not detailed.
**Missing Details**:
- Where is half-life configured? Per drug? Per protocol?
- Default half-life values?
- Validation against clinical data?

### 7. Edge Cases
**Issue**: Several edge cases not addressed:
- Patient enrolls mid-fortnight
- Simulation starts/ends mid-fortnight
- Very long gaps between visits (missed appointments)
- Patients who never return after initial visit

### 8. Performance Considerations
**Issue**: No analysis of performance impact.
**Missing Details**:
- 26 updates/year vs current per-visit updates
- Memory overhead of tracking more state
- Optimization strategies for large simulations

### 9. Clinical Validation
**Issue**: No specific validation criteria.
**Missing Details**:
- Which clinical endpoints to compare?
- Acceptable deviation from current results?
- Real-world data sources for validation?

### 10. Protocol Specification Updates
**Issue**: Protocol spec changes not fully detailed.
**Missing Details**:
- How does ProtocolSpecification class change?
- Validation for new fields?
- Default values for transition_model field?

## Recommended Additions to Plan

### 1. Data Structure Design
Add a section detailing exact data structures for state tracking.

### 2. Migration Guide
Create explicit guide for converting existing protocols.

### 3. Validation Framework
Define specific metrics and acceptance criteria.

### 4. Performance Budget
Set explicit performance targets and measurement approach.

### 5. Clinical Alignment
Add section on clinical interpretation of fortnightly updates.

### 6. Error Handling
Define behavior for edge cases and error conditions.

### 7. Monitoring and Debugging
How to debug time-based progression issues?

### 8. Documentation Plan
User-facing documentation for the new model.