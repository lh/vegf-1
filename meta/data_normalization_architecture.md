# Data Normalization Architecture

## Overview

This document outlines the architectural decision to implement explicit data normalization layers in our simulation system, separating type conversion from business logic.

## Current Problem

The simulation system currently handles multiple data types (datetime objects, strings, numeric values) within business logic functions. This approach violates the Single Responsibility Principle and creates:

- Complex, multi-path code that's harder to test
- Mixed concerns (data conversion + business logic)
- Performance overhead from repeated type checking
- Debugging difficulty when distinguishing type issues from logic issues

## Proposed Solution

Implement a clear separation between data normalization and business logic:

```python
# Data layer - handles all type conversions
DataNormalizer.normalize_patient_data(raw_data) -> normalized_data

# Business layer - only handles normalized data types
process_simulation_results(normalized_data) -> results
```

## Architecture Benefits

### 1. Separation of Concerns
- Data normalization is isolated from business logic
- Each layer has a single, clear responsibility
- Easier to understand and maintain

### 2. Type Safety
- Functions have clear contracts about expected types
- Reduces runtime type errors
- Enables better static analysis

### 3. Performance
- Convert data once at system boundaries
- Avoid repeated type checking in hot paths
- More efficient data processing

### 4. Testability
- Unit test conversion logic separately
- Test business logic with known types
- Simpler test cases (single path)

### 5. Debugging
- Clear error boundaries
- Know immediately if issue is type-related or logic-related
- Better error messages

## Implementation Pattern

### Data Normalization Layer

```python
class DataNormalizer:
    """Handles all data type conversions at system boundaries"""

    @staticmethod
    def normalize_patient_data(patient_data):
        """Ensure all dates are datetime objects"""
        for visit in patient_data:
            if 'date' in visit:
                visit['date'] = DataNormalizer._to_datetime(visit['date'])
        return patient_data

    @staticmethod
    def _to_datetime(date_value):
        """Convert various date formats to datetime"""
        if isinstance(date_value, datetime):
            return date_value
        elif isinstance(date_value, str):
            return pd.to_datetime(date_value)
        elif isinstance(date_value, (int, float)):
            return datetime.fromtimestamp(date_value)
        else:
            raise ValueError(f"Unsupported date type: {type(date_value)}")
```

### Business Logic Layer

```python
def process_simulation_results(sim, patient_histories, params):
    """Process simulation results with normalized data"""
    # Data is already normalized - no type checking needed
    for visit in patient_histories:
        visit_time = (visit['date'] - baseline).days / 30.44
        # Pure business logic...
```

## Implementation Guidelines

### 1. Identify System Boundaries
- JSON deserialization points
- Database query results
- External API responses
- User input processing

### 2. Create Normalization Functions
- One function per data structure type
- Clear input/output type contracts
- Comprehensive error handling
- Validation of required fields

### 3. Apply at Boundaries
- Normalize immediately after data enters system
- Keep normalized format throughout processing
- Only denormalize when leaving system

### 4. Document Expected Types
- Use type hints consistently
- Document transformation rules
- Provide examples

## Migration Strategy

1. **Phase 1**: Create DataNormalizer class
2. **Phase 2**: Add normalization at entry points
3. **Phase 3**: Refactor business logic to expect normalized data
4. **Phase 4**: Remove type checking from business logic
5. **Phase 5**: Add comprehensive tests

## Example: Simulation Runner

### Before (Mixed Concerns)
```python
def process_visit(visit):
    # Type checking mixed with business logic
    if isinstance(visit['date'], str):
        date = pd.to_datetime(visit['date'])
    elif isinstance(visit['date'], datetime):
        date = pd.Timestamp(visit['date'])

    # Business logic
    time_delta = (date - baseline).days / 30.44
```

### After (Separated Concerns)
```python
# At system boundary
normalized_data = DataNormalizer.normalize_visits(raw_data)

# In business logic
def process_visit(visit):
    # Clean business logic only
    time_delta = (visit['date'] - baseline).days / 30.44
```

## Conclusion

This architectural change provides:
- Cleaner, more maintainable code
- Better performance
- Improved testability
- Enhanced debugging capabilities
- Type safety throughout the system

The investment in proper data normalization will pay dividends in reduced bugs, easier maintenance, and clearer code structure.