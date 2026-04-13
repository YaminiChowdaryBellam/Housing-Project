"""
Phase 2 — Analysis Engine
=========================
Pure functions that compute every derived metric used by the dashboard.
No UI, no side effects — fully testable and importable.

Metrics produced:
  - Gap severity by AMI band (absolute, per-100, percentage)
  - Years to close gap at historical and user-defined production rates
  - Production pace vs. required pace to hit 2029 goal
  - Permit trend statistics (peak year, YoY change, SF/MF split)
  - Cost burden progression (spread to middle-income bands 2014→2024)
  - Rent-income gap timeline with 2021 inflection point flagged
  - Entry-level homeownership collapse (price bracket shift 2018→2022)
  - Income polarization (net household change by band)
"""

import pandas as pd
import numpy as np
from data_loader import (
    load_all,
    HACR_CONSTANTS,
)

# ════════════════════════════════════════════════════════════════════════════
# 1. GAP ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

def gap_summary(supply_demand_gap: pd.DataFrame,
                affordable_per_100: pd.DataFrame) -> pd.DataFrame:
    """
    Merge the supply-demand gap table with the affordable-units-per-100
    table to produce one comprehensive gap DataFrame per AMI band.

    Columns returned:
      income_threshold, renter_households, affordable_units,
      gap (negative = deficit), gap_pct, units_per_100,
      deficit_flag, severity_label
    """
    merged = supply_demand_gap.merge(
        affordable_per_100[["income_threshold", "units_per_100", "deficit_flag"]],
        on="income_threshold",
        how="left",
    )

    def _severity(row):
        u = row["units_per_100"]
        if u < 20:   return "Critical"
        if u < 50:   return "Severe"
        if u < 80:   return "Moderate"
        if u < 100:  return "Low"
        return "Surplus"

    merged["severity_label"] = merged.apply(_severity, axis=1)
    return merged


def gap_at_band(gap_df: pd.DataFrame, band: str) -> dict:
    """Return gap metrics for a single income band as a plain dict."""
    row = gap_df[gap_df["income_threshold"] == band].iloc[0]
    return {
        "income_threshold":  row["income_threshold"],
        "renter_households": int(row["renter_households"]),
        "affordable_units":  int(row["affordable_units"]),
        "gap":               int(row["gap"]),
        "gap_pct":           float(row["gap_pct"]),
        "units_per_100":     int(row["units_per_100"]),
        "severity_label":    row["severity_label"],
    }


def total_deficit_units(gap_df: pd.DataFrame) -> int:
    """Sum of all deficit bands (bands where gap < 0)."""
    return int(gap_df[gap_df["gap"] < 0]["gap"].sum())


# ════════════════════════════════════════════════════════════════════════════
# 2. PRODUCTION PACE & YEARS-TO-CLOSE
# ════════════════════════════════════════════════════════════════════════════

def years_to_close(deficit: int, annual_production: int) -> float:
    """
    How many years at `annual_production` units/year to close `deficit`.
    Returns float('inf') if production <= 0, or 0 if no deficit.
    """
    if deficit >= 0:
        return 0.0
    if annual_production <= 0:
        return float("inf")
    return round(abs(deficit) / annual_production, 1)


def production_pace_table(gap_df: pd.DataFrame,
                           current_pace: int = None) -> pd.DataFrame:
    """
    For each deficit AMI band, calculate years to close at three production
    rates: current HACR pace, 2× pace, and 5× pace.

    current_pace defaults to HACR FY2025 production (660 units/yr).
    """
    if current_pace is None:
        current_pace = HACR_CONSTANTS["fy2025_production"]

    deficit_bands = gap_df[gap_df["gap"] < 0].copy()
    rows = []
    for _, r in deficit_bands.iterrows():
        deficit = abs(int(r["gap"]))
        rows.append({
            "income_threshold":        r["income_threshold"],
            "deficit_units":           deficit,
            "units_per_100":           int(r["units_per_100"]),
            "severity_label":          r["severity_label"],
            "years_at_current_pace":   years_to_close(-deficit, current_pace),
            "years_at_2x_pace":        years_to_close(-deficit, current_pace * 2),
            "years_at_5x_pace":        years_to_close(-deficit, current_pace * 5),
        })
    return pd.DataFrame(rows)


def goal_progress_metrics() -> dict:
    """
    Wake County 2024-2029 Strategic Plan goal tracking.
    Returns current progress, gap to goal, required annual pace.
    """
    constants  = HACR_CONSTANTS
    goal       = constants["production_goal_2029"]
    achieved   = constants["production_achieved_to_date"]
    remaining  = goal - achieved
    # Strategic plan started 2024; 2029 = 5-year window, ~3.5 years left from now (Apr 2026)
    years_left = 3.5
    required_pace = round(remaining / years_left, 0)

    return {
        "goal_2029":          goal,
        "achieved_to_date":   achieved,
        "pct_complete":       round(achieved / goal * 100, 1),
        "remaining":          remaining,
        "years_left":         years_left,
        "required_pace":      int(required_pace),
        "current_pace":       constants["fy2025_production"],
        "pace_gap":           int(required_pace - constants["fy2025_production"]),
        "on_track":           constants["fy2025_production"] >= required_pace,
        "pipeline_units":     constants["development_pipeline_units"],
    }


def annual_production_df() -> pd.DataFrame:
    """
    Historical HACR affordable unit production (2019–2025) from annual report,
    with cumulative total and gap to 2029 goal.
    """
    history = HACR_CONSTANTS["annual_production_history"]
    goal    = HACR_CONSTANTS["production_goal_2029"]
    rows = []
    cumulative = 0
    for year in sorted(history):
        units = history[year]
        cumulative += units
        rows.append({
            "year":       year,
            "units":      units,
            "cumulative": cumulative,
            "gap_to_goal": max(0, goal - cumulative),
        })
    return pd.DataFrame(rows)


# ════════════════════════════════════════════════════════════════════════════
# 3. PERMIT TREND ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

def permit_trend_stats(permits: pd.DataFrame) -> dict:
    """
    Key statistics derived from the building permit time series.

    Returns:
      peak_year, peak_total, peak_mf_year, peak_mf_units,
      latest_year, latest_sf, latest_mf, latest_total,
      mf_change_since_peak_pct, sf_cagr (2014→latest),
      avg_annual_total, demand_gap_annual (permits vs 18k–23k need)
    """
    peak_row     = permits.loc[permits["total"].idxmax()]
    peak_mf_row  = permits.loc[permits["multifamily"].idxmax()]
    latest       = permits.iloc[-1]
    first        = permits.iloc[0]
    n_years      = latest["year"] - first["year"]

    sf_cagr = round(
        ((latest["single_family"] / first["single_family"]) ** (1 / n_years) - 1) * 100, 1
    )
    mf_change = round(
        (latest["multifamily"] - peak_mf_row["multifamily"])
        / peak_mf_row["multifamily"] * 100, 1
    )

    return {
        "peak_year":               int(peak_row["year"]),
        "peak_total":              int(peak_row["total"]),
        "peak_mf_year":            int(peak_mf_row["year"]),
        "peak_mf_units":           int(peak_mf_row["multifamily"]),
        "latest_year":             int(latest["year"]),
        "latest_sf":               int(latest["single_family"]),
        "latest_mf":               int(latest["multifamily"]),
        "latest_total":            int(latest["total"]),
        "mf_change_since_peak_pct": mf_change,
        "sf_cagr_pct":             sf_cagr,
        "avg_annual_total":        int(permits["total"].mean()),
        # Annual demand estimate from NC Chamber / HACR: 18k–23k units/yr
        "demand_low":              18_000,
        "demand_high":             23_000,
        "supply_gap_vs_demand_low": int(18_000 - latest["total"]),
    }


def permits_with_annotations(permits: pd.DataFrame) -> pd.DataFrame:
    """Add annotation labels to key years for chart callouts."""
    df = permits.copy()
    df["annotation"] = ""
    df.loc[df["year"] == 2021, "annotation"] = "Rent spike year"
    df.loc[df["year"] == df.loc[df["multifamily"].idxmax(), "year"],
           "annotation"] = "MF peak"
    df.loc[df["year"] == df["year"].max(), "annotation"] = "Latest"
    return df


# ════════════════════════════════════════════════════════════════════════════
# 4. COST BURDEN PROGRESSION
# ════════════════════════════════════════════════════════════════════════════

def cost_burden_spread(cost_burden_by_income: pd.DataFrame) -> pd.DataFrame:
    """
    Reshape cost burden by income to long format for heatmap / grouped bar.
    Adds a 'crisis_flag' for bands where 2024 burden > 50%.
    """
    df = cost_burden_by_income.copy()
    df["crisis_flag_2024"] = df["pct_2024"] > 50
    df["new_crisis_band"]  = (df["pct_2024"] > 50) & (df["pct_2014"] <= 50)

    long = df.melt(
        id_vars=["income_band", "crisis_flag_2024", "new_crisis_band",
                 "change_2014_2024"],
        value_vars=["pct_2014", "pct_2019", "pct_2024"],
        var_name="period",
        value_name="pct_cost_burdened",
    )
    long["year"] = long["period"].map(
        {"pct_2014": 2014, "pct_2019": 2019, "pct_2024": 2024}
    )
    return long.drop(columns="period")


def bands_newly_in_crisis(cost_burden_by_income: pd.DataFrame) -> list:
    """
    Return income bands that crossed the 50% cost-burden threshold
    between 2014 and 2024 (were safe in 2014, now in crisis in 2024).
    """
    df = cost_burden_by_income
    return df.loc[
        (df["pct_2024"] > 50) & (df["pct_2014"] <= 50),
        "income_band"
    ].tolist()


def biggest_burden_jump(cost_burden_by_income: pd.DataFrame) -> dict:
    """The income band with the largest absolute increase 2014→2024."""
    df  = cost_burden_by_income
    idx = df["change_2014_2024"].idxmax()
    row = df.loc[idx]
    return {
        "income_band":  row["income_band"],
        "pct_2014":     row["pct_2014"],
        "pct_2024":     row["pct_2024"],
        "change":       round(row["change_2014_2024"], 1),
    }


# ════════════════════════════════════════════════════════════════════════════
# 5. RENT–INCOME GAP & 2021 INFLECTION POINT
# ════════════════════════════════════════════════════════════════════════════

def rent_income_gap_stats(income_vs_required: pd.DataFrame) -> dict:
    """
    Key statistics from the renter income vs. income-required series.
    Flags the 2021 inflection point where the gap spiked.
    """
    df = income_vs_required.copy()

    pre_2021   = df[df["year"] < 2021]
    post_2021  = df[df["year"] >= 2021]

    avg_gap_pre  = round(pre_2021["gap"].mean(), 0)
    avg_gap_post = round(post_2021["gap"].mean(), 0)
    worst_year   = df.loc[df["gap"].idxmin(), "year"]
    worst_gap    = int(df["gap"].min())
    latest_gap   = int(df.iloc[-1]["gap"])
    latest_year  = int(df.iloc[-1]["year"])

    # YoY change in required income in 2021
    req_2020 = int(df.loc[df["year"] == 2020, "income_required"].values[0])
    req_2021 = int(df.loc[df["year"] == 2021, "income_required"].values[0])
    spike_2021 = req_2021 - req_2020

    return {
        "avg_gap_pre_2021":    int(avg_gap_pre),
        "avg_gap_post_2021":   int(avg_gap_post),
        "gap_worsened_by":     int(avg_gap_post - avg_gap_pre),
        "worst_year":          int(worst_year),
        "worst_gap":           worst_gap,
        "latest_year":         latest_year,
        "latest_gap":          latest_gap,
        "income_spike_2021":   spike_2021,       # how much required income jumped in 2021
        "gap_narrowed_since_peak": worst_gap - latest_gap,  # positive = improvement
        "still_unaffordable":  latest_gap < 0,
    }


def rent_growth_stats(median_rent: pd.DataFrame) -> dict:
    """Key rent growth statistics for KPI cards."""
    df  = median_rent.dropna(subset=["yoy_change_pct"])
    peak_row = df.loc[df["yoy_change_pct"].idxmax()]
    first    = int(median_rent.iloc[0]["wake_rent"])
    latest   = int(median_rent.iloc[-1]["wake_rent"])

    return {
        "rent_2015":          first,
        "rent_latest":        latest,
        "latest_year":        int(median_rent.iloc[-1]["year"]),
        "total_growth_pct":   round((latest - first) / first * 100, 1),
        "total_growth_dollars": latest - first,
        "peak_yoy_year":      int(peak_row["year"]),
        "peak_yoy_pct":       float(peak_row["yoy_change_pct"]),
        "peak_yoy_dollars":   int(median_rent.loc[
                                      median_rent["year"] == peak_row["year"],
                                      "yoy_change_dollars"].values[0]),
    }


# ════════════════════════════════════════════════════════════════════════════
# 6. HOMEOWNERSHIP COLLAPSE (entry-level market)
# ════════════════════════════════════════════════════════════════════════════

def entry_level_collapse(homes_sold: pd.DataFrame) -> dict:
    """
    Quantify the disappearance of homes sold under $250K (2018 → 2022).
    """
    row = homes_sold[homes_sold["price_bracket"] == "<$250K"].iloc[0]
    return {
        "pct_under_250k_2018": row["pct_2018"],
        "pct_under_250k_2022": row["pct_2022"],
        "drop_pp":             round(row["shift"], 2),          # percentage points
        "drop_relative_pct":   round(row["shift"] / row["pct_2018"] * 100, 1),
    }


def home_value_growth(median_home_value: pd.DataFrame) -> dict:
    """Key home value appreciation stats for KPI cards."""
    first  = median_home_value.iloc[0]
    latest = median_home_value.iloc[-1]
    return {
        "value_2014":         int(first["wake_value"]),
        "value_latest":       int(latest["wake_value"]),
        "latest_year":        int(latest["year"]),
        "total_growth_pct":   round((latest["wake_value"] - first["wake_value"])
                                    / first["wake_value"] * 100, 1),
        "total_growth_dollars": int(latest["wake_value"] - first["wake_value"]),
    }


# ════════════════════════════════════════════════════════════════════════════
# 7. INCOME POLARIZATION
# ════════════════════════════════════════════════════════════════════════════

def polarization_stats(net_hh_change: pd.DataFrame) -> dict:
    """
    Summary of income polarization: how many lower-income households
    were lost vs. higher-income households gained.
    """
    lost_bands   = net_hh_change[net_hh_change["net_change"] < 0]
    gained_bands = net_hh_change[net_hh_change["net_change"] > 0]

    top_gainer = net_hh_change.loc[net_hh_change["net_change"].idxmax()]
    top_loser  = net_hh_change.loc[net_hh_change["net_change"].idxmin()]

    return {
        "total_hh_lost_low_income":   int(lost_bands["net_change"].sum()),
        "total_hh_gained_high_income": int(gained_bands["net_change"].sum()),
        "n_bands_lost":               len(lost_bands),
        "n_bands_gained":             len(gained_bands),
        "top_gaining_band":           top_gainer["income_band"],
        "top_gaining_count":          int(top_gainer["net_change"]),
        "top_losing_band":            top_loser["income_band"],
        "top_losing_count":           int(top_loser["net_change"]),
        "ratio":                      round(
            abs(gained_bands["net_change"].sum()) /
            abs(lost_bands["net_change"].sum()), 1
        ),
    }


# ════════════════════════════════════════════════════════════════════════════
# 8. VACANCY PRESSURE
# ════════════════════════════════════════════════════════════════════════════

def vacancy_pressure_stats(vacancy: pd.DataFrame) -> dict:
    """Vacancy trend — how far Wake County is from the healthy 5% benchmark."""
    latest = vacancy.iloc[-1]
    first  = vacancy.iloc[0]
    return {
        "latest_year":        int(latest["year"]),
        "latest_wake_pct":    float(latest["wake_pct"]),
        "healthy_benchmark":  5.0,
        "gap_to_healthy":     round(5.0 - latest["wake_pct"], 2),
        "change_since_2014":  round(latest["wake_pct"] - first["wake_pct"], 2),
        "trend":              "declining" if latest["wake_pct"] < first["wake_pct"]
                              else "rising",
    }


# ════════════════════════════════════════════════════════════════════════════
# 9. MASTER ANALYSIS — single call for dashboard
# ════════════════════════════════════════════════════════════════════════════

def run_full_analysis() -> dict:
    """
    Load all data and run every analysis function.
    Returns a single dict consumed by the Streamlit dashboard.
    """
    d = load_all()

    gap_df       = gap_summary(d["supply_demand_gap"], d["affordable_per_100"])
    pace_df      = production_pace_table(gap_df)
    production   = annual_production_df()
    permit_stats = permit_trend_stats(d["building_permits"])
    permits_ann  = permits_with_annotations(d["building_permits"])
    burden_long  = cost_burden_spread(d["cost_burden_by_income"])
    new_crisis   = bands_newly_in_crisis(d["cost_burden_by_income"])
    biggest_jump = biggest_burden_jump(d["cost_burden_by_income"])
    gap_stats    = rent_income_gap_stats(d["income_vs_required"])
    rent_stats   = rent_growth_stats(d["median_rent"])
    entry_lvl    = entry_level_collapse(d["homes_sold_by_price"])
    home_growth  = home_value_growth(d["median_home_value"])
    polar_stats  = polarization_stats(d["net_hh_change"])
    vacancy_stat = vacancy_pressure_stats(d["vacancy_rate"])
    goal_metrics = goal_progress_metrics()

    return {
        # Raw DataFrames
        "gap_df":             gap_df,
        "pace_df":            pace_df,
        "production_df":      production,
        "permits":            permits_ann,
        "burden_long":        burden_long,
        # Scalar metric dicts
        "goal_metrics":       goal_metrics,
        "permit_stats":       permit_stats,
        "new_crisis_bands":   new_crisis,
        "biggest_burden_jump": biggest_jump,
        "rent_income_stats":  gap_stats,
        "rent_stats":         rent_stats,
        "entry_level":        entry_lvl,
        "home_growth":        home_growth,
        "polarization":       polar_stats,
        "vacancy":            vacancy_stat,
        # Raw data pass-through (for charts)
        "supply_demand_gap":  d["supply_demand_gap"],
        "affordable_per_100": d["affordable_per_100"],
        "cost_burden_income": d["cost_burden_by_income"],
        "income_vs_required": d["income_vs_required"],
        "median_rent":        d["median_rent"],
        "building_permits":   d["building_permits"],
        "net_hh_change":      d["net_hh_change"],
        "rental_deficit":     d["rental_deficit"],
        "housing_stock":      d["housing_stock"],
        "rent_by_education":  d["rent_by_education"],
        "median_home_value":  d["median_home_value"],
        "homes_sold_by_price": d["homes_sold_by_price"],
        "vacancy_rate":       d["vacancy_rate"],
        "hacr_constants":     d["hacr_constants"],
    }


# ════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 2 — Analysis Engine Validation")
    print("=" * 60)

    a = run_full_analysis()

    # ── Gap Summary ──────────────────────────────────────────────────────────
    print("\n── 1. Gap Summary by AMI Band ──")
    print(a["gap_df"][["income_threshold", "renter_households",
                        "affordable_units", "gap",
                        "units_per_100", "severity_label"]].to_string(index=False))

    print(f"\n   Total deficit (all bands combined): "
          f"{total_deficit_units(a['gap_df']):,} units")

    # ── Production Pace ──────────────────────────────────────────────────────
    print("\n── 2. Years to Close Gap by AMI Band ──")
    print(a["pace_df"][["income_threshold", "deficit_units",
                         "years_at_current_pace", "years_at_2x_pace",
                         "years_at_5x_pace"]].to_string(index=False))

    # ── Goal Progress ────────────────────────────────────────────────────────
    gm = a["goal_metrics"]
    print("\n── 3. 2029 Production Goal Progress ──")
    print(f"   Goal:           {gm['goal_2029']:,} homes")
    print(f"   Achieved:       {gm['achieved_to_date']:,} ({gm['pct_complete']}%)")
    print(f"   Remaining:      {gm['remaining']:,}")
    print(f"   Required pace:  {gm['required_pace']:,} units/yr")
    print(f"   Current pace:   {gm['current_pace']:,} units/yr")
    print(f"   Pace gap:       {gm['pace_gap']:,} units/yr short")
    print(f"   On track:       {gm['on_track']}")

    # ── Permit Stats ─────────────────────────────────────────────────────────
    ps = a["permit_stats"]
    print("\n── 4. Permit Trend Statistics ──")
    print(f"   Peak year (total):   {ps['peak_year']} ({ps['peak_total']:,} permits)")
    print(f"   Peak MF year:        {ps['peak_mf_year']} ({ps['peak_mf_units']:,} MF units)")
    print(f"   Latest ({ps['latest_year']}):        SF {ps['latest_sf']:,}  MF {ps['latest_mf']:,}  Total {ps['latest_total']:,}")
    print(f"   MF change since peak: {ps['mf_change_since_peak_pct']}%")
    print(f"   Supply gap vs demand: {ps['supply_gap_vs_demand_low']:,} units short of 18k/yr minimum")

    # ── Cost Burden ──────────────────────────────────────────────────────────
    bj = a["biggest_burden_jump"]
    print("\n── 5. Cost Burden Spread ──")
    print(f"   Biggest jump:  {bj['income_band']}  "
          f"{bj['pct_2014']}% → {bj['pct_2024']}%  (+{bj['change']} pp)")
    print(f"   New crisis bands (crossed 50% threshold): {a['new_crisis_bands']}")

    # ── Rent-Income Gap ──────────────────────────────────────────────────────
    ri = a["rent_income_stats"]
    print("\n── 6. Rent–Income Gap ──")
    print(f"   Avg gap pre-2021:   ${ri['avg_gap_pre_2021']:,}/yr")
    print(f"   Avg gap post-2021:  ${ri['avg_gap_post_2021']:,}/yr")
    print(f"   2021 income spike:  +${ri['income_spike_2021']:,} required in one year")
    print(f"   Worst gap year:     {ri['worst_year']}  (${ri['worst_gap']:,})")
    print(f"   Latest ({ri['latest_year']}) gap:  ${ri['latest_gap']:,}")

    # ── Entry-Level Collapse ─────────────────────────────────────────────────
    el = a["entry_level"]
    print("\n── 7. Entry-Level Homeownership ──")
    print(f"   Homes sold <$250K:  {el['pct_under_250k_2018']}% (2018) → "
          f"{el['pct_under_250k_2022']}% (2022)  "
          f"({el['drop_relative_pct']}% relative decline)")

    # ── Polarization ─────────────────────────────────────────────────────────
    po = a["polarization"]
    print("\n── 8. Income Polarization ──")
    print(f"   HHs lost  (<$75K):      {po['total_hh_lost_low_income']:,}")
    print(f"   HHs gained (>$75K):     {po['total_hh_gained_high_income']:,}")
    print(f"   Top gainer: {po['top_gaining_band']} (+{po['top_gaining_count']:,})")
    print(f"   Top loser:  {po['top_losing_band']} ({po['top_losing_count']:,})")
    print(f"   Ratio gained:lost =     {po['ratio']}:1")

    # ── Vacancy ──────────────────────────────────────────────────────────────
    v = a["vacancy"]
    print("\n── 9. Vacancy Pressure ──")
    print(f"   Latest vacancy rate:  {v['latest_wake_pct']}%  "
          f"(healthy benchmark: {v['healthy_benchmark']}%)")
    print(f"   Gap to healthy:       {v['gap_to_healthy']} pp")

    print("\n" + "=" * 60)
    print("All analysis functions passed.")
    print("=" * 60)
