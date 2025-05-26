"""
Alternative: Download Carbon icons directly from GitHub without npm
This script fetches icons from the Carbon GitHub repository
"""

import requests
import re
from pathlib import Path

def download_carbon_icon(icon_name: str, size: int = 32) -> str:
    """Download a Carbon icon directly from GitHub"""
    
    # Carbon icons are hosted on GitHub
    url = f"https://raw.githubusercontent.com/carbon-design-system/carbon/main/packages/icons/src/svg/{size}/{icon_name}.svg"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            content = response.text.strip()
            # Clean up the SVG
            content = re.sub(r'<\?xml.*?\?>', '', content).strip()
            return content
        else:
            return None
    except Exception as e:
        print(f"Error downloading {icon_name}: {e}")
        return None

def update_carbon_button_file(icons_dict: dict):
    """Update the carbon_button.py file with new icons"""
    
    carbon_button_path = Path(__file__).parent / "carbon_button.py"
    
    # Read the current file
    with open(carbon_button_path, 'r') as f:
        lines = f.readlines()
    
    # Find where to insert new icons
    class_started = False
    insert_index = -1
    
    for i, line in enumerate(lines):
        if "class CarbonIcons:" in line:
            class_started = True
        elif class_started and line.strip() and not line.startswith(" "):
            # End of class found
            insert_index = i
            break
    
    if insert_index == -1:
        print("Could not find insertion point in carbon_button.py")
        return False
    
    # Create new icon definitions
    new_lines = []
    for name, svg in sorted(icons_dict.items()):
        # Check if icon already exists
        icon_exists = any(f"{name} = " in line for line in lines)
        if not icon_exists:
            new_lines.append(f"    {name} = '''{svg}'''\n")
            new_lines.append("    \n")
    
    # Insert the new lines
    if new_lines:
        # Remove the last empty line
        if new_lines[-1].strip() == "":
            new_lines = new_lines[:-1]
        
        # Insert before the end of class
        lines[insert_index:insert_index] = new_lines
        
        # Write back
        with open(carbon_button_path, 'w') as f:
            f.writelines(lines)
        
        return True
    else:
        print("All icons already exist in carbon_button.py")
        return False

# Essential icons for your app
ESSENTIAL_ICONS = {
    "upload": "UPLOAD",
    "download": "DOWNLOAD",
    "copy": "COPY", 
    "play--filled": "PLAY",
    "document": "DOCUMENT",
    "home": "HOME",
    "chart--bar": "CHART_BAR",
    "warning": "WARNING",
    "information": "INFO",
    "checkmark--filled": "SUCCESS",
    "close": "CLOSE",
    "add": "ADD",
    "delete": "DELETE",
    "save": "SAVE",
    "settings": "SETTINGS"
}

if __name__ == "__main__":
    print("🌐 Downloading Carbon icons from GitHub...\n")
    
    downloaded_icons = {}
    failed_icons = []
    
    for carbon_name, python_name in ESSENTIAL_ICONS.items():
        print(f"Downloading {carbon_name}...", end=" ")
        svg = download_carbon_icon(carbon_name)
        
        if svg:
            downloaded_icons[python_name] = svg
            print("✅")
        else:
            failed_icons.append(carbon_name)
            print("❌")
    
    print(f"\n📊 Downloaded {len(downloaded_icons)} of {len(ESSENTIAL_ICONS)} icons")
    
    if failed_icons:
        print(f"\n⚠️  Failed to download: {', '.join(failed_icons)}")
        print("\nTrying alternative names...")
        
        # Try alternative names
        alternatives = {
            "play--filled": "play-filled-alt",
            "chart--bar": "chart-bar",
            "checkmark--filled": "checkmark-filled"
        }
        
        for failed in failed_icons[:]:
            if failed in alternatives:
                alt_name = alternatives[failed]
                print(f"Trying {alt_name}...", end=" ")
                svg = download_carbon_icon(alt_name)
                if svg:
                    python_name = ESSENTIAL_ICONS[failed]
                    downloaded_icons[python_name] = svg
                    failed_icons.remove(failed)
                    print("✅")
                else:
                    print("❌")
    
    if downloaded_icons:
        print("\n📝 Updating carbon_button.py...")
        if update_carbon_button_file(downloaded_icons):
            print("✅ Successfully added new icons!")
            print(f"\n🎉 Done! Added {len(downloaded_icons)} icons to carbon_button.py")
        else:
            print("\n✅ Icons already exist or update not needed")
            
        # Show what was added
        print("\nIcons available:")
        for name in sorted(downloaded_icons.keys()):
            print(f"  - CarbonIcons.{name}")
    
    # Create a quick reference
    print("\n📖 Quick usage example:")
    print("from utils.carbon_button import carbon_button, CarbonIcons")
    print("")
    print('if carbon_button("Upload", CarbonIcons.UPLOAD, key="upload_btn"):')
    print('    st.success("Uploaded!")')