#!/usr/bin/env Rscript

# Quick test of enrollment visualization

# Load required libraries
library(ggplot2)
library(lubridate)
library(dplyr)

# Create sample data
start_date <- as.Date("2023-01-01")
end_date <- as.Date("2023-12-31")
dates <- seq(start_date, end_date, by="day")
patient_ids <- 1:length(dates)

# Create data frame
df <- data.frame(
  patient_id = patient_ids,
  enrollment_date = dates
)

# Save to CSV
write.csv(df, "test_enrollment.csv", row.names = FALSE)
cat("Created test data with", nrow(df), "patients\n")

# Aggregate by month
monthly_data <- df %>%
  mutate(month = floor_date(enrollment_date, "month")) %>%
  count(month) %>%
  arrange(month)

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

# Create the plot
p <- ggplot(monthly_data, aes(x = month, y = n)) +
  geom_bar(stat = "identity", fill = "#4682B4", alpha = 0.7) +
  # Add a smoothed trend line
  geom_smooth(method = "loess", color = "#B22222", linewidth = 1, se = FALSE) +
  theme_tufte_enhanced() +
  # Labels
  labs(
    title = "Patient Enrollment Over Time",
    subtitle = paste0("Total of ", nrow(df), " patients enrolled"),
    x = "Month",
    y = "Number of Patients",
    caption = "Data source: Test data"
  ) +
  # Format x-axis
  scale_x_date(
    date_breaks = "1 month",
    date_labels = "%b %Y",
    expand = expansion(mult = c(0.02, 0.02))
  )

# Save to file
output_file <- "test_enrollment_plot.png"
ggsave(output_file, plot = p, width = 10, height = 5, dpi = 120)
cat("Plot saved to:", output_file, "\n")