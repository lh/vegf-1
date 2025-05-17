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

# Visualization Guidelines
- For visual acuity graphs use an x axis scale running from 0 to 85 and so far as is possible make sure they all have the same vertical height for the scale. This is to maintain a consistent mental model for the user.
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