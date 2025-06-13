# 📁 WHERE TO PUT THINGS - Directory Guide

**IMPORTANT**: Read this before creating any new files!

## 🚨 Golden Rule
**NEVER create files directly in the root directory unless they are:**
- Configuration files (.gitignore, Dockerfile, etc.)
- Package files (requirements.txt, package.json)
- Main entry points (APE.py)
- Essential documentation (README.md, CLAUDE.md)

## 📂 Directory Guide

### For Development Work

#### `workspace/` - Your Development Playground 🎮
**USE THIS FIRST!** A scratch space for active development.
- Temporary test scripts
- Quick experiments
- Data exploration
- Work-in-progress code
- Can be messy - cleaned up regularly

#### `dev/test_scripts/` - Test & Debug Scripts 🧪
- `test_*.py` - Test scripts
- `debug_*.py` - Debug scripts
- `verify_*.py` - Verification scripts
- `fix_*.py` - Fix scripts
- `validate_*.py` - Validation scripts

#### `dev/experiments/` - Experimental Features 🔬
- New feature prototypes
- Performance experiments
- Alternative implementations

### For Scripts & Tools

#### `scripts/analysis/` - Analysis Scripts 📊
- `analyze_*.py` - Data analysis
- `extract_*.py` - Data extraction
- `compare_*.py` - Comparison tools

#### `scripts/simulation/` - Simulation Runners 🏃
- `run_*.py` - Scripts that run simulations
- Batch processing scripts
- Performance testing scripts

#### `scripts/setup/` - Setup & Configuration 🔧
- `*.sh` - Shell scripts
- Installation scripts
- Environment setup

### For Output & Data

#### `output/` - All Generated Files 📤 (GITIGNORED)
- `output/plots/` - PNG, PDF, SVG files
- `output/data/` - CSV, JSON output files
- `output/logs/` - Log files
- **Note**: This entire directory is gitignored!

### For Documentation

#### `meta/planning/` - Planning & Design Docs 📝
- `*_PLAN.md` - Planning documents
- `*_SUMMARY.md` - Summary documents
- `*_GUIDE.md` - Guide documents
- Design decisions
- Meeting notes

#### `meta/clinical_summaries/` - Clinical Documentation 🏥
- Protocol summaries
- Clinical trial data
- Literature reviews

## 🎯 Quick Decision Tree

**"Where should I put this file?"**

1. **Is it a quick test or experiment?**
   → `workspace/`

2. **Is it a test/debug/verify script?**
   → `dev/test_scripts/`

3. **Is it analyzing existing data?**
   → `scripts/analysis/`

4. **Is it running simulations?**
   → `scripts/simulation/`

5. **Is it output from running code?**
   → `output/` (gitignored)

6. **Is it documentation?**
   → `meta/planning/` or `meta/clinical_summaries/`

7. **Is it a new experimental feature?**
   → `dev/experiments/`

8. **Still unsure?**
   → `workspace/` first, organize later!

## 🚫 What NOT to Do

❌ DON'T create test files in root
❌ DON'T save plots/output in root  
❌ DON'T leave temporary files in root
❌ DON'T create "quick test" files in root

## 💡 Pro Tips

1. **Use workspace/ liberally** - It's there to be messy
2. **Run this check**: `ls -la | grep -E "^-" | wc -l` 
   - Should be < 30 files at root
3. **Regular cleanup**: Move files from workspace/ to proper locations
4. **When in doubt**: Put it in workspace/ first

## 🧹 Keeping It Clean

### Weekly Cleanup Checklist
- [ ] Check root for stray files
- [ ] Clean up workspace/
- [ ] Move test scripts to dev/test_scripts/
- [ ] Delete old output files
- [ ] Organize new documentation

### Before Committing
- [ ] No new files in root (unless essential)
- [ ] Output files are in output/ (gitignored)
- [ ] Test scripts are in proper directories
- [ ] Workspace is reasonably clean

---

## 🌳 Working on Multiple Features? Use Git Worktrees!

Instead of manually copying directories (and getting confused), use git worktrees:

### Why Worktrees?
- Work on multiple features in parallel
- Each feature gets its own directory
- No confusion about which directory has which changes
- Shared git history across all worktrees

### Quick Start
```bash
# Add a new worktree for a feature
git worktree add ../CC-economic-analysis -b feature/economic-analysis

# Check all your worktrees
scripts/dev/worktree-status.sh

# Remove when done
git worktree remove ../CC-economic-analysis
```

### Learn More
- Full guide: `meta/planning/GIT_WORKTREE_STRATEGY.md`
- Status helper: `scripts/dev/worktree-status.sh`

---

**Remember**: A clean repository is a happy repository! 🎉