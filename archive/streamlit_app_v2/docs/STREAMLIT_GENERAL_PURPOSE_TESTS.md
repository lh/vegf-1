# General Purpose Streamlit Tests

This document outlines a set of reusable tests that could be abstracted into a general-purpose testing framework for any Streamlit application.

## UI Structure Tests

### 1. No Nested Expanders Test
**Purpose**: Verify that expanders are not nested inside other expanders (causes runtime errors)
```python
def test_no_nested_expanders():
    # Track expander depth and fail if > 1
```

### 2. No Nested Columns Test
**Purpose**: Ensure columns aren't created inside other columns
```python
def test_no_nested_columns():
    # Track column creation context
```

### 3. Container Hierarchy Test
**Purpose**: Validate proper container/column/expander nesting
```python
def test_valid_container_hierarchy():
    # Check for valid parent-child relationships
```

## Session State Tests

### 4. Session State Type Consistency
**Purpose**: Ensure session state values maintain consistent types
```python
def test_session_state_type_consistency():
    # Verify types don't change unexpectedly
```

### 5. Required Session State Keys
**Purpose**: Check that required keys exist before use
```python
def test_required_session_state_keys():
    # Verify app doesn't crash from missing keys
```

### 6. Session State Mutation Safety
**Purpose**: Ensure session state isn't mutated in unsafe ways
```python
def test_session_state_mutation_safety():
    # Check for direct list/dict mutations
```

## Widget Tests

### 7. Unique Widget Keys
**Purpose**: Verify all widgets have unique keys (prevents conflicts)
```python
def test_unique_widget_keys():
    # Track all widget keys and check for duplicates
```

### 8. File Uploader Size Limits
**Purpose**: Ensure file uploaders have appropriate size limits
```python
def test_file_uploader_limits():
    # Check max_upload_size is set appropriately
```

### 9. Button Action Validation
**Purpose**: Verify buttons have associated actions
```python
def test_button_actions():
    # Ensure button clicks trigger expected behavior
```

## Performance Tests

### 10. Widget Count Limits
**Purpose**: Prevent excessive widget creation that slows apps
```python
def test_widget_count_limits():
    # Count total widgets and warn if excessive
```

### 11. Dataframe Size Warnings
**Purpose**: Warn about large dataframes in st.dataframe()
```python
def test_dataframe_performance():
    # Check dataframe sizes and suggest pagination
```

### 12. Cache Usage Validation
**Purpose**: Verify proper use of st.cache decorators
```python
def test_cache_usage():
    # Check functions that should be cached
```

## Error Handling Tests

### 13. Try-Except Coverage
**Purpose**: Ensure critical operations have error handling
```python
def test_error_handling_coverage():
    # Verify file operations, API calls have try-except
```

### 14. User-Friendly Error Messages
**Purpose**: Check that errors show helpful messages
```python
def test_user_friendly_errors():
    # Verify st.error() used instead of raw exceptions
```

### 15. Progress Bar Cleanup
**Purpose**: Ensure progress bars are cleared on error
```python
def test_progress_cleanup():
    # Verify progress.empty() in finally blocks
```

## Navigation Tests

### 16. Page Navigation Validity
**Purpose**: Verify st.switch_page() targets exist
```python
def test_page_navigation():
    # Check all page switches reference valid files
```

### 17. Navigation State Preservation
**Purpose**: Ensure navigation preserves necessary state
```python
def test_navigation_state():
    # Verify required state transfers between pages
```

## Data Display Tests

### 18. Empty State Handling
**Purpose**: Verify graceful handling of empty data
```python
def test_empty_state_display():
    # Check for user-friendly empty state messages
```

### 19. Data Type Display Compatibility
**Purpose**: Ensure data types are compatible with display widgets
```python
def test_data_display_compatibility():
    # Verify dataframes, charts get correct data types
```

### 20. Timezone Handling
**Purpose**: Verify consistent timezone handling
```python
def test_timezone_consistency():
    # Check datetime displays are timezone-aware
```

## Accessibility Tests

### 21. Form Label Coverage
**Purpose**: Ensure all inputs have labels
```python
def test_form_labels():
    # Verify all inputs have associated labels
```

### 22. Help Text Coverage
**Purpose**: Check that complex widgets have help text
```python
def test_help_text_coverage():
    # Verify help parameter used appropriately
```

## Security Tests

### 23. File Path Validation
**Purpose**: Ensure file operations use safe paths
```python
def test_file_path_security():
    # Check for path traversal vulnerabilities
```

### 24. Input Sanitization
**Purpose**: Verify user inputs are sanitized
```python
def test_input_sanitization():
    # Check text inputs for injection risks
```

## State Machine Tests

### 25. State Transition Validity
**Purpose**: Verify valid state transitions in multi-step forms
```python
def test_state_transitions():
    # Check state machine follows expected flow
```

## Memory Tests

### 26. Memory Leak Detection
**Purpose**: Check for memory leaks in reruns
```python
def test_memory_leaks():
    # Monitor memory usage across reruns
```

### 27. Large Object Cleanup
**Purpose**: Verify large objects are properly cleaned up
```python
def test_large_object_cleanup():
    # Check that temporary large objects are released
```

## Implementation Strategy

These tests could be packaged as:

1. **Pytest Plugin**: `pytest-streamlit-best-practices`
   ```python
   # Install with: pip install pytest-streamlit-best-practices
   # Use with: pytest --streamlit-checks
   ```

2. **Standalone Validator**: `streamlit-validator`
   ```python
   from streamlit_validator import validate_app
   validate_app("my_app.py")
   ```

3. **Decorator-Based**: Apply to page functions
   ```python
   @validate_streamlit_best_practices
   def my_page():
       st.title("My Page")
   ```

4. **CI/CD Integration**: GitHub Action
   ```yaml
   - name: Streamlit Best Practices Check
     uses: streamlit/best-practices-action@v1
   ```

## Benefits

1. **Prevent Common Errors**: Catch issues before runtime
2. **Improve Performance**: Identify performance bottlenecks
3. **Enhance UX**: Ensure consistent user experience
4. **Maintain Quality**: Enforce best practices across team
5. **Save Development Time**: Catch issues early in development

## Notes

- Tests should be configurable (strict vs. warning modes)
- Should provide clear remediation suggestions
- Could include auto-fix capabilities for some issues
- Performance impact of tests should be minimal
- Should work with Streamlit's execution model