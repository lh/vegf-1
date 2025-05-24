import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

data = pd.DataFrame(
    {
        "value": [364, 232, 143, 357, 204, 131, 254, 158, 91, 196, 122, 74],
        "category": [
            "West",
            "West",
            "West",
            "East",
            "East",
            "East",
            "Central",
            "Central",
            "Central",
            "South",
            "South",
            "South",
        ],
        "sub_category": [
            "Consumer",
            "Corporate",
            "Home office",
            "Consumer",
            "Corporate",
            "Home office",
            "Consumer",
            "Corporate",
            "Home office",
            "Consumer",
            "Corporate",
            "Home office",
        ],
    }
)

cat_order = ["West", "East", "Central", "South"]
data["category"] = pd.Categorical(data["category"], categories=cat_order, ordered=True)
data = data.sort_values(["category", "value"], ascending=[True, False])

pivot_df = data.pivot(index="category", columns="sub_category", values="value")
totals = pivot_df.sum(axis=1)

fig, ax = plt.subplots(figsize=(7, 5))

bar_width = 0.25
x = np.arange(len(pivot_df.index))

ax.bar(x, totals, width=bar_width * 3.5, color="lightgrey", zorder=0, label="Total")

for i, sub_cat in enumerate(pivot_df.columns):
    ax.bar(
        x + (i - 1) * bar_width,
        pivot_df[sub_cat],
        width=bar_width,
        label=sub_cat,
        zorder=1,
    )

ax.set_xlabel("Category")
ax.set_ylabel("Value")
ax.set_title("Regions - Revenue by Segment", loc="left")
ax.set_xticks(x)
ax.set_xticklabels(pivot_df.index)
ax.legend(title="Sub Category")

fig.savefig(
    "grouped-barplot-with-the-total-of-each-group-represented-as-a-grey-rectangle.png",
    dpi=100,
    bbox_inches="tight",
)
plt.show()