# ⚠️ DEPRECATED - Version 1 Parquet Migration (Reference Only)

This was the Parquet migration attempt of V1. It has been superseded by `streamlit_app_v2/`.

## Status: MOTHBALLED
- **Do not use for new development**
- **Kept for reference only** - Parquet integration patterns
- **See `streamlit_app_v2/` for the current system**

## What This Was
An attempt to migrate V1 to use Parquet files for better performance with large simulations.
While the Parquet integration worked, the underlying V1 issues remained.

## Why Deprecated
Same issues as V1 plus:
- Built on flawed V1 foundation
- Migration increased complexity without fixing core issues
- V2 implements Parquet support from the ground up

## V2 Approach
V2 will implement Parquet support properly when needed, with:
- Clean data model from the start
- Proper serialization layer
- No retrofitting required

**For all new work, use `streamlit_app_v2/`**