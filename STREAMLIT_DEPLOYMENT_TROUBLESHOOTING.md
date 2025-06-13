# Streamlit Cloud Deployment Troubleshooting

## Current Issue
After refactoring, Streamlit Cloud cannot find the app or shows access issues. The deployment is looking for "VEGF-1" (uppercase) instead of "vegf-1" (lowercase).

## Solutions to Try

### 1. Update Streamlit Cloud Settings

In your Streamlit Cloud dashboard:

1. **Delete the old app deployment**
   - Go to https://share.streamlit.io/
   - Find the existing VEGF-1 app
   - Click on the three dots menu → Delete app
   - This will clear any cached settings from the old structure

2. **Create a fresh deployment**
   - Click "New app"
   - Repository: `lh/vegf-1` (ensure lowercase)
   - Branch: `main`
   - Main file path: `APE.py` (NOT `streamlit_app_v2/APE.py`)
   - Click "Deploy"

### 2. Repository Name Case Sensitivity

GitHub repository names are case-sensitive in URLs but not in the repository itself. Check:

1. Go to your GitHub repository settings
2. Verify the exact repository name (should be `vegf-1`)
3. If it's `VEGF-1`, you might want to rename it to `vegf-1` for consistency

### 3. Streamlit Configuration Files

Ensure these files exist in your repository root:

**`.streamlit/config.toml`** (already exists)
```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

**`packages.txt`** (if you need system dependencies)
```
# Add any apt-get packages here if needed
```

### 4. Python Version Specification

Create a `.python-version` file:
```
3.11
```

Or add to `runtime.txt`:
```
python-3.11.0
```

### 5. Entry Point Verification

Make sure Streamlit Cloud can find your app:

1. The main file must be `APE.py` in the root directory
2. It should contain Streamlit code (imports streamlit, has st.set_page_config, etc.)
3. The pages/ directory must be at root level (Streamlit requirement)

### 6. Requirements.txt Issues

Common problems:
- Missing `streamlit` package (it's there in yours ✓)
- Version conflicts
- Development dependencies causing issues

Your requirements.txt looks correct for production.

### 7. Access and Permissions

If you see "doesn't have access":

1. **Check repository visibility**
   - If private, ensure Streamlit Cloud has access
   - Go to GitHub Settings → Applications → Streamlit → Configure
   - Ensure your repository is in the allowed list

2. **Re-authenticate**
   - Log out of Streamlit Cloud
   - Log back in with GitHub
   - Re-authorize the GitHub app if prompted

### 8. Clear Cache and Cookies

Sometimes Streamlit Cloud caches old configurations:
1. Clear browser cache/cookies for share.streamlit.io
2. Try incognito/private browsing mode
3. Try a different browser

### 9. Debug with Logs

In Streamlit Cloud:
1. Click on your app
2. Click "Manage app" → "View logs"
3. Look for specific error messages about:
   - File not found
   - Import errors
   - Permission issues

## Quick Checklist

- [ ] Repository name is lowercase `vegf-1` in GitHub
- [ ] Main branch is `main` (not `master`)
- [ ] `APE.py` exists in root directory
- [ ] `pages/` directory exists in root
- [ ] `requirements.txt` is in root
- [ ] No syntax errors in Python files
- [ ] Streamlit Cloud has access to repository (if private)
- [ ] Old deployment was deleted before creating new one

## If All Else Fails

1. **Fork and Test**
   - Fork the repository to a test account
   - Deploy from the fork to isolate if it's a repo-specific issue

2. **Minimal Test**
   - Create branch with just APE.py and requirements.txt
   - Deploy that to verify basic connectivity

3. **Contact Support**
   - Streamlit Community Forum: https://discuss.streamlit.io/
   - Include deployment URL and error messages

## Deployment URL Format

Your deployment URL should be:
```
https://vegf-1.streamlit.app/
```

NOT:
```
https://VEGF-1.streamlit.app/
```

The subdomain is based on your repository name and must be lowercase.