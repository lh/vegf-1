"""
Utility to clean up duplicate protocols in the temp directory.

This removes older versions of protocols that have the same base name,
keeping only the most recent version of each.
"""

import re
from pathlib import Path
from collections import defaultdict
import time


def clean_duplicate_protocols():
    """Remove duplicate protocols, keeping only the newest version of each."""
    # Fix the path to point to the correct location
    TEMP_DIR = Path(__file__).parent.parent.parent / "protocols" / "v2" / "temp"
    
    if not TEMP_DIR.exists():
        print("No temp directory found.")
        return
    
    # Group files by base name
    protocol_groups = defaultdict(list)
    
    for file in TEMP_DIR.glob("*.yaml"):
        # Extract base name (remove timestamp suffix)
        base_name = re.sub(r'_\d{10}$', '', file.stem)
        protocol_groups[base_name].append(file)
    
    # Process each group
    total_deleted = 0
    for base_name, files in protocol_groups.items():
        if len(files) > 1:
            # Sort by modification time, newest first
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            print(f"\nFound {len(files)} versions of '{base_name}':")
            for i, file in enumerate(files):
                mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file.stat().st_mtime))
                if i == 0:
                    print(f"  ✓ Keeping: {file.name} (modified: {mtime})")
                else:
                    print(f"  ✗ Deleting: {file.name} (modified: {mtime})")
                    try:
                        file.unlink()
                        total_deleted += 1
                    except Exception as e:
                        print(f"    Error deleting: {e}")
    
    if total_deleted > 0:
        print(f"\n✅ Cleaned up {total_deleted} duplicate protocol(s)")
    else:
        print("\n✅ No duplicates found")


if __name__ == "__main__":
    print("Protocol Cleanup Utility")
    print("=" * 50)
    clean_duplicate_protocols()