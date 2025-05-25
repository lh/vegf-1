# AMD Protocol Explorer V2 - Streamlit Interface

Clean implementation of the AMD Protocol Explorer using the V2 simulation engine with complete parameter traceability.

## Key Features

- **No Hidden Parameters**: Every simulation parameter must be explicitly defined in protocol files
- **Full Audit Trail**: Complete tracking from parameter definition to simulation result
- **Protocol-Driven**: All simulations driven by versioned YAML protocol specifications
- **Clean Architecture**: Built on V2 simulation engine without legacy code

## Quick Start

```bash
# From the project root
cd streamlit_app_v2
streamlit run app.py
```

## Pages

### 1. Protocol Manager 📋
- Browse available protocol files
- View all protocol parameters
- Validate protocol specifications
- Export protocols in different formats

### 2. Run Simulation 🚀
- Select simulation engine (ABS or DES)
- Configure simulation parameters
- Execute simulations with progress tracking
- View immediate results summary

### 3. Analysis Overview 📊
- Vision outcome distributions
- Treatment pattern analysis
- Patient trajectory visualization
- Complete audit trail viewer

## Protocol Files

Protocols are stored in `protocols/v2/` as YAML files. Each protocol must define:

- Treatment timing parameters (intervals, extensions)
- Disease state transition probabilities
- Vision change model for all state/treatment combinations
- Patient population characteristics
- Discontinuation rules

Example: `protocols/v2/eylea_treat_and_extend_v1.0.yaml`

## Architecture

```
streamlit_app_v2/
├── app.py                    # Main application entry
├── pages/                    # Streamlit pages
│   ├── 1_Protocol_Manager.py
│   ├── 2_Run_Simulation.py
│   └── 3_Analysis_Overview.py
├── components/              # Reusable UI components (future)
├── utils/                   # Utility functions (future)
└── requirements.txt         # Python dependencies
```

## Key Differences from V1

1. **No Defaults**: All parameters must be in protocol files
2. **Immutable Protocols**: Protocol specs are frozen after loading
3. **Audit Trail**: Every parameter and decision is logged
4. **Clean Separation**: No mixing of V1 and V2 code
5. **Type Safety**: Strong typing throughout

## Adding New Protocols

1. Create a new YAML file in `protocols/v2/`
2. Include ALL required parameters (no defaults)
3. Validate using Protocol Manager
4. Test with small simulation first

## Future Enhancements

- [ ] Protocol comparison tools
- [ ] Batch simulation runner
- [ ] Advanced visualizations
- [ ] Parameter sensitivity analysis
- [ ] Results export to various formats
- [ ] Protocol library with templates