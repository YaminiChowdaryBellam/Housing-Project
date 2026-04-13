"""
Build a visual Data Model diagram for the Wake County Housing Data.
Outputs: /Users/yamini/Documents/Housing-Project/data_model_diagram.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

OUTPUT = "/Users/yamini/Documents/Housing-Project/data_model_diagram.png"

# ── Colour palette ───────────────────────────────────────────────────────────
NAVY       = "#1B3A6B"
TEAL       = "#007A87"
PURPLE     = "#5B2D8E"
FOREST     = "#1A7A3C"
WHITE      = "#FFFFFF"
LIGHT_NAVY = "#D6E0F0"
LIGHT_TEAL = "#D2EEF0"
LIGHT_PURP = "#E8DAF0"
LIGHT_GRN  = "#D4EDDA"
BG         = "#F8FAFB"
DARK       = "#1A1A2E"
AMBER      = "#E68A00"
LINK_GREY  = "#8899AA"
LINK_RED   = "#C0392B"

fig, ax = plt.subplots(figsize=(22, 16), facecolor=BG)
ax.set_xlim(0, 22)
ax.set_ylim(0, 16)
ax.set_facecolor(BG)
ax.axis("off")

# ── Title ────────────────────────────────────────────────────────────────────
ax.text(11, 15.5, "Wake County HACR — Data Model",
        ha="center", va="center", fontsize=22, fontweight="bold",
        color=NAVY, fontfamily="sans-serif")
ax.text(11, 15.1, "How the 4 wakehousingdata.org Excel Files Connect to Each Other",
        ha="center", va="center", fontsize=12, color=TEAL, fontfamily="sans-serif")

# ── Helper: draw a file box with tables inside ──────────────────────────────
def draw_file_box(ax, x, y, w, h, title, color, bg_color, tables, icon=""):
    """
    x, y = bottom-left corner of the box
    tables = list of (table_name, key_cols) tuples
    """
    # Outer rounded box
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                         facecolor=bg_color, edgecolor=color, linewidth=2.5,
                         zorder=2)
    ax.add_patch(box)

    # Header bar
    hdr = FancyBboxPatch((x + 0.05, y + h - 0.65), w - 0.1, 0.55,
                          boxstyle="round,pad=0.08",
                          facecolor=color, edgecolor="none", zorder=3)
    ax.add_patch(hdr)
    ax.text(x + w / 2, y + h - 0.37, f"{icon}  {title}",
            ha="center", va="center", fontsize=11, fontweight="bold",
            color=WHITE, fontfamily="sans-serif", zorder=4)

    # Table rows
    row_h = 0.42
    start_y = y + h - 0.85
    table_centers = {}
    for i, (tname, keys) in enumerate(tables):
        ty = start_y - i * row_h
        # Alternating row bg
        rbg = WHITE if i % 2 == 0 else bg_color
        row_box = FancyBboxPatch((x + 0.15, ty - 0.15), w - 0.30, row_h - 0.04,
                                  boxstyle="round,pad=0.04",
                                  facecolor=rbg, edgecolor=color, linewidth=0.5,
                                  alpha=0.7, zorder=3)
        ax.add_patch(row_box)

        # Table name
        ax.text(x + 0.35, ty + 0.06, tname,
                ha="left", va="center", fontsize=8.2, fontweight="bold",
                color=DARK, fontfamily="sans-serif", zorder=4)

        # Key columns (right side)
        ax.text(x + w - 0.3, ty + 0.06, keys,
                ha="right", va="center", fontsize=7, fontweight="normal",
                color=LINK_GREY, fontfamily="sans-serif", style="italic", zorder=4)

        # Store center points for arrows
        table_centers[tname] = (x + w / 2, ty + 0.06)

    return table_centers


# ── Positions for 4 boxes (2×2 grid with center gap for dimensions) ─────────
BOX_W = 5.5
BOX_H_DEMO = 5.5  # demographics has more tables
BOX_H_STD  = 4.5

# Demographics — top-left
demo_tables = [
    ("Population Over Time",         "year"),
    ("% Change in Population",       "year, geo"),
    ("Median Household Income",      "year, geo"),
    ("HH Income Distribution",       "income_band"),
    ("Net Change in HH by Income",   "income_band"),
    ("HH by Income & Tenure",        "income_band"),
    ("Households by Race",           "race"),
    ("Population by Age",            "year, age"),
    ("Educational Attainment",       "education"),
    ("Household Size Distribution",  "size"),
]
demo_centers = draw_file_box(
    ax, 0.5, 10, BOX_W, BOX_H_DEMO,
    "DEMOGRAPHICS", NAVY, LIGHT_NAVY, demo_tables, "[A]"
)

# Homeownership — top-right
home_tables = [
    ("Homeownership Rate",           "year, geo"),
    ("Median Home Values",           "year, geo"),
    ("Owner Cost Burden by Income",  "income_band, year"),
    ("Homes Sold by Price Bracket",  "price_bracket"),
    ("Ownership Rate by Income",     "income_band, geo"),
    ("Ownership Rate by Race",       "race, geo"),
    ("Homeowner Vacancy Rate",       "year, geo"),
]
home_centers = draw_file_box(
    ax, 16, 10.5, BOX_W, BOX_H_STD,
    "HOMEOWNERSHIP", TEAL, LIGHT_TEAL, home_tables, "[B]"
)

# Rental — bottom-left
rent_tables = [
    ("Median Rent",                  "year, geo"),
    ("Rental Deficit / Surplus",     "income_band"),
    ("Affordable Units per 100",     "income_band"),
    ("Renter Cost Burden by Income", "income_band, year"),
    ("Rent by Education Level",      "education"),
    ("Income Required vs. Actual",   "year"),
]
rent_centers = draw_file_box(
    ax, 0.5, 3.5, BOX_W, BOX_H_STD,
    "RENTAL AFFORDABILITY", PURPLE, LIGHT_PURP, rent_tables, "[C]"
)

# Housing Supply — bottom-right
supply_tables = [
    ("Building Permits Issued",      "year, type"),
    ("Vacancy Rate (Rental)",        "year, geo"),
    ("Demand vs. Supply by Income",  "income_band"),
    ("Housing Stock by Tenure",      "tenure"),
    ("Stock by Building Type",       "type, tenure, geo"),
]
supply_centers = draw_file_box(
    ax, 16, 4, BOX_W, BOX_H_STD,
    "HOUSING SUPPLY", FOREST, LIGHT_GRN, supply_tables, "[D]"
)

# ── Center: Shared Dimensions Hub ───────────────────────────────────────────
hub_x, hub_y = 11, 9.0
hub_w, hub_h = 4.5, 4.8

hub_box = FancyBboxPatch((hub_x - hub_w/2, hub_y - hub_h/2), hub_w, hub_h,
                          boxstyle="round,pad=0.15",
                          facecolor=WHITE, edgecolor=AMBER, linewidth=3,
                          zorder=5)
ax.add_patch(hub_box)

# Hub header
hub_hdr = FancyBboxPatch((hub_x - hub_w/2 + 0.1, hub_y + hub_h/2 - 0.7),
                           hub_w - 0.2, 0.55,
                           boxstyle="round,pad=0.08",
                           facecolor=AMBER, edgecolor="none", zorder=6)
ax.add_patch(hub_hdr)
ax.text(hub_x, hub_y + hub_h/2 - 0.42, "SHARED DIMENSIONS  (Join Keys)",
        ha="center", va="center", fontsize=11, fontweight="bold",
        color=WHITE, fontfamily="sans-serif", zorder=7)

# Dimension entries in the hub
dims = [
    ("1.  YEAR", "2013-2025", "Links ALL time-series tables across all 4 files"),
    ("2.  INCOME BAND", "<$20K to $150K+", "Links gap, burden, tenure, and deficit tables"),
    ("3.  RACE / ETHNICITY", "7 groups", "Links demographics to homeownership equity"),
    ("4.  EDUCATION", "5 levels", "Links attainment to affordable rent"),
    ("5.  GEOGRAPHY", "Wake vs. NC", "Benchmark comparison across tables"),
]

dim_start_y = hub_y + hub_h/2 - 1.0
for i, (dname, values, desc) in enumerate(dims):
    dy = dim_start_y - i * 0.72
    ax.text(hub_x - hub_w/2 + 0.35, dy, dname,
            ha="left", va="center", fontsize=9, fontweight="bold",
            color=NAVY, fontfamily="sans-serif", zorder=7)
    ax.text(hub_x + hub_w/2 - 0.35, dy, values,
            ha="right", va="center", fontsize=7.5, fontweight="normal",
            color=AMBER, fontfamily="sans-serif", zorder=7)
    ax.text(hub_x - hub_w/2 + 0.35, dy - 0.22, desc,
            ha="left", va="center", fontsize=7, fontweight="normal",
            color=LINK_GREY, fontfamily="sans-serif", style="italic", zorder=7)

# ── Arrows from each file box to the hub ─────────────────────────────────────
arrow_style = "Simple,tail_width=2,head_width=10,head_length=6"

# Demographics → Hub (right edge to hub left)
ax.annotate("", xy=(hub_x - hub_w/2, hub_y + 1.2),
            xytext=(0.5 + BOX_W, 12.5),
            arrowprops=dict(arrowstyle="-|>", color=NAVY,
                           lw=2.2, connectionstyle="arc3,rad=-0.15"),
            zorder=1)
ax.text(7.5, 13.0, "year, income_band,\nrace, education",
        ha="center", va="center", fontsize=7.5, color=NAVY,
        fontweight="bold", fontfamily="sans-serif",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=LIGHT_NAVY, edgecolor=NAVY, alpha=0.8),
        zorder=8)

# Homeownership → Hub (left edge to hub right)
ax.annotate("", xy=(hub_x + hub_w/2, hub_y + 1.2),
            xytext=(16, 12.5),
            arrowprops=dict(arrowstyle="-|>", color=TEAL,
                           lw=2.2, connectionstyle="arc3,rad=0.15"),
            zorder=1)
ax.text(14.5, 13.0, "year, income_band,\nrace",
        ha="center", va="center", fontsize=7.5, color=TEAL,
        fontweight="bold", fontfamily="sans-serif",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=LIGHT_TEAL, edgecolor=TEAL, alpha=0.8),
        zorder=8)

# Rental → Hub (right edge to hub left)
ax.annotate("", xy=(hub_x - hub_w/2, hub_y - 1.2),
            xytext=(0.5 + BOX_W, 5.5),
            arrowprops=dict(arrowstyle="-|>", color=PURPLE,
                           lw=2.2, connectionstyle="arc3,rad=0.15"),
            zorder=1)
ax.text(7.5, 5.0, "year, income_band,\neducation",
        ha="center", va="center", fontsize=7.5, color=PURPLE,
        fontweight="bold", fontfamily="sans-serif",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=LIGHT_PURP, edgecolor=PURPLE, alpha=0.8),
        zorder=8)

# Housing Supply → Hub (left edge to hub right)
ax.annotate("", xy=(hub_x + hub_w/2, hub_y - 1.2),
            xytext=(16, 5.8),
            arrowprops=dict(arrowstyle="-|>", color=FOREST,
                           lw=2.2, connectionstyle="arc3,rad=-0.15"),
            zorder=1)
ax.text(14.5, 5.2, "year, income_band",
        ha="center", va="center", fontsize=7.5, color=FOREST,
        fontweight="bold", fontfamily="sans-serif",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=LIGHT_GRN, edgecolor=FOREST, alpha=0.8),
        zorder=8)

# ── Cross-file relationship arrows (direct table-to-table) ──────────────────

# 1. Rental Deficit ↔ Demand vs. Supply (bottom horizontal)
ax.annotate("", xy=(16, 5.73), xytext=(6, 5.73),
            arrowprops=dict(arrowstyle="<|-|>", color=LINK_RED,
                           lw=1.8, connectionstyle="arc3,rad=-0.25",
                           linestyle="dashed"),
            zorder=1)
ax.text(11, 2.8, "\u2460 Same gap data — two views",
        ha="center", va="center", fontsize=8, color=LINK_RED,
        fontweight="bold", fontfamily="sans-serif",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#FDE8E8", edgecolor=LINK_RED, alpha=0.9),
        zorder=8)

# 2. Renter Cost Burden ↔ Net HH Change (left vertical)
ax.annotate("", xy=(3, 10), xytext=(3, 8),
            arrowprops=dict(arrowstyle="<|-|>", color=LINK_RED,
                           lw=1.8, linestyle="dashed"),
            zorder=1)
ax.text(3, 9.0, "\u2461 Burden\ndrives\ndisplacement",
        ha="center", va="center", fontsize=7, color=LINK_RED,
        fontweight="bold", fontfamily="sans-serif",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="#FDE8E8", edgecolor=LINK_RED, alpha=0.9),
        zorder=8)

# 3. Ownership by Race ↔ HH by Race (top horizontal)
ax.annotate("", xy=(16, 11.6), xytext=(6, 11.2),
            arrowprops=dict(arrowstyle="<|-|>", color=LINK_RED,
                           lw=1.8, connectionstyle="arc3,rad=0.2",
                           linestyle="dashed"),
            zorder=1)
ax.text(11, 15.85, "\u2462 Rate \u00d7 Count = Equity gap",
        ha="center", va="center", fontsize=8, color=LINK_RED,
        fontweight="bold", fontfamily="sans-serif",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#FDE8E8", edgecolor=LINK_RED, alpha=0.9),
        zorder=8)

# ── Legend ───────────────────────────────────────────────────────────────────
legend_y = 1.3
ax.text(0.8, legend_y + 1.0, "LEGEND", fontsize=10, fontweight="bold",
        color=NAVY, fontfamily="sans-serif")

legend_items = [
    (NAVY,   "Demographics file"),
    (TEAL,   "Homeownership file"),
    (PURPLE, "Rental Affordability file"),
    (FOREST, "Housing Supply file"),
    (AMBER,  "Shared dimension (join key)"),
]
for i, (c, label) in enumerate(legend_items):
    lx = 0.8 + i * 3.2
    ax.add_patch(FancyBboxPatch((lx, legend_y, ), 0.35, 0.35,
                                boxstyle="round,pad=0.05",
                                facecolor=c, edgecolor="none", zorder=8))
    ax.text(lx + 0.5, legend_y + 0.17, label,
            ha="left", va="center", fontsize=8, color=DARK,
            fontfamily="sans-serif", zorder=8)

# Dashed arrow legend
ax.annotate("", xy=(17.5, legend_y + 0.17), xytext=(16.5, legend_y + 0.17),
            arrowprops=dict(arrowstyle="<|-|>", color=LINK_RED,
                           lw=1.5, linestyle="dashed"),
            zorder=8)
ax.text(17.7, legend_y + 0.17, "Direct cross-file relationship",
        ha="left", va="center", fontsize=8, color=DARK,
        fontfamily="sans-serif", zorder=8)

# Footer
ax.text(11, 0.3,
        "Data Model  |  4 Excel files  \u00b7  26 tables  \u00b7  5 shared dimensions  \u00b7  6 key cross-file relationships  |  wakehousingdata.org",
        ha="center", va="center", fontsize=8, color=LINK_GREY,
        fontfamily="sans-serif", style="italic")

plt.tight_layout(pad=0.5)
plt.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor=BG)
plt.close()
print(f"\u2713 Data model diagram saved: {OUTPUT}")
