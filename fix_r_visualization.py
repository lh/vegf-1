#!/usr/bin/env python
"""
Script to fix R visualization issues.

This creates a direct replacement for visualization.R that adds a trend line.
"""

import os
import sys
import tempfile

# Define the new R script with trend lines
R_SCRIPT_TEMPLATE = """#!/usr/bin/env Rscript

# R Visualization Script for APE: AMD Protocol Explorer
# This script generates high-quality visualizations using ggplot2
# following Edward Tufte design principles.

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

# Create a Tufte-inspired theme
theme_tufte_enhanced <- function(base_size = 11, base_family = "") {
  half_line <- base_size / 2
  
  theme_minimal(base_size = base_size, base_family = base_family) +
    theme(
      # Remove most background elements
      panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank(),
      panel.grid.major.y = element_line(color = "#f0f0f0"),
      
      # Minimize axis lines and ticks
      axis.line.x = element_line(color = "black", linewidth = 0.3),
      axis.ticks.x = element_line(color = "black", linewidth = 0.3),
      axis.ticks.length = unit(half_line / 2, "pt"),
      
      # Text elements
      axis.title = element_text(size = rel(0.9), hjust = 0),
      axis.text = element_text(size = rel(0.8)),
      plot.title = element_text(size = rel(1.2), hjust = 0, face = "bold"),
      plot.subtitle = element_text(size = rel(0.9), hjust = 0, color = "grey30"),
      plot.caption = element_text(size = rel(0.7), color = "grey30", hjust = 1),
      
      # Margins
      plot.margin = margin(half_line, half_line, half_line, half_line),
      
      # Legend
      legend.background = element_blank(),
      legend.key = element_blank(),
      legend.position = "top"
    )
}

# Function to create enrollment visualization
create_enrollment_visualization <- function(data_path, output_path) {
  # Read data
  print(paste("Reading data from:", data_path))
  if (!file.exists(data_path)) {
    stop(paste("Data file not found:", data_path))
  }
  
  data <- read.csv(data_path)
  
  # Print data structure for debugging
  print(paste("Data loaded with", nrow(data), "rows"))
  print("Columns in data:")
  print(names(data))
  
  # Convert enrollment_date to proper date format
  if (!"enrollment_date" %in% names(data)) {
    stop("Required column 'enrollment_date' not found in data")
  }
  
  # Ensure enrollment_date is in proper format
  data$enrollment_date <- as.Date(data$enrollment_date)
  
  # Aggregate by month
  monthly_data <- data %>%
    mutate(month = floor_date(enrollment_date, "month")) %>%
    count(month) %>%
    arrange(month)
  
  print(paste("Aggregated data has", nrow(monthly_data), "rows"))
  
  # Create the plot with enhanced Tufte-inspired design and trend line
  p <- ggplot(monthly_data, aes(x = month, y = n)) +
    # Add bars for month counts
    geom_bar(stat = "identity", fill = "#4682B4", alpha = 0.7) +
    # Add a clear trend line (red)
    geom_smooth(method = "loess", color = "#B22222", linewidth = 1.2, se = FALSE) +
    # Use enhanced Tufte theme
    theme_tufte_enhanced(base_size = 14) +
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
  
  # Save to file using ggsave
  print(paste("Saving plot to:", output_path))
  ggsave(output_path, plot = p, width = opt$width, height = opt$height, dpi = opt$dpi)
  
  print(paste("Visualization saved successfully to:", output_path))
  
  # Check if the file was created successfully
  if (file.exists(output_path)) {
    file_info <- file.info(output_path)
    print(paste("File created with size:", file_info$size, "bytes"))
  } else {
    warning("File was not created successfully")
  }
}

# Function to create visual acuity over time visualization
create_va_over_time_visualization <- function(data_path, output_path) {
  # Read data
  data <- read.csv(data_path)
  
  # Check data structure
  print(paste("Data loaded with", nrow(data), "rows"))
  print("Columns in data:")
  print(names(data))
  
  # Convert date/time to proper format if needed
  if ("time" %in% colnames(data)) {
    data$time <- as.numeric(data$time)
  }
  
  # Create the plot with trend line
  p <- ggplot(data, aes(x = time, y = visual_acuity)) +
    # Add data points with transparency
    geom_point(color = "#4682B4", size = 2, alpha = 0.6) +
    # Add a line connecting the points
    geom_line(color = "#4682B4", linewidth = 0.8) +
    # Add a smoothed trend line with confidence interval
    geom_smooth(method = "loess", color = "#B22222", linewidth = 1.2, se = TRUE, alpha = 0.2) +
    # Add a horizontal reference line for baseline
    geom_hline(yintercept = mean(data$visual_acuity[1:3], na.rm = TRUE), 
               linetype = "dashed", color = "#555555", alpha = 0.5) +
    # Use enhanced Tufte theme
    theme_tufte_enhanced(base_size = 14) +
    # Labels
    labs(
      title = "Mean Visual Acuity Over Time",
      subtitle = "Change in visual acuity throughout simulation period",
      x = "Time (weeks)",
      y = "Visual Acuity",
      caption = "Data source: AMD Protocol Explorer"
    )
  
  # Save to file
  ggsave(output_path, plot = p, width = opt$width, height = opt$height, dpi = opt$dpi)
  
  print(paste("VA visualization saved to:", output_path))
}

# Function to create dual timeframe visualization
create_dual_timeframe_visualization <- function(data_path, output_path) {
  # Read data
  data <- read.csv(data_path)
  
  # Check if we have both calendar and patient time data
  has_calendar_time <- "calendar_time" %in% colnames(data) && "calendar_va" %in% colnames(data)
  has_patient_time <- "patient_time" %in% colnames(data) && "patient_va" %in% colnames(data)
  
  if (!has_calendar_time || !has_patient_time) {
    stop("Data must include both calendar_time/calendar_va and patient_time/patient_va columns")
  }
  
  # Reshape data to long format
  long_data <- data %>%
    pivot_longer(
      cols = c(calendar_va, patient_va),
      names_to = "metric_type",
      values_to = "visual_acuity"
    ) %>%
    mutate(
      time = if_else(metric_type == "calendar_va", calendar_time, patient_time),
      time_type = if_else(metric_type == "calendar_va", "Calendar Time (months)", "Patient Time (weeks)")
    )
  
  # Create the plot with enhanced design
  p <- ggplot(long_data, aes(x = time, y = visual_acuity, color = time_type)) +
    # Add data points
    geom_point(size = 2, alpha = 0.6) +
    # Add connecting lines
    geom_line(linewidth = 0.8) +
    # Add smooth trend lines with confidence intervals
    geom_smooth(method = "loess", linewidth = 1.2, se = TRUE, alpha = 0.2) +
    facet_wrap(~ time_type, scales = "free_x") +
    theme_tufte_enhanced(base_size = 14) +
    scale_color_manual(values = c("Calendar Time (months)" = "#4682B4", "Patient Time (weeks)" = "#6A5ACD")) +
    # Labels
    labs(
      title = "Visual Acuity by Calendar vs. Patient Time",
      subtitle = "Comparing time reference frames for acuity progression",
      y = "Visual Acuity",
      caption = "Data source: AMD Protocol Explorer"
    ) +
    theme(
      strip.background = element_blank(),
      strip.text = element_text(face = "bold"),
      legend.position = "none"
    )
  
  # Save to file
  ggsave(output_path, plot = p, width = opt$width, height = opt$height, dpi = opt$dpi)
  
  print(paste("Dual timeframe visualization saved to:", output_path))
}

# Function to create discontinuation plot
create_discontinuation_plot <- function(data_path, output_path) {
  # Read data
  data <- read.csv(data_path)
  
  # Check required columns
  required_cols <- c("time", "count", "type")
  if (!all(required_cols %in% colnames(data))) {
    stop("Data must include time, count, and type columns")
  }
  
  # Create the plot with enhanced design
  p <- ggplot(data, aes(x = time, y = count, fill = type)) +
    geom_bar(stat = "identity", position = "stack", alpha = 0.8) +
    theme_tufte_enhanced(base_size = 14) +
    scale_fill_brewer(palette = "Blues", direction = -1) +
    # Labels
    labs(
      title = "Discontinuations by Type Over Time",
      subtitle = "Distribution of discontinuation types throughout simulation",
      x = "Time (weeks)",
      y = "Count",
      fill = "Discontinuation Type",
      caption = "Data source: AMD Protocol Explorer"
    )
  
  # Save to file
  ggsave(output_path, plot = p, width = opt$width, height = opt$height, dpi = opt$dpi)
  
  print(paste("Discontinuation plot saved to:", output_path))
}

# Main execution
# Debug print of parameters
cat("=== R VISUALIZATION PARAMETERS ===\\n")
cat("Input data file: ", opt$data, "\\n")
cat("Output file: ", opt$output, "\\n")
cat("Visualization type: ", opt$type, "\\n")
cat("Checking if input file exists: ", file.exists(opt$data), "\\n")
cat("==================================\\n")

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
} else if (opt$type == "discontinuation") {
  create_discontinuation_plot(opt$data, opt$output)
} else {
  stop("Unknown visualization type:", opt$type)
}
"""

def main():
    """Update the R visualization script with enhancements."""
    print("Fixing R visualization script...")
    
    # Determine the path to visualization.R
    script_dir = os.path.dirname(os.path.abspath(__file__))
    r_script_path = os.path.join(script_dir, "streamlit_app", "r_scripts", "visualization.R")
    
    print(f"Original R script path: {r_script_path}")
    
    # Create backup of the original script
    backup_path = r_script_path + ".bak"
    try:
        if os.path.exists(r_script_path):
            import shutil
            shutil.copy2(r_script_path, backup_path)
            print(f"Created backup at: {backup_path}")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")
    
    # Write the new script
    print(f"Writing enhanced R script to: {r_script_path}")
    try:
        # Create r_scripts directory if it doesn't exist
        os.makedirs(os.path.dirname(r_script_path), exist_ok=True)
        
        # Write the new script
        with open(r_script_path, 'w') as f:
            f.write(R_SCRIPT_TEMPLATE)
        
        # Make the script executable
        os.chmod(r_script_path, 0o755)
        
        print(f"Successfully wrote enhanced R script ({os.path.getsize(r_script_path)} bytes)")
    except Exception as e:
        print(f"Error writing R script: {e}")
        return
    
    # Create a direct test data file
    print("Creating test data file...")
    try:
        temp_dir = tempfile.gettempdir()
        test_data_path = os.path.join(temp_dir, "test_enrollment_data.csv")
        
        # Simple CSV data
        csv_data = "patient_id,enrollment_date\n"
        import datetime
        start_date = datetime.date(2023, 1, 1)
        for i in range(1, 366):
            date = start_date + datetime.timedelta(days=i-1)
            csv_data += f"{i},{date}\n"
        
        with open(test_data_path, 'w') as f:
            f.write(csv_data)
        
        print(f"Created test data file at: {test_data_path}")
        
        # Test output path
        test_output_path = os.path.join(temp_dir, "test_enrollment_viz.png")
        
        # Run the R script directly
        print("Testing R script...")
        import subprocess
        cmd = [
            "Rscript", r_script_path,
            f"--data={test_data_path}",
            f"--output={test_output_path}",
            "--type=enrollment",
            "--width=10",
            "--height=5",
            "--dpi=120"
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"Command completed with return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if os.path.exists(test_output_path):
            file_size = os.path.getsize(test_output_path)
            print(f"Test visualization created: {test_output_path} ({file_size} bytes)")
            print("Test SUCCESSFUL - R script is working properly with trend line!")
        else:
            print(f"Test FAILED - Output file was not created: {test_output_path}")
    
    except Exception as e:
        print(f"Error testing R script: {e}")
    
    print("\nTo use the enhanced visualizations:")
    print("1. Restart your Streamlit application")
    print("2. Navigate to the Staggered Simulation page")
    print("3. Run a simulation to see the enhanced visualizations with trend lines")
    print(f"\nIf you encounter any issues, the original script is backed up at: {backup_path}")

if __name__ == "__main__":
    main()