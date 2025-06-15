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
    width: int = 40
) -> None:
    """Display an ape logo on the page.
    
    Args:
        specific_logo: Specific logo filename to use, or None for random
        width: Width in pixels for the logo
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
        st.markdown(f"🦍")
        return
    
    # Display the logo simply using st.image
    st.image(str(logo_path), width=width)


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