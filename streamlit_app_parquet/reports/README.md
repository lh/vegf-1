# APE: AMD Protocol Explorer Reports

This directory contains Quarto templates for generating reports from simulation results.

## Contents

- `simulation_report.qmd` - Template for comprehensive simulation reports

## How the Reports Work

Reports are generated using [Quarto](https://quarto.org/), which combines markdown, code, and data to create professional documents. The Streamlit application handles running Quarto with the appropriate parameters.

The general process is:
1. Simulation results are saved as JSON data
2. The Quarto template is rendered with this data as an input parameter
3. The resulting report is made available for download

## Required R Packages

These reports require the following R packages:
- jsonlite - For reading JSON data
- dplyr - For data manipulation
- ggplot2 - For static visualizations
- plotly - For interactive visualizations
- knitr - For report generation
- kableExtra - For enhanced tables

## Adding New Reports

To add a new report template:

1. Create a new `.qmd` file in this directory
2. Use YAML front matter to define parameters:
   ```yaml
   title: "Report Title"
   format: html
   params:
     dataPath: ""
     otherParam: "default value"
   ```
3. Update the app code to use your new template

## Customizing Reports

To customize a report:

1. Edit the `.qmd` file to change content structure
2. Modify the R code chunks to change visualizations and analysis
3. Add/modify parameters as needed for different data inputs

## Testing Report Templates

You can test templates directly with Quarto:

```bash
quarto render simulation_report.qmd --to html -P dataPath=path/to/sample/data.json
```