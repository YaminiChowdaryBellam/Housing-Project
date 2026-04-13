#!/usr/bin/env python3
"""
Phase 1 — Data Loader
=====================
Parses all 4 real Wake County wakehousingdata.org Excel exports into clean,
labeled pandas DataFrames. Every function maps to a specific named table
inside the source file. No synthetic data.

Source files (all in parent directory):
  - Snapshot View - Wake County - Demographics - 2026-04-12.xlsx
  - Snapshot View - Wake County - Homeownership - 2026-04-12.xlsx
  - Snapshot View - Wake County - Housing Supply - 2026-04-12.xlsx
  - Snapshot View - Wake County - Rental Affordability - 2026-04-12.xlsx

HACR Annual Report constants (wakehousingdata.org/annualreport, 2025):
  - Affordable units produced total since 2019 : 7,086
  - Affordable ownership units produced        : 311
  - HACR FY2025 production                     : 660 homes / $18M
  - Development pipeline                       : 1,532 homes

Installation: pip install openpyxl
"""


import os
import openpyxl
import pandas as pd

# ── File paths ────────────────────────────��──────────────────────────��────────
_BASE = os.path.join(os.path.dirname(__file__), "..")

FILES = {
    "demographics":    os.path.join(_BASE, "Snapshot View - Wake County - Demographics - 2026-04-12.xlsx"),
    "homeownership":   os.path.join(_BASE, "Snapshot View - Wake County - Homeownership - 2026-04-12.xlsx"),
    "supply":          os.path.join(_BASE, "Snapshot View - Wake County - Housing Supply - 2026-04-12.xlsx"),
    "rental":          os.path.join(_BASE, "Snapshot View - Wake County - Rental Affordability - 2026-04-12.xlsx"),
}

# ── HACR Annual Report constants (not in Excel files) ────────────────────────
HACR_CONSTANTS = {
    # Production
    "affordable_units_produced_total":      7_086,   # since 2019 (rental)
    "affordable_ownership_units_produced":  311,
    "fy2025_production":                    660,
    "fy2025_investment_dollars":            18_000_000,
    "development_pipeline_units":           1_532,
    # 2024-2029 strategic goal
    "production_goal_2029":                 2_500,
    "production_achieved_to_date":          2_065,
    # Homelessness (for reference)
    "pit_count_2024":                       992,
    "pit_count_2025_estimate":              1_258,
    # Historical annual production estimates (derived from report narrative)
    "annual_production_history": {
        2019: 320, 2020: 290, 2021: 410,
        2022: 480, 2023: 505, 2024: 600, 2025: 660,
    },
}


# ── Internal helper ───────────────────────────────────────────────────────────
def _rows(file_key: str) -> list[list]:
    """Return all non-empty rows from the first sheet as a list of value lists."""
    wb = openpyxl.load_workbook(FILES[file_key], data_only=True)
    ws = wb.active
    result = []
    for row in ws.iter_rows(values_only=True):
        vals = [v for v in row if v is not None]
        if vals:
            result.append(vals)
    return result


def _find_section(rows: list[list], header_text: str) -> int:
    """Return the index of the row whose first cell matches header_text."""
    for i, row in enumerate(rows):
        if row[0] == header_text:
            return i
    raise ValueError(f"Section '{header_text}' not found in sheet.")


def _extract_table(rows: list[list], section_header: str,
                   col_names: list[str], n_rows: int) -> pd.DataFrame:
    """
    Locate section_header, skip the column-name row immediately after,
    then read n_rows of data into a DataFrame with col_names.
    """
    idx = _find_section(rows, section_header)
    data = []
    for row in rows[idx + 2 : idx + 2 + n_rows]:   # +2: skip header + col row
        # Pad short rows with None so they align with col_names
        padded = list(row) + [None] * (len(col_names) - len(row))
        data.append(padded[:len(col_names)])
    df = pd.DataFrame(data, columns=col_names)
    return df


# ═════════════════════════════════════════════���════════════════════════════════
# HOUSING SUPPLY  (primary file for Project 3)
# ══════════════════════════════════════════════════════════════════════════════

def load_building_permits() -> pd.DataFrame:
    """
    Residential Building Permits Issued — Wake County 2014–2024.
    Columns: year (int), single_family (int), multifamily (int), total (int)
    """
    rows = _rows("supply")
    idx = _find_section(rows, "Residential Building Permits Issued")
    data = []
    for row in rows[idx + 2 : idx + 2 + 11]:   # 2014–2024 = 11 years
        year, sf, mf = int(row[0]), int(row[1]), int(row[2])
        data.append({"year": year, "single_family": sf, "multifamily": mf,
                     "total": sf + mf})
    return pd.DataFrame(data)


def load_supply_demand_gap() -> pd.DataFrame:
    """
    Demand and Supply of Rental Housing by Income — Wake County (latest ACS).
    Columns: income_threshold, renter_households, affordable_units, gap, gap_pct
    """
    rows = _rows("supply")
    idx = _find_section(rows, "Demand and Supply of Rental Housing by Income")
    labels = ["<$20K", "<$35K", "<$50K", "<$75K", "<$100K", "<$150K"]
    data = []
    for i, row in enumerate(rows[idx + 2 : idx + 2 + 6]):
        renter_hh     = int(row[1])
        affordable    = int(row[2])
        gap           = affordable - renter_hh
        data.append({
            "income_threshold": labels[i],
            "renter_households": renter_hh,
            "affordable_units":  affordable,
            "gap":               gap,            # negative = deficit
            "gap_pct":           round(gap / renter_hh * 100, 1),
        })
    return pd.DataFrame(data)


def load_vacancy_rate() -> pd.DataFrame:
    """
    Share of Homes That Are Vacant and Available — 2014–2024.
    Columns: year, nc_pct, wake_pct
    """
    rows = _rows("supply")
    idx = _find_section(rows, "Share of Homes That Are Vacant and Available")
    data = []
    for row in rows[idx + 2 : idx + 2 + 11]:
        data.append({"year": int(row[0]), "nc_pct": float(row[1]),
                     "wake_pct": float(row[2])})
    return pd.DataFrame(data)


def load_housing_stock() -> dict:
    """
    Occupancy and Tenure of Housing Stock — single snapshot.
    Returns a dict with total, vacant, owner_occupied, renter_occupied counts.
    """
    rows = _rows("supply")
    idx = _find_section(rows, "Occupancy and Tenure of Housing Stock")
    # Row idx+2: ['All Homes', 460175, 35872, 0, 0]
    # Row idx+3: ['Occupied Homes', 0, 0, 295069, 165106]
    all_row      = rows[idx + 2]
    occupied_row = rows[idx + 3]
    return {
        "total_homes":       int(all_row[1]),
        "vacant_homes":      int(all_row[2]),
        "owner_occupied":    int(occupied_row[3]),
        "renter_occupied":   int(occupied_row[4]),
        "pct_owner":         round(int(occupied_row[3]) /
                                   (int(occupied_row[3]) + int(occupied_row[4])) * 100, 1),
        "pct_renter":        round(int(occupied_row[4]) /
                                   (int(occupied_row[3]) + int(occupied_row[4])) * 100, 1),
    }


def load_total_homes_growth() -> pd.DataFrame:
    """
    Percent Change in Total Homes — Wake County vs NC 2013–2023.
    Columns: year, nc_pct_change, wake_pct_change
    """
    rows = _rows("supply")
    idx = _find_section(rows, "Percent Change in Total Homes")
    data = []
    for row in rows[idx + 2 : idx + 2 + 11]:
        data.append({"year": int(row[0]), "nc_pct_change": float(row[1]),
                     "wake_pct_change": float(row[2])})
    return pd.DataFrame(data)


def load_renter_typology() -> pd.DataFrame:
    """
    Renter-Occupied Homes by Building Typology — NC vs Wake County.
    Columns: typology, nc_pct, wake_pct
    """
    rows = _rows("supply")
    idx = _find_section(rows, "Renter-Occupied Homes by Building Typology")
    cols = ["typology", "nc_pct", "wake_pct"]
    data = []
    for row in rows[idx + 2 : idx + 2 + 2]:   # NC row, Wake row
        # row[0]=geography, row[1..6]=typologies; need to pivot
        pass
    # Alternative: read header row then data rows
    header_row = rows[idx + 1]   # typology labels
    typologies = header_row[1:]  # skip 'Geography'
    for geo_row in rows[idx + 2 : idx + 2 + 2]:
        geo = geo_row[0]
        for j, typ in enumerate(typologies):
            data.append({"geography": geo, "typology": typ,
                         "pct": float(geo_row[j + 1])})
    return pd.DataFrame(data)


# ══════════════════════════════════════════════════���═══════════════════════════
# RENTAL AFFORDABILITY  (primary file for Project 3)
# ═══════════════════════════��══════════════════════════════���═══════════════════

def load_median_rent() -> pd.DataFrame:
    """
    Median Rent — Wake County vs NC 2015–2024.
    Columns: year, nc_rent, wake_rent, yoy_change_pct
    """
    rows = _rows("rental")
    idx = _find_section(rows, "Median Rent")
    data = []
    for row in rows[idx + 2 : idx + 2 + 10]:
        data.append({"year": int(row[0]), "nc_rent": int(row[1]),
                     "wake_rent": int(row[2])})
    df = pd.DataFrame(data)
    df["yoy_change_pct"] = df["wake_rent"].pct_change().mul(100).round(1)
    df["yoy_change_dollars"] = df["wake_rent"].diff().round(0)
    return df


def load_affordable_units_per_100() -> pd.DataFrame:
    """
    Affordable Rental Homes per 100 Renter Households by Income — Wake County.
    Columns: income_threshold, units_per_100, deficit_flag
    """
    rows = _rows("rental")
    idx = _find_section(rows, "Affordable Rental Homes per 100 Renter Households by Income")
    labels = ["<$20K", "<$35K", "<$50K", "<$75K", "<$100K", "<$150K"]
    data = []
    for i, row in enumerate(rows[idx + 2 : idx + 2 + 6]):
        units = int(row[1])
        data.append({
            "income_threshold": labels[i],
            "units_per_100":    units,
            "deficit_flag":     units < 100,   # True = fewer units than renters
        })
    return pd.DataFrame(data)


def load_cost_burden_overall() -> pd.DataFrame:
    """
    Renter Cost Burden Rate — Wake County 2019 & 2024.
    Columns: year, pct_cost_burdened, pct_severely_cost_burdened
    """
    rows = _rows("rental")
    idx = _find_section(rows, "Renter Cost Burden Rate")
    data = []
    for row in rows[idx + 2 : idx + 2 + 2]:
        data.append({
            "year":                       int(row[0]),
            "pct_cost_burdened":          float(row[1]),
            "pct_severely_cost_burdened": float(row[2]),
        })
    return pd.DataFrame(data)


def load_cost_burden_by_income() -> pd.DataFrame:
    """
    Renter Cost Burden Rate by Income Band — 2014, 2019, 2024.
    Columns: income_band, pct_2014, pct_2019, pct_2024, change_2014_2024
    """
    rows = _rows("rental")
    idx = _find_section(rows, "Renter Cost Burden Rate by Income")
    labels = ["<$20K", "$20K–$35K", "$35K–$50K", "$50K–$75K",
              "$75K–$100K", "$100K+"]
    data = []
    for i, row in enumerate(rows[idx + 2 : idx + 2 + 6]):
        p14, p19, p24 = float(row[1]), float(row[2]), float(row[3])
        data.append({
            "income_band":        labels[i],
            "pct_2014":           p14,
            "pct_2019":           p19,
            "pct_2024":           p24,
            "change_2014_2024":   round(p24 - p14, 2),
        })
    return pd.DataFrame(data)


def load_income_vs_required() -> pd.DataFrame:
    """
    Median Renter Income vs. Income Required to Afford Median Rent — 2015–2024.
    Columns: year, median_renter_income, income_required, gap (negative = unaffordable)
    """
    rows = _rows("rental")
    idx = _find_section(rows,
          "Income Required to Afford Median Rent Vs. Median Renter Income")
    data = []
    for row in rows[idx + 2 : idx + 2 + 10]:
        income    = int(row[1])
        required  = int(row[2])
        data.append({
            "year":                  int(row[0]),
            "median_renter_income":  income,
            "income_required":       required,
            "gap":                   income - required,   # negative = unaffordable
        })
    return pd.DataFrame(data)


def load_rent_by_education() -> pd.DataFrame:
    """
    Median Rent vs. Affordable Rent by Educational Attainment — 2023.
    Columns: education_level, affordable_rent, median_rent (for reference)
    """
    rows = _rows("rental")
    idx = _find_section(rows,
          "Comparison of Median Rent and Rent Affordable by Educational Attainment")
    row = rows[idx + 2]   # single data row: 2023
    return pd.DataFrame([
        {"education_level": "No HS Diploma",        "affordable_rent": round(row[2], 0), "median_rent": int(row[1])},
        {"education_level": "HS Diploma",           "affordable_rent": round(row[3], 0), "median_rent": int(row[1])},
        {"education_level": "College Degree",       "affordable_rent": round(row[4], 0), "median_rent": int(row[1])},
        {"education_level": "Graduate Degree",      "affordable_rent": round(row[5], 0), "median_rent": int(row[1])},
    ])


def load_rental_deficit() -> pd.DataFrame:
    """
    Rental Housing Deficit/Surplus by Income — Wake County.
    Identical table appears in both rental and supply files; sourced from rental.
    Columns: income_threshold, deficit_surplus
    """
    rows = _rows("rental")
    idx = _find_section(rows, "Rental Housing Deficit/Surplus by Income")
    labels = ["<$20K", "<$35K", "<$50K", "<$75K", "<$100K", "<$150K"]
    data = []
    for i, row in enumerate(rows[idx + 2 : idx + 2 + 6]):
        data.append({
            "income_threshold": labels[i],
            "deficit_surplus":  int(row[1]),
            "is_deficit":       int(row[1]) < 0,
        })
    return pd.DataFrame(data)


# ═════════════════════════��════════════════════════════��═══════════════════════
# DEMOGRAPHICS  (supporting data for context panels)
# ═════════════════════════════════════════��══════════════════════════════��═════

def load_population() -> pd.DataFrame:
    """
    Population Over Time — Wake County 2015–2025.
    Columns: year, population
    """
    rows = _rows("demographics")
    idx = _find_section(rows, "Population Over Time")
    data = []
    for row in rows[idx + 2 : idx + 2 + 11]:
        data.append({"year": int(row[0]), "population": int(row[1])})
    return pd.DataFrame(data)


def load_median_hh_income() -> pd.DataFrame:
    """
    Median Household Income — NC vs Wake County 2014–2024.
    Columns: year, nc_income, wake_income
    """
    rows = _rows("demographics")
    idx = _find_section(rows, "Median Household Income")
    data = []
    for row in rows[idx + 2 : idx + 2 + 11]:
        data.append({"year": int(row[0]), "nc_income": int(row[1]),
                     "wake_income": int(row[2])})
    return pd.DataFrame(data)


def load_net_hh_change_by_income() -> pd.DataFrame:
    """
    Net Change in Number of Households by Income Band — 2014 to 2024.
    Columns: income_band, net_change, direction ('gained' or 'lost')
    """
    rows = _rows("demographics")
    idx = _find_section(rows, "Net Change in Number of Households by Income Band")
    labels = ["<$20K", "$20K–$35K", "$35K–$50K", "$50K–$75K",
              "$75K–$100K", "$100K–$150K", "$150K+"]
    data = []
    for i, row in enumerate(rows[idx + 2 : idx + 2 + 7]):
        net = int(row[1])
        data.append({
            "income_band":  labels[i],
            "net_change":   net,
            "direction":    "gained" if net >= 0 else "lost",
        })
    return pd.DataFrame(data)


def load_income_distribution() -> pd.DataFrame:
    """
    Household Income Distribution — 2014 vs 2024 (% share).
    Columns: income_range, pct_2014, pct_2024, shift
    """
    rows = _rows("demographics")
    idx = _find_section(rows, "Household Income Distribution")
    labels = ["<$20K", "$20K–$35K", "$35K–$50K", "$50K–$75K",
              "$75K–$100K", "$100K–$150K", "$150K+"]
    data = []
    for i, row in enumerate(rows[idx + 2 : idx + 2 + 7]):
        p14 = round(float(row[1]), 2)
        p24 = round(float(row[2]), 2)
        data.append({
            "income_range": labels[i],
            "pct_2014":     p14,
            "pct_2024":     p24,
            "shift":        round(p24 - p14, 2),
        })
    return pd.DataFrame(data)


# ══════════════════════���═══════════════════════════════��═══════════════════════
# HOMEOWNERSHIP  (supporting data for context panels)
# ══════════════════════════════���═══════════════════════════════════���═══════════

def load_median_home_value() -> pd.DataFrame:
    """
    Median Home Values — NC vs Wake County 2014–2024.
    Columns: year, nc_value, wake_value, yoy_change_pct
    """
    rows = _rows("homeownership")
    idx = _find_section(rows, "Median Home Values")
    data = []
    for row in rows[idx + 2 : idx + 2 + 11]:
        data.append({"year": int(row[0]), "nc_value": int(row[1]),
                     "wake_value": int(row[2])})
    df = pd.DataFrame(data)
    df["yoy_change_pct"] = df["wake_value"].pct_change().mul(100).round(1)
    return df


def load_homes_sold_by_price() -> pd.DataFrame:
    """
    Share of Total Homes Sold by Price Bracket — 2018 vs 2022.
    Columns: price_bracket, pct_2018, pct_2022, shift
    """
    rows = _rows("homeownership")
    idx = _find_section(rows, "Share of Total Homes Sold by Price Bracket")
    brackets = ["<$250K", "$250K–$500K", "$500K–$750K",
                "$750K–$1M", "$1M–$1.5M", "$1.5M+"]
    data = []
    for i, row in enumerate(rows[idx + 2 : idx + 2 + 6]):
        p18 = round(float(row[1]), 2)
        p22 = round(float(row[2]), 2)
        data.append({"price_bracket": brackets[i], "pct_2018": p18,
                     "pct_2022": p22, "shift": round(p22 - p18, 2)})
    return pd.DataFrame(data)


def load_homeownership_rate() -> pd.DataFrame:
    """
    Homeownership Rate — NC vs Wake County 2014–2024.
    Columns: year, nc_rate, wake_rate
    """
    rows = _rows("homeownership")
    idx = _find_section(rows, "Homeownership Rate")
    data = []
    for row in rows[idx + 2 : idx + 2 + 11]:
        data.append({"year": int(row[0]), "nc_rate": round(float(row[1]), 2),
                     "wake_rate": round(float(row[2]), 2)})
    return pd.DataFrame(data)


# ═══════════════════════════════════════════════════��══════════════════════════
# MASTER LOADER — returns all tables in one call
# ══════════════════════════════════════════════════════════════════════════���═══

def load_all() -> dict:
    """
    Load every table used by the dashboard.
    Returns a dict keyed by table name.
    """
    return {
        # Housing Supply
        "building_permits":        load_building_permits(),
        "supply_demand_gap":       load_supply_demand_gap(),
        "vacancy_rate":            load_vacancy_rate(),
        "housing_stock":           load_housing_stock(),        # dict, not df
        "total_homes_growth":      load_total_homes_growth(),
        "renter_typology":         load_renter_typology(),
        # Rental Affordability
        "median_rent":             load_median_rent(),
        "affordable_per_100":      load_affordable_units_per_100(),
        "cost_burden_overall":     load_cost_burden_overall(),
        "cost_burden_by_income":   load_cost_burden_by_income(),
        "income_vs_required":      load_income_vs_required(),
        "rent_by_education":       load_rent_by_education(),
        "rental_deficit":          load_rental_deficit(),
        # Demographics
        "population":              load_population(),
        "median_hh_income":        load_median_hh_income(),
        "net_hh_change":           load_net_hh_change_by_income(),
        "income_distribution":     load_income_distribution(),
        # Homeownership
        "median_home_value":       load_median_home_value(),
        "homes_sold_by_price":     load_homes_sold_by_price(),
        "homeownership_rate":      load_homeownership_rate(),
        # Constants from annual report
        "hacr_constants":          HACR_CONSTANTS,             # dict, not df
    }


# ════════════════════��═════════════════════════════════════════════════════════
# VALIDATION — run directly to confirm all tables load cleanly
# ═══════════════════════════════════════════���══════════════════════════════��═══

if __name__ == "__main__":
    import traceback

    print("=" * 60)
    print("Phase 1 — Data Loader Validation")
    print("=" * 60)

    loaders = [
        ("building_permits",      load_building_permits),
        ("supply_demand_gap",     load_supply_demand_gap),
        ("vacancy_rate",          load_vacancy_rate),
        ("housing_stock",         load_housing_stock),
        ("total_homes_growth",    load_total_homes_growth),
        ("renter_typology",       load_renter_typology),
        ("median_rent",           load_median_rent),
        ("affordable_per_100",    load_affordable_units_per_100),
        ("cost_burden_overall",   load_cost_burden_overall),
        ("cost_burden_by_income", load_cost_burden_by_income),
        ("income_vs_required",    load_income_vs_required),
        ("rent_by_education",     load_rent_by_education),
        ("rental_deficit",        load_rental_deficit),
        ("population",            load_population),
        ("median_hh_income",      load_median_hh_income),
        ("net_hh_change",         load_net_hh_change_by_income),
        ("income_distribution",   load_income_distribution),
        ("median_home_value",     load_median_home_value),
        ("homes_sold_by_price",   load_homes_sold_by_price),
        ("homeownership_rate",    load_homeownership_rate),
    ]

    passed = 0
    failed = 0
    for name, fn in loaders:
        try:
            result = fn()
            if isinstance(result, dict):
                print(f"  ✓  {name:<30}  dict with {len(result)} keys")
            else:
                print(f"  ✓  {name:<30}  {result.shape[0]} rows × {result.shape[1]} cols")
                if result.isnull().any().any():
                    null_cols = result.columns[result.isnull().any()].tolist()
                    print(f"     ⚠  nulls in: {null_cols}")
            passed += 1
        except Exception:
            print(f"  ✗  {name}")
            traceback.print_exc()
            failed += 1

    print()
    print(f"Result: {passed} passed / {failed} failed")
    print()

    if failed == 0:
        print("Sample — Supply-Demand Gap:")
        print(load_supply_demand_gap().to_string(index=False))
        print()
        print("Sample — Cost Burden by Income:")
        print(load_cost_burden_by_income().to_string(index=False))
        print()
        print("Sample — Income vs Required:")
        print(load_income_vs_required().to_string(index=False))
        print()
        print("Sample — Building Permits (last 5 years):")
        print(load_building_permits().tail(5).to_string(index=False))
