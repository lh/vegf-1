#!/bin/bash
# Sync deployment branch with main branch changes
# This script cherry-picks or merges changes from main while preserving deployment structure

set -e

echo "🔄 Syncing deployment branch with main..."

# Save current branch
CURRENT_BRANCH=$(git branch --show-current)

# Ensure we're on main and it's up to date
echo "📥 Updating main branch..."
git checkout main
git pull origin main

# Switch to deployment
echo "🚀 Switching to deployment branch..."
git checkout deployment

# Option 1: Cherry-pick specific commits (recommended for selective updates)
# Uncomment and modify as needed:
# git cherry-pick <commit-hash>

# Option 2: Merge main but keep deployment structure
# This merges code changes but preserves file deletions in deployment
echo "🔀 Merging main changes (keeping deployment structure)..."
git merge main --strategy=ours --no-commit

# Selectively accept changes only for files that exist in deployment
git checkout main -- APE.py pages/ ape/ assets/ protocols/ simulation_v2/ visualization/ requirements.txt README.md CLAUDE.md

# Remove any accidentally added files
echo "🧹 Cleaning up unwanted files..."
# Remove submodules if they got added
rm -rf aflibercept_2mg_data eylea_high_dose_data vegf_literature_data 2>/dev/null || true
git rm -rf aflibercept_2mg_data eylea_high_dose_data vegf_literature_data 2>/dev/null || true

# Remove test and dev directories
git rm -rf tests/ dev/ scripts/ meta/ docs/ archive/ workspace/ 2>/dev/null || true

# Commit the merge
git commit -m "Sync with main branch - $(date +%Y-%m-%d)" || echo "No changes to commit"

echo "✅ Deployment branch synced!"
echo ""
echo "Next steps:"
echo "1. Review changes: git diff HEAD~1"
echo "2. Push to remote: git push origin deployment"
echo "3. Return to $CURRENT_BRANCH: git checkout $CURRENT_BRANCH"