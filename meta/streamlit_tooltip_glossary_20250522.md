# Streamlit Tooltip Glossary for Patient State Visualizations

**Created:** 2025-05-22 19:47:00  
**Purpose:** Ready-to-implement tooltip content for streamlit patient state visualizations

## Implementation Notes

This glossary is designed for:
- Hover tooltips on streamgraph visualizations
- Expandable help sections in Streamlit sidebar
- Context-sensitive help bubbles
- Documentation modal dialogs

## Current State View Tooltips

### Active Treatment
**Label:** Active  
**Tooltip:** Currently receiving regular anti-VEGF injections in either loading or maintenance phase. Patients continue treatment per protocol guidelines.

### Retreatment in Progress  
**Label:** Recommencing treatment  
**Tooltip:** Previously discontinued patients now restarting treatment (loading phase). This is a temporary state lasting 1-3 months before returning to active treatment.

### Stable Remission
**Label:** Untreated - remission  
**Tooltip:** Stable patients who reached maximum treatment intervals (16+ weeks) and discontinued treatment. May recommence if disease activity returns.

### Administrative Issues
**Label:** Not booked  
**Tooltip:** Treatment stopped due to administrative barriers such as insurance issues, access problems, or scheduling conflicts. Treatment resumes when resolved.

### Course Complete
**Label:** Not renewed  
**Tooltip:** Completed planned treatment course (typically 12 months). Clinician chose not to continue treatment. May restart new course if needed.

### Unclear Discontinuation
**Label:** Discontinued without reason  
**Tooltip:** Treatment stopped by clinician decision without clear documented medical reason. Cases may require review.

### Poor Visual Outcome (Future)
**Label:** Stopped - poor outcome  
**Tooltip:** Treatment discontinued due to vision declining below threshold (e.g., <30 letters). Currently not implemented in simulation.

## Cumulative State View Tooltips

### Never Discontinued
**Label:** Active  
**Tooltip:** Patients who have never experienced treatment discontinuation since starting therapy.

### Treatment Restart History
**Label:** Retreated  
**Tooltip:** Patients who have experienced at least one treatment restart after a period of discontinuation. Shows cumulative treatment history.

### Planned Discontinuation History
**Label:** Discontinued planned  
**Tooltip:** Patients who have experienced discontinuation due to achieving stable remission (maximum treatment intervals reached).

### Administrative Discontinuation History
**Label:** Discontinued administrative  
**Tooltip:** Patients who have experienced treatment interruption due to administrative barriers or access issues.

### Course Completion History
**Label:** Discontinued duration  
**Tooltip:** Patients who completed their planned treatment course without renewal by clinician decision.

### Unclear Discontinuation History
**Label:** Discontinued  
**Tooltip:** Patients who have been discontinued without clear documented reason in their treatment history.

## Visualization Context Tooltips

### Current vs Cumulative Views
**Current State View:** Shows where patients are RIGHT NOW at each time point. Better for operational planning and resource allocation.

**Cumulative State View:** Shows what patients have EVER experienced. Better for outcome analysis and treatment pattern research.

### Data Conservation
**Conservation Principle:** All visualizations maintain total patient count - every patient is in exactly one state at each time point.

### Clinical Transitions
**Allowed Transitions:** Patients can move between any states based on clinical circumstances. Current state view shows realistic patient flow patterns.

## Implementation Code Snippets

### Streamlit Tooltip Implementation
```python
import streamlit as st

# For plotly charts with custom hover templates
hover_template = {
    'active': 'Active Treatment<br>Currently receiving injections<br>Count: %{y}<extra></extra>',
    'recommencing': 'Recommencing Treatment<br>Temporary retreatment state<br>Count: %{y}<extra></extra>',
    # ... etc
}

# For help bubbles
with st.expander("📖 Understanding Patient States"):
    st.markdown(tooltip_content['current_state_explanation'])
```

### Modal Help Dialog
```python
if st.button("ℹ️ State Definitions"):
    st.modal("Patient State Glossary", content=glossary_content)
```

## Accessibility Notes

- Use clear, jargon-free language
- Provide context for medical abbreviations
- Include visual indicators (icons, colors) with text descriptions
- Ensure tooltips are keyboard accessible
- Provide alternative text for color-coded information

---

**Last Updated:** 2025-05-22 19:47:00  
**Next Steps:** Integrate into streamlit visualization components  
**Dependencies:** streamlit, plotly tooltip system, visualization/color_system.py