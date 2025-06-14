"""Workflow progress indicator component for consistent navigation."""

import streamlit as st
from typing import List, Optional, Tuple


def workflow_progress_indicator(current_step: str) -> None:
    """Display a workflow progress indicator showing the current step.
    
    Args:
        current_step: The current step identifier ('home', 'protocol', 'simulation', 'analysis')
    """
    steps = [
        ('home', '🏠 Home', 'APE.py'),
        ('protocol', '📋 Protocol', 'pages/1_Protocol_Manager.py'),
        ('simulation', '🚀 Simulation', 'pages/2_Simulations.py'),
        ('analysis', '📊 Analysis', 'pages/3_Analysis.py')
    ]
    
    # Find current step index
    current_idx = next((i for i, (id, _, _) in enumerate(steps) if id == current_step), 0)
    
    # Create columns for steps
    cols = st.columns(len(steps))
    
    for idx, (col, (step_id, label, page)) in enumerate(zip(cols, steps)):
        with col:
            if idx < current_idx:
                # Completed step - clickable
                if st.button(
                    f"✅ {label}",
                    key=f"workflow_{step_id}",
                    use_container_width=True,
                    help="Click to go back"
                ):
                    st.switch_page(page)
            elif idx == current_idx:
                # Current step - highlighted but not clickable
                st.markdown(
                    f"""
                    <div style="
                        background-color: #0066CC;
                        color: white;
                        padding: 0.5rem;
                        border-radius: 0.25rem;
                        text-align: center;
                        font-weight: bold;
                    ">
                        {label}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Future step - grayed out
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f0f0f0;
                        color: #999;
                        padding: 0.5rem;
                        border-radius: 0.25rem;
                        text-align: center;
                    ">
                        {label}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    # Add a subtle line below
    st.markdown("---")


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
                        f"{label} →",
                        key=key,
                        help_text=help_text,
                        full_width=True,
                        button_type="primary"
                    )
    
    return clicked