# APE: AMD Protocol Explorer Deployment Guide

This guide provides instructions for deploying the APE dashboard to Streamlit Cloud and running it locally.

## Local Deployment

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git (to clone the repository)

### Steps

1. Clone the repository:
   ```bash
   git clone [your-repository-url]
   cd [repository-directory]
   ```

2. Install dependencies:
   ```bash
   pip install -r streamlit_requirements.txt
   ```

3. Run the setup script:
   ```bash
   python setup_streamlit.py
   ```

4. Launch the application:
   ```bash
   python run_ape.py
   ```
   
   Alternatively, you can run it directly with Streamlit:
   ```bash
   streamlit run streamlit_app/app.py
   ```

5. The dashboard will be available at http://localhost:8502 by default.

## Streamlit Cloud Deployment

### Prerequisites

- GitHub account
- Repository containing the APE code
- Streamlit Cloud account (sign up at https://streamlit.io/cloud)

### Steps

1. Push your code to a GitHub repository.

2. Log in to Streamlit Cloud (https://share.streamlit.io/).

3. Click "New app" and connect to your GitHub repository.

4. Configure the app:
   - Set the repository: Your GitHub repository URL
   - Set the branch: `main` (or your preferred branch)
   - Set the main file path: `run_ape.py`
   - Advanced settings:
     - Python version: 3.9 or higher
     - Packages: Leave blank as requirements will be read from the requirements.txt file

5. Click "Deploy" and wait for the app to build and deploy.

6. Your app will be available at a URL like: `https://[your-app-name].streamlit.app`

### Troubleshooting Cloud Deployment

1. **Missing Packages**: If deployment fails due to missing packages, check the Streamlit Cloud logs and update the requirements.txt file accordingly.

2. **Quarto Integration**: Quarto is automatically installed in the Streamlit Cloud environment. If you encounter issues:
   - Check the logs for installation errors
   - Make sure the `quarto_utils.py` file is correctly detecting the Streamlit Cloud environment
   - You may need to adjust the Quarto version in the installation script if a newer version is required

3. **R Package Issues**: If R packages fail to install:
   - Ensure the requirements.txt file includes r-base
   - Check if the CRAN mirror settings in `quarto_utils.py` are working correctly
   - You may need to add specific R packages to the requirements.txt file

## Environment Variables

You can customize the app behavior using environment variables:

1. **Local Development**: Set environment variables in your shell or add a `.streamlit/secrets.toml` file.

2. **Streamlit Cloud**: Set them in the Streamlit Cloud dashboard under "Advanced settings" > "Secrets".

Available environment variables:

- `APE_DEFAULT_SIMULATION`: Set the default simulation configuration name
- `APE_ENABLE_DEBUG`: Set to "true" to enable debug information
- `IS_STREAMLIT_CLOUD`: Set to "true" to force Streamlit Cloud environment detection

## External Integrations

### R and Quarto

For report generation functionality to work:

1. **Local Development**:
   - Install R: https://cran.r-project.org/
   - Install Quarto: https://quarto.org/docs/get-started/
   - Install required R packages: `install.packages(c("jsonlite", "dplyr", "ggplot2", "knitr", "kableExtra", "plotly"))`

2. **Streamlit Cloud**: 
   - R and required packages are automatically installed
   - Quarto is automatically installed at runtime
   - No manual setup required