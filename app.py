# MQ submission
# ────────────────────────────────────────────────
import streamlit as st
import pandas as pd
from datetime import date
import altair as alt

# ----------------------------
# Config
# ----------------------------
today = date(2026, 2, 22)

FEASIBLE_DAILY_SPEND_BY_INDUSTRY = {
    "Airlines": 6000,
    "Hotels": 3000,
    "OTA": 5000,
    "Tourism": 2000,
    "Travel": 3000,
    "Rail": 2500,
    "Aggregator": 3500,
    None: 2500
}

DEFAULTS = {
    "commission_rate": 0.08,
    "aov": 400,
    "insurance_attach": 0.10,
    "insurance_margin": 20,
    "booking_cvr": 0.05,
}

THRESH = {
    "min_searches": 2000,
    "low_cpc": 1.50,
    "low_booking_cvr": 0.03,
    "min_fill_rate": 0.70,
}

YOY_BASELINE_FACTOR = 0.65
MOM_VOLATILITY = 0.12  # +/- 12% deterministic swing

# ----------------------------
# Dataset (fictional)
# NOTE: updated to create a clear conversion-risk example (low booking_cvr)
# ----------------------------
data = [
    # id, advertiser, industry, booked_budget, spend_to_date, start, end, notes, status, owner,
    # searches, impressions, clicks, cpc, fill_rate, booking_cvr, aov, commission_rate, insurance_attach, insurance_margin
    [1, "Airline A", "Airlines", 50000, 22000, "2026-02-01", "2026-03-15", "Launch delayed due to assets", "In-flight", "Sarah K.",
     12000, 40000, 2200, 2.20, 0.85, 0.055, 420, 0.08, 0.10, 20],

    [2, "Hotel B", "Hotels", 30000, 18000, "2026-01-10", "2026-03-01", "", "In-flight", "Mike T.",
     9000, 28000, 1400, 1.80, 0.80, 0.045, 350, 0.10, 0.12, 18],

    [3, "OTA C", "OTA", 75000, 72000, "2026-01-01", "2026-02-28", "Strong early performance", "In-flight", "Lisa M.",
     18000, 65000, 5200, 2.60, 0.92, 0.060, 380, 0.07, 0.09, 22],

    [4, "Tourism Board D", "Tourism", 40000, 9000, "2026-02-05", "2026-04-01", "Waiting on creative approval", "In-flight", "James L.",
     3500, 16000, 240, 1.10, 0.55, 0.030, 420, 0.06, 0.06, 15],

    [5, "Airline E", "Airlines", 60000, 35000, "2026-01-15", "2026-03-10", "", "In-flight", "Alex R.",
     14000, 52000, 2600, 2.05, 0.88, 0.050, 410, 0.08, 0.10, 20],

    [6, "Hotel F", "Hotels", 25000, 4000, "2026-02-10", "2026-03-10", "Low impressions — inventory constraints", "In-flight", "Rachel P.",
     1800, 6000, 120, 1.70, 0.60, 0.040, 320, 0.10, 0.10, 18],

    # UPDATED: make conversion clearly risky here (booking_cvr 0.015 << threshold 0.03)
    [7, "Cruise G", "Travel", 90000, 20000, "2026-01-20", "2026-04-20", "Clicks strong but bookings weak", "In-flight", "Tom B.",
     7000, 21000, 500, 2.40, 0.78, 0.015, 520, 0.06, 0.08, 30],

    [8, "Car Rental H", "Travel", 20000, 15000, "2026-01-25", "2026-02-25", "", "In-flight", "Emma S.",
     6500, 18000, 900, 1.60, 0.82, 0.040, 220, 0.06, 0.05, 10],

    [9, "Aggregator X", "Aggregator", 45000, 12000, "2026-02-01", "2026-03-01", "Budget approval delays from client", "In-flight", "Mike T.",
     5000, 14000, 350, 1.30, 0.62, 0.035, 300, 0.07, 0.08, 15],

    [10, "Hotel J", "Hotels", 38000, 37000, "2026-01-05", "2026-03-05", "", "In-flight", "Sarah K.",
     11000, 36000, 2100, 2.10, 0.90, 0.050, 360, 0.10, 0.12, 18],

    [11, "European Rail Pass", "Rail", None, 0, "2026-03-01", "2026-06-30", "Awaiting final budget approval", "Pre-flight", "Alex R.",
     None, None, None, None, None, None, None, None, None, None],

    [12, "Caribbean Resort Promo", "Hotels", 42000, 42000, "2026-01-01", "2026-02-20", "Completed - strong ROI", "Completed", "Lisa M.",
     9000, 30000, 2200, 2.20, 0.93, 0.060, 370, 0.10, 0.15, 18],

    [13, "Japan Cherry Blossom", "Tourism", 65000, 12000, "2026-02-10", "2026-05-15", "", "In-flight", "James L.",
     4200, 20000, 380, 1.40, 0.65, 0.030, 450, 0.06, 0.06, 15],

    [14, "Alaska Cruise Extension", None, 38000, 0, None, "2026-04-30", "Dates TBD - proposal stage", "Pre-flight", "Emma S.",
     None, None, None, None, None, None, None, None, None, None],

    [15, "US Ski Season Wrap-up", "Travel", 28000, 28000, "2025-12-01", "2026-02-18", "Ended early - low demand", "Completed", "Tom B.",
     6000, 19000, 800, 1.50, 0.85, 0.030, 280, 0.06, 0.05, 10],

    [16, "South America Eco Tours", "Tourism", 55000, 8000, "2026-02-15", "2026-07-31", "Creative assets pending", "In-flight", "Rachel P.",
     2600, 12000, 180, 1.20, 0.58, 0.028, 420, 0.06, 0.06, 15],
]

columns = [
    "campaign_id", "advertiser", "industry", "booked_budget", "spend_to_date",
    "start_date", "end_date", "notes", "status", "owner",
    "searches", "impressions", "clicks", "cpc", "fill_rate",
    "booking_cvr", "aov", "commission_rate",
    "insurance_attach", "insurance_margin"
]

df = pd.DataFrame(data, columns=columns)
df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")

for k, v in DEFAULTS.items():
    df[k] = df[k].fillna(v)

# ----------------------------
# Pacing
# ----------------------------
df["days_total"] = (df["end_date"] - df["start_date"]).dt.days
df["days_elapsed"] = (pd.to_datetime(today) - df["start_date"]).dt.days.clip(lower=0)
df["days_remaining"] = (df["end_date"] - pd.to_datetime(today)).dt.days.clip(lower=0)

df["pct_time"] = (df["days_elapsed"] / df["days_total"].replace([0, pd.NA], 1)).clip(upper=1).round(2)
df["pct_spend"] = (df["spend_to_date"] / df["booked_budget"].replace([0, pd.NA], 1)).clip(upper=1).round(2)

df["expected_spend"] = (df["booked_budget"] * df["pct_time"]).round(0)
df["spend_behind"] = (df["expected_spend"] - df["spend_to_date"]).clip(lower=0).round(0)
df["budget_remaining"] = (df["booked_budget"] - df["spend_to_date"]).clip(lower=0).round(0)
df["required_daily"] = (df["budget_remaining"] / df["days_remaining"].replace([0, pd.NA], 1)).round(0)
df["avg_daily_spend"] = (df["spend_to_date"] / df["days_elapsed"].replace([0, pd.NA], 1)).round(2)

df["feasible_daily_spend"] = df["industry"].apply(lambda x: FEASIBLE_DAILY_SPEND_BY_INDUSTRY.get(x, 2500))
df["is_feasible"] = df.apply(
    lambda r: False if pd.isna(r["required_daily"]) else (r["required_daily"] <= r["feasible_daily_spend"]),
    axis=1
)

# ----------------------------
# Unit economics (Deep Dive only)
# ----------------------------
df["ctr"] = (df["clicks"] / df["impressions"].replace([0, pd.NA], 1)).round(4)
df["ads_revenue"] = (df["clicks"] * df["cpc"]).round(0)

df["bookings"] = (df["clicks"] * df["booking_cvr"]).round(0)
df["booking_value"] = (df["bookings"] * df["aov"]).round(0)
df["booking_revenue"] = (df["booking_value"] * df["commission_rate"]).round(0)

df["insurance_units"] = (df["bookings"] * df["insurance_attach"]).round(0)
df["insurance_revenue"] = (df["insurance_units"] * df["insurance_margin"]).round(0)

df["gross_revenue"] = (df["ads_revenue"] + df["booking_revenue"] + df["insurance_revenue"]).round(0)

# YoY baseline (fictional)
df["ads_rev_yoy_base"] = (df["ads_revenue"] * YOY_BASELINE_FACTOR).round(0)
df["booking_rev_yoy_base"] = (df["booking_revenue"] * YOY_BASELINE_FACTOR).round(0)
df["ins_rev_yoy_base"] = (df["insurance_revenue"] * YOY_BASELINE_FACTOR).round(0)

def safe_growth(curr, base):
    if pd.isna(curr) or pd.isna(base) or base <= 0:
        return 0.0
    return (curr - base) / base

# MoM baseline (fictional, deterministic)
def mom_factor(campaign_id: int) -> float:
    x = (campaign_id * 37) % 100
    swing = (x / 100.0) * 2 * MOM_VOLATILITY - MOM_VOLATILITY
    return 1.0 + swing

def pct_change(curr, base):
    if pd.isna(curr) or pd.isna(base) or base == 0:
        return pd.NA
    return (curr - base) / base

df["ads_rev_mom_base"] = df.apply(lambda r: (r["ads_revenue"] / mom_factor(int(r["campaign_id"])) if pd.notna(r["ads_revenue"]) else pd.NA), axis=1)
df["booking_rev_mom_base"] = df.apply(lambda r: (r["booking_revenue"] / mom_factor(int(r["campaign_id"])+11) if pd.notna(r["booking_revenue"]) else pd.NA), axis=1)
df["ins_rev_mom_base"] = df.apply(lambda r: (r["insurance_revenue"] / mom_factor(int(r["campaign_id"])+23) if pd.notna(r["insurance_revenue"]) else pd.NA), axis=1)

df["ads_rev_mom_chg"] = df.apply(lambda r: pct_change(r["ads_revenue"], r["ads_rev_mom_base"]), axis=1)
df["booking_rev_mom_chg"] = df.apply(lambda r: pct_change(r["booking_revenue"], r["booking_rev_mom_base"]), axis=1)
df["ins_rev_mom_chg"] = df.apply(lambda r: pct_change(r["insurance_revenue"], r["ins_rev_mom_base"]), axis=1)

# ----------------------------
# Bottleneck classification
# Per request: remove "Healthy" and "Relevance" from the visible set
# ----------------------------
def classify_bottleneck(row):
    critical = ["booked_budget", "start_date", "end_date"]
    if any(pd.isna(row[c]) for c in critical):
        return "Data", "Missing critical budget/dates", "Clarify booked budget + start/end dates with Sales; confirm placement surfaces."

    if pd.notna(row["searches"]) and row["searches"] < THRESH["min_searches"]:
        return "Supply", "Low search volume (distribution/inventory)", "Increase partner exposure; expand eligible placements; open new geo/routes."

    if pd.notna(row["fill_rate"]) and row["fill_rate"] < THRESH["min_fill_rate"]:
        return "Demand", "Low fill rate (insufficient advertiser demand)", "Seed demand: onboard advertisers; broaden eligibility; package inventory; managed deals."

    if pd.notna(row["cpc"]) and row["cpc"] < THRESH["low_cpc"]:
        return "Demand", "Weak CPC / low auction pressure", "Increase competition; improve targeting; premium inventory packaging; ranking/auction tuning."

    # Conversion risk (explicit)
    if pd.notna(row["booking_cvr"]) and row["booking_cvr"] < THRESH["low_booking_cvr"]:
        return "Conversion", "Low click→booking conversion", "Reduce booking friction; improve ranking; ensure price competitiveness; optimize checkout."

    # Default: keep internal as Demand (neutral) so we don't show Healthy/Relevance categories
    return "Demand", "No acute bottleneck detected (monitor)", "Maintain pacing; monitor delivery + performance; iterate on incremental lifts."

df[["bottleneck", "bottleneck_why", "remedy"]] = df.apply(lambda r: pd.Series(classify_bottleneck(r)), axis=1)

# ----------------------------
# Risk scoring
# ----------------------------
def get_risk_score(row):
    if row["bottleneck"] == "Data":
        return 8

    gap = row["pct_spend"] - row["pct_time"]
    if gap < -0.30: pacing_score = 5
    elif gap < -0.15: pacing_score = 3
    elif gap < -0.05: pacing_score = 1
    else: pacing_score = 0

    req = row["required_daily"]
    feas_base = row["feasible_daily_spend"]
    if pd.isna(req) or pd.isna(feas_base):
        feas_score = 0
    elif req > 2.5 * feas_base:
        feas_score = 4
    elif req > feas_base:
        feas_score = 2
    else:
        feas_score = 0

    notes_lower = str(row["notes"]).lower()
    qual_score = 0
    if any(w in notes_lower for w in ["delay", "delayed", "launch"]): qual_score += 2
    if any(w in notes_lower for w in ["approval", "assets", "creative"]): qual_score += 2
    if any(w in notes_lower for w in ["low impressions", "inventory"]): qual_score += 2
    if any(w in notes_lower for w in ["budget", "approval delays"]): qual_score += 1

    # Explicit conversion penalty (so it surfaces)
    conv_score = 2 if row["bottleneck"] == "Conversion" else 0

    return pacing_score + feas_score + qual_score + conv_score

df["risk_score"] = df.apply(get_risk_score, axis=1)
df["risk"] = df["risk_score"].apply(lambda s: "Red" if s >= 6 else "Yellow" if s >= 3 else "Green")

df["why_at_risk"] = df.apply(
    lambda r: "Missing critical data (budget/dates)" if r["bottleneck"] == "Data"
    else ("On track — no major concerns." if r["risk"] == "Green"
          else f"Spend {r['pct_spend']:.0%} vs time {r['pct_time']:.0%}. Bottleneck: {r['bottleneck_why']}"),
    axis=1
)

def recommend_action(row):
    if row["bottleneck"] == "Data":
        return "Clarify booked budget + dates; confirm placements; unblock setup."
    if row["risk"] == "Green":
        return "Maintain pacing; monitor blockers; run small performance lifts."
    if pd.notna(row["required_daily"]) and pd.notna(row["feasible_daily_spend"]) and row["required_daily"] > 2.5 * row["feasible_daily_spend"]:
        return "Unrealistic recovery pace → reforecast; reallocate; renegotiate dates or add inventory."
    return row["remedy"]

df["next_action"] = df.apply(recommend_action, axis=1)

# ----------------------------
# Portfolio totals for Tab 1
# ----------------------------
total_budget = df["booked_budget"].sum(skipna=True)
budget_red = df[df["risk"] == "Red"]["booked_budget"].sum(skipna=True)
pct_budget_red = budget_red / total_budget if total_budget and total_budget > 0 else 0

ads_total = df["ads_revenue"].sum(skipna=True)
booking_total = df["booking_revenue"].sum(skipna=True)
ins_total = df["insurance_revenue"].sum(skipna=True)
gross_total = df["gross_revenue"].sum(skipna=True)

ads_yoy = df["ads_rev_yoy_base"].sum(skipna=True)
booking_yoy = df["booking_rev_yoy_base"].sum(skipna=True)
ins_yoy = df["ins_rev_yoy_base"].sum(skipna=True)
gross_yoy = (ads_yoy + booking_yoy + ins_yoy)

ads_yoy_growth = safe_growth(ads_total, ads_yoy)
booking_yoy_growth = safe_growth(booking_total, booking_yoy)
ins_yoy_growth = safe_growth(ins_total, ins_yoy)
gross_yoy_growth = safe_growth(gross_total, gross_yoy)

# ----------------------------
# Styling
# ----------------------------
def color_rows(row):
    if row["risk"] == "Red":    return ["background-color: #ffebee"] * len(row)
    if row["risk"] == "Yellow": return ["background-color: #fff9c4"] * len(row)
    return ["background-color: #e8f5e9"] * len(row)

# ----------------------------
# UI
# ----------------------------
st.title("Campaign Risk & Revenue Dashboard")

tab1, tab2, tab3 = st.tabs(["Overview", "Priority List", "Deep Dive"])

# ----------------------------
# Tab 1: Overview
# ----------------------------
with tab1:
    c1, c2 = st.columns(2)
    c1.metric("Total Booked Budget", f"${total_budget:,.0f}", f"{gross_yoy_growth:.1%} YoY (gross rev)")
    c2.metric("Budget At Risk", f"${budget_red:,.0f} ({pct_budget_red:.1%})")

    st.write("---")
    st.subheader("Revenue Breakdown (Ads + Booking + Insurance)")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ads Revenue", f"${ads_total:,.0f}", f"{ads_yoy_growth:.1%} YoY")
    k2.metric("Booking Revenue", f"${booking_total:,.0f}", f"{booking_yoy_growth:.1%} YoY")
    k3.metric("Insurance Revenue", f"${ins_total:,.0f}", f"{ins_yoy_growth:.1%} YoY")
    k4.metric("Total Gross Revenue", f"${gross_total:,.0f}", f"{gross_yoy_growth:.1%} YoY")

    # Bottom chart: bars (current vs prior) + line on secondary axis (YoY growth %)
    breakdown_df = pd.DataFrame({
        "component": ["Ads", "Booking", "Insurance"],
        "current": [ads_total, booking_total, ins_total],
        "prior_year": [ads_yoy, booking_yoy, ins_yoy],
        "yoy_growth": [ads_yoy_growth, booking_yoy_growth, ins_yoy_growth]
    })

    prior_bar = alt.Chart(breakdown_df).mark_bar(opacity=0.35).encode(
        x=alt.X("component:N", title="Revenue component"),
        y=alt.Y("prior_year:Q", title="Revenue ($)"),
        tooltip=["component", alt.Tooltip("prior_year:Q", format=",.0f")]
    )

    current_bar = alt.Chart(breakdown_df).mark_bar().encode(
        x="component:N",
        y="current:Q",
        tooltip=["component", alt.Tooltip("current:Q", format=",.0f")]
    )

    growth_line = alt.Chart(breakdown_df).mark_line(point=True).encode(
        x="component:N",
        y=alt.Y("yoy_growth:Q", title="YoY growth (%)", axis=alt.Axis(format="%")),
        tooltip=[alt.Tooltip("yoy_growth:Q", format=".1%")]
    )

    st.altair_chart(
        alt.layer(prior_bar + current_bar, growth_line).resolve_scale(y="independent").properties(height=320),
        use_container_width=True
    )
    st.caption("Prior year is a fictional baseline. Values represent YTD")

# ----------------------------
# Tab 2: Priority List
# Requirements:
# - Add revenue at risk by filter
# - Remove Healthy/Relevance (done via filter options + classifier)
# ----------------------------
with tab2:
    st.subheader("Campaigns Needing Attention (Ops view)")

    risk_filter = st.selectbox("Filter by Risk", ["All", "Red", "Yellow", "Green"])
    bottleneck_filter = st.selectbox("Filter by Bottleneck", ["All", "Data", "Supply", "Demand", "Conversion"])

    filtered = df.copy()
    if risk_filter != "All":
        filtered = filtered[filtered["risk"] == risk_filter]
    if bottleneck_filter != "All":
        filtered = filtered[filtered["bottleneck"] == bottleneck_filter]

    # Revenue at risk by filter (gross revenue component rollup)
    # Interpreting "at risk" as filtered set (whatever you filter to)
    ads_risk = filtered["ads_revenue"].sum(skipna=True)
    booking_risk = filtered["booking_revenue"].sum(skipna=True)
    ins_risk = filtered["insurance_revenue"].sum(skipna=True)
    gross_risk = filtered["gross_revenue"].sum(skipna=True)

    st.subheader("Revenue at Risk (based on current filters)")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Ads (filtered)", f"${ads_risk:,.0f}")
    r2.metric("Booking (filtered)", f"${booking_risk:,.0f}")
    r3.metric("Insurance (filtered)", f"${ins_risk:,.0f}")
    r4.metric("Total (filtered)", f"${gross_risk:,.0f}")

    st.write("---")

    view_cols = [
        "risk", "bottleneck", "status", "owner", "advertiser", "industry",
        "booked_budget", "spend_to_date", "spend_behind", "days_remaining",
        "pct_time", "pct_spend",
        "why_at_risk", "next_action"
    ]

    display_df = filtered[view_cols].copy()

    styled = display_df.style.format({
        "booked_budget": lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A",
        "spend_to_date": lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A",
        "spend_behind": lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A",
        "pct_time": "{:.0%}",
        "pct_spend": "{:.0%}",
    }).apply(color_rows, axis=1)

    st.dataframe(styled, use_container_width=True, hide_index=True)
    st.caption("Portfolio view of all active campaigns. For detailed unit economics diagnostic and recommendation please see deep dive tab.")

# ----------------------------
# Tab 3: Deep Dive
# Requirements:
# - Unit economics table adds MoM change column (no chart)
# - Trajectory: current vs required pacing, and clear feasibility statement
# ----------------------------
with tab3:
    st.subheader("Campaign Deep Dive (Economics + Recovery Plan)")

    advertiser = st.selectbox("Select campaign", sorted(df["advertiser"].dropna().unique()))
    camp = df[df["advertiser"] == advertiser].iloc[0]

    feasible_text = "✅ Feasible" if camp["is_feasible"] else "❌ Not feasible"
    st.markdown(f"**Risk**: **{camp['risk']}** | **Bottleneck**: **{camp['bottleneck']}** | **Recovery**: **{feasible_text}**")
    st.markdown(f"**Why**: {camp['why_at_risk']}")
    st.markdown(f"**Recommended action**: **{camp['next_action']}**")

    st.write("---")
    budget_str = f"${camp['booked_budget']:,.0f}" if pd.notna(camp["booked_budget"]) else "N/A"
    st.write(f"Spend: **${camp['spend_to_date']:,.0f} out of {budget_str}** ({camp['pct_spend']:.0%})")
    st.write(f"Time elapsed: **{camp['pct_time']:.0%}** | Behind schedule: **${camp['spend_behind']:,.0f}**")

    st.subheader("Feasibility Check")
    feas_df = pd.DataFrame({
        "Metric": ["Budget remaining", "Required daily spend", "Feasible daily spend (industry)", "Days remaining", "Feasible?"],
        "Value": [
            f"${camp['budget_remaining']:,.0f}" if pd.notna(camp["budget_remaining"]) else "N/A",
            f"${camp['required_daily']:,.0f}/day" if pd.notna(camp["required_daily"]) else "N/A",
            f"${camp['feasible_daily_spend']:,.0f}/day",
            f"{int(camp['days_remaining'])}" if pd.notna(camp["days_remaining"]) else "N/A",
            "Yes" if camp["is_feasible"] else "No"
        ]
    })
    st.dataframe(feas_df, use_container_width=True, hide_index=True)

    st.write("---")
    st.subheader("Revenue Changes breakdown")
    ue_rows = [
        ("Ads revenue", camp["ads_revenue"], camp["ads_rev_mom_chg"]),
        ("Booking revenue", camp["booking_revenue"], camp["booking_rev_mom_chg"]),
        ("Insurance revenue", camp["insurance_revenue"], camp["ins_rev_mom_chg"]),
        ("Total gross revenue", camp["gross_revenue"], pd.NA),
    ]
    ue_tbl = pd.DataFrame(ue_rows, columns=["Component", "Current", "MoM change"])
    ue_tbl["Current"] = ue_tbl["Current"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
    ue_tbl["MoM change"] = ue_tbl["MoM change"].apply(lambda x: f"{x:.1%}" if pd.notna(x) else "—")
    st.dataframe(ue_tbl, use_container_width=True, hide_index=True)
    st.caption("All MoM comps are fictional to support diagnostic.")

    st.write("---")
    st.subheader("Funnel Diagnostics")

    funnel_rows = [
        ("Search Volume", "Supply", camp["searches"]),
        ("Impressions", "Supply", camp["impressions"]),
        ("CTR", "Demand", camp["ctr"]),
        ("CPC", "Demand", camp["cpc"]),
        ("Booking Conversion Rate", "Conversion", camp["booking_cvr"])
    ]

    funnel_df = pd.DataFrame(funnel_rows, columns=["Metric","Funnel Type","Current"])

    # MoM changes (fictional deterministic comps)
    def mom_change(value, seed):
        if pd.isna(value):
            return pd.NA
        factor = 1 + ((seed*37)%10 - 5)/100
        prev = value / factor
        return (value - prev) / prev

    funnel_df["MoM Change"] = [
        mom_change(camp["searches"],1),
        mom_change(camp["impressions"],2),
        mom_change(camp["ctr"],3),
        mom_change(camp["cpc"],4),
        mom_change(camp["booking_cvr"],5),
    ]

    funnel_df["Current"] = funnel_df.apply(
        lambda r: f"{r['Current']:.2%}" if r["Metric"] in ["CTR","Booking Conversion Rate"]
        else f"${r['Current']:.2f}" if r["Metric"]=="CPC"
        else f"{int(r['Current'])}", axis=1
    )

    funnel_df["MoM Change"] = funnel_df["MoM Change"].apply(
        lambda x: f"{x:.1%}" if pd.notna(x) else "N/A"
    )

    st.dataframe(funnel_df, use_container_width=True, hide_index=True)

    
    st.write("---")
    st.subheader("Delivery Trajectory (Current vs Required)")
    if pd.notna(camp["start_date"]) and pd.notna(camp["end_date"]) and pd.notna(camp["booked_budget"]):
        dates = pd.date_range(camp["start_date"], camp["end_date"])
        curve = pd.DataFrame({"date": dates})
        curve["days_from_start"] = (curve["date"] - camp["start_date"]).dt.days
        curve["days_from_today"] = (curve["date"] - pd.to_datetime(today)).dt.days

        daily_trend = camp["spend_to_date"] / max(int(camp["days_elapsed"]), 1)
        req_daily = float(camp["required_daily"]) if pd.notna(camp["required_daily"]) else 0.0

        hist = curve[curve["date"] <= pd.to_datetime(today)].copy()
        if camp["days_elapsed"] > 0:
            hist["actual_trend"] = (
                hist["days_from_start"] / max(int(camp["days_elapsed"]), 1) * camp["spend_to_date"]
            ).clip(0, camp["spend_to_date"])
        else:
            hist["actual_trend"] = 0

        future = curve[curve["date"] >= pd.to_datetime(today)].copy()
        future["current_pace_path"] = (
            camp["spend_to_date"] + (future["days_from_today"].clip(lower=0) * daily_trend)
        ).clip(upper=camp["booked_budget"])
        future["required_pace_path"] = (
            camp["spend_to_date"] + (future["days_from_today"].clip(lower=0) * req_daily)
        ).clip(upper=camp["booked_budget"])

        future["gap_low"] = future["current_pace_path"]
        future["gap_high"] = future["required_pace_path"]

        hist_line = alt.Chart(hist).mark_line(size=3).encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("actual_trend:Q", title="Cumulative Spend ($)")
        )

        # two future lines + shaded gap (colors are defaults; line styles differentiate clearly)
        current_line = alt.Chart(future).mark_line(strokeDash=[6, 4], size=3).encode(
            x="date:T", y="current_pace_path:Q"
        )
        required_line = alt.Chart(future).mark_line(strokeDash=[2, 2], size=3).encode(
            x="date:T", y="required_pace_path:Q"
        )
        gap_area = alt.Chart(future).mark_area(opacity=0.18).encode(
            x="date:T", y="gap_low:Q", y2="gap_high:Q"
        )

        today_df = pd.DataFrame({"date": [pd.to_datetime(today)], "spend": [camp["spend_to_date"]]})
        today_rule = alt.Chart(today_df).mark_rule(size=2, strokeDash=[4, 4]).encode(x="date:T")
        today_point = alt.Chart(today_df).mark_point(size=120, filled=True).encode(x="date:T", y="spend:Q")

        chart = (gap_area + hist_line + current_line + required_line + today_rule + today_point).properties(
            height=420,
            title=f"Current pace vs required pace (End: {camp['end_date'].date()})"
        ).interactive()

        st.altair_chart(chart, use_container_width=True)

        lift = max(req_daily - daily_trend, 0)
        st.caption(
            f"Current pace ≈ ${daily_trend:,.0f}/day | Required pace ≈ ${req_daily:,.0f}/day | "
            f"Lift needed: +${lift:,.0f}/day | Feasible threshold: ${camp['feasible_daily_spend']:,.0f}/day → {feasible_text}"
        )
    else:
        st.info("Not enough date/budget data to render trajectory.")

st.caption("Prototype — Fictional data ")
