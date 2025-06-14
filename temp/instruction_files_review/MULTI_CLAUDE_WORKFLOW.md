# Multi-Claude Development Workflow

This document describes how to work with multiple Claude instances simultaneously using git worktrees.

## Quick Start

We've set up git aliases for easy worktree management:

```bash
# Create a new feature worktree
git wnew economic-analysis

# List all worktrees
git wlist

# Check status of all worktrees
git wstatus

# Merge feature and deploy
git wmerge economic-analysis

# Quick deploy main to deployment
git deploy
```

## Workflow Overview

```
main branch (CC/)
    ├── feature/economic-analysis (CC-economic-analysis/)
    ├── feature/ui-improvements (CC-ui-improvements/)
    └── feature/plotly-fixes (CC-plotly-fixes/)
             ↓
         main (merge)
             ↓
       deployment (auto-deploy)
```

## Step-by-Step Guide

### 1. Starting a New Feature with a Claude

```bash
# Create a new worktree for Claude to work in
git wnew economic-analysis

# This creates:
# - Directory: ../CC-economic-analysis/
# - Branch: feature/economic-analysis
# - Context file: CLAUDE_CONTEXT.md
```

### 2. Give Context to Claude

Share the contents of `CLAUDE_CONTEXT.md` with your Claude instance:

```
You are working in the **economic-analysis** worktree on branch **feature/economic-analysis**.

## Your Focus Area
Focus exclusively on: economic-analysis

## Important Notes
- This is a git worktree, not the main repository
- Your branch: feature/economic-analysis
- Parent directory: ../CC-economic-analysis/
- Always commit and push your changes to the feature branch
- Do NOT switch branches or merge to main
```

### 3. Work in Parallel

- Claude 1: Works on economic analysis in `CC-economic-analysis/`
- Claude 2: Works on UI improvements in `CC-ui-improvements/`
- Claude 3: Works on visualization fixes in `CC-plotly-fixes/`

No conflicts! Each Claude has their own isolated workspace.

### 4. Check Progress

```bash
# See all worktrees and their branches
git wlist

# Check status across all worktrees
git wstatus
```

### 5. Merge and Deploy

When a feature is complete:

```bash
# Merges to main and deploys automatically
git wmerge economic-analysis

# Or just deploy current main
git deploy
```

## Example Session

```bash
# Monday: Start three features
git wnew economic-analysis
git wnew ui-improvements  
git wnew plotly-fixes

# Give each worktree to a different Claude instance

# Tuesday: UI improvements are done
git wmerge ui-improvements

# Wednesday: Economic analysis is done
git wmerge economic-analysis

# Thursday: All features merged, deploy everything
git deploy
```

## Best Practices

1. **One Feature Per Claude**: Each Claude works on one feature in one worktree
2. **Clear Feature Names**: Use descriptive names like `plotly-fixes` not `fix1`
3. **Regular Syncing**: Run `git wsync feature-name` to keep features up to date
4. **Clean Up**: Run `git wclean feature-name` after merging

## Common Commands Reference

| Command | What it does |
|---------|--------------|
| `git wnew feature-name` | Create new feature worktree |
| `git wlist` | List all worktrees |
| `git wstatus` | Status of all worktrees |
| `git wsync feature-name` | Update feature with latest main |
| `git wmerge feature-name` | Merge feature and deploy |
| `git wclean feature-name` | Remove worktree and branch |
| `git deploy` | Quick deploy main to deployment |

## Troubleshooting

### "Worktree already exists"
```bash
# Remove the old worktree first
git wclean feature-name
# Then create new one
git wnew feature-name
```

### "Cannot merge - conflicts"
```bash
# Sync the feature branch first
git wsync feature-name
# Resolve conflicts in the worktree
cd ../CC-feature-name/
# Fix conflicts, commit, then merge
git wmerge feature-name
```

### Finding a Lost Worktree
```bash
# List all worktrees with paths
git worktree list
```

## Advanced: Manual Commands

If you prefer not to use the aliases:

```bash
# Create worktree manually
git worktree add -b feature/my-feature ../CC-my-feature main

# Remove worktree manually
git worktree remove ../CC-my-feature
git branch -d feature/my-feature

# Deploy manually
git checkout deployment
git merge main --no-edit
git push origin deployment
git checkout main
```