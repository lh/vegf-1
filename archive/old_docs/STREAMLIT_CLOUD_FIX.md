# Streamlit Cloud Deployment Fix

Since your app works in GitHub Codespaces but not on Streamlit Cloud, the issue is with Streamlit Cloud's configuration, not your code.

## Most Likely Issues & Solutions

### 1. **Old App Configuration Cached** (MOST LIKELY)

Streamlit Cloud is probably still looking for the old path (`streamlit_app_v2/APE.py`).

**Solution:**
1. Go to https://share.streamlit.io/
2. Find your app (might be listed as VEGF-1 or vegf-1)
3. Click the three dots menu (⋮) → **Delete app**
4. Wait 2-3 minutes for full deletion
5. Click **New app**
6. Configure:
   - GitHub repo: `lh/vegf-1`
   - Branch: `main`
   - Main file path: `APE.py` (just this, no directory)
7. Deploy

### 2. **Python Version Mismatch**

Streamlit Cloud might be using a different Python version.

**Solution - Add these files to your repo root:**

Create `.python-version`:
```
3.11
```

Or create `runtime.txt`:
```
python-3.11.0
```

### 3. **Hidden Import Issues**

Some imports might work locally but fail on Streamlit Cloud.

**Quick Test - Create a minimal APE:**
```python
# Save as TEST_APE.py
import streamlit as st

st.set_page_config(page_title="Test APE", page_icon="🦍")
st.title("Test Deployment")
st.write("If you see this, basic deployment works!")

# Now test imports one by one
try:
    from ape.utils.carbon_button_helpers import navigation_button
    st.success("✅ Import successful!")
except Exception as e:
    st.error(f"❌ Import failed: {e}")
```

Deploy `TEST_APE.py` first to isolate the issue.

### 4. **Requirements.txt Issues**

Sometimes version conflicts only show up in deployment.

**Create a minimal requirements.txt for testing:**
```
streamlit==1.28.0
pandas==2.0.0
numpy==1.24.0
matplotlib==3.7.0
pyyaml==6.0
```

### 5. **Case Sensitivity in Imports**

Linux (Streamlit Cloud) is case-sensitive, macOS/Windows often aren't.

**Check all your imports match exact case:**
```bash
# Find potential case issues
find . -name "*.py" -type f -exec grep -l "from ape" {} \; | head -20
```

## Quick Diagnostic Steps

### Step 1: Check Streamlit Cloud Logs
1. Go to your app on Streamlit Cloud
2. Click **Manage app** → **View logs**
3. Look for the EXACT error message
4. Common errors:
   - `ModuleNotFoundError`: Missing from requirements.txt
   - `FileNotFoundError`: Wrong file path
   - `ImportError`: Package version conflict

### Step 2: Test with Minimal App
Create `MINIMAL_APE.py`:
```python
import streamlit as st

st.title("Minimal APE Test")
st.write("Testing deployment...")

# Test file system
import os
st.write("Current directory:", os.getcwd())
st.write("Files in root:", os.listdir("."))

# Test pages directory
if os.path.exists("pages"):
    st.write("Pages found:", os.listdir("pages"))
else:
    st.error("Pages directory not found!")
```

### Step 3: Force Rebuild
Sometimes Streamlit Cloud needs a forced rebuild:

1. Make a trivial change (add a space to README.md)
2. Commit and push:
   ```bash
   git add README.md
   git commit -m "Force Streamlit Cloud rebuild"
   git push
   ```

## If Nothing Works

### Nuclear Option - New Repository
1. Create a new repo `vegf-1-deploy` 
2. Copy only essential files:
   - APE.py
   - pages/
   - ape/
   - requirements.txt
   - .streamlit/
   - assets/
   - protocols/
3. Deploy from new repo
4. If it works, you know it's a configuration issue with the original

### Contact Streamlit Support
Post on https://discuss.streamlit.io/ with:
- Your repo URL
- Deployment URL
- Error message from logs
- Screenshot of deployment settings

## Most Common Fix

90% of the time, it's the cached configuration. The full delete + recreate usually fixes it:

1. **Delete** existing app completely
2. **Wait** 5 minutes (important!)
3. **Create** new app with correct settings
4. **Ensure** Main file path is just `APE.py` not `streamlit_app_v2/APE.py`

The fact that it works in Codespaces confirms your code is fine - this is purely a Streamlit Cloud configuration issue.