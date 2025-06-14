# Git Worktree Example for Your Workflow

## Your Specific Use Case: Parallel Development

Based on your mention of wanting to develop two things in parallel, here's how git worktrees solve your confusion:

### Before (Manual Directory Copying)
```
/Users/rose/Code/
├── CC/                    # Main work
├── CC-copy/               # Manual copy for feature A
├── CC-backup/             # Another copy for feature B
└── CC-old/                # Which one was this again? 🤔
```
**Problems**: 
- Hard to track which copy has which changes
- Risk of working in wrong directory
- Manual syncing of changes

### After (Git Worktrees)
```
/Users/rose/Code/
├── CC/                    # Main branch
├── CC-economic/           # Economic analysis feature
└── CC-ui-fix/             # UI bug fixes
```
**Benefits**:
- Each directory is a proper git checkout
- Clear branch associations
- Automatic git integration

## Real Example: Economic Analysis + UI Fixes

### Step 1: Start Economic Analysis Feature
```bash
# In your main CC directory
git worktree add ../CC-economic -b feature/economic-analysis
cd ../CC-economic
claude  # Start working on economic features
```

### Step 2: Urgent UI Bug Comes In
```bash
# Don't disturb your economic work! Create new worktree
git worktree add ../CC-ui-fix -b bugfix/ui-crash
cd ../CC-ui-fix
claude  # Fix the bug independently
```

### Step 3: Work in Parallel
- Terminal 1: Continue economic development in CC-economic/
- Terminal 2: Fix UI bugs in CC-ui-fix/
- Terminal 3: Review PRs in main CC/

### Step 4: Check Status Anytime
```bash
./scripts/dev/worktree-status.sh
```
Shows exactly what you're working on in each directory!

### Step 5: Clean Up When Done
```bash
# After merging economic feature
cd ~/Code/CC
git worktree remove ../CC-economic

# After fixing UI bug
git worktree remove ../CC-ui-fix
```

## Your Workspace/ Directory in Each Worktree

Each worktree gets its own workspace/:
- `CC/workspace/` - General experiments
- `CC-economic/workspace/` - Economic analysis experiments
- `CC-ui-fix/workspace/` - UI debugging tests

No more confusion about which test belongs to which feature!

## Try It Now!

```bash
# Create a test worktree
git worktree add ../CC-test -b test/worktree-demo

# Check your worktrees
./scripts/dev/worktree-status.sh

# Remove it
git worktree remove ../CC-test
```

This eliminates the confusion you mentioned and makes parallel development much cleaner!