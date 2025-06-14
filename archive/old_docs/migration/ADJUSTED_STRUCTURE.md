# Adjusted Refactoring Structure

## The Problem
Streamlit has specific expectations:
1. Pages must be in `pages/` directory relative to the main script
2. The main script (APE.py) should be at the root
3. Imports should be simple and not require path manipulation

## Recommended Structure

```
vegf-1/
# STREAMLIT APP (Deployment Core)
├── APE.py                          # Main entry point
├── pages/                          # Streamlit pages (MUST be here)
│   ├── 1_Protocol_Manager.py      # Production pages
│   ├── 2_Simulations.py
│   └── 3_Analysis.py
├── components/                     # UI components
├── core/                          # Simulation engine
├── utils/                         # Application utilities  
├── visualizations/                # Visualization modules
├── protocols/                     # Protocol definitions
├── assets/                        # Static assets
├── simulation_results/            # Results directory
├── .streamlit/                    # Streamlit config
├── requirements.txt               # Production dependencies
└── README.md                      # User documentation

# DEVELOPMENT LAYER
├── dev/                          # All development-only code
│   ├── pages/                    # Debug pages (98_, 99_)
│   ├── experiments/              # Experimental features
│   ├── test_scripts/             # Testing utilities
│   ├── migration/                # Refactoring tools
│   └── benchmarks/               # Performance testing
│
├── literature_extraction/        # Keep existing structure
├── clinical_analysis/           # Analysis tools
├── validation/                  # Scientific validation
├── visualization/              # Central styling (shared)
├── tests/                      # Test suite
├── docs/                       # Documentation
├── meta/                       # Project insights
├── mcp/                       # MCP servers
├── archive/                   # Old implementations
│   ├── streamlit_app/
│   ├── streamlit_app_parquet/
│   └── streamlit_app_v2/      # Archive after extraction
│
├── requirements-dev.txt        # Dev dependencies
├── CLAUDE.md                   # AI instructions
├── pyproject.toml             # Python config
└── .deployment/               # Deployment configs
```

## Key Changes from Original Plan

1. **No `ape/` subdirectory** - Keep app modules at root level
2. **Pages stay in `pages/`** - Required by Streamlit
3. **Debug pages in `dev/pages/`** - Can be run with `streamlit run dev/pages/99_Debug.py`
4. **Simpler imports** - No need for `ape.` prefix everywhere

## Benefits

1. **Streamlit Compatible** - Works with Streamlit's expectations
2. **Clean Deployment** - Just exclude `dev/`, `archive/`, etc.
3. **Simple Imports** - `from components.x import y` works naturally
4. **Developer Friendly** - Debug pages easily accessible

## Migration Steps

1. Move files from `ape/` back to root:
   - `ape/components/` → `components/`
   - `ape/core/` → `core/`
   - etc.

2. Move debug pages to `dev/pages/`:
   - `pages/98_*.py` → `dev/pages/`
   - `pages/99_*.py` → `dev/pages/`

3. Update imports to remove `ape.` prefix

4. Archive `streamlit_app_v2/` after extraction

## Deployment

For deployment, simply exclude:
- `dev/`
- `archive/`
- `literature_extraction/`
- `clinical_analysis/`
- Test files (`test_*.py`, `*_test.py`)
- Development configs (`requirements-dev.txt`, `CLAUDE.md`)

This gives us the same separation but with a cleaner, more Streamlit-friendly structure.