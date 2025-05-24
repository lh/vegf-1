# Future Enhancements for VEGF Simulation Platform

This document tracks proposed enhancements and design considerations for the VEGF simulation platform.

## 1. In-Simulation Documentation System

### Concept
Add accessible internal documentation within the simulation interface, available via pop-ups or similar UI elements.

### Rationale
Many design decisions in the simulation are based on clinical evidence, statistical models, or specific assumptions. Making this documentation available at the point of use would:
- Help users understand why certain choices were made
- Provide transparency about model assumptions
- Reduce support burden by answering common questions
- Preserve institutional knowledge

### Proposed Implementation
1. **Toggle Control**: Add a checkbox labeled "Show Documentation" in settings or help menu
2. **Progressive Disclosure**:
   - Level 1: Tooltips with brief explanations (1-2 sentences)
   - Level 2: Pop-ups with detailed explanations and references
   - Level 3: Links to full technical documentation
3. **Contextual Placement**: Documentation icons (?) next to relevant UI elements
4. **Documentation Types**:
   - Model assumptions (e.g., why VA follows certain distributions)
   - Parameter choices (e.g., why specific discontinuation thresholds)
   - Visualization decisions (e.g., why 0-85 range for VA)
   - Statistical methods (e.g., confidence interval calculations)

### Considerations
- Keep documentation non-technical for general users
- Maintain separation between user docs and developer docs
- Ensure documentation updates are part of the development workflow
- Consider i18n/internationalization for future

---

## 2. Discrete Event Simulation (DES) Implementation

**Task**: Implement DES alongside existing Agent-Based Simulation (ABS)

---

## 3. Cohort Size Visualization

**Task**: Add cohort size/survival curve visualization (possibly sinusoidal?)

**Notes**: Need to distinguish between:
- Number of measurements (current implementation)
- Actual cohort size (patients still in study)
- Consider Kaplan-Meier style survival curves

---

## 4. Investigate Narrow Starting VA Distribution

**Task**: Investigate why initial visual acuity distribution appears narrow

**Potential areas to explore**:
- Data initialization in patient generators
- Distribution parameters in configuration
- Sampling methodology

---

## 5. Refactor simulation_runner.py

**Task**: Refactor simulation_runner.py for better maintainability

**Goals**:
- Break down large functions
- Separate visualization from data processing
- Improve testability
- Better error handling
- Consistent pattern usage

---

## Implementation Priority

To be determined based on:
1. User feedback
2. Clinical relevance
3. Technical dependencies
4. Available resources

## Notes

These enhancements are tracked here for future consideration. Each should be properly scoped and designed before implementation.