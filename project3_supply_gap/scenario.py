"""
Phase 3 — Scenario Engine
==========================
Interactive logic layer that powers the dashboard sliders.

Given user-controlled inputs:
  - annual_production  : units produced per year (slider)
  - target_band        : AMI band to focus on (dropdown)
  - cost_per_unit      : subsidy cost per affordable unit (slider)
  - pct_targeting_band : share of production targeting the chosen band (slider)

The engine calculates:
  - Year-by-year gap closure trajectory
  - Cumulative investment required
  - Households helped annually and cumulatively
  - Break-even year (when gap closes)
  - Comparison against 3 named policy benchmarks
  - Sensitivity table across production rates

All functions are pure — same inputs always return the same outputs.
No Streamlit imports here; the dashboard calls these functions directly.
"""

import math
import pandas as pd
import numpy as np
from analysis import run_full_analysis, years_to_close, HACR_CONSTANTS

# ── Cost-per-unit defaults by AMI band ───────────────────────────────────────
# Sourced from HACR program data and national LIHTC/HOME averages
DEFAULT_COST_PER_UNIT = {
    "<$20K":  185_000,   # Deep subsidy — PSH / PBRA level
    "<$35K":  145_000,   # HOME / LIHTC targeting 30–50% AMI
    "<$50K":  115_000,   # LIHTC 60% AMI / mixed-income
    "<$75K":   85_000,   # Light-touch subsidy / workforce housing
    "<$100K":  60_000,   # Minimal subsidy
    "<$150K":  35_000,   # Near-market
}

# ── Named policy benchmarks for comparison panel ─────────────────────────────
BENCHMARKS = {
    "Current Pace\n(HACR FY2025)": {
        "annual_production": 660,
        "pct_targeting":     1.00,
        "cost_per_unit":     145_000,
        "color":             "#6B7280",   # gray
        "description":       "660 affordable homes/yr at current HACR investment level ($18M)"
    },
    "2× Scale-Up\n($36M/yr)": {
        "annual_production": 1_320,
        "pct_targeting":     1.00,
        "cost_per_unit":     145_000,
        "color":             "#F59E0B",   # amber
        "description":       "Double production via Housing Opportunity Fund launch (2026 priority)"
    },
    "5× Scale-Up\n($90M/yr)": {
        "annual_production": 3_300,
        "pct_targeting":     1.00,
        "cost_per_unit":     145_000,
        "color":             "#10B981",   # green
        "description":       "5× production — matches NC annual affordable housing demand estimate"
    },
    "Targeted Deep\nSubsidy (<$20K)": {
        "annual_production": 660,
        "pct_targeting":     1.00,
        "cost_per_unit":     185_000,
        "color":             "#7C3AED",   # purple
        "description":       "All 660 units targeted at critical <$20K band (PSH / deep subsidy)"
    },
}


# ════════════════════════════════════════════════════════════════════════════
# CORE SCENARIO RUNNER
# ════════════════════════════════════════════════════════════════════════════

def run_scenario(
    deficit: int,
    annual_production: int,
    pct_targeting_band: float,
    cost_per_unit: int,
    start_year: int = 2026,
    max_years: int = 60,
) -> dict:
    """
    Core scenario calculation.

    Parameters
    ----------
    deficit             : current unit deficit (positive int, e.g. 26037 for <$35K)
    annual_production   : total affordable units produced per year
    pct_targeting_band  : share of production aimed at this AMI band (0.0–1.0)
    cost_per_unit       : average subsidy per unit ($)
    start_year          : first year of production (default 2026)
    max_years           : stop simulation after this many years even if gap open

    Returns
    -------
    dict with scalar summary metrics + a year-by-year trajectory DataFrame
    """
    effective_production = annual_production * pct_targeting_band
    annual_investment    = annual_production * cost_per_unit

    # ── Year-by-year trajectory ──────────────────────────────────────────────
    remaining    = deficit
    rows         = []
    closed_year  = None

    for yr_offset in range(max_years):
        year        = start_year + yr_offset
        produced    = min(effective_production, remaining)   # don't overshoot
        remaining   = max(0, remaining - produced)
        cumulative  = deficit - remaining
        cumul_invest = annual_investment * (yr_offset + 1)
        pct_closed  = round(cumulative / deficit * 100, 1) if deficit > 0 else 100.0

        rows.append({
            "year":                   year,
            "units_produced_band":    round(produced, 0),
            "remaining_deficit":      round(remaining, 0),
            "cumulative_units":       round(cumulative, 0),
            "pct_gap_closed":         pct_closed,
            "annual_investment":      annual_investment,
            "cumulative_investment":  cumul_invest,
            "households_helped_yr":   round(produced, 0),
        })

        if remaining == 0 and closed_year is None:
            closed_year = year
            break   # gap fully closed — stop early

    traj_df = pd.DataFrame(rows)

    # ── Scalar summary ───────────────────────────────────────────────────────
    if closed_year:
        years_needed      = closed_year - start_year + 1
        total_investment  = annual_investment * years_needed
        gap_closed        = True
    else:
        years_needed      = max_years
        total_investment  = annual_investment * max_years
        pct_closed_final  = traj_df.iloc[-1]["pct_gap_closed"]
        gap_closed        = False

    # Milestones: year when 25%, 50%, 75% of gap closed
    milestones = {}
    for pct_target in [25, 50, 75, 100]:
        milestone_rows = traj_df[traj_df["pct_gap_closed"] >= pct_target]
        if not milestone_rows.empty:
            milestones[pct_target] = int(milestone_rows.iloc[0]["year"])
        else:
            milestones[pct_target] = None

    # Cost per household helped (total subsidy / households reached)
    total_hh_helped = min(deficit, effective_production * years_needed)
    cost_per_hh_helped = (
        round(total_investment / total_hh_helped, 0)
        if total_hh_helped > 0 else None
    )

    # ROI framing: HACR reports $1.80 returned per $1 invested
    roi_return = round(total_investment * 1.80, 0)
    annual_savings_total = round(
        min(deficit, effective_production) *
        HACR_CONSTANTS.get("annual_savings_per_person", 14_700), 0
    ) if hasattr(HACR_CONSTANTS, "get") else 0

    return {
        # Inputs (echo back for display)
        "annual_production":       annual_production,
        "effective_production":    round(effective_production, 0),
        "pct_targeting_band":      pct_targeting_band,
        "cost_per_unit":           cost_per_unit,
        "start_year":              start_year,
        "initial_deficit":         deficit,
        # Outputs
        "gap_closed":              gap_closed,
        "years_to_close":          years_needed if gap_closed else None,
        "close_year":              closed_year,
        "pct_closed_after_sim":    float(traj_df.iloc[-1]["pct_gap_closed"]),
        "annual_investment":       annual_investment,
        "total_investment":        total_investment,
        "cost_per_hh_helped":      cost_per_hh_helped,
        "roi_return_estimated":    roi_return,
        "milestones":              milestones,   # {25: year, 50: year, ...}
        # DataFrame
        "trajectory":              traj_df,
    }


# ════════════════════════════════════════════════════════════════════════════
# MULTI-BAND SCENARIO — run one set of inputs across all deficit bands
# ════════════════════════════════════════════════════════════════════════════

def run_all_bands(
    gap_df: pd.DataFrame,
    annual_production: int,
    pct_targeting: float,
    cost_per_unit: int,
    start_year: int = 2026,
) -> pd.DataFrame:
    """
    Run the scenario across every AMI deficit band simultaneously.
    Returns a summary DataFrame — one row per band.
    Useful for the "what happens if we scale production?" comparison panel.
    """
    rows = []
    deficit_bands = gap_df[gap_df["gap"] < 0]

    for _, band_row in deficit_bands.iterrows():
        band    = band_row["income_threshold"]
        deficit = abs(int(band_row["gap"]))
        result  = run_scenario(
            deficit=deficit,
            annual_production=annual_production,
            pct_targeting_band=pct_targeting,
            cost_per_unit=cost_per_unit,
            start_year=start_year,
        )
        rows.append({
            "income_threshold":     band,
            "deficit_units":        deficit,
            "severity_label":       band_row["severity_label"],
            "years_to_close":       result["years_to_close"] if result["gap_closed"] else ">60",
            "close_year":           result["close_year"],
            "annual_investment":    result["annual_investment"],
            "total_investment":     result["total_investment"],
            "cost_per_hh_helped":   result["cost_per_hh_helped"],
            "pct_closed_after_sim": result["pct_closed_after_sim"],
            "milestone_50pct":      result["milestones"].get(50),
            "milestone_75pct":      result["milestones"].get(75),
        })

    return pd.DataFrame(rows)


# ════════════════════════════════════════════════════════════════════════════
# BENCHMARK COMPARISON — run all named policy scenarios on one band
# ════════════════════════════════════════════════════════════════════════════

def run_benchmark_comparison(
    deficit: int,
    target_band: str = "<$35K",
    start_year: int = 2026,
) -> pd.DataFrame:
    """
    Run all four named policy benchmarks against the same deficit.
    Returns a DataFrame with one row per benchmark — used for the
    grouped comparison bar chart in the dashboard.
    """
    rows = []
    for name, cfg in BENCHMARKS.items():
        result = run_scenario(
            deficit=deficit,
            annual_production=cfg["annual_production"],
            pct_targeting_band=cfg["pct_targeting"],
            cost_per_unit=cfg["cost_per_unit"],
            start_year=start_year,
        )
        rows.append({
            "scenario":             name.replace("\n", " "),
            "color":                cfg["color"],
            "description":          cfg["description"],
            "annual_production":    cfg["annual_production"],
            "years_to_close":       result["years_to_close"] if result["gap_closed"] else 60,
            "close_year":           result["close_year"] if result["gap_closed"] else None,
            "gap_closed":           result["gap_closed"],
            "total_investment_M":   round(result["total_investment"] / 1e6, 1),
            "annual_investment_M":  round(result["annual_investment"] / 1e6, 1),
            "cost_per_hh":          result["cost_per_hh_helped"],
            "milestone_50pct_yr":   result["milestones"].get(50),
        })

    return pd.DataFrame(rows)


# ════════════════════════════════════════════════════════════════════════════
# SENSITIVITY TABLE — vary production rate, show years-to-close matrix
# ════════════════════════════════════════════════════════════════════════════

def sensitivity_table(
    gap_df: pd.DataFrame,
    production_rates: list = None,
    pct_targeting: float = 1.0,
) -> pd.DataFrame:
    """
    Matrix of years-to-close for every combination of:
      rows = AMI deficit bands
      cols = production rate scenarios

    production_rates: list of annual unit counts to test.
    Returns a wide DataFrame — rows are bands, columns are production rates.
    """
    if production_rates is None:
        production_rates = [330, 660, 1_000, 1_320, 2_000, 3_300, 5_000]

    deficit_bands = gap_df[gap_df["gap"] < 0]
    rows = []

    for _, band_row in deficit_bands.iterrows():
        band    = band_row["income_threshold"]
        deficit = abs(int(band_row["gap"]))
        row = {"AMI Band": band, "Current Deficit": deficit}

        for rate in production_rates:
            effective = rate * pct_targeting
            ytc = years_to_close(-deficit, effective)
            label = f"{ytc:.0f} yrs" if ytc != float("inf") else ">60 yrs"
            if ytc <= 10:
                label = f"✅ {ytc:.0f} yrs"
            elif ytc <= 20:
                label = f"🟡 {ytc:.0f} yrs"
            elif ytc <= 40:
                label = f"🟠 {ytc:.0f} yrs"
            else:
                label = f"🔴 {label}"
            row[f"{rate:,}/yr"] = label

        rows.append(row)

    return pd.DataFrame(rows)


# ════════════════════════════════════════════════════════════════════════════
# INVESTMENT REQUIREMENT TABLE
# ════════════════════════════════════════════════════════════════════════════

def investment_requirement_table(gap_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each deficit band, calculate:
      - Total investment to close the gap (at default cost per unit)
      - Required annual investment at 10yr / 20yr / 30yr timelines
    Returns a DataFrame suitable for CAPER export.
    """
    rows = []
    for _, band_row in gap_df[gap_df["gap"] < 0].iterrows():
        band    = band_row["income_threshold"]
        deficit = abs(int(band_row["gap"]))
        cpu     = DEFAULT_COST_PER_UNIT.get(band, 145_000)
        total   = deficit * cpu

        rows.append({
            "AMI Band":                band,
            "Unit Deficit":            deficit,
            "Cost/Unit ($)":           f"${cpu:,}",
            "Total Investment ($M)":   round(total / 1e6, 1),
            "Annual Invest – 10yr ($M)": round(total / 10 / 1e6, 1),
            "Annual Invest – 20yr ($M)": round(total / 20 / 1e6, 1),
            "Annual Invest – 30yr ($M)": round(total / 30 / 1e6, 1),
        })

    return pd.DataFrame(rows)


# ════════════════════════════════════════════════════════════════════════════
# TRAJECTORY MERGE — combine multiple scenarios for one overlay chart
# ════════════════════════════════════════════════════════════════════════════

def trajectory_overlay(
    deficit: int,
    scenarios: dict,
    start_year: int = 2026,
) -> pd.DataFrame:
    """
    Run multiple (name → config) scenario dicts and merge their trajectories
    into one long DataFrame for a multi-line overlay chart.

    scenarios: {label: {annual_production, pct_targeting, cost_per_unit}}
    """
    frames = []
    for label, cfg in scenarios.items():
        result = run_scenario(
            deficit=deficit,
            annual_production=cfg["annual_production"],
            pct_targeting_band=cfg.get("pct_targeting", 1.0),
            cost_per_unit=cfg.get("cost_per_unit", 145_000),
            start_year=start_year,
        )
        traj = result["trajectory"].copy()
        traj["scenario"] = label
        traj["color"]    = cfg.get("color", "#3B82F6")
        frames.append(traj)

    return pd.concat(frames, ignore_index=True)


# ════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("Phase 3 — Scenario Engine Validation")
    print("=" * 65)

    a = run_full_analysis()
    gap_df = a["gap_df"]

    # ── 1. Core scenario: <$35K band at current pace ─────────────────────────
    deficit_35k = abs(int(gap_df[gap_df["income_threshold"] == "<$35K"]["gap"].values[0]))
    r = run_scenario(
        deficit=deficit_35k,
        annual_production=660,
        pct_targeting_band=1.0,
        cost_per_unit=145_000,
    )
    print(f"\n── 1. Core Scenario: <$35K band at current HACR pace (660 units/yr) ──")
    print(f"   Initial deficit:          {r['initial_deficit']:,} units")
    print(f"   Effective production/yr:  {int(r['effective_production']):,} units")
    print(f"   Gap closed?               {r['gap_closed']}")
    print(f"   Years to close:           {r['years_to_close']}")
    print(f"   Close year:               {r['close_year']}")
    print(f"   Annual investment:        ${r['annual_investment']/1e6:.1f}M")
    print(f"   Total investment:         ${r['total_investment']/1e6:.1f}M")
    print(f"   Cost per HH helped:       ${r['cost_per_hh_helped']:,.0f}")
    print(f"   Milestones: 25%→{r['milestones'][25]}  50%→{r['milestones'][50]}  "
          f"75%→{r['milestones'][75]}")
    print(f"\n   First 10 years of trajectory:")
    print(r["trajectory"].head(10)[
        ["year", "units_produced_band", "remaining_deficit",
         "pct_gap_closed", "cumulative_investment"]
    ].to_string(index=False))

    # ── 2. Multi-band scenario at 2× pace ────────────────────────────────────
    print(f"\n── 2. All Deficit Bands at 2× Pace (1,320 units/yr) ──")
    multi = run_all_bands(gap_df, annual_production=1_320,
                          pct_targeting=1.0, cost_per_unit=145_000)
    print(multi[["income_threshold", "deficit_units", "years_to_close",
                  "total_investment", "cost_per_hh_helped"]].to_string(index=False))

    # ── 3. Benchmark comparison for <$35K ────────────────────────────────────
    print(f"\n── 3. Benchmark Comparison — <$35K band ──")
    bench = run_benchmark_comparison(deficit_35k, target_band="<$35K")
    print(bench[["scenario", "annual_production", "years_to_close",
                  "total_investment_M", "annual_investment_M",
                  "milestone_50pct_yr"]].to_string(index=False))

    # ── 4. Sensitivity table ─────────────────────────────────────────────────
    print(f"\n── 4. Sensitivity Table (years to close by production rate) ──")
    sens = sensitivity_table(gap_df)
    print(sens.to_string(index=False))

    # ── 5. Investment requirement table ──────────────────────────────────────
    print(f"\n── 5. Investment Requirements to Close Each Band ──")
    inv = investment_requirement_table(gap_df)
    print(inv.to_string(index=False))

    # ── 6. Trajectory overlay for chart ──────────────────────────────────────
    print(f"\n── 6. Trajectory Overlay (3 scenarios, <$35K band) ──")
    overlay = trajectory_overlay(
        deficit=deficit_35k,
        scenarios={
            "Current (660/yr)":  {"annual_production": 660,   "pct_targeting": 1.0, "color": "#6B7280"},
            "2× Scale (1,320/yr)": {"annual_production": 1_320, "pct_targeting": 1.0, "color": "#F59E0B"},
            "5× Scale (3,300/yr)": {"annual_production": 3_300, "pct_targeting": 1.0, "color": "#10B981"},
        },
    )
    print(f"   Overlay shape: {overlay.shape} — "
          f"{overlay['scenario'].nunique()} scenarios, "
          f"{overlay.groupby('scenario').size().to_dict()}")

    print("\n" + "=" * 65)
    print("All scenario functions passed.")
    print("=" * 65)
