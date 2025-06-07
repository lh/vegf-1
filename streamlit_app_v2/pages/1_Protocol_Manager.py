"""
Protocol Manager - Browse and manage protocol specifications.
"""

import streamlit as st
import sys
from pathlib import Path
import yaml
import json
from datetime import datetime
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from simulation_v2.protocols.protocol_spec import ProtocolSpecification

st.set_page_config(
    page_title="Protocol Manager", 
    page_icon="🦍", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Style Streamlit native buttons to be less obtrusive
st.markdown("""
<style>
    /* Remove red text from ALL Streamlit buttons */
    .stButton > button p {
        color: inherit !important;
    }
    
    /* Remove red active/focus states from all buttons */
    .stButton > button:active,
    .stButton > button:focus,
    .stDownloadButton > button:active,
    .stDownloadButton > button:focus,
    .stFileUploader > div > div > button:active,
    .stFileUploader > div > div > button:focus {
        color: #009688 !important;  /* Teal color */
        border-color: #009688 !important;
        outline: none !important;
        box-shadow: 0 0 0 0.2rem rgba(0, 150, 136, 0.25) !important;
    }
    
    /* Also override any red text that might appear */
    .stButton > button:active p,
    .stButton > button:focus p,
    .stDownloadButton > button:active p,
    .stDownloadButton > button:focus p,
    .stFileUploader > div > div > button:active p,
    .stFileUploader > div > div > button:focus p {
        color: #009688 !important;  /* Teal color */
    }
    
    /* Make file uploader button minimal */
    .stFileUploader > div > div > button {
        background-color: transparent !important;
        border: 1px solid #ddd !important;
        color: #666 !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.875rem !important;
    }
    
    .stFileUploader > div > div > button:hover {
        background-color: #f0f0f0 !important;
        border-color: #999 !important;
    }
    
    /* Make download button minimal */
    .stDownloadButton > button {
        background-color: transparent !important;
        border: 1px solid #ddd !important;
        color: #666 !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.875rem !important;
    }
    
    .stDownloadButton > button:hover {
        background-color: #f0f0f0 !important;
        border-color: #999 !important;
    }
    
    /* Additional styling for file uploader text */
    .stFileUploader label {
        font-size: 0.875rem !important;
        color: #666 !important;
    }
    
    /* Make everything in expanders more compact */
    .streamlit-expanderContent {
        padding: 0.5rem 1rem !important;
    }
    
    .streamlit-expanderContent .stMarkdown {
        margin-bottom: 0.5rem !important;
    }
    
    .streamlit-expanderContent .stButton {
        margin: 0.25rem 0 !important;
    }
    
    /* Make download button even smaller */
    .streamlit-expanderContent .stDownloadButton > button {
        padding: 0.25rem 0.75rem !important;
        font-size: 0.75rem !important;
        min-height: unset !important;
    }
    
    /* Compact file uploader in expander */
    .streamlit-expanderContent .stFileUploader {
        margin-bottom: 0.5rem !important;
    }
    
    .streamlit-expanderContent .stFileUploader > div > div > button {
        padding: 0.25rem 0.75rem !important;
        font-size: 0.75rem !important;
        min-height: unset !important;
    }
    
    /* Reduce caption spacing */
    .streamlit-expanderContent .stCaption {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
    }
    
    /* Make expander headers more compact */
    .streamlit-expanderHeader {
        font-size: 0.875rem !important;
        padding: 0.5rem !important;
    }
    
    /* Reduce overall spacing in Manage section */
    div[data-testid="column"]:has(.streamlit-expander) .stMarkdown {
        margin-bottom: 0.25rem !important;
    }
    
    /* Hide "Drag and drop file here" text */
    .stFileUploader > div > div > small {
        display: none !important;
    }
    
    /* Make the file uploader section even more compact */
    .stFileUploader > div {
        gap: 0.25rem !important;
    }
    
    /* Remove borders from file uploader drop zone */
    .stFileUploader [data-testid="stFileUploadDropzone"] {
        border: none !important;
        background-color: #f8f8f8 !important;
    }
    
    /* Add some spacing between upload and download sections */
    .stFileUploader {
        margin-bottom: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Add parent for utils import
sys.path.append(str(Path(__file__).parent.parent))
from utils.carbon_button_helpers import (
    top_navigation_home_button, ape_button, delete_button,
    navigation_button
)


# Top navigation
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if top_navigation_home_button():
        st.switch_page("APE.py")
with col2:
    st.title("Protocol Manager")
    st.markdown("Browse, view, and validate treatment protocol specifications.")

# Protocol directory - use parent directory path
PROTOCOL_DIR = Path(__file__).parent.parent.parent / "protocols" / "v2"
TEMP_DIR = PROTOCOL_DIR / "temp"

# Create temp directory if it doesn't exist
TEMP_DIR.mkdir(exist_ok=True)

# Clean up old temp files (older than 1 hour)
import time
current_time = time.time()
for temp_file in TEMP_DIR.glob("*.yaml"):
    if current_time - temp_file.stat().st_mtime > 3600:  # 1 hour
        try:
            temp_file.unlink()
        except:
            pass

# Security limits
MAX_PROTOCOLS = 100  # Maximum number of protocols allowed
MAX_FILE_SIZE = 1_048_576  # 1MB max file size

# Get available protocols (separate default and temp)
default_files = list(PROTOCOL_DIR.glob("*.yaml"))
temp_files = list(TEMP_DIR.glob("*.yaml"))
protocol_files = default_files + temp_files

if not protocol_files:
    # Centered upload prompt
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### No protocols available")
        st.markdown("Upload a protocol YAML file to get started.")
        if navigation_button("Return to Home", key="return_home", full_width=True):
            st.switch_page("APE.py")
    st.stop()

# Show subtle info about temporary protocols
if temp_files:
    st.info("Temporary protocols are cleared hourly. Download any you want to keep.")

# Protocol Management Bar
col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

with col1:
    st.subheader("Select Protocol")
    
    # Format function to show default vs temp
    def format_protocol(file):
        name = file.stem
        if file.parent == TEMP_DIR:
            return f"{name} (temporary)"
        else:
            return f"{name}"
    
    # Try to maintain selection across reruns
    if 'selected_protocol_name' in st.session_state:
        # Find the file that matches the stored name
        default_index = 0
        for i, file in enumerate(protocol_files):
            if file.stem == st.session_state.selected_protocol_name:
                default_index = i
                break
    else:
        default_index = 0
    
    selected_file = st.selectbox(
        "Available Protocols",
        protocol_files,
        format_func=format_protocol,
        label_visibility="collapsed",
        index=default_index,
        key="protocol_selector"
    )
    
    # Store the selection for persistence
    if selected_file:
        st.session_state.selected_protocol_name = selected_file.stem

with col2:
    st.subheader(" ")  # Invisible subheader for alignment
    # Single Manage button for upload/download (using save/floppy disk icon)
    if ape_button("Manage", key="manage_btn", icon="save", full_width=True):
        st.session_state.show_manage = not st.session_state.get('show_manage', False)
    
    if st.session_state.get('show_manage', False):
        with st.container():
            # Upload section
            uploaded_file = st.file_uploader(
                "",
                type=['yaml', 'yml'],
                label_visibility="collapsed"
            )
            
            if uploaded_file is not None:
                try:
                    # Check protocol count limit
                    if len(protocol_files) >= MAX_PROTOCOLS:
                        raise ValueError(f"Protocol limit reached ({MAX_PROTOCOLS} files). Please delete some protocols first.")
                    
                    # Check file size
                    file_size = len(uploaded_file.getvalue())
                    if file_size > MAX_FILE_SIZE:
                        raise ValueError(f"File too large. Maximum size is {MAX_FILE_SIZE//1024}KB")
                    
                    # Validate filename
                    filename = uploaded_file.name
                    if not filename.endswith(('.yaml', '.yml')):
                        raise ValueError("Only YAML files are allowed")
                    
                    # Sanitize filename (remove path traversal attempts)
                    safe_filename = Path(filename).name
                    if '..' in safe_filename or '/' in safe_filename:
                        raise ValueError("Invalid filename")
                    
                    # First, validate the YAML can be loaded safely
                    content = uploaded_file.read()
                    uploaded_file.seek(0)  # Reset for later use
                    
                    # Try to parse YAML safely
                    try:
                        test_data = yaml.safe_load(content)
                        if not isinstance(test_data, dict):
                            raise ValueError("Invalid protocol format")
                    except yaml.YAMLError as e:
                        raise ValueError(f"Invalid YAML: {e}")
                    
                    # Try to load as ProtocolSpecification to validate structure
                    validation_path = TEMP_DIR / f"validating_{safe_filename}"
                    with open(validation_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    
                    try:
                        # This will validate all required fields
                        test_spec = ProtocolSpecification.from_yaml(validation_path)
                        
                        # Save with timestamp to avoid collisions
                        base_name = safe_filename.rsplit('.', 1)[0]
                        timestamp = int(time.time())
                        final_filename = f"{base_name}_{timestamp}.yaml"
                        final_path = TEMP_DIR / final_filename
                        
                        validation_path.rename(final_path)
                        
                        st.success(f"Uploaded and validated: {safe_filename}")
                        st.session_state.show_upload = False  # Close the expander
                        st.rerun()
                    except Exception as e:
                        # Clean up temp file on validation failure
                        validation_path.unlink(missing_ok=True)
                        raise ValueError(f"Invalid protocol: {e}")
                    
                except Exception as e:
                    st.error(f"Failed to upload: {e}")
            
            # Download section - only show if a protocol is loaded
            if 'current_protocol' in st.session_state and st.session_state.current_protocol:
                try:
                    # Get the spec from the selected file
                    spec = ProtocolSpecification.from_yaml(selected_file)
                    yaml_str = yaml.dump(spec.to_yaml_dict(), default_flow_style=False, sort_keys=False)
                    
                    if selected_file.parent == TEMP_DIR:
                        st.markdown("<small style='color: #FFA500;'>⚠️ Temporary protocol - download to keep it!</small>", unsafe_allow_html=True)
                    
                    st.download_button(
                        label="Download",
                        data=yaml_str,
                        file_name=f"{spec.name.lower().replace(' ', '_')}_v{spec.version}.yaml",
                        mime="text/yaml",
                        use_container_width=True
                    )
                except:
                    pass  # If spec can't be loaded, just don't show download

with col3:
    st.subheader(" ")  # Invisible subheader for alignment
    # Create a copy with a new name
    if ape_button("Duplicate", key="duplicate_btn", icon="copy", full_width=True):
        st.session_state.show_duplicate = not st.session_state.get('show_duplicate', False)
    
    # Use session state to control popover visibility
    if st.session_state.get('duplicate_success', False):
        st.success("Duplicate created successfully!")
        # Clear the flag after showing
        st.session_state.duplicate_success = False
    
    if st.session_state.get('show_duplicate', False):
        with st.expander("Duplicate Protocol", expanded=True):
            st.info("Create a copy of this protocol with a new name")
            
            new_name = st.text_input("New Protocol Name", value=f"{selected_file.stem} Copy", key="dup_name")
            new_version = st.text_input("Version", value="1.0.1", key="dup_version")
            new_author = st.text_input("Author", value="Your Name", key="dup_author")
            new_description = st.text_area("Description", value=f"Copy of {selected_file.stem}", key="dup_desc")
            
            # Show creating status
            if st.session_state.get('creating_duplicate', False):
                st.info("Creating duplicate...")
            
            # Regular button - requires click
            if ape_button("Create Duplicate", key="create_dup_btn",
                         icon="copy", full_width=True,
                         disabled=st.session_state.get('creating_duplicate', False)):
                try:
                    # Set flag to prevent multiple clicks
                    st.session_state.creating_duplicate = True
                    
                    # Check protocol count limit
                    if len(protocol_files) >= MAX_PROTOCOLS:
                        raise ValueError(f"Protocol limit reached ({MAX_PROTOCOLS} files). Please delete some protocols first.")
                    
                    # Validate new name isn't too long
                    if len(new_name) > 100:
                        raise ValueError("Protocol name too long (max 100 characters)")
                    
                    # Load the original spec data as a dict
                    with open(selected_file) as f:
                        data = yaml.safe_load(f)
                    
                    # Update the metadata
                    data['name'] = new_name
                    data['version'] = new_version
                    data['author'] = new_author
                    data['description'] = new_description
                    data['created_date'] = datetime.now().strftime("%Y-%m-%d")
                    
                    # Always create with timestamp for duplicates to ensure uniqueness
                    base_filename = f"{new_name.lower().replace(' ', '_')}_v{new_version}"
                    timestamp = int(time.time())
                    filename = f"{base_filename}_{timestamp}.yaml"
                    
                    # Ensure filename isn't too long
                    if len(filename) > 255:
                        raise ValueError("Generated filename too long")
                        
                    save_path = TEMP_DIR / filename
                    
                    # Write the modified data
                    with open(save_path, 'w') as f:
                        yaml.dump(data, f, sort_keys=False, default_flow_style=False)
                    
                    # Validate the new file can be loaded
                    test_spec = ProtocolSpecification.from_yaml(save_path)
                    
                    # Set success flag and clear creating flag
                    st.session_state.duplicate_success = True
                    st.session_state.creating_duplicate = False
                    st.session_state.show_duplicate = False  # Close the expander
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create duplicate: {e}")
                    # Clear the flag on error too
                    st.session_state.creating_duplicate = False

with col4:
    st.subheader(" ")  # Invisible subheader for alignment
    # Delete protocol (only temporary ones)
    if selected_file and selected_file.parent == TEMP_DIR:
        if delete_button(key="delete_btn", full_width=True):
            st.session_state.show_delete = not st.session_state.get('show_delete', False)
        
        if st.session_state.get('show_delete', False):
            with st.expander("Delete Protocol", expanded=True):
                # Check if file still exists
                if not selected_file.exists():
                    st.info("This protocol has already been deleted.")
                    if ape_button("Refresh", key="refresh_deleted", icon="play", full_width=True):
                        # Clear the selection
                        if 'selected_protocol_name' in st.session_state:
                            del st.session_state.selected_protocol_name
                        st.rerun()
                else:
                    st.warning("**Delete Protocol**")
                    st.markdown(f"Delete **{selected_file.stem}**?")
                    st.markdown("**This action cannot be undone.**")
                    
                    # For safety, require explicit click (no Enter key shortcut for delete)
                    if delete_button(key=f"delete_{selected_file.stem}", full_width=True):
                        try:
                            selected_file.unlink()
                            # Clear the selection from session state
                            if 'selected_protocol_name' in st.session_state:
                                del st.session_state.selected_protocol_name
                            st.success("Protocol deleted successfully!")
                            st.session_state.show_delete = False  # Close the expander
                            time.sleep(0.5)  # Brief pause to show success
                            st.rerun()
                        except FileNotFoundError:
                            st.error("Protocol already deleted by another user")
                            if 'selected_protocol_name' in st.session_state:
                                del st.session_state.selected_protocol_name
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")
    else:
        # For default protocols, just leave an empty space
        st.empty()

# Import simulation package section
st.markdown("---")
# Import functionality removed - now in Simulations page
st.markdown("---")

# Load selected protocol
try:
    spec = ProtocolSpecification.from_yaml(selected_file)
    st.session_state.current_protocol = {
        'name': spec.name,
        'version': spec.version,
        'path': str(selected_file),
        'spec': spec
    }
    
    
    # Main content with prominent action button
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.header(f"{spec.name} v{spec.version}")
        st.markdown(f"**Author:** {spec.author}")
        st.markdown(f"**Description:** {spec.description}")
        st.markdown(f"**Protocol Type:** {spec.protocol_type}")
        
    with col2:
        # Move technical details to a single compact line at bottom
        st.markdown("")  # Spacer
        st.markdown("")  # Spacer
        st.markdown("")  # Spacer
        st.caption(f"Created: {spec.created_date} • {spec.checksum[:8]}...")
        
    with col3:
        # Now we have room for a bigger button!
        st.markdown("")  # Small spacer
        
        if ape_button("Next: Run Simulation", key="main_sim_btn",
                     icon="play", full_width=True,
                     is_primary_action=True):
            st.switch_page("pages/2_Run_Simulation.py")
    
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
    
    # Subtle reminder for temp protocols
    if selected_file.parent == TEMP_DIR:
        st.markdown("---")
        st.caption("This temporary protocol expires in 1 hour")
    
except Exception as e:
    st.error(f"Error loading protocol: {e}")
    st.exception(e)