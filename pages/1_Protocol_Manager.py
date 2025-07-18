"""
Protocol Manager - Browse and manage protocol specifications.
"""

import streamlit as st
from pathlib import Path
import yaml
import json
from datetime import datetime
import time
import re
import pandas as pd
import random

from simulation_v2.protocols.protocol_spec import ProtocolSpecification
from simulation_v2.protocols.time_based_protocol_spec import TimeBasedProtocolSpecification
from ape.utils.startup_redirect import handle_page_startup
from simulation_v2.models.baseline_vision_distributions import (
    NormalDistribution, BetaWithThresholdDistribution, UniformDistribution
)
from ape.utils.distribution_presets import get_distribution_presets

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

# Show auto-save indicator if active
if st.session_state.get('show_save_indicator', False):
    # Calculate time since last save
    if 'last_save_time' in st.session_state:
        time_since_save = time.time() - st.session_state.last_save_time
        if time_since_save < 2:
            st.success("✓ Auto-saved", icon="✅")
        st.session_state.show_save_indicator = False

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

# Load preferred protocols configuration
def load_preferred_protocols():
    """Load the preferred protocols configuration."""
    config_path = Path("protocols/preferred_protocols.yaml")
    if config_path.exists():
        try:
            with open(config_path) as f:
                return yaml.safe_load(f)
        except Exception:
            return None
    return None

# Auto-save functionality for temporary protocols
def auto_save_protocol(selected_file, protocol_type):
    """Auto-save changes to temporary protocol files."""
    if protocol_type != "temp" or not st.session_state.get('edit_mode', False):
        return
    
    # Get the actual protocol type from session state
    actual_protocol_type = st.session_state.get('current_protocol', {}).get('type', 'standard')
    is_time_based = actual_protocol_type == 'time_based'
        
    try:
        # Load the current YAML data
        with open(selected_file) as f:
            data = yaml.safe_load(f)
        
        # Track if any changes were made
        changes_made = False
        
        # Update metadata if edited
        if 'edit_author' in st.session_state and st.session_state.edit_author != data.get('author', ''):
            data['author'] = st.session_state.edit_author
            changes_made = True
        if 'edit_description' in st.session_state and st.session_state.edit_description != data.get('description', ''):
            data['description'] = st.session_state.edit_description
            changes_made = True
        
        # Update timing parameters if edited
        timing_fields = [
            ('edit_min_interval', 'min_interval_days'),
            ('edit_max_interval', 'max_interval_days'),
            ('edit_extension', 'extension_days'),
            ('edit_shortening', 'shortening_days')
        ]
        
        for session_key, yaml_key in timing_fields:
            if session_key in st.session_state:
                try:
                    new_val = int(st.session_state[session_key])
                    if new_val != data.get(yaml_key):
                        data[yaml_key] = new_val
                        changes_made = True
                except:
                    pass
        
        # Save if changes were made
        if changes_made:
            # Add modified timestamp
            data['modified_date'] = datetime.now().strftime("%Y-%m-%d")
            
            # Write the updated data
            with open(selected_file, 'w') as f:
                yaml.dump(data, f, sort_keys=False, default_flow_style=False)
                
            # Show subtle save indicator
            if 'last_save_time' not in st.session_state or time.time() - st.session_state.last_save_time > 2:
                st.session_state.last_save_time = time.time()
                st.session_state.show_save_indicator = True
    except:
        pass  # Silently fail auto-save to not disrupt user


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

# Load preferred protocols configuration
if 'preferred_config' not in st.session_state:
    st.session_state.preferred_config = load_preferred_protocols()

# Sort protocols to show preferred first
if st.session_state.preferred_config and st.session_state.preferred_config.get('ui_settings', {}).get('show_preferred_first', True):
    preferred_stems = set()
    for category in ['time_based', 'visit_based']:
        for pref in st.session_state.preferred_config.get('preferred_protocols', {}).get(category, []):
            preferred_stems.add(Path(pref['path']).stem)
    
    # Sort with preferred first, then by type, then alphabetically
    protocol_files.sort(key=lambda x: (
        0 if x[0].stem in preferred_stems else 1,  # Preferred first
        x[1] != "time_based",  # Time-based before standard
        x[0].stem  # Then alphabetical
    ))

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
    
    # Base formatting
    if ptype == "temp":
        formatted = f"{name} (temporary)"
    elif ptype == "time_based":
        formatted = f"{name} [TIME-BASED]"
    else:
        formatted = f"{name} [STANDARD]"
    
    # Check if this is a preferred protocol
    if st.session_state.preferred_config:
        preferred_stems = set()
        for category in ['time_based', 'visit_based']:
            for pref in st.session_state.preferred_config.get('preferred_protocols', {}).get(category, []):
                pref_stem = Path(pref['path']).stem
                if pref_stem == name:
                    if (category == 'time_based' and ptype == "time_based") or \
                       (category == 'visit_based' and ptype == "standard"):
                        return f"⭐ {formatted}"
    
    return formatted

# Try to maintain selection across reruns
if 'selected_protocol_name' in st.session_state:
    # Find the file that matches the stored name
    default_index = 0
    for i, (file, ptype) in enumerate(protocol_files):
        if file.stem == st.session_state.selected_protocol_name:
            default_index = i
            break
else:
    # Default to first preferred protocol if available
    default_index = 0
    if st.session_state.preferred_config:
        default_name = st.session_state.preferred_config.get('ui_settings', {}).get('default_selection')
        if default_name:
            # Try to find by partial match
            for i, (file, ptype) in enumerate(protocol_files):
                if file.stem in default_name or default_name.startswith(file.stem):
                    default_index = i
                    break

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

# Show info about preferred protocols
if st.session_state.preferred_config and st.session_state.preferred_config.get('ui_settings', {}).get('mark_preferred_with_star', True):
    st.caption("⭐ indicates recommended protocols for T&E vs T&T comparison studies")

# Action buttons in 4 equal columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Edit/Commit button (only for temporary protocols)
    if selected_file and protocol_type == "temp":
        # Toggle between Edit and Commit Changes based on mode
        if st.session_state.get('edit_mode', False):
            # In edit mode - show Commit Changes button
            if ape_button("Commit Changes", key="save_edit_btn", icon="save", full_width=True, is_primary_action=True):
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
                    
                    # Update disease transitions if edited (for standard protocols)
                    if not is_time_based:
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
                            types_list = [t.strip() for t in st.session_state.edit_disc_types.split(',') if t.strip()]
                            if types_list:
                                data['discontinuation_rules']['discontinuation_types'] = types_list
                    
                    # Update population parameters if edited
                    dist_type_key = 'tb_edit_dist_type' if is_time_based else 'edit_dist_type'
                    if dist_type_key in st.session_state:
                        dist_type = st.session_state[dist_type_key]
                        
                        if dist_type == "normal":
                            # Create/update baseline_vision_distribution in new format
                            prefix = 'tb_edit' if is_time_based else 'edit'
                            normal_dist = {
                                'type': 'normal'
                            }
                            
                            if f'{prefix}_pop_mean' in st.session_state:
                                try:
                                    normal_dist['mean'] = float(st.session_state[f'{prefix}_pop_mean'])
                                except:
                                    normal_dist['mean'] = 70
                            else:
                                normal_dist['mean'] = 70
                                    
                            if f'{prefix}_pop_std' in st.session_state:
                                try:
                                    normal_dist['std'] = float(st.session_state[f'{prefix}_pop_std'])
                                except:
                                    normal_dist['std'] = 10
                            else:
                                normal_dist['std'] = 10
                                    
                            if f'{prefix}_pop_min' in st.session_state and st.session_state[f'{prefix}_pop_min'].isdigit():
                                normal_dist['min'] = int(st.session_state[f'{prefix}_pop_min'])
                            else:
                                normal_dist['min'] = 20
                                
                            if f'{prefix}_pop_max' in st.session_state and st.session_state[f'{prefix}_pop_max'].isdigit():
                                normal_dist['max'] = int(st.session_state[f'{prefix}_pop_max'])
                            else:
                                normal_dist['max'] = 90
                            
                            data['baseline_vision_distribution'] = normal_dist
                            
                            # Remove old baseline_vision format if it exists
                            if 'baseline_vision' in data:
                                del data['baseline_vision']
                                
                        elif dist_type == "beta_with_threshold":
                            # Create/update beta distribution
                            prefix = 'tb_edit' if is_time_based else 'edit'
                            beta_dist = {
                                'type': 'beta_with_threshold'
                            }
                            
                            if f'{prefix}_beta_alpha' in st.session_state:
                                try:
                                    beta_dist['alpha'] = float(st.session_state[f'{prefix}_beta_alpha'])
                                except:
                                    beta_dist['alpha'] = 3.5
                            
                            if f'{prefix}_beta_beta' in st.session_state:
                                try:
                                    beta_dist['beta'] = float(st.session_state[f'{prefix}_beta_beta'])
                                except:
                                    beta_dist['beta'] = 2.0
                                    
                            if f'{prefix}_beta_min' in st.session_state:
                                try:
                                    beta_dist['min'] = int(st.session_state[f'{prefix}_beta_min'])
                                except:
                                    beta_dist['min'] = 5
                                    
                            if f'{prefix}_beta_max' in st.session_state:
                                try:
                                    beta_dist['max'] = int(st.session_state[f'{prefix}_beta_max'])
                                except:
                                    beta_dist['max'] = 98
                                    
                            if f'{prefix}_beta_threshold' in st.session_state:
                                try:
                                    beta_dist['threshold'] = int(st.session_state[f'{prefix}_beta_threshold'])
                                except:
                                    beta_dist['threshold'] = 70
                                    
                            if f'{prefix}_beta_reduction' in st.session_state:
                                try:
                                    beta_dist['threshold_reduction'] = float(st.session_state[f'{prefix}_beta_reduction'])
                                except:
                                    beta_dist['threshold_reduction'] = 0.6
                            
                            data['baseline_vision_distribution'] = beta_dist
                            
                            # Remove old baseline_vision format if it exists
                            if 'baseline_vision' in data:
                                del data['baseline_vision']
                            
                        elif dist_type == "uniform":
                            # Create/update uniform distribution
                            prefix = 'tb_edit' if is_time_based else 'edit'
                            uniform_dist = {
                                'type': 'uniform'
                            }
                            
                            if f'{prefix}_uniform_min' in st.session_state:
                                try:
                                    uniform_dist['min'] = int(st.session_state[f'{prefix}_uniform_min'])
                                except:
                                    uniform_dist['min'] = 20
                            else:
                                uniform_dist['min'] = 20
                                    
                            if f'{prefix}_uniform_max' in st.session_state:
                                try:
                                    uniform_dist['max'] = int(st.session_state[f'{prefix}_uniform_max'])
                                except:
                                    uniform_dist['max'] = 90
                            else:
                                uniform_dist['max'] = 90
                            
                            data['baseline_vision_distribution'] = uniform_dist
                            
                            # Remove old baseline_vision format if it exists
                            if 'baseline_vision' in data:
                                del data['baseline_vision']
                    
                    # Save the updated data
                    with open(selected_file, 'w') as f:
                        yaml.dump(data, f, sort_keys=False, default_flow_style=False)
                    
                    # Clear edit mode
                    st.session_state.edit_mode = False
                    
                    # Clear all edit session state variables
                    keys_to_clear = [k for k in st.session_state.keys() if k.startswith('edit_') or k.startswith('tb_edit_')]
                    for key in keys_to_clear:
                        del st.session_state[key]
                    
                    st.success("Changes committed successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Failed to save changes: {str(e)}")
        else:
            # Not in edit mode - show Edit button
            if ape_button("Edit", key="edit_btn", icon="edit", full_width=True):
                st.session_state.edit_mode = True
    else:
        # For default protocols, show a disabled ghost button
        ape_button("Edit", key="edit_btn_disabled", icon="edit", full_width=True, disabled=True)

with col2:
    # Combined Duplicate & Edit button - creates a copy and immediately enters edit mode
    if ape_button("Duplicate & Edit", key="duplicate_edit_btn", icon="copy", full_width=True):
        try:
            # Check protocol count limit
            if len(protocol_files) >= MAX_PROTOCOLS:
                st.error(f"Protocol limit reached ({MAX_PROTOCOLS} files). Please delete some protocols first.")
            else:
                # Load the original spec data as a dict
                with open(selected_file) as f:
                    data = yaml.safe_load(f)
                
                # Generate new name and metadata
                original_name = data.get('name', selected_file.stem)
                new_name = f"{original_name} Copy"
                new_version = "1.0.1"
                
                # Update the metadata
                data['name'] = new_name
                data['version'] = new_version
                data['author'] = st.session_state.get('user_name', 'Your Name')
                data['description'] = f"Copy of {original_name}"
                data['created_date'] = datetime.now().strftime("%Y-%m-%d")
                
                # Generate memorable name for protocol
                colors = ['azure', 'crimson', 'emerald', 'golden', 'ivory', 'jade', 'lavender', 
                         'obsidian', 'pearl', 'ruby', 'sapphire', 'silver', 'topaz', 'violet']
                gemstones = ['amethyst', 'beryl', 'citrine', 'diamond', 'garnet', 'jasper', 
                            'moonstone', 'onyx', 'opal', 'quartz', 'tourmaline', 'zircon']
                
                # Create unique memorable name
                max_attempts = 10
                for _ in range(max_attempts):
                    color = random.choice(colors)
                    gem = random.choice(gemstones)
                    memorable_name = f"{color}-{gem}"
                    
                    # Check if this name already exists
                    matching_files = list(TEMP_DIR.glob(f"*_{memorable_name}.yaml"))
                    if not matching_files:
                        break
                else:
                    # Fallback to timestamp if can't find unique name
                    memorable_name = f"copy-{int(time.time()) % 10000}"
                
                # Create filename with memorable name
                base_filename = f"{new_name.lower().replace(' ', '_')}_v{new_version}"
                filename = f"{base_filename}_{memorable_name}.yaml"
                
                # Ensure filename isn't too long
                if len(filename) > 255:
                    filename = f"protocol_{memorable_name}.yaml"
                    
                save_path = TEMP_DIR / filename
                
                # Write the modified data
                with open(save_path, 'w') as f:
                    yaml.dump(data, f, sort_keys=False, default_flow_style=False)
                
                # Check if the original protocol is time-based
                is_time_based = protocol_type == "time_based" or data.get('model_type') == 'time_based'
                
                # For time-based protocols, copy parameter files if they exist
                if is_time_based:
                    param_files = [
                        'disease_transitions_file',
                        'treatment_effect_file', 
                        'vision_parameters_file',
                        'discontinuation_parameters_file',
                        'demographics_parameters_file'
                    ]
                    
                    # Create unique parameters directory for this protocol
                    # Use the memorable name to ensure uniqueness
                    temp_params_dir = TEMP_DIR / f"parameters_{memorable_name}"
                    temp_params_dir.mkdir(exist_ok=True)
                    
                    # Copy each parameter file and update paths in protocol
                    original_dir = selected_file.parent
                    for param_field in param_files:
                        if param_field in data and data[param_field]:
                            param_path = Path(data[param_field])
                            source_file = original_dir / param_path
                            
                            if source_file.exists():
                                # Copy to protocol-specific parameters directory
                                dest_file = temp_params_dir / param_path.name
                                import shutil
                                shutil.copy2(source_file, dest_file)
                                
                                # Update the path in the protocol to point to the new location
                                data[param_field] = f"parameters_{memorable_name}/{param_path.name}"
                    
                    # Re-save the protocol with updated parameter paths
                    with open(save_path, 'w') as f:
                        yaml.dump(data, f, sort_keys=False, default_flow_style=False)
                
                # Validate the new file can be loaded
                
                if is_time_based:
                    test_spec = TimeBasedProtocolSpecification.from_yaml(save_path)
                else:
                    test_spec = ProtocolSpecification.from_yaml(save_path)
                
                # Select the newly created duplicate
                st.session_state.selected_protocol_name = save_path.stem
                
                # Automatically enter edit mode
                st.session_state.edit_mode = True
                
                # Show success message
                st.session_state.duplicate_edit_success = True
                
                # Close any open dialogs
                st.session_state.show_duplicate = False
                st.session_state.show_delete = False
                st.session_state.show_manage = False
                
                st.rerun()
                
        except Exception as e:
            st.error(f"Failed to duplicate: {str(e)}")

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
                  icon="export"):
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

                    # Generate memorable name for uploaded protocol
                    colors = ['azure', 'crimson', 'emerald', 'golden', 'ivory', 'jade', 'lavender', 
                             'obsidian', 'pearl', 'ruby', 'sapphire', 'silver', 'topaz', 'violet']
                    gemstones = ['amethyst', 'beryl', 'citrine', 'diamond', 'garnet', 'jasper', 
                                'moonstone', 'onyx', 'opal', 'quartz', 'tourmaline', 'zircon']
                    
                    # Create unique memorable name
                    base_name = safe_filename.rsplit('.', 1)[0]
                    max_attempts = 10
                    for _ in range(max_attempts):
                        color = random.choice(colors)
                        gem = random.choice(gemstones)
                        memorable_name = f"{color}-{gem}"
                        
                        # Check if this name already exists
                        final_filename = f"{base_name}_{memorable_name}.yaml"
                        final_path = TEMP_DIR / final_filename
                        if not final_path.exists():
                            break
                    else:
                        # Fallback to timestamp if can't find unique name
                        memorable_name = f"upload-{int(time.time()) % 10000}"
                        final_filename = f"{base_name}_{memorable_name}.yaml"
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
        
        # Export section
        st.markdown("---")
        st.markdown("**Export**")
        
        # Only show export options if a protocol is loaded
        if selected_file and selected_file.exists():
            try:
                # Read the raw YAML first
                with open(selected_file, 'r') as f:
                    raw_yaml = f.read()
                    
                # Parse to get basic info
                with open(selected_file, 'r') as f:
                    yaml_data = yaml.safe_load(f)
                    
                protocol_name = yaml_data.get('name', 'protocol').lower().replace(' ', '_')
                protocol_version = yaml_data.get('version', '1.0')
                
                # Determine if this is a time-based protocol
                is_time_based = yaml_data.get('model_type') == 'time_based' or protocol_type == "time_based"
                
                # Show warning for temp protocols
                if selected_file.parent == TEMP_DIR:
                    st.markdown("<small style='color: #FFA500;'>Temporary protocol - download to keep it!</small>", unsafe_allow_html=True)
                
                # Download options
                if is_time_based and selected_file.parent == TEMP_DIR:
                    # Time-based temp protocol - offer both single file and ZIP
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="Download Protocol",
                            data=raw_yaml,
                            file_name=f"{protocol_name}_v{protocol_version}.yaml",
                            mime="text/yaml",
                            use_container_width=True,
                            help="Download protocol file only"
                        )
                    with col2:
                        # Create ZIP with protocol and parameters
                        import zipfile
                        import io
                        
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            # Add protocol file
                            zip_file.writestr(f"{protocol_name}_v{protocol_version}.yaml", raw_yaml)
                            
                            # Add parameter files if they exist
                            if 'disease_transitions_file' in yaml_data:
                                param_path = Path(yaml_data['disease_transitions_file'])
                                if len(param_path.parts) > 0 and param_path.parts[0].startswith('parameters_'):
                                    temp_params_dir = TEMP_DIR / param_path.parts[0]
                                    if temp_params_dir.exists():
                                        for param_file in temp_params_dir.glob("*.yaml"):
                                            with open(param_file, 'r') as f:
                                                zip_file.writestr(f"parameters/{param_file.name}", f.read())
                        
                        zip_buffer.seek(0)
                        st.download_button(
                            label="Download with Parameters",
                            data=zip_buffer.getvalue(),
                            file_name=f"{protocol_name}_v{protocol_version}_complete.zip",
                            mime="application/zip",
                            use_container_width=True,
                            help="Download protocol with all parameter files"
                        )
                else:
                    # Single download button for other protocols
                    st.download_button(
                        label="Download Protocol",
                        data=raw_yaml,
                        file_name=f"{protocol_name}_v{protocol_version}.yaml",
                        mime="text/yaml",
                        use_container_width=True
                    )
                
                # PDF Export
                st.markdown("---")
                st.markdown("**Export as PDF**")
                if ape_button("Generate PDF Report", key="generate_pdf", icon="document", full_width=True):
                    try:
                        # Load spec for PDF generation
                        if is_time_based:
                            spec = TimeBasedProtocolSpecification.from_yaml(selected_file)
                        else:
                            spec = ProtocolSpecification.from_yaml(selected_file)
                            
                        from ape.utils.protocol_pdf_generator import generate_protocol_pdf
                        pdf_bytes = generate_protocol_pdf(spec, is_time_based)
                        
                        st.download_button(
                            label="Download PDF Report",
                            data=pdf_bytes,
                            file_name=f"{protocol_name}_v{protocol_version}_report.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="download_pdf"
                        )
                    except Exception as e:
                        st.error(f"Failed to generate PDF: {e}")
                        
            except Exception as e:
                st.error(f"Error in export section: {str(e)}")
        else:
            st.info("Select a protocol to see export options")

# Handle duplicate & edit success message
if st.session_state.get('duplicate_edit_success', False):
    st.success("Protocol duplicated! You are now in edit mode. Make your changes and click 'Commit Changes' when done.")
    # Clear the flag after showing
    st.session_state.duplicate_edit_success = False

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
                            # For time-based protocols, also clean up parameter files
                            with open(selected_file, 'r') as f:
                                data = yaml.safe_load(f)
                            
                            if data.get('model_type') == 'time_based':
                                # Find the protocol-specific parameters directory
                                # Extract memorable name from filename (last part before .yaml)
                                filename_parts = selected_file.stem.split('_')
                                if len(filename_parts) >= 2:
                                    # Memorable name is typically the last part (e.g., "golden-garnet")
                                    memorable_name = filename_parts[-1]
                                    temp_params_dir = TEMP_DIR / f"parameters_{memorable_name}"
                                    
                                    if temp_params_dir.exists():
                                        import shutil
                                        shutil.rmtree(temp_params_dir)
                            
                            # Delete the protocol file
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

# Time-based protocol spec is already imported at the top

# Load selected protocol
try:
    # For temp protocols, check if they're actually time-based by looking at the file content
    is_time_based_protocol = protocol_type == "time_based"
    
    if protocol_type == "temp":
        # Check if this is actually a time-based protocol
        with open(selected_file, 'r') as f:
            data = yaml.safe_load(f)
            if data.get('model_type') == 'time_based':
                is_time_based_protocol = True
    
    if is_time_based_protocol:
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
    
    # Show edit mode indicator if in edit mode
    if st.session_state.get('edit_mode', False) and protocol_type == "temp":
        st.warning("**Edit Mode** - Changes are saved automatically. Click 'Commit Changes' to finalize your edits.")
    # Show model type indicator for time-based protocols
    if st.session_state.get('current_protocol', {}).get('type') == 'time_based':
        st.info("**Time-Based Model**: Disease progression updates every 14 days, independent of visit schedule")
    
    # Compact metadata display
    if st.session_state.get('edit_mode', False) and protocol_type == "temp":
        # Editable metadata
        col1, col2 = st.columns([3, 1])
        with col1:
            new_author = st.text_input("Author", value=spec.author, key="edit_author", on_change=lambda: auto_save_protocol(selected_file, protocol_type))
            new_description = st.text_area("Description", value=spec.description, key="edit_description", height=70, on_change=lambda: auto_save_protocol(selected_file, protocol_type))
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
    if is_time_based_protocol:
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
                min_interval = st.text_input("Min Interval (days)", value=str(spec.min_interval_days), key="edit_min_interval", on_change=lambda: auto_save_protocol(selected_file, protocol_type))
                st.caption(f"= {int(min_interval)/7:.1f} weeks" if min_interval.isdigit() else "Invalid")
                extension = st.text_input("Extension (days)", value=str(spec.extension_days), key="edit_extension", on_change=lambda: auto_save_protocol(selected_file, protocol_type))
                st.caption(f"= {int(extension)/7:.1f} weeks" if extension.isdigit() else "Invalid")
            with col2:
                max_interval = st.text_input("Max Interval (days)", value=str(spec.max_interval_days), key="edit_max_interval", on_change=lambda: auto_save_protocol(selected_file, protocol_type))
                st.caption(f"= {int(max_interval)/7:.1f} weeks" if max_interval.isdigit() else "Invalid")
                shortening = st.text_input("Shortening (days)", value=str(spec.shortening_days), key="edit_shortening", on_change=lambda: auto_save_protocol(selected_file, protocol_type))
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
    if is_time_based_protocol:
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
                
                # Distribution Presets Section
                st.caption("**Distribution Presets**")
                preset_manager = get_distribution_presets()
                available_presets = preset_manager.get_available_presets()
                
                preset_col1, preset_col2 = st.columns([3, 1])
                
                with preset_col1:
                    if available_presets:
                        preset_options = ["Custom..."] + [preset['name'] for preset in available_presets]
                        selected_preset = st.selectbox(
                            "Load Preset",
                            preset_options,
                            key="tb_edit_preset_selector",
                            help="Load a predefined distribution or create custom"
                        )
                        
                        if selected_preset != "Custom...":
                            # Find the selected preset
                            preset_data = next((p for p in available_presets if p['name'] == selected_preset), None)
                            if preset_data:
                                st.caption(f"{preset_data.get('description', 'No description')}")
                                st.caption(f"{preset_manager.get_preset_summary(preset_data)}")
                                
                                if ape_button("Apply Preset", key="tb_apply_preset"):
                                    # Apply preset to session state
                                    preset_config = preset_manager.preset_to_distribution_config(preset_data)
                                    
                                    # Update session state based on preset type
                                    st.session_state['tb_edit_dist_type'] = preset_config['type']
                                    
                                    if preset_config['type'] == 'normal':
                                        st.session_state['tb_edit_pop_mean'] = str(preset_config['mean'])
                                        st.session_state['tb_edit_pop_std'] = str(preset_config['std'])
                                        st.session_state['tb_edit_pop_min'] = str(preset_config['min'])
                                        st.session_state['tb_edit_pop_max'] = str(preset_config['max'])
                                    elif preset_config['type'] == 'beta_with_threshold':
                                        st.session_state['tb_edit_beta_alpha'] = str(preset_config['alpha'])
                                        st.session_state['tb_edit_beta_beta'] = str(preset_config['beta'])
                                        st.session_state['tb_edit_beta_min'] = str(preset_config['min'])
                                        st.session_state['tb_edit_beta_max'] = str(preset_config['max'])
                                        st.session_state['tb_edit_beta_threshold'] = str(preset_config['threshold'])
                                        st.session_state['tb_edit_beta_reduction'] = str(preset_config['threshold_reduction'])
                                    elif preset_config['type'] == 'uniform':
                                        st.session_state['tb_edit_uniform_min'] = str(preset_config['min'])
                                        st.session_state['tb_edit_uniform_max'] = str(preset_config['max'])
                                    
                                    st.success(f"Applied preset: {selected_preset}")
                                    st.rerun()
                    else:
                        st.info("No presets available")
                
                with preset_col2:
                    if ape_button("Save as Preset", key="tb_save_preset_btn"):
                        st.session_state['tb_show_save_preset'] = True
                
                
                # Save preset dialog
                if st.session_state.get('tb_show_save_preset', False):
                    with st.expander("Save Current Distribution as Preset", expanded=True):
                        preset_name = st.text_input("Preset Name", key="tb_preset_name")
                        preset_desc = st.text_area("Description", key="tb_preset_desc", height=80)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if ape_button("Save", key="tb_save_preset_confirm"):
                                if preset_name:
                                    try:
                                        # Build current distribution config
                                        current_config = {'type': current_type}
                                        
                                        if current_type == 'normal':
                                            current_config.update({
                                                'mean': int(st.session_state.get('tb_edit_pop_mean', spec.baseline_vision_mean)),
                                                'std': int(st.session_state.get('tb_edit_pop_std', spec.baseline_vision_std)),
                                                'min': int(st.session_state.get('tb_edit_pop_min', spec.baseline_vision_min)),
                                                'max': int(st.session_state.get('tb_edit_pop_max', spec.baseline_vision_max))
                                            })
                                        elif current_type == 'beta_with_threshold':
                                            defaults = {'alpha': 3.5, 'beta': 2.0, 'min': 5, 'max': 98, 'threshold': 70, 'threshold_reduction': 0.6}
                                            if current_dist and current_dist.get('type') == 'beta_with_threshold':
                                                for key in defaults:
                                                    if key in current_dist:
                                                        defaults[key] = current_dist[key]
                                            current_config.update({
                                                'alpha': float(st.session_state.get('tb_edit_beta_alpha', defaults['alpha'])),
                                                'beta': float(st.session_state.get('tb_edit_beta_beta', defaults['beta'])),
                                                'min': int(st.session_state.get('tb_edit_beta_min', defaults['min'])),
                                                'max': int(st.session_state.get('tb_edit_beta_max', defaults['max'])),
                                                'threshold': int(st.session_state.get('tb_edit_beta_threshold', defaults['threshold'])),
                                                'threshold_reduction': float(st.session_state.get('tb_edit_beta_reduction', defaults['threshold_reduction']))
                                            })
                                        elif current_type == 'uniform':
                                            current_config.update({
                                                'min': int(st.session_state.get('tb_edit_uniform_min', spec.baseline_vision_min)),
                                                'max': int(st.session_state.get('tb_edit_uniform_max', spec.baseline_vision_max))
                                            })
                                        
                                        filename = preset_manager.save_preset(
                                            current_config, preset_name, preset_desc, "User defined"
                                        )
                                        st.success(f"Saved preset as {filename}")
                                        st.session_state['tb_show_save_preset'] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error saving preset: {e}")
                                else:
                                    st.error("Please enter a preset name")
                        with col2:
                            if ape_button("Cancel", key="tb_save_preset_cancel"):
                                st.session_state['tb_show_save_preset'] = False
                                st.rerun()
                
                st.divider()
                
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
                
                # Show the actual protocol distribution
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
    elif not is_time_based_protocol:
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
    # Get the actual protocol type from session state
    actual_protocol_type = st.session_state.get('current_protocol', {}).get('type', 'standard')
    if actual_protocol_type != "time_based":
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
    if not is_time_based_protocol:
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
                
                # Distribution Presets Section
                st.caption("**Distribution Presets**")
                preset_manager = get_distribution_presets()
                available_presets = preset_manager.get_available_presets()
                
                preset_col1, preset_col2, preset_col3 = st.columns([2, 1, 1])
                
                with preset_col1:
                    if available_presets:
                        preset_options = ["Custom..."] + [preset['name'] for preset in available_presets]
                        selected_preset = st.selectbox(
                            "Load Preset",
                            preset_options,
                            key="edit_preset_selector",
                            help="Load a predefined distribution or create custom"
                        )
                        
                        if selected_preset != "Custom...":
                            # Find the selected preset
                            preset_data = next((p for p in available_presets if p['name'] == selected_preset), None)
                            if preset_data:
                                st.caption(f"{preset_data.get('description', 'No description')}")
                                st.caption(f"{preset_manager.get_preset_summary(preset_data)}")
                                
                                if ape_button("Apply Preset", key="apply_preset"):
                                    # Apply preset to session state
                                    preset_config = preset_manager.preset_to_distribution_config(preset_data)
                                    
                                    # Update session state based on preset type
                                    st.session_state['edit_dist_type'] = preset_config['type']
                                    
                                    if preset_config['type'] == 'normal':
                                        st.session_state['edit_pop_mean'] = str(preset_config['mean'])
                                        st.session_state['edit_pop_std'] = str(preset_config['std'])
                                        st.session_state['edit_pop_min'] = str(preset_config['min'])
                                        st.session_state['edit_pop_max'] = str(preset_config['max'])
                                    elif preset_config['type'] == 'beta_with_threshold':
                                        st.session_state['edit_beta_alpha'] = str(preset_config['alpha'])
                                        st.session_state['edit_beta_beta'] = str(preset_config['beta'])
                                        st.session_state['edit_beta_min'] = str(preset_config['min'])
                                        st.session_state['edit_beta_max'] = str(preset_config['max'])
                                        st.session_state['edit_beta_threshold'] = str(preset_config['threshold'])
                                        st.session_state['edit_beta_reduction'] = str(preset_config['threshold_reduction'])
                                    elif preset_config['type'] == 'uniform':
                                        st.session_state['edit_uniform_min'] = str(preset_config['min'])
                                        st.session_state['edit_uniform_max'] = str(preset_config['max'])
                                    
                                    st.success(f"Applied preset: {selected_preset}")
                                    st.rerun()
                    else:
                        st.info("No presets available")
                
                with preset_col2:
                    if ape_button("Save as Preset", key="save_preset_btn"):
                        st.session_state['show_save_preset'] = True
                
                
                # Save preset dialog
                if st.session_state.get('show_save_preset', False):
                    with st.expander("Save Current Distribution as Preset", expanded=True):
                        preset_name = st.text_input("Preset Name", key="preset_name")
                        preset_desc = st.text_area("Description", key="preset_desc", height=80)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if ape_button("Save", key="save_preset_confirm"):
                                if preset_name:
                                    try:
                                        # Build current distribution config
                                        current_config = {'type': current_type}
                                        
                                        if current_type == 'normal':
                                            current_config.update({
                                                'mean': int(st.session_state.get('edit_pop_mean', spec.baseline_vision_mean)),
                                                'std': int(st.session_state.get('edit_pop_std', spec.baseline_vision_std)),
                                                'min': int(st.session_state.get('edit_pop_min', spec.baseline_vision_min)),
                                                'max': int(st.session_state.get('edit_pop_max', spec.baseline_vision_max))
                                            })
                                        elif current_type == 'beta_with_threshold':
                                            defaults = {'alpha': 3.5, 'beta': 2.0, 'min': 5, 'max': 98, 'threshold': 70, 'threshold_reduction': 0.6}
                                            if current_dist and current_dist.get('type') == 'beta_with_threshold':
                                                for key in defaults:
                                                    if key in current_dist:
                                                        defaults[key] = current_dist[key]
                                            current_config.update({
                                                'alpha': float(st.session_state.get('edit_beta_alpha', defaults['alpha'])),
                                                'beta': float(st.session_state.get('edit_beta_beta', defaults['beta'])),
                                                'min': int(st.session_state.get('edit_beta_min', defaults['min'])),
                                                'max': int(st.session_state.get('edit_beta_max', defaults['max'])),
                                                'threshold': int(st.session_state.get('edit_beta_threshold', defaults['threshold'])),
                                                'threshold_reduction': float(st.session_state.get('edit_beta_reduction', defaults['threshold_reduction']))
                                            })
                                        elif current_type == 'uniform':
                                            current_config.update({
                                                'min': int(st.session_state.get('edit_uniform_min', spec.baseline_vision_min)),
                                                'max': int(st.session_state.get('edit_uniform_max', spec.baseline_vision_max))
                                            })
                                        
                                        filename = preset_manager.save_preset(
                                            current_config, preset_name, preset_desc, "User defined"
                                        )
                                        st.success(f"Saved preset as {filename}")
                                        st.session_state['show_save_preset'] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error saving preset: {e}")
                                else:
                                    st.error("Please enter a preset name")
                        with col2:
                            if ape_button("Cancel", key="save_preset_cancel"):
                                st.session_state['show_save_preset'] = False
                                st.rerun()
                
                st.divider()
                
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
    if not is_time_based_protocol:
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