At the start of each session, use the memory server to retrieve relevant project context and maintain continuity.

## 📁 IMPORTANT: File Organization
**ALWAYS consult WHERE_TO_PUT_THINGS.md before creating new files!**
- Use `workspace/` for temporary development work
- NEVER clutter the root directory with test files
- See WHERE_TO_PUT_THINGS.md for the complete guide

## 📋 Active Implementation Instructions
**IMPORTANT**: Check `instructions.md` in the project root for the current implementation plan and follow it exactly.

### Current Active Implementation: Economic Analysis Features
- **Primary Guide**: `instructions.md` - Economic Analysis Implementation Plan
- **TDD Approach**: `TDD_ECONOMIC_PLAN.md` - Test specifications
- **Design Decisions**: `ECONOMIC_ANALYSIS_PLANNING.md` - Architecture choices
- **Status**: Starting Phase 1 - Core Cost Infrastructure
- **Next Steps**: Write failing tests for CostConfig class, then implement

Automatically store the following in the memory server:
1. Key project context (requirements, architecture decisions)
2. Important code snippets with descriptive tags
3. Design patterns and conventions used in the project
4. Solutions to complex problems for future reference
5. Module/component information with appropriate tags
6. Testing strategies and edge cases

Tag all memories appropriately to enable efficient retrieval in future sessions.

Use Git and github  for version control. You have access to the gh command. Use it.

# Git and GitHub Instructions
1. Use concise, descriptive commit messages that explain the purpose of changes
2. DO NOT add attribution like "Generated with Claude" or "Co-Authored-By" to commits
3. Follow project conventions for branch naming and PR format
4. Include issue numbers in commit messages when applicable
5. When asked to create PRs, use existing PR templates if available

# Development Environment
- This is a development environment. Always git commit and push after changes. Use the gh command for github if needed.
- "When modifying Streamlit components, test changes with test scripts and show the user the results before updating the app"
- **NO SILENT FALLBACKS**: Never add try/except blocks that hide errors or fall back to alternative implementations. Fail fast with clear error messages.
- **TESTING REQUIRES FAILURES**: When testing new features, force their use without fallbacks so errors are visible.
- **EXPLICIT ERRORS**: If something might fail, let it fail with a clear error message rather than silently switching to an alternative.

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
- Quick test to verify Playwright can connect
- Takes a screenshot for verification
- Minimal output, good for CI/CD

#### Interactive Debugging (Recommended)
```bash
# Run test app on different port
streamlit run test_streamlit_app.py --server.port 8503

# Debug in browser with DevTools
node playwright_debug_configurable.js 8503
```
- Opens visible browser window with DevTools
- Console logging and error reporting
- Interactive mode - browser stays open for manual testing
- Press Ctrl+C to exit

#### Advanced Debugging
```bash
node playwright_advanced_debug.js
```
- Video recording of sessions
- Full element analysis
- Comprehensive debug information capture
- Network monitoring

### Port Management
- **Main app**: Use your actual port (usually 8502)
- **Testing**: Use alternate ports (8503, 8504, etc.)
- **Command syntax**: `node script.js [port]`
- **Example**: `node playwright_debug_configurable.js 8504`

### Testing Real vs Test Apps
- **Real app debugging**: `node playwright_debug_configurable.js 8502`
- **Safe testing**: Use `test_streamlit_app.py` on alternate port
- **Port conflicts**: Always specify different port for testing

### Key Files
- `playwright_debug_configurable.js` - Main debugging tool
- `test_streamlit_app.py` - Safe test Streamlit app
- `test_playwright_simple.js` - Quick connection test
- `playwright_advanced_debug.js` - Full-featured debugger

### Best Practices
- ALWAYS use alternate ports for testing to avoid disrupting running apps
- Use the test Streamlit app for initial Playwright verification
- Only debug real apps when necessary and with caution
- Capture screenshots for visual verification
- ONLY run tests against real simulation data, NEVER with synthetic test data
- Verify data integrity in automated tests by checking key values match expected distributions
- When validating visualizations, check the actual data source, not just the visual appearance

# Visualization Guidelines
- For visual acuity graphs use a y-axis scale running from 0 to 85 and so far as is possible make sure they all have the same vertical height for the scale. This is to maintain a consistent mental model for the user.
- X-axis ticks should be at yearly intervals (0, 12, 24, 36, 48, 60 months) for better readability and understanding of time progression
- "For all visualizations, follow Tufte principles documented in meta/visualization_templates.md"
- "Maintain consistent styling across charts with the established color system"

# Styling and Visualization Standards

  1. Single Source of Truth: All colors, opacity values, and styling constants MUST be defined in the central color system
  (visualization.color_system). Never define fallback or alternative values elsewhere.
  2. No Duplicate Definitions: Never redefine or create local copies of styling values. Import all styling constants from the
   central system.
  3. Fix at Source: When encountering styling issues, fix them in the central color system rather than creating workarounds
  in individual components.
  4. Consistent Naming: Always use the established naming conventions from the central system. Don't create alternative names
   for the same concept.
  5. Clean Visualization Style: Follow Tufte principles in all visualizations - remove unnecessary chart elements, use
  minimal styling, and focus on data representation.
  6. No Bounding Lines: Avoid unnecessary bounding boxes, borders, and visual elements that don't contribute to data
  understanding.
  7. Error Handling: If a styling element is missing, report the issue rather than creating a local fallback.
  8. Refactoring Priority: Consider inconsistent styling as a bug that needs immediate attention, not as a feature to be
  worked around.

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

# Always run these tests before committing changes
When making changes to the codebase, always run the following tests before committing:
1. For discontinuation tracking changes:
   - `python verify_fixed_discontinuation.py`
   - `python verify_streamlit_integration.py`

2. For Streamlit visualization changes:
   - Check visualization output in the `output/debug` directory

3. Always confirm ABS/DES compatibility:
   - Test both ABS and DES implementations with the same configuration

# Simulation Management and Performance

## Recent Improvements (2025-06-21)

### Recruitment Modes
- **Fixed Total Mode**: Specify total patients, system calculates monthly rate
- **Constant Rate Mode**: Specify patients/month, continues throughout simulation
- Enables modeling of both clinical trials and real-world steady-state operations

### Simulation File Management
- New naming: `YYYYMMDD-HHMMSS-sim-Xp-Yy` (e.g., `20250124-120530-sim-1000p-5y`)
- Files automatically sort by date/time
- Saved simulations browser with quick actions
- Auto-loads latest simulation in analysis pages

### Performance Optimizations
- Calendar-time transformation now uses vectorized pandas operations
- 10-100x speedup for large datasets (1000+ patients process in seconds)
- Progress indicators show transformation status
- Removed inefficient patient-by-patient loops

### User Experience
- Session state persistence across pages
- One-click navigation to Calendar-Time Analysis or Patient Explorer
- Latest simulation automatically selected in analysis pages
- Enrollment period can extend throughout entire simulation

# DATA INTEGRITY VERIFICATION PROTOCOL

These protocols MUST be followed for all data manipulation and visualization tasks:

  1. Be explicit about the data structure: Tell me exactly what fields contain the real data. For example:
    - "The patient visit times are in results['patient_histories'][patient_id]['visits'][i]['time']"
    - "The discontinuation events are marked by visit['is_discontinuation_visit'] == True"
  
  2. Demand data inspection BEFORE any implementation:
    ```python
    # First, inspect the data structure
    print("Sample patient data:", patient_histories[first_patient_id])
    print("Visit structure:", patient_histories[first_patient_id]['visits'][0])
    
    # Then, verify the specific values you'll be working with
    print("Time values:", [visit['time'] for visit in patient_histories[first_patient_id]['visits'][:5]])
    print("Discontinuation events:", sum(1 for visit in patient_histories[first_patient_id]['visits'] if visit.get('is_discontinuation_visit')))
    ```
  
  3. Reject synthetic patterns immediately: When you see sigmoid curves or smooth transitions, challenge them:
    - "Why are you using sigmoid? Show me where in the data this curve comes from"
    - "This looks too smooth. Show me the actual patient state counts at each time point"
    - "Demonstrate from the raw data how these patterns emerge, not from smoothing algorithms"
  
  4. Request raw data exports for verification and traceability:
    ```python
    # Export the actual counts at each time point for verification
    with open('actual_patient_states.csv', 'w') as f:
        f.write("month,active,discontinued_planned,discontinued_admin,...\n")
        for month, counts in sorted(state_counts.items()):
            f.write(f"{month},{counts['active']},{counts['discontinued_planned']},{counts['discontinued_admin']},...\n")
    print("Raw data exported to actual_patient_states.csv for verification")
    ```
  
  5. Fail fast and loudly on missing data: Implement explicit error handling:
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
  
  6. Document data lineage in code and visualization outputs:
    ```python
    # Add a data source annotation to all visualizations
    plt.annotate(f"Data source: {data_source_file}\nPatient count: {len(patient_histories)}\nTime period: {start_date} to {end_date}",
                xy=(0.01, 0.01), xycoords='figure fraction', fontsize=8)
    ```
  
  7. Validate conservation principles in data transforms:
    ```python
    # Ensure patient count remains constant across transformations
    original_patient_count = len(patient_histories)
    # ... perform data transformation ...
    transformed_patient_count = sum(len(group) for group in patient_groups)
    assert original_patient_count == transformed_patient_count, f"ERROR: Patient count mismatch! Original: {original_patient_count}, After transformation: {transformed_patient_count}"
    ```