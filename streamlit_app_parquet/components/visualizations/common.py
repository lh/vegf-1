"""
Common utilities for visualizations.

This module provides shared functions used across different visualization methods.
"""

import os
import sys
import subprocess
import tempfile
import logging
import uuid
import time
import hashlib
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
import matplotlib.pyplot as plt
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_r_available() -> bool:
    """Check if R is installed and available.

    Returns
    -------
    bool
        True if R is installed, False otherwise
    """
    try:
        # Try platform-specific command first
        if sys.platform == 'win32':
            cmd = ["where", "Rscript"]
        else:
            cmd = ["which", "Rscript"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        # If command failed, try running Rscript directly
        if result.returncode != 0:
            result = subprocess.run(
                ["Rscript", "--version"],
                capture_output=True,
                text=True,
                check=False
            )

        return result.returncode == 0
    except Exception as e:
        logger.warning(f"Error checking R installation: {e}")
        return False


def check_r_packages() -> bool:
    """Check if required R packages are installed.

    Returns
    -------
    bool
        True if all required packages are installed, False otherwise
    """
    if not is_r_available():
        return False

    required_packages = ["ggplot2", "optparse", "lubridate", "scales", "dplyr", "tidyr"]

    try:
        # Create temporary R script to check packages
        with tempfile.NamedTemporaryFile(suffix=".R", mode="w", delete=False) as f:
            f.write("""
            installed <- rownames(installed.packages())
            required <- c("{}")
            missing <- required[!required %in% installed]
            if (length(missing) > 0) {{
                cat("MISSING:", paste(missing, collapse=", "))
                quit(status=1)
            }} else {{
                cat("OK: All packages installed")
                quit(status=0)
            }}
            """.format('", "'.join(required_packages)))
            check_script = f.name

        # Run the script
        result = subprocess.run(
            ["Rscript", check_script],
            capture_output=True,
            text=True,
            check=False
        )

        # Clean up
        os.unlink(check_script)

        if result.returncode != 0:
            logger.warning(f"Missing R packages: {result.stdout}")
            return False
        else:
            logger.info(f"R packages check: {result.stdout}")
            return True

    except Exception as e:
        logger.warning(f"Error checking R packages: {e}")
        return False


def install_r_packages() -> bool:
    """Install required R packages.

    Returns
    -------
    bool
        True if packages were installed successfully, False otherwise
    """
    if not is_r_available():
        return False

    required_packages = ["ggplot2", "optparse", "lubridate", "scales", "dplyr", "tidyr"]

    try:
        # Create temporary R script to install packages
        with tempfile.NamedTemporaryFile(suffix=".R", mode="w", delete=False) as f:
            f.write("""
            required <- c("{}")
            for (pkg in required) {{
                if (!require(pkg, character.only = TRUE, quietly = TRUE)) {{
                    install.packages(pkg, repos = "https://cran.r-project.org")
                }}
            }}
            installed <- rownames(installed.packages())
            missing <- required[!required %in% installed]
            if (length(missing) > 0) {{
                cat("FAILED TO INSTALL:", paste(missing, collapse=", "))
                quit(status=1)
            }} else {{
                cat("OK: All packages installed")
                quit(status=0)
            }}
            """.format('", "'.join(required_packages)))
            install_script = f.name

        # Run the script
        result = subprocess.run(
            ["Rscript", install_script],
            capture_output=True,
            text=True,
            check=False
        )

        # Clean up
        os.unlink(install_script)

        if result.returncode != 0:
            logger.warning(f"Failed to install R packages: {result.stdout}")
            return False
        else:
            logger.info(f"R packages installation: {result.stdout}")
            return True

    except Exception as e:
        logger.warning(f"Error installing R packages: {e}")
        return False

def get_r_script_path() -> str:
    """Get the path to the R visualization script.

    Returns
    -------
    str
        Path to the R script
    """
    r_script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "r_scripts", "visualization.R")
    return r_script_path

def ensure_r_script_exists() -> bool:
    """Ensure the R visualization script exists, creating it if needed.

    Returns
    -------
    bool
        True if the script exists or was created successfully, False otherwise
    """
    r_script_path = get_r_script_path()

    if os.path.exists(r_script_path):
        logger.info(f"R script already exists at {r_script_path}")
        return True

    try:
        # First, ensure the r_scripts directory exists
        r_scripts_dir = os.path.dirname(r_script_path)
        if not os.path.exists(r_scripts_dir):
            logger.info(f"Creating R scripts directory: {r_scripts_dir}")
            os.makedirs(r_scripts_dir, exist_ok=True)

        # Either import from template file or use a fallback template
        try:
            from streamlit_app.components.visualizations.r_script_template import R_SCRIPT_TEMPLATE
            template = R_SCRIPT_TEMPLATE
            logger.info("Using R script template from r_script_template.py")
        except ImportError:
            # Fallback if template module doesn't exist
            logger.warning("r_script_template.py not found, using fallback template")
            template = '''#!/usr/bin/env Rscript

# R Visualization Script for APE: AMD Protocol Explorer
# This script generates high-quality visualizations using ggplot2

# Check for and install required packages if needed
required_packages <- c("ggplot2", "optparse", "lubridate", "scales", "dplyr", "tidyr")
new_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]
if(length(new_packages)) install.packages(new_packages, repos = "https://cran.r-project.org")

# Load libraries
library(ggplot2)
library(optparse)
library(lubridate)
library(scales)
library(dplyr)
library(tidyr)

# Parse command line arguments
option_list <- list(
  make_option("--data", type="character", help="Path to CSV data file"),
  make_option("--output", type="character", help="Path to save output visualization"),
  make_option("--type", type="character", default="enrollment", help="Type of visualization to create"),
  make_option("--width", type="integer", default=10, help="Width of the output image in inches"),
  make_option("--height", type="integer", default=5, help="Height of the output image in inches"),
  make_option("--dpi", type="integer", default=120, help="Resolution of the output image in DPI"),
  make_option("--theme", type="character", default="tufte", help="Visualization theme (tufte, minimal, classic)")
)

opt <- parse_args(OptionParser(option_list=option_list))

# Create a theme
basic_theme <- function() {
  theme_minimal() +
    theme(
      panel.grid.minor = element_blank(),
      axis.line = element_line(color = "black", size = 0.3)
    )
}

# Function to create enrollment visualization
create_enrollment_visualization <- function(data_path, output_path) {
  # Read data
  data <- read.csv(data_path)

  # Convert enrollment_date to proper date format
  data$enrollment_date <- as.Date(data$enrollment_date)

  # Aggregate by month
  monthly_data <- data %>%
    mutate(month = floor_date(enrollment_date, "month")) %>%
    count(month) %>%
    arrange(month)

  # Create the plot
  p <- ggplot(monthly_data, aes(x = month, y = n)) +
    geom_bar(stat = "identity", fill = "blue", alpha = 0.7) +
    basic_theme() +
    labs(title = "Patient Enrollment Over Time", x = "Month", y = "Number of Patients")

  # Save to file
  ggsave(output_path, plot = p, width = opt$width, height = opt$height, dpi = opt$dpi)
  cat("Visualization saved to:", output_path, "\n")
}

# Function to create va over time visualization
create_va_over_time_visualization <- function(data_path, output_path) {
  # Read data
  data <- read.csv(data_path)

  # Create the plot
  p <- ggplot(data, aes(x = time, y = visual_acuity)) +
    geom_line(color = "blue") +
    basic_theme() +
    labs(title = "Visual Acuity Over Time", x = "Time", y = "Visual Acuity")

  # Save to file
  ggsave(output_path, plot = p, width = opt$width, height = opt$height, dpi = opt$dpi)
  cat("VA visualization saved to:", output_path, "\n")
}

# Function to create dual timeframe visualization
create_dual_timeframe_visualization <- function(data_path, output_path) {
  # Read data and create plot
  data <- read.csv(data_path)

  # Simple dual plot
  p <- ggplot() +
    geom_line(data = data[data$calendar_time > 0,], aes(x = calendar_time, y = calendar_va), color = "blue") +
    geom_line(data = data[data$patient_time > 0,], aes(x = patient_time, y = patient_va), color = "red") +
    basic_theme() +
    labs(title = "Dual Timeframe Analysis", x = "Time", y = "Visual Acuity")

  # Save to file
  ggsave(output_path, plot = p, width = opt$width, height = opt$height, dpi = opt$dpi)
  cat("Dual timeframe visualization saved to:", output_path, "\n")
}

# Main execution
if (is.null(opt$data) || is.null(opt$output)) {
  stop("Data and output paths are required.")
}

# Select visualization based on type
if (opt$type == "enrollment") {
  create_enrollment_visualization(opt$data, opt$output)
} else if (opt$type == "va_over_time") {
  create_va_over_time_visualization(opt$data, opt$output)
} else if (opt$type == "dual_timeframe") {
  create_dual_timeframe_visualization(opt$data, opt$output)
} else {
  stop("Unknown visualization type:", opt$type)
}
'''

        # Create the script
        logger.info(f"Writing R script to {r_script_path}")
        with open(r_script_path, 'w') as f:
            f.write(template)

        # Make executable
        os.chmod(r_script_path, 0o755)

        # Verify the script was created
        if os.path.exists(r_script_path):
            file_size = os.path.getsize(r_script_path)
            logger.info(f"Created R script at {r_script_path} (size: {file_size} bytes)")
            return True
        else:
            logger.error(f"Failed to verify R script creation at {r_script_path}")
            return False
    except Exception as e:
        logger.error(f"Error creating R script: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def create_unique_filename(prefix: str, suffix: str) -> str:
    """Create a unique filename with timestamp and random UUID.
    
    Parameters
    ----------
    prefix : str
        Prefix for the filename
    suffix : str
        Suffix for the filename (file extension)
    
    Returns
    -------
    str
        Unique filename
    """
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_id}{suffix}"

def dataframe_to_temp_csv(data, prefix: str = "viz_data") -> Tuple[str, str]:
    """Save a DataFrame to a temporary CSV file.
    
    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame to save
    prefix : str, optional
        Prefix for the filename, by default "viz_data"
    
    Returns
    -------
    Tuple[str, str]
        Tuple containing (temp_dir_path, csv_file_path)
    """
    temp_dir = tempfile.mkdtemp()
    csv_filename = create_unique_filename(prefix, ".csv")
    csv_path = os.path.join(temp_dir, csv_filename)
    
    data.to_csv(csv_path, index=False)
    logger.info(f"Saved data to temporary CSV: {csv_path}")
    
    return temp_dir, csv_path

class VisualizationTimer:
    """Context manager for timing visualization operations."""
    
    def __init__(self, name: str):
        """Initialize timer.
        
        Parameters
        ----------
        name : str
            Name of the operation being timed
        """
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        """Start the timer."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End the timer and log the elapsed time."""
        elapsed_time = time.time() - self.start_time
        logger.info(f"{self.name} completed in {elapsed_time:.2f} seconds")