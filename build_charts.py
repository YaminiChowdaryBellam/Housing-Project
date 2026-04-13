"""
Generate all chart images for the PowerPoint presentation.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import os

OUT = "/Users/yamini/Documents/Housing-Project/charts"
os.makedirs(OUT, exist_ok=True)

# ── Palette ──────────────────────────────────────────────────────────────────
NAVY   = "#1B3A6B"
TEAL   = "#007A87"
RED    = "#C0392B"
GREEN  = "#1A7A3C"
AMBER  = "#E68A00"
PURPLE = "#5B2D8E"
LIGHT  = "#E8F4F8"
BG     = "#FAFCFE"
DARK   = "#1A1A2E"
GREY   = "#AABBCC"

def save(fig, name):
    fig.savefig(f"{OUT}/{name}", dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  + {name}")

# ════════════════════════════════════════════════════════════════════════════
# CHART 1 — Supply-Demand Gap by Income Band
# ════════════════════════════════════════════════════════════════════════════
bands  = ["<$20K", "<$35K", "<$50K", "<$75K", "<$100K", "<$150K"]
renter = [19938, 39111, 60690, 92483, 117033, 143714]
afford = [3164, 13074, 36222, 95808, 148765, 158495]
gap    = [a - r for r, a in zip(renter, afford)]

fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=BG)
ax.set_facecolor(BG)
colors = [RED if g < 0 else GREEN for g in gap]
bars = ax.bar(bands, gap, color=colors, edgecolor="white", linewidth=1.5, width=0.65)
for bar, g in zip(bars, gap):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (800 if g > 0 else -1800),
            f"{g:+,}", ha="center", va="bottom" if g > 0 else "top",
            fontsize=11, fontweight="bold", color=DARK)
ax.axhline(0, color=DARK, linewidth=0.8)
ax.set_title("Rental Housing Deficit / Surplus by Income Band", fontsize=14, fontweight="bold", color=NAVY, pad=15)
ax.set_ylabel("Units (Deficit / Surplus)", fontsize=10, color=DARK)
ax.set_xlabel("Household Income Threshold", fontsize=10, color=DARK)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
save(fig, "01_supply_demand_gap.png")

# ════════════════════════════════════════════════════════════════════════════
# CHART 2 — Affordable Units per 100 Renters
# ════════════════════════════════════════════════════════════════════════════
per100 = [16, 33, 60, 104, 127, 110]

fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
ax.set_facecolor(BG)
bar_colors = [RED if p < 100 else GREEN for p in per100]
bars = ax.barh(bands[::-1], per100[::-1], color=[bar_colors[i] for i in range(5, -1, -1)],
               edgecolor="white", linewidth=1.5, height=0.55)
ax.axvline(100, color=AMBER, linewidth=2, linestyle="--", label="100 = Balanced (enough for everyone)")
for bar, p in zip(bars, per100[::-1]):
    ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
            str(p), ha="left", va="center", fontsize=12, fontweight="bold", color=DARK)
ax.set_title("Affordable Rental Homes per 100 Renter Households", fontsize=14, fontweight="bold", color=NAVY, pad=15)
ax.set_xlabel("Affordable Units Available per 100 Renters", fontsize=10, color=DARK)
ax.legend(loc="lower right", fontsize=9, framealpha=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_xlim(0, 145)
save(fig, "02_per_100_renters.png")

# ════════════════════════════════════════════════════════════════════════════
# CHART 3 — Renter Cost Burden by Income (2014 vs 2024)
# ════════════════════════════════════════════════════════════════════════════
burden_bands = ["<$20K", "$20K-$35K", "$35K-$50K", "$50K-$75K", "$75K-$100K", "$100K+"]
burden_2014  = [93.43, 80.41, 34.51, 9.75, 2.66, 1.15]
burden_2024  = [96.0,  94.69, 88.85, 55.79, 20.76, 4.06]

fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=BG)
ax.set_facecolor(BG)
x = np.arange(len(burden_bands))
w = 0.35
bars1 = ax.bar(x - w/2, burden_2014, w, label="2014", color=TEAL, edgecolor="white", linewidth=1.2)
bars2 = ax.bar(x + w/2, burden_2024, w, label="2024", color=RED, edgecolor="white", linewidth=1.2)
for bar, val in zip(bars1, burden_2014):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
            f"{val:.0f}%", ha="center", va="bottom", fontsize=8, color=TEAL, fontweight="bold")
for bar, val in zip(bars2, burden_2024):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
            f"{val:.0f}%", ha="center", va="bottom", fontsize=8, color=RED, fontweight="bold")
ax.axhline(30, color=AMBER, linewidth=1.5, linestyle="--", label="HUD 30% Threshold")
ax.set_xticks(x)
ax.set_xticklabels(burden_bands)
ax.set_title("Renter Cost Burden Rate by Income Band  (2014 vs 2024)", fontsize=14, fontweight="bold", color=NAVY, pad=15)
ax.set_ylabel("% of Renters Cost-Burdened", fontsize=10, color=DARK)
ax.legend(loc="upper right", fontsize=9, framealpha=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_ylim(0, 110)
save(fig, "03_cost_burden.png")

# ════════════════════════════════════════════════════════════════════════════
# CHART 4 — Income Required vs Median Renter Income
# ════════════════════════════════════════════════════════════════════════════
years_inc   = list(range(2015, 2025))
renter_inc  = [40068, 42431, 44819, 46981, 49439, 51200, 53128, 57972, 61376, 65172]
required    = [44160, 45280, 47040, 48800, 50920, 52480, 61400, 65360, 65640, 65920]

fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=BG)
ax.set_facecolor(BG)
ax.plot(years_inc, renter_inc, "-o", color=TEAL, linewidth=2.5, markersize=7, label="Actual Median Renter Income")
ax.plot(years_inc, required, "-s", color=RED, linewidth=2.5, markersize=7, label="Income Required to Afford Median Rent")
ax.fill_between(years_inc, renter_inc, required,
                where=[r > i for r, i in zip(required, renter_inc)],
                color=RED, alpha=0.12, label="Affordability Gap")
# Annotate 2021 spike
ax.annotate("2021: $8,920\njump needed", xy=(2021, 61400),
            xytext=(2021.5, 57000),
            arrowprops=dict(arrowstyle="->", color=RED, lw=1.5),
            fontsize=9, color=RED, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FDE8E8", edgecolor=RED, alpha=0.8))
ax.set_title("Income Required to Afford Rent  vs.  Actual Renter Income", fontsize=14, fontweight="bold", color=NAVY, pad=15)
ax.set_ylabel("Annual Income ($)", fontsize=10, color=DARK)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${int(x):,}"))
ax.legend(loc="upper left", fontsize=9, framealpha=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
save(fig, "04_income_vs_rent.png")

# ════════════════════════════════════════════════════════════════════════════
# CHART 5 — Entry-Level Home Sales Collapse
# ════════════════════════════════════════════════════════════════════════════
price_brackets = ["<$250K", "$250K-$500K", "$500K-$750K", "$750K-$1M", "$1M-$1.5M", "$1.5M+"]
pct_2018 = [28.58, 53.77, 12.40, 2.79, 0.95, 1.51]
pct_2022 = [3.09,  50.10, 32.20, 8.61, 4.33, 1.67]

fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=BG)
ax.set_facecolor(BG)
x = np.arange(len(price_brackets))
w = 0.35
bars1 = ax.bar(x - w/2, pct_2018, w, label="2018", color=TEAL, edgecolor="white", linewidth=1.2)
bars2 = ax.bar(x + w/2, pct_2022, w, label="2022", color=PURPLE, edgecolor="white", linewidth=1.2)
# Highlight the collapse
ax.annotate("89% drop\nin 4 years", xy=(0, 3.09), xytext=(0.8, 22),
            arrowprops=dict(arrowstyle="->", color=RED, lw=2),
            fontsize=11, fontweight="bold", color=RED,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FDE8E8", edgecolor=RED))
ax.set_xticks(x)
ax.set_xticklabels(price_brackets, fontsize=9)
ax.set_title("Share of Homes Sold by Price Bracket  (2018 vs 2022)", fontsize=14, fontweight="bold", color=NAVY, pad=15)
ax.set_ylabel("% of Total Sales", fontsize=10, color=DARK)
ax.legend(loc="upper right", fontsize=9, framealpha=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
save(fig, "05_entry_level_collapse.png")

# ════════════════════════════════════════════════════════════════════════════
# CHART 6 — Vacancy Rate Trend
# ════════════════════════════════════════════════════════════════════════════
vac_years = list(range(2014, 2025))
vac_wake  = [3.58, 3.12, 2.83, 2.82, 2.81, 2.74, 2.77, 2.87, 3.77, 3.85, 3.72]
vac_nc    = [4.06, 3.81, 3.62, 3.49, 3.36, 3.22, 3.07, 2.99, 3.00, 2.96, 3.01]

fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
ax.set_facecolor(BG)
ax.fill_between(vac_years, 5, 7, color=GREEN, alpha=0.08, label="Healthy Range (5%+)")
ax.axhline(5, color=GREEN, linewidth=1.5, linestyle="--", alpha=0.7)
ax.plot(vac_years, vac_wake, "-o", color=NAVY, linewidth=2.5, markersize=7, label="Wake County")
ax.plot(vac_years, vac_nc, "-s", color=GREY, linewidth=2, markersize=6, label="North Carolina")
ax.text(2024.2, 3.72, "3.72%", fontsize=10, fontweight="bold", color=RED)
ax.text(2024.2, 5.1, "5% healthy", fontsize=8, color=GREEN, style="italic")
ax.set_title("Rental Vacancy Rate: Wake County vs. North Carolina", fontsize=14, fontweight="bold", color=NAVY, pad=15)
ax.set_ylabel("Vacancy Rate (%)", fontsize=10, color=DARK)
ax.legend(loc="upper right", fontsize=9, framealpha=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_ylim(1.5, 7)
save(fig, "06_vacancy_rate.png")

# ════════════════════════════════════════════════════════════════════════════
# CHART 7 — Net Household Change by Income Band
# ════════════════════════════════════════════════════════════════════════════
hh_bands  = ["<$20K", "$20K-$35K", "$35K-$50K", "$50K-$75K", "$75K-$100K", "$100K-$150K", "$150K+"]
hh_change = [-9976, -13200, -7177, -1531, 7043, 28585, 100784]

fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=BG)
ax.set_facecolor(BG)
colors = [RED if c < 0 else GREEN for c in hh_change]
bars = ax.barh(hh_bands[::-1], hh_change[::-1],
               color=[colors[i] for i in range(6, -1, -1)],
               edgecolor="white", linewidth=1.5, height=0.55)
ax.axvline(0, color=DARK, linewidth=0.8)
for bar, c in zip(bars, hh_change[::-1]):
    x_pos = bar.get_width() + (1500 if c > 0 else -1500)
    ax.text(x_pos, bar.get_y() + bar.get_height()/2,
            f"{c:+,}", ha="left" if c > 0 else "right", va="center",
            fontsize=9, fontweight="bold", color=DARK)
ax.set_title("Net Change in Households by Income Band  (2014-2024)", fontsize=14, fontweight="bold", color=NAVY, pad=15)
ax.set_xlabel("Net Change in Households", fontsize=10, color=DARK)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
save(fig, "07_hh_change.png")

# ════════════════════════════════════════════════════════════════════════════
# CHART 8 — Scenario Comparison: Years to Close the <$35K Gap
# ════════════════════════════════════════════════════════════════════════════
scenarios = ["Current Pace\n660 units/yr", "2x Scale-Up\n1,320 units/yr",
             "5x Scale-Up\n3,300 units/yr", "Deep Subsidy\n(<$20K focus)"]
years_close = [40, 20, 8, 40]
sc_colors   = [RED, AMBER, GREEN, PURPLE]

fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
ax.set_facecolor(BG)
bars = ax.bar(scenarios, years_close, color=sc_colors, edgecolor="white", linewidth=1.5, width=0.55)
for bar, y in zip(bars, years_close):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f"{y} yrs", ha="center", va="bottom", fontsize=13, fontweight="bold", color=DARK)
ax.set_title("Years to Close the <$35K Affordable Housing Gap\nunder Different Policy Scenarios",
             fontsize=14, fontweight="bold", color=NAVY, pad=15)
ax.set_ylabel("Years to Close Gap", fontsize=10, color=DARK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_ylim(0, 50)
# Add investment note
ax.text(0.5, 0.02, "Total investment is $3.8B regardless of pace — only the timeline changes",
        transform=ax.transAxes, ha="center", fontsize=9, color=AMBER,
        fontweight="bold", style="italic",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF8E8", edgecolor=AMBER, alpha=0.9))
save(fig, "08_scenarios.png")

# ════════════════════════════════════════════════════════════════════════════
# CHART 9 — Median Rent Trend
# ════════════════════════════════════════════════════════════════════════════
rent_years = list(range(2015, 2025))
rent_wake  = [1104, 1132, 1176, 1220, 1273, 1312, 1535, 1634, 1641, 1648]
rent_nc    = [797, 816, 844, 877, 907, 932, 988, 1093, 1162, 1228]

fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
ax.set_facecolor(BG)
ax.plot(rent_years, rent_wake, "-o", color=NAVY, linewidth=2.5, markersize=7, label="Wake County")
ax.plot(rent_years, rent_nc, "-s", color=GREY, linewidth=2, markersize=6, label="North Carolina")
ax.fill_between(rent_years, rent_wake, rent_nc, color=NAVY, alpha=0.08)
# Annotate 2021 jump
ax.annotate("+$223/mo\nin one year", xy=(2021, 1535), xytext=(2019.5, 1600),
            arrowprops=dict(arrowstyle="->", color=RED, lw=1.5),
            fontsize=10, fontweight="bold", color=RED,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FDE8E8", edgecolor=RED))
ax.set_title("Median Rent Trend: Wake County vs. North Carolina", fontsize=14, fontweight="bold", color=NAVY, pad=15)
ax.set_ylabel("Monthly Rent ($)", fontsize=10, color=DARK)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${int(x):,}"))
ax.legend(loc="upper left", fontsize=9, framealpha=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
save(fig, "09_rent_trend.png")

# ════════════════════════════════════════════════════════════════════════════
# CHART 10 — Homeownership Rate by Race
# ════════════════════════════════════════════════════════════════════════════
races      = ["Asian", "White", "Other/\nAI/AN/NHPI", "Hispanic/\nLatino", "Black"]
own_wake   = [72.04, 71.40, 50.98, 49.94, 45.47]
own_nc     = [67.13, 74.79, 54.82, 52.07, 47.50]

fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
ax.set_facecolor(BG)
x = np.arange(len(races))
w = 0.35
ax.bar(x - w/2, own_wake, w, label="Wake County", color=NAVY, edgecolor="white", linewidth=1.2)
ax.bar(x + w/2, own_nc, w, label="North Carolina", color=TEAL, edgecolor="white", linewidth=1.2)
for i, (wk, nc) in enumerate(zip(own_wake, own_nc)):
    ax.text(i - w/2, wk + 1.5, f"{wk:.1f}%", ha="center", fontsize=8, fontweight="bold", color=NAVY)
    ax.text(i + w/2, nc + 1.5, f"{nc:.1f}%", ha="center", fontsize=8, fontweight="bold", color=TEAL)
# Gap annotation
ax.annotate("25.9 pp gap", xy=(4, 45.47), xytext=(3.2, 38),
            arrowprops=dict(arrowstyle="->", color=RED, lw=1.5),
            fontsize=10, fontweight="bold", color=RED,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FDE8E8", edgecolor=RED))
ax.set_xticks(x)
ax.set_xticklabels(races)
ax.set_title("Homeownership Rate by Race / Ethnicity", fontsize=14, fontweight="bold", color=NAVY, pad=15)
ax.set_ylabel("Homeownership Rate (%)", fontsize=10, color=DARK)
ax.legend(loc="lower right", fontsize=9, framealpha=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_ylim(0, 85)
save(fig, "10_ownership_by_race.png")

print(f"\nAll charts saved to {OUT}/")
