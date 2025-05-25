"""
Visualization components for the APE Streamlit application.

This module provides functions for creating and displaying various
visualizations including R-based and matplotlib-based options.
"""

import os
import sys
import uuid
import tempfile
import subprocess
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from pathlib import Path
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_r_installation():
    """Check if R is installed and available.
    
    Returns
    -------
    bool
        True if R is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["which", "R"],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except Exception as e:
        logger.warning(f"Error checking R installation: {e}")
        return False

def create_enrollment_visualization_matplotlib(enrollment_df, title="Patient Enrollment by Month"):
    """Create a matplotlib visualization of patient enrollment.
    
    Parameters
    ----------
    enrollment_df : pandas.DataFrame
        DataFrame with patient enrollment data
    title : str, optional
        Title for the visualization, by default "Patient Enrollment by Month"
    
    Returns
    -------
    matplotlib.figure.Figure
        Matplotlib figure object
    """
    try:
        # Group by month
        enrollment_df['month'] = enrollment_df['enrollment_date'].dt.strftime('%Y-%m')
        monthly_counts = enrollment_df['month'].value_counts().sort_index()
        
        # Create a small figure
        fig, ax = plt.subplots(figsize=(8, 4), dpi=80)
        
        # Simple bar chart
        ax.bar(range(len(monthly_counts)), monthly_counts.values, color='#4682B4')
        
        # Clean up the appearance
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Set labels and title
        ax.set_title(title, fontsize=12)
        ax.set_ylabel('Patients')
        
        # X-axis labels
        ax.set_xticks(range(len(monthly_counts)))
        ax.set_xticklabels(monthly_counts.index, rotation=45, ha='right')
        
        plt.tight_layout()
        return fig
    except Exception as e:
        logger.error(f"Error creating matplotlib visualization: {e}")
        # Create a simple error figure
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, f"Error creating visualization: {e}", 
                ha='center', va='center', transform=ax.transAxes)
        return fig

def render_enrollment_visualization(enrollment_df):
    """Render patient enrollment visualization using both matplotlib and R.
    
    This function first shows a matplotlib visualization immediately,
    then attempts to replace it with a higher-quality R visualization
    if R is available. This provides a responsive experience with
    progressive enhancement.
    
    Parameters
    ----------
    enrollment_df : pandas.DataFrame
        DataFrame with 'patient_id' and 'enrollment_date' columns
    """
    # First, create placeholder for the visualization
    viz_placeholder = st.empty()
    
    # Immediately show matplotlib visualization
    fig = create_enrollment_visualization_matplotlib(enrollment_df)
    viz_placeholder.pyplot(fig)
    plt.close(fig)
    
    # Now try to create R visualization in the background
    try:
        # Check if R is installed
        if not check_r_installation():
            logger.warning("R is not installed, using matplotlib visualization only")
            return
            
        # Create a unique temp file for the R data and output
        unique_id = str(uuid.uuid4())[:8]
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = os.path.join(temp_dir, f"enrollment_data_{unique_id}.csv")
            output_path = os.path.join(temp_dir, f"enrollment_plot_{unique_id}.png")
            
            # Save data to CSV
            enrollment_df.to_csv(csv_path, index=False)
            
            # Determine R script path
            r_script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "r_visualization.R")
            
            # Create the R script if it doesn't exist
            if not os.path.exists(r_script_path):
                logger.info(f"Creating R script at {r_script_path}")
                create_r_visualization_script(r_script_path)
            
            # Run R script to create visualization
            r_command = [
                "Rscript", r_script_path, 
                "--data", csv_path,
                "--output", output_path,
                "--type", "enrollment"
            ]
            
            logger.info(f"Running R command: {' '.join(r_command)}")
            result = subprocess.run(
                r_command,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check if R script executed successfully
            if result.returncode == 0 and os.path.exists(output_path):
                # Replace the matplotlib visualization with R visualization
                logger.info(f"R visualization created successfully at {output_path}")
                viz_placeholder.image(output_path)
            else:
                logger.error(f"Error running R script: {result.stderr}")
                # Keep the matplotlib visualization
    except Exception as e:
        logger.error(f"Error creating R visualization: {e}")
        # Keep the matplotlib visualization

def create_r_visualization_script(output_path):
    """Create the R visualization script.
    
    Parameters
    ----------
    output_path : str
        Path to save the R script
    """
    r_script = """#!/usr/bin/env Rscript

# Check for and install required packages if needed
required_packages <- c("ggplot2", "optparse", "lubridate", "scales", "dplyr")
new_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]
if(length(new_packages)) install.packages(new_packages, repos = "https://cran.r-project.org")

# Load libraries
library(ggplot2)
library(optparse)
library(lubridate)
library(scales)
library(dplyr)

# Parse command line arguments
option_list <- list(
  make_option("--data", type="character", help="Path to CSV data file"),
  make_option("--output", type="character", help="Path to save output visualization"),
  make_option("--type", type="character", default="enrollment", help="Type of visualization to create")
)

opt <- parse_args(OptionParser(option_list=option_list))

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
  
  # Create the plot with Tufte-inspired design
  p <- ggplot(monthly_data, aes(x = month, y = n)) +
    geom_bar(stat = "identity", fill = "#4682B4", alpha = 0.8) +
    # Remove unnecessary chart junk
    theme_minimal() +
    theme(
      panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank(),
      panel.grid.major.y = element_line(color = "#f0f0f0"),
      axis.line.x = element_line(color = "black", size = 0.3),
      axis.ticks.x = element_line(color = "black", size = 0.3),
      axis.title = element_text(size = 11),
      axis.text = element_text(size = 10),
      plot.title = element_text(size = 14, hjust = 0),
      plot.subtitle = element_text(size = 11, hjust = 0, color = "grey30"),
      plot.caption = element_text(size = 9, color = "grey30", hjust = 1)
    ) +
    # Labels
    labs(
      title = "Patient Enrollment Over Time",
      subtitle = paste0("Total of ", nrow(data), " patients enrolled"),
      x = "Month",
      y = "Number of Patients",
      caption = "Data source: Staggered enrollment simulation"
    ) +
    # Format x-axis
    scale_x_date(
      date_breaks = "1 month",
      date_labels = "%b %Y",
      expand = expansion(mult = c(0.02, 0.02))
    )
  
  # Save to file using direct device rather than Cairo
  ggsave(output_path, plot = p, width = 10, height = 5, dpi = 120)
  
  cat("Visualization saved to:", output_path, "\n")
}

# Main execution
if (is.null(opt$data) || is.null(opt$output)) {
  stop("Data and output paths are required.")
}

if (opt$type == "enrollment") {
  create_enrollment_visualization(opt$data, opt$output)
} else {
  stop("Unknown visualization type:", opt$type)
}
"""
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write the script
    with open(output_path, 'w') as f:
        f.write(r_script)
    
    # Make executable
    os.chmod(output_path, 0o755)

def create_dual_timeframe_visualizations(results, output_dir):
    """Create visualizations that compare calendar time vs. patient time.
    
    Parameters
    ----------
    results : dict
        Simulation results dictionary
    output_dir : str
        Directory to save visualizations
    
    Returns
    -------
    dict
        Dictionary of visualization paths
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize visualization paths
    viz_paths = {}
    
    try:
        # Extract data for visualization
        if "calendar_time_va" in results and "patient_time_va" in results:
            # Create matplotlib dual timeframe visualization
            calendar_data = results["calendar_time_va"]
            patient_data = results["patient_time_va"]
            
            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=100)
            
            # Calendar time plot
            ax1.plot(
                [point["month"] for point in calendar_data], 
                [point["mean_va"] for point in calendar_data], 
                marker='o', color='#4682B4', linewidth=2
            )
            ax1.set_title("Mean VA by Calendar Time")
            ax1.set_xlabel("Months Since Simulation Start")
            ax1.set_ylabel("Mean Visual Acuity")
            ax1.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Patient time plot
            ax2.plot(
                [point["week"] for point in patient_data], 
                [point["mean_va"] for point in patient_data], 
                marker='o', color='#6A5ACD', linewidth=2
            )
            ax2.set_title("Mean VA by Patient Time")
            ax2.set_xlabel("Weeks Since Patient Enrollment")
            ax2.set_ylabel("Mean Visual Acuity")
            ax2.grid(axis='y', linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            
            # Save figure
            dual_path = os.path.join(output_dir, "dual_timeframe.png")
            plt.savefig(dual_path, dpi=100, bbox_inches='tight')
            plt.close(fig)
            
            viz_paths["dual_timeframe"] = dual_path
            
            # Create patient time visualization with sample sizes
            if "sample_sizes" in patient_data[0]:
                fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
                
                # Line for mean VA
                line = ax.plot(
                    [point["week"] for point in patient_data],
                    [point["mean_va"] for point in patient_data],
                    marker='o', color='#4682B4', linewidth=2,
                    label="Mean Visual Acuity"
                )
                
                # Bar chart for sample sizes
                ax2 = ax.twinx()
                bars = ax2.bar(
                    [point["week"] for point in patient_data],
                    [point["sample_size"] for point in patient_data],
                    alpha=0.3, color='#6A5ACD'
                )
                
                # Set labels and title
                ax.set_xlabel("Weeks Since Patient Enrollment")
                ax.set_ylabel("Mean Visual Acuity")
                ax2.set_ylabel("Sample Size")
                ax.set_title("Mean Visual Acuity by Patient Time")
                
                # Add grid
                ax.grid(axis='y', linestyle='--', alpha=0.3)
                
                # Add legend
                ax.legend(loc='upper left')
                
                plt.tight_layout()
                
                # Save figure
                patient_time_path = os.path.join(output_dir, "patient_time.png")
                plt.savefig(patient_time_path, dpi=100, bbox_inches='tight')
                plt.close(fig)
                
                viz_paths["patient_time"] = patient_time_path
    except Exception as e:
        logger.error(f"Error creating dual timeframe visualizations: {e}")
    
    return viz_paths