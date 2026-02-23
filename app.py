# MQ submission
# ────────────────────────────────────────────────

import streamlit as st
import pandas as pd
from datetime import date
import altair as alt

today = date(2026, 2, 22)
FEASIBLE_DAILY_SPEND = 2000

# ────────────────────────────────────────────────
# Dataset – 16 campaigns (mix of stages + missing data)
# ────────────────────────────────────────────────
data = [
    [1, "Airline A", "Airlines", 50000, 22000, "2026-02-01", "2026-03-15", "Launch delayed due to assets", "In-flight", "Sarah K."],
    [2, "Hotel B", "Hotels", 30000, 18000, "2026-01-10", "2026-03-01", "", "In-flight", "Mike T."],
    [3, "OTA C", "OTA", 75000, 72000, "2026-01-01", "2026-02-28", "Strong early performance", "In-flight", "Lisa M."],
    [4, "Tourism Board D", "Tourism", 40000, 9000, "2026-02-05", "2026-04-01", "Waiting on creative approval", "In-flight", "James L."],
    [5, "Airline E", "Airlines", 60000, 35000, "2026-01-15", "2026-03-10", "", "In-flight", "Alex R."],
    [6, "Hotel F", "Hotels", 25000, 4000, "2026-02-10", "2026-03-10", "Low impressions — inventory constraints", "In-flight", "Rachel P."],
    [7, "Cruise G", "Travel", 90000, 20000, "2026-01-20", "2026-04-20", "", "In-flight", "Tom B."],
    [8, "Car Rental H", "Travel", 20000, 15000, "2026-01-25", "2026-02-25", "", "In-flight", "Emma S."],
    [9, "Aggregator X", "Aggregator", 45000, 12000, "2026-02-01", "2026-03-01", "Budget approval delays from client", "In-flight", "Mike T."],
    [10, "Hotel J", "Hotels", 38000, 37000, "2026-01-05", "2026-03-05", "", "In-flight", "Sarah K."],
    [11, "European Rail Pass", "Rail", None, 0, "2026-03-01", "2026-06-30", "Awaiting final budget approval", "Pre-flight", "Alex R."],
    [12, "Caribbean Resort Promo", "Hotels", 42000, 42000, "2026-01-01", "2026-02-20", "Completed - strong ROI", "Completed", "Lisa M."],
    [13, "Japan Cherry Blossom", "Tourism", 65000, 12000, "2026-02-10", "2026-05-15", "", "In-flight", "James L."],
    [14, "Alaska Cruise Extension", None, 38000, 0, None, "2026-04-30", "Dates TBD - proposal stage", "Pre-flight", "Emma S."],
    [15, "US Ski Season Wrap-up", "Travel", 28000, 28000, "2025-12-01", "2026-02-18", "Ended early - low demand", "Completed", "Tom B."],
    [16, "South America Eco Tours", "Tourism", 55000, 8000, "2026-02-15", "2026-07-31", "Creative assets pending", "In-flight", "Rachel P."],
]

columns = ["campaign_id", "advertiser", "industry", "opportunity", "spend_to_date", 
           "start_date", "end_date", "notes", "status", "owner"]

df = pd.DataFrame(data, columns=columns)
df["start_date"] = pd.to_datetime(df["start_date"], errors='coerce')
df["end_date"]   = pd.to_datetime(df["end_date"],   errors='coerce')

# ────────────────────────────────────────────────
# Core Metrics (safe for missing values)
# ────────────────────────────────────────────────
df["days_total"]     = (df["end_date"] - df["start_date"]).dt.days
df["days_elapsed"]   = (pd.to_datetime(today) - df["start_date"]).dt.days.clip(lower=0)
df["days_remaining"] = (df["end_date"] - pd.to_datetime(today)).dt.days.clip(lower=0)

df["pct_time"]   = (df["days_elapsed"] / df["days_total"].replace([0, pd.NA], 1)).clip(upper=1).round(2)
df["pct_spend"]  = (df["spend_to_date"] / df["opportunity"].replace([0, pd.NA], 1)).clip(upper=1).round(2)

df["expected_spend"]       = (df["opportunity"] * df["pct_time"]).round(0)
df["spend_behind"]         = (df["expected_spend"] - df["spend_to_date"]).clip(lower=0).round(0)
df["opportunity_remaining"] = (df["opportunity"] - df["spend_to_date"]).clip(lower=0).round(0)
df["required_daily"]       = (df["opportunity_remaining"] / df["days_remaining"].replace([0, pd.NA], 1)).round(0)
df["avg_daily_spend"]      = (df["spend_to_date"] / df["days_elapsed"].replace([0, pd.NA], 1)).round(2)

# ────────────────────────────────────────────────
# Risk Logic (handles missing data)
# ────────────────────────────────────────────────
def get_risk_components(row):
    # Missing critical data check first
    if pd.isna(row["opportunity"]) or pd.isna(row["start_date"]) or pd.isna(row["end_date"]):
        return 5, "Missing critical data (opportunity/dates)", "", "Clarify with sales on opportunity size and campaign dates"
    
    # Pacing
    gap = row["pct_spend"] - row["pct_time"]
    if gap < -0.30: pacing_score, pacing_why = 5, "Significantly behind pacing"
    elif gap < -0.15: pacing_score, pacing_why = 3, "Moderately behind pacing"
    elif gap < -0.05: pacing_score, pacing_why = 1, "Slightly behind pacing"
    else: pacing_score, pacing_why = 0, "On or ahead of pacing"
    
    # Feasibility
    req = row["required_daily"]
    if pd.isna(req): feas_score, feas_why = 0, ""
    elif req > 2.5 * FEASIBLE_DAILY_SPEND: feas_score, feas_why = 4, "Unrealistic catch-up required"
    elif req > FEASIBLE_DAILY_SPEND:      feas_score, feas_why = 2, "Challenging daily pace needed"
    else: feas_score, feas_why = 0, ""
    
    # Qualitative
    qual_score, qual_issues = 0, ""
    notes_lower = str(row["notes"]).lower()
    if any(w in notes_lower for w in ["delay", "delayed", "launch"]): 
        qual_score += 3; qual_issues += "launch/creative delay, "
    if any(w in notes_lower for w in ["approval", "assets", "creative"]): 
        qual_score += 2; qual_issues += "awaiting approval/assets, "
    if any(w in notes_lower for w in ["low impressions", "inventory"]): 
        qual_score += 3; qual_issues += "inventory/low impressions, "
    if any(w in notes_lower for w in ["budget", "approval delays"]): 
        qual_score += 2; qual_issues += "budget approval issues, "
    qual_issues = qual_issues.rstrip(", ")
    
    return pacing_score + feas_score + qual_score, pacing_why, feas_why, qual_issues

df["risk_score"], df["pacing_why"], df["feas_why"], df["qual_issues"] = zip(*df.apply(get_risk_components, axis=1))

df["risk"] = df["risk_score"].apply(lambda s: "Red" if s >= 6 else "Yellow" if s >= 3 else "Green")

df["why_at_risk"] = df.apply(
    lambda r: r["pacing_why"] if "Missing critical data" in r["pacing_why"] else
              ("On track — no major concerns." if r["risk"] == "Green" else
               f"{r['pacing_why'].capitalize()}. {r['feas_why']} {r['qual_issues']}".strip()),
    axis=1
)

df["next_action"] = df.apply(
    lambda r: "Clarify with sales on opportunity size and campaign dates." if "Missing critical data" in r["why_at_risk"] else
              "Maintain pacing — continue monitoring." if r["risk"] == "Green" else
              "Urgently escalate blockers (approval/delay/inventory) with client/team." if r["qual_issues"] else
              "Unrealistic recovery pace → consider pausing or reallocating budget." if r["feas_why"] else
              "Increase bids 25–50% or expand targeting to accelerate delivery." if r["spend_behind"] > 0 else
              "Review & optimize underperforming placements.",
    axis=1
)

# Portfolio Metrics
total_opp = df["opportunity"].sum(min_count=1)
opp_red = df[df["risk"] == "Red"]["opportunity"].sum(min_count=1)
opp_on_track = total_opp - opp_red if pd.notna(total_opp) else 0

# Styling
def color_rows(row):
    if row["risk"] == "Red":    return ["background-color: #ffebee"] * len(row)
    if row["risk"] == "Yellow": return ["background-color: #fff9c4"] * len(row)
    return ["background-color: #e8f5e9"] * len(row)

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────
st.title("HTS Media · Campaign Risk & Action Dashboard")

tab1, tab2, tab3 = st.tabs(["Overview", "Priority List", "Deep Dive"])

with tab1:

    # ────────────────────────────────────────────────
    # Portfolio Totals
    # ────────────────────────────────────────────────
    total_opp = df["opportunity"].sum(skipna=True)
    opp_red = df[df["risk"] == "Red"]["opportunity"].sum(skipna=True)
    opp_on_track = total_opp - opp_red

    # ────────────────────────────────────────────────
    # Cumulative Opportunity Curve Base
    # ────────────────────────────────────────────────
    curve_df = df.dropna(subset=["start_date", "opportunity"]).copy()
    curve_df = curve_df.sort_values("start_date")

    curve_df["cum_opp"] = curve_df["opportunity"].cumsum()

    # Hypothetical prior year baseline
    curve_df["prior_year"] = curve_df["cum_opp"] * 0.65

    yoy_growth = (
        (curve_df["cum_opp"].iloc[-1] - curve_df["prior_year"].iloc[-1])
        / curve_df["prior_year"].iloc[-1]
    )

    # ────────────────────────────────────────────────
    # KPI Row ✅ UPDATED
    # ────────────────────────────────────────────────
    # % of portfolio at risk
    pct_opp_red = opp_red / total_opp if total_opp > 0 else 0

    c1, c2 = st.columns(2)

    c1.metric(
        "Total Opportunity",
        f"${total_opp:,.0f}",
        f"{yoy_growth:.1%} YoY"
    )

    c2.metric(
        "Opportunity At Risk",
        f"${opp_red:,.0f} ({pct_opp_red:.1%})"
    )
    st.write("---")

    st.subheader("Portfolio Opportunity Growth")

    # ────────────────────────────────────────────────
    # Opportunity Curve
    # ────────────────────────────────────────────────
    base = alt.Chart(curve_df)

    current_line = base.mark_line(size=3).encode(
        x=alt.X("start_date:T", title="Time"),
        y=alt.Y("cum_opp:Q", title="Cumulative Opportunity ($)")
    )

    prior_line = base.mark_line(strokeDash=[6,4]).encode(
        x="start_date:T",
        y="prior_year:Q"
    )

    st.altair_chart(
        (current_line + prior_line).properties(height=350),
        use_container_width=True
    )
with tab2:
    st.subheader("Campaigns Needing Attention")
    
    risk_filter = st.selectbox("Filter by Risk Level", ["All", "Red", "Yellow", "Green"])
    
    filtered_df = df if risk_filter == "All" else df[df["risk"] == risk_filter]
    
    tmp = filtered_df.copy()
    tmp["budget_spent"] = tmp["spend_to_date"]
    tmp["pct_portfolio"] = tmp["opportunity"] / total_opp if pd.notna(total_opp) else 0
    
    view_cols = [
        "risk", "status", "owner", "advertiser", "industry",
        "opportunity", "budget_spent", "spend_behind",
        "pct_portfolio", "days_remaining", "why_at_risk", "next_action"
    ]
    
    totals = pd.DataFrame({
        "risk": ["TOTAL"], "status": [""], "owner": [""], "advertiser": [""], "industry": [""],
        "opportunity": [tmp["opportunity"].sum(min_count=1)],
        "budget_spent": [tmp["budget_spent"].sum()],
        "spend_behind": [tmp["spend_behind"].sum()],
        "pct_portfolio": [tmp["opportunity"].sum(min_count=1) / total_opp if pd.notna(total_opp) else 0],
        "days_remaining": [""], "why_at_risk": [""], "next_action": [""]
    })
    
    display_df = pd.concat([tmp, totals], ignore_index=True)
    
    styled = display_df[view_cols].style.format({
        "opportunity": lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A",
        "budget_spent": "${:,.0f}",
        "spend_behind": "${:,.0f}",
        "pct_portfolio": "{:.1%}"
    }).apply(color_rows, axis=1)
    
    st.dataframe(styled, use_container_width=True, hide_index=True)
    
    st.caption("Green = On pace | Yellow = Recoverable pacing risk | Red = Immediate delivery risk or missing data requiring clarification")

with tab3:
    st.subheader("Campaign Deep Dive")
    
    urgency_filter = st.selectbox("Filter by Urgency", ["All", "≤ 7 days", "≤ 14 days", "≤ 30 days"])
    scoped = df.copy()
    if urgency_filter == "≤ 7 days": scoped = scoped[scoped["days_remaining"] <= 7]
    elif urgency_filter == "≤ 14 days": scoped = scoped[scoped["days_remaining"] <= 14]
    elif urgency_filter == "≤ 30 days": scoped = scoped[scoped["days_remaining"] <= 30]
    
    risk_filter = st.selectbox("Filter by Risk Level", ["All", "Red", "Yellow", "Green"], key="tab3_risk")
    scoped = scoped if risk_filter == "All" else scoped[scoped["risk"] == risk_filter]
    
    if scoped.empty:
        st.warning("No campaigns match the selected filters.")
        advertiser = None
    else:
        advertiser = st.selectbox("Select campaign", sorted(scoped["advertiser"]))
    
    if advertiser:
        camp = df[df["advertiser"] == advertiser].iloc[0]
        
        st.markdown(f"**Risk Level**: **{camp['risk']}**")
        st.markdown(f"**Status**: {camp['status']}")
        st.markdown(f"**Owner**: {camp['owner']}")
        st.markdown(f"**Why it's flagged**: {camp['why_at_risk']}")
        st.markdown(f"**Recommended next step**: **{camp['next_action']}**")
        
        st.write("---")
        
        # Safe formatting for opportunity and pct_spend
        opp_val = camp.get('opportunity', 'N/A')
        opp_str = f"${opp_val:,.0f}" if pd.notna(opp_val) else "N/A"
        pct_str = f"{camp['pct_spend']:.0%}" if pd.notna(opp_val) else "N/A"
        st.write(f"Spend: **${camp['spend_to_date']:,.0f} out of {opp_str}** ({pct_str})")
        
        days_total_str = camp['days_total'] if pd.notna(camp['days_total']) else 'N/A'
        st.write(
            f"Time elapsed: **{camp['pct_time']:.0%}** "
            f"({camp['days_elapsed']} / {days_total_str} days) "
            f"| Behind schedule: **${camp['spend_behind']:,.0f}**"
        )
        
        st.subheader("Finish-on-time requirements")
        avg_daily = camp["avg_daily_spend"]
        gap_daily = (camp["required_daily"] - avg_daily).round(2) if pd.notna(camp.get("required_daily")) else "N/A"
        req_df = pd.DataFrame({
            "Metric": ["Remaining opportunity", "Required daily spend", "Average daily spend (so far)", "Daily spend gap", "Days remaining"],
            "Value": [
                f"${camp['opportunity_remaining']:,.0f}" if pd.notna(camp.get("opportunity_remaining")) else "N/A",
                f"${camp['required_daily']:,.0f}/day" if pd.notna(camp.get("required_daily")) else "N/A",
                f"${avg_daily:,.0f}/day",
                f"${gap_daily:,.0f}/day" if isinstance(gap_daily, (int, float)) else gap_daily,
                f"{camp['days_remaining']}"
            ]
        })
        st.dataframe(req_df, use_container_width=True, hide_index=True)
        
        # ────────────────────────────────────────────────
        # Delivery Trajectory (from your previous working version)
        # ────────────────────────────────────────────────
        st.subheader("Delivery Trajectory (from today)")
        dates = pd.date_range(camp["start_date"], camp["end_date"])
        curve = pd.DataFrame({"date": dates})
        curve["days_from_start"] = (curve["date"] - camp["start_date"]).dt.days
        curve["days_from_today"] = (curve["date"] - pd.to_datetime(today)).dt.days
        
        daily_trend = camp["spend_to_date"] / max(camp["days_elapsed"], 1)
        
        hist = curve[curve["date"] <= pd.to_datetime(today)].copy()
        if camp["days_elapsed"] > 0:
            hist["actual_trend"] = (hist["days_from_start"] / max(camp["days_elapsed"], 1) * camp["spend_to_date"]).clip(0, camp["spend_to_date"])
        else:
            hist["actual_trend"] = 0
        
        future = curve[curve["date"] >= pd.to_datetime(today)].copy()
        future["trend_proj"] = (camp["spend_to_date"] + (future["days_from_today"].clip(lower=0) * daily_trend)).clip(upper=camp["opportunity"] if pd.notna(camp["opportunity"]) else camp["spend_to_date"])
        future["required_path"] = (camp["spend_to_date"] + (future["days_from_today"].clip(lower=0) * camp["required_daily"])).clip(upper=camp["opportunity"] if pd.notna(camp["opportunity"]) else camp["spend_to_date"])
        
        future["gap_low"] = future["trend_proj"]
        future["gap_high"] = future["required_path"]
        
        hist_line = alt.Chart(hist).mark_line(color="#1f77b4", size=3).encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("actual_trend:Q", title="Cumulative Spend ($)")
        )
        
        trend_line = alt.Chart(future).mark_line(color="#1f77b4", strokeDash=[6,4], size=3).encode(
            x="date:T",
            y=alt.Y("trend_proj:Q")
        )
        
        req_line = alt.Chart(future).mark_line(color="#ff7f0e", strokeDash=[5,5], size=3).encode(
            x="date:T",
            y="required_path:Q"
        )
        
        gap_area = alt.Chart(future).mark_area(opacity=0.15, color="#d62728").encode(
            x="date:T",
            y="gap_low:Q",
            y2="gap_high:Q"
        )
        
        today_df = pd.DataFrame({"date": [pd.to_datetime(today)], "spend": [camp["spend_to_date"]]})
        today_rule = alt.Chart(today_df).mark_rule(color="#d62728", size=2, strokeDash=[4,4]).encode(x="date:T")
        today_point = alt.Chart(today_df).mark_point(color="#d62728", size=120, filled=True).encode(x="date:T", y="spend:Q")
        
        end_df = pd.DataFrame({"date": [camp["end_date"]]})
        end_rule = alt.Chart(end_df).mark_rule(color="black", size=2).encode(x="date:T")
        
        lift = max(camp["required_daily"] - daily_trend, 0)
        label_df = pd.DataFrame({
            "date": [pd.to_datetime(today) + pd.Timedelta(days=1)],
            "y": [camp["spend_to_date"] + 1000],
            "label": [f"Req: ${camp['required_daily']:,.0f}/day | Lift needed: +${lift:,.0f}/day"]
        })
        label = alt.Chart(label_df).mark_text(align="left", dx=8, dy=-10, size=12).encode(
            x="date:T",
            y="y:Q",
            text="label:N"
        )
        
        chart = (gap_area + hist_line + trend_line + req_line + today_rule + today_point + end_rule + label).properties(
            height=420,
            title=f"Recovery plan from today → end (End: {camp['end_date'].date() if pd.notna(camp['end_date']) else 'N/A'})"
        ).interactive()
        
        st.altair_chart(chart, use_container_width=True)
        st.caption("Solid blue = actuals to today | Blue dashed = trend continuation | Orange dashed = required recovery | Red shaded = catch-up gap | Black = end date")

st.caption("Prototype — Fictional data — HTS Media interview exercise")
