# Deployment Branch Maintenance Guide

## Overview
The `deployment` branch is a clean version of `main` without submodules and development files, specifically for Streamlit Cloud deployment.

## Keeping Deployment Updated

### Method 1: Automated Sync Script (Recommended)
```bash
# Run from main branch after making changes
./scripts/sync_deployment.sh
```

This script:
- Updates main from origin
- Merges changes while preserving deployment's clean structure
- Removes any accidentally added files
- Creates a commit with the sync date

### Method 2: Manual Cherry-Pick (For Specific Changes)
```bash
# 1. Make changes on main
git checkout main
# ... make your changes ...
git commit -m "Fix: Update visualization"
git push origin main

# 2. Note the commit hash
git log -1 --oneline
# Example output: abc1234 Fix: Update visualization

# 3. Apply to deployment
git checkout deployment
git cherry-pick abc1234
git push origin deployment
```

### Method 3: GitHub Actions (Automated CI/CD)
Create `.github/workflows/sync-deployment.yml`:

```yaml
name: Sync Deployment Branch
on:
  push:
    branches: [main]
    paths:
      - 'APE.py'
      - 'pages/**'
      - 'ape/**'
      - 'simulation_v2/**'
      - 'visualization/**'
      - 'requirements.txt'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Sync deployment branch
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          
          # Checkout deployment
          git checkout deployment
          
          # Merge main changes
          git merge main --strategy=ours --no-commit
          
          # Cherry-pick only app files
          git checkout main -- APE.py pages/ ape/ assets/ protocols/ simulation_v2/ visualization/ requirements.txt
          
          # Remove submodules
          rm -rf aflibercept_2mg_data eylea_high_dose_data vegf_literature_data || true
          
          # Commit if there are changes
          git diff --cached --quiet || git commit -m "Auto-sync with main - $(date +%Y-%m-%d)"
          
          # Push
          git push origin deployment
```

### Method 4: Git Worktree Workflow
Using the worktree setup from earlier:

```bash
# Set up deployment worktree
git worktree add ../CC-deployment deployment

# Work in main
cd ~/Code/CC
# ... make changes ...
git commit -m "Update"
git push

# Sync to deployment
cd ../CC-deployment
git merge main --strategy=ours --no-commit
git checkout main -- APE.py pages/ ape/ simulation_v2/ visualization/ requirements.txt
git commit -m "Sync with main"
git push
```

## What Gets Synced

### Always Sync These:
- `APE.py` - Main application
- `pages/*.py` - All page files
- `ape/**/*.py` - Core application modules
- `simulation_v2/**/*.py` - Simulation engine
- `visualization/**/*.py` - Visualization components
- `assets/` - Images and static files
- `protocols/` - Protocol configurations
- `requirements.txt` - Dependencies
- `README.md` - Documentation
- `CLAUDE.md` - AI instructions

### Never Sync These:
- Git submodules (aflibercept_2mg_data, etc.)
- Test files and directories
- Development scripts
- Documentation beyond README
- Archive directories
- Output/data files
- Workspace directories

## Best Practices

1. **Test Locally First**
   ```bash
   git checkout deployment
   streamlit run APE.py
   ```

2. **Keep Commits Atomic**
   - Make small, focused changes
   - Easier to cherry-pick if needed

3. **Tag Deployments**
   ```bash
   git tag -a v1.0.0-deploy -m "Production deployment v1.0.0"
   git push origin v1.0.0-deploy
   ```

4. **Monitor Deployment Size**
   ```bash
   git checkout deployment
   du -sh .
   find . -type f -name "*.py" | wc -l
   ```

5. **Regular Maintenance**
   - Sync weekly or after major features
   - Check for accidentally added files
   - Verify Streamlit Cloud deployment works

## Troubleshooting

### If Submodules Reappear
```bash
git rm -rf aflibercept_2mg_data eylea_high_dose_data vegf_literature_data
git rm -f .gitmodules
git commit -m "Remove submodules"
```

### If Large Files Get Added
```bash
find . -type f -size +1M -not -path "./.git/*"
# Remove any large files found
```

### If Deployment Fails
1. Check Streamlit Cloud logs
2. Verify no private dependencies
3. Test with minimal requirements.txt
4. Try deploying a simple test file first

## Emergency Rollback
```bash
# Find last working deployment
git log --oneline -10

# Reset to that commit
git reset --hard <commit-hash>
git push --force origin deployment
```