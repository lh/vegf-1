# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

At the start of each session, use the memory server to retrieve relevant project context and maintain continuity.

Automatically store the following in the memory server:
1. Key project context (requirements, architecture decisions)
2. Important code snippets with descriptive tags
3. Design patterns and conventions used in the project
4. Solutions to complex problems for future reference
5. Module/component information with appropriate tags
6. Testing strategies and edge cases

Tag all memories appropriately to enable efficient retrieval in future sessions.

Use Git and github for version control. You have access to the gh command. Use it.

# Git and GitHub Instructions
1. Use concise, descriptive commit messages that explain the purpose of changes
2. DO NOT add attribution like "Generated with Claude" or "Co-Authored-By" to commits
3. Follow project conventions for branch naming and PR format
4. Include issue numbers in commit messages when applicable
5. When asked to create PRs, use existing PR templates if available

# Development Environment
- This is a development environment. Always git commit and push after changes. Use the gh command for github if needed.
- When modifying Streamlit components, test changes with test scripts and show the user the results before updating the app

# British English Standards
- **ALL user-facing text must use British English spelling**: This includes UI labels, messages, documentation, and comments in user-visible files
- **Examples**: "colour" not "color", "centre" not "center", "analyse" not "analyze", "organisation" not "organization"
- **Internal code**: Variable names and function names can remain in American English for consistency with Python conventions
- **Key areas requiring British English**:
  - Streamlit UI text (st.write, st.header, button labels, etc.)
  - Error messages and user notifications
  - Documentation files (*.md)
  - Plot titles, axis labels, and legends
  - Help text and tooltips
  - Protocol file descriptions

## Common Development Commands

### Running the Application
```bash
cd streamlit_app_v2
streamlit run APE.py
```

### Testing
```bash
# Run all tests
python scripts/run_tests.py --all

# Run unit tests only (default)
python scripts/run_tests.py

# Run UI tests only
python scripts/run_tests.py --ui

# Run tests in watch mode
python scripts/run_tests.py --watch

# Run with coverage
python scripts/run_tests.py --coverage

# Run baseline regression tests
./run_baseline_tests.sh

# Run specific test verification
python verify_fixed_discontinuation.py
python verify_streamlit_integration.py
```

### Development Setup
```bash
# Initial setup
./scripts/dev_setup.sh

# Install dependencies
pip install -r requirements.txt

# Install playwright for UI testing
playwright install chromium
```

## Architecture Overview

### Application Structure
- **APE.py**: Main entry point for the Streamlit application
- **pages/**: Individual Streamlit pages (Protocol Manager, Run Simulation, Analysis Overview)
- **core/**: Core simulation engine (ABS and DES implementations)
- **utils/**: Visualization utilities including ChartBuilder and StyleConstants
- **protocols/v2/**: YAML protocol specifications
- **simulation_results/**: Saved simulation outputs with standardized naming

### Key Design Patterns

#### 1. Protocol-Driven Simulations
- All simulations driven by YAML protocol files in `protocols/v2/`
- No hidden defaults - every parameter must be explicit
- Protocols are immutable after loading
- Full audit trail from parameter to result

#### 2. Visualization System
- **ChartBuilder Pattern**: Fluent API for consistent chart creation
- **Dual Mode System**: Toggle between Analysis (Tufte) and Presentation (Zoom) modes
- **Central Styling**: All visual constants in `utils/style_constants.py`
- **No fallbacks**: Fail fast on missing styling elements

#### 3. Button Styling System
- Progressive brightness states: Resting → Hover → Active
- Dynamic layout adaptation based on user workflow state
- Consistent action-oriented navigation

### Simulation Features

#### Recruitment Modes
- **Fixed Total Mode**: Specify total patients, system calculates monthly rate
- **Constant Rate Mode**: Specify patients/month, continues throughout simulation

#### File Management
- Naming: `YYYYMMDD-HHMMSS-sim-Xp-Yy` (e.g., `20250124-120530-sim-1000p-5y`)
- Auto-loads latest simulation in analysis pages
- Calendar-time transformation uses vectorized pandas operations

# Playwright Integration

## Streamlit App Debugging with Playwright

Playwright is configured and working in both `streamlit_app` and `streamlit_app_parquet` directories for browser automation and debugging.

### Quick Start for Debugging
1. **Test Setup**: Ensure Playwright is installed with `npx playwright install chromium`
2. **Use Configurable Port Scripts**: Use `playwright_debug_configurable.js` to avoid port conflicts
3. **Default Ports**: Scripts default to port 8503 (not 8502) to avoid interfering with running apps

### Available Debugging Scripts

#### Basic Connection Test
```bash
cd streamlit_app  # or streamlit_app_parquet
node test_playwright_simple.js
```

#### Interactive Debugging (Recommended)
```bash
# Run test app on different port
streamlit run test_streamlit_app.py --server.port 8503

# Debug in browser with DevTools
node playwright_debug_configurable.js 8503
```

#### Advanced Debugging
```bash
node playwright_advanced_debug.js
```

### Port Management
- **Main app**: Use your actual port (usually 8502)
- **Testing**: Use alternate ports (8503, 8504, etc.)
- **Command syntax**: `node script.js [port]`
- **Example**: `node playwright_debug_configurable.js 8504`

### Best Practices
- ALWAYS use alternate ports for testing to avoid disrupting running apps
- Use the test Streamlit app for initial Playwright verification
- Only debug real apps when necessary and with caution
- Capture screenshots for visual verification
- ONLY run tests against real simulation data, NEVER with synthetic test data
- Verify data integrity in automated tests by checking key values match expected distributions
- When validating visualizations, check the actual data source, not just the visual appearance

# Visualization Guidelines
- For visual acuity graphs use a y-axis scale running from 0 to 85 and so far as is possible make sure they all have the same vertical height for the scale
- X-axis ticks should be at yearly intervals (0, 12, 24, 36, 48, 60 months) for better readability
- For all visualizations, follow Tufte principles documented in meta/visualization_templates.md
- Maintain consistent styling across charts with the established color system

# Styling and Visualization Standards

1. **Single Source of Truth**: All colors, opacity values, and styling constants MUST be defined in the central color system (visualization.color_system). Never define fallback or alternative values elsewhere.
2. **No Duplicate Definitions**: Never redefine or create local copies of styling values. Import all styling constants from the central system.
3. **Fix at Source**: When encountering styling issues, fix them in the central color system rather than creating workarounds in individual components.
4. **Consistent Naming**: Always use the established naming conventions from the central system. Don't create alternative names for the same concept.
5. **Clean Visualization Style**: Follow Tufte principles in all visualizations - remove unnecessary chart elements, use minimal styling, and focus on data representation.
6. **No Bounding Lines**: Avoid unnecessary bounding boxes, borders, and visual elements that don't contribute to data understanding.
7. **Error Handling**: If a styling element is missing, report the issue rather than creating a local fallback.
8. **Refactoring Priority**: Consider inconsistent styling as a bug that needs immediate attention, not as a feature to be worked around.

# CRITICAL SCIENTIFIC TOOL PRINCIPLES

**NEVER GENERATE SYNTHETIC DATA**: This is a scientific analysis tool, not a demo

This is the single most important principle guiding all development, testing, and validation:

- If data is missing, FAIL FAST with clear error messages
- NEVER create fallback data, synthetic timelines, or mock values
- NEVER add try/except blocks that hide missing data
- The integrity of the analysis depends on using only real simulation data
- NEVER use test data or fixtures in production code - test data belongs ONLY in test files
- ALWAYS validate that functions like `generate_sample_results` are not being called in production code
- When implementing visualizations, ONLY use real data from simulations, NEVER create synthetic curves
- ALWAYS verify data conservation principles (e.g., total patient counts must remain constant)
- Flag and refuse to use any code containing "sample", "mock", "fake", "dummy", or "synthetic" outside test contexts
- IMMEDIATELY halt and speak up if asked to replace actual data with something "prettier" or "smoother"
- NEVER "enhance" actual data for aesthetics - show the real data with all its messiness
- When debugging, inspect and verify the ACTUAL data values rather than making assumptions
- Do not "normalize" or "standardize" data without explicit scientific justification
- Document actual data sources and calculation methods in code comments
- In testing, verify against known reference values, not arbitrary placeholders

These principles are NON-NEGOTIABLE. As the postmortem in meta/streamgraph_synthetic_data_postmortem.md states: 
"In scientific computing, accuracy is paramount. Never invent data. Ever."

# Workflow Reminder
- Every summary should be followed by an offer to git commit and push and update documentation

# Test-Driven Development (TDD) Requirements

## CRITICAL: Always Follow TDD Process
Based on lessons learned from regression incidents, these TDD practices are MANDATORY:

### 1. Strict TDD Discipline
**ALWAYS start with a failing test before implementing any fix or feature:**
```python
# Example: Before adding a missing method
def test_get_visits_df_exists():
    results = create_test_results()
    visits_df = results.get_visits_df()
    assert 'patient_id' in visits_df.columns
```

### 2. Regression Test for Every Bug
**Every bug fix MUST include a test that fails without the fix:**
```python
# Example: Test that would have caught downstream issues
def test_treatment_patterns_with_memory_results():
    results = InMemoryResults(...)
    transitions, visits = extract_treatment_patterns(results)
    assert len(visits) > 0
```

### 3. Run Full Test Suite Before Committing
- **Manual testing first**: Run `python scripts/run_tests.py` before attempting to commit
- **Don't rely on pre-commit hooks**: They're a safety net, not a primary validation
- **Check for warnings**: Even if tests pass, investigate any warnings

### 4. Understand Before Fixing
Before implementing any fix, ask:
- Why is this broken? What's the root cause?
- Was the missing functionality intentional? What's the design pattern?
- What other components might be affected by this change?
- Are there existing tests that should have caught this?

### 5. NaN and Data Type Handling
When working with data comparisons:
```python
# WRONG: Direct comparison fails for NaN
assert value1 == value2  # Fails if both are NaN

# CORRECT: Handle NaN properly
if pd.isna(value1) and pd.isna(value2):
    pass  # Both NaN is OK
elif pd.isna(value1) or pd.isna(value2):
    pytest.fail("One value is NaN, other is not")
else:
    assert value1 == value2
```

### 6. Dangers of Mock-Driven Development

**CRITICAL WARNING**: Avoid over-mocking in tests, especially for scientific computing tools like APE.

#### Why Mock-Driven Development is Dangerous

1. **Mock-driven instead of test-driven**: Creating mocks that mirror what you *think* the code should do, rather than testing actual behavior. This leads to tests that pass even when the real code is broken.

2. **Mock contamination risk**: There's a real danger of accidentally using mock patterns or data structures in production code, thinking they're real. The "sample"/"synthetic" data issue is a prime example.

3. **Over-mocking hides integration issues**: By mocking everything, you miss actual integration problems - like the missing `get_visits_df` method that only showed up when real code tried to use it.

4. **Tests document mocks, not behavior**: Tests end up verifying that mocks work as configured, not that the actual system works correctly.

#### For Scientific Tools Like APE

This is particularly dangerous because:
- Mock data might not represent real simulation behavior
- Integration between components is critical for data integrity  
- The actual data flow matters more than individual unit behavior
- Scientific accuracy depends on real data transformations

#### Better Approach

```python
# WRONG: Over-mocked test
def test_simulation():
    mock_engine = Mock()
    mock_engine.run.return_value = Mock(patients=100)
    assert mock_engine.run().patients == 100  # Tests the mock!

# CORRECT: Use real components with minimal test data
def test_simulation():
    engine = SimulationEngine()
    results = engine.run(n_patients=10, duration_years=0.1)
    assert results.patient_count == 10  # Tests actual behavior
```

**Rules for Mocking**:
- Use real simulation data, even if small (10 patients, 0.1 years)
- Test actual integration points between components
- Only mock external dependencies (file system, network, databases)
- NEVER mock core business logic or data structures
- If a test needs many mocks, it's testing at the wrong level

# Always run these tests before committing changes
When making changes to the codebase, always run the following tests before committing:
1. For discontinuation tracking changes:
   - `python verify_fixed_discontinuation.py`
   - `python verify_streamlit_integration.py`

2. For Streamlit visualization changes:
   - Check visualization output in the `output/debug` directory

3. Always confirm ABS/DES compatibility:
   - Test both ABS and DES implementations with the same configuration
   
4. For any core interface changes (SimulationResults, etc.):
   - Run full test suite: `python scripts/run_tests.py --all`
   - Check integration tests specifically
   - Add regression tests for the specific functionality

# DATA INTEGRITY VERIFICATION PROTOCOL

These protocols MUST be followed for all data manipulation and visualization tasks:

1. **Be explicit about the data structure**: Tell me exactly what fields contain the real data. For example:
   - "The patient visit times are in results['patient_histories'][patient_id]['visits'][i]['time']"
   - "The discontinuation events are marked by visit['is_discontinuation_visit'] == True"

2. **Demand data inspection BEFORE any implementation**:
   ```python
   # First, inspect the data structure
   print("Sample patient data:", patient_histories[first_patient_id])
   print("Visit structure:", patient_histories[first_patient_id]['visits'][0])
   
   # Then, verify the specific values you'll be working with
   print("Time values:", [visit['time'] for visit in patient_histories[first_patient_id]['visits'][:5]])
   print("Discontinuation events:", sum(1 for visit in patient_histories[first_patient_id]['visits'] if visit.get('is_discontinuation_visit')))
   ```

3. **Reject synthetic patterns immediately**: When you see sigmoid curves or smooth transitions, challenge them:
   - "Why are you using sigmoid? Show me where in the data this curve comes from"
   - "This looks too smooth. Show me the actual patient state counts at each time point"
   - "Demonstrate from the raw data how these patterns emerge, not from smoothing algorithms"

4. **Request raw data exports for verification and traceability**:
   ```python
   # Export the actual counts at each time point for verification
   with open('actual_patient_states.csv', 'w') as f:
       f.write("month,active,discontinued_planned,discontinued_admin,...\n")
       for month, counts in sorted(state_counts.items()):
           f.write(f"{month},{counts['active']},{counts['discontinued_planned']},{counts['discontinued_admin']},...\n")
   print("Raw data exported to actual_patient_states.csv for verification")
   ```

5. **Fail fast and loudly on missing data**: Implement explicit error handling:
   ```python
   if 'patient_histories' not in results:
       raise ValueError("ERROR: No patient histories available - cannot create visualization")
       
   if not patient_histories:
       raise ValueError("ERROR: Patient histories dictionary is empty")
       
   # Verify key fields exist in the data structure
   first_patient = next(iter(patient_histories.values()))
   if 'visits' not in first_patient:
       raise ValueError("ERROR: Patient data missing required 'visits' field")
   ```

6. **Document data lineage in code and visualization outputs**:
   ```python
   # Add a data source annotation to all visualizations
   plt.annotate(f"Data source: {data_source_file}\nPatient count: {len(patient_histories)}\nTime period: {start_date} to {end_date}",
               xy=(0.01, 0.01), xycoords='figure fraction', fontsize=8)
   ```

7. **Validate conservation principles in data transforms**:
   ```python
   # Ensure patient count remains constant across transformations
   original_patient_count = len(patient_histories)
   # ... perform data transformation ...
   transformed_patient_count = sum(len(group) for group in patient_groups)
   assert original_patient_count == transformed_patient_count, f"ERROR: Patient count mismatch! Original: {original_patient_count}, After transformation: {transformed_patient_count}"
   ```