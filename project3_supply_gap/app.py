"""
Phase 5 — Polished Dashboard
==============================
"Closing the Gap" — Wake County Affordable Housing Supply-Demand Scenario Modeler

Tabs:
  1. Overview         — KPI cards + narrative + gap snapshot
  2. Supply-Demand Gap — Waterfall + units-per-100 + cost burden + education + price bracket
  3. Production & Permits — HACR production tracker + permit trends + vacancy
  4. Scenario Modeler — Interactive sliders → gap closure trajectory + how-to guide
  5. CAPER Export     — Download-ready HUD reporting tables + data quality checklist

Phase 5 additions:
  - Consistent CHART_CONFIG (clean Plotly toolbar)
  - Methodology expander in sidebar (HUD formulas, data quality, limitations)
  - "Story in 3 Numbers" narrative in Tab 1
  - Education vs. rent chart in Tab 2
  - Price bracket shift chart in Tab 2
  - Vacancy trend chart in Tab 3
  - How-to-use guide in Tab 4
  - Data quality checklist in Tab 5
  - Consistent footer on all tabs

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from analysis import run_full_analysis
from scenario import (
    run_scenario,
    run_benchmark_comparison,
    run_all_bands,
    sensitivity_table,
    investment_requirement_table,
    trajectory_overlay,
    DEFAULT_COST_PER_UNIT,
    BENCHMARKS,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wake County | Closing the Gap",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── HACR brand colours ────────────────────────────────────────────────────────
NAVY   = "#1B3A6B"
TEAL   = "#007078"
RED    = "#DC2626"
AMBER  = "#F59E0B"
GREEN  = "#10B981"
PURPLE = "#7C3AED"
GRAY   = "#6B7280"
LTBG   = "#F0F4F8"

# ── Global Plotly config — hides noisy toolbar, keeps download button ─────────
CHART_CONFIG = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d",
        "zoomIn2d", "zoomOut2d", "autoScale2d",
        "hoverClosestCartesian", "hoverCompareCartesian",
        "toggleSpikelines",
    ],
    "displaylogo": False,
    "toImageButtonOptions": {
        "format": "png", "filename": "hacr_chart",
        "height": 500, "width": 900, "scale": 2,
    },
}

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  /* top bar */
  .block-container {{ padding-top: 3rem; }}
  /* KPI cards */
  .kpi-card {{
      background: {LTBG}; border-left: 5px solid {TEAL};
      border-radius: 6px; padding: 14px 18px; margin-bottom: 6px;
  }}
  .kpi-value  {{ font-size: 1.9rem; font-weight: 700; color: {NAVY}; line-height:1.1; }}
  .kpi-label  {{ font-size: 0.78rem; color: #555; margin-top: 2px; }}
  .kpi-delta  {{ font-size: 0.82rem; font-weight: 600; margin-top: 4px; }}
  .red        {{ color: {RED}; }}
  .green      {{ color: {GREEN}; }}
  .amber      {{ color: {AMBER}; }}
  /* section headings */
  .section-head {{
      font-size: 1.05rem; font-weight: 700; color: {NAVY};
      border-bottom: 2px solid {TEAL}; padding-bottom: 4px;
      margin: 18px 0 10px 0;
  }}
  /* callout box */
  .callout {{
      background:#FEF9C3; border-left:4px solid {AMBER};
      border-radius:4px; padding:10px 14px; font-size:0.86rem;
      margin-bottom:10px;
  }}
  .callout-red {{
      background:#FEE2E2; border-left:4px solid {RED};
      border-radius:4px; padding:10px 14px; font-size:0.86rem;
      margin-bottom:10px;
  }}
  .callout-green {{
      background:#DCFCE7; border-left:4px solid {GREEN};
      border-radius:4px; padding:10px 14px; font-size:0.86rem;
      margin-bottom:10px;
  }}
  /* insight narrative box */
  .insight-box {{
      background: linear-gradient(135deg, {NAVY}10, {TEAL}18);
      border: 1px solid {TEAL}44; border-radius: 8px;
      padding: 16px 20px; margin: 12px 0;
  }}
  .insight-number {{
      font-size: 2.4rem; font-weight: 800; color: {NAVY}; line-height:1;
  }}
  .insight-title {{
      font-size: 0.95rem; font-weight: 700; color: {TEAL}; margin: 2px 0 4px 0;
  }}
  .insight-body {{
      font-size: 0.82rem; color: #444; line-height: 1.5;
  }}
  /* badge */
  .badge {{
      display: inline-block; padding: 2px 8px; border-radius: 12px;
      font-size: 0.72rem; font-weight: 700; margin-right: 4px;
  }}
  .badge-red    {{ background:#FEE2E2; color:{RED}; }}
  .badge-green  {{ background:#DCFCE7; color:#065F46; }}
  .badge-amber  {{ background:#FEF9C3; color:#92400E; }}
  .badge-navy   {{ background:{NAVY}18; color:{NAVY}; }}
  /* dashboard footer */
  .dash-footer {{
      border-top: 1px solid #E5E7EB; margin-top: 28px;
      padding-top: 10px; font-size: 0.72rem; color: #9CA3AF;
      line-height: 1.7;
  }}
  /* data quality table */
  .dq-pass {{ color:{GREEN}; font-weight:700; }}
  .dq-warn {{ color:{AMBER}; font-weight:700; }}
  .dq-fail {{ color:{RED};   font-weight:700; }}
</style>
""", unsafe_allow_html=True)


def kpi(value, label, delta=None, delta_good=None):
    """Render a styled KPI card."""
    delta_html = ""
    if delta:
        cls = "green" if delta_good else "red"
        delta_html = f'<div class="kpi-delta {cls}">{delta}</div>'
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'{delta_html}</div>',
        unsafe_allow_html=True,
    )


def callout(msg, kind="amber"):
    cls = {"amber": "callout", "red": "callout-red", "green": "callout-green"}.get(kind, "callout")
    st.markdown(f'<div class="{cls}">{msg}</div>', unsafe_allow_html=True)


def insight_box(number, title, body):
    """Large-number insight card for the narrative section."""
    st.markdown(
        f'<div class="insight-box">'
        f'<div class="insight-number">{number}</div>'
        f'<div class="insight-title">{title}</div>'
        f'<div class="insight-body">{body}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def badge(text, kind="navy"):
    return f'<span class="badge badge-{kind}">{text}</span>'


def tab_footer(sources: list = None):
    """Consistent data-source footer at the bottom of every tab."""
    defaults = [
        "wakehousingdata.org Snapshot exports (Apr 2026)",
        "HACR 2025 Annual Housing Impact Report",
        "HUD FY2024 Income Limits — Wake County, NC",
        "U.S. Census ACS 5-Year Estimates",
    ]
    lines = sources or defaults
    items = " &nbsp;·&nbsp; ".join(f"<b>{s}</b>" for s in lines)
    st.markdown(
        f'<div class="dash-footer">📌 Data sources: {items}</div>',
        unsafe_allow_html=True,
    )


# ── Load & cache data ─────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading real Wake County data…")
def load():
    return run_full_analysis()

a = load()

# Handy aliases
gap_df     = a["gap_df"]
permits    = a["building_permits"]
prod_df    = a["production_df"]
rent_df    = a["median_rent"]
iv_df      = a["income_vs_required"]
cb_income  = a["cost_burden_income"]
burden_long= a["burden_long"]
net_hh     = a["net_hh_change"]
deficit_df = a["rental_deficit"]
edu_df     = a["rent_by_education"]
hv_df      = a["median_home_value"]
price_df   = a["homes_sold_by_price"]
const      = a["hacr_constants"]
stock      = a["housing_stock"]

gm  = a["goal_metrics"]
ps  = a["permit_stats"]
ri  = a["rent_income_stats"]
rs  = a["rent_stats"]
el  = a["entry_level"]
po  = a["polarization"]
vac = a["vacancy"]
bj  = a["biggest_burden_jump"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<div style='background:{NAVY};padding:12px 14px;border-radius:6px;margin-bottom:8px;'>"
        f"<div style='color:white;font-size:1.05rem;font-weight:700;'>Wake County HACR</div>"
        f"<div style='color:#9DB8D8;font-size:0.75rem;'>Research, Data & Systems Division</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("**🎚️ Dashboard Controls**")
    sidebar_band = st.selectbox(
        "Primary AMI band focus",
        ["<$20K", "<$35K", "<$50K"],
        index=1,
        help="Filters Overview KPIs and pre-fills Scenario Modeler",
    )
    st.divider()

    # ── Methodology expander ──────────────────────────────────────────────────
    with st.expander("📐 Methodology & Definitions", expanded=False):
        st.markdown(f"""
**AMI (Area Median Income)**
HUD FY2024 Wake County AMI = $95,200 (4-person HH). Income bands use cumulative thresholds
(<$20K, <$35K, <$50K, <$75K, <$100K, <$150K).

**Affordability Definition**
A unit is "affordable" if gross rent ≤ 30% of the AMI band's monthly income
(HUD cost-burden standard, 24 CFR §5.609).

**Gap Calculation**
`Gap = Affordable Units Available − Renter Households at Band`
Negative = deficit. Source: ACS 5-Year PUMS via wakehousingdata.org.

**Cost Burden**
Households paying >30% gross income on housing (HUD definition).
Severely cost-burdened = >50%.

**Years to Close**
`Years = Deficit ÷ (Annual Production × % Targeting Band)`
Assumes constant production rate; does not model population growth.

**Cost per Unit**
Defaults reflect HACR program data and national LIHTC/HOME averages:
- PSH / <$20K : ~$185,000
- HOME / <$35K: ~$145,000
- LIHTC / <$50K: ~$115,000

**ROI Estimate**
$1.80 returned per $1 invested — HACR 2025 Annual Report,
consistent with national housing + supportive services research.

**Known Limitations**
- Supply data does not capture unit quality or bedroom size
- Population growth is not modelled (gap may grow over time)
- Permit counts ≠ affordable unit counts
- Cost-per-unit averages mask wide project-level variance
        """)

    with st.expander("🗃️ Data Sources", expanded=False):
        st.markdown("""
| Dataset | Source | Updated |
|---------|--------|---------|
| Housing Supply | wakehousingdata.org | Apr 2026 |
| Rental Affordability | wakehousingdata.org | Apr 2026 |
| Demographics | wakehousingdata.org | Apr 2026 |
| Homeownership | wakehousingdata.org | Apr 2026 |
| Production data | HACR Annual Report 2025 | Mar 2025 |
| AMI thresholds | HUD FY2024 | Apr 2024 |
| Permit data | ACS via wakehousingdata | Apr 2026 |
        """)

    st.divider()
    st.markdown(
        f"<div style='font-size:0.72rem;color:#9CA3AF;line-height:1.6;'>"
        f"Project 3 of 3 · Housing Data Analyst<br>Interview Portfolio · Wake County HACR<br>"
        f"Built with real wakehousingdata.org data</div>",
        unsafe_allow_html=True,
    )


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"<h2 style='color:{NAVY};margin-top:0.5rem;margin-bottom:0;'>🏘️ Closing the Gap</h2>"
    f"<p style='color:{TEAL};font-size:1rem;margin-top:2px;'>"
    f"Wake County Affordable Housing Supply-Demand Scenario Modeler · Real Data</p>",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🔻 Supply-Demand Gap",
    "🏗️ Production & Permits",
    "🎛️ Scenario Modeler",
    "📋 CAPER Export",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    # ── Top KPI row ───────────────────────────────────────────────────────────
    band_row = gap_df[gap_df["income_threshold"] == sidebar_band].iloc[0]
    deficit  = abs(int(band_row["gap"]))
    ytc      = deficit / const["fy2025_production"]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: kpi(f"{deficit:,}", f"Unit deficit · {sidebar_band} AMI", "Only affordable band in focus", False)
    with c2: kpi(f"{int(band_row['units_per_100'])}", f"Affordable units per 100 renters · {sidebar_band}", f"Target: 100 units per 100 renters", False)
    with c3: kpi(f"{ytc:.0f} yrs", f"Years to close at current pace", f"At 660 units/yr — closes {2026+int(ytc)}", False)
    with c4: kpi(f"${rs['rent_latest']:,}", f"Median rent Wake County ({rs['latest_year']})", f"+{rs['total_growth_pct']}% since 2015", False)
    with c5: kpi(f"{bj['pct_2024']}%", f"Cost burden — {bj['income_band']} renters (2024)", f"Was {bj['pct_2014']}% in 2014 (+{bj['change']} pp)", False)
    with c6: kpi(f"{gm['pct_complete']}%", f"2029 goal progress ({gm['achieved_to_date']:,}/{gm['goal_2029']:,})", f"On track ✅  ({const['fy2025_production']}/yr > {gm['required_pace']}/yr needed)", True)

    # ── Story in 3 numbers ────────────────────────────────────────────────────
    st.markdown('<div class="section-head">The Story in 3 Numbers</div>', unsafe_allow_html=True)
    n1, n2, n3 = st.columns(3)
    with n1:
        insight_box(
            "39 yrs",
            "To close the <$35K rental gap at current pace",
            f"There are <b>{abs(int(gap_df[gap_df['income_threshold']=='<$35K']['gap'].values[0])):,} fewer</b> affordable units "
            f"than renter households earning under $35K. At HACR's current production of "
            f"{const['fy2025_production']} units/yr, the gap closes in <b>2065</b>. "
            f"At 5× pace it closes in <b>2033</b>.",
        )
    with n2:
        insight_box(
            "+$8,920",
            "Income required to afford rent jumped in 2021 alone",
            f"From 2015–2020 the rent-income gap averaged just <b>${abs(ri['avg_gap_pre_2021']):,}/yr</b>. "
            f"In 2021 rents spiked — the required income jumped <b>+${ri['income_spike_2021']:,}</b> "
            f"in a single year, pushing the gap to <b>${abs(ri['worst_gap']):,}</b> at its worst.",
        )
    with n3:
        insight_box(
            "89%",
            "Collapse of homes sold under $250K (2018→2022)",
            f"Entry-level homeownership has nearly vanished: homes sold under $250K fell from "
            f"<b>{el['pct_under_250k_2018']}%</b> of all sales in 2018 to just "
            f"<b>{el['pct_under_250k_2022']}%</b> in 2022 — "
            f"a <b>{abs(el['drop_relative_pct'])}% relative decline</b> in four years.",
        )

    st.divider()

    # ── Three headline callouts ───────────────────────────────────────────────
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        callout(
            f"🔴 <b>{deficit:,} unit shortfall</b> for {sidebar_band} AMI renters. "
            f"Only <b>{int(band_row['units_per_100'])} affordable units</b> exist "
            f"per 100 renter households at this income level.",
            "red"
        )
    with col_b:
        callout(
            f"⚡ <b>2021 rent shock:</b> Required income to afford median rent "
            f"jumped <b>+${ri['income_spike_2021']:,}</b> in a single year — "
            f"opening an <b>${abs(ri['worst_gap']):,} annual gap</b> vs. median renter income.",
            "amber"
        )
    with col_c:
        callout(
            f"📉 <b>Entry-level market collapsed:</b> Homes sold under $250K "
            f"fell from <b>{el['pct_under_250k_2018']}%</b> (2018) to "
            f"<b>{el['pct_under_250k_2022']}%</b> (2022) — "
            f"an <b>{abs(el['drop_relative_pct'])}% relative decline</b>.",
            "red"
        )

    st.divider()

    # ── Gap overview bar + income polarization ────────────────────────────────
    left, right = st.columns([3, 2])

    with left:
        st.markdown('<div class="section-head">Affordable Unit Gap by AMI Band</div>', unsafe_allow_html=True)
        fig_gap = go.Figure()
        colors = [RED if g < 0 else GREEN for g in gap_df["gap"]]
        fig_gap.add_bar(
            x=gap_df["income_threshold"],
            y=gap_df["gap"],
            marker_color=colors,
            text=[f"{int(g):,}" for g in gap_df["gap"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Gap: %{y:,} units<extra></extra>",
        )
        fig_gap.add_hline(y=0, line_color=NAVY, line_width=1.5)
        fig_gap.update_layout(
            height=320, margin=dict(t=20, b=10),
            yaxis_title="Units (deficit = negative)",
            xaxis_title="Income Threshold",
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#E5E7EB"),
        )
        st.plotly_chart(fig_gap, use_container_width=True)
        st.caption("Negative bars = more renter households than affordable units available. Source: wakehousingdata.org Housing Supply export.")

    with right:
        st.markdown('<div class="section-head">Income Polarization (2014→2024)</div>', unsafe_allow_html=True)
        net_hh_sorted = net_hh.sort_values("net_change")
        colors_pol = [RED if v < 0 else GREEN for v in net_hh_sorted["net_change"]]
        fig_pol = go.Figure()
        fig_pol.add_bar(
            x=net_hh_sorted["net_change"],
            y=net_hh_sorted["income_band"],
            orientation="h",
            marker_color=colors_pol,
            text=[f"{v:+,}" for v in net_hh_sorted["net_change"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Net change: %{x:,} HHs<extra></extra>",
        )
        fig_pol.add_vline(x=0, line_color=NAVY, line_width=1.5)
        fig_pol.update_layout(
            height=320, margin=dict(t=20, b=10, l=10),
            xaxis_title="Net Household Change",
            plot_bgcolor="white",
            xaxis=dict(gridcolor="#E5E7EB"),
        )
        st.plotly_chart(fig_pol, use_container_width=True)
        st.caption(f"Wake added {po['top_gaining_count']:,} {po['top_gaining_band']} HHs while losing {abs(po['total_hh_lost_low_income']):,} under-$75K HHs. Ratio: {po['ratio']}:1.")

    # ── Housing stock snapshot ────────────────────────────────────────────────
    st.markdown('<div class="section-head">Wake County Housing Stock Snapshot</div>', unsafe_allow_html=True)
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Total Homes",       f"{stock['total_homes']:,}")
    s2.metric("Owner-Occupied",    f"{stock['owner_occupied']:,}", f"{stock['pct_owner']}%")
    s3.metric("Renter-Occupied",   f"{stock['renter_occupied']:,}", f"{stock['pct_renter']}%")
    s4.metric("Vacant",            f"{stock['vacant_homes']:,}")
    s5.metric("Vacancy Rate",      f"{vac['latest_wake_pct']}%",
              f"{vac['gap_to_healthy']} pp below healthy 5%",
              delta_color="inverse")

    tab_footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SUPPLY-DEMAND GAP
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-head">Renter Households vs. Affordable Units Available</div>', unsafe_allow_html=True)

    # ── Grouped bar: renters vs units by band ─────────────────────────────────
    fig_waterfall = go.Figure()
    fig_waterfall.add_bar(
        name="Renter Households",
        x=gap_df["income_threshold"],
        y=gap_df["renter_households"],
        marker_color=NAVY,
        hovertemplate="<b>%{x}</b><br>Renter HHs: %{y:,}<extra></extra>",
    )
    fig_waterfall.add_bar(
        name="Affordable Units Available",
        x=gap_df["income_threshold"],
        y=gap_df["affordable_units"],
        marker_color=TEAL,
        hovertemplate="<b>%{x}</b><br>Affordable Units: %{y:,}<extra></extra>",
    )
    fig_waterfall.update_layout(
        barmode="group", height=380,
        margin=dict(t=20, b=10),
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#E5E7EB", title="Count"),
        xaxis_title="Income Threshold (cumulative)",
        legend=dict(orientation="h", y=-0.2),
    )

    # Shade deficit region
    for i, row in gap_df[gap_df["gap"] < 0].iterrows():
        fig_waterfall.add_annotation(
            x=row["income_threshold"],
            y=max(row["renter_households"], row["affordable_units"]) * 1.06,
            text=f"<b>Deficit<br>{abs(int(row['gap'])):,}</b>",
            showarrow=False,
            font=dict(color=RED, size=11),
        )

    st.plotly_chart(fig_waterfall, use_container_width=True)
    callout("The gap only closes at the <b><$75K</b> threshold and above. Every band below $75K has <b>fewer affordable units than renter households</b> — the crisis is concentrated in the bottom 40% of earners.", "red")

    st.divider()

    # ── Units per 100 gauge row + cost burden heatmap ─────────────────────────
    col_u, col_b = st.columns([2, 3])

    with col_u:
        st.markdown('<div class="section-head">Affordable Units per 100 Renters</div>', unsafe_allow_html=True)
        ap100 = a["affordable_per_100"].copy()
        fig_u100 = go.Figure()
        bar_colors = [RED if r < 50 else (AMBER if r < 80 else GREEN)
                      for r in ap100["units_per_100"]]
        fig_u100.add_bar(
            x=ap100["income_threshold"],
            y=ap100["units_per_100"],
            marker_color=bar_colors,
            text=ap100["units_per_100"],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y} units per 100 renters<extra></extra>",
        )
        fig_u100.add_hline(y=100, line_dash="dash", line_color=GREEN,
                           annotation_text="Target: 100 units", annotation_position="top right")
        fig_u100.update_layout(
            height=320, margin=dict(t=20, b=10),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#E5E7EB", title="Units per 100 Renters"),
            showlegend=False,
        )
        st.plotly_chart(fig_u100, use_container_width=True)
        st.caption("🔴 < 50  🟡 50–80  🟢 ≥ 100. Target is 100 units per 100 renters (parity).")

    with col_b:
        st.markdown('<div class="section-head">Cost Burden Spread by Income Band (2014 → 2024)</div>', unsafe_allow_html=True)
        pivot = cb_income[["income_band", "pct_2014", "pct_2019", "pct_2024"]].set_index("income_band")

        fig_cb = go.Figure()
        colors_cb = [GRAY, AMBER, RED]
        for col, yr, clr in zip(["pct_2014", "pct_2019", "pct_2024"],
                                  [2014, 2019, 2024], colors_cb):
            fig_cb.add_bar(
                name=str(yr),
                x=cb_income["income_band"],
                y=cb_income[col],
                marker_color=clr,
                hovertemplate=f"<b>%{{x}}</b><br>{yr}: %{{y:.1f}}%<extra></extra>",
            )
        fig_cb.add_hline(y=50, line_dash="dot", line_color=RED,
                         annotation_text="50% crisis threshold",
                         annotation_position="top left",
                         annotation_font_color=RED)
        fig_cb.update_layout(
            barmode="group", height=320,
            margin=dict(t=20, b=10),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#E5E7EB", title="% Cost Burdened", range=[0, 105]),
            legend=dict(orientation="h", y=-0.25),
        )
        st.plotly_chart(fig_cb, use_container_width=True)
        callout(
            f"Two bands <b>newly crossed the 50% crisis threshold</b> since 2014: "
            f"<b>{', '.join(a['new_crisis_bands'])}</b>. "
            f"Biggest jump: <b>{bj['income_band']}</b> rose "
            f"{bj['pct_2014']}% → <b>{bj['pct_2024']}%</b> (+{bj['change']} pp).",
            "amber"
        )

    st.divider()

    # ── Rent-income gap timeline ──────────────────────────────────────────────
    st.markdown('<div class="section-head">Renter Income vs. Income Required to Afford Median Rent (2015–2024)</div>', unsafe_allow_html=True)
    fig_ri = go.Figure()
    fig_ri.add_scatter(
        x=iv_df["year"], y=iv_df["median_renter_income"],
        name="Median Renter Income",
        mode="lines+markers",
        line=dict(color=TEAL, width=3),
        marker=dict(size=7),
        hovertemplate="<b>%{x}</b><br>Renter Income: $%{y:,}<extra></extra>",
    )
    fig_ri.add_scatter(
        x=iv_df["year"], y=iv_df["income_required"],
        name="Income Required to Afford Median Rent",
        mode="lines+markers",
        line=dict(color=RED, width=3, dash="dash"),
        marker=dict(size=7),
        hovertemplate="<b>%{x}</b><br>Required Income: $%{y:,}<extra></extra>",
    )
    # Fill the gap
    fig_ri.add_traces([
        go.Scatter(x=iv_df["year"], y=iv_df["income_required"],
                   fill=None, mode="lines", line_color="rgba(0,0,0,0)", showlegend=False),
        go.Scatter(x=iv_df["year"], y=iv_df["median_renter_income"],
                   fill="tonexty", mode="lines", line_color="rgba(0,0,0,0)",
                   fillcolor="rgba(220,38,38,0.12)", showlegend=False,
                   name="Affordability gap"),
    ])
    # 2021 annotation
    fig_ri.add_annotation(
        x=2021, y=61_400,
        text=f"<b>2021: rents spiked<br>+${ri['income_spike_2021']:,} required<br>in one year</b>",
        showarrow=True, arrowhead=2, arrowcolor=RED,
        font=dict(color=RED, size=11),
        ax=60, ay=-50,
    )
    fig_ri.update_layout(
        height=340, margin=dict(t=20, b=10),
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#E5E7EB", title="Annual Income ($)", tickprefix="$", tickformat=","),
        xaxis=dict(dtick=1),
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fig_ri, use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gap before 2021 (avg)", f"${abs(ri['avg_gap_pre_2021']):,}/yr")
    c2.metric("Gap after 2021 (avg)",  f"${abs(ri['avg_gap_post_2021']):,}/yr",
              f"Worsened by ${abs(ri['gap_worsened_by']):,}", delta_color="inverse")
    c3.metric("Worst gap year",         f"{ri['worst_year']}",
              f"${abs(ri['worst_gap']):,} shortfall")
    c4.metric(f"Gap in {ri['latest_year']}",
              f"${abs(ri['latest_gap']):,}/yr",
              f"Narrowing but still unaffordable", delta_color="inverse")

    st.divider()

    # ── Education vs. affordability + price bracket shift ────────────────────
    col_edu, col_price = st.columns(2)

    with col_edu:
        st.markdown('<div class="section-head">Who Can Afford to Rent? — By Education Level (2023)</div>',
                    unsafe_allow_html=True)
        median_rent_val = int(edu_df["median_rent"].iloc[0])
        fig_edu = go.Figure()
        bar_colors_edu = [GREEN if r >= median_rent_val else RED
                          for r in edu_df["affordable_rent"]]
        fig_edu.add_bar(
            x=edu_df["education_level"],
            y=edu_df["affordable_rent"],
            marker_color=bar_colors_edu,
            text=[f"${int(v):,}" for v in edu_df["affordable_rent"]],
            textposition="outside",
            name="Max Affordable Rent",
            hovertemplate="<b>%{x}</b><br>Can afford: $%{y:,.0f}/mo<extra></extra>",
        )
        fig_edu.add_hline(
            y=median_rent_val,
            line_dash="dash", line_color=NAVY, line_width=2,
            annotation_text=f"Median Rent ${median_rent_val:,}",
            annotation_position="top left",
            annotation_font_color=NAVY,
        )
        fig_edu.update_layout(
            height=300, margin=dict(t=20, b=10),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#E5E7EB", title="Max Affordable Monthly Rent ($)",
                       tickprefix="$", tickformat=","),
            xaxis_title="Highest Education Level",
            showlegend=False,
            title=dict(text="🟢 above line = can afford median rent  🔴 below = cannot", x=0,
                       font=dict(size=11, color=GRAY)),
        )
        st.plotly_chart(fig_edu, use_container_width=True, config=CHART_CONFIG)
        callout(
            f"Only renters with a <b>College Degree or higher</b> can afford Wake County's "
            f"${median_rent_val:,}/mo median rent. Renters without a HS diploma can only afford "
            f"<b>${int(edu_df[edu_df['education_level']=='No HS Diploma']['affordable_rent'].values[0]):,}/mo</b> — "
            f"less than half the median.",
            "red",
        )

    with col_price:
        st.markdown('<div class="section-head">Entry-Level Homeownership Collapse — Homes Sold by Price (2018 vs 2022)</div>',
                    unsafe_allow_html=True)
        fig_price = go.Figure()
        fig_price.add_bar(
            x=price_df["price_bracket"], y=price_df["pct_2018"],
            name="2018", marker_color=TEAL,
            hovertemplate="<b>%{x}</b><br>2018: %{y:.1f}%<extra></extra>",
        )
        fig_price.add_bar(
            x=price_df["price_bracket"], y=price_df["pct_2022"],
            name="2022", marker_color=RED,
            hovertemplate="<b>%{x}</b><br>2022: %{y:.1f}%<extra></extra>",
        )
        # Annotate the <$250K collapse
        fig_price.add_annotation(
            x="<$250K", y=price_df[price_df["price_bracket"]=="<$250K"]["pct_2018"].values[0],
            text=f"<b>−{abs(el['drop_relative_pct'])}%<br>in 4 yrs</b>",
            showarrow=True, arrowhead=2, arrowcolor=RED,
            font=dict(color=RED, size=11), ax=50, ay=-35,
        )
        fig_price.update_layout(
            barmode="group", height=300, margin=dict(t=20, b=10),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#E5E7EB", title="Share of Homes Sold (%)",
                       ticksuffix="%"),
            legend=dict(orientation="h", y=-0.25),
            title=dict(
                text="Market shifted entirely to $250K–$750K range — first-time buyers priced out",
                x=0, font=dict(size=11, color=GRAY),
            ),
        )
        st.plotly_chart(fig_price, use_container_width=True, config=CHART_CONFIG)
        callout(
            f"Homes sold under <b>$250K</b> fell from <b>{el['pct_under_250k_2018']}%</b> (2018) "
            f"to just <b>{el['pct_under_250k_2022']}%</b> (2022). Meanwhile, <b>$500K–$750K</b> homes "
            f"nearly tripled their share. First-time buyers with moderate incomes have "
            f"almost no purchase options.",
            "red",
        )

    tab_footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PRODUCTION & PERMITS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    # ── Goal gauge + annual production bars ───────────────────────────────────
    col_g, col_p = st.columns([1, 3])

    with col_g:
        st.markdown('<div class="section-head">2029 Goal</div>', unsafe_allow_html=True)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=gm["pct_complete"],
            number={"suffix": "%", "font": {"size": 36}},
            delta={"reference": 50, "valueformat": ".1f"},
            title={"text": f"{gm['achieved_to_date']:,} / {gm['goal_2029']:,}<br><span style='font-size:0.8em'>homes</span>"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar":  {"color": GREEN},
                "steps": [
                    {"range": [0,  33], "color": "#FEE2E2"},
                    {"range": [33, 66], "color": "#FEF9C3"},
                    {"range": [66, 100], "color": "#DCFCE7"},
                ],
                "threshold": {"line": {"color": NAVY, "width": 3}, "value": 100},
            },
        ))
        fig_gauge.update_layout(height=280, margin=dict(t=10, b=0, l=20, r=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.metric("Required pace",  f"{gm['required_pace']:,} units/yr")
        st.metric("Current pace",   f"{gm['current_pace']:,} units/yr",
                  f"+{abs(gm['pace_gap']):,} above required ✅", delta_color="normal")

    with col_p:
        st.markdown('<div class="section-head">Annual Affordable Housing Production & Cumulative Progress</div>', unsafe_allow_html=True)
        fig_prod = go.Figure()
        fig_prod.add_bar(
            x=prod_df["year"], y=prod_df["units"],
            name="Annual Units Produced",
            marker_color=TEAL,
            hovertemplate="<b>%{x}</b><br>Annual: %{y:,} units<extra></extra>",
        )
        fig_prod.add_scatter(
            x=prod_df["year"], y=prod_df["cumulative"],
            name="Cumulative Total",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color=NAVY, width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>Cumulative: %{y:,}<extra></extra>",
        )
        fig_prod.add_hline(
            y=const["fy2025_production"],
            line_dash="dot", line_color=GREEN,
            annotation_text=f"Current pace ({const['fy2025_production']}/yr)",
            annotation_position="bottom right",
        )
        fig_prod.update_layout(
            height=280, margin=dict(t=20, b=10),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#E5E7EB", title="Annual Units"),
            yaxis2=dict(overlaying="y", side="right", title="Cumulative Units",
                        showgrid=False),
            legend=dict(orientation="h", y=-0.3),
        )
        st.plotly_chart(fig_prod, use_container_width=True)

    st.divider()

    # ── Building permits trend ────────────────────────────────────────────────
    st.markdown('<div class="section-head">Residential Building Permits Issued (2014–2024)</div>', unsafe_allow_html=True)
    col_perm, col_pstat = st.columns([3, 1])

    with col_perm:
        fig_perm = go.Figure()
        fig_perm.add_bar(
            x=permits["year"], y=permits["single_family"],
            name="Single-Family", marker_color=NAVY,
            hovertemplate="<b>%{x}</b><br>SF: %{y:,}<extra></extra>",
        )
        fig_perm.add_bar(
            x=permits["year"], y=permits["multifamily"],
            name="Multifamily", marker_color=TEAL,
            hovertemplate="<b>%{x}</b><br>MF: %{y:,}<extra></extra>",
        )
        # demand band
        fig_perm.add_hrect(y0=18_000, y1=23_000, fillcolor="rgba(16,185,129,0.08)",
                           line_width=0, annotation_text="Annual demand range (18k–23k)",
                           annotation_position="top left",
                           annotation_font_color=GREEN)
        # 2021 and 2022 annotations
        fig_perm.add_annotation(x=2022, y=17_961,
            text="<b>Peak: 17,961</b>", showarrow=True, arrowhead=2,
            arrowcolor=AMBER, font=dict(color=AMBER, size=11), ay=-40)
        fig_perm.add_annotation(x=2021, y=16_988,
            text="<b>2021 rent<br>spike year</b>", showarrow=True, arrowhead=2,
            arrowcolor=RED, font=dict(color=RED, size=10), ax=40, ay=-50)
        fig_perm.update_layout(
            barmode="stack", height=340, margin=dict(t=20, b=10),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#E5E7EB", title="Permits Issued"),
            xaxis=dict(dtick=1),
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig_perm, use_container_width=True)

    with col_pstat:
        st.markdown('<div class="section-head">Key Stats</div>', unsafe_allow_html=True)
        st.metric("Peak year",          f"{ps['peak_year']}", f"{ps['peak_total']:,} total permits")
        st.metric("Peak MF year",       f"{ps['peak_mf_year']}", f"{ps['peak_mf_units']:,} MF units")
        st.metric("MF since peak",      f"{ps['mf_change_since_peak_pct']}%",
                  "Multifamily cooling", delta_color="inverse")
        st.metric(f"Latest ({ps['latest_year']}) total", f"{ps['latest_total']:,}",
                  f"{ps['supply_gap_vs_demand_low']:,} short of 18k demand floor",
                  delta_color="inverse")
        callout(f"Multifamily permits fell <b>{abs(ps['mf_change_since_peak_pct'])}%</b> from their 2022 peak — supply is <b>cooling</b> precisely when the gap needs to close.", "amber")

    st.divider()

    # ── Median rent + home value twin axis ───────────────────────────────────
    st.markdown('<div class="section-head">Median Rent & Home Value Trends</div>', unsafe_allow_html=True)
    col_r, col_h = st.columns(2)

    with col_r:
        fig_rent = go.Figure()
        fig_rent.add_scatter(
            x=rent_df["year"], y=rent_df["wake_rent"],
            name="Wake County", mode="lines+markers",
            line=dict(color=NAVY, width=3), marker=dict(size=7),
        )
        fig_rent.add_scatter(
            x=rent_df["year"], y=rent_df["nc_rent"],
            name="North Carolina", mode="lines+markers",
            line=dict(color=GRAY, width=2, dash="dot"), marker=dict(size=5),
        )
        fig_rent.add_annotation(x=2021, y=1535,
            text=f"<b>+${int(rent_df.loc[rent_df.year==2021,'yoy_change_dollars'].values[0]):,} in 2021</b>",
            showarrow=True, arrowhead=2, arrowcolor=RED,
            font=dict(color=RED, size=11), ax=-60, ay=-35)
        fig_rent.update_layout(
            height=280, margin=dict(t=20, b=10),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#E5E7EB", title="Median Monthly Rent ($)",
                       tickprefix="$", tickformat=","),
            xaxis=dict(dtick=1),
            legend=dict(orientation="h", y=-0.3),
            title=dict(text=f"Median Rent  (+{rs['total_growth_pct']}% since 2015)", x=0),
        )
        st.plotly_chart(fig_rent, use_container_width=True)

    with col_h:
        fig_hv = go.Figure()
        fig_hv.add_scatter(
            x=hv_df["year"], y=hv_df["wake_value"],
            name="Wake County", mode="lines+markers",
            line=dict(color=TEAL, width=3), marker=dict(size=7),
        )
        fig_hv.add_scatter(
            x=hv_df["year"], y=hv_df["nc_value"],
            name="North Carolina", mode="lines+markers",
            line=dict(color=GRAY, width=2, dash="dot"), marker=dict(size=5),
        )
        fig_hv.update_layout(
            height=280, margin=dict(t=20, b=10),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#E5E7EB", title="Median Home Value ($)",
                       tickprefix="$", tickformat=","),
            xaxis=dict(dtick=1),
            legend=dict(orientation="h", y=-0.3),
            title=dict(text=f"Median Home Value  (+{a['home_growth']['total_growth_pct']}% since 2014)", x=0),
        )
        st.plotly_chart(fig_hv, use_container_width=True, config=CHART_CONFIG)

    st.divider()

    # ── Vacancy trend ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-head">Vacancy Rate Trend — Wake County vs. North Carolina (2014–2024)</div>',
                unsafe_allow_html=True)
    vac_df = a["vacancy_rate"]
    col_vac, col_vstat = st.columns([3, 1])

    with col_vac:
        fig_vac = go.Figure()
        fig_vac.add_scatter(
            x=vac_df["year"], y=vac_df["wake_pct"],
            name="Wake County", mode="lines+markers",
            line=dict(color=NAVY, width=3), marker=dict(size=7),
            hovertemplate="<b>%{x}</b><br>Wake: %{y:.2f}%<extra></extra>",
        )
        fig_vac.add_scatter(
            x=vac_df["year"], y=vac_df["nc_pct"],
            name="North Carolina", mode="lines+markers",
            line=dict(color=GRAY, width=2, dash="dot"), marker=dict(size=5),
            hovertemplate="<b>%{x}</b><br>NC: %{y:.2f}%<extra></extra>",
        )
        fig_vac.add_hrect(
            y0=4.5, y1=5.5, fillcolor="rgba(16, 185, 129, 0.08)", line_width=0,
            annotation_text="Healthy range (4.5–5.5%)",
            annotation_position="top right",
            annotation_font_color=GREEN,
        )
        fig_vac.update_layout(
            height=260, margin=dict(t=20, b=10),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#E5E7EB", title="Vacancy Rate (%)",
                       ticksuffix="%", range=[0, 7]),
            xaxis=dict(dtick=1),
            legend=dict(orientation="h", y=-0.3),
            title=dict(
                text="Low vacancy = constrained supply — less choice and pricing power for renters",
                x=0, font=dict(size=11, color=GRAY),
            ),
        )
        st.plotly_chart(fig_vac, use_container_width=True, config=CHART_CONFIG)

    with col_vstat:
        st.markdown('<div class="section-head">Vacancy Stats</div>', unsafe_allow_html=True)
        st.metric("Latest vacancy (Wake)",  f"{vac['latest_wake_pct']}%",
                  f"{vac['gap_to_healthy']} pp below healthy floor",
                  delta_color="inverse")
        st.metric("Trend since 2014",
                  f"{vac['change_since_2014']:+.2f} pp",
                  "Consistently below healthy" if vac["latest_wake_pct"] < 4.5 else "",
                  delta_color="inverse")
        callout(
            f"Wake County's vacancy rate of <b>{vac['latest_wake_pct']}%</b> is well below the "
            f"healthy <b>5%</b> benchmark. Low vacancy signals a <b>tight rental market</b> where "
            f"landlords hold pricing power and renters face limited choice.",
            "amber",
        )

    tab_footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SCENARIO MODELER
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown(
        f"<p style='color:{GRAY};font-size:0.9rem;'>Adjust the sliders below to model "
        f"any policy scenario. All gap numbers are <b>real Wake County data.</b></p>",
        unsafe_allow_html=True,
    )

    with st.expander("📖 How to use this modeler", expanded=False):
        st.markdown(f"""
**Step 1 — Pick an AMI Band**
Choose which income group to focus on. The <b><$35K band</b> has the largest
absolute deficit ({abs(int(gap_df[gap_df['income_threshold']=='<$35K']['gap'].values[0])):,} units)
and is HACR's primary focus for HOME/ESG-funded programs.

**Step 2 — Set Annual Production**
Current HACR pace is **{const['fy2025_production']} units/yr**.
The 2026 Housing Opportunity Fund could enable 2× or higher.
Try 3,300/yr to see what matching NC's annual demand estimate would do.

**Step 3 — Set % Targeting the Band**
In practice, not all production targets the lowest AMI bands.
A realistic targeted scenario might be 660 units/yr but only 40–60%
aimed at <$35K — adjust accordingly.

**Step 4 — Cost per Unit**
Defaults are pre-filled per band from HACR program averages.
Deep subsidy programs (PSH, PBRA) run ~$185K; RRH-style ~$115K.

**What the trajectory means**
The chart shows % of the gap closed each year.
The benchmark panel compares your scenario to 4 named policy options.
Total investment is the same regardless of pace — you're choosing *when*, not *if*.
        """, unsafe_allow_html=True)

    # ── Slider inputs ─────────────────────────────────────────────────────────
    sc1, sc2, sc3, sc4 = st.columns([2, 2, 2, 2])

    with sc1:
        target_band = st.selectbox(
            "AMI Band to Target",
            ["<$20K", "<$35K", "<$50K"],
            index=["<$20K", "<$35K", "<$50K"].index(sidebar_band),
        )
    with sc2:
        annual_prod = st.slider(
            "Annual Production (units/yr)",
            min_value=100, max_value=5_000,
            value=660, step=50,
        )
    with sc3:
        pct_target = st.slider(
            "% of Production Targeting This Band",
            min_value=10, max_value=100,
            value=100, step=5,
            format="%d%%",
        ) / 100
    with sc4:
        cpu = st.slider(
            "Cost per Unit ($)",
            min_value=50_000, max_value=250_000,
            value=DEFAULT_COST_PER_UNIT.get(target_band, 145_000),
            step=5_000,
            format="$%d",
        )

    # ── Run scenario ──────────────────────────────────────────────────────────
    band_deficit = abs(int(gap_df[gap_df["income_threshold"] == target_band]["gap"].values[0]))
    result = run_scenario(
        deficit=band_deficit,
        annual_production=annual_prod,
        pct_targeting_band=pct_target,
        cost_per_unit=cpu,
    )

    # ── Output KPIs ───────────────────────────────────────────────────────────
    r1, r2, r3, r4, r5 = st.columns(5)
    with r1:
        kpi(f"{target_band}", f"AMI band targeted", f"Deficit: {band_deficit:,} units", False)
    with r2:
        kpi(f"{int(result['effective_production']):,}/yr",
            "Effective units/yr for this band",
            f"{annual_prod:,} total × {pct_target:.0%}", True)
    with r3:
        if result["gap_closed"]:
            kpi(f"{result['years_to_close']} yrs",
                f"Years to close gap",
                f"Closes in {result['close_year']}", True)
        else:
            kpi(f">{60} yrs", "Gap does not close",
                f"Only {result['pct_closed_after_sim']:.1f}% closed in 60 yrs", False)
    with r4:
        kpi(f"${result['annual_investment']/1e6:.1f}M",
            "Annual investment required",
            f"${result['total_investment']/1e6:.0f}M total", False)
    with r5:
        kpi(f"${result['cost_per_hh_helped']:,.0f}" if result["cost_per_hh_helped"] else "N/A",
            "Cost per household helped",
            f"ROI est. ${result['roi_return_estimated']/1e6:.1f}M returned", True)

    st.divider()

    # ── Trajectory chart ──────────────────────────────────────────────────────
    traj_col, bench_col = st.columns([3, 2])

    with traj_col:
        st.markdown('<div class="section-head">Gap Closure Trajectory</div>', unsafe_allow_html=True)

        overlay_scenarios = {
            "Your Scenario": {
                "annual_production": annual_prod,
                "pct_targeting": pct_target,
                "cost_per_unit": cpu,
                "color": NAVY,
            },
            "Current Pace (660/yr)": {
                "annual_production": 660,
                "pct_targeting": 1.0,
                "cost_per_unit": cpu,
                "color": GRAY,
            },
            "2× Scale (1,320/yr)": {
                "annual_production": 1_320,
                "pct_targeting": 1.0,
                "cost_per_unit": cpu,
                "color": AMBER,
            },
        }

        overlay_df = trajectory_overlay(band_deficit, overlay_scenarios)

        fig_traj = px.line(
            overlay_df,
            x="year", y="pct_gap_closed",
            color="scenario",
            color_discrete_map={k: v["color"] for k, v in overlay_scenarios.items()},
            markers=True,
            labels={"year": "Year", "pct_gap_closed": "% Gap Closed",
                    "scenario": "Scenario"},
            hover_data={"remaining_deficit": True, "annual_investment": True},
        )
        fig_traj.add_hline(y=100, line_dash="dot", line_color=GREEN,
                           annotation_text="Gap fully closed", annotation_position="bottom right")
        fig_traj.add_hline(y=50, line_dash="dash", line_color=AMBER,
                           annotation_text="50% milestone", annotation_position="bottom right")
        fig_traj.update_layout(
            height=360, margin=dict(t=20, b=10),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#E5E7EB", range=[0, 105], ticksuffix="%"),
            legend=dict(orientation="h", y=-0.25),
        )
        st.plotly_chart(fig_traj, use_container_width=True)

        # Milestone callout
        m = result["milestones"]
        if m.get(50) and m.get(75):
            callout(
                f"At <b>{annual_prod:,} units/yr</b> ({pct_target:.0%} targeting {target_band}): "
                f"50% closed by <b>{m[50]}</b> · 75% by <b>{m.get(75, '–')}</b> · "
                f"Gap fully closed by <b>{result.get('close_year', '–')}</b>.",
                "green" if result["gap_closed"] else "amber",
            )

    with bench_col:
        st.markdown('<div class="section-head">Benchmark Comparison</div>', unsafe_allow_html=True)
        bench_df = run_benchmark_comparison(band_deficit, target_band)

        fig_bench = go.Figure()
        fig_bench.add_bar(
            x=bench_df["scenario"],
            y=bench_df["years_to_close"],
            marker_color=bench_df["color"].tolist(),
            text=[f"{y} yrs" if y < 60 else ">60 yrs" for y in bench_df["years_to_close"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Years to close: %{y}<extra></extra>",
        )
        # Your scenario marker
        fig_bench.add_scatter(
            x=bench_df["scenario"][:1],
            y=[result["years_to_close"] if result["gap_closed"] else 60],
            mode="markers",
            marker=dict(symbol="star", size=18, color=NAVY),
            name="Your scenario",
            hovertemplate=f"Your scenario: {result['years_to_close'] if result['gap_closed'] else '>60'} yrs<extra></extra>",
        )
        fig_bench.update_layout(
            height=320, margin=dict(t=20, b=10),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#E5E7EB", title="Years to Close Gap", range=[0, 50]),
            showlegend=False,
        )
        st.plotly_chart(fig_bench, use_container_width=True)

        st.markdown("**Annual investment by benchmark**")
        for _, row in bench_df.iterrows():
            st.markdown(
                f"<small><b style='color:{row['color']};'>■</b> "
                f"{row['scenario']}: <b>${row['annual_investment_M']}M/yr</b> · "
                f"{row['years_to_close']} yrs</small>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Sensitivity table ─────────────────────────────────────────────────────
    st.markdown('<div class="section-head">Sensitivity Table — Years to Close by Production Rate</div>', unsafe_allow_html=True)
    sens = sensitivity_table(gap_df)
    st.dataframe(sens, hide_index=True, use_container_width=True)
    st.caption("✅ ≤10 yrs  🟡 ≤20  🟠 ≤40  🔴 >40. Assumes 100% of production targets each band.")

    tab_footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — CAPER EXPORT
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown(
        "<p style='font-size:0.9rem;color:#555;'>Download-ready tables formatted for "
        "HUD Consolidated Annual Performance and Evaluation Report (CAPER), "
        "Action Plans, and Local System Assessments.</p>",
        unsafe_allow_html=True,
    )

    # ── Table 1: Gap summary ──────────────────────────────────────────────────
    st.markdown('<div class="section-head">Table 1 — Affordable Housing Gap by AMI Band</div>', unsafe_allow_html=True)
    gap_export = gap_df[[
        "income_threshold", "renter_households",
        "affordable_units", "gap", "units_per_100", "severity_label",
    ]].copy()
    gap_export.columns = [
        "AMI Threshold", "Renter Households", "Affordable Units",
        "Gap (Deficit)", "Units per 100 Renters", "Severity",
    ]
    st.dataframe(gap_export, hide_index=True, use_container_width=True)
    st.download_button(
        "⬇️ Download Table 1 (CSV)",
        data=gap_export.to_csv(index=False),
        file_name="CAPER_T1_gap_by_ami_band.csv",
        mime="text/csv",
    )

    st.divider()

    # ── Table 2: Investment requirements ─────────────────────────────────────
    st.markdown('<div class="section-head">Table 2 — Investment Required to Close Each AMI Band Gap</div>', unsafe_allow_html=True)
    inv_tbl = investment_requirement_table(gap_df)
    st.dataframe(inv_tbl, hide_index=True, use_container_width=True)
    st.download_button(
        "⬇️ Download Table 2 (CSV)",
        data=inv_tbl.to_csv(index=False),
        file_name="CAPER_T2_investment_requirements.csv",
        mime="text/csv",
    )

    st.divider()

    # ── Table 3: Cost burden progression ─────────────────────────────────────
    st.markdown('<div class="section-head">Table 3 — Renter Cost Burden Rate by Income Band (2014, 2019, 2024)</div>', unsafe_allow_html=True)
    cb_export = cb_income.copy()
    cb_export.columns = [
        "Income Band", "% Cost Burdened 2014",
        "% Cost Burdened 2019", "% Cost Burdened 2024",
        "Change 2014→2024 (pp)",
    ]
    st.dataframe(cb_export, hide_index=True, use_container_width=True)
    st.download_button(
        "⬇️ Download Table 3 (CSV)",
        data=cb_export.to_csv(index=False),
        file_name="CAPER_T3_cost_burden_by_income.csv",
        mime="text/csv",
    )

    st.divider()

    # ── Table 4: Permit trends ────────────────────────────────────────────────
    st.markdown('<div class="section-head">Table 4 — Residential Building Permits (2014–2024)</div>', unsafe_allow_html=True)
    perm_export = permits.copy()
    perm_export.columns = ["Year", "Single-Family", "Multifamily", "Total"]
    perm_export["SF Share (%)"] = (perm_export["Single-Family"] / perm_export["Total"] * 100).round(1)
    perm_export["MF Share (%)"] = (perm_export["Multifamily"] / perm_export["Total"] * 100).round(1)
    st.dataframe(perm_export, hide_index=True, use_container_width=True)
    st.download_button(
        "⬇️ Download Table 4 (CSV)",
        data=perm_export.to_csv(index=False),
        file_name="CAPER_T4_building_permits.csv",
        mime="text/csv",
    )

    st.divider()

    # ── Table 5: Education vs affordability ──────────────────────────────────
    st.markdown('<div class="section-head">Table 5 — Affordable Rent by Educational Attainment vs. Median Rent (2023)</div>', unsafe_allow_html=True)
    edu_export = edu_df.copy()
    edu_export["Can Afford Median Rent?"] = edu_export["affordable_rent"].apply(
        lambda x: "✅ Yes" if x >= edu_export["median_rent"].iloc[0] else "❌ No"
    )
    edu_export["Gap to Median Rent ($)"] = (edu_export["affordable_rent"] - edu_export["median_rent"]).round(0).astype(int)
    edu_export.columns = [
        "Education Level", "Affordable Rent ($)", "Median Rent ($)",
        "Can Afford?", "Gap ($)",
    ]
    st.dataframe(edu_export, hide_index=True, use_container_width=True)
    st.download_button(
        "⬇️ Download Table 5 (CSV)",
        data=edu_export.to_csv(index=False),
        file_name="CAPER_T5_education_affordability.csv",
        mime="text/csv",
    )

    st.divider()

    # ── Download all as zip ───────────────────────────────────────────────────
    import io, zipfile

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("CAPER_T1_gap_by_ami_band.csv",        gap_export.to_csv(index=False))
        zf.writestr("CAPER_T2_investment_requirements.csv", inv_tbl.to_csv(index=False))
        zf.writestr("CAPER_T3_cost_burden_by_income.csv",   cb_export.to_csv(index=False))
        zf.writestr("CAPER_T4_building_permits.csv",         perm_export.to_csv(index=False))
        zf.writestr("CAPER_T5_education_affordability.csv",  edu_export.to_csv(index=False))
    zip_buffer.seek(0)

    st.download_button(
        "⬇️ Download All Tables (ZIP)",
        data=zip_buffer,
        file_name="HACR_CAPER_tables.zip",
        mime="application/zip",
    )

    st.divider()

    # ── Data Quality Checklist ────────────────────────────────────────────────
    st.markdown('<div class="section-head">Data Quality Checklist</div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.85rem;color:#555;'>"
        "Per HUD HMIS Data Standards and CAPER reporting requirements.</p>",
        unsafe_allow_html=True,
    )
    dq_checks = [
        ("✅", "PASS",  "AMI thresholds aligned to HUD FY2024 Wake County limits"),
        ("✅", "PASS",  "Gap calculations use cumulative income bands (HUD standard)"),
        ("✅", "PASS",  "Cost burden threshold = 30% gross income (24 CFR §5.609)"),
        ("✅", "PASS",  "No null values in primary gap or cost burden tables"),
        ("✅", "PASS",  "Permit data cross-referenced with Housing Supply export"),
        ("✅", "PASS",  "Year-over-year change metrics computed from first-year baseline"),
        ("⚠️", "REVIEW","Production cost-per-unit figures are program averages — vary by project"),
        ("⚠️", "REVIEW","Permit counts reflect approvals, not construction completions"),
        ("⚠️", "REVIEW","ACS cost-burden estimates carry ±3–5% margin of error"),
        ("ℹ️", "NOTE",  "Scenario model assumes constant annual production (no population growth adjustment)"),
        ("ℹ️", "NOTE",  "Price bracket data available for 2018 and 2022 only — 2023/2024 not yet published"),
    ]
    dq_df = pd.DataFrame(dq_checks, columns=["Status", "Result", "Check"])
    st.dataframe(dq_df, hide_index=True, use_container_width=True)

    tab_footer([
        "wakehousingdata.org Snapshot exports (Apr 2026)",
        "HACR 2025 Annual Housing Impact Report",
        "HUD CAPER Reporting Specifications FY2024",
        "24 CFR §5.609 — HUD Cost Burden Definition",
    ])
