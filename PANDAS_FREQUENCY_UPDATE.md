# Pandas Frequency Alias Updates (2025-01-24)

## Background
Pandas 2.2+ is deprecating single-letter frequency aliases in favor of more explicit ones that indicate the period end.

## Changes Made
Updated all deprecated frequency aliases to their new equivalents:

### Files Updated:
1. **streamlit_app_parquet/staggered_data_processor.py**
   - Line 315: `f'{cohort_months}M'` → `f'{cohort_months}ME'`

2. **streamlit_app/staggered_simulation.py**
   - Line 223: `to_period('Q')` → `to_period('QE')`

### Already Updated (no changes needed):
- `streamlit_app_parquet/staggered_data_processor.py` lines 173, 194: Already using 'ME'
- `streamlit_app_parquet/pages/5_Calendar_Time_Analysis.py` line 124: Already using 'QE'
- `streamlit_app_parquet/staggered_visualizations.py` lines 249, 435: Already using 'QE' and 'ME'

## Frequency Alias Reference
| Old | New | Meaning |
|-----|-----|---------|
| M   | ME  | Month End |
| Q   | QE  | Quarter End |
| Y   | YE  | Year End |
| H   | h   | Hour |
| T   | min | Minute |
| S   | s   | Second |
| L   | ms  | Millisecond |
| U   | us  | Microsecond |
| N   | ns  | Nanosecond |

## Notes
- When using numeric prefixes (e.g., '3M' for 3 months), the new format is '3ME'
- Daily frequency 'D' remains unchanged
- This change ensures compatibility with pandas 3.0+