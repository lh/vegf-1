# APE Application Components Analysis

## Overview
Based on analysis of the codebase, there are three distinct systems that should be separated:

1. **Core APE Simulation Application** (for deployment)
2. **Real Clinical Data Analysis Tools** (separate repository candidate)  
3. **Literature Parameter Extraction Tools** (development/research tools)

## 1. Core APE Components (For Deployment)

### Essential Application Files
```
streamlit_app_v2/
├── APE.py                          # Main application
├── requirements.txt                # Dependencies
├── .streamlit/                     # Streamlit config
│
├── pages/                          # Core application pages
│   ├── 1_Protocol_Manager.py       # Protocol configuration
│   ├── 2_Run_Simulation.py         # Run simulations
│   ├── 3_Analysis.py               # Calendar-time analysis
│   └── 4_Patient_Explorer.py       # Individual patient analysis
│
├── core/                          # Simulation engine
│   ├── abs_simulation.py          # Agent-based simulation
│   ├── des_simulation.py          # Discrete event simulation
│   ├── patient.py                 # Patient model
│   ├── protocol.py                # Protocol handling
│   └── state_machine.py           # State transitions
│
├── components/                    # UI components
│   ├── treatment_patterns/        # Treatment analysis
│   ├── economics/                 # Economic analysis
│   └── ui_elements/               # Common UI elements
│
├── utils/                         # Core utilities
│   ├── chart_builder.py           # Visualization framework
│   ├── style_constants.py         # Styling system
│   ├── session_state.py           # Session management
│   └── visualization_modes.py     # Display modes
│
├── visualizations/                # Visualization modules
│   ├── streamgraph_treatment_states.py
│   ├── streamgraph_comprehensive.py
│   └── economic_charts.py
│
├── protocols/v2/                  # YAML protocol definitions
│   ├── aflibercept_pro.yaml
│   ├── aflibercept_te.yaml
│   └── ...
│
└── simulation_results/            # Results storage pattern
```

### Shared Dependencies (at root)
```
visualization/
└── color_system.py               # Central color system

validation/                       # Scientific validation
├── verify_fixed_discontinuation.py
├── verify_streamlit_integration.py
└── ...
```

## 2. Real Clinical Data Analysis (Separate Repository Candidate)

### Analysis Tools for Real-World Data
```
analysis/                         # Clinical data analysis
├── eylea_data_analysis.py       # Real-world data analysis
├── eylea_intervals_analysis.py  # Treatment interval analysis
├── analyze_covid_gap_consequences.py
├── analyze_inappropriate_discontinuations.py
├── identify_premature_discontinuations.py
├── patient_outcomes.py
├── visualize_long_gap_*.py      # Gap analysis visualizations
└── visualize_va_*.py            # Vision analysis tools

# Root-level analysis scripts
analyze_des_patients.py
analyze_discontinuation_flags.py
analyze_existing_simulation.py
analyze_high_va_patients.py
analyze_streamgraph_data.py
analyze_visits.py

# Real data inspection tools
streamlit_app_parquet/inspect_real_data.py
streamlit_app/inspect_real_data.py
test_real_data_streamgraph.py
```

### Why Separate Repository?
- Different data security requirements (PHI/PII concerns)
- Different deployment model (likely on-premises)
- Different user base (clinicians/researchers vs modelers)
- Different compliance requirements
- Could be proprietary while simulation remains open

## 3. Literature & Parameter Extraction (Development Tools)

### Literature Data Extraction
```
# Submodules with copyright-sensitive data
aflibercept_2mg_data/
├── extract_aflibercept_2mg_data.py
└── [PDF extraction tools]

eylea_high_dose_data/
├── extract_pdf_data.py
├── extract_appendix_text.py
├── analyze_extracted_text.py
├── detailed_data_extraction.py
├── extract_with_docling*.py
├── practical_simulation_parameters.py
└── mcp-pdf-extraction-server-fork/

vegf_literature_data/
└── [Literature PDFs and extraction]

# Root extraction scripts
extract_literature_data.py        # Main literature extraction
extract_baseline_va.py           # VA parameter extraction
extract_initial_va.py
extract_above_threshold*.py
extract_discontinuation_criteria.py
protocol_parameters.py           # Parameter compilation

# Parameter estimation
analysis/parameter_estimation.py  # Statistical parameter fitting
```

### Development/Research Tools (Keep in Main Repo)
```
streamlit_app_v2/
├── experiments/                 # Experimental features
├── tests/                      # Test infrastructure
└── scripts/                    # Development scripts

# Debug and development pages
streamlit_app_v2/pages/98_debug_calendar_time.py
streamlit_app_v2/pages/99_Debug_Economics.py
```

## Recommended Repository Structure

### 1. Main Repository (vegf-1) - For Deployment
```
vegf-1/
├── APE.py                      # Lifted from streamlit_app_v2
├── pages/
├── core/
├── components/
├── utils/
├── visualizations/
├── protocols/
├── visualization/              # Shared with other repos
├── validation/
└── docs/
```

### 2. Clinical Analysis Repository (vegf-clinical-analysis)
```
vegf-clinical-analysis/
├── analysis/                   # Move from main repo
├── data_loaders/
├── visualization/              # Import from main repo
├── reports/
└── notebooks/
```

### 3. Keep in Main Repository (Development Only)
```
vegf-1/
├── literature_extraction/      # Organize extraction tools
│   ├── aflibercept_2mg_data/ # Submodule
│   ├── eylea_high_dose_data/ # Submodule
│   ├── vegf_literature_data/  # Submodule
│   └── scripts/               # Extraction scripts
├── development/               # Development-only tools
│   ├── experiments/
│   ├── parameter_estimation/
│   └── debug_pages/
└── archive/                   # Historical code
```

## Deployment Exclusions

When creating deployment branch, exclude:
- `/archive/`
- `/literature_extraction/`
- `/development/`
- `/analysis/` (if not moved to separate repo)
- Any `*debug*.py` files
- Test data files
- Experiment pages

## Benefits of This Separation

1. **Cleaner deployment** - Only simulation platform in production
2. **Better security** - Real data tools can have stricter access
3. **Focused development** - Each tool has clear purpose
4. **Easier compliance** - Different requirements per repository
5. **Flexible licensing** - Can have different licenses per component