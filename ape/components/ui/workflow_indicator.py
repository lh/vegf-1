"""Workflow progress indicator component for consistent navigation."""

import streamlit as st
from typing import List, Optional, Tuple
from ape.utils.carbon_button_helpers import navigation_button


def workflow_progress_indicator(current_step: str, on_current_action: callable = None, 
                              has_results: bool = False) -> None:
    """Display a workflow progress indicator showing the current step.
    
    Args:
        current_step: The current step identifier ('home', 'protocol', 'simulation', 'analysis')
        on_current_action: Callback function to execute when current step button is clicked
        has_results: Whether simulation results are available (enables Analysis navigation)
    """
    
    # Check if a protocol is selected
    has_protocol = st.session_state.get('current_protocol') is not None
    
    steps = [
        ('home', 'Home', 'APE.py', None),  # No icon
        ('protocol', 'Protocol', 'pages/1_Protocol_Manager.py', None),
        ('simulation', 'Simulation', 'pages/2_Simulations.py', None),  # Removed play icon
        ('analysis', 'Analysis', 'pages/3_Analysis.py', None),
        ('workload', 'Workload', 'pages/5_Workload_Analysis.py', None),
        ('financial', 'Financial', 'pages/6_Financial_Parameters.py', None),
        ('comparison', 'Compare', 'pages/4_Simulation_Comparison.py', None)
    ]
    
    # Find current step index
    current_idx = next((i for i, (id, _, _, _) in enumerate(steps) if id == current_step), 0)
    
    # Create columns for steps
    cols = st.columns(len(steps))
    
    for idx, (col, (step_id, label, page, icon)) in enumerate(zip(cols, steps)):
        with col:
            # Add icon to label if present
            display_label = f"{icon} {label}" if icon else label
            
            if idx < current_idx:
                # Completed step - clickable with ghost Carbon button
                # Use invisible icon for workload and financial buttons
                button_icon = 'invisible' if step_id in ["workload", "financial"] else None
                if navigation_button(
                    display_label,
                    icon_name=button_icon,  # Invisible for workload and financial, None for others
                    key=f"workflow_{step_id}",
                    full_width=True,
                    help_text="Click to go back",
                    button_type="ghost"
                ):
                    st.switch_page(page)
            elif idx == current_idx:
                # Current step - actionable if callback provided
                # Special case: change "Simulation" to "Run Simulation" when on simulation page
                if step_id == "simulation" and current_step == "simulation":
                    display_label = "Run Simulation"
                
                # Use invisible icon for workload and financial buttons
                button_icon = 'invisible' if step_id in ["workload", "financial"] else None
                
                if on_current_action:
                    # Make it an action button
                    if navigation_button(
                        display_label,
                        icon_name=button_icon,  # Invisible for workload and financial, None for others
                        key=f"workflow_action_{step_id}",
                        full_width=True,
                        button_type="primary",
                        help_text=f"Run {label}" if step_id == "simulation" else f"Perform {label} action"
                    ):
                        on_current_action()
                else:
                    # Just show as current (disabled)
                    navigation_button(
                        display_label,
                        icon_name=button_icon,  # Invisible for workload and financial, None for others
                        key=f"workflow_current_{step_id}",
                        full_width=True,
                        button_type="primary",
                        disabled=True
                    )
            else:
                # Future step - check if it should be enabled
                # Protocol is always accessible
                if step_id == "protocol":
                    if navigation_button(
                        display_label,
                        icon_name=None,  # Disable auto-icon since we're using our own
                        key=f"workflow_{step_id}",
                        full_width=True,
                        help_text="Browse and select protocols",
                        button_type="secondary"
                    ):
                        st.switch_page(page)
                # Simulation requires a protocol to be selected
                elif step_id == "simulation":
                    if has_protocol:
                        if navigation_button(
                            display_label,
                            icon_name=None,
                            key=f"workflow_{step_id}",
                            full_width=True,
                            help_text="Run or load simulations",
                            button_type="secondary"
                        ):
                            st.switch_page(page)
                    else:
                        # Show as ghost button when no protocol selected
                        navigation_button(
                            display_label,
                            icon_name=None,
                            key=f"workflow_{step_id}_disabled",
                            full_width=True,
                            help_text="Select a protocol first",
                            button_type="ghost",
                            disabled=True
                        )
                # Comparison and Financial are always accessible
                elif step_id in ["comparison", "financial"]:
                    # Use invisible icon for financial button
                    button_icon = 'invisible' if step_id == "financial" else None
                    help_texts = {
                        "comparison": "Compare simulation results",
                        "financial": "Configure financial parameters"
                    }
                    if navigation_button(
                        display_label,
                        icon_name=button_icon,
                        key=f"workflow_{step_id}",
                        full_width=True,
                        help_text=help_texts.get(step_id, f"View {label}"),
                        button_type="secondary"
                    ):
                        st.switch_page(page)
                # Analysis and Workload buttons are only enabled if we have results
                elif step_id in ["analysis", "workload"] and has_results:
                    # Use invisible icon for workload button only
                    button_icon = 'invisible' if step_id == "workload" else None
                    help_texts = {
                        "analysis": "View analysis results",
                        "workload": "View workload and economic analysis"
                    }
                    if navigation_button(
                        display_label,
                        icon_name=button_icon,  # Invisible for workload, auto-detect for others
                        key=f"workflow_{step_id}",
                        full_width=True,
                        help_text=help_texts.get(step_id, f"View {label}"),
                        button_type="secondary"
                    ):
                        st.switch_page(page)
                else:
                    # Disabled future step (only Analysis without results)
                    # Use invisible icon for workload and financial buttons
                    button_icon = 'invisible' if step_id in ["workload", "financial"] else None
                    navigation_button(
                        display_label,
                        icon_name=button_icon,  # Invisible for workload and financial, None for others
                        key=f"workflow_future_{step_id}",
                        full_width=True,
                        button_type="ghost",
                        disabled=True
                    )


def consistent_button_bar(
    left_buttons: List[Tuple[str, str, Optional[str]]] = None,
    right_buttons: List[Tuple[str, str, Optional[str]]] = None,
    primary_action: Optional[Tuple[str, str, Optional[str]]] = None
) -> dict:
    """Create a consistent button bar across all pages.
    
    Args:
        left_buttons: List of (label, key, help_text) for left-aligned buttons
        right_buttons: List of (label, key, help_text) for right-aligned buttons  
        primary_action: Tuple of (label, key, help_text) for the primary action button
        
    Returns:
        Dict mapping button keys to whether they were clicked
    """
    clicked = {}
    
    # Create columns with spacing
    if left_buttons and (right_buttons or primary_action):
        left_col, spacer, right_col = st.columns([2, 3, 2])
    elif left_buttons:
        left_col = st.columns(1)[0]
        right_col = None
    elif right_buttons or primary_action:
        left_col = None
        right_col = st.columns(1)[0]
    else:
        return clicked
    
    # Left buttons
    if left_buttons and left_col:
        with left_col:
            left_cols = st.columns(len(left_buttons))
            for col, (label, key, help_text) in zip(left_cols, left_buttons):
                with col:
                    # Import carbon button helper
                    from ape.utils.carbon_button_helpers import navigation_button
                    clicked[key] = navigation_button(
                        label,
                        key=key,
                        help_text=help_text,
                        full_width=True,
                        button_type="ghost"
                    )
    
    # Right buttons and primary action
    if (right_buttons or primary_action) and right_col:
        with right_col:
            num_buttons = len(right_buttons or []) + (1 if primary_action else 0)
            right_cols = st.columns(num_buttons)
            
            # Regular right buttons
            if right_buttons:
                for col, (label, key, help_text) in zip(right_cols[:-1] if primary_action else right_cols, right_buttons):
                    with col:
                        from ape.utils.carbon_button_helpers import navigation_button
                        clicked[key] = navigation_button(
                            label,
                            key=key,
                            help_text=help_text,
                            full_width=True,
                            button_type="secondary"
                        )
            
            # Primary action (always last)
            if primary_action:
                with right_cols[-1]:
                    label, key, help_text = primary_action
                    from ape.utils.carbon_button_helpers import navigation_button
                    clicked[key] = navigation_button(
                        label,
                        key=key,
                        help_text=help_text,
                        full_width=True,
                        button_type="primary"
                    )
    
    return clicked