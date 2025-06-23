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
        # Check if we should select a newly created config
        if 'newly_created_config' in st.session_state:
            target_config = st.session_state['newly_created_config']
            if target_config in available_configs:
                default_index = list(available_configs.keys()).index(target_config)
            else:
                # If not found, try to find it by partial match (in case of naming differences)
                for idx, key in enumerate(available_configs.keys()):
                    if target_config.replace("Cost Config: ", "") in key:
                        default_index = idx
                        break
                else:
                    default_index = 0
            # Clear the flag after using it
            del st.session_state['newly_created_config']
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
        
        if ape_button("New Config", key="new_config", full_width=True):
            st.session_state['create_new'] = True
    else:
        st.warning("No configurations found")
        if ape_button("Create First Config", key="create_first", full_width=True):
            st.session_state['create_new'] = True

# Main content area
if st.session_state.get('create_new', False):
    st.header("Create New Financial Configuration")
    
    # Build template options including all existing configs
    template_options = {}
    
    # Add all available configurations
    for config_name, config_path in get_available_configs().items():
        template_options[config_name] = str(config_path)
    
    # Add empty template option
    template_options["Empty Template"] = None
    
    selected_template = st.selectbox(
        "Start from template",
        options=list(template_options.keys()),
        help="Choose an existing configuration as a template"
    )
    
    new_name = st.text_input("Configuration Name", placeholder="e.g., Custom NHS Configuration")
    
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if ape_button("Create", key="confirm_create", is_primary_action=True):
            if new_name:
                # Load template if selected
                if template_options[selected_template]:
                    template_path = Path(template_options[selected_template])
                    config = load_financial_config(template_path)
                    
                    # Update metadata to reflect this is a new config based on template
                    # For old format files (starting with 'resources'), we need to restructure
                    if 'resources' in config and 'metadata' not in config:
                        # This is an old format file - add metadata at the beginning
                        old_config = config.copy()
                        config = {
                            'metadata': {
                                'name': new_name,
                                'created': datetime.now().isoformat(),
                                'based_on': selected_template,
                                'source': str(template_path)
                            }
                        }
                        # Add all the original content after metadata
                        config.update(old_config)
                    else:
                        # New format or already has metadata - just update it
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
                    st.success(f"Created new configuration: {new_name}")
                    st.session_state['create_new'] = False
                    # Set the newly created config to be selected
                    st.session_state['newly_created_config'] = f"Cost Config: {safe_name}"
                    st.rerun()
            else:
                st.error("Please enter a configuration name")
    
    with col2:
        if ape_button("Cancel", key="cancel_create"):
            st.session_state['create_new'] = False
            st.rerun()

elif available_configs:
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
                    for drug_id, cost in sorted(drug_costs.items()):
                        drug_df_data.append({
                            'Drug': drug_id.replace('_', ' ').title(),
                            'Cost (£)': f"£{cost:,.0f}"
                        })
                    drug_df = pd.DataFrame(drug_df_data)
                    st.dataframe(drug_df, hide_index=True, use_container_width=True)
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
                            'Cost (£)': f"£{cost:,.0f}"
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
                    for visit_name, visit_info in sorted(visit_types.items()):
                        visit_df_data.append({
                            'Visit Type': visit_name.replace('_', ' ').title(),
                            'Total Cost (£)': f"£{visit_info.get('total_cost', 0):,.0f}",
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
                            'Cost (£)': f"£{cost:,.0f}"
                        })
                    event_df = pd.DataFrame(event_df_data)
                    st.dataframe(event_df, hide_index=True, use_container_width=True)
                else:
                    st.info("No special events defined")
            
            # Cost Statistics
            st.divider()
            st.markdown("### Cost Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Calculate totals
            total_drug_costs = sum(drug_costs.values()) if drug_costs else 0
            avg_drug_cost = total_drug_costs / len(drug_costs) if drug_costs else 0
            
            total_visit_costs = sum(v.get('total_cost', 0) for v in visit_types.values()) if visit_types else 0
            avg_visit_cost = total_visit_costs / len(visit_types) if visit_types else 0
            
            with col1:
                st.metric("Drug Types", len(drug_costs))
                st.metric("Avg Drug Cost", f"£{avg_drug_cost:,.0f}")
            
            with col2:
                st.metric("Visit Types", len(visit_types))
                st.metric("Avg Visit Cost", f"£{avg_visit_cost:,.0f}")
            
            with col3:
                st.metric("Components", len(components))
                st.metric("Special Events", len(special_events))
            
            with col4:
                # Find min/max costs
                if drug_costs:
                    min_drug = min(drug_costs.values())
                    max_drug = max(drug_costs.values())
                    st.metric("Drug Cost Range", f"£{min_drug} - £{max_drug}")
                if visit_types:
                    visit_costs = [v.get('total_cost', 0) for v in visit_types.values()]
                    if visit_costs:
                        min_visit = min(visit_costs)
                        max_visit = max(visit_costs)
                        st.metric("Visit Cost Range", f"£{min_visit} - £{max_visit}")
        
        with tabs[1]:  # Drug Costs
            st.subheader("Drug Costs")
            st.write("Cost per administration (including VAT)")
            
            drug_costs = config.get('drug_costs', {})
            
            # Create a container for drug costs
            for drug_id, cost in drug_costs.items():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    drug_display = drug_id.replace('_', ' ').title()
                    st.text_input("Drug", value=drug_display, key=f"drug_name_{drug_id}", disabled=True)
                with col2:
                    new_cost = st.number_input(
                        "Cost (£)", 
                        value=cost, 
                        min_value=0, 
                        step=1,
                        key=f"drug_cost_{drug_id}"
                    )
                    # Update edited config
                    if 'drug_costs' not in st.session_state.edited_config:
                        st.session_state.edited_config['drug_costs'] = {}
                    st.session_state.edited_config['drug_costs'][drug_id] = new_cost
                with col3:
                    if st.button("Remove", key=f"del_drug_{drug_id}"):
                        del st.session_state.edited_config['drug_costs'][drug_id]
                        st.rerun()
            
            # Add new drug
            st.divider()
            st.subheader("Add New Drug")
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                new_drug_id = st.text_input("Drug ID", key="new_drug_id", placeholder="e.g., eylea_2mg")
            with col2:
                new_drug_cost = st.number_input("Cost (£)", min_value=0, step=1, key="new_drug_cost")
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
                        value=cost, 
                        min_value=0, 
                        step=1, 
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
                with st.expander(f"{visit_name.replace('_', ' ').title()} - Total: £{visit_info.get('total_cost', 0)}"):
                    # Display components
                    if 'components' in visit_info:
                        st.write("**Components:**")
                        for comp in visit_info['components']:
                            comp_cost = components.get(comp, 0)
                            st.write(f"- {comp.replace('_', ' ').title()}: £{comp_cost}")
                    
                    # Edit total cost
                    new_total = st.number_input(
                        "Total Cost Override", 
                        value=visit_info.get('total_cost', 0),
                        min_value=0,
                        step=1,
                        key=f"visit_total_{visit_name}",
                        help="Leave as calculated sum or override with custom total"
                    )
                    
                    # Update edited config
                    if 'visit_types' not in st.session_state.edited_config:
                        st.session_state.edited_config['visit_types'] = {}
                    if visit_name not in st.session_state.edited_config['visit_types']:
                        st.session_state.edited_config['visit_types'][visit_name] = visit_info.copy()
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
                        value=cost, 
                        min_value=0, 
                        step=1, 
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
                            value=proc_info.get('unit_cost', 0),
                            min_value=0,
                            step=1,
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
                            value=drug_info.get('unit_cost', 0),
                            min_value=0,
                            step=1,
                            key=f"drug_unit_cost_{drug_id}"
                        )
                    with col2:
                        if 'expected_generic_cost' in drug_info:
                            new_generic = st.number_input(
                                "Expected Generic/Biosimilar Cost (£)",
                                value=drug_info.get('expected_generic_cost', 0),
                                min_value=0,
                                step=1,
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