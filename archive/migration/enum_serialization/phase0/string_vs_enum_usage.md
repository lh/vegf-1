# String vs Enum Usage Analysis

**Generated**: 2025-05-25  
**Purpose**: Map which parts of codebase use strings vs enums for disease states

## Files Using String Literals

### 1. treat_and_extend_des.py
```python
'disease_state': 'stable' if not patient["disease_activity"]["fluid_detected"] else 'active'
```
- Uses lowercase strings: 'stable', 'active'
- Direct conditional assignment based on fluid detection

### 2. treat_and_extend_des_fixed.py
```python
'disease_state': 'stable' if not patient["disease_activity"]["fluid_detected"] else 'active'
```
- Identical pattern to above
- Fixed version still uses strings

### 3. enhanced_treat_and_extend_des.py
```python
'disease_state': 'stable' if not patient.state["disease_activity"]["fluid_detected"] else 'active'
```
- Enhanced version also uses strings
- Pattern consistent across DES variants

### 4. treat_and_extend_abs_fixed.py
```python
'disease_state': 'active' if patient.disease_activity["fluid_detected"] else 'stable'
```
- Even the "fixed" ABS version uses strings!
- This explains why fixed total simulations work

### 5. simulation/treat_and_extend_adapter.py
```python
'disease_state': 'stable' if not patient.state["disease_activity"]["fluid_detected"] else 'active'
```
- Adapter also uses strings

## Files Using DiseaseState Enum

### 1. simulation/clinical_model.py
- Defines the enum
- Returns enum from `simulate_vision_change()`
- Uses enum internally for all logic

### 2. simulation/patient_state.py
- Receives enum from clinical_model
- Stores in visit data without conversion
- This is where enum enters the data pipeline

### 3. simulation/abs.py (base class)
- Passes through whatever patient_state provides
- No conversion happening here

### 4. Regular treat_and_extend_abs.py
- Would use enums from clinical model
- But we're using treat_and_extend_abs_fixed.py instead!

## Key Findings

1. **ALL production simulation files use strings**, not enums!
   - Both ABS and DES variants
   - Even the "fixed" versions
   
2. **Only the clinical model uses enums internally**
   - But its output is ignored for disease_state
   - Simulations determine state from fluid detection instead

3. **The enum serialization error only happens with staggered simulations**
   - Because they inherit from base classes
   - Which use the clinical model's enum output

4. **String values are inconsistent with enum**:
   - Strings: 'stable', 'active' (lowercase)
   - Enum.__str__(): Would return same (has custom method)
   - Enum.name: 'STABLE', 'ACTIVE' (uppercase)

## The Real Problem

The simulations are **bypassing the clinical model** for disease state:
- Clinical model has sophisticated state transitions
- Simulations just check: `fluid_detected ? 'active' : 'stable'`
- This is a major simplification!

## Implications

1. We're not using the full disease state model (NAIVE, HIGHLY_ACTIVE)
2. State transitions are binary, not probabilistic
3. The clinical model's disease state logic is effectively unused
4. String usage is actually hiding a bigger architectural issue