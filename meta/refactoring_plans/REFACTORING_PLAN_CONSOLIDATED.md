# VEGF-1 Repository Refactoring Plan - Consolidated Version

## Executive Summary
This plan refactors the VEGF-1 repository to achieve easy deployment of the APE simulation platform while preserving all development tools. The key innovation is a **dual-mode structure** that maintains everything in one repository but clearly separates deployment from development.

## Core Principles
1. **Single Repository** - Keep everything together for easier management
2. **Clear Separation** - Deployment vs Development boundaries
3. **No Data Loss** - Preserve all existing tools and utilities
4. **Easy Deployment** - Single command to run production app
5. **Developer Friendly** - All tools remain accessible

## Target Structure

```
vegf-1/
# DEPLOYMENT CORE (What gets deployed)
├── APE.py                          # Main application entry point
├── requirements.txt                # Production dependencies only
├── .streamlit/                     # Streamlit configuration
├── ape/                           # Core application modules
│   ├── components/                # UI components
│   ├── core/                      # Simulation engine
│   ├── pages/                     # Streamlit pages (production only)
│   ├── protocols/                 # Protocol definitions
│   ├── utils/                     # Application utilities
│   └── visualizations/            # Visualization modules
├── assets/                        # Static assets (images, etc.)
├── simulation_results/            # Results directory
└── README.md                      # User documentation

# DEVELOPMENT LAYER (Excluded from deployment)
├── requirements-dev.txt           # Development dependencies
├── CLAUDE.md                      # AI development instructions
├── pyproject.toml                 # Modern Python project config
├── .deployment/                   # Deployment configuration
│   ├── Dockerfile                 # Container setup
│   ├── deploy.sh                  # Deployment scripts
│   └── production.gitignore       # Production exclusions
│
├── dev/                          # Development-only code
│   ├── experiments/              # Experimental features
│   ├── debug_pages/              # Debug UI pages (98_, 99_)
│   ├── test_scripts/             # Testing utilities
│   ├── migration/                # Refactoring tools
│   └── benchmarks/               # Performance testing
│
├── literature_extraction/        # Parameter extraction tools
│   ├── aflibercept_2mg_data/   # Submodule (unchanged)
│   ├── eylea_high_dose_data/   # Submodule (unchanged)
│   ├── vegf_literature_data/   # Submodule (unchanged)
│   └── scripts/                 # Extraction scripts
│
├── clinical_analysis/           # Clinical data analysis
│   ├── analysis/               # Analysis tools
│   ├── scripts/                # Analysis scripts
│   └── README.md               # Documentation
│
├── validation/                  # Scientific validation
│   ├── verify_*.py             # Validation scripts
│   └── test_data/              # Reference data
│
├── visualization/              # Central styling system
│   └── color_system.py         # Shared across all apps
│
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
├── docs/                       # Technical documentation
├── meta/                       # Project insights
├── notebooks/                  # Jupyter notebooks
├── examples/                   # Example usage
├── mcp/                       # MCP servers
├── Paper/                     # Academic paper
├── reports/                   # Generated reports
└── archive/                   # Historical implementations
    ├── streamlit_app/
    ├── streamlit_app_parquet/
    └── old_simulation/
```

## Implementation Phases

### Phase 0: Pre-flight Analysis (Day 1 Morning)
1. **Dependency Mapping**
   ```bash
   # Create dependency graph
   python dev/migration/analyze_imports.py
   ```
2. **Backup Current State**
   ```bash
   git tag pre-refactor-backup
   git push --tags
   ```
3. **Create Feature Branch**
   ```bash
   git checkout -b refactor/deployment-structure
   ```

### Phase 1: Core Extraction (Day 1 Afternoon)
1. **Create APE Core Structure**
   ```bash
   mkdir -p ape/{components,core,pages,protocols,utils,visualizations}
   ```
2. **Move Core Modules** (using git mv)
   ```bash
   # Move from streamlit_app_v2 to ape/
   git mv streamlit_app_v2/components/* ape/components/
   git mv streamlit_app_v2/core/* ape/core/
   # ... etc
   ```
3. **Create APE.py**
   ```python
   # APE.py - Main entry point
   import streamlit as st
   from ape.core import initialize_app
   
   if __name__ == "__main__":
       initialize_app()
   ```

### Phase 2: Development Organization (Day 2)
1. **Create Development Structure**
   ```bash
   mkdir -p dev/{experiments,debug_pages,test_scripts,migration,benchmarks}
   ```
2. **Move Development Tools**
   - Move debug pages (98_, 99_) to dev/debug_pages/
   - Move experiments to dev/experiments/
   - Keep test scripts accessible
3. **Update Import Paths**
   - Use automated script to update imports
   - Maintain backwards compatibility shims

### Phase 3: Deployment Configuration (Day 3)
1. **Create Deployment Tools**
   ```bash
   mkdir -p .deployment
   ```
2. **Production Requirements**
   ```bash
   # requirements.txt (production only)
   streamlit>=1.29.0
   pandas>=2.0.0
   numpy>=1.24.0
   plotly>=5.17.0
   # ... other production deps
   ```
3. **Development Requirements**
   ```bash
   # requirements-dev.txt
   -r requirements.txt
   pytest>=7.0.0
   black>=23.0.0
   pylint>=2.0.0
   # ... development tools
   ```

### Phase 4: Testing & Validation (Day 4)
1. **Update Test Imports**
2. **Run Full Test Suite**
3. **Validate Scientific Accuracy**
4. **Performance Benchmarks**

### Phase 5: Documentation & Cleanup (Day 5)
1. **Update Documentation**
2. **Create Migration Guide**
3. **Archive Old Code**
4. **Update CI/CD**

## Deployment Strategy

### Local Development
```bash
# Full development environment
pip install -r requirements-dev.txt
streamlit run APE.py

# Access development tools
streamlit run dev/debug_pages/99_Debug_Dashboard.py
```

### Production Deployment
```bash
# Production only
pip install -r requirements.txt
streamlit run APE.py --server.maxUploadSize 1000
```

### Docker Deployment
```dockerfile
# .deployment/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY APE.py .
COPY ape/ ./ape/
COPY assets/ ./assets/
COPY .streamlit/ ./.streamlit/
CMD ["streamlit", "run", "APE.py"]
```

### Production Branch Strategy
Instead of complex .gitignore rules, use a deployment script:
```bash
# .deployment/deploy.sh
#!/bin/bash
# Create clean deployment branch
git checkout -b deployment/production
# Remove development directories
git rm -r dev/ literature_extraction/ clinical_analysis/ tests/ notebooks/
git rm -r archive/ examples/ meta/ scripts/
git rm requirements-dev.txt CLAUDE.md
git commit -m "Production deployment"
```

## Key Improvements Over Previous Plans

### 1. **Single Repository Approach**
- Simpler to manage than multiple repos
- Preserves all development context
- Easy to switch between deployment and development

### 2. **Clear Deployment Boundary**
- `ape/` directory contains ONLY production code
- `dev/` directory for ALL development tools
- Simple rule: deploy `ape/` + `APE.py`

### 3. **Preserved Development Workflow**
- All tools remain in the repository
- Development pages easily accessible
- No need to switch repositories

### 4. **Flexible Deployment Options**
- Local development with full tools
- Docker containers for production
- Cloud deployment ready
- Easy CI/CD integration

### 5. **Scientific Integrity Maintained**
- Validation tools always available
- No code changes during refactor
- Git history preserved with git mv

## Success Criteria

### Deployment Success
- [ ] `streamlit run APE.py` works from root
- [ ] Docker build succeeds with minimal image size
- [ ] Production has no development dependencies
- [ ] Deployment takes < 5 minutes

### Development Success
- [ ] All development tools accessible
- [ ] Debug pages work: `streamlit run dev/debug_pages/99_*.py`
- [ ] Tests pass: `pytest tests/`
- [ ] Literature extraction tools functional

### Scientific Success
- [ ] No changes to simulation algorithms
- [ ] All validation scripts pass
- [ ] Patient count conservation verified
- [ ] Results reproducible

### Performance Success
- [ ] App startup < 3 seconds
- [ ] Simulation performance unchanged
- [ ] Memory usage stable
- [ ] No import slowdowns

## Risk Mitigation

### Rollback Strategy
```bash
# If anything goes wrong
git checkout main
git branch -D refactor/deployment-structure
```

### Incremental Testing
- Test after each file move
- Validate imports continuously
- Keep backwards compatibility shims

### Data Protection
- No changes to simulation_results/
- Preserve all .gitignore entries for data
- Validate data paths still work

## Communication Plan

### Before Starting
- Create GitHub issue: "Refactoring for deployment"
- Tag: enhancement, refactoring
- Announce in team channel

### During Refactoring
- Daily progress updates
- Commit messages: "refactor: [phase] description"
- Push feature branch regularly

### After Completion
- PR with full description
- Request review from stakeholders
- Beta testing period (3 days)
- Merge after approval

## Next Steps

1. **Review this plan** - Get stakeholder approval
2. **Run dependency analysis** - Understand current structure
3. **Create migration scripts** - Automate import updates
4. **Begin Phase 0** - Start with backups

## Questions to Resolve

1. Should we keep `streamlit_app_v2` name internally or rename to `ape`?
2. Do we need backwards compatibility for old import paths?
3. Should debug pages be password protected in development?
4. What's the preferred Docker base image?

---

This consolidated plan provides a cleaner, simpler approach that achieves easy deployment without sacrificing any development capabilities. The key insight is using directory structure rather than complex branching or multiple repositories to separate concerns.