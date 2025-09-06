import streamlit as st
import pandas as pd
from pathlib import Path

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="Certis Security+ • ROI & Theory Companion",
    page_icon="💡",
    layout="centered"
)

# -------------------------------
# Helpers
# -------------------------------
def compute_roi(annual_ops_cost: float,
                labor_share: float,
                manpower_reduction: float,
                productivity_gain: float,
                platform_cost: float):
    """
    Simple didactic model:
    - Baseline cost = annual_ops_cost
    - Labor cost = annual_ops_cost * labor_share
    - Non-labor cost = annual_ops_cost * (1 - labor_share)
    - Savings from manpower reduction apply to the labor portion
    - Productivity gain is illustrated as a throughput effect (kept for display; not double-counted in cost)
    - New cost = (labor - savings) + non-labor + platform_cost
    """
    labor_cost = annual_ops_cost * labor_share
    non_labor = annual_ops_cost * (1 - labor_share)

    labor_savings = labor_cost * manpower_reduction
    new_ops_cost = (labor_cost - labor_savings) + non_labor + platform_cost
    savings = annual_ops_cost - new_ops_cost
    roi = (savings / platform_cost) if platform_cost else 0.0

    # Avoid division by zero; floor savings at 1 for payback math
    payback_months = 12 * (platform_cost / max(savings, 1)) if platform_cost > 0 else 0.0

    # Throughput effect (not used in cost calc; for narrative)
    throughput_effect = (1 + productivity_gain)

    results = {
        "Baseline cost": annual_ops_cost,
        "New cost": new_ops_cost,
        "Savings": savings,
        "Platform cost": platform_cost,
        "ROI (Savings / Platform)": roi,
        "Payback (months)": payback_months,
        "Labor share": labor_share,
        "Manpower reduction (%)": manpower_reduction,
        "Productivity gain (%)": productivity_gain,
        "Throughput multiplier (1+prod)": throughput_effect
    }
    return results


def load_markdown(relative_path: str) -> str:
    """Safely load a local markdown file if it exists; otherwise return a helpful note."""
    p = Path(__file__).parent / relative_path
    if p.exists():
        return p.read_text(encoding="utf-8")
    return f"> ⚠️ Could not find `{relative_path}`. Make sure your repo contains this file."


def format_money(x: float) -> str:
    try:
        return f"${x:,.0f}"
    except Exception:
        return str(x)


# -------------------------------
# Sidebar (shared inputs)
# -------------------------------
with st.sidebar:
    st.header("Adjust assumptions")

    st.caption("Defaults mirror the case narrative: labor ~80% of cost, ~20% manpower reduction, "
               "~25% productivity gain, platform cost ~$600k.")

    annual_ops_cost = st.number_input(
        "Baseline annual ops cost ($)",
        min_value=500_000,
        step=100_000,
        value=5_000_000
    )
    labor_share = st.slider("Labor share of ops cost", 0.30, 0.95, 0.80)
    manpower_reduction = st.slider("Manpower reduction (%)", 0.00, 0.50, 0.20)
    productivity_gain = st.slider("Productivity gain (%)", 0.00, 0.40, 0.25)
    platform_cost = st.number_input(
        "Annual platform + change mgmt cost ($)",
        min_value=100_000,
        step=50_000,
        value=600_000
    )

    st.markdown("---")
    st.subheader("Quick presets")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("Mall / Jewel-ish"):
            labor_share = 0.80
            manpower_reduction = 0.20
            productivity_gain = 0.25
            platform_cost = 600_000
    with col_p2:
        if st.button("Precinct / JTC-ish"):
            labor_share = 0.78
            manpower_reduction = 0.18
            productivity_gain = 0.25
            platform_cost = 750_000

# -------------------------------
# Tabs
# -------------------------------
tab_calc, tab_sens, tab_theory, tab_about = st.tabs(
    ["ROI Calculator", "Sensitivity", "Theory Map", "About"]
)

# -------------------------------
# ROI Calculator
# -------------------------------
with tab_calc:
    st.title("Security+ ROI Sandbox")
    st.write("Explore how **manpower savings** and **productivity gains** turn into measurable ROI.")

    results = compute_roi(
        annual_ops_cost, labor_share, manpower_reduction, productivity_gain, platform_cost
    )
    df = pd.DataFrame(
        {
            "Metric": [
                "Baseline cost",
                "New cost",
                "Savings",
                "Platform cost",
                "ROI (Savings / Platform)",
                "Payback (months)"
            ],
            "Value": [
                results["Baseline cost"],
                results["New cost"],
                results["Savings"],
                results["Platform cost"],
                round(results["ROI (Savings / Platform)"], 2),
                round(results["Payback (months)"], 1)
            ]
        }
    )

    st.subheader("Results")
    st.table(df)

    # Nice summary chips
    c1, c2, c3 = st.columns(3)
    c1.metric("Savings", format_money(results["Savings"]))
    c2.metric("ROI (x)", f"{results['ROI (Savings / Platform)']:.2f}x")
    c3.metric("Payback", f"{results['Payback (months)']:.1f} months")

    # Download CSV
    csv_df = pd.DataFrame([results])
    st.download_button(
        "Download results as CSV",
        data=csv_df.to_csv(index=False).encode("utf-8"),
        file_name="security_plus_roi_results.csv",
        mime="text/csv"
    )

    st.caption(
        "Didactic model for classroom use. It illustrates why an outcome-based, platform-led operating model "
        "can self-fund via tech-for-labor substitution and productivity improvements."
    )

# -------------------------------
# Sensitivity
# -------------------------------
with tab_sens:
    st.title("Sensitivity analysis")

    st.write("Sweep a lever to see how outcomes change while other inputs stay fixed.")

    opt = st.selectbox(
        "Choose lever to sweep",
        ["Manpower reduction (%)", "Productivity gain (%)"]
    )

    steps = st.slider("Number of steps", 5, 30, 15)

    if opt == "Manpower reduction (%)":
        xs = pd.Series([i / 100 for i in list(range(0, 41, max(1, int(40/(steps-1)))))], name="Manpower cut")
        rows = []
        for mcut in xs:
            r = compute_roi(annual_ops_cost, labor_share, mcut, productivity_gain, platform_cost)
            r["x"] = mcut
            rows.append(r)
        sens_df = pd.DataFrame(rows)
        chart_df = sens_df[["x", "Savings", "ROI (Savings / Platform)", "Payback (months)"]].copy()
        chart_df.rename(columns={"x": "Manpower cut"}, inplace=True)
        st.line_chart(chart_df.set_index("Manpower cut"))
        st.caption("Higher manpower cuts on a high-labor-cost base typically improve ROI and reduce payback.")
    else:
        xs = pd.Series([i / 100 for i in list(range(0, 41, max(1, int(40/(steps-1)))))], name="Productivity gain")
        rows = []
        for pg in xs:
            r = compute_roi(annual_ops_cost, labor_share, manpower_reduction, pg, platform_cost)
            r["x"] = pg
            rows.append(r)
        sens_df = pd.DataFrame(rows)
        chart_df = sens_df[["x", "Savings", "ROI (Savings / Platform)", "Payback (months)"]].copy()
        chart_df.rename(columns={"x": "Productivity gain"}, inplace=True)
        st.line_chart(chart_df.set_index("Productivity gain"))
        st.caption("Productivity gains enhance economics even without deeper manpower cuts.")

# -------------------------------
# Theory Map (loads your markdown files)
# -------------------------------
with tab_theory:
    st.title("Theory ↔ Case Mapping")

    st.markdown("#### Value Proposition Map")
    st.markdown(load_markdown("theory-to-case/value-proposition-map.md"))

    st.markdown("---")
    st.markdown("#### Strategic Challenges Map")
    st.markdown(load_markdown("theory-to-case/strategic-challenges-map.md"))

    st.markdown("---")
    st.markdown("#### Frameworks Applied")
    st.markdown(load_markdown("theory-to-case/frameworks.md"))

# -------------------------------
# About
# -------------------------------
with tab_about:
    st.title("About this companion")

    st.markdown("""
**Course:** Technology & Digitization of Supply Chains  
**School:** SP Jain School of Global Management  
**Team:** Group 4 — Sanchit, Midhun, Venarose, Dhruv

**What this app demonstrates**
- We operationalize the case narrative into a quantitative sandbox.
- We connect slide claims to academic frameworks and page-anchored evidence.
- We make the value-proposition shift (from guard-hours to outcomes) measurable.

**Slide taglines you can add**
- *Value Proposition slide:* **“Explore how manpower savings and productivity gains turn into ROI — scan to try our interactive Security+ model.”**  
- *Caption near QR/link:* **“This sandbox lets you adjust labor share, manpower cuts, and productivity gains to see how Security+ economics deliver measurable ROI.”**
""")

    st.markdown("---")
    st.write("If you have our deck or GitHub link, you can jump between slides, this app, and the theory files for full transparency.")
