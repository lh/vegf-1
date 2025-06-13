# Testing Export/Import Features

## How to Test the Export Feature

1. **First, you need a simulation to export:**
   - Run the APE app: `streamlit run APE.py`
   - Go to "Run Simulation" page
   - Run any simulation (can use default settings)
   - Wait for simulation to complete

2. **Once simulation is complete:**
   - Click "View Results" or go to "Analysis Overview"
   - Click on the "Audit Trail" tab (last tab)
   - Scroll down past the audit events
   - You should see the "Export Simulation" section with a "📦 Download Package" button

## How to Test the Import Feature

1. **Go to Protocol Manager:**
   - From the home page, click "Protocol Manager"
   - Scroll down past the protocol selection
   - You should see "📥 Import Simulation Package" expander
   - Click to expand it

2. **Import a package:**
   - Upload a previously exported .zip file
   - Click "Import Simulation"
   - Once imported, you can navigate to Analysis Overview to see the results

## Troubleshooting

- **Export button not showing?** Make sure you have run a simulation first. The export feature only appears when there's simulation data to export.

- **Import section not showing?** The import section should always be visible in Protocol Manager. If not showing, check browser console for errors.

- **File upload errors?** Make sure the file is under 500MB and is a valid APE simulation package (.zip file).