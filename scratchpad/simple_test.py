import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

# Create a simplified test dataset with just 2 categories
data = pd.DataFrame(
    {
        "value": [364, 232, 357, 204],
        "category": ["West", "West", "East", "East"],
        "sub_category": ["Consumer", "Corporate", "Consumer", "Corporate"],
    }
)

# Define category order
cat_order = ["West", "East"]
data["category"] = pd.Categorical(data["category"], categories=cat_order, ordered=True)
data = data.sort_values(["category", "value"], ascending=[True, False])

# Pivot data
pivot_df = data.pivot(index="category", columns="sub_category", values="value")
totals = pivot_df.sum(axis=1)

# Create figure and axes
fig, ax = plt.subplots(figsize=(7, 5))

# Set up bar positioning with fixed width as in original
bar_width = 0.25
x = np.arange(len(pivot_df.index))
x_spacing = 2  # Increase spacing between category groups
x_adjusted = x * x_spacing  # Adjust x positions to have space between categories

# Draw background bars for totals
ax.bar(x_adjusted, totals, width=bar_width * 3.5, color="lightgrey", zorder=0, label="Total")

# Draw bars for each subcategory
for i, sub_cat in enumerate(pivot_df.columns):
    ax.bar(
        x_adjusted + (i - 1) * bar_width,
        pivot_df[sub_cat],
        width=bar_width,
        label=sub_cat,
        zorder=1,
    )

# Set up labels and formatting
ax.set_xlabel("Category")
ax.set_ylabel("Value")
ax.set_title("Simplified Test", loc="left")
ax.set_xticks(x_adjusted)
ax.set_xticklabels(pivot_df.index)
ax.legend(title="Sub Category")

# Save and show figure
output_file = "simple_test.png"
fig.savefig(output_file, dpi=100, bbox_inches="tight")
print(f"Saved: {output_file}")
plt.close(fig)