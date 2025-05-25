# ⚠️ DEPRECATED - Version 1 (Reference Only)

This is the original V1 Streamlit application. It has been superseded by `streamlit_app_v2/`.

## Status: MOTHBALLED
- **Do not use for new development**
- **Kept for reference only** - some visualizations were particularly nice
- **See `streamlit_app_v2/` for the current system**

## Why V1 was Deprecated
- Hardcoded parameters throughout
- No protocol specification system  
- Mixed FOV/TOM representations
- Fallback behaviors that undermined design principles
- Difficult to maintain and extend

## Notable V1 Features (for reference)
- Streamgraph visualizations
- Patient state tracking charts
- Calendar time analysis
- Various visualization experiments

## Migration
All functionality has been reimplemented in V2 with:
- Test-driven development
- Clean separation of concerns
- Protocol specification system
- No hardcoded parameters
- Consistent styling via ChartBuilder
- Dual visualization modes (Presentation/Analysis)

**For all new work, use `streamlit_app_v2/`**