# Pandas Future-Proofing Guide

This document explains the pandas deprecation warnings we encountered and how we fixed them to ensure compatibility with future pandas versions.

## Overview

In June 2025, we addressed several FutureWarnings in our codebase to ensure compatibility with upcoming pandas versions. These fixes follow pandas' recommended practices rather than suppressing warnings.

## Fixed Issues

### 1. Boolean Downcasting Warning

**Location**: `components/treatment_patterns/pattern_analyzer.py`

**Original Code**:
```python
visits_df['after_gap'] = visits_df.groupby('patient_id')['had_long_gap'].shift(1)
visits_df['after_gap'] = visits_df['after_gap'].fillna(False).astype('bool')
```

**Warning**:
```
FutureWarning: Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated 
and will change in a future version. Call result.infer_objects(copy=False) instead.
```

**Root Cause**: 
- The `shift()` operation creates NaN values in an object-dtype column
- Using `.fillna()` on object dtype triggers automatic downcasting behavior that will change

**Fixed Code**:
```python
after_gap_shifted = visits_df.groupby('patient_id')['had_long_gap'].shift(1)
visits_df['after_gap'] = after_gap_shifted.astype('boolean').fillna(False)
```

**Why This Works**:
- We use pandas' nullable boolean dtype (`'boolean'`) which properly handles NaN values
- Converting to boolean type BEFORE fillna avoids downcasting ambiguity
- The nullable boolean dtype is designed for this exact use case

### 2. DataFrame Concatenation Warning

**Location**: `components/treatment_patterns/pattern_analyzer_enhanced.py`

**Original Code**:
```python
terminal_transitions.append({
    'patient_id': patient['patient_id'],
    'from_state': current_state,
    'to_state': terminal_state,
    'interval_days': None  # This causes issues!
})
# ...
enhanced_transitions = pd.concat([transitions_df, terminal_df], ignore_index=True)
```

**Warning**:
```
FutureWarning: The behavior of DataFrame concatenation with empty or all-NA entries 
is deprecated. In a future version, this will no longer exclude empty or all-NA 
columns when determining the result dtypes.
```

**Root Cause**:
- Using `None` for numeric columns creates object dtype
- Concatenating DataFrames with mismatched dtypes (float vs object) triggers the warning

**Fixed Code**:
```python
terminal_transitions.append({
    'patient_id': patient['patient_id'],
    'from_state': current_state,
    'to_state': terminal_state,
    'interval_days': np.nan  # Use np.nan for missing numeric values
})

# Ensure dtype consistency before concatenation
if terminal_transitions:
    terminal_df = pd.DataFrame(terminal_transitions)
    
    for col in terminal_df.columns:
        if col in transitions_df.columns and col != 'patient_id':
            if transitions_df[col].dtype in [np.float64, np.float32]:
                terminal_df[col] = terminal_df[col].astype(transitions_df[col].dtype)
    
    enhanced_transitions = pd.concat([transitions_df, terminal_df], ignore_index=True)
```

**Why This Works**:
- `np.nan` is the proper representation for missing numeric values
- It maintains consistent float dtype across DataFrames
- Explicit dtype conversion ensures compatibility

## Best Practices for Future Development

### 1. Handling Missing Values
- **Numeric columns**: Always use `np.nan`, never `None`
- **Boolean columns**: Use pandas' nullable boolean dtype (`'boolean'`)
- **String columns**: Use `pd.NA` for pandas 1.0+ compatibility

### 2. DataFrame Operations
- Always ensure consistent dtypes before concatenation
- Be explicit about dtype conversions
- Use nullable dtypes when dealing with potentially missing data

### 3. Type Conversions
```python
# Good: Explicit about nullable types
df['bool_col'] = df['bool_col'].astype('boolean')
df['int_col'] = df['int_col'].astype('Int64')  # Nullable integer

# Bad: Ambiguous conversions
df['bool_col'] = df['bool_col'].fillna(False).astype('bool')
```

### 4. Concatenation Checklist
Before concatenating DataFrames:
1. Check column names match
2. Check dtypes match
3. Use consistent missing value representations
4. Consider using `pd.concat` with `sort=False` to maintain column order

## Testing for Future Compatibility

To test your code for future pandas compatibility:

```python
import pandas as pd
# Enable future behavior
pd.set_option('future.no_silent_downcasting', True)

# Your code here...
```

## References

- [Pandas Future Warnings Documentation](https://pandas.pydata.org/docs/user_guide/gotchas.html#futurewarning)
- [Nullable Data Types in Pandas](https://pandas.pydata.org/docs/user_guide/integer_na.html)
- [Best Practices for DataFrame Concatenation](https://pandas.pydata.org/docs/user_guide/merging.html)

## Summary

By addressing these warnings proactively:
1. Our code is ready for pandas 2.x and beyond
2. We follow pandas' recommended best practices
3. We avoid unexpected behavior changes when upgrading
4. The codebase is more maintainable and explicit about type handling

Remember: **Fix the root cause, don't suppress the warning!**