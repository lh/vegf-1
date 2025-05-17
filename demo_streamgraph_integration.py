"""Demo script to show streamgraph integration in streamlit."""

import streamlit as st
import matplotlib.pyplot as plt
from streamlit_app.streamgraph_discontinuation import generate_enhanced_discontinuation_streamgraph
from streamlit_app.discontinuation_chart import generate_enhanced_discontinuation_plot

# Create test data
sample_results = {
    "population_size": 100,
    "duration_years": 5,
    "discontinuation_counts": {
        "Planned": 15,
        "Administrative": 8,
        "Not Renewed": 12,
        "Premature": 10
    },
    "recurrences": {
        "total": 20,
        "by_type": {
            "stable_max_interval": 9,
            "random_administrative": 2,
            "treatment_duration": 2,
            "premature": 7
        }
    }
}

# Streamlit app
st.set_page_config(page_title="Streamgraph Demo", layout="wide")
st.title("Patient Cohort Streamgraph Visualization")

# Show both visualizations
st.subheader("Patient Cohort Flow (Streamgraph)")
streamgraph = generate_enhanced_discontinuation_streamgraph(sample_results)
st.pyplot(streamgraph)
st.caption("Streamgraph showing patient lifecycle through treatment states")

st.subheader("Discontinuation Breakdown (Bar Chart)")
bar_chart = generate_enhanced_discontinuation_plot(sample_results)
st.pyplot(bar_chart)
st.caption("Discontinuation reasons by retreatment status")

# Show comparison
st.write("""
### Comparison

**Streamgraph Advantages:**
- Shows cohort size changes over time
- Visualizes patient flow between states
- Clear representation of the treatment lifecycle
- Can highlight newly discontinued/retreated patients

**Bar Chart Advantages:**
- Clear quantitative comparison
- Easy to read exact numbers
- Simple categorization by type
""")