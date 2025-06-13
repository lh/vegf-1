#!/usr/bin/env python3
"""Verify the repository structure is correct for Streamlit deployment."""

import os
import sys
from pathlib import Path

def check_deployment_structure():
    """Check if all required files exist for Streamlit deployment."""
    
    root = Path(".")
    errors = []
    warnings = []
    
    # Required files
    required_files = {
        "APE.py": "Main application entry point",
        "requirements.txt": "Python dependencies",
        ".gitignore": "Git ignore file"
    }
    
    # Required directories
    required_dirs = {
        "pages": "Streamlit pages directory",
        "ape": "Application modules",
        ".streamlit": "Streamlit configuration"
    }
    
    # Check required files
    print("Checking required files...")
    for file, desc in required_files.items():
        if not (root / file).exists():
            errors.append(f"❌ Missing {file} - {desc}")
        else:
            print(f"✅ {file} exists")
    
    # Check required directories
    print("\nChecking required directories...")
    for dir, desc in required_dirs.items():
        if not (root / dir).exists():
            errors.append(f"❌ Missing {dir}/ - {desc}")
        else:
            print(f"✅ {dir}/ exists")
            
    # Check pages
    if (root / "pages").exists():
        pages = list((root / "pages").glob("*.py"))
        print(f"\nFound {len(pages)} pages:")
        for page in sorted(pages):
            print(f"  - {page.name}")
    
    # Check for old structure remnants
    print("\nChecking for old structure...")
    if (root / "streamlit_app_v2").exists():
        warnings.append("⚠️  Old streamlit_app_v2/ directory still exists (should be in archive/)")
    
    # Check APE.py imports
    print("\nChecking APE.py imports...")
    try:
        with open("APE.py", "r") as f:
            content = f.read()
            if "import streamlit" in content:
                print("✅ APE.py imports streamlit")
            else:
                errors.append("❌ APE.py doesn't import streamlit")
                
            if "st.set_page_config" in content:
                print("✅ APE.py has page config")
            else:
                warnings.append("⚠️  APE.py missing st.set_page_config")
    except Exception as e:
        errors.append(f"❌ Cannot read APE.py: {e}")
    
    # Check requirements.txt
    print("\nChecking requirements.txt...")
    try:
        with open("requirements.txt", "r") as f:
            reqs = f.read()
            if "streamlit" in reqs:
                print("✅ requirements.txt includes streamlit")
            else:
                errors.append("❌ requirements.txt missing streamlit")
    except Exception as e:
        errors.append(f"❌ Cannot read requirements.txt: {e}")
    
    # Summary
    print("\n" + "="*50)
    print("DEPLOYMENT READINESS CHECK")
    print("="*50)
    
    if errors:
        print(f"\n❌ Found {len(errors)} errors:")
        for error in errors:
            print(f"  {error}")
    else:
        print("\n✅ All required files present!")
    
    if warnings:
        print(f"\n⚠️  Found {len(warnings)} warnings:")
        for warning in warnings:
            print(f"  {warning}")
    
    print("\n📋 Deployment settings for Streamlit Cloud:")
    print("  Repository: lh/vegf-1")
    print("  Branch: main")
    print("  Main file path: APE.py")
    print("  Python version: 3.11 (recommended)")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = check_deployment_structure()
    sys.exit(0 if success else 1)