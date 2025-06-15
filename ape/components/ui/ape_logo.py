"""Ape logo component for consistent display across pages."""

import streamlit as st
import random
from pathlib import Path
from typing import Optional, List


def get_available_ape_logos() -> List[str]:
    """Get list of available ape logo files."""
    return [
        "ape_logo.svg",
        "sad_ape.svg",
        "banana_ape.svg",
        "closed_eyes_ape.svg",
        "tongue_ape.svg",
        "thoughtful_ape.svg"
    ]


def display_ape_logo(
    specific_logo: Optional[str] = None,
    width: int = 40,
    position: str = "top-right"
) -> None:
    """Display an ape logo on the page.
    
    Args:
        specific_logo: Specific logo filename to use, or None for random
        width: Width in pixels for the logo
        position: Where to position the logo (currently only top-right supported)
    """
    # Get logo path
    if specific_logo:
        logo_file = specific_logo
    else:
        # Pick a random logo
        available_logos = get_available_ape_logos()
        logo_file = random.choice(available_logos)
    
    logo_path = Path(__file__).parent.parent.parent.parent / "assets" / logo_file
    
    if not logo_path.exists():
        # Fallback to emoji if file not found
        st.markdown(
            f'<div style="position: fixed; top: 10px; right: 10px; font-size: {width}px; z-index: 999;">🦍</div>',
            unsafe_allow_html=True
        )
        return
    
    # Read the SVG file
    with open(logo_path, 'r') as f:
        svg_content = f.read()
    
    # Create a unique ID for this instance
    unique_id = f"ape-logo-{hash(logo_file)}_{random.randint(1000, 9999)}"
    
    # Display the logo in a fixed position
    if position == "top-right":
        st.markdown(
            f"""
            <div id="{unique_id}" style="
                position: fixed;
                top: 10px;
                right: 10px;
                width: {width}px;
                height: {width}px;
                z-index: 999;
                opacity: 0.8;
                transition: opacity 0.2s;
            ">
                <div style="width: 100%; height: 100%;">
                    {svg_content}
                </div>
            </div>
            <style>
                #{unique_id}:hover {{
                    opacity: 1;
                }}
                #{unique_id} svg {{
                    width: 100%;
                    height: 100%;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )


def get_page_specific_logo(page_name: str) -> Optional[str]:
    """Get a specific logo for a page if desired.
    
    Args:
        page_name: Name of the page
        
    Returns:
        Logo filename or None for random selection
    """
    # We could assign specific logos to pages if desired
    # For now, return None to use random selection
    page_logos = {
        # "simulation": "closed_eyes_ape.svg",  # When running simulations
        # "home": "banana_ape.svg",  # Happy on home page
        # "analysis": "thoughtful_ape.svg",  # Thinking during analysis
    }
    
    return page_logos.get(page_name)