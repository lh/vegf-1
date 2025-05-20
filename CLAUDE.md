At the start of each session, use the memory server to retrieve relevant project context and maintain continuity.

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

# Playwright Integration
- Use Playwright for automated testing of the Streamlit application
- All Playwright tests should be run against the local Streamlit server (port 8502)
- Follow the setup instructions in streamlit_app/PLAYWRIGHT.md when using Playwright
- Run the setup script (./streamlit_app/setup-playwright.sh) to ensure browser binaries are installed
- Verify tests work with real data and actual application components
- Use the existing test script (streamlit_app/playwright_streamlit.js) as a template for new tests
- Capture screenshots during tests to provide visual verification of application state

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

# Critical Scientific Tool Principles

**NEVER GENERATE SYNTHETIC DATA**: This is a scientific analysis tool, not a demo
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

These principles are NON-NEGOTIABLE. As the postmortem in meta/streamgraph_synthetic_data_postmortem.md states: 
"In scientific computing, accuracy is paramount. Never invent data. Ever."

# Workflow Reminder
- Every summary should be followed by an offer to git commit and push and update documentation

# VERY IMPORTANT RULWES ABOUT INTEGRITY

  1. Be explicit about the data structure: Tell me exactly what fields contain the real data. For example:
    - "The patient visit times are in results['patient_histories'][patient_id]['visits'][i]['time']"
    - "The discontinuation events are marked by visit['is_discontinuation_visit'] == True"
  2. Demand data inspection first: Make me show you what's actually in the data before plotting:
  # First, inspect the data
  print("Sample patient data:", patient_histories[first_patient_id])
  print("Visit structure:", patient_histories[first_patient_id]['visits'][0])
  3. Reject synthetic data immediately: When you see sigmoid curves or smooth transitions, challenge them:
    - "Why are you using sigmoid? Show me where in the data this curve comes from"
    - "This looks too smooth. Show me the actual patient state counts at each time point"
  4. Request raw data exports: Ask for the actual numbers:
  # Export the actual counts at each time point
  with open('actual_patient_states.csv', 'w') as f:
      f.write("month,active,discontinued_planned,discontinued_admin,...\n")
      f.write(f"{month},{counts['active']},{counts['discontinued_planned']},...\n")
  5. Fail fast on missing data: Insist on error messages when data is missing:
  if 'patient_histories' not in results:
      raise ValueError("No patient histories available - cannot create visualization")