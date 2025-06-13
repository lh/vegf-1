# Git Worktree Development Strategy

## Why Git Worktrees Are Perfect for VEGF-1

### Current Pain Points (Solved by Worktrees)
- Manual directory copying leads to confusion
- Risk of working in wrong directory
- Difficult to track which changes belong where
- Hard to switch contexts between features

### Benefits for Your Workflow
1. **Parallel Development**: Work on economic analysis in one worktree while debugging UI in another
2. **Clean Separation**: Each feature gets its own directory with isolated state
3. **Shared Git History**: All worktrees use the same .git repository
4. **Easy Context Switching**: Just change directories to switch features

## Suggested Worktree Structure

```
/Users/rose/Code/
├── CC/                           # Main worktree (main branch)
├── CC-economic-analysis/         # Feature worktree
├── CC-ui-improvements/           # Feature worktree
├── CC-bugfix-discontinuation/    # Bugfix worktree
└── CC-experiment-streamgraph/    # Experimental worktree
```

## Integration with Current Organization

### 1. Workspace Directory Usage
Each worktree has its own `workspace/` directory for experiments specific to that feature:
- Main worktree: General development
- Feature worktrees: Feature-specific experiments

### 2. Output Directory Isolation
Each worktree generates its own `output/` (gitignored), preventing data mixing

### 3. Configuration Persistence
CLAUDE.md and WHERE_TO_PUT_THINGS.md exist in all worktrees, maintaining consistency

## Recommended Workflow

### Creating a New Feature Worktree
```bash
# From main repository
cd /Users/rose/Code/CC

# Create worktree for economic analysis feature
git worktree add ../CC-economic-analysis -b feature/economic-analysis

# Navigate to new worktree
cd ../CC-economic-analysis

# Start Claude Code in this worktree
claude
```

### Daily Development Pattern
1. **Morning**: Check active worktrees
   ```bash
   git worktree list
   ```

2. **Feature Work**: Navigate to appropriate worktree
   ```bash
   cd ~/Code/CC-economic-analysis
   claude  # Work on economic features
   ```

3. **Bug Fix**: Switch to bugfix worktree
   ```bash
   cd ~/Code/CC-bugfix-discontinuation
   claude  # Fix bugs without disrupting feature work
   ```

### Cleanup When Done
```bash
# After merging feature
git worktree remove ../CC-economic-analysis
```

## Best Practices

### 1. Naming Convention
- Features: `CC-feature-description`
- Bugs: `CC-bugfix-issue`
- Experiments: `CC-experiment-idea`

### 2. Worktree Limits
- Keep active worktrees to 3-4 maximum
- Remove completed worktrees promptly
- Use descriptive branch names

### 3. Development Isolation
- Each worktree's `workspace/` is independent
- Test data stays in worktree's `output/`
- Configuration changes should be coordinated

## Quick Reference Commands

```bash
# List all worktrees
git worktree list

# Add new worktree with new branch
git worktree add ../CC-feature-name -b feature/name

# Add worktree for existing branch
git worktree add ../CC-bugfix bugfix/issue-123

# Remove worktree (after merging)
git worktree remove ../CC-feature-name

# Clean up worktree references
git worktree prune
```

## Integration with Pre-commit Hooks
The pre-commit hook works in all worktrees automatically since it's part of the shared .git directory!

## Example: Starting Economic Analysis Feature

```bash
# In main worktree
cd /Users/rose/Code/CC
git worktree add ../CC-economic -b feature/economic-analysis

# In new worktree
cd ../CC-economic
claude

# Now you can:
# - Implement economic features in CC-economic/
# - Fix urgent bugs in CC/ (main)
# - Test experimental ideas in CC-experiment/
# All without context switching confusion!
```

## Worktree Status Helper Script
Consider adding to scripts/dev/:
```bash
#!/bin/bash
# scripts/dev/worktree-status.sh
echo "🌳 Git Worktree Status"
echo "====================="
git worktree list | while read -r line; do
    dir=$(echo "$line" | awk '{print $1}')
    branch=$(echo "$line" | awk '{print $3}' | tr -d '[]')
    echo ""
    echo "📁 $dir"
    echo "🌿 Branch: $branch"
    if [ -d "$dir" ]; then
        cd "$dir"
        # Show latest commit
        echo "📝 Latest: $(git log -1 --oneline)"
        # Check for uncommitted changes
        if [ -n "$(git status --porcelain)" ]; then
            echo "⚠️  Has uncommitted changes"
        else
            echo "✅ Clean working directory"
        fi
    fi
done
```

This approach will eliminate your directory confusion and make parallel development much smoother!