#!/usr/bin/env Rscript

# R script for creating beautiful enrollment visualizations
# This can be called from Python using the subprocess module

# Remove dependency on Cairo which requires X11
library(ggplot2)
library(lubridate)
library(dplyr)
# library(Cairo)  # Removed - requires X11 which may not be available
library(viridis) # For better color palettes
library(scales) # For nice scales

# Function to create enrollment plot from data
create_enrollment_plot <- function(data_file, output_file, width = 8, height = 5) {
  # Read the enrollment data 
  enrollment_data <- read.csv(data_file)
  
  # Convert dates to proper format
  enrollment_data$enrollment_date <- as.Date(enrollment_data$enrollment_date)
  
  # Create monthly data for visualization
  monthly_data <- enrollment_data %>%
    mutate(month = floor_date(enrollment_date, "month")) %>%
    count(month) %>%
    arrange(month)
    
  # Ensure we have the min and max dates
  date_range <- range(monthly_data$month)
  
  # Calculate total patient count
  total_patients <- sum(monthly_data$n)
  
  # Create a beautiful Tufte-inspired plot
  ggplot(monthly_data, aes(x = month, y = n)) +
    # Main bars for monthly enrollment
    geom_bar(stat = "identity", fill = "#4682B4", alpha = 0.8, width = 25) +

    # Remove redundant data points on top of bars
    # geom_point(size = 2, color = "#333333") +
    
    # Add smooth trend line
    geom_smooth(se = FALSE, color = "#E41A1C", size = 0.8, alpha = 0.7, method = "loess") +
    
    # Clean, minimal theme inspired by Tufte
    theme_minimal() +
    theme(
      panel.grid.major.x = element_blank(),
      panel.grid.minor.x = element_blank(),
      panel.grid.minor.y = element_blank(),
      panel.grid.major.y = element_line(color = "gray90"),
      axis.line.x = element_line(color = "gray70"),
      plot.title = element_text(hjust = 0, size = 14, face = "bold"),
      plot.subtitle = element_text(hjust = 0, size = 11, color = "gray30"),
      plot.caption = element_text(hjust = 1, size = 9, color = "gray50"),
      axis.title = element_text(size = 10, color = "gray30"),
      axis.text = element_text(size = 9),
      plot.background = element_rect(fill = "white", color = NA)
    ) +
    
    # Readable labels
    labs(
      title = "Patient Enrollment by Month",
      subtitle = paste0("Total Enrollment: ", total_patients, " patients"),
      x = NULL,
      y = "Patients Enrolled",
      caption = paste0("Period: ", format(min(monthly_data$month), "%b %Y"), " - ", 
                       format(max(monthly_data$month), "%b %Y"))
    ) +
    
    # X-axis with cleaner date format
    scale_x_date(
      date_breaks = "2 months",
      date_labels = "%b '%y",
      expand = c(0.01, 0.01)
    ) +
    
    # Y-axis with human-readable values
    scale_y_continuous(
      breaks = pretty_breaks(n = 5),
      expand = c(0, 2)
    )
  
  # Save as high-quality PNG without using Cairo
  ggsave(
    filename = output_file,
    width = width,
    height = height,
    dpi = 120,
    bg = "white",
    device = "png"  # Explicitly specify png device instead of Cairo
  )
  
  # Return success message
  return(paste("Plot saved successfully to", output_file))
}

# If the script is run directly from command line
if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  
  if (length(args) >= 2) {
    data_file <- args[1]
    output_file <- args[2]
    
    # Optional width and height
    width <- if(length(args) >= 3) as.numeric(args[3]) else 8
    height <- if(length(args) >= 4) as.numeric(args[4]) else 5
    
    result <- create_enrollment_plot(data_file, output_file, width, height)
    cat(result)
  } else {
    cat("Usage: Rscript r_visualization.R <data_file.csv> <output_file.png> [width] [height]\n")
  }
}