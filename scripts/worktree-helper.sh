#!/bin/bash
# Git Worktree Helper for Multi-Claude Development
# This script helps manage multiple worktrees for parallel development with different Claude instances

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the repository root
REPO_ROOT=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename "$REPO_ROOT")

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Create a new feature worktree
new-feature() {
    if [ -z "$1" ]; then
        print_error "Usage: worktree-helper.sh new-feature <feature-name>"
        echo "Example: worktree-helper.sh new-feature economic-analysis"
        exit 1
    fi
    
    local feature_name="$1"
    local branch_name="feature/$feature_name"
    local worktree_dir="../${REPO_NAME}-${feature_name}"
    
    print_info "Creating worktree for feature: $feature_name"
    
    # Check if branch already exists
    if git show-ref --verify --quiet "refs/heads/$branch_name"; then
        print_warning "Branch $branch_name already exists. Creating worktree from existing branch."
        git worktree add "$worktree_dir" "$branch_name"
    else
        # Create new branch from main
        git worktree add -b "$branch_name" "$worktree_dir" main
    fi
    
    print_success "Created worktree at $worktree_dir with branch $branch_name"
    
    # Create a CLAUDE.md file with context for the Claude instance
    cat > "$REPO_ROOT/$worktree_dir/CLAUDE_CONTEXT.md" << EOF
# Claude Context for $feature_name

You are working in the **$feature_name** worktree on branch **$branch_name**.

## Your Focus Area
Focus exclusively on: $feature_name

## Important Notes
- This is a git worktree, not the main repository
- Your branch: $branch_name
- Parent directory: $worktree_dir
- Always commit and push your changes to the feature branch
- Do NOT switch branches or merge to main

## When Complete
Let the user know the feature is ready to merge by saying:
"Feature $feature_name is complete and ready to merge to main"
EOF
    
    print_success "Created CLAUDE_CONTEXT.md in the worktree"
    echo ""
    print_info "Next steps:"
    echo "  1. cd $worktree_dir"
    echo "  2. Share CLAUDE_CONTEXT.md with your Claude instance"
    echo "  3. Start developing!"
}

# List all worktrees with useful info
list-worktrees() {
    print_info "Current worktrees:"
    echo ""
    
    git worktree list | while read -r line; do
        local path=$(echo "$line" | awk '{print $1}')
        local commit=$(echo "$line" | awk '{print $2}')
        local branch=$(echo "$line" | awk -F'[][]' '{print $2}')
        
        if [[ "$path" == "$REPO_ROOT" ]]; then
            echo -e "${GREEN}Main:${NC} $path [$branch]"
        else
            local dirname=$(basename "$path")
            echo -e "${BLUE}Feature:${NC} $dirname [$branch]"
        fi
    done
}

# Sync a feature branch with main
sync-feature() {
    if [ -z "$1" ]; then
        print_error "Usage: worktree-helper.sh sync-feature <feature-name>"
        exit 1
    fi
    
    local feature_name="$1"
    local branch_name="feature/$feature_name"
    
    print_info "Syncing $branch_name with main..."
    
    # Save current branch
    local current_branch=$(git branch --show-current)
    
    # Fetch latest
    git fetch origin
    
    # Switch to feature branch
    git checkout "$branch_name"
    
    # Rebase on main
    git rebase origin/main
    
    print_success "Feature branch $branch_name is now up to date with main"
    
    # Return to original branch
    git checkout "$current_branch"
}

# Merge a feature and deploy
merge-deploy() {
    if [ -z "$1" ]; then
        print_error "Usage: worktree-helper.sh merge-deploy <feature-name>"
        exit 1
    fi
    
    local feature_name="$1"
    local branch_name="feature/$feature_name"
    
    print_info "Merging $branch_name to main and deploying..."
    
    # Ensure we're on main
    git checkout main
    
    # Pull latest main
    git pull origin main
    
    # Merge feature branch
    print_info "Merging $branch_name into main..."
    git merge "$branch_name" --no-edit
    
    # Push main
    git push origin main
    
    # Deploy to deployment branch
    print_info "Deploying to deployment branch..."
    git checkout deployment
    git merge main --no-edit
    git push origin deployment
    
    # Return to main
    git checkout main
    
    print_success "Feature $feature_name merged and deployed!"
    
    # Ask about cleanup
    echo ""
    read -p "Remove the feature branch and worktree? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup-feature "$feature_name"
    fi
}

# Clean up a feature (remove worktree and branch)
cleanup-feature() {
    if [ -z "$1" ]; then
        print_error "Usage: worktree-helper.sh cleanup-feature <feature-name>"
        exit 1
    fi
    
    local feature_name="$1"
    local branch_name="feature/$feature_name"
    local worktree_dir="../${REPO_NAME}-${feature_name}"
    
    print_info "Cleaning up feature: $feature_name"
    
    # Remove worktree
    if git worktree list | grep -q "$worktree_dir"; then
        git worktree remove "$worktree_dir" --force
        print_success "Removed worktree: $worktree_dir"
    else
        print_warning "Worktree not found: $worktree_dir"
    fi
    
    # Delete local branch
    git branch -D "$branch_name" 2>/dev/null && print_success "Deleted local branch: $branch_name" || print_warning "Local branch not found: $branch_name"
    
    # Delete remote branch
    git push origin --delete "$branch_name" 2>/dev/null && print_success "Deleted remote branch: $branch_name" || print_warning "Remote branch not found: $branch_name"
}

# Quick status of all worktrees
status-all() {
    print_info "Status of all worktrees:"
    echo ""
    
    git worktree list | while read -r line; do
        local path=$(echo "$line" | awk '{print $1}')
        local branch=$(echo "$line" | awk -F'[][]' '{print $2}')
        
        echo -e "${BLUE}=== $path [$branch] ===${NC}"
        
        # Run git status in that worktree
        git -C "$path" status --short --branch
        echo ""
    done
}

# Deploy current main to deployment
quick-deploy() {
    print_info "Quick deploy from main to deployment..."
    
    local current_branch=$(git branch --show-current)
    
    git checkout main
    git pull origin main
    git checkout deployment
    git merge main --no-edit
    git push origin deployment
    git checkout "$current_branch"
    
    print_success "Deployed main to deployment branch!"
}

# Setup aliases for easier use
setup-aliases() {
    print_info "Setting up git aliases for worktree commands..."
    
    # Get the absolute path to the script
    local script_path="$REPO_ROOT/scripts/worktree-helper.sh"
    
    git config --global alias.wnew "!bash $script_path new-feature"
    git config --global alias.wlist "!bash $script_path list-worktrees"
    git config --global alias.wsync "!bash $script_path sync-feature"
    git config --global alias.wmerge "!bash $script_path merge-deploy"
    git config --global alias.wclean "!bash $script_path cleanup-feature"
    git config --global alias.wstatus "!bash $script_path status-all"
    git config --global alias.deploy "!bash $script_path quick-deploy"
    
    print_success "Git aliases created!"
    echo ""
    echo "You can now use:"
    echo "  git wnew <feature-name>     - Create new feature worktree"
    echo "  git wlist                   - List all worktrees"
    echo "  git wsync <feature-name>    - Sync feature with main"
    echo "  git wmerge <feature-name>   - Merge feature and deploy"
    echo "  git wclean <feature-name>   - Clean up feature"
    echo "  git wstatus                 - Status of all worktrees"
    echo "  git deploy                  - Quick deploy main to deployment"
}

# Help message
show-help() {
    echo "Git Worktree Helper for Multi-Claude Development"
    echo ""
    echo "Usage: $0 <command> [arguments]"
    echo ""
    echo "Commands:"
    echo "  new-feature <name>      Create a new feature worktree"
    echo "  list-worktrees          List all worktrees"
    echo "  sync-feature <name>     Sync feature branch with main"
    echo "  merge-deploy <name>     Merge feature to main and deploy"
    echo "  cleanup-feature <name>  Remove worktree and delete branch"
    echo "  status-all              Show status of all worktrees"
    echo "  quick-deploy            Deploy main to deployment branch"
    echo "  setup-aliases           Create git aliases for easy access"
    echo "  help                    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 new-feature economic-analysis"
    echo "  $0 merge-deploy economic-analysis"
    echo "  $0 setup-aliases  # Then use: git wnew my-feature"
}

# Main command dispatcher
case "$1" in
    new-feature)
        new-feature "$2"
        ;;
    list-worktrees)
        list-worktrees
        ;;
    sync-feature)
        sync-feature "$2"
        ;;
    merge-deploy)
        merge-deploy "$2"
        ;;
    cleanup-feature)
        cleanup-feature "$2"
        ;;
    status-all)
        status-all
        ;;
    quick-deploy)
        quick-deploy
        ;;
    setup-aliases)
        setup-aliases
        ;;
    help|--help|-h|"")
        show-help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show-help
        exit 1
        ;;
esac