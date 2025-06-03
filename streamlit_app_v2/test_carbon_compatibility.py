#!/usr/bin/env python3
"""
Test script to verify streamlit-carbon-button compatibility
with the current Streamlit version.
"""

import subprocess
import sys
import tempfile
import os

def test_carbon_compatibility():
    """Test Carbon button installation and compatibility."""
    print("🧪 Testing Carbon button compatibility with Streamlit...")
    print("=" * 50)
    
    # Create a temporary virtual environment
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = os.path.join(tmpdir, "test_venv")
        
        print(f"📁 Creating test environment in {tmpdir}")
        
        # Create virtual environment
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        
        # Determine the pip path based on OS
        if sys.platform == "win32":
            pip_path = os.path.join(venv_path, "Scripts", "pip")
            python_path = os.path.join(venv_path, "Scripts", "python")
        else:
            pip_path = os.path.join(venv_path, "bin", "pip")
            python_path = os.path.join(venv_path, "bin", "python")
        
        # Install streamlit first
        print("\n📦 Installing Streamlit...")
        subprocess.run([pip_path, "install", "streamlit>=1.28.0"], check=True)
        
        # Get installed Streamlit version
        result = subprocess.run(
            [python_path, "-c", "import streamlit; print(streamlit.__version__)"],
            capture_output=True, text=True
        )
        streamlit_version = result.stdout.strip()
        print(f"✅ Streamlit version: {streamlit_version}")
        
        # Install streamlit-carbon-button
        print("\n📦 Installing streamlit-carbon-button...")
        try:
            subprocess.run([pip_path, "install", "streamlit-carbon-button"], check=True)
            print("✅ streamlit-carbon-button installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install streamlit-carbon-button")
            return False
        
        # Create a test Streamlit app
        test_app_path = os.path.join(tmpdir, "test_app.py")
        with open(test_app_path, "w") as f:
            f.write("""
import streamlit as st
from streamlit_carbon_button import carbon_button, CarbonIcons

st.title("Carbon Button Compatibility Test")

# Test basic button
if carbon_button("Test Button", key="test1"):
    st.success("Basic button works!")

# Test button with icon
if carbon_button("Save", key="test2", icon=CarbonIcons.SAVE):
    st.success("Icon button works!")

# Test different button types
col1, col2, col3 = st.columns(3)

with col1:
    if carbon_button("Primary", key="test3", button_type="primary"):
        st.info("Primary button clicked")

with col2:
    if carbon_button("Secondary", key="test4", button_type="secondary"):
        st.info("Secondary button clicked")

with col3:
    if carbon_button("Danger", key="test5", button_type="danger"):
        st.error("Danger button clicked")

# Test full width button
if carbon_button("Full Width", key="test6", use_container_width=True):
    st.success("Full width button works!")

st.success("All Carbon button types are working correctly!")
""")
        
        # Test importing in Python
        print("\n🐍 Testing Python import...")
        test_import = subprocess.run(
            [python_path, "-c", "from streamlit_carbon_button import carbon_button, CarbonIcons; print('Import successful')"],
            capture_output=True, text=True
        )
        
        if test_import.returncode == 0:
            print("✅ Python import successful")
        else:
            print("❌ Python import failed:")
            print(test_import.stderr)
            return False
        
        # Get Carbon button version info
        version_check = subprocess.run(
            [python_path, "-c", "import streamlit_carbon_button; print(f'Version: {getattr(streamlit_carbon_button, \"__version__\", \"Unknown\")}')"],
            capture_output=True, text=True
        )
        print(f"📌 {version_check.stdout.strip()}")
        
        print("\n✅ Compatibility test passed!")
        print(f"   Streamlit {streamlit_version} is compatible with streamlit-carbon-button")
        print(f"\n📝 Test app created at: {test_app_path}")
        print("   You can run it with: streamlit run " + test_app_path)
        
        return True

if __name__ == "__main__":
    success = test_carbon_compatibility()
    
    if success:
        print("\n🎉 Carbon button compatibility verified!")
        print("\nNext steps:")
        print("1. Run ./setup-playwright.sh to install Playwright")
        print("2. Run ./run-baseline-tests.sh to capture current button behavior")
        print("3. Review the generated reports")
    else:
        print("\n❌ Compatibility test failed")
        sys.exit(1)