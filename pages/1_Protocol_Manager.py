"""
Protocol Manager - Browse and manage protocol specifications.
"""

import streamlit as st
from pathlib import Path
import yaml
import json
from datetime import datetime
import re
import pandas as pd

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from ape.utils.startup_redirect import handle_page_startup
from simulation_v2.models.baseline_vision_distributions import (
    NormalDistribution, BetaWithThresholdDistribution, UniformDistribution
)

st.set_page_config(
    page_title="Protocol Manager", 
    page_icon="📋", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Check for startup redirect
handle_page_startup("protocol_manager")

# Import UI components
from ape.components.ui.workflow_indicator import workflow_progress_indicator, consistent_button_bar

# Show workflow progress
workflow_progress_indicator("protocol")

# Minimal CSS for clean interface
st.markdown("""
<style>
    /* Hide "Drag and drop file here" text */
    .stFileUploader > div > div > small {
        display: none !important;
    }
    
    /* Clean file uploader drop zone */
    .stFileUploader [data-testid="stFileUploadDropzone"] {
        border: 1px dashed #ddd !important;
        background-color: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# Add parent for utils import
from ape.utils.carbon_button_helpers import (
    ape_button, delete_button,
    navigation_button
)


def draw_baseline_vision_distribution(dist_type, params, session_prefix="edit"):
    """
    Draw the baseline vision distribution based on current parameters.
    
    Args:
        dist_type: Type of distribution ('normal', 'beta_with_threshold', 'uniform')
        params: Dictionary of parameters for the distribution
        session_prefix: Prefix for session state keys ('edit' or 'tb_edit')
    """
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy import stats
    
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.linspace(0, 100, 1000)
    
    try:
        if dist_type == "normal":
            # Get parameters from session state or defaults
            mean = float(st.session_state.get(f'{session_prefix}_pop_mean', params.get('mean', 70)))
            std = float(st.session_state.get(f'{session_prefix}_pop_std', params.get('std', 10)))
            min_val = int(st.session_state.get(f'{session_prefix}_pop_min', params.get('min', 20)))
            max_val = int(st.session_state.get(f'{session_prefix}_pop_max', params.get('max', 90)))
            
            # Create distribution
            dist = NormalDistribution(mean=mean, std=std, min_value=min_val, max_value=max_val)
            
            # Plot PDF
            y = stats.norm.pdf(x, mean, std)
            ax.plot(x, y, 'b-', linewidth=2, label=f'Normal(μ={mean:.0f}, σ={std:.0f})')
            
            # Shade allowed range
            ax.fill_between(x, 0, y, where=(x >= min_val) & (x <= max_val), 
                           alpha=0.3, color='blue', label=f'Range: [{min_val}, {max_val}]')
            
        elif dist_type == "beta_with_threshold":
            # Get parameters from session state or defaults
            alpha = float(st.session_state.get(f'{session_prefix}_beta_alpha', params.get('alpha', 3.5)))
            beta = float(st.session_state.get(f'{session_prefix}_beta_beta', params.get('beta', 2.0)))
            min_val = int(st.session_state.get(f'{session_prefix}_beta_min', params.get('min', 5)))
            max_val = int(st.session_state.get(f'{session_prefix}_beta_max', params.get('max', 98)))
            threshold = int(st.session_state.get(f'{session_prefix}_beta_threshold', params.get('threshold', 70)))
            reduction = float(st.session_state.get(f'{session_prefix}_beta_reduction', params.get('threshold_reduction', 0.6)))
            
            # Create distribution
            dist = BetaWithThresholdDistribution(
                alpha=alpha, beta=beta, min_value=min_val, max_value=max_val,
                threshold=threshold, threshold_reduction=reduction
            )
            
            # Plot using the distribution's internal PDF
            ax.plot(dist.x_values, dist.pdf, 'orange', linewidth=2, 
                   label=f'Beta(α={alpha:.1f}, β={beta:.1f}) + threshold')
            
            # Show threshold
            ax.axvline(threshold, color='red', linestyle='--', alpha=0.5, 
                      label=f'Threshold: {threshold}')
            
            # Calculate and show statistics
            samples = [dist.sample() for _ in range(5000)]
            mean_val = np.mean(samples)
            pct_above_70 = sum(s > 70 for s in samples) / len(samples) * 100
            
            ax.text(0.02, 0.95, f'Mean: {mean_val:.1f}\n% > 70: {pct_above_70:.1f}%', 
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
        elif dist_type == "uniform":
            # Get parameters from session state or defaults
            min_val = int(st.session_state.get(f'{session_prefix}_uniform_min', params.get('min', 20)))
            max_val = int(st.session_state.get(f'{session_prefix}_uniform_max', params.get('max', 90)))
            
            # Create distribution
            dist = UniformDistribution(min_value=min_val, max_value=max_val)
            
            # Plot uniform distribution
            y = np.zeros_like(x)
            mask = (x >= min_val) & (x <= max_val)
            y[mask] = 1.0 / (max_val - min_val)
            ax.plot(x, y, 'g-', linewidth=2, label=f'Uniform[{min_val}, {max_val}]')
            ax.fill_between(x, 0, y, where=mask, alpha=0.3, color='green')
            
    except (ValueError, TypeError) as e:
        # If parameters are invalid, show error message
        ax.text(0.5, 0.5, f'Invalid parameters:\n{str(e)}', 
               transform=ax.transAxes, ha='center', va='center',
               bbox=dict(boxstyle='round', facecolor='red', alpha=0.3))
    
    ax.set_xlabel('Baseline Vision (ETDRS letters)')
    ax.set_ylabel('Probability Density')
    ax.set_title('Baseline Vision Distribution Preview')
    ax.set_xlim(0, 100)
    ax.set_ylim(bottom=0)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    return fig


# Remove redundant title - page name is sufficient

# Protocol directories - both standard and time-based
STANDARD_PROTOCOL_DIR = Path(__file__).parent.parent / "protocols" / "v2"
TIME_BASED_PROTOCOL_DIR = Path(__file__).parent.parent / "protocols" / "v2_time_based"
TEMP_DIR = STANDARD_PROTOCOL_DIR / "temp"

# Create directories if they don't exist
STANDARD_PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)
TIME_BASED_PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

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

# Get available protocols (standard, time-based, and temp)
standard_files = list(STANDARD_PROTOCOL_DIR.glob("*.yaml"))
time_based_files = list(TIME_BASED_PROTOCOL_DIR.glob("*.yaml"))
temp_files = list(TEMP_DIR.glob("*.yaml"))

# Combine all protocol files with type information
protocol_files = []
for f in standard_files:
    protocol_files.append((f, "standard"))
for f in time_based_files:
    protocol_files.append((f, "time_based"))
for f in temp_files:
    protocol_files.append((f, "temp"))

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

# Protocol selection
st.subheader("Select Protocol")

# Format function to show protocol type
def format_protocol(file_info):
    file, ptype = file_info
    name = file.stem
    if ptype == "temp":
        return f"{name} (temporary)"
    elif ptype == "time_based":
        return f"{name} [TIME-BASED]"
    else:
        return f"{name} [STANDARD]"

# Try to maintain selection across reruns
if 'selected_protocol_name' in st.session_state:
    # Find the file that matches the stored name
    default_index = 0
    for i, (file, ptype) in enumerate(protocol_files):
        if file.stem == st.session_state.selected_protocol_name:
            default_index = i
            break
else:
    default_index = 0

# Select protocol on its own line
selected_item = st.selectbox(
    "Available Protocols",
    protocol_files,
    format_func=format_protocol,
    label_visibility="collapsed",
    index=default_index,
    key="protocol_selector"
)

# Extract file and type from selected item
if selected_item:
    selected_file, protocol_type = selected_item
    st.session_state.selected_protocol_name = selected_file.stem
    st.session_state.selected_protocol_type = protocol_type
else:
    selected_file = None
    protocol_type = None

# Action buttons in 4 equal columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Edit button (only for temporary protocols)
    if selected_file and protocol_type == "temp":
        if ape_button("Edit", key="edit_btn", full_width=True):
            st.session_state.edit_mode = not st.session_state.get('edit_mode', False)
    else:
        # For default protocols, show a disabled ghost button
        ape_button("Edit", key="edit_btn_disabled", full_width=True, disabled=True)

with col2:
    # Create a copy with a new name
    if ape_button("Duplicate", key="duplicate_btn", icon="copy", full_width=True):
        st.session_state.show_duplicate = not st.session_state.get('show_duplicate', False)

with col3:
    # Delete protocol (only temporary ones)
    if selected_file and protocol_type == "temp":
        if delete_button(key="delete_btn", full_width=True):
            st.session_state.show_delete = not st.session_state.get('show_delete', False)
    else:
        # For default protocols, show a disabled ghost button
        delete_button(key="delete_btn_disabled", full_width=True, disabled=True)

with col4:
    if ape_button("Import/Export", 
                  key="toggle_import_export",
                  full_width=True,
                  icon="save"):
        st.session_state.show_manage = not st.session_state.get('show_manage', False)

# Show manage panel if toggled
if st.session_state.get('show_manage', False):
    # Create columns with the panel in the 4th column
    panel_col1, panel_col2, panel_col3, panel_col4 = st.columns(4)
    with panel_col4:
        # Upload section
        st.markdown("**Import**")
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
                    st.markdown("<small style='color: #FFA500;'>Temporary protocol - download to keep it!</small>", unsafe_allow_html=True)

                st.download_button(
                    label="Download",
                    data=yaml_str,
                    file_name=f"{spec.name.lower().replace(' ', '_')}_v{spec.version}.yaml",
                    mime="text/yaml",
                    use_container_width=True
                )
            except:
                pass  # If spec can't be loaded, just don't show download

# Handle duplicate dialog
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
                    if protocol_type == "time_based":
                        from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
                        test_spec = TimeBasedProtocolSpecification.from_yaml(save_path)
                    else:
                        test_spec = ProtocolSpecification.from_yaml(save_path)
                    
                    # Select the newly created duplicate
                    st.session_state.selected_protocol_name = save_path.stem
                    
                    # Set success flag and clear creating flag
                    st.session_state.duplicate_success = True
                    st.session_state.creating_duplicate = False
                    st.session_state.show_duplicate = False  # Close the expander
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create duplicate: {e}")
                    # Clear the flag on error too
                    st.session_state.creating_duplicate = False

# Handle delete dialog
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

# Import functionality removed - now in Simulations page

# Import time-based protocol spec if needed
if protocol_type == "time_based":
    from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification

# Load selected protocol
try:
    if protocol_type == "time_based":
        # Load as time-based protocol
        spec = TimeBasedProtocolSpecification.from_yaml(selected_file)
        st.session_state.current_protocol = {
            'name': spec.name,
            'version': spec.version,
            'path': str(selected_file),
            'spec': spec,
            'type': 'time_based'
        }
    else:
        # Load as standard protocol
        spec = ProtocolSpecification.from_yaml(selected_file)
        st.session_state.current_protocol = {
            'name': spec.name,
            'version': spec.version,
            'path': str(selected_file),
            'spec': spec,
            'type': 'standard'
        }
    
    
    # Main content header
    st.header(f"{spec.name} v{spec.version}")
    
    # Show edit mode controls if in edit mode
    if st.session_state.get('edit_mode', False) and protocol_type == "temp":
        st.warning("**Edit Mode** - Make changes below and save when ready")
        save_col, cancel_col, _, _ = st.columns(4)
        with save_col:
            if ape_button("Save Changes", key="save_changes", is_primary_action=True, full_width=True):
                try:
                    # Load the current YAML data
                    with open(selected_file) as f:
                        data = yaml.safe_load(f)
                    
                    # Update metadata if edited
                    if 'edit_author' in st.session_state:
                        data['author'] = st.session_state.edit_author
                    if 'edit_description' in st.session_state:
                        data['description'] = st.session_state.edit_description
                    
                    # Update timing parameters if edited
                    if 'edit_min_interval' in st.session_state and st.session_state.edit_min_interval.isdigit():
                        data['min_interval_days'] = int(st.session_state.edit_min_interval)
                    if 'edit_max_interval' in st.session_state and st.session_state.edit_max_interval.isdigit():
                        data['max_interval_days'] = int(st.session_state.edit_max_interval)
                    if 'edit_extension' in st.session_state and st.session_state.edit_extension.isdigit():
                        data['extension_days'] = int(st.session_state.edit_extension)
                    if 'edit_shortening' in st.session_state and st.session_state.edit_shortening.isdigit():
                        data['shortening_days'] = int(st.session_state.edit_shortening)
                    
                    # Update disease transitions if edited
                    states = ['NAIVE', 'STABLE', 'ACTIVE', 'HIGHLY_ACTIVE']
                    for from_state in states:
                        for to_state in states:
                            key = f'edit_trans_{from_state}_{to_state}'
                            if key in st.session_state:
                                try:
                                    value = float(st.session_state[key])
                                    # Ensure transitions TO NAIVE from other states remain 0
                                    if to_state == 'NAIVE' and from_state != 'NAIVE':
                                        value = 0.0
                                    data['disease_transitions'][from_state][to_state] = value
                                except:
                                    pass  # Skip invalid values
                    
                    # Update treatment effect multipliers if edited
                    for from_state in states:
                        for to_state in states:
                            key = f'edit_mult_{from_state}_{to_state}'
                            if key in st.session_state:
                                try:
                                    value = float(st.session_state[key])
                                    # Initialize structure if needed
                                    if from_state not in data.get('treatment_effect_on_transitions', {}):
                                        data.setdefault('treatment_effect_on_transitions', {})[from_state] = {'multipliers': {}}
                                    data['treatment_effect_on_transitions'][from_state]['multipliers'][to_state] = value
                                except:
                                    pass  # Skip invalid values
                    
                    # Update vision model parameters if edited
                    for state in states:
                        for treatment in ['treated', 'untreated']:
                            scenario = f"{state.lower()}_{treatment}"
                            mean_key = f'edit_vision_{scenario}_mean'
                            std_key = f'edit_vision_{scenario}_std'
                            
                            if mean_key in st.session_state:
                                try:
                                    data['vision_change_model'][scenario]['mean'] = float(st.session_state[mean_key])
                                except:
                                    pass
                            
                            if std_key in st.session_state:
                                try:
                                    data['vision_change_model'][scenario]['std'] = float(st.session_state[std_key])
                                except:
                                    pass
                    
                    # Update population parameters if edited
                    if 'edit_dist_type' in st.session_state:
                        dist_type = st.session_state.edit_dist_type
                        
                        if dist_type == "normal":
                            # Update normal distribution parameters
                            if 'edit_pop_mean' in st.session_state:
                                try:
                                    data['baseline_vision']['mean'] = float(st.session_state.edit_pop_mean)
                                except:
                                    pass
                            if 'edit_pop_std' in st.session_state:
                                try:
                                    data['baseline_vision']['std'] = float(st.session_state.edit_pop_std)
                                except:
                                    pass
                            if 'edit_pop_min' in st.session_state and st.session_state.edit_pop_min.isdigit():
                                data['baseline_vision']['min'] = int(st.session_state.edit_pop_min)
                            if 'edit_pop_max' in st.session_state and st.session_state.edit_pop_max.isdigit():
                                data['baseline_vision']['max'] = int(st.session_state.edit_pop_max)
                            
                            # Remove baseline_vision_distribution if switching to normal
                            if 'baseline_vision_distribution' in data:
                                del data['baseline_vision_distribution']
                                
                        elif dist_type == "beta_with_threshold":
                            # Create/update beta distribution
                            beta_dist = {
                                'type': 'beta_with_threshold'
                            }
                            
                            if 'edit_beta_alpha' in st.session_state:
                                try:
                                    beta_dist['alpha'] = float(st.session_state.edit_beta_alpha)
                                except:
                                    beta_dist['alpha'] = 3.5
                            
                            if 'edit_beta_beta' in st.session_state:
                                try:
                                    beta_dist['beta'] = float(st.session_state.edit_beta_beta)
                                except:
                                    beta_dist['beta'] = 2.0
                                    
                            if 'edit_beta_min' in st.session_state:
                                try:
                                    beta_dist['min'] = int(st.session_state.edit_beta_min)
                                except:
                                    beta_dist['min'] = 5
                                    
                            if 'edit_beta_max' in st.session_state:
                                try:
                                    beta_dist['max'] = int(st.session_state.edit_beta_max)
                                except:
                                    beta_dist['max'] = 98
                                    
                            if 'edit_beta_threshold' in st.session_state:
                                try:
                                    beta_dist['threshold'] = int(st.session_state.edit_beta_threshold)
                                except:
                                    beta_dist['threshold'] = 70
                                    
                            if 'edit_beta_reduction' in st.session_state:
                                try:
                                    beta_dist['threshold_reduction'] = float(st.session_state.edit_beta_reduction)
                                except:
                                    beta_dist['threshold_reduction'] = 0.6
                            
                            data['baseline_vision_distribution'] = beta_dist
                            
                            # Update baseline_vision to match beta expectations
                            data['baseline_vision']['mean'] = 58
                            data['baseline_vision']['std'] = 15
                            data['baseline_vision']['min'] = beta_dist.get('min', 5)
                            data['baseline_vision']['max'] = beta_dist.get('max', 98)
                            
                        elif dist_type == "uniform":
                            # Create/update uniform distribution
                            uniform_dist = {
                                'type': 'uniform'
                            }
                            
                            if 'edit_uniform_min' in st.session_state:
                                try:
                                    uniform_dist['min'] = int(st.session_state.edit_uniform_min)
                                    data['baseline_vision']['min'] = uniform_dist['min']
                                except:
                                    pass
                                    
                            if 'edit_uniform_max' in st.session_state:
                                try:
                                    uniform_dist['max'] = int(st.session_state.edit_uniform_max)
                                    data['baseline_vision']['max'] = uniform_dist['max']
                                except:
                                    pass
                            
                            data['baseline_vision_distribution'] = uniform_dist
                    else:
                        # Legacy update for protocols without distribution type
                        if 'edit_pop_mean' in st.session_state:
                            try:
                                data['baseline_vision']['mean'] = float(st.session_state.edit_pop_mean)
                            except:
                                pass
                        if 'edit_pop_std' in st.session_state:
                            try:
                                data['baseline_vision']['std'] = float(st.session_state.edit_pop_std)
                            except:
                                pass
                        if 'edit_pop_min' in st.session_state and st.session_state.edit_pop_min.isdigit():
                            data['baseline_vision']['min'] = int(st.session_state.edit_pop_min)
                        if 'edit_pop_max' in st.session_state and st.session_state.edit_pop_max.isdigit():
                            data['baseline_vision']['max'] = int(st.session_state.edit_pop_max)
                    
                    # Update discontinuation rules if edited
                    if 'edit_disc_pv_thresh' in st.session_state and st.session_state.edit_disc_pv_thresh.isdigit():
                        data['discontinuation_rules']['poor_vision_threshold'] = int(st.session_state.edit_disc_pv_thresh)
                    if 'edit_disc_pv_prob' in st.session_state:
                        try:
                            data['discontinuation_rules']['poor_vision_probability'] = float(st.session_state.edit_disc_pv_prob)
                        except:
                            pass
                    if 'edit_disc_hi_thresh' in st.session_state and st.session_state.edit_disc_hi_thresh.isdigit():
                        data['discontinuation_rules']['high_injection_count'] = int(st.session_state.edit_disc_hi_thresh)
                    if 'edit_disc_hi_prob' in st.session_state:
                        try:
                            data['discontinuation_rules']['high_injection_probability'] = float(st.session_state.edit_disc_hi_prob)
                        except:
                            pass
                    if 'edit_disc_lt_thresh' in st.session_state and st.session_state.edit_disc_lt_thresh.isdigit():
                        data['discontinuation_rules']['long_treatment_months'] = int(st.session_state.edit_disc_lt_thresh)
                    if 'edit_disc_lt_prob' in st.session_state:
                        try:
                            data['discontinuation_rules']['long_treatment_probability'] = float(st.session_state.edit_disc_lt_prob)
                        except:
                            pass
                    if 'edit_disc_types' in st.session_state:
                        # Parse discontinuation types from comma-separated input
                        types = [t.strip() for t in st.session_state.edit_disc_types.split(',') if t.strip()]
                        if types:
                            data['discontinuation_rules']['discontinuation_types'] = types
                    
                    # For time-based protocols, save parameter file changes
                    if protocol_type == "time_based":
                        # Handle baseline vision distribution updates
                        if 'tb_edit_dist_type' in st.session_state:
                            dist_type = st.session_state.tb_edit_dist_type
                            
                            if dist_type == "normal":
                                # Update normal distribution parameters
                                if 'tb_edit_pop_mean' in st.session_state:
                                    try:
                                        data['baseline_vision']['mean'] = float(st.session_state.tb_edit_pop_mean)
                                    except:
                                        pass
                                if 'tb_edit_pop_std' in st.session_state:
                                    try:
                                        data['baseline_vision']['std'] = float(st.session_state.tb_edit_pop_std)
                                    except:
                                        pass
                                if 'tb_edit_pop_min' in st.session_state and st.session_state.tb_edit_pop_min.isdigit():
                                    data['baseline_vision']['min'] = int(st.session_state.tb_edit_pop_min)
                                if 'tb_edit_pop_max' in st.session_state and st.session_state.tb_edit_pop_max.isdigit():
                                    data['baseline_vision']['max'] = int(st.session_state.tb_edit_pop_max)
                                
                                # Remove baseline_vision_distribution if switching to normal
                                if 'baseline_vision_distribution' in data:
                                    del data['baseline_vision_distribution']
                                    
                            elif dist_type == "beta_with_threshold":
                                # Create/update beta distribution
                                beta_dist = {
                                    'type': 'beta_with_threshold'
                                }
                                
                                if 'tb_edit_beta_alpha' in st.session_state:
                                    try:
                                        beta_dist['alpha'] = float(st.session_state.tb_edit_beta_alpha)
                                    except:
                                        beta_dist['alpha'] = 3.5
                                
                                if 'tb_edit_beta_beta' in st.session_state:
                                    try:
                                        beta_dist['beta'] = float(st.session_state.tb_edit_beta_beta)
                                    except:
                                        beta_dist['beta'] = 2.0
                                        
                                if 'tb_edit_beta_min' in st.session_state:
                                    try:
                                        beta_dist['min'] = int(st.session_state.tb_edit_beta_min)
                                    except:
                                        beta_dist['min'] = 5
                                        
                                if 'tb_edit_beta_max' in st.session_state:
                                    try:
                                        beta_dist['max'] = int(st.session_state.tb_edit_beta_max)
                                    except:
                                        beta_dist['max'] = 98
                                        
                                if 'tb_edit_beta_threshold' in st.session_state:
                                    try:
                                        beta_dist['threshold'] = int(st.session_state.tb_edit_beta_threshold)
                                    except:
                                        beta_dist['threshold'] = 70
                                        
                                if 'tb_edit_beta_reduction' in st.session_state:
                                    try:
                                        beta_dist['threshold_reduction'] = float(st.session_state.tb_edit_beta_reduction)
                                    except:
                                        beta_dist['threshold_reduction'] = 0.6
                                
                                data['baseline_vision_distribution'] = beta_dist
                                
                                # Update baseline_vision to match beta expectations
                                data['baseline_vision']['mean'] = 58
                                data['baseline_vision']['std'] = 15
                                data['baseline_vision']['min'] = beta_dist.get('min', 5)
                                data['baseline_vision']['max'] = beta_dist.get('max', 98)
                                
                            elif dist_type == "uniform":
                                # Create/update uniform distribution
                                uniform_dist = {
                                    'type': 'uniform'
                                }
                                
                                if 'tb_edit_uniform_min' in st.session_state:
                                    try:
                                        uniform_dist['min'] = int(st.session_state.tb_edit_uniform_min)
                                        data['baseline_vision']['min'] = uniform_dist['min']
                                    except:
                                        pass
                                        
                                if 'tb_edit_uniform_max' in st.session_state:
                                    try:
                                        uniform_dist['max'] = int(st.session_state.tb_edit_uniform_max)
                                        data['baseline_vision']['max'] = uniform_dist['max']
                                    except:
                                        pass
                                
                                data['baseline_vision_distribution'] = uniform_dist
                        
                        # Handle parameter file changes
                        if 'tb_param_changes' in st.session_state:
                            protocol_dir = Path(spec.source_file).parent
                            
                            # Save each modified parameter file
                            for param_type, param_data in st.session_state.tb_param_changes.items():
                                if param_type == 'transitions':
                                    param_path = protocol_dir / spec.disease_transitions_file
                                elif param_type == 'effects':
                                    param_path = protocol_dir / spec.treatment_effect_file
                                elif param_type == 'vision':
                                    param_path = protocol_dir / spec.vision_parameters_file
                                elif param_type == 'discontinuation':
                                    param_path = protocol_dir / spec.discontinuation_parameters_file
                                else:
                                    continue
                                
                                # Backup original
                                if param_path.exists():
                                    import shutil
                                    backup_path = param_path.with_suffix('.yaml.bak')
                                    shutil.copy2(param_path, backup_path)
                                
                                # Save changes
                                with open(param_path, 'w') as f:
                                    yaml.dump(param_data, f, default_flow_style=False, sort_keys=False)
                            
                            # Clear parameter changes from session state
                            del st.session_state['tb_param_changes']
                    
                    # Update modified date
                    data['modified_date'] = datetime.now().strftime("%Y-%m-%d")
                    
                    # Write back to file
                    with open(selected_file, 'w') as f:
                        yaml.dump(data, f, sort_keys=False, default_flow_style=False)
                    
                    st.success("Changes saved!")
                    st.session_state.edit_mode = False
                    
                    # Clear edit fields from session state
                    for key in list(st.session_state.keys()):
                        if key.startswith('edit_'):
                            del st.session_state[key]
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save changes: {e}")
        with cancel_col:
            if ape_button("Cancel", key="cancel_edit", full_width=True):
                st.session_state.edit_mode = False
                st.rerun()
    
    # Show model type indicator for time-based protocols
    if protocol_type == "time_based":
        st.info("**Time-Based Model**: Disease progression updates every 14 days, independent of visit schedule")
    
    # Compact metadata display
    if st.session_state.get('edit_mode', False) and protocol_type == "temp":
        # Editable metadata
        col1, col2 = st.columns([3, 1])
        with col1:
            new_author = st.text_input("Author", value=spec.author, key="edit_author")
            new_description = st.text_area("Description", value=spec.description, key="edit_description", height=70)
        with col2:
            st.caption(f"Created: {spec.created_date}")
            st.caption(f"Checksum: {spec.checksum[:8]}...")
    else:
        # Read-only display
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"**Author:** {spec.author} • **Type:** {spec.protocol_type}")
            st.caption(f"**Description:** {spec.description}")
        with col2:
            st.caption(f"Created: {spec.created_date}")
            st.caption(f"Checksum: {spec.checksum[:8]}...")
    
    # Protocol parameters tabs - different for time-based
    if protocol_type == "time_based":
        tab1, tab2, tab3, tab4 = st.tabs([
            "Timing Parameters",
            "Model Type",
            "Population",
            "Parameter Files"
        ])
    else:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Timing Parameters", 
            "Disease Transitions", 
            "Vision Model",
            "Population",
            "Discontinuation"
        ])
    
    with tab1:
        st.subheader("Treatment Timing Parameters")
        if st.session_state.get('edit_mode', False) and selected_file.parent == TEMP_DIR:
            # Editable parameters
            col1, col2 = st.columns(2)
            with col1:
                min_interval = st.text_input("Min Interval (days)", value=str(spec.min_interval_days), key="edit_min_interval")
                st.caption(f"= {int(min_interval)/7:.1f} weeks" if min_interval.isdigit() else "Invalid")
                extension = st.text_input("Extension (days)", value=str(spec.extension_days), key="edit_extension")
                st.caption(f"= {int(extension)/7:.1f} weeks" if extension.isdigit() else "Invalid")
            with col2:
                max_interval = st.text_input("Max Interval (days)", value=str(spec.max_interval_days), key="edit_max_interval")
                st.caption(f"= {int(max_interval)/7:.1f} weeks" if max_interval.isdigit() else "Invalid")
                shortening = st.text_input("Shortening (days)", value=str(spec.shortening_days), key="edit_shortening")
                st.caption(f"= {int(shortening)/7:.1f} weeks" if shortening.isdigit() else "Invalid")
        else:
            # Read-only display
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Min Interval", f"{spec.min_interval_days} days ({spec.min_interval_days/7:.1f} weeks)")
                st.metric("Extension", f"{spec.extension_days} days ({spec.extension_days/7:.1f} weeks)")
            with col2:
                st.metric("Max Interval", f"{spec.max_interval_days} days ({spec.max_interval_days/7:.1f} weeks)")
                st.metric("Shortening", f"{spec.shortening_days} days ({spec.shortening_days/7:.1f} weeks)")
    
    # Handle time-based protocol specific tabs
    if protocol_type == "time_based":
        with tab2:
            st.subheader("Model Type")
            st.info("**Time-Based Disease Progression Model**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Model Type", spec.model_type)
                st.metric("Update Interval", f"{spec.update_interval_days} days")
            with col2:
                st.metric("Transition Model", spec.transition_model)
                if hasattr(spec, 'loading_dose_injections') and spec.loading_dose_injections:
                    st.metric("Loading Doses", f"{spec.loading_dose_injections} injections")
            
            st.caption("Disease states update every 14 days (fortnightly) for all patients, independent of visit schedule.")
            st.caption("Vision changes continuously based on disease state and time since last injection.")
        
        with tab3:
            st.subheader("Patient Population")
            
            if st.session_state.get('edit_mode', False) and selected_file.parent == TEMP_DIR:
                # Distribution type selector for time-based protocols
                st.caption("Choose baseline vision distribution type")
                
                # Get current distribution type
                current_dist = getattr(spec, 'baseline_vision_distribution', None)
                if current_dist and isinstance(current_dist, dict):
                    current_type = current_dist.get('type', 'normal')
                else:
                    current_type = 'normal'
                
                dist_type = st.selectbox(
                    "Distribution Type",
                    ["normal", "beta_with_threshold", "uniform"],
                    index=["normal", "beta_with_threshold", "uniform"].index(current_type),
                    key="tb_edit_dist_type",
                    help="Normal: Standard clinical trial distribution\nBeta with threshold: UK real-world data\nUniform: For testing"
                )
                
                if dist_type == "normal":
                    # Editable normal distribution parameters
                    st.caption("Normal distribution parameters (ETDRS letters)")
                    col1, col2 = st.columns(2)
                    with col1:
                        mean_val = st.text_input("Mean", value=str(spec.baseline_vision_mean), key="tb_edit_pop_mean")
                        st.caption(f"Average baseline vision" if mean_val.replace('.','').isdigit() else "Invalid")
                        std_val = st.text_input("Standard Deviation", value=str(spec.baseline_vision_std), key="tb_edit_pop_std")
                        st.caption(f"Vision variability" if std_val.replace('.','').isdigit() else "Invalid")
                    with col2:
                        min_val = st.text_input("Minimum", value=str(spec.baseline_vision_min), key="tb_edit_pop_min")
                        st.caption(f"Worst allowed vision" if min_val.isdigit() else "Invalid")
                        max_val = st.text_input("Maximum", value=str(spec.baseline_vision_max), key="tb_edit_pop_max")
                        st.caption(f"Best allowed vision" if max_val.isdigit() else "Invalid")
                        
                elif dist_type == "beta_with_threshold":
                    # Editable beta distribution parameters
                    st.caption("Beta distribution with threshold effect (UK real-world)")
                    
                    # Default values
                    defaults = {
                        'alpha': 3.5,
                        'beta': 2.0,
                        'min': 5,
                        'max': 98,
                        'threshold': 70,
                        'threshold_reduction': 0.6
                    }
                    
                    # Get current values if they exist
                    if current_dist and current_dist.get('type') == 'beta_with_threshold':
                        for key in defaults:
                            if key in current_dist:
                                defaults[key] = current_dist[key]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        alpha_val = st.text_input("Alpha", value=str(defaults['alpha']), key="tb_edit_beta_alpha")
                        st.caption("Shape parameter α")
                        min_val = st.text_input("Min", value=str(defaults['min']), key="tb_edit_beta_min")
                        st.caption("Minimum vision")
                        
                    with col2:
                        beta_val = st.text_input("Beta", value=str(defaults['beta']), key="tb_edit_beta_beta")
                        st.caption("Shape parameter β")
                        max_val = st.text_input("Max", value=str(defaults['max']), key="tb_edit_beta_max")
                        st.caption("Maximum vision")
                        
                    with col3:
                        threshold_val = st.text_input("Threshold", value=str(defaults['threshold']), key="tb_edit_beta_threshold")
                        st.caption("NICE funding threshold")
                        reduction_val = st.text_input("Reduction", value=str(defaults['threshold_reduction']), key="tb_edit_beta_reduction")
                        st.caption("Reduction above threshold")
                    
                    st.info("Based on UK real-world data: mean=58.4, ~20.4% > 70 letters")
                    
                elif dist_type == "uniform":
                    # Editable uniform distribution parameters
                    st.caption("Uniform distribution parameters (for testing)")
                    col1, col2 = st.columns(2)
                    with col1:
                        min_val = st.text_input("Minimum", value=str(spec.baseline_vision_min), key="tb_edit_uniform_min")
                        st.caption("Minimum vision")
                    with col2:
                        max_val = st.text_input("Maximum", value=str(spec.baseline_vision_max), key="tb_edit_uniform_max")
                        st.caption("Maximum vision")
                
                # Show live preview of the distribution
                st.subheader("Distribution Preview")
                params = {
                    'mean': spec.baseline_vision_mean,
                    'std': spec.baseline_vision_std,
                    'min': spec.baseline_vision_min,
                    'max': spec.baseline_vision_max
                }
                if current_dist and isinstance(current_dist, dict):
                    params.update(current_dist)
                
                fig = draw_baseline_vision_distribution(dist_type, params, session_prefix="tb_edit")
                st.pyplot(fig)
            else:
                # Read-only display
                # Check if using advanced distribution
                if hasattr(spec, 'baseline_vision_distribution') and spec.baseline_vision_distribution:
                    dist = spec.baseline_vision_distribution
                    dist_type = dist.get('type', 'normal')
                    
                    if dist_type == 'beta_with_threshold':
                        st.info("**Using Beta Distribution with Threshold Effect** (UK Real-World Data)")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Distribution", "Beta + Threshold")
                            st.metric("Alpha (α)", dist.get('alpha', 3.5))
                            st.metric("Beta (β)", dist.get('beta', 2.0))
                        with col2:
                            st.metric("Range", f"{dist.get('min', 5)}-{dist.get('max', 98)}")
                            st.metric("Threshold", f"{dist.get('threshold', 70)} letters")
                            st.metric("Reduction", f"{dist.get('threshold_reduction', 0.6)*100:.0f}%")
                        with col3:
                            st.metric("Expected Mean", "~58.4 letters")
                            st.metric("Expected % >70", "~20.4%")
                            st.metric("Expected Std", "~15.1 letters")
                    elif dist_type == 'uniform':
                        st.info("**Using Uniform Distribution** (For Testing)")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Distribution", "Uniform")
                            st.metric("Minimum", f"{dist.get('min', 20)} letters")
                        with col2:
                            st.metric("Maximum", f"{dist.get('max', 90)} letters")
                            st.metric("Expected Mean", f"{(dist.get('min', 20) + dist.get('max', 90))/2:.0f} letters")
                else:
                    # Standard normal distribution
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Baseline Vision Mean", f"{spec.baseline_vision_mean} letters")
                        st.metric("Baseline Vision Std", f"{spec.baseline_vision_std} letters")
                    with col2:
                        st.metric("Vision Range Min", f"{spec.baseline_vision_min} letters")
                        st.metric("Vision Range Max", f"{spec.baseline_vision_max} letters")
        
        with tab4:
            st.subheader("Parameters")
            
            # Create sub-tabs for different parameter types
            param_tabs = st.tabs(["Disease Transitions", "Treatment Effects", "Vision", "Discontinuation"])
            
            # Load parameter files
            protocol_dir = Path(spec.source_file).parent
            
            # Disease Transitions sub-tab
            with param_tabs[0]:
                transitions_path = protocol_dir / spec.disease_transitions_file
                if transitions_path.exists():
                    with open(transitions_path) as f:
                        trans_data = yaml.safe_load(f)
                    
                    transitions = trans_data.get('fortnightly_transitions', {})
                    states = list(transitions.keys())
                    
                    if st.session_state.get('edit_mode', False) and selected_file.parent == TEMP_DIR:
                        st.info("Edit fortnightly (14-day) transition probabilities")
                        st.warning("Rows must sum to 1.0")
                        
                        # Track if changes were made
                        changes_made = False
                        
                        for from_state in states:
                            st.markdown(f"**From {from_state}:**")
                            cols = st.columns(len(states))
                            
                            row_sum = 0.0
                            new_values = {}
                            
                            for i, to_state in enumerate(states):
                                with cols[i]:
                                    current_val = transitions[from_state][to_state]
                                    
                                    if to_state == 'NAIVE' and from_state != 'NAIVE':
                                        st.text_input(
                                            to_state,
                                            value="0.0000",
                                            disabled=True,
                                            key=f"tb_trans_{from_state}_{to_state}"
                                        )
                                        new_values[to_state] = 0.0
                                    else:
                                        val_str = st.text_input(
                                            to_state,
                                            value=f"{current_val:.4f}",
                                            key=f"tb_trans_{from_state}_{to_state}"
                                        )
                                        try:
                                            val = float(val_str)
                                            new_values[to_state] = val
                                            row_sum += val
                                            if abs(val - current_val) > 0.0001:
                                                changes_made = True
                                        except:
                                            new_values[to_state] = current_val
                                            row_sum += current_val
                            
                            # Show row sum validation
                            if abs(row_sum - 1.0) > 0.0001:
                                st.error(f"Row sum: {row_sum:.4f} (must equal 1.0)")
                            else:
                                st.success(f"Row sum: {row_sum:.4f} ✓")
                                # Update values if valid
                                transitions[from_state] = new_values
                        
                        # Store changes in session state
                        if changes_made:
                            if 'tb_param_changes' not in st.session_state:
                                st.session_state.tb_param_changes = {}
                            st.session_state.tb_param_changes['transitions'] = trans_data
                    else:
                        # Read-only display
                        matrix = []
                        for from_state in states:
                            row = [transitions[from_state][to_state] for to_state in states]
                            matrix.append(row)
                        
                        df = pd.DataFrame(matrix, index=states, columns=states)
                        st.dataframe(df.style.format("{:.4f}"), use_container_width=True)
            
            # Treatment Effects sub-tab
            with param_tabs[1]:
                effects_path = protocol_dir / spec.treatment_effect_file
                if effects_path.exists():
                    with open(effects_path) as f:
                        effects_data = yaml.safe_load(f)
                    
                    if st.session_state.get('edit_mode', False) and selected_file.parent == TEMP_DIR:
                        st.info("Edit treatment effect parameters")
                        
                        # Efficacy decay
                        st.markdown("### Treatment Efficacy Decay")
                        decay = effects_data.get('treatment_efficacy_decay', {})
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            half_life = st.text_input(
                                "Half-life (days)",
                                value=str(decay.get('half_life_days', 84)),
                                key="tb_half_life"
                            )
                            try:
                                decay['half_life_days'] = int(half_life)
                            except:
                                pass
                        
                        with col2:
                            min_eff = st.text_input(
                                "Minimum efficacy",
                                value=f"{decay.get('min_efficacy', 0.1):.2f}",
                                key="tb_min_efficacy"
                            )
                            try:
                                decay['min_efficacy'] = float(min_eff)
                            except:
                                pass
                        
                        effects_data['treatment_efficacy_decay'] = decay
                        
                        # Multipliers
                        st.markdown("### State Transition Multipliers")
                        st.caption("How treatment modifies transition probabilities (1.0 = no effect)")
                        
                        multipliers = effects_data.get('treatment_multipliers', {})
                        
                        for state in ['STABLE', 'ACTIVE', 'HIGHLY_ACTIVE']:
                            if state in multipliers:
                                st.markdown(f"**From {state}:**")
                                mults = multipliers[state].get('multipliers', {})
                                
                                cols = st.columns(len(mults))
                                for i, (trans, mult) in enumerate(mults.items()):
                                    with cols[i % len(cols)]:
                                        new_mult = st.text_input(
                                            trans.replace('_to_', ' → '),
                                            value=f"{mult:.2f}",
                                            key=f"tb_mult_{state}_{trans}"
                                        )
                                        try:
                                            mults[trans] = float(new_mult)
                                        except:
                                            pass
                        
                        # Store changes
                        if 'tb_param_changes' not in st.session_state:
                            st.session_state.tb_param_changes = {}
                        st.session_state.tb_param_changes['effects'] = effects_data
                    else:
                        # Read-only display
                        decay = effects_data.get('treatment_efficacy_decay', {})
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Half-life", f"{decay.get('half_life_days', 84)} days")
                        with col2:
                            st.metric("Decay Model", decay.get('decay_model', 'exponential'))
                        with col3:
                            st.metric("Min Efficacy", f"{decay.get('min_efficacy', 0.1):.0%}")
                        
                        st.markdown("**Treatment Multipliers:**")
                        mult_data = []
                        for state, info in effects_data.get('treatment_multipliers', {}).items():
                            for trans, mult in info.get('multipliers', {}).items():
                                mult_data.append({
                                    'From': state,
                                    'Transition': trans.replace('_to_', ' → '),
                                    'Multiplier': f"×{mult:.2f}"
                                })
                        if mult_data:
                            df = pd.DataFrame(mult_data)
                            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Vision Parameters sub-tab
            with param_tabs[2]:
                vision_path = protocol_dir / spec.vision_parameters_file
                if vision_path.exists():
                    with open(vision_path) as f:
                        vision_data = yaml.safe_load(f)
                    
                    if st.session_state.get('edit_mode', False) and selected_file.parent == TEMP_DIR:
                        st.info("Edit vision model parameters")
                        
                        # Key parameters only - not overwhelming
                        st.markdown("### Vision Ceilings")
                        ceilings = vision_data.get('vision_ceilings', {})
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            factor = st.text_input(
                                "Baseline ceiling factor",
                                value=f"{ceilings.get('baseline_ceiling_factor', 1.2):.2f}",
                                key="tb_ceiling_factor",
                                help="Max vision = baseline × factor"
                            )
                            try:
                                ceilings['baseline_ceiling_factor'] = float(factor)
                            except:
                                pass
                        
                        with col2:
                            abs_ceiling = st.text_input(
                                "Absolute ceiling",
                                value=str(ceilings.get('absolute_ceiling_default', 85)),
                                key="tb_abs_ceiling"
                            )
                            try:
                                ceilings['absolute_ceiling_default'] = int(abs_ceiling)
                            except:
                                pass
                        
                        vision_data['vision_ceilings'] = ceilings
                        
                        # Store changes
                        if 'tb_param_changes' not in st.session_state:
                            st.session_state.tb_param_changes = {}
                        st.session_state.tb_param_changes['vision'] = vision_data
                    else:
                        # Read-only summary
                        measurement = vision_data.get('vision_measurement', {})
                        ceilings = vision_data.get('vision_ceilings', {})
                        hemorrhage = vision_data.get('hemorrhage_risk', {})
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Vision Range", 
                                     f"{measurement.get('min_measurable_vision', 0)}-{measurement.get('max_measurable_vision', 100)}")
                        with col2:
                            st.metric("Ceiling Factor", 
                                     f"×{ceilings.get('baseline_ceiling_factor', 1.2)}")
                        with col3:
                            st.metric("Hemorrhage Risk", 
                                     f"{hemorrhage.get('base_risk_active', 0.01)*100:.1f}% / fortnight")
            
            # Discontinuation sub-tab
            with param_tabs[3]:
                disc_path = protocol_dir / spec.discontinuation_parameters_file
                if disc_path.exists():
                    with open(disc_path) as f:
                        disc_data = yaml.safe_load(f)
                    
                    if st.session_state.get('edit_mode', False) and selected_file.parent == TEMP_DIR:
                        st.info("Edit discontinuation parameters")
                        
                        params = disc_data.get('discontinuation_parameters', {})
                        
                        # Poor vision
                        st.markdown("### Poor Vision")
                        pv = params.get('poor_vision', {})
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            thresh = st.text_input(
                                "Vision threshold",
                                value=str(pv.get('vision_threshold', 20)),
                                key="tb_pv_threshold"
                            )
                            try:
                                pv['vision_threshold'] = int(thresh)
                            except:
                                pass
                        
                        with col2:
                            grace = st.text_input(
                                "Grace period (visits)",
                                value=str(pv.get('grace_period_visits', 2)),
                                key="tb_pv_grace"
                            )
                            try:
                                pv['grace_period_visits'] = int(grace)
                            except:
                                pass
                        
                        with col3:
                            prob = st.text_input(
                                "Probability",
                                value=f"{pv.get('discontinuation_probability', 0.8):.2f}",
                                key="tb_pv_prob"
                            )
                            try:
                                pv['discontinuation_probability'] = float(prob)
                            except:
                                pass
                        
                        params['poor_vision'] = pv
                        disc_data['discontinuation_parameters'] = params
                        
                        # Store changes
                        if 'tb_param_changes' not in st.session_state:
                            st.session_state.tb_param_changes = {}
                        st.session_state.tb_param_changes['discontinuation'] = disc_data
                    else:
                        # Read-only summary
                        params = disc_data.get('discontinuation_parameters', {})
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if 'poor_vision' in params:
                                pv = params['poor_vision']
                                st.metric("Poor Vision Threshold", 
                                         f"< {pv.get('vision_threshold', 20)} letters")
                            
                            if 'deterioration' in params:
                                det = params['deterioration']
                                st.metric("Deterioration Threshold", 
                                         f"{det.get('vision_loss_threshold', -10)} letters")
                        
                        with col2:
                            if 'attrition' in params:
                                attr = params['attrition']
                                st.metric("Base Attrition", 
                                         f"{attr.get('base_probability_per_visit', 0.005)*100:.1f}%/visit")
                            
                            if 'administrative' in params:
                                admin = params['administrative']
                                st.metric("Admin Errors", 
                                         f"{admin.get('probability_per_visit', 0.005)*100:.1f}%/visit")
    
    # Only show disease transitions tab for standard protocols
    elif protocol_type != "time_based":
        with tab2:
            st.subheader("Disease State Transitions")
            
            if st.session_state.get('edit_mode', False) and selected_file.parent == TEMP_DIR:
                # Editable transition matrix
                import pandas as pd
                states = ['NAIVE', 'STABLE', 'ACTIVE', 'HIGHLY_ACTIVE']
                
                st.caption("Edit transition probabilities (0.0 to 1.0). Rows must sum to 1.0.")
                st.caption("Transitions TO NAIVE from other states are not allowed (always 0).")
                
                # Create editable inputs in a grid
                for i, from_state in enumerate(states):
                    cols = st.columns([1.5] + [1]*4)  # Label column + 4 state columns
                    with cols[0]:
                        st.markdown(f"**From {from_state}:**")
                    
                    row_sum = 0.0
                    for j, to_state in enumerate(states):
                        with cols[j+1]:
                            current_val = spec.disease_transitions[from_state][to_state]
                            
                            # Block editing transitions TO NAIVE from other states
                            if to_state == 'NAIVE' and from_state != 'NAIVE':
                                st.text_input(
                                    to_state,
                                    value="0.00",
                                    key=f"edit_trans_{from_state}_{to_state}",
                                    disabled=True,
                                    label_visibility="visible"
                                )
                            else:
                                val = st.text_input(
                                    to_state,
                                    value=f"{current_val:.2f}",
                                    key=f"edit_trans_{from_state}_{to_state}",
                                    label_visibility="visible"
                                )
                                try:
                                    row_sum += float(val)
                                except:
                                    pass
                    
                    # Show row sum validation
                    if abs(row_sum - 1.0) > 0.01:
                        st.error(f"Row sum: {row_sum:.2f} (must equal 1.0)")
                    else:
                        st.success(f"Row sum: {row_sum:.2f} ✓")
            else:
                # Read-only display
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
        
        # Add explainer
        with st.expander("How treatment multipliers work"):
            st.markdown("""
            Treatment multipliers modify disease state transitions when a patient receives treatment:
            
            - **Multiplier > 1.0**: Makes transition MORE likely (e.g., 2.0 = doubles the chance)
            - **Multiplier < 1.0**: Makes transition LESS likely (e.g., 0.5 = halves the chance)  
            - **Multiplier = 1.0**: No effect (same as untreated)
            
            **Example:** If ACTIVE→STABLE has 10% base probability and multiplier 2.0:
            - Without treatment: 10% chance
            - With treatment: 10% × 2.0 = 20% chance
            
            Typically, multipliers that improve vision are > 1.0, while those that worsen vision are < 1.0.
            
            **Important:** Transitions occur **per visit**, not monthly. This means:
            - Patients with 4-week intervals: ~13 transition opportunities/year
            - Patients with 16-week intervals: ~3 transition opportunities/year
            
            This creates a challenge: the same transition probabilities shouldn't apply equally to both cases,
            as the underlying biological progression happens continuously, not just at visits.
            """)
        
        if st.session_state.get('edit_mode', False) and selected_file.parent == TEMP_DIR:
            # Editable treatment effect multipliers
            st.caption("Treatment multiplies transition probabilities. Empty = no effect (1.0)")
            
            for from_state in states:
                with st.expander(f"Treatment effect from {from_state}"):
                    multipliers = spec.treatment_effect_on_transitions.get(from_state, {}).get('multipliers', {})
                    
                    if not multipliers:
                        st.info(f"No treatment effects defined for {from_state} state")
                    else:
                        for to_state, multiplier in multipliers.items():
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.text(f"{from_state} → {to_state}")
                            with col2:
                                st.text_input(
                                    "Multiplier",
                                    value=f"{multiplier:.2f}",
                                    key=f"edit_mult_{from_state}_{to_state}",
                                    label_visibility="collapsed"
                                )
        else:
            # Read-only display in a cleaner format
            for from_state in states:
                multipliers = spec.treatment_effect_on_transitions.get(from_state, {}).get('multipliers', {})
                if multipliers:
                    st.markdown(f"**{from_state}:**")
                    for to_state, multiplier in multipliers.items():
                        st.caption(f"  • {from_state} → {to_state}: ×{multiplier}")
                else:
                    st.caption(f"**{from_state}:** No treatment effects")
    
    # Vision Model tab for standard protocols only
    if protocol_type != "time_based":
        with tab3:
            st.subheader("Vision Change Model")
            
            if st.session_state.get('edit_mode', False) and selected_file.parent == TEMP_DIR:
                # Editable vision change parameters in table format
                st.caption("Monthly vision change (ETDRS letters). Negative = vision loss, Positive = vision gain")
            
                # Create table-like layout
                # Header row
                header_cols = st.columns([1.5, 2, 2])
                with header_cols[0]:
                    st.markdown("**State**")
                with header_cols[1]:
                    st.markdown("**Untreated**")
                    subcols = st.columns(2)
                    with subcols[0]:
                        st.caption("Mean")
                    with subcols[1]:
                        st.caption("Std Dev")
                with header_cols[2]:
                    st.markdown("**Treated**")
                    subcols = st.columns(2)
                    with subcols[0]:
                        st.caption("Mean")
                    with subcols[1]:
                        st.caption("Std Dev")
                
                # Data rows
                for state in states:
                    row_cols = st.columns([1.5, 2, 2])
                    
                    with row_cols[0]:
                        st.markdown(f"**{state}**")
                    
                    # Untreated values
                    with row_cols[1]:
                        scenario = f"{state.lower()}_untreated"
                        if scenario in spec.vision_change_model:
                            params = spec.vision_change_model[scenario]
                            subcols = st.columns(2)
                            with subcols[0]:
                                st.text_input(
                                    "Mean",
                                    value=f"{params['mean']:.2f}",
                                    key=f"edit_vision_{scenario}_mean",
                                    label_visibility="collapsed"
                                )
                            with subcols[1]:
                                st.text_input(
                                    "Std Dev",
                                    value=f"{params['std']:.2f}",
                                    key=f"edit_vision_{scenario}_std",
                                    label_visibility="collapsed"
                                )
                    
                    # Treated values
                    with row_cols[2]:
                        scenario = f"{state.lower()}_treated"
                        if scenario in spec.vision_change_model:
                            params = spec.vision_change_model[scenario]
                            subcols = st.columns(2)
                            with subcols[0]:
                                st.text_input(
                                    "Mean",
                                    value=f"{params['mean']:.2f}",
                                    key=f"edit_vision_{scenario}_mean",
                                    label_visibility="collapsed"
                                )
                            with subcols[1]:
                                st.text_input(
                                    "Std Dev",
                                    value=f"{params['std']:.2f}",
                                    key=f"edit_vision_{scenario}_std",
                                    label_visibility="collapsed"
                                )
            else:
                # Read-only display
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
    
    # Population tab - tab4 for standard, handled differently for time-based
    if protocol_type != "time_based":
        with tab4:
            st.subheader("Patient Population")
        
        if st.session_state.get('edit_mode', False) and selected_file.parent == TEMP_DIR:
            # Distribution type selector
            st.caption("Choose baseline vision distribution type")
            
            # Get current distribution type
            current_dist = getattr(spec, 'baseline_vision_distribution', None)
            if current_dist and isinstance(current_dist, dict):
                current_type = current_dist.get('type', 'normal')
            else:
                current_type = 'normal'
            
            dist_type = st.selectbox(
                "Distribution Type",
                ["normal", "beta_with_threshold", "uniform"],
                index=["normal", "beta_with_threshold", "uniform"].index(current_type),
                key="edit_dist_type",
                help="Normal: Standard clinical trial distribution\nBeta with threshold: UK real-world data\nUniform: For testing"
            )
            
            if dist_type == "normal":
                # Editable normal distribution parameters
                st.caption("Normal distribution parameters (ETDRS letters)")
                col1, col2 = st.columns(2)
                with col1:
                    mean_val = st.text_input("Mean", value=str(spec.baseline_vision_mean), key="edit_pop_mean")
                    st.caption(f"Average baseline vision" if mean_val.replace('.','').isdigit() else "Invalid")
                    std_val = st.text_input("Standard Deviation", value=str(spec.baseline_vision_std), key="edit_pop_std")
                    st.caption(f"Vision variability" if std_val.replace('.','').isdigit() else "Invalid")
                with col2:
                    min_val = st.text_input("Minimum", value=str(spec.baseline_vision_min), key="edit_pop_min")
                    st.caption(f"Worst allowed vision" if min_val.isdigit() else "Invalid")
                    max_val = st.text_input("Maximum", value=str(spec.baseline_vision_max), key="edit_pop_max")
                    st.caption(f"Best allowed vision" if max_val.isdigit() else "Invalid")
                    
            elif dist_type == "beta_with_threshold":
                # Editable beta distribution parameters
                st.caption("Beta distribution with threshold effect (UK real-world)")
                
                # Default values
                defaults = {
                    'alpha': 3.5,
                    'beta': 2.0,
                    'min': 5,
                    'max': 98,
                    'threshold': 70,
                    'threshold_reduction': 0.6
                }
                
                # Get current values if they exist
                if current_dist and current_dist.get('type') == 'beta_with_threshold':
                    for key in defaults:
                        if key in current_dist:
                            defaults[key] = current_dist[key]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    alpha_val = st.text_input("Alpha", value=str(defaults['alpha']), key="edit_beta_alpha")
                    st.caption("Shape parameter α")
                    min_val = st.text_input("Min", value=str(defaults['min']), key="edit_beta_min")
                    st.caption("Minimum vision")
                    
                with col2:
                    beta_val = st.text_input("Beta", value=str(defaults['beta']), key="edit_beta_beta")
                    st.caption("Shape parameter β")
                    max_val = st.text_input("Max", value=str(defaults['max']), key="edit_beta_max")
                    st.caption("Maximum vision")
                    
                with col3:
                    threshold_val = st.text_input("Threshold", value=str(defaults['threshold']), key="edit_beta_threshold")
                    st.caption("NICE funding threshold")
                    reduction_val = st.text_input("Reduction", value=str(defaults['threshold_reduction']), key="edit_beta_reduction")
                    st.caption("Reduction above threshold")
                
                st.info("Based on UK real-world data: mean=58.4, ~20.4% > 70 letters")
                
            elif dist_type == "uniform":
                # Editable uniform distribution parameters
                st.caption("Uniform distribution parameters (for testing)")
                col1, col2 = st.columns(2)
                with col1:
                    min_val = st.text_input("Minimum", value=str(spec.baseline_vision_min), key="edit_uniform_min")
                    st.caption("Minimum vision")
                with col2:
                    max_val = st.text_input("Maximum", value=str(spec.baseline_vision_max), key="edit_uniform_max")
                    st.caption("Maximum vision")
            
            # Show live preview of the distribution
            st.subheader("Distribution Preview")
            params = {
                'mean': spec.baseline_vision_mean,
                'std': spec.baseline_vision_std,
                'min': spec.baseline_vision_min,
                'max': spec.baseline_vision_max
            }
            if current_dist and isinstance(current_dist, dict):
                params.update(current_dist)
            
            fig = draw_baseline_vision_distribution(dist_type, params, session_prefix="edit")
            st.pyplot(fig)
        else:
            # Read-only display
            # Check if using advanced distribution
            if hasattr(spec, 'baseline_vision_distribution') and spec.baseline_vision_distribution:
                dist = spec.baseline_vision_distribution
                dist_type = dist.get('type', 'normal')
                
                if dist_type == 'beta_with_threshold':
                    st.info("**Using Beta Distribution with Threshold Effect** (UK Real-World Data)")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Distribution", "Beta + Threshold")
                        st.metric("Alpha (α)", dist.get('alpha', 3.5))
                        st.metric("Beta (β)", dist.get('beta', 2.0))
                    with col2:
                        st.metric("Range", f"{dist.get('min', 5)}-{dist.get('max', 98)}")
                        st.metric("Threshold", f"{dist.get('threshold', 70)} letters")
                        st.metric("Reduction", f"{dist.get('threshold_reduction', 0.6)*100:.0f}%")
                    with col3:
                        st.metric("Expected Mean", "~58.4 letters")
                        st.metric("Expected % >70", "~20.4%")
                        st.metric("Expected Std", "~15.1 letters")
                elif dist_type == 'uniform':
                    st.info("**Using Uniform Distribution** (For Testing)")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Distribution", "Uniform")
                        st.metric("Minimum", f"{dist.get('min', 20)} letters")
                    with col2:
                        st.metric("Maximum", f"{dist.get('max', 90)} letters")
                        st.metric("Expected Mean", f"{(dist.get('min', 20) + dist.get('max', 90))/2:.0f} letters")
            else:
                # Standard normal distribution
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Baseline Vision Mean", f"{spec.baseline_vision_mean} letters")
                    st.metric("Baseline Vision Std", f"{spec.baseline_vision_std} letters")
                with col2:
                    st.metric("Vision Range Min", f"{spec.baseline_vision_min} letters")
                    st.metric("Vision Range Max", f"{spec.baseline_vision_max} letters")
            
        # Show the actual protocol distribution
        if not st.session_state.get('edit_mode', False):
            st.subheader("Baseline Vision Distribution")
            
            # Determine what distribution is being used
            if hasattr(spec, 'baseline_vision_distribution') and spec.baseline_vision_distribution:
                dist_config = spec.baseline_vision_distribution
                dist_type = dist_config.get('type', 'normal')
            else:
                dist_type = 'normal'
                dist_config = {
                    'type': 'normal',
                    'mean': spec.baseline_vision_mean,
                    'std': spec.baseline_vision_std,
                    'min': spec.baseline_vision_min,
                    'max': spec.baseline_vision_max
                }
            
            # Create the distribution visualization
            from simulation_v2.models.baseline_vision_distributions import DistributionFactory
            
            try:
                # Create the actual distribution
                distribution = DistributionFactory.create_distribution(dist_config)
                
                import numpy as np
                import matplotlib.pyplot as plt
                from scipy import stats
                
                fig, ax = plt.subplots(figsize=(8, 4))
                x = np.linspace(0, 100, 1000)
                
                # Plot the actual distribution being used
                if dist_type == 'normal':
                    y = stats.norm.pdf(x, dist_config['mean'], dist_config['std'])
                    ax.plot(x, y, 'b-', linewidth=2, label=f"Normal(μ={dist_config['mean']}, σ={dist_config['std']})")
                    ax.fill_between(x, 0, y, 
                                   where=(x >= dist_config['min']) & (x <= dist_config['max']), 
                                   alpha=0.3, color='blue')
                    ax.axvline(dist_config['min'], color='k', linestyle=':', alpha=0.5, label=f"Min: {dist_config['min']}")
                    ax.axvline(dist_config['max'], color='k', linestyle=':', alpha=0.5, label=f"Max: {dist_config['max']}")
                    
                elif dist_type == 'beta_with_threshold':
                    # Use the actual distribution object for accurate plotting
                    ax.plot(distribution.x_values, distribution.pdf, 'orange', linewidth=2, 
                           label=distribution.get_description())
                    ax.axvline(dist_config['threshold'], color='red', linestyle='--', alpha=0.5, 
                              label=f"Threshold: {dist_config['threshold']}")
                    
                    # Calculate and show statistics
                    stats_dict = distribution.get_statistics()
                    ax.text(0.02, 0.95, f"Mean: {stats_dict['mean']:.1f}\nStd: {stats_dict['std']:.1f}\n% > 70: {stats_dict['pct_above_70']:.1f}%", 
                           transform=ax.transAxes, verticalalignment='top',
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                    
                elif dist_type == 'uniform':
                    y = np.zeros_like(x)
                    mask = (x >= dist_config['min']) & (x <= dist_config['max'])
                    y[mask] = 1.0 / (dist_config['max'] - dist_config['min'])
                    ax.plot(x, y, 'g-', linewidth=2, label=f"Uniform[{dist_config['min']}, {dist_config['max']}]")
                    ax.fill_between(x, 0, y, where=mask, alpha=0.3, color='green')
                
                # Add NICE threshold reference
                ax.axvline(70, color='orange', linestyle='-', alpha=0.3, label='NICE Threshold: 70')
                
                ax.set_xlabel('Baseline Vision (ETDRS letters)')
                ax.set_ylabel('Probability Density')
                ax.set_title(f'Protocol Baseline Vision Distribution ({dist_type.replace("_", " ").title()})')
                ax.set_xlim(0, 100)
                ax.set_ylim(bottom=0)
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                st.pyplot(fig)
                
            except Exception as e:
                st.error(f"Error creating distribution visualization: {str(e)}")
        
        # Show UK data breakdown
        with st.expander("UK Baseline Vision Data (2,029 patients)"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                **Actual Distribution:**
                - Mean: 58.36 letters
                - Median: 62.00 letters  
                - Std Dev: 15.12 letters
                - Range: 5-98 letters
                - **Best fit: Beta distribution**
                - Negative skew (-0.72)
                """)
            with col2:
                st.markdown("""
                **Vision Categories:**
                - Very Poor (0-30): 5.8%
                - Poor (31-50): 22.2%
                - Moderate (51-70): 51.6%
                - Good (71-85): 20.2%
                - Excellent (86-100): 0.2%
                
                **Key finding:** Only 20.4% measure >70 at first treatment
                - But all qualified with ≤70 at funding decision
                - 51.6% cluster in 51-70 range
                
                **Why some measure >70 at treatment:**
                - Measurement variability (±5 letters typical)
                - Regression to the mean
                - Time delay between funding & treatment
                - Possible measurement bias at funding
                
                **Best fit:** Beta + threshold effect
                - Natural disease: Beta(α=3.5, β=2.0) 
                - 60% reduction above 70 (funding filter)
                - Captures both biology + healthcare system
                """)
    
    # Discontinuation tab - only for standard protocols (tab5)
    if protocol_type != "time_based":
        with tab5:
            st.subheader("Discontinuation Rules")
            
            rules = spec.discontinuation_rules
            
            if st.session_state.get('edit_mode', False) and selected_file.parent == TEMP_DIR:
                # Editable discontinuation rules matching metric style
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**Poor Vision**")
                    # Threshold input styled like metric
                    st.caption("Threshold")
                    pv_thresh = st.text_input("Threshold", value=str(rules['poor_vision_threshold']), key="edit_disc_pv_thresh", label_visibility="collapsed")
                    st.caption(f"< {pv_thresh} letters" if pv_thresh.isdigit() else "Invalid threshold")
                    
                    # Probability input styled like metric  
                    st.caption("Probability")
                    pv_prob = st.text_input("Probability", value=f"{rules['poor_vision_probability']:.2f}", key="edit_disc_pv_prob", label_visibility="collapsed")
                    try:
                        st.caption(f"{float(pv_prob)*100:.0f}% per visit")
                    except:
                        st.caption("Invalid probability")
                
                with col2:
                    st.markdown("**High Injection Count**")
                    # Threshold input styled like metric
                    st.caption("Threshold")
                    hi_thresh = st.text_input("Threshold", value=str(rules['high_injection_count']), key="edit_disc_hi_thresh", label_visibility="collapsed")
                    st.caption(f"> {hi_thresh} injections" if hi_thresh.isdigit() else "Invalid threshold")
                    
                    # Probability input styled like metric
                    st.caption("Probability")  
                    hi_prob = st.text_input("Probability", value=f"{rules['high_injection_probability']:.2f}", key="edit_disc_hi_prob", label_visibility="collapsed")
                    try:
                        st.caption(f"{float(hi_prob)*100:.0f}% per visit")
                    except:
                        st.caption("Invalid probability")
                    
                with col3:
                    st.markdown("**Long Treatment**")
                    # Threshold input styled like metric
                    st.caption("Threshold")
                    lt_thresh = st.text_input("Threshold", value=str(rules['long_treatment_months']), key="edit_disc_lt_thresh", label_visibility="collapsed")
                    st.caption(f"> {lt_thresh} months" if lt_thresh.isdigit() else "Invalid threshold")
                    
                    # Probability input styled like metric
                    st.caption("Probability")
                    lt_prob = st.text_input("Probability", value=f"{rules['long_treatment_probability']:.2f}", key="edit_disc_lt_prob", label_visibility="collapsed")
                    try:
                        st.caption(f"{float(lt_prob)*100:.0f}% per visit")
                    except:
                        st.caption("Invalid probability")
                
                if 'discontinuation_types' in rules:
                    st.markdown("**Discontinuation Types**")
                    disc_types = st.text_input("Types (comma-separated)", value=", ".join(rules['discontinuation_types']), key="edit_disc_types")
                    st.caption("Enter discontinuation types separated by commas")
            else:
                # Read-only display
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
    if protocol_type == "temp":
        st.markdown("---")
        st.caption("This temporary protocol expires in 1 hour")
    
    # Navigation is handled by the workflow indicator at the top
    
except Exception as e:
    st.error(f"Error loading protocol: {e}")
    st.exception(e)

# Add a little ape at the bottom as a fun surprise
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    from ape.components.ui.ape_logo import display_ape_logo
    display_ape_logo(width=50)