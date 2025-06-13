#!/bin/bash
# Git worktree status helper - shows status of all worktrees

echo "🌳 Git Worktree Status"
echo "====================="

# Get the main repository path
MAIN_REPO=$(git worktree list | head -1 | awk '{print $1}')
echo "📍 Main repository: $MAIN_REPO"
echo ""

# Process each worktree
git worktree list | while IFS= read -r line; do
    # Parse worktree info
    dir=$(echo "$line" | awk '{print $1}')
    sha=$(echo "$line" | awk '{print $2}')
    branch=$(echo "$line" | sed -n 's/.*\[\(.*\)\].*/\1/p')
    
    # Check if it's the main worktree
    if [ "$dir" = "$MAIN_REPO" ]; then
        echo "🏠 MAIN WORKTREE"
    else
        echo "🌿 FEATURE WORKTREE"
    fi
    
    echo "📁 Directory: $dir"
    echo "🔖 Branch: $branch"
    
    if [ -d "$dir" ]; then
        # Save current directory
        CURRENT_DIR=$(pwd)
        cd "$dir" || continue
        
        # Show latest commit
        echo "📝 Latest commit: $(git log -1 --format='%h %s' 2>/dev/null || echo 'No commits yet')"
        
        # Check working directory status
        STATUS=$(git status --porcelain 2>/dev/null)
        if [ -z "$STATUS" ]; then
            echo "✅ Clean working directory"
        else
            echo "⚠️  Uncommitted changes:"
            # Count different types of changes
            MODIFIED=$(echo "$STATUS" | grep -c "^ M")
            ADDED=$(echo "$STATUS" | grep -c "^A")
            DELETED=$(echo "$STATUS" | grep -c "^ D")
            UNTRACKED=$(echo "$STATUS" | grep -c "^??")
            
            [ $MODIFIED -gt 0 ] && echo "   📝 Modified: $MODIFIED files"
            [ $ADDED -gt 0 ] && echo "   ➕ Added: $ADDED files"
            [ $DELETED -gt 0 ] && echo "   ➖ Deleted: $DELETED files"
            [ $UNTRACKED -gt 0 ] && echo "   ❓ Untracked: $UNTRACKED files"
        fi
        
        # Check if branch is behind/ahead of remote
        if git rev-parse --abbrev-ref @{u} >/dev/null 2>&1; then
            UPSTREAM=$(git rev-parse --abbrev-ref @{u} 2>/dev/null)
            AHEAD=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "0")
            BEHIND=$(git rev-list --count HEAD..@{u} 2>/dev/null || echo "0")
            
            if [ "$AHEAD" -gt 0 ] || [ "$BEHIND" -gt 0 ]; then
                echo "🔄 Remote status:"
                [ "$AHEAD" -gt 0 ] && echo "   ⬆️  Ahead by $AHEAD commits"
                [ "$BEHIND" -gt 0 ] && echo "   ⬇️  Behind by $BEHIND commits"
            fi
        else
            echo "🔗 No remote tracking branch"
        fi
        
        # Return to original directory
        cd "$CURRENT_DIR"
    else
        echo "❌ Directory not found!"
    fi
    
    echo "---"
    echo ""
done

# Show helpful commands
echo "💡 Quick Commands:"
echo "   Add worktree:    git worktree add ../CC-feature -b feature/name"
echo "   Remove worktree: git worktree remove ../CC-feature"
echo "   List worktrees:  git worktree list"
echo "   Prune stale:     git worktree prune"