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
    page_icon="📋", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add parent for utils import
sys.path.append(str(Path(__file__).parent.parent))
from utils.button_styling import style_navigation_buttons

# Apply our button styling
style_navigation_buttons()


# Top navigation
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if st.button("🦍 Home", key="top_home"):
        st.switch_page("APE.py")
with col2:
    st.title("📋 Protocol Manager")
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
    st.warning("No protocol files found.")
    st.info("Upload a protocol YAML file to get started.")
    
    # Add navigation button to home
    if st.button("🦍 **Return to Home**", use_container_width=True):
        st.switch_page("APE.py")
    st.stop()

# Show warning only if there are temporary protocols and user hasn't dismissed it
if temp_files and not st.session_state.get('dismissed_temp_warning', False):
    warning_col1, warning_col2 = st.columns([10, 1])
    with warning_col1:
        st.warning("⚠️ **Important**: User-created protocols are temporary and shared. They may be modified by others and are cleared hourly. **Always download protocols you want to keep!**")
    with warning_col2:
        if st.button("✕", key="dismiss_warning", help="Dismiss this warning"):
            st.session_state.dismissed_temp_warning = True
            st.rerun()

# Protocol Management Bar
col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

with col1:
    st.subheader("Select Protocol")
    
    # Format function to show default vs temp
    def format_protocol(file):
        name = file.stem
        if file.parent == TEMP_DIR:
            return f"📝 {name} (temporary)"
        else:
            return f"📌 {name} (default)"
    
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
    # Upload new protocol
    with st.popover("📤 Upload", use_container_width=True):
        st.markdown("**Upload Protocol File**")
        
        # File uploader doesn't need a form since it auto-submits
        uploaded_file = st.file_uploader(
            "Choose a YAML file",
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
                    
                    st.success(f"✅ Uploaded and validated {safe_filename}")
                    st.rerun()
                except Exception as e:
                    # Clean up temp file on validation failure
                    validation_path.unlink(missing_ok=True)
                    raise ValueError(f"Invalid protocol: {e}")
                    
            except Exception as e:
                st.error(f"Failed to upload: {e}")

with col3:
    st.subheader(" ")  # Invisible subheader for alignment
    # Create a copy with a new name
    # Use session state to control popover visibility
    if st.session_state.get('duplicate_success', False):
        st.success("✅ Duplicate created successfully!")
        # Clear the flag after showing
        st.session_state.duplicate_success = False
    
    with st.popover("📝 Duplicate", use_container_width=True):
        st.markdown("**Duplicate Protocol**")
        st.info("Create a copy of this protocol with a new name")
        
        new_name = st.text_input("New Protocol Name", value=f"{selected_file.stem} Copy", key="dup_name")
        new_version = st.text_input("Version", value="1.0.1", key="dup_version")
        new_author = st.text_input("Author", value="Your Name", key="dup_author")
        new_description = st.text_area("Description", value=f"Copy of {selected_file.stem}", key="dup_desc")
        
        # Show creating status
        if st.session_state.get('creating_duplicate', False):
            st.info("✨ Creating duplicate...")
        
        # Regular button - requires click
        if st.button("📝 Create Duplicate", use_container_width=True, 
                     disabled=st.session_state.get('creating_duplicate', False),
                     key="create_dup_btn"):
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
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create duplicate: {e}")
                # Clear the flag on error too
                st.session_state.creating_duplicate = False

with col4:
    st.subheader(" ")  # Invisible subheader for alignment
    # Download button placeholder - will be populated after spec is loaded
    download_placeholder = st.empty()

with col5:
    st.subheader(" ")  # Invisible subheader for alignment
    # Delete protocol (only temporary ones)
    if selected_file and selected_file.parent == TEMP_DIR:
        with st.popover("🗑️ Delete", use_container_width=True):
            # Check if file still exists
            if not selected_file.exists():
                st.info("This protocol has already been deleted.")
                if st.button("🔄 Refresh", use_container_width=True):
                    # Clear the selection
                    if 'selected_protocol_name' in st.session_state:
                        del st.session_state.selected_protocol_name
                    st.rerun()
            else:
                st.warning("**Delete Protocol**")
                st.markdown(f"Delete **{selected_file.stem}**?")
                st.markdown("⚠️ This action cannot be undone.")
                
                # For safety, require explicit click (no Enter key shortcut for delete)
                if st.button("🗑️ Confirm Delete", type="secondary", use_container_width=True, 
                           key=f"delete_{selected_file.stem}"):
                    try:
                        selected_file.unlink()
                        # Clear the selection from session state
                        if 'selected_protocol_name' in st.session_state:
                            del st.session_state.selected_protocol_name
                        st.success("✅ Protocol deleted successfully!")
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

# Load selected protocol
try:
    spec = ProtocolSpecification.from_yaml(selected_file)
    st.session_state.current_protocol = {
        'name': spec.name,
        'version': spec.version,
        'path': str(selected_file),
        'spec': spec
    }
    
    # Now populate the download button
    with download_placeholder.container():
        # Use the proper conversion method
        yaml_str = yaml.dump(spec.to_yaml_dict(), default_flow_style=False, sort_keys=False)
        
        # Emphasize download for temp files
        if selected_file.parent == TEMP_DIR:
            label = "💾 Download"
            help_text = "Download this temporary protocol before it expires!"
        else:
            label = "📥 Download"
            help_text = "Download protocol as YAML"
            
        st.download_button(
            label=label,
            data=yaml_str,
            file_name=f"{spec.name.lower().replace(' ', '_')}_v{spec.version}.yaml",
            mime="text/yaml",
            use_container_width=True
        )
    
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
        
        if st.button("🚀 **Next: Simulation**\n\n→", 
                    use_container_width=True,
                    key="main_sim_btn"):
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
    
    # Just show reminder for temp protocols, no duplicate button
    if selected_file.parent == TEMP_DIR:
        st.markdown("---")
        st.info("💾 **Remember to download!** This temporary protocol will be deleted after 1 hour.")
    
except Exception as e:
    st.error(f"Error loading protocol: {e}")
    st.exception(e)