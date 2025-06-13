"""
Working solutions for icon buttons in Streamlit
"""

import streamlit as st
import base64

# Solution 1: Native Material Icons (Streamlit 1.31.0+)
def material_icon_button():
    """Using Streamlit's built-in Material Symbols"""
    if st.button("Upload File", icon=":material/upload_file:"):
        st.success("Uploaded!")
    
    if st.button("Download", icon=":material/download:"):
        st.success("Downloaded!")

# Solution 2: Custom HTML Buttons with Click Detection
def custom_html_button(label: str, icon_svg: str, key: str):
    """
    Create a custom button with SVG icon that Streamlit can detect clicks on.
    Uses a hidden checkbox for click detection.
    """
    
    # Create unique ID
    button_id = f"btn_{key}"
    
    # Inject the custom button HTML and JavaScript
    st.markdown(f"""
    <style>
    #{button_id} {{
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        font-size: 14px;
        font-weight: 400;
        color: rgb(49, 51, 63);
        background-color: white;
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 0.5rem;
        cursor: pointer;
        transition: all 0.3s;
        text-decoration: none;
        font-family: "Source Sans Pro", sans-serif;
    }}
    
    #{button_id}:hover {{
        border-color: rgb(255, 75, 75);
        color: rgb(255, 75, 75);
    }}
    
    #{button_id} svg {{
        margin-right: 0.5rem;
        width: 16px;
        height: 16px;
    }}
    </style>
    
    <button id="{button_id}" onclick="
        var checkbox = document.querySelector('input[type=checkbox][id$={key}]');
        if(checkbox) {{ checkbox.click(); }}
    ">
        {icon_svg}
        {label}
    </button>
    """, unsafe_allow_html=True)
    
    # Hidden checkbox for click detection
    return st.checkbox("", key=key, label_visibility="hidden")

# Solution 3: SVG as Background Image
def svg_background_button(label: str, svg_base64: str, key: str):
    """Button with SVG as background image"""
    
    button_style = f"""
    <style>
    div[data-testid="stButton"] button {{
        background-image: url('data:image/svg+xml;base64,{svg_base64}');
        background-repeat: no-repeat;
        background-position: 10px center;
        padding-left: 35px;
    }}
    </style>
    """
    
    st.markdown(button_style, unsafe_allow_html=True)
    return st.button(label, key=key)

# Solution 4: Streamlit-Extras Approach
def styled_button_with_icon(label: str, icon_url: str, key: str):
    """Using streamlit-extras for styled buttons"""
    try:
        from streamlit_extras.stylable_container import stylable_container
        
        with stylable_container(
            key=f"container_{key}",
            css_styles=f"""
                button {{
                    background-image: url('{icon_url}');
                    background-repeat: no-repeat;
                    background-position: 10px center;
                    background-size: 16px 16px;
                    padding-left: 35px;
                }}
            """
        ):
            return st.button(label, key=key)
    except ImportError:
        st.warning("Install streamlit-extras for this feature: pip install streamlit-extras")
        return st.button(label, key=key)

# Solution 5: Column-based Icon Button
def column_icon_button(label: str, icon_svg: str, key: str):
    """Simpler approach using columns"""
    col1, col2 = st.columns([0.1, 0.9], gap="small")
    
    with col1:
        st.markdown(f'<div style="padding-top: 5px;">{icon_svg}</div>', 
                   unsafe_allow_html=True)
    
    with col2:
        return st.button(label, key=key, use_container_width=True)

# Helper function to convert SVG to base64
def svg_to_base64(svg_string: str) -> str:
    """Convert SVG string to base64 for use in CSS"""
    return base64.b64encode(svg_string.encode()).decode()

# Example Carbon SVG icon
CARBON_UPLOAD_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="currentColor">
    <path d="M26 24v4H6v-4H4v4a2 2 0 0 0 2 2h20a2 2 0 0 0 2-2v-4z"/>
    <path d="M6 12l1.41 1.41L15 5.83V24h2V5.83l7.59 7.58L26 12 16 2 6 12z"/>
</svg>'''

# Demo usage
if __name__ == "__main__":
    st.title("Icon Button Solutions")
    
    # Method 1: Custom HTML Button
    if custom_html_button("Upload with Carbon", CARBON_UPLOAD_SVG, "custom_upload"):
        st.success("Custom HTML button clicked!")
    
    # Method 2: Column approach
    if column_icon_button("Download", CARBON_UPLOAD_SVG, "column_download"):
        st.success("Column button clicked!")
    
    # Method 3: Native Material icons (if available)
    try:
        if st.button("Native Icon", icon=":material/upload:"):
            st.success("Native icon button clicked!")
    except:
        st.info("Update Streamlit to 1.31.0+ for native icon support")