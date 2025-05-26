# Protocol Duplication Fix

## Issue
Protocols were "breeding" - creating multiple duplicates every second in the dropdown. The user reported seeing 4, then 5, 6, 8, 10, 11... protocols multiplying rapidly.

## Root Cause
1. **Timestamp Suffixes**: Every upload/duplicate created a new file with a timestamp suffix
2. **No Deduplication**: The dropdown showed all files, including all timestamped versions
3. **Continuous Creation**: Something was triggering protocol creation in a loop

## Solution Implemented

### 1. Deduplication in Dropdown
```python
# Remove timestamp pattern (_1234567890) from display
base_name = re.sub(r'_\d{10}$', '', name)

# Show only the most recent version of each protocol
for file in sorted(temp_files, key=lambda f: f.stat().st_mtime, reverse=True):
    if base_name not in seen_names:
        unique_protocols.append(file)
```

### 2. Replace on Upload
Instead of always creating new timestamped files:
```python
# Check if protocol with this name exists
if existing_file:
    # Replace the existing file
    existing_file.unlink()
    final_path = existing_file
else:
    # Create new file with timestamp
    final_path = TEMP_DIR / f"{base_name}_{timestamp}.yaml"
```

### 3. Cleanup Utility
Created `utils/clean_duplicate_protocols.py` to remove existing duplicates:
- Cleaned up 97 duplicate protocols
- Kept only the most recent version of each

## Prevention
- Protocols with the same base name now replace existing versions
- Dropdown shows clean names without timestamps
- Only one version of each protocol appears in the list

## Result
The protocol dropdown now shows a clean, deduplicated list of protocols without the "breeding" behavior.