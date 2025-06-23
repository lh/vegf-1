"""
Financial Parameters Manager - Create, edit, and manage cost configurations.

This page allows users to:
- View and edit existing financial parameter sets
- Create new parameter sets
- Load NHS-aligned configurations
- Export/import configurations
"""

import streamlit as st
import yaml
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any, Optional
import copy
import pandas as pd

from ape.utils.carbon_button_helpers import ape_button
from ape.utils.startup_redirect import handle_page_startup

st.set_page_config(
    page_title="Financial Parameters",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Check for startup redirect
handle_page_startup("financial_parameters")

st.title("Financial Parameters Manager")
st.markdown("Create and manage cost configurations for economic analysis")

# Define base paths
RESOURCE_DIR = Path("protocols/resources")
COST_CONFIG_DIR = Path("protocols/cost_configs")

# Ensure directories exist
RESOURCE_DIR.mkdir(parents=True, exist_ok=True)
COST_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_financial_config(file_path: Path) -> Dict[str, Any]:
    """Load a financial configuration from YAML file."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
        return {}

def save_financial_config(config: Dict[str, Any], file_path: Path) -> bool:
    """Save financial configuration to YAML file."""
    try:
        with open(file_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {e}")
        return False

def get_available_configs() -> Dict[str, Path]:
    """Get all available financial configurations."""
    configs = {}
    
    # Check resources directory
    for file in RESOURCE_DIR.glob("*.yaml"):
        configs[f"Resources: {file.stem}"] = file
    
    # Check cost configs directory
    for file in COST_CONFIG_DIR.glob("*.yaml"):
        configs[f"Cost Config: {file.stem}"] = file
    
    return configs

# Initialize session state for edited config
if 'edited_config' not in st.session_state:
    st.session_state.edited_config = None

# Sidebar for configuration selection
with st.sidebar:
    st.header("Configuration Selection")
    
    available_configs = get_available_configs()
    
    if available_configs:
        # Determine default selection
        if 'select_config' in st.session_state and st.session_state['select_config'] in available_configs:
            default_index = list(available_configs.keys()).index(st.session_state['select_config'])
            del st.session_state['select_config']  # Clear after use
        else:
            default_index = 0
            
        selected_config_name = st.selectbox(
            "Select Configuration",
            options=list(available_configs.keys()),
            index=default_index,
            help="Choose a financial parameter set to view or edit"
        )
        
        selected_path = available_configs[selected_config_name]
        
        st.divider()
        
        # New config section right in the sidebar
        st.subheader("Create New Config")
        
        with st.form("new_config_form"):
            new_name = st.text_input("Configuration Name", placeholder="e.g., My Custom Config")
            
            # Template selection
            template_options = ["Empty Template"] + list(available_configs.keys())
            selected_template = st.selectbox("Based on", options=template_options)
            
            submitted = st.form_submit_button("Create", type="primary", use_container_width=True)
            
            if submitted and new_name:
                # Load template if selected
                if selected_template != "Empty Template":
                    template_path = available_configs[selected_template]
                    config = load_financial_config(template_path)
                    
                    # Update metadata
                    if 'resources' in config and 'metadata' not in config:
                        # Old format - restructure
                        old_config = config.copy()
                        config = {
                            'metadata': {
                                'name': new_name,
                                'created': datetime.now().isoformat(),
                                'based_on': selected_template,
                                'source': str(template_path)
                            }
                        }
                        config.update(old_config)
                    else:
                        # New format or already has metadata
                        if 'metadata' not in config:
                            config['metadata'] = {}
                        config['metadata']['name'] = new_name
                        config['metadata']['created'] = datetime.now().isoformat()
                        config['metadata']['based_on'] = selected_template
                        config['metadata']['source'] = str(template_path)
                else:
                    # Create empty template
                    config = {
                        'metadata': {
                            'name': new_name,
                            'created': datetime.now().isoformat(),
                            'version': '1.0'
                        },
                        'resources': {
                            'roles': {},
                            'visit_requirements': {},
                            'session_parameters': {}
                        },
                        'costs': {
                            'procedures': {},
                            'drugs': {}
                        }
                    }
                
                # Save new configuration
                safe_name = new_name.lower().replace(' ', '_').replace('-', '_')
                new_path = COST_CONFIG_DIR / f"{safe_name}.yaml"
                
                if save_financial_config(config, new_path):
                    st.success(f"Created '{new_name}'! Please select it above.")
                    st.balloons()
                    st.rerun()
    else:
        st.warning("No configurations found")
        st.subheader("Create Your First Config")
        
        with st.form("first_config_form"):
            new_name = st.text_input("Configuration Name", placeholder="e.g., My First Config")
            submitted = st.form_submit_button("Create", type="primary", use_container_width=True)
            
            if submitted and new_name:
                # Create empty template
                config = {
                    'metadata': {
                        'name': new_name,
                        'created': datetime.now().isoformat(),
                        'version': '1.0'
                    },
                    'resources': {
                        'roles': {},
                        'visit_requirements': {},
                        'session_parameters': {}
                    },
                    'costs': {
                        'procedures': {},
                        'drugs': {}
                    }
                }
                
                # Save new configuration
                safe_name = new_name.lower().replace(' ', '_').replace('-', '_')
                new_path = COST_CONFIG_DIR / f"{safe_name}.yaml"
                
                if save_financial_config(config, new_path):
                    st.success(f"Created '{new_name}'!")
                    st.balloons()
                    st.rerun()

# Main content area
if available_configs:
    # View/Edit existing configuration
    config = load_financial_config(selected_path)
    
    # Initialize edited config if needed
    if st.session_state.edited_config is None or st.session_state.get('last_selected_path') != selected_path:
        st.session_state.edited_config = copy.deepcopy(config)
        st.session_state.last_selected_path = selected_path
    
    # Configuration header
    col1, col2 = st.columns([3, 1])
    with col1:
        # Use the edited config's name if available, otherwise fall back to original
        display_name = st.session_state.edited_config.get('metadata', {}).get('name', selected_path.stem)
        st.header(display_name)
    with col2:
        if ape_button("Save Changes", key="save_changes", is_primary_action=True):
            if save_financial_config(st.session_state.edited_config, selected_path):
                st.success("Configuration saved!")
                # Reload the config to ensure consistency
                config = load_financial_config(selected_path)
                st.session_state.edited_config = copy.deepcopy(config)
    
    # Metadata section
    if 'metadata' in config:
        with st.expander("Metadata", expanded=False):
            st.json(config['metadata'])
    
    # Create tabs for different sections based on config type
    if 'drug_costs' in config or 'visit_components' in config:
        # New format (cost configs)
        tabs = st.tabs(["Summary", "Drug Costs", "Visit Components", "Visit Types", "Special Events", "Validation", "Export"])
        
        with tabs[0]:  # Summary
            st.subheader("Cost Summary")
            st.write("Overview of all costs in this configuration")
            
            # Create columns for different cost categories
            col1, col2 = st.columns(2)
            
            with col1:
                # Drug Costs Summary
                st.markdown("### Drug Costs")
                drug_costs = st.session_state.edited_config.get('drug_costs', {})
                if drug_costs:
                    drug_df_data = []
                    for drug_id, cost_data in sorted(drug_costs.items()):
                        # Handle both simple numeric values and nested objects
                        if isinstance(cost_data, dict):
                            # Nested format with unit_cost
                            cost_value = cost_data.get('unit_cost', 0)
                            drug_df_data.append({
                                'Drug': drug_id.replace('_', ' ').title(),
                                'Cost (£)': f"£{cost_value:,.0f}"
                            })
                        elif isinstance(cost_data, (int, float)):
                            # Simple numeric format
                            drug_df_data.append({
                                'Drug': drug_id.replace('_', ' ').title(),
                                'Cost (£)': f"£{cost_data:,.0f}"
                            })
                    if drug_df_data:
                        drug_df = pd.DataFrame(drug_df_data)
                        st.dataframe(drug_df, hide_index=True, use_container_width=True)
                    else:
                        st.info("No drug costs defined")
                else:
                    st.info("No drug costs defined")
                
                # Visit Components Summary
                st.markdown("### Visit Components")
                components = st.session_state.edited_config.get('visit_components', {})
                if components:
                    comp_df_data = []
                    for comp_id, cost in sorted(components.items()):
                        comp_df_data.append({
                            'Component': comp_id.replace('_', ' ').title(),
                            'Cost (£)': f"£{float(cost):,.0f}" if isinstance(cost, (int, float)) else f"£{cost}"
                        })
                    comp_df = pd.DataFrame(comp_df_data)
                    st.dataframe(comp_df, hide_index=True, use_container_width=True)
                else:
                    st.info("No visit components defined")
            
            with col2:
                # Visit Types Summary
                st.markdown("### Visit Types")
                visit_types = st.session_state.edited_config.get('visit_types', {})
                if visit_types:
                    visit_df_data = []
                    components = st.session_state.edited_config.get('visit_components', {})
                    for visit_name, visit_info in sorted(visit_types.items()):
                        # Calculate total from components if not explicitly set
                        calculated_total = 0
                        if 'components' in visit_info:
                            calculated_total = sum(components.get(comp, 0) for comp in visit_info['components'])
                        
                        # Get the total cost - check both 'total_cost' and 'total_override'
                        total_cost = visit_info.get('total_cost', visit_info.get('total_override'))
                        if total_cost is None:
                            total_cost = calculated_total
                        else:
                            total_cost = float(total_cost)
                            
                        visit_df_data.append({
                            'Visit Type': visit_name.replace('_', ' ').title(),
                            'Total Cost (£)': f"£{total_cost:,.0f}",
                            'Decision Maker': '✓' if visit_info.get('decision_maker', False) else ''
                        })
                    visit_df = pd.DataFrame(visit_df_data)
                    st.dataframe(visit_df, hide_index=True, use_container_width=True)
                else:
                    st.info("No visit types defined")
                
                # Special Events Summary
                st.markdown("### Special Events")
                special_events = st.session_state.edited_config.get('special_events', {})
                if special_events:
                    event_df_data = []
                    for event_id, cost in sorted(special_events.items()):
                        event_df_data.append({
                            'Event': event_id.replace('_', ' ').title(),
                            'Cost (£)': f"£{float(cost):,.0f}" if isinstance(cost, (int, float)) else f"£{cost}"
                        })
                    event_df = pd.DataFrame(event_df_data)
                    st.dataframe(event_df, hide_index=True, use_container_width=True)
                else:
                    st.info("No special events defined")
            
            # Cost Statistics
            st.divider()
            st.markdown("### Cost Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Calculate totals (handle different formats)
            if drug_costs:
                drug_values = []
                for cost_data in drug_costs.values():
                    if isinstance(cost_data, dict):
                        # Nested format with unit_cost
                        drug_values.append(float(cost_data.get('unit_cost', 0)))
                    elif isinstance(cost_data, (int, float)):
                        # Simple numeric format
                        drug_values.append(float(cost_data))
                    # Skip non-numeric entries
                    
                numeric_drug_count = len(drug_values)
                total_drug_costs = sum(drug_values)
                avg_drug_cost = total_drug_costs / numeric_drug_count if numeric_drug_count > 0 else 0
            else:
                drug_values = []
                numeric_drug_count = 0
                total_drug_costs = avg_drug_cost = 0
            
            if visit_types:
                visit_costs = []
                components = st.session_state.edited_config.get('visit_components', {})
                for visit_info in visit_types.values():
                    # Calculate total from components if not explicitly set
                    calculated_total = 0
                    if 'components' in visit_info:
                        calculated_total = sum(components.get(comp, 0) for comp in visit_info['components'])
                    
                    # Get the total cost - check both 'total_cost' and 'total_override'
                    total_cost = visit_info.get('total_cost', visit_info.get('total_override'))
                    if total_cost is None:
                        total_cost = calculated_total
                    else:
                        total_cost = float(total_cost)
                    
                    visit_costs.append(total_cost)
                    
                total_visit_costs = sum(visit_costs)
                avg_visit_cost = total_visit_costs / len(visit_costs) if visit_costs else 0
            else:
                visit_costs = []
                total_visit_costs = avg_visit_cost = 0
            
            with col1:
                st.metric("Drug Types", numeric_drug_count)
                st.metric("Avg Drug Cost", f"£{avg_drug_cost:,.0f}")
            
            with col2:
                st.metric("Visit Types", len(visit_types))
                st.metric("Avg Visit Cost", f"£{avg_visit_cost:,.0f}")
            
            with col3:
                st.metric("Components", len(components))
                st.metric("Special Events", len(special_events))
            
            with col4:
                # Find min/max costs
                if drug_costs and drug_values:
                    min_drug = min(drug_values)
                    max_drug = max(drug_values)
                    st.metric("Drug Cost Range", f"£{min_drug:,.0f} - £{max_drug:,.0f}")
                if visit_types and visit_costs:
                    min_visit = min(visit_costs)
                    max_visit = max(visit_costs)
                    st.metric("Visit Cost Range", f"£{min_visit:,.0f} - £{max_visit:,.0f}")
        
        with tabs[1]:  # Drug Costs
            st.subheader("Drug Costs")
            st.write("Cost per administration (including VAT)")
            
            drug_costs = config.get('drug_costs', {})
            
            # Create a container for drug costs
            for drug_id, cost_data in drug_costs.items():
                # Handle both simple numeric values and nested objects
                if isinstance(cost_data, dict):
                    # Nested format with unit_cost, list_price, etc.
                    cost_value = cost_data.get('unit_cost', 0)
                    list_price = cost_data.get('list_price', None)
                elif isinstance(cost_data, (int, float)):
                    # Simple numeric format
                    cost_value = cost_data
                    list_price = None
                else:
                    # Skip non-numeric entries like 'default_drug'
                    continue
                    
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    drug_display = drug_id.replace('_', ' ').title()
                    st.text_input("Drug", value=drug_display, key=f"drug_name_{drug_id}", disabled=True)
                with col2:
                    new_cost = st.number_input(
                        "Unit Cost (£)", 
                        value=float(cost_value), 
                        min_value=0.0, 
                        step=1.0,
                        key=f"drug_cost_{drug_id}"
                    )
                with col3:
                    if list_price is not None:
                        st.text_input("List Price (£)", value=f"£{list_price:,.0f}", key=f"list_price_{drug_id}", disabled=True)
                    else:
                        st.text("")  # Empty space
                with col4:
                    if st.button("Remove", key=f"del_drug_{drug_id}"):
                        del st.session_state.edited_config['drug_costs'][drug_id]
                        st.rerun()
                        
                # Update edited config - preserve the structure
                if 'drug_costs' not in st.session_state.edited_config:
                    st.session_state.edited_config['drug_costs'] = {}
                    
                if isinstance(cost_data, dict):
                    # Preserve the nested structure
                    if drug_id not in st.session_state.edited_config['drug_costs']:
                        st.session_state.edited_config['drug_costs'][drug_id] = cost_data.copy()
                    st.session_state.edited_config['drug_costs'][drug_id]['unit_cost'] = new_cost
                else:
                    # Simple numeric format
                    st.session_state.edited_config['drug_costs'][drug_id] = new_cost
            
            # Add new drug
            st.divider()
            st.subheader("Add New Drug")
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                new_drug_id = st.text_input("Drug ID", key="new_drug_id", placeholder="e.g., eylea_2mg")
            with col2:
                new_drug_cost = st.number_input("Cost (£)", min_value=0.0, step=1.0, key="new_drug_cost")
            with col3:
                if ape_button("Add", key="add_drug"):
                    if new_drug_id:
                        if 'drug_costs' not in st.session_state.edited_config:
                            st.session_state.edited_config['drug_costs'] = {}
                        st.session_state.edited_config['drug_costs'][new_drug_id] = new_drug_cost
                        st.rerun()
        
        with tabs[2]:  # Visit Components
            st.subheader("Visit Components")
            st.write("Individual cost components that make up visits")
            
            components = config.get('visit_components', {})
            
            for comp_id, cost in components.items():
                col1, col2 = st.columns([3, 2])
                with col1:
                    comp_display = comp_id.replace('_', ' ').title()
                    st.text_input("Component", value=comp_display, key=f"comp_{comp_id}", disabled=True)
                with col2:
                    new_cost = st.number_input(
                        "Cost (£)", 
                        value=float(cost), 
                        min_value=0.0, 
                        step=1.0, 
                        key=f"comp_cost_{comp_id}"
                    )
                    # Update edited config
                    if 'visit_components' not in st.session_state.edited_config:
                        st.session_state.edited_config['visit_components'] = {}
                    st.session_state.edited_config['visit_components'][comp_id] = new_cost
        
        with tabs[3]:  # Visit Types
            st.subheader("Visit Types")
            st.write("Complete visit definitions with component breakdowns")
            
            visit_types = config.get('visit_types', {})
            
            for visit_name, visit_info in visit_types.items():
                # Calculate total from components if not explicitly set
                components = config.get('visit_components', {})
                calculated_total = 0
                if 'components' in visit_info:
                    calculated_total = sum(components.get(comp, 0) for comp in visit_info['components'])
                
                # Get the total cost - check both 'total_cost' and 'total_override'
                total_cost = visit_info.get('total_cost', visit_info.get('total_override'))
                if total_cost is None:
                    total_cost = calculated_total
                else:
                    total_cost = float(total_cost)
                
                with st.expander(f"{visit_name.replace('_', ' ').title()} - Total: £{total_cost:,.0f}"):
                    # Display components
                    if 'components' in visit_info:
                        st.write("**Components:**")
                        component_total = 0
                        for comp in visit_info['components']:
                            comp_cost = components.get(comp, 0)
                            component_total += comp_cost
                            st.write(f"- {comp.replace('_', ' ').title()}: £{comp_cost}")
                        st.write(f"**Component Total: £{component_total}**")
                        
                        # Show if override is active
                        if abs(total_cost - component_total) > 0.01:  # Using small epsilon for float comparison
                            st.info(f"💡 Override active: £{total_cost:,.0f} (calculated: £{component_total:,.0f})")
                    
                    # Checkbox to use calculated total
                    use_calculated = st.checkbox(
                        "Use calculated total from components",
                        value=abs(total_cost - calculated_total) < 0.01,  # True if they're essentially equal
                        key=f"use_calc_{visit_name}",
                        help="When checked, total will automatically update when component costs change"
                    )
                    
                    # Edit total cost - only show if not using calculated
                    if not use_calculated:
                        new_total = st.number_input(
                            "Total Cost Override", 
                            value=float(total_cost),
                            min_value=0.0,
                            step=1.0,
                            key=f"visit_total_{visit_name}",
                            help="Set a custom total that won't change when components are updated"
                        )
                    else:
                        new_total = calculated_total
                        st.write(f"**Total: £{new_total:,.0f}** (auto-calculated)")
                    
                    # Update edited config
                    if 'visit_types' not in st.session_state.edited_config:
                        st.session_state.edited_config['visit_types'] = {}
                    if visit_name not in st.session_state.edited_config['visit_types']:
                        st.session_state.edited_config['visit_types'][visit_name] = visit_info.copy()
                    
                    # Store the total - if using calculated, store None or the calculated value
                    if use_calculated:
                        # For configs using 'total_override', set it to None to use calculated
                        if 'total_override' in visit_info:
                            st.session_state.edited_config['visit_types'][visit_name]['total_override'] = None
                        # Don't store total_cost if we want it calculated
                        if 'total_cost' in st.session_state.edited_config['visit_types'][visit_name]:
                            del st.session_state.edited_config['visit_types'][visit_name]['total_cost']
                    else:
                        # Store the override value
                        if 'total_override' in visit_info:
                            st.session_state.edited_config['visit_types'][visit_name]['total_override'] = new_total
                        else:
                            st.session_state.edited_config['visit_types'][visit_name]['total_cost'] = new_total
                    
                    # Decision maker flag
                    requires_dm = st.checkbox(
                        "Requires Decision Maker",
                        value=visit_info.get('decision_maker', False),
                        key=f"visit_dm_{visit_name}"
                    )
                    st.session_state.edited_config['visit_types'][visit_name]['decision_maker'] = requires_dm
        
        with tabs[4]:  # Special Events
            st.subheader("Special Events")
            st.write("Costs for special circumstances")
            
            special_events = config.get('special_events', {})
            
            for event_id, cost in special_events.items():
                col1, col2 = st.columns([3, 2])
                with col1:
                    event_display = event_id.replace('_', ' ').title()
                    st.text_input("Event", value=event_display, key=f"event_{event_id}", disabled=True)
                with col2:
                    new_cost = st.number_input(
                        "Cost (£)", 
                        value=float(cost), 
                        min_value=0.0, 
                        step=1.0, 
                        key=f"event_cost_{event_id}"
                    )
                    # Update edited config
                    if 'special_events' not in st.session_state.edited_config:
                        st.session_state.edited_config['special_events'] = {}
                    st.session_state.edited_config['special_events'][event_id] = new_cost
        
        with tabs[5]:  # Validation
            st.subheader("Validation Targets")
            st.write("Expected values for model validation")
            
            validation = config.get('validation_targets', {})
            
            # Display validation data as JSON for now
            st.json(validation)
        
        with tabs[6]:  # Export
            st.subheader("Export Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Download current edited version as YAML
                yaml_str = yaml.dump(st.session_state.edited_config, default_flow_style=False, sort_keys=False)
                st.download_button(
                    label="Download as YAML",
                    data=yaml_str,
                    file_name=f"{selected_path.stem}_edited.yaml",
                    mime="text/yaml"
                )
            
            with col2:
                # Download as JSON
                json_str = json.dumps(st.session_state.edited_config, indent=2)
                st.download_button(
                    label="Download as JSON",
                    data=json_str,
                    file_name=f"{selected_path.stem}_edited.json",
                    mime="application/json"
                )
    
    else:
        # Old format (resources) - NHS Standard Resources style
        tabs = st.tabs(["Summary", "Roles", "Visit Requirements", "Procedures", "Drugs", "Session Parameters", "Export"])
        
        with tabs[0]:  # Summary
            st.subheader("Cost Summary")
            st.write("Overview of all costs and resources in this configuration")
            
            # Create columns for different cost categories
            col1, col2 = st.columns(2)
            
            with col1:
                # Procedures Summary
                st.markdown("### Procedure Costs")
                procedures = st.session_state.edited_config.get('costs', {}).get('procedures', {})
                if procedures:
                    proc_df_data = []
                    for proc_name, proc_info in sorted(procedures.items()):
                        proc_df_data.append({
                            'Procedure': proc_name.replace('_', ' ').title(),
                            'HRG Code': proc_info.get('hrg_code', ''),
                            'Cost (£)': f"£{proc_info.get('unit_cost', 0):,.0f}"
                        })
                    proc_df = pd.DataFrame(proc_df_data)
                    st.dataframe(proc_df, hide_index=True, use_container_width=True)
                else:
                    st.info("No procedures defined")
                
                # Drugs Summary
                st.markdown("### Drug Costs")
                drugs = st.session_state.edited_config.get('costs', {}).get('drugs', {})
                if drugs:
                    drug_df_data = []
                    for drug_id, drug_info in sorted(drugs.items()):
                        drug_df_data.append({
                            'Drug': drug_info.get('name', drug_id),
                            'Cost (£)': f"£{drug_info.get('unit_cost', 0):,.0f}",
                            'Generic Cost': f"£{drug_info.get('expected_generic_cost', 0):,.0f}" if 'expected_generic_cost' in drug_info else '-'
                        })
                    drug_df = pd.DataFrame(drug_df_data)
                    st.dataframe(drug_df, hide_index=True, use_container_width=True)
                else:
                    st.info("No drugs defined")
            
            with col2:
                # Roles Summary
                st.markdown("### Staff Roles")
                roles = st.session_state.edited_config.get('resources', {}).get('roles', {})
                if roles:
                    role_df_data = []
                    for role_name, role_info in sorted(roles.items()):
                        role_df_data.append({
                            'Role': role_name.replace('_', ' ').title(),
                            'Capacity/Session': role_info.get('capacity_per_session', 0)
                        })
                    role_df = pd.DataFrame(role_df_data)
                    st.dataframe(role_df, hide_index=True, use_container_width=True)
                else:
                    st.info("No roles defined")
                
                # Visit Requirements Summary
                st.markdown("### Visit Requirements")
                visits = st.session_state.edited_config.get('resources', {}).get('visit_requirements', {})
                if visits:
                    visit_df_data = []
                    for visit_type, visit_info in sorted(visits.items()):
                        visit_df_data.append({
                            'Visit Type': visit_type.replace('_', ' ').title(),
                            'Duration (min)': visit_info.get('duration_minutes', 0),
                            'Staff Needed': sum(visit_info.get('roles_needed', {}).values())
                        })
                    visit_df = pd.DataFrame(visit_df_data)
                    st.dataframe(visit_df, hide_index=True, use_container_width=True)
                else:
                    st.info("No visit requirements defined")
            
            # Cost Statistics
            st.divider()
            st.markdown("### Cost Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Calculate statistics
            if procedures:
                proc_costs = [p.get('unit_cost', 0) for p in procedures.values()]
                avg_proc_cost = sum(proc_costs) / len(proc_costs) if proc_costs else 0
                min_proc_cost = min(proc_costs) if proc_costs else 0
                max_proc_cost = max(proc_costs) if proc_costs else 0
            else:
                avg_proc_cost = min_proc_cost = max_proc_cost = 0
            
            if drugs:
                drug_costs = [d.get('unit_cost', 0) for d in drugs.values()]
                avg_drug_cost = sum(drug_costs) / len(drug_costs) if drug_costs else 0
                min_drug_cost = min(drug_costs) if drug_costs else 0
                max_drug_cost = max(drug_costs) if drug_costs else 0
            else:
                avg_drug_cost = min_drug_cost = max_drug_cost = 0
            
            with col1:
                st.metric("Procedures", len(procedures))
                st.metric("Avg Procedure Cost", f"£{avg_proc_cost:,.0f}")
            
            with col2:
                st.metric("Drugs", len(drugs))
                st.metric("Avg Drug Cost", f"£{avg_drug_cost:,.0f}")
            
            with col3:
                st.metric("Roles", len(roles))
                st.metric("Visit Types", len(visits))
            
            with col4:
                if procedures:
                    st.metric("Procedure Range", f"£{min_proc_cost} - £{max_proc_cost}")
                if drugs:
                    st.metric("Drug Range", f"£{min_drug_cost} - £{max_drug_cost}")
        
        with tabs[1]:  # Roles
            st.subheader("Staff Roles and Capacities")
            
            roles = config.get('resources', {}).get('roles', {})
            
            for role_name, role_info in roles.items():
                with st.expander(f"{role_name.replace('_', ' ').title()}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_capacity = st.number_input(
                            "Capacity per Session",
                            value=role_info.get('capacity_per_session', 0),
                            min_value=0,
                            key=f"capacity_{role_name}"
                        )
                        # Update edited config
                        if 'resources' not in st.session_state.edited_config:
                            st.session_state.edited_config['resources'] = {}
                        if 'roles' not in st.session_state.edited_config['resources']:
                            st.session_state.edited_config['resources']['roles'] = {}
                        if role_name not in st.session_state.edited_config['resources']['roles']:
                            st.session_state.edited_config['resources']['roles'][role_name] = {}
                        st.session_state.edited_config['resources']['roles'][role_name]['capacity_per_session'] = new_capacity
                    
                    with col2:
                        new_desc = st.text_area(
                            "Description",
                            value=role_info.get('description', ''),
                            key=f"desc_{role_name}"
                        )
                        st.session_state.edited_config['resources']['roles'][role_name]['description'] = new_desc
        
        with tabs[2]:  # Visit Requirements
            st.subheader("Visit Type Requirements")
            
            visits = config.get('resources', {}).get('visit_requirements', {})
            
            for visit_type, visit_info in visits.items():
                with st.expander(f"{visit_type.replace('_', ' ').title()}"):
                    # Duration
                    new_duration = st.number_input(
                        "Duration (minutes)",
                        value=visit_info.get('duration_minutes', 0),
                        min_value=0,
                        step=5,
                        key=f"duration_{visit_type}"
                    )
                    
                    # Description
                    new_desc = st.text_area(
                        "Description",
                        value=visit_info.get('description', ''),
                        key=f"visit_desc_{visit_type}"
                    )
                    
                    st.write("**Resources Needed:**")
                    for role, count in visit_info.get('roles_needed', {}).items():
                        new_count = st.number_input(
                            f"{role.replace('_', ' ').title()}",
                            value=count,
                            min_value=0,
                            key=f"visit_{visit_type}_role_{role}"
                        )
                        # Update edited config
                        if 'resources' not in st.session_state.edited_config:
                            st.session_state.edited_config['resources'] = {}
                        if 'visit_requirements' not in st.session_state.edited_config['resources']:
                            st.session_state.edited_config['resources']['visit_requirements'] = {}
                        if visit_type not in st.session_state.edited_config['resources']['visit_requirements']:
                            st.session_state.edited_config['resources']['visit_requirements'][visit_type] = visit_info.copy()
                        st.session_state.edited_config['resources']['visit_requirements'][visit_type]['duration_minutes'] = new_duration
                        st.session_state.edited_config['resources']['visit_requirements'][visit_type]['description'] = new_desc
                        if 'roles_needed' not in st.session_state.edited_config['resources']['visit_requirements'][visit_type]:
                            st.session_state.edited_config['resources']['visit_requirements'][visit_type]['roles_needed'] = {}
                        st.session_state.edited_config['resources']['visit_requirements'][visit_type]['roles_needed'][role] = new_count
        
        with tabs[3]:  # Procedures
            st.subheader("Procedure Costs")
            
            procedures = config.get('costs', {}).get('procedures', {})
            
            for proc_name, proc_info in procedures.items():
                with st.expander(f"{proc_name.replace('_', ' ').title()}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_hrg = st.text_input(
                            "HRG Code",
                            value=proc_info.get('hrg_code', ''),
                            key=f"hrg_{proc_name}"
                        )
                        new_cost = st.number_input(
                            "Unit Cost (£)",
                            value=float(proc_info.get('unit_cost', 0)),
                            min_value=0.0,
                            step=1.0,
                            key=f"proc_cost_{proc_name}"
                        )
                    with col2:
                        new_desc = st.text_area(
                            "Description",
                            value=proc_info.get('description', ''),
                            key=f"proc_desc_{proc_name}"
                        )
                    
                    # Update edited config
                    if 'costs' not in st.session_state.edited_config:
                        st.session_state.edited_config['costs'] = {}
                    if 'procedures' not in st.session_state.edited_config['costs']:
                        st.session_state.edited_config['costs']['procedures'] = {}
                    if proc_name not in st.session_state.edited_config['costs']['procedures']:
                        st.session_state.edited_config['costs']['procedures'][proc_name] = {}
                    st.session_state.edited_config['costs']['procedures'][proc_name]['hrg_code'] = new_hrg
                    st.session_state.edited_config['costs']['procedures'][proc_name]['unit_cost'] = new_cost
                    st.session_state.edited_config['costs']['procedures'][proc_name]['description'] = new_desc
        
        with tabs[4]:  # Drugs
            st.subheader("Drug Costs")
            
            drugs = config.get('costs', {}).get('drugs', {})
            
            for drug_id, drug_info in drugs.items():
                with st.expander(drug_info.get('name', drug_id)):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input(
                            "Drug Name",
                            value=drug_info.get('name', drug_id),
                            key=f"drug_name_full_{drug_id}"
                        )
                        new_cost = st.number_input(
                            "Unit Cost (£)",
                            value=float(drug_info.get('unit_cost', 0)),
                            min_value=0.0,
                            step=1.0,
                            key=f"drug_unit_cost_{drug_id}"
                        )
                    with col2:
                        if 'expected_generic_cost' in drug_info:
                            new_generic = st.number_input(
                                "Expected Generic/Biosimilar Cost (£)",
                                value=float(drug_info.get('expected_generic_cost', 0)),
                                min_value=0.0,
                                step=1.0,
                                key=f"drug_generic_{drug_id}"
                            )
                        else:
                            new_generic = None
                    
                    # Update edited config
                    if 'costs' not in st.session_state.edited_config:
                        st.session_state.edited_config['costs'] = {}
                    if 'drugs' not in st.session_state.edited_config['costs']:
                        st.session_state.edited_config['costs']['drugs'] = {}
                    if drug_id not in st.session_state.edited_config['costs']['drugs']:
                        st.session_state.edited_config['costs']['drugs'][drug_id] = {}
                    st.session_state.edited_config['costs']['drugs'][drug_id]['name'] = new_name
                    st.session_state.edited_config['costs']['drugs'][drug_id]['unit_cost'] = new_cost
                    if new_generic is not None:
                        st.session_state.edited_config['costs']['drugs'][drug_id]['expected_generic_cost'] = new_generic
        
        with tabs[5]:  # Session Parameters
            st.subheader("Session Parameters")
            
            session = config.get('resources', {}).get('session_parameters', {})
            
            col1, col2 = st.columns(2)
            with col1:
                new_duration = st.number_input(
                    "Session Duration (hours)",
                    value=session.get('session_duration_hours', 4),
                    min_value=1,
                    max_value=12,
                    key="session_duration"
                )
                new_sessions = st.number_input(
                    "Sessions per Day",
                    value=session.get('sessions_per_day', 2),
                    min_value=1,
                    max_value=4,
                    key="sessions_per_day"
                )
            
            with col2:
                st.write("**Working Days:**")
                days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                current_days = session.get('working_days', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])
                selected_days = []
                
                for day in days:
                    if st.checkbox(day, value=day in current_days, key=f"day_{day}"):
                        selected_days.append(day)
            
            # Update edited config
            if 'resources' not in st.session_state.edited_config:
                st.session_state.edited_config['resources'] = {}
            if 'session_parameters' not in st.session_state.edited_config['resources']:
                st.session_state.edited_config['resources']['session_parameters'] = {}
            st.session_state.edited_config['resources']['session_parameters']['session_duration_hours'] = new_duration
            st.session_state.edited_config['resources']['session_parameters']['sessions_per_day'] = new_sessions
            st.session_state.edited_config['resources']['session_parameters']['working_days'] = selected_days
        
        with tabs[6]:  # Export
            st.subheader("Export Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Download current edited version as YAML
                yaml_str = yaml.dump(st.session_state.edited_config, default_flow_style=False, sort_keys=False)
                st.download_button(
                    label="Download as YAML",
                    data=yaml_str,
                    file_name=f"{selected_path.stem}_edited.yaml",
                    mime="text/yaml"
                )
            
            with col2:
                # Download as JSON
                json_str = json.dumps(st.session_state.edited_config, indent=2)
                st.download_button(
                    label="Download as JSON",
                    data=json_str,
                    file_name=f"{selected_path.stem}_edited.json",
                    mime="application/json"
                )

else:
    st.info("No financial configurations found. Click 'New Config' in the sidebar to create one.")

# Footer
st.divider()
st.caption("Financial parameters define the economic assumptions used in workload and cost analysis. Changes are saved when you click 'Save Changes'.")