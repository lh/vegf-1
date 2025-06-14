# Pandas Frequency Alias Updates (2025-01-24)

## Background
Pandas 2.2+ has different requirements for frequency aliases depending on the function used.

## Important Distinction
- **For `to_period()`**: Use OLD format ('M', 'Q', 'Y')
- **For `resample()`, `pd.Grouper()`, `date_range()`**: Use NEW format ('ME', 'QE', 'YE')

## Current State
After investigation, the correct usage is:

### Functions using OLD format:
- `dt.to_period('M')` - for monthly periods
- `dt.to_period('Q')` - for quarterly periods
- `dt.to_period('3M')` - for 3-month periods

### Functions using NEW format:
- `resample('ME')` - for month end resampling
- `resample('QE')` - for quarter end resampling
- `pd.Grouper(freq='ME')` - for month end grouping
- `pd.date_range(freq='ME')` - for month end date ranges

## Files Status:
1. **streamlit_app_parquet/staggered_data_processor.py**
   - Lines 173, 194, 315: Using 'M' with to_period() ✓

2. **streamlit_app_parquet/pages/5_Calendar_Time_Analysis.py**
   - Line 124: Using 'QE' with resample() ✓

3. **streamlit_app_parquet/staggered_visualizations.py**
   - Line 249: Using 'QE' with to_period() (needs 'Q')
   - Line 435: Using 'ME' with pd.Grouper() ✓

4. **streamlit_app/staggered_simulation.py**
   - Line 223: Using 'Q' with to_period() ✓

## Frequency Alias Reference
| Function | Old | New | Meaning |
|----------|-----|-----|---------|
| to_period() | M | M | Month |
| resample() | M | ME | Month End |
| pd.Grouper() | M | ME | Month End |
| date_range() | M | ME | Month End |

## Notes
- The warnings about 'M' being deprecated apply to resample/Grouper/date_range, NOT to_period()
- This is confusing but appears to be the current pandas behavior
- Monitor pandas updates as this may change in future versions