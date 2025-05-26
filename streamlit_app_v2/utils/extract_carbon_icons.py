"""
Helper script to automatically extract and update Carbon icons in carbon_button.py

Usage:
1. npm install @carbon/icons (in the utils directory)
2. python extract_carbon_icons.py
3. Icons are automatically added to carbon_button.py
4. npm uninstall @carbon/icons (cleanup)
"""

import os
import re
from pathlib import Path

def extract_carbon_icon(icon_name: str, size: int = 32) -> str:
    """Extract a Carbon icon SVG from node_modules"""
    
    # Common paths where npm might install
    possible_paths = [
        f"node_modules/@carbon/icons/svg/{size}/{icon_name}.svg",
        f"../node_modules/@carbon/icons/svg/{size}/{icon_name}.svg",
        f"../../node_modules/@carbon/icons/svg/{size}/{icon_name}.svg",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read().strip()
                # Clean up the SVG (remove XML declaration if present)
                content = re.sub(r'<\?xml.*?\?>', '', content).strip()
                return content
    
    return None

def update_carbon_icons_class(icons_dict: dict):
    """Update the CarbonIcons class in carbon_button.py"""
    
    carbon_button_path = Path(__file__).parent / "carbon_button.py"
    
    if not carbon_button_path.exists():
        print(f"Error: {carbon_button_path} not found!")
        return False
    
    # Read the current file
    with open(carbon_button_path, 'r') as f:
        content = f.read()
    
    # Find the CarbonIcons class
    class_start = content.find("class CarbonIcons:")
    if class_start == -1:
        print("Error: CarbonIcons class not found!")
        return False
    
    # Find the end of the class (next class or end of file)
    class_end = content.find("\nclass ", class_start + 1)
    if class_end == -1:
        class_end = content.find("\n\n# ", class_start + 1)
    if class_end == -1:
        class_end = len(content)
    
    # Build the new class content
    new_class_lines = [
        "class CarbonIcons:",
        '    """',
        '    Carbon Design System icons (v11)',
        '    Downloaded from: https://carbondesignsystem.com/',
        '    ',
        '    To add more icons:',
        '    1. Visit https://carbondesignsystem.com/elements/icons/library/',
        '    2. Search for the icon you need',
        '    3. Download as SVG (32px size recommended)',
        '    4. Copy the SVG content here',
        '    ',
        '    Benefits of embedding:',
        '    - No npm/node dependencies',
        '    - Works on Streamlit Community Cloud',
        '    - Fast loading (no external requests)',
        '    - Version stable',
        '    """',
        '    '
    ]
    
    # Add each icon
    for icon_name, svg_content in sorted(icons_dict.items()):
        new_class_lines.append(f"    {icon_name} = '''{svg_content}'''")
        new_class_lines.append("    ")
    
    # Join the lines
    new_class_content = '\n'.join(new_class_lines)
    
    # Replace the old class with the new one
    new_content = content[:class_start] + new_class_content + content[class_end:]
    
    # Write back to file
    with open(carbon_button_path, 'w') as f:
        f.write(new_content)
    
    return True

# Icons we need for the app (Carbon naming -> Python naming)
ICON_MAPPINGS = {
    "upload": "UPLOAD",
    "download": "DOWNLOAD", 
    "copy": "COPY",
    "play--filled": "PLAY",
    "document": "DOCUMENT",
    "home": "HOME",
    "chart--bar": "CHART_BAR",
    "warning": "WARNING",
    "warning--filled": "WARNING_FILLED",
    "information": "INFO",
    "information--filled": "INFO_FILLED",
    "delete": "DELETE",
    "add": "ADD",
    "checkmark": "CHECKMARK",
    "checkmark--filled": "SUCCESS",
    "close": "CLOSE",
    "error": "ERROR",
    "error--filled": "ERROR_FILLED",
    "folder": "FOLDER",
    "settings": "SETTINGS",
    "analytics": "ANALYTICS",
    "dashboard": "DASHBOARD",
    "save": "SAVE",
    "edit": "EDIT",
    "view": "VIEW",
    "search": "SEARCH",
    "filter": "FILTER",
    "refresh": "REFRESH",
    "send": "SEND",
    "calendar": "CALENDAR",
    "time": "TIME",
    "user": "USER",
    "users": "USERS",
    "logout": "LOGOUT",
    "login": "LOGIN"
}

if __name__ == "__main__":
    print("🔍 Extracting Carbon icons...")
    
    # Check if @carbon/icons is installed
    if not any(os.path.exists(p) for p in ["node_modules/@carbon/icons", "../node_modules/@carbon/icons"]):
        print("\n❌ @carbon/icons not found!")
        print("\nTo install:")
        print("  cd utils")
        print("  npm install @carbon/icons")
        print("\nThen run this script again.")
        exit(1)
    
    # Extract icons
    extracted_icons = {}
    missing_icons = []
    
    for carbon_name, python_name in ICON_MAPPINGS.items():
        svg = extract_carbon_icon(carbon_name)
        if svg:
            extracted_icons[python_name] = svg
            print(f"✅ Extracted: {carbon_name} -> {python_name}")
        else:
            missing_icons.append(carbon_name)
            print(f"❌ Not found: {carbon_name}")
    
    print(f"\n📊 Extracted {len(extracted_icons)} of {len(ICON_MAPPINGS)} icons")
    
    if missing_icons:
        print(f"\n⚠️  Missing icons: {', '.join(missing_icons)}")
        print("These might have different names in the Carbon library.")
    
    # Update the carbon_button.py file
    print("\n📝 Updating carbon_button.py...")
    if update_carbon_icons_class(extracted_icons):
        print("✅ Successfully updated CarbonIcons class!")
        print(f"\n🎉 Done! {len(extracted_icons)} icons have been added to carbon_button.py")
        print("\nYou can now uninstall @carbon/icons:")
        print("  npm uninstall @carbon/icons")
    else:
        print("❌ Failed to update carbon_button.py")
        print("\nManual update needed. Here are the icons:\n")
        for name, svg in extracted_icons.items():
            print(f"    {name} = '''{svg}'''\n")