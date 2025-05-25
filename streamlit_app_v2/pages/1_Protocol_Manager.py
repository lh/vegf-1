"""
Protocol Manager - Browse and manage protocol specifications.
"""

import streamlit as st
import sys
from pathlib import Path
import yaml
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification

st.set_page_config(page_title="Protocol Manager", page_icon="📋", layout="wide")

st.title("📋 Protocol Manager")
st.markdown("Browse, view, and validate treatment protocol specifications.")

# Protocol directory
PROTOCOL_DIR = Path("protocols/v2")

# Get available protocols
protocol_files = list(PROTOCOL_DIR.glob("*.yaml"))

if not protocol_files:
    st.warning("No protocol files found in protocols/v2/")
    st.stop()

# Sidebar - Protocol selector
st.sidebar.header("Select Protocol")
selected_file = st.sidebar.selectbox(
    "Available Protocols",
    protocol_files,
    format_func=lambda x: x.stem
)

# Load selected protocol
try:
    spec = ProtocolSpecification.from_yaml(selected_file)
    st.session_state.current_protocol = {
        'name': spec.name,
        'version': spec.version,
        'path': str(selected_file),
        'spec': spec
    }
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header(f"{spec.name} v{spec.version}")
        st.markdown(f"**Author:** {spec.author}")
        st.markdown(f"**Description:** {spec.description}")
        st.markdown(f"**Created:** {spec.created_date}")
        
    with col2:
        st.metric("Checksum", spec.checksum[:16] + "...")
        st.metric("Protocol Type", spec.protocol_type)
    
    # Protocol parameters tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Timing Parameters", 
        "Disease Transitions", 
        "Vision Model",
        "Population",
        "Discontinuation"
    ])
    
    with tab1:
        st.subheader("Treatment Timing Parameters")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Min Interval", f"{spec.min_interval_days} days ({spec.min_interval_days/7:.1f} weeks)")
            st.metric("Extension", f"{spec.extension_days} days ({spec.extension_days/7:.1f} weeks)")
        with col2:
            st.metric("Max Interval", f"{spec.max_interval_days} days ({spec.max_interval_days/7:.1f} weeks)")
            st.metric("Shortening", f"{spec.shortening_days} days ({spec.shortening_days/7:.1f} weeks)")
    
    with tab2:
        st.subheader("Disease State Transitions")
        
        # Display transition matrix
        import pandas as pd
        states = ['NAIVE', 'STABLE', 'ACTIVE', 'HIGHLY_ACTIVE']
        matrix_data = []
        for from_state in states:
            row = []
            for to_state in states:
                prob = spec.disease_transitions[from_state][to_state]
                row.append(f"{prob:.2f}")
            matrix_data.append(row)
            
        df = pd.DataFrame(matrix_data, index=states, columns=states)
        st.dataframe(df, use_container_width=True)
        
        # Treatment effect
        st.subheader("Treatment Effect Multipliers")
        st.json(spec.treatment_effect_on_transitions)
    
    with tab3:
        st.subheader("Vision Change Model")
        
        # Create a table of vision changes
        vision_data = []
        for scenario, params in sorted(spec.vision_change_model.items()):
            state, treatment = scenario.rsplit('_', 1)
            vision_data.append({
                'State': state.upper(),
                'Treatment': treatment.capitalize(),
                'Mean Change': params['mean'],
                'Std Dev': params['std']
            })
            
        vision_df = pd.DataFrame(vision_data)
        st.dataframe(vision_df, use_container_width=True, hide_index=True)
    
    with tab4:
        st.subheader("Patient Population")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Baseline Vision Mean", f"{spec.baseline_vision_mean} letters")
            st.metric("Baseline Vision Std", f"{spec.baseline_vision_std} letters")
        with col2:
            st.metric("Vision Range Min", f"{spec.baseline_vision_min} letters")
            st.metric("Vision Range Max", f"{spec.baseline_vision_max} letters")
            
        # Show distribution
        import numpy as np
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(8, 4))
        x = np.linspace(0, 100, 1000)
        mean = spec.baseline_vision_mean
        std = spec.baseline_vision_std
        y = (1/(std * np.sqrt(2*np.pi))) * np.exp(-0.5*((x-mean)/std)**2)
        
        ax.plot(x, y, 'b-', linewidth=2)
        ax.axvline(mean, color='r', linestyle='--', label=f'Mean: {mean}')
        ax.axvline(spec.baseline_vision_min, color='k', linestyle=':', label=f'Min: {spec.baseline_vision_min}')
        ax.axvline(spec.baseline_vision_max, color='k', linestyle=':', label=f'Max: {spec.baseline_vision_max}')
        ax.fill_between(x, 0, y, where=(x >= spec.baseline_vision_min) & (x <= spec.baseline_vision_max), alpha=0.3)
        ax.set_xlabel('Baseline Vision (ETDRS letters)')
        ax.set_ylabel('Probability Density')
        ax.set_title('Baseline Vision Distribution')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    
    with tab5:
        st.subheader("Discontinuation Rules")
        
        rules = spec.discontinuation_rules
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Poor Vision**")
            st.metric("Threshold", f"< {rules['poor_vision_threshold']} letters")
            st.metric("Probability", f"{rules['poor_vision_probability']*100:.0f}% per visit")
            
        with col2:
            st.markdown("**High Injection Count**")
            st.metric("Threshold", f"> {rules['high_injection_count']} injections")
            st.metric("Probability", f"{rules['high_injection_probability']*100:.0f}% per visit")
            
        with col3:
            st.markdown("**Long Treatment**")
            st.metric("Threshold", f"> {rules['long_treatment_months']} months")
            st.metric("Probability", f"{rules['long_treatment_probability']*100:.0f}% per visit")
        
        if 'discontinuation_types' in rules:
            st.markdown("**Discontinuation Types:** " + ", ".join(rules['discontinuation_types']))
    
    # Export options
    st.markdown("---")
    st.subheader("Export Protocol")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download YAML
        yaml_str = yaml.dump(spec.__dict__, default_flow_style=False, sort_keys=False)
        st.download_button(
            label="📥 Download YAML",
            data=yaml_str,
            file_name=f"{spec.name.lower().replace(' ', '_')}_v{spec.version}.yaml",
            mime="text/yaml"
        )
        
    with col2:
        # Download JSON
        json_str = json.dumps(spec.to_audit_log(), indent=2)
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"{spec.name.lower().replace(' ', '_')}_v{spec.version}.json",
            mime="application/json"
        )
        
    with col3:
        # Copy to clipboard button (using session state)
        if st.button("📋 Copy Checksum"):
            st.code(spec.checksum)
            st.success("Checksum displayed above")
    
except Exception as e:
    st.error(f"Error loading protocol: {e}")
    st.exception(e)