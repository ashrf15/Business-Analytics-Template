# utils_capacity/recommendation_capacity/capacity_utilization.py

import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# === Mesiniaga visual identity (blue & white) ===
px.defaults.template = "plotly_white"
PX_SEQ = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#99CCFF"]

# 🔹 Helper function to render CIO tables with 3 nested expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

def _safe_sum(series):
    try:
        return float(pd.to_numeric(series, errors="coerce").fillna(0).sum())
    except Exception:
        return 0.0

def _safe_mean(series):
    try:
        return float(pd.to_numeric(series, errors="coerce").dropna().mean())
    except Exception:
        return float("nan")

def _safe_min(series):
    try:
        return float(pd.to_numeric(series, errors="coerce").dropna().min())
    except Exception:
        return float("nan")

def _safe_max(series):
    try:
        return float(pd.to_numeric(series, errors="coerce").dropna().max())
    except Exception:
        return float("nan")

def _fmt_cur(v):
    try:
        return f"${float(v):,.2f}"
    except Exception:
        return "N/A"

def _ratio(a, b):
    try:
        if float(b) == 0:
            return "0.00"
        return f"{float(a)/float(b):.2f}"
    except Exception:
        return "0.00"

def _modal_bin(series, bins=20):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return None, 0
    cats = pd.cut(s, bins=bins, include_lowest=True)
    vc = cats.value_counts().sort_values(ascending=False)
    top_bin = vc.index[0]
    top_cnt = int(vc.iloc[0])
    return str(top_bin), top_cnt

def _median_by(group_df, value_col, group_col):
    g = (
        group_df[[group_col, value_col]]
        .dropna()
        .groupby(group_col)[value_col]
        .median()
        .sort_values(ascending=False)
    )
    if g.empty:
        return None, None, None, None
    top_name = g.index[0]
    top_val = float(g.iloc[0])
    low_name = g.index[-1]
    low_val = float(g.iloc[-1])
    return top_name, top_val, low_name, low_val

def capacity_utilization(df):

    # =======================
    # 1) CPU Utilization
    # =======================
    with st.expander("📌 CPU Utilization Distribution"):
        if "avg_cpu_utilization" in df.columns:
            cpu = pd.to_numeric(df["avg_cpu_utilization"], errors="coerce")

            # Graph 1: Histogram
            fig_cpu_hist = px.histogram(
                df,
                x="avg_cpu_utilization",
                nbins=20,
                title="CPU Utilization Distribution (%)",
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig_cpu_hist, use_container_width=True, key="cap_cpu_hist")

            # Analysis for Histogram
            cpu_mean = _safe_mean(cpu)
            cpu_min = _safe_min(cpu)
            cpu_max = _safe_max(cpu)
            n_assets = int(df["asset_id"].nunique()) if "asset_id" in df.columns else len(df)
            bin_label, bin_count = _modal_bin(cpu, bins=20)
            st.write(f"""
**What this graph is:** A histogram showing **CPU utilization distribution** across assets.  
- **X-axis:** CPU utilization bands (%).  
- **Y-axis:** Number of assets in each band.

**What it shows in your data:** Average CPU = **{cpu_mean:.2f}%** across **{n_assets}** assets, spanning **{cpu_min:.2f}%–{cpu_max:.2f}%**. The **modal band** is **{bin_label}** with **{bin_count}** assets (typical operating range).

**Overall:** The shape indicates whether capacity is concentrated at lower levels or **approaching saturation**.

**How to read it operationally:**  
1) **Peaks (right tail):** Guardrails/auto-scaling for hot nodes.  
2) **Plateaus (middle):** Maintain headroom and watch drift.  
3) **Downswings (left tail):** Consolidate or right-size underused nodes.  
4) **Mix:** Pair with type-level views to target the biggest cohorts.

**Why this matters:** Matching **provisioned CPU** to **observed load** reduces cost and **prevents SLA risk** on hotspots.
""")

            # Graph 2: Box plot by component type (or global if type missing)
            fig_cpu_box = px.box(
                df,
                x="component_type" if "component_type" in df.columns else None,
                y="avg_cpu_utilization",
                title="CPU Utilization Spread by Component Type (%)",
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig_cpu_box, use_container_width=True, key="cap_cpu_box")

            # Analysis for Box Plot
            if "component_type" in df.columns:
                top_name, top_med, low_name, low_med = _median_by(df, "avg_cpu_utilization", "component_type")
                if top_name is not None:
                    st.write(f"""
**What this graph is:** A box plot showing **CPU utilization spread by component type**.  
- **X-axis:** Component type.  
- **Y-axis:** CPU utilization (%).  

**What it shows in your data:** Highest median CPU in **{top_name} = {top_med:.2f}%**, lowest median in **{low_name} = {low_med:.2f}%**.

**Overall:** Types differ in workload intensity/sizing, implying **inconsistent provisioning practices**.

**How to read it operationally:**  
1) **Peaks (high medians/outliers):** Rebalance and add guardrails.  
2) **Plateaus (tight IQR):** Healthy, keep templates enforced.  
3) **Downswings (low medians):** Consider consolidation or down-tiering.  
4) **Mix:** Standardize SKUs where spread is widest.

**Why this matters:** Reducing **variance by type** simplifies ops and improves **predictability**.
""")
                else:
                    st.write(f"""
**What this graph is:** A box plot showing **estate-wide CPU utilization spread**.  
- **X-axis:** (All assets).  
- **Y-axis:** CPU utilization (%).

**What it shows in your data:** Average CPU ≈ **{cpu_mean:.2f}%**, range **{cpu_min:.2f}%–{cpu_max:.2f}%** with visible outliers.

**Overall:** Dispersion highlights both **underuse** and **hotspots**.

**How to read it operationally:**  
1) **Peaks:** Prioritize hot-node interventions.  
2) **Plateaus:** Maintain consistent capacity envelopes.  
3) **Downswings:** Consolidate to reduce idle cost.  
4) **Mix:** Track IQR changes month-to-month for drift.

**Why this matters:** Tighter spread → **fewer surprises** and steadier SLAs.
""")
            else:
                st.write(f"""
**What this graph is:** A box plot summarizing **CPU utilization dispersion** for the entire estate.  
- **X-axis:** (All assets).  
- **Y-axis:** CPU utilization (%).

**What it shows in your data:** Typical operating band is the interquartile range; outliers mark **exceptional load** conditions.

**Overall:** Use it to spot **under-** and **over-provisioned** assets at a glance.

**How to read it operationally:**  
1) **Peaks:** Guardrails/redistribution.  
2) **Plateaus:** Keep current sizing.  
3) **Downswings:** Right-size or retire.  
4) **Mix:** Compare vs. last month to confirm improvements.

**Why this matters:** Efficient sizing yields **lower OPEX** and **fewer escalations**.
""")

            # Graph 3: Time trend (date-only)
            if "data_timestamp" in df.columns:
                df_ts = df.copy()
                df_ts["data_timestamp"] = pd.to_datetime(df_ts["data_timestamp"], errors="coerce")
                df_ts["day"] = df_ts["data_timestamp"].dt.normalize()
                ts = (
                    df_ts.dropna(subset=["day"])
                    .groupby("day", as_index=False)["avg_cpu_utilization"].mean()
                    .sort_values("day")
                )
                if not ts.empty and len(ts) > 1:
                    fig_cpu_trend = px.line(
                        ts,
                        x="day",
                        y="avg_cpu_utilization",
                        title="Mean CPU Utilization Over Time",
                        color_discrete_sequence=PX_SEQ
                    )
                    fig_cpu_trend.update_traces(mode="lines+markers")
                    fig_cpu_trend.update_layout(xaxis_title="Date", yaxis_title="Average CPU (%)")
                    st.plotly_chart(fig_cpu_trend, use_container_width=True, key="cap_cpu_trend")

                    # Analysis for Trend
                    peak_row = ts.loc[ts["avg_cpu_utilization"].idxmax()]
                    low_row  = ts.loc[ts["avg_cpu_utilization"].idxmin()]
                    ts_mean  = float(ts["avg_cpu_utilization"].mean())
                    st.write(f"""
**What this graph is:** A time series of **daily mean CPU utilization**.  
- **X-axis:** Calendar date.  
- **Y-axis:** Average CPU utilization (%).

**What it shows in your data:** Peak on **{peak_row['day'].date()}** at **{peak_row['avg_cpu_utilization']:.2f}%**; lowest on **{low_row['day'].date()}** at **{low_row['avg_cpu_utilization']:.2f}%**. Period average = **{ts_mean:.2f}%**.

**Overall:** Rising segments imply **demand growth**; flat/falling indicate **stabilization**.

**How to read it operationally:**  
1) **Peaks:** Trigger hot-spot rebalancing and guardrails.  
2) **Plateaus:** Hold gains; keep outflow ≥ inflow.  
3) **Downswings:** Validate which fixes worked (staffing/automation/triage).  
4) **Mix:** Pair with type to ensure critical services are protected.

**Why this matters:** Trend shifts forecast **capacity adds** and **risk windows** ahead of time.
""")

            # Evidence sets for CIO tables
            low_mask = cpu < 30
            high_mask = cpu > 80

            cpu_low_savings = _safe_sum(df.loc[low_mask, "potential_savings_usd"]) if "potential_savings_usd" in df.columns else 0.0
            cpu_low_cost    = _safe_sum(df.loc[low_mask, "cost_per_month_usd"])    if "cost_per_month_usd" in df.columns else 0.0
            cpu_total_cost  = _safe_sum(df["cost_per_month_usd"])                  if "cost_per_month_usd" in df.columns else 0.0

            n_low = int(low_mask.sum())
            n_high = int(high_mask.sum())

            cpu_peak_evi = f"Peak CPU utilization in dataset is {cpu_max:.2f}%, while the minimum is {cpu_min:.2f}%."
            cpu_low_evi  = f"Underutilized cohort (<30%) contains {n_low} assets; modal band {bin_label} has {bin_count} assets."
            cpu_high_evi = f"High-load cohort (>80%) contains {n_high} assets."
            cpu_cost_evi = f"Total monthly run-rate cost recorded is {_fmt_cur(cpu_total_cost)} across the estate."

            # CIO tables (≥4 rows each) with phase details + real math
            cpu_cio = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Consolidate or retire underutilized CPU nodes | **Phase 1 – Identify:** Flag assets with average CPU below 30 percent across the period and confirm that this low utilization is stable over time rather than a one-day anomaly. <br><br>**Phase 2 – Migrate:** Plan and execute migration of remaining workloads from these low-utilization assets onto denser hosts that are operating closer to the estate average of {cpu_mean:.2f} percent but still within safe headroom. <br><br>**Phase 3 – Decommission:** After successful migration, decommission the freed hosts and ensure that related licenses, support contracts, and power allocations are removed from the cost base. | - Reduces the total number of active hosts so that infrastructure running costs are lower and the environment becomes simpler to operate.<br><br>- Lowers power and cooling consumption because fewer physical servers are needed to handle the same amount of work.<br><br>- Frees up rack space and data centre capacity which can be used for future growth or to avoid new hardware purchases.<br><br>- Cuts software and support renewals that are tied to retired hardware which directly reduces operating expenditure. | Savings Rate = Σ(potential_savings_usd for CPU<30) / Σ(cost_per_month_usd for CPU<30) = { _fmt_cur(cpu_low_savings) } / { _fmt_cur(cpu_low_cost) } = **{ _ratio(cpu_low_savings, cpu_low_cost) }x**. | {cpu_low_evi} Histogram left tail isolates idle capacity; {cpu_cost_evi}. |
| Standardize CPU sizes to 2–3 right-sized SKUs | **Phase 1 – Template:** Define a small set of standard CPU and memory configurations that are suitable for the main workload categories so that new servers and virtual machines follow clear sizing rules. <br><br>**Phase 2 – Migrate:** Gradually move over-sized or unusual configurations into the closest standard SKU without allowing utilization to exceed a safe range around {cpu_mean:.2f} percent. <br><br>**Phase 3 – Enforce:** Apply technical guardrails and approval steps in provisioning tools so that new deployments automatically comply with the standard SKUs. | - Reduces over provisioning because teams have to choose from a small number of standard sizes rather than picking arbitrary large configurations.<br><br>- Simplifies procurement and capacity planning since recurring purchases are built around a predictable set of hardware or VM sizes.<br><br>- Improves performance predictability because similar workloads run on consistent capacity envelopes across environments.<br><br>- Decreases the number of one-off exceptions that consume engineering time and make the platform harder to support. | Avoided Cost ≈ (Oversize share × Count × Avg node cost). Oversize share inferred from box-plot dispersion between types (top median {top_name if 'top_name' in locals() and top_name else '—'}). | Box plot shows cross-type variance; high medians and outliers indicate oversize risk to normalize. |
| Rehost low-utilization VMs to denser hosts | **Phase 1 – Pool:** Group virtual machines with average CPU below 30 percent into logical pools that respect application constraints, data locality, and compliance rules. <br><br>**Phase 2 – Pack:** Place these virtual machines onto target hosts so that overall host utilization moves closer to {cpu_mean:.2f} percent without breaching safe capacity thresholds. <br><br>**Phase 3 – Verify:** Monitor performance and incident behaviour after consolidation and then power down any hosts that are no longer required. | - Unlocks direct operating expenditure savings because entire physical hosts can be turned off once workloads are consolidated.<br><br>- Raises utilization efficiency so that each remaining host delivers more useful work per unit of capacity consumed.<br><br>- Improves power usage effectiveness by reducing the number of servers that must be powered and cooled to support the environment.<br><br>- Simplifies inventory and asset management because there are fewer hardware items to track, maintain, and audit. | Hosts Avoided × Monthly host cost (use n_low={n_low} as upper bound of candidate VMs). | Histogram modal band {bin_label} ({bin_count} assets) and the left tail identify the main consolidation pool. |
| Hot-node throttling avoidance via burst buffers | **Phase 1 – Detect:** Identify and tag nodes that regularly exceed 80 percent CPU utilization so that the most heavily loaded assets are clearly visible in monitoring. <br><br>**Phase 2 – Buffer:** Introduce short term burst capacity through auto-scaling, temporary resource boosts, or workload redistribution to protect these nodes during peak periods. <br><br>**Phase 3 – Tune:** Review peak events each month and adjust configuration, thresholds, or placement so that repeated high utilization incidents are reduced over time. | - Reduces the risk of throttling and performance degradation on nodes that consistently run near maximum CPU utilization.<br><br>- Protects latency-sensitive applications by ensuring they have access to additional headroom when demand suddenly increases.<br><br>- Decreases firefighting effort for operations teams because fewer incidents are driven by predictable saturation on a small set of hot nodes.<br><br>- Creates a more stable and predictable environment during peak usage windows which supports better customer experience. | Risk Cohort Size = n_high={n_high}; Cost at Risk ≈ (Incidents avoided × avg incident cost). | {cpu_high_evi}; right-tail density in histogram and peak at {cpu_max:.2f}% underline risk hotspots. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Implement CPU guardrails and auto-scaling | **Phase 1 – Thresholds:** Define clear alert thresholds for sustained CPU utilization above 80 percent and make sure they are configured in monitoring tools that teams actually watch. <br><br>**Phase 2 – Actions:** For services that breach these thresholds, configure automatic responses such as horizontal scaling, vertical scaling, or prioritized workload shedding. <br><br>**Phase 3 – Review:** Review alert and scaling behaviour every month to refine thresholds and avoid both false positives and missed risk windows. | - Reduces the chance that users experience slow responses or errors because systems can react before CPU saturation completely exhausts capacity.<br><br>- Keeps incident counts lower by catching early warning signals instead of waiting for outages or severe service degradation.<br><br>- Makes performance more predictable under variable demand because scaling rules are applied consistently whenever thresholds are crossed.<br><br>- Helps operations teams spend less time manually chasing capacity problems and more time on strategic improvements. | SLA Gain ≈ Δ(SLA-met %) after rollout. Target cohort size: n_high={n_high}. | {cpu_high_evi}; trend and high-tail bins show where guardrails provide the most value. |
| Hot-spot rebalancing across hosts | **Phase 1 – Identify:** Use utilization graphs to identify specific hosts and services that regularly exceed healthy CPU levels and classify them as hotspots. <br><br>**Phase 2 – Rebalance:** Redistribute workloads between hosts by moving noisy neighbours away or reassigning services while respecting affinity, licensing, and compliance constraints. <br><br>**Phase 3 – Validate:** Monitor the affected hosts after rebalancing to ensure CPU utilization moves closer to {cpu_mean:.2f} percent and remains within a stable band. | - Reduces chronic hotspots that cause unpredictable performance issues and service degradation for the users running on those hosts.<br><br>- Increases the overall throughput of the environment because capacity is shared more evenly across available infrastructure.<br><br>- Lowers the probability of CPU-related incidents and emergency interventions on a small number of overloaded nodes.<br><br>- Provides evidence-based input to future capacity planning by clarifying which workloads truly need more resources and which just needed rebalancing. | Time Saved = (Δ response time) × (requests on affected nodes). | Peak day and lowest day gap {cpu_max:.2f}%–{cpu_min:.2f}% from trend informs urgency. |
| Predictive capacity planning | **Phase 1 – Model:** Use historical daily mean CPU utilization to establish a baseline trend and identify typical growth patterns over weeks and months. <br><br>**Phase 2 – Forecast:** Convert this trend into forward-looking capacity curves that show when current infrastructure will approach or exceed safe utilization limits. <br><br>**Phase 3 – Align:** Synchronize procurement, change windows, and scaling actions with these forecasts so that new capacity arrives before demand creates a risk. | - Avoids last-minute capacity purchases and rushed implementation work that can introduce errors or downtime.<br><br>- Creates a structured link between business growth, demand patterns, and technology capacity planning decisions.<br><br>- Reduces the risk of SLA breaches driven by capacity exhaustion because infrastructure upgrades are scheduled proactively.<br><br>- Gives management a clear view of when investments are required and what risks are mitigated by each decision. | Peak Deferral Value ≈ (months deferred × peak capacity cost). | {cpu_peak_evi}; trend direction provides early signal for when capacity thresholds will be hit. |
| Golden signals dashboard | **Phase 1 – Instrument:** Ensure CPU, queue length, and error rate metrics are consistently collected and displayed on a central dashboard for all critical services. <br><br>**Phase 2 – Correlate:** Regularly compare spikes in CPU utilization with error bursts and queue build-up to understand which patterns typically lead to user-visible issues. <br><br>**Phase 3 – Iterate:** Perform weekly or monthly reviews of incidents using this dashboard and document follow-up actions to improve detection and responses. | - Shortens the time it takes to detect and diagnose performance problems because engineers can see key signals in one place.<br><br>- Lowers mean time to resolve incidents since teams can quickly correlate CPU stress with error rates and backlog behaviour.<br><br>- Reduces the frequency of repeated patterns because incident reviews feed improvements back into monitoring rules and runbooks.<br><br>- Builds a shared understanding of system health across teams which improves coordination during high-impact events. | MTTR Reduction × incident count; tie to n_high hotspots for target scope. | High-tail histogram bins and box plot outliers map directly to nodes that should be highlighted in the dashboard. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate planned CPU optimizations | **Phase 1 – Calendar:** Build a simple change calendar that shows when CPU-related optimization work such as consolidation or scaling will occur and which services are involved. <br><br>**Phase 2 – Impact:** For each optimization, describe the expected impact, potential risk, and rollback plan in language that business users can easily understand. <br><br>**Phase 3 – Report:** After each optimization wave, share before and after metrics that show how utilization and performance have changed. | - Reduces surprise and confusion when performance changes happen because users know in advance what is being done and why it matters.<br><br>- Builds trust that the infrastructure team is actively managing capacity rather than reacting only when issues appear.<br><br>- Lowers escalation volume since customers can see that remediation work is scheduled and being tracked transparently.<br><br>- Creates a clear record of improvements that can be used in service reviews and contractual discussions. | Complaints Avoided × handling minutes; use troughs from trend to time communication. | Trend shows low-demand windows and histogram spread shows the overall posture of the estate. |
| Priority safeguards for critical services | **Phase 1 – Tag:** Identify which applications and services are considered critical for business operations and label the infrastructure supporting them as high priority. <br><br>**Phase 2 – Reserve:** Ensure that these critical services have reserved CPU headroom or isolation so that they are protected from noisy neighbours and general load spikes. <br><br>**Phase 3 – Monitor:** Continuously track utilization and performance for these critical paths and trigger alerts when patterns deviate from expected baselines. | - Protects the most important user journeys from CPU-related performance drops during busy periods.<br><br>- Reduces the likelihood that key customers or high-value transactions are impacted by resource contention.<br><br>- Provides clear evidence to stakeholders that critical services are treated differently and receive stronger protection.<br><br>- Supports better prioritisation during incident response because teams know exactly which systems must be preserved first. | Churn Risk Avoided proxy via protected transactions on high-risk days. | {cpu_high_evi} exposes risk concentration that can directly affect critical customer interactions. |
| Expectation management during peaks | **Phase 1 – Trigger:** Use CPU trend and forecasting to identify days or periods where utilization is expected to approach historical peaks such as {cpu_max:.2f} percent. <br><br>**Phase 2 – ETA:** Proactively inform affected users about potential slowdowns or maintenance actions and provide realistic response time expectations. <br><br>**Phase 3 – Review:** After the peak period, compare satisfaction and incident data to see whether the communication approach reduced frustration. | - Lowers user frustration because customers are not blindsided by slow responses or short maintenance windows during peak load days.<br><br>- Decreases duplicate contacts to the service desk since people already know that performance might be temporarily affected.<br><br>- Helps business teams plan critical activities around known stress windows rather than colliding with peak technical load.<br><br>- Provides feedback on which communication styles or channels are most effective during high-demand events. | Contact Deflection = repeats avoided × minutes per contact. | Peaks at {cpu_max:.2f}% in the trend justify proactive communication and expectation management. |
| Customer-agent pairing for impacted services | **Phase 1 – Map:** Associate specific service owners or technical leads with the assets and services that form the high CPU tail so that accountability during incidents is clear. <br><br>**Phase 2 – Assign:** During known high-demand periods, assign named contacts or agents who will handle escalations and user questions for these high-risk services. <br><br>**Phase 3 – Measure:** Track user satisfaction and resolution times for issues handled by these dedicated contacts and refine the model if needed. | - Speeds up triage and resolution for users affected by CPU-related problems because the right experts are already aligned to those services.<br><br>- Makes communication during incidents more direct and clear as users know who is responsible for a given service.<br><br>- Improves perceived service quality for critical or heavily impacted users who receive more focused support.<br><br>- Encourages ownership and continuous improvement among service teams assigned to high-risk parts of the estate. | CSAT uplift × retention value. | Right-tail assets (n_high={n_high}) indicate where users are most likely to feel impact first and where this pairing model adds the most value. |
"""
            }
            render_cio_tables("CPU Utilization — CIO Recommendations", cpu_cio)

        else:
            st.info("Column 'avg_cpu_utilization' not found in dataset.")

    # =======================
    # 2) Memory Utilization
    # =======================
    with st.expander("📌 Memory Utilization Distribution"):
        if "avg_memory_utilization" in df.columns:
            mem = pd.to_numeric(df["avg_memory_utilization"], errors="coerce")

            # Graph 1: Box plot by component type
            fig_mem_box = px.box(
                df,
                x="component_type" if "component_type" in df.columns else None,
                y="avg_memory_utilization",
                title="Memory Utilization Spread by Component Type (%)",
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig_mem_box, use_container_width=True, key="cap_mem_box")

            # Analysis for Memory Box
            mem_mean = _safe_mean(mem)
            mem_min = _safe_min(mem)
            mem_max = _safe_max(mem)
            n_assets = int(df["asset_id"].nunique()) if "asset_id" in df.columns else len(df)
            if "component_type" in df.columns:
                top_name, top_med, low_name, low_med = _median_by(df, "avg_memory_utilization", "component_type")
                if top_name is not None:
                    st.write(f"""
**What this graph is:** A box plot showing **memory utilization spread by component type**.  
- **X-axis:** Component type.  
- **Y-axis:** Memory utilization (%).

**What it shows in your data:** Highest median memory in **{top_name} = {top_med:.2f}%**, lowest median in **{low_name} = {low_med:.2f}%**. Estate-wide average = **{mem_mean:.2f}%** over **{n_assets}** assets (range **{mem_min:.2f}%–{mem_max:.2f}%**).

**Overall:** Variability by type implies **different workload intensity/sizing**.

**How to read it operationally:**  
1) **Peaks:** Rebalance, add guardrails.  
2) **Plateaus:** Keep templates and monitoring.  
3) **Downswings:** Downsize RAM or consolidate.  
4) **Mix:** Standardize where spread is widest.

**Why this matters:** Tuning memory by type improves **throughput, stability, and cost**.
""")
                else:
                    st.write(f"""
**What this graph is:** A box plot summarizing **estate-wide memory utilization**.  
- **X-axis:** (All assets).  
- **Y-axis:** Memory utilization (%).

**What it shows in your data:** Average **{mem_mean:.2f}%**, range **{mem_min:.2f}%–{mem_max:.2f}%**, with outliers indicating atypical memory pressure or over-allocation.

**Overall:** Dispersion surfaces both **risk** (high) and **waste** (low).

**How to read it operationally:**  
1) **Peaks:** Guardrails/reallocation to reduce paging.  
2) **Plateaus:** Maintain sizing discipline.  
3) **Downswings:** Consider downsizing to cut cost.  
4) **Mix:** Track IQR month-over-month.

**Why this matters:** Efficient memory sizing reduces **latency incidents** and **OPEX**.
""")
            else:
                st.write(f"""
**What this graph is:** A box plot of **memory utilization** for the estate.  
- **X-axis:** (All assets).  
- **Y-axis:** Memory utilization (%).

**What it shows in your data:** Across **{n_assets}** assets, memory ranges **{mem_min:.2f}%–{mem_max:.2f}%** with an average of **{mem_mean:.2f}%**.

**Overall:** IQR shows the typical envelope; outliers flag **exceptional cases**.

**How to read it operationally:**  
1) **Peaks:** Add headroom / rebalance.  
2) **Plateaus:** Maintain current allocations.  
3) **Downswings:** Right-size RAM tiers.  
4) **Mix:** Compare vs. CPU to detect imbalance.

**Why this matters:** Balanced memory avoids **slowdowns** and **escalations**.
""")

            # Graph 2: Histogram
            fig_mem_hist = px.histogram(
                df,
                x="avg_memory_utilization",
                nbins=20,
                title="Memory Utilization Distribution (%)",
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig_mem_hist, use_container_width=True, key="cap_mem_hist")

            # Analysis for Memory Histogram
            bin_label, bin_count = _modal_bin(mem, bins=20)
            st.write(f"""
**What this graph is:** A histogram showing **memory utilization distribution**.  
- **X-axis:** Memory utilization bands (%).  
- **Y-axis:** Asset count per band.

**What it shows in your data:** Average memory = **{mem_mean:.2f}%** (range **{mem_min:.2f}%–{mem_max:.2f}%**). **Modal band** = **{bin_label}** with **{bin_count}** assets.

**Overall:** Shape indicates whether memory is mostly **under-used** or **near saturation**.

**How to read it operationally:**  
1) **Peaks (right tail):** Safeguards for latency-sensitive apps.  
2) **Plateaus:** Maintain headroom; watch drift.  
3) **Downswings (left tail):** Down-tier RAM/licensing.  
4) **Mix:** Cross-check with incidents for user impact.

**Why this matters:** Proper memory sizing preserves **performance** and reduces **waste**.
""")

            # Graph 3: Memory trend over time
            if "data_timestamp" in df.columns:
                df_ts = df.copy()
                df_ts["data_timestamp"] = pd.to_datetime(df_ts["data_timestamp"], errors="coerce")
                df_ts["day"] = df_ts["data_timestamp"].dt.normalize()
                ts = (
                    df_ts.dropna(subset=["day"])
                    .groupby("day", as_index=False)["avg_memory_utilization"].mean()
                    .sort_values("day")
                )
                if not ts.empty and len(ts) > 1:
                    fig_mem_trend = px.line(
                        ts,
                        x="day",
                        y="avg_memory_utilization",
                        title="Mean Memory Utilization Over Time",
                        color_discrete_sequence=PX_SEQ
                    )
                    fig_mem_trend.update_traces(mode="lines+markers")
                    fig_mem_trend.update_layout(xaxis_title="Date", yaxis_title="Average Memory (%)")
                    st.plotly_chart(fig_mem_trend, use_container_width=True, key="cap_memory_trend")

                    # Analysis for Memory Trend
                    peak_row = ts.loc[ts["avg_memory_utilization"].idxmax()]
                    low_row  = ts.loc[ts["avg_memory_utilization"].idxmin()]
                    ts_mean  = float(ts["avg_memory_utilization"].mean())
                    st.write(f"""
**What this graph is:** A time series of **daily mean memory utilization**.  
- **X-axis:** Calendar date.  
- **Y-axis:** Average memory utilization (%).

**What it shows in your data:** Peak on **{peak_row['day'].date()}** at **{peak_row['avg_memory_utilization']:.2f}%**; lowest on **{low_row['day'].date()}** at **{low_row['avg_memory_utilization']:.2f}%**. Period average = **{ts_mean:.2f}%**.

**Overall:** Rising segments = **pressure build-up**; falling = **relief**.

**How to read it operationally:**  
1) **Peaks:** Leak checks / scaling actions.  
2) **Plateaus:** Maintain buffers.  
3) **Downswings:** Confirm which fixes worked.  
4) **Mix:** Align maintenance with low-pressure windows.

**Why this matters:** Trends reveal **risk windows** and timing for **safe changes**.
""")

            # Evidence and masks
            low_mask = mem < 30
            high_mask = mem > 80
            n_low = int(low_mask.sum())
            n_high = int(high_mask.sum())

            mem_low_savings = _safe_sum(df.loc[low_mask, "potential_savings_usd"]) if "potential_savings_usd" in df.columns else 0.0
            mem_low_cost    = _safe_sum(df.loc[low_mask, "cost_per_month_usd"])    if "cost_per_month_usd" in df.columns else 0.0
            mem_total_cost  = _safe_sum(df["cost_per_month_usd"])                  if "cost_per_month_usd" in df.columns else 0.0

            mem_peak_evi = f"Peak memory utilization observed at {mem_max:.2f}% with a minimum of {mem_min:.2f}%."
            mem_low_evi  = f"Underutilized memory cohort (<30%) includes {n_low} assets; modal band {bin_label} has {bin_count} assets."
            mem_high_evi = f"High-pressure memory cohort (>80%) includes {n_high} assets."
            mem_cost_evi = f"Total recorded monthly cost is {_fmt_cur(mem_total_cost)}."

            mem_cio = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Downsize RAM on persistently low-use nodes | **Phase 1 – Identify:** Track assets whose memory utilization remains below 30 percent over a meaningful period rather than just a single snapshot. <br><br>**Phase 2 – Resize:** Propose smaller RAM configurations that still keep some headroom but move utilization closer to a safe band around {mem_mean:.2f} percent. <br><br>**Phase 3 – Validate:** After resizing, monitor performance to confirm that there is no paging or user-visible slowdown before treating the change as fully successful. | - Reduces spending on memory and memory-based licenses because capacity that is not being used is no longer paid for unnecessarily.<br><br>- Encourages a disciplined approach to hardware sizing so that teams request only the amount of RAM that is actually needed for their workloads.<br><br>- Lowers power usage because smaller memory footprints often consume less energy over time.<br><br>- Frees budget that can be redirected to higher-value capacity upgrades where utilization and user impact are visibly higher. | Savings Rate = Σ(potential_savings_usd for Mem<30) / Σ(cost_per_month_usd for Mem<30) = { _fmt_cur(mem_low_savings) } / { _fmt_cur(mem_low_cost) } = **{ _ratio(mem_low_savings, mem_low_cost) }x**. | {mem_low_evi}; histogram left tail and box lower whiskers highlight candidates; {mem_cost_evi}. |
| Consolidate workloads on denser memory hosts | **Phase 1 – Pool:** Group low-memory-utilization assets into migration pools that respect application compatibility and data locality. <br><br>**Phase 2 – Pack:** Move these workloads onto fewer hosts while keeping post-consolidation utilization below 80 percent so that stability is not compromised. <br><br>**Phase 3 – Power down:** Decommission or repurpose hosts that no longer carry active workloads and verify that monitoring shows no regression. | - Decreases the number of physical or virtual hosts that need to be maintained which directly reduces operational overhead.<br><br>- Raises memory utilization on remaining hosts so that invested capacity is used more efficiently and delivers better value.<br><br>- Delays or avoids future hardware purchases because existing infrastructure is used more fully before expansion is considered.<br><br>- Simplifies backup, patching, and monitoring activities since there are fewer machines to protect and manage. | Hosts Avoided × monthly host cost; upper bound from n_low={n_low}. | Histogram concentration at low bands supports consolidation of lightly used memory resources. |
| License tier alignment by RAM footprint | **Phase 1 – Map:** Build a clear mapping between memory configurations and software license tiers so that the cost impact of different RAM sizes is transparent. <br><br>**Phase 2 – Down-tier:** Identify systems where current memory size forces a higher license tier even though utilization is consistently low and plan a safe move to a lower tier. <br><br>**Phase 3 – Automate:** Introduce checks in provisioning and change workflows that highlight configurations that push workloads into higher license tiers without clear justification. | - Lowers recurring license costs by avoiding paying for high tiers that are not actually necessary for the workload.<br><br>- Makes compliance and license management easier because configurations are more closely aligned with documented tier rules.<br><br>- Encourages teams to think about licensing impact when designing or modifying their server footprints.<br><br>- Helps financial stakeholders see a direct connection between technical configuration choices and recurring software spend. | Δ Tier Count × Fee per tier; focus on low-band assets (modal {bin_label}, {bin_count} assets). | Distribution shows many assets below thresholds associated with higher-cost license levels. |
| Hot-memory relief on >80% nodes | **Phase 1 – Detect:** Continuously monitor and flag nodes where memory utilization is above 80 percent for extended periods so that stressed systems are clearly visible. <br><br>**Phase 2 – Remedy:** Plan actions such as adding RAM, moving memory-heavy workloads elsewhere, or optimizing applications that consume excessive memory on those nodes. <br><br>**Phase 3 – Verify:** Track latency, error rates, and memory utilization after changes to ensure that the high-pressure state has been relieved. | - Reduces the likelihood of paging storms and severe slowdowns that occur when memory is exhausted and the system falls back on disk.<br><br>- Improves responsiveness for users and applications that rely on these nodes during busy periods.<br><br>- Decreases the number of incidents opened due to memory-related performance issues and system instability.<br><br>- Extends the useful life of the environment by systematically removing the worst memory bottlenecks instead of letting them accumulate. | Risk Cohort Size = n_high={n_high}; impact = reduction in high-percentile latency × requests. | {mem_high_evi}; right-tail bins and high medians identify main memory hotspots. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Guardrails at 80 percent memory | **Phase 1 – Thresholds:** Configure clear alert thresholds that trigger when memory utilization remains above 80 percent for a defined period. <br><br>**Phase 2 – Actions:** Link these alerts to concrete actions such as scaling up, scaling out, or workload redistribution for affected services. <br><br>**Phase 3 – Review:** Regularly review alert behaviour and adjust thresholds or actions to balance noise and risk. | - Reduces the chance that users experience slowdown due to memory saturation because intervention happens before systems reach critical levels.<br><br>- Keeps incident volumes lower by correcting early warning signs rather than waiting for outages or severe degradation.<br><br>- Helps maintain stable throughput and response times under varying load conditions.<br><br>- Gives operations teams confidence that memory pressure is being managed consistently and not left to ad hoc decision making. | Δ Response Time × request volume on high-risk nodes (n_high={n_high}). | Histogram right tail and box outliers represent the group of nodes where guardrails matter most. |
| NUMA-aware placement and rebalancing | **Phase 1 – Audit:** Analyse how applications use memory across NUMA nodes to detect patterns that increase cross-node access and reduce efficiency. <br><br>**Phase 2 – Rebalance:** Adjust workload placement or configuration to improve locality so that memory accesses stay closer to the cores that are executing the work. <br><br>**Phase 3 – Monitor:** Monitor cache and latency metrics after changes to confirm that performance has improved and remains stable. | - Improves effective memory bandwidth for demanding applications by reducing costly remote memory accesses.<br><br>- Stabilises latency for workloads that are sensitive to memory performance, especially under high load.<br><br>- Increases utilisation efficiency since the same hardware can handle more work when memory access is optimised.<br><br>- Provides a clear, technical explanation for performance improvements that can be communicated to stakeholders. | Throughput gain × value per transaction on affected nodes. | Box spread highlights imbalances by type that may be influenced by poor placement. |
| Memory leak detection cadence | **Phase 1 – Baseline:** Establish a reference pattern for memory utilisation growth over time for each major service so that unusual behaviour stands out. <br><br>**Phase 2 – Detect:** Use this baseline to automatically flag services where memory usage climbs steadily without returning to normal levels, indicating a possible leak. <br><br>**Phase 3 – Fix:** Prioritise and resolve these issues through code fixes or configuration changes and confirm that the post-fix trend is flat or cyclical as expected. | - Prevents slow-burning incidents where performance gradually deteriorates as memory is consumed and never freed.<br><br>- Reduces unplanned restarts and emergency maintenance caused by memory exhaustion in long-running services.<br><br>- Improves user experience over long periods because systems remain responsive during extended workloads or campaigns.<br><br>- Helps development teams focus remediation effort on services that show clear evidence of leaks instead of guessing. | Incidents avoided × MTTR cost; justify with days near peaks in trend. | Trend shows sustained rises and relief periods that reveal where leak detection is needed. |
| Read-heavy cache optimization | **Phase 1 – Profile:** Identify applications and endpoints that generate a high volume of read requests, especially during peak memory utilization days. <br><br>**Phase 2 – Cache:** Design or adjust caching strategies for these read-heavy flows so that frequently accessed data is served from memory-efficient caches rather than always from primary storage. <br><br>**Phase 3 – Validate:** Monitor cache hit ratios and end-to-end latency to confirm that the new cache design reduces memory pressure and improves response times. | - Lowers the load on backend systems by serving repeated requests more efficiently from cache.<br><br>- Improves response times for users as frequently accessed data is returned faster from memory-based caches.<br><br>- Reduces contention on shared resources such as databases and storage arrays during traffic spikes.<br><br>- Provides a scalable way to handle growth in read traffic without immediately requiring large memory or hardware upgrades. | Δ Backend calls × time saved per call. | Peak day {mem_max:.2f}% vs low {mem_min:.2f}% supports targeting optimisation where memory pressure is highest. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Publish memory capacity posture | **Phase 1 – Scorecards:** Prepare simple monthly scorecards that show memory utilization trends, thresholds, and actions in non-technical language. <br><br>**Phase 2 – Actions:** Clearly link each highlighted risk to an owner and a due date so that stakeholders understand who is responsible for improvement. <br><br>**Phase 3 – Outcomes:** Present updates on these scorecards in regular forums, showing how actions have changed the trend. | - Increases transparency so that stakeholders feel informed about memory risks before they lead to incidents.<br><br>- Reduces escalations driven by uncertainty because there is a visible plan to address hotspots and underutilized areas.<br><br>- Creates a shared understanding of capacity posture which helps align business priorities and technical work.<br><br>- Builds confidence that memory-related performance issues are being tracked and addressed systematically. | Complaints avoided × handling minutes; correlate to trough scheduling. | Distribution and trend communicate capacity posture in a way that non-technical audiences can understand. |
| Protect latency-sensitive flows | **Phase 1 – Tag:** Identify which business transactions or user journeys are most sensitive to memory-related performance issues and tag the services that support them. <br><br>**Phase 2 – Reserve:** Ensure these critical flows have reserved memory headroom and appropriate isolation from noisy neighbours in the platform. <br><br>**Phase 3 – Observe:** Continuously measure SLOs and configure quick rollback options if memory pressure begins to affect these flows. | - Keeps the most important user journeys fast and stable even when the overall environment is under stress.<br><br>- Reduces the number of high-severity incidents that affect many users at once because critical flows are better protected.<br><br>- Improves customer satisfaction and trust among key user groups whose work depends on consistently responsive systems.<br><br>- Supports commercial discussions by demonstrating that high-value services receive dedicated performance safeguards. | Reduction in p95 latency × critical requests. | Right-tail cohort (n_high={n_high}) maps to zones where latency-sensitive flows are most at risk. |
| Maintenance scheduling using trend | **Phase 1 – Pick troughs:** Use memory utilization trends to select days or time windows with lower pressure as preferred maintenance slots. <br><br>**Phase 2 – Notify:** Inform users in advance about planned work in these windows, describing expected impact and timing. <br><br>**Phase 3 – Validate:** Compare incident rates and user feedback for maintenance performed in low-pressure periods versus high-pressure periods. | - Reduces the probability that maintenance work triggers user-visible performance issues because it runs when memory demand is at its lowest.<br><br>- Lowers user frustration by aligning changes with periods when they are less dependent on peak performance.<br><br>- Improves the predictability of maintenance outcomes since resource contention is less likely to distort results.<br><br>- Provides data to refine maintenance policies and scheduling practices over time. | Δ Incidents during maintenance windows. | Trend identifies safe windows where memory demand is lowest, often associated with {mem_min:.2f}% periods. |
| Knowledge capture from high-performers | **Phase 1 – Identify:** Look for systems that operate near the median utilization of {mem_mean:.2f} percent with consistently low incident rates and classify them as high performers. <br><br>**Phase 2 – Document:** Capture their configuration, capacity settings, and operational playbooks so that others can reproduce the same patterns. <br><br>**Phase 3 – Replicate:** Apply these successful patterns to similar systems and monitor whether their memory utilization and stability improve. | - Spreads good engineering practices from a few high-performing systems to a broader part of the environment.<br><br>- Reduces variability in performance and incident rates between teams because successful patterns are documented and reused.<br><br>- Shortens the learning curve for new services by giving them proven starting configurations instead of guessing.<br><br>- Builds a culture of continuous improvement where teams learn from internal successes rather than only from failures. | Variance reduction × tickets affected. | Box plot shows tight IQR bands that can be used as templates for other systems. |
"""
            }
            render_cio_tables("Memory Utilization — CIO Recommendations", mem_cio)

        else:
            st.info("Column 'avg_memory_utilization' not found in dataset.")

    # =======================
    # 3) Storage Utilization
    # =======================
    with st.expander("📌 Storage Utilization and Capacity"):
        if "avg_storage_utilization" in df.columns:
            sto = pd.to_numeric(df["avg_storage_utilization"], errors="coerce")

            # Graph 1: Histogram
            fig_sto_hist = px.histogram(
                df,
                x="avg_storage_utilization",
                nbins=20,
                title="Storage Utilization Distribution (%)",
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig_sto_hist, use_container_width=True, key="cap_sto_hist")

            # Analysis for Storage Histogram
            sto_mean = _safe_mean(sto)
            sto_min = _safe_min(sto)
            sto_max = _safe_max(sto)
            n_assets = int(df["asset_id"].nunique()) if "asset_id" in df.columns else len(df)
            bin_label, bin_count = _modal_bin(sto, bins=20)
            st.write(f"""
**What this graph is:** A histogram showing **storage utilization distribution**.  
- **X-axis:** Storage utilization bands (%).  
- **Y-axis:** Asset count per band.

**What it shows in your data:** Average storage = **{sto_mean:.2f}%** across **{n_assets}** assets (range **{sto_min:.2f}%–{sto_max:.2f}%**). **Modal band** = **{bin_label}** with **{bin_count}** assets.

**Overall:** Reveals concentration of **cold** vs **hot** storage pools.

**How to read it operationally:**  
1) **Peaks (right tail):** Prioritize hot-data on fast tiers.  
2) **Plateaus:** Maintain alerts and growth tracking.  
3) **Downswings (left tail):** Tier/migrate cold data.  
4) **Mix:** Pair with size to detect oversizing.

**Why this matters:** Proper tiering/right-sizing reduces **capacity cost** and **I/O risk**.
""")

            # Graph 2: Scatter Storage Size vs Utilization (if storage_tb exists)
            if "storage_tb" in df.columns:
                fig_sto_scatter = px.scatter(
                    df, x="storage_tb", y="avg_storage_utilization",
                    title="Storage Size (TB) vs Utilization (%)",
                    trendline="ols",
                    color_discrete_sequence=PX_SEQ
                )
                st.plotly_chart(fig_sto_scatter, use_container_width=True, key="cap_sto_scatter")

                # Analysis for Storage Scatter
                st.write(f"""
**What this graph is:** A scatter plot relating **provisioned storage (TB)** to **utilization (%)**.  
- **X-axis:** Provisioned capacity (TB).  
- **Y-axis:** Storage utilization (%).

**What it shows in your data:** Lower-right points indicate **oversized** volumes; upper-left suggests **upgrade pressure**. The trendline shows how size correlates with utilization.

**Overall:** Visualizes **rightsizing opportunities** and **hotspot risk**.

**How to read it operationally:**  
1) **Peaks:** Move hot data to faster tiers.  
2) **Plateaus:** Track trendline slope for drift.  
3) **Downswings:** Shrink or retier under-used large volumes.  
4) **Mix:** Validate with access frequency before action.

**Why this matters:** Aligning size with use avoids **paying for empty TBs** and prevents **throttling**.
""")

            # Graph 3: Time trend (date-only)
            if "data_timestamp" in df.columns:
                df_ts = df.copy()
                df_ts["data_timestamp"] = pd.to_datetime(df_ts["data_timestamp"], errors="coerce")
                df_ts["day"] = df_ts["data_timestamp"].dt.normalize()
                ts = (
                    df_ts.dropna(subset=["day"])
                    .groupby("day", as_index=False)["avg_storage_utilization"].mean()
                    .sort_values("day")
                )
                if not ts.empty and len(ts) > 1:
                    fig_sto_trend = px.line(
                        ts,
                        x="day",
                        y="avg_storage_utilization",
                        title="Mean Storage Utilization Over Time",
                        color_discrete_sequence=PX_SEQ
                    )
                    fig_sto_trend.update_traces(mode="lines+markers")
                    fig_sto_trend.update_layout(xaxis_title="Date", yaxis_title="Average Storage (%)")
                    st.plotly_chart(fig_sto_trend, use_container_width=True, key="cap_sto_trend")

                    # Analysis for Storage Trend
                    peak_row = ts.loc[ts["avg_storage_utilization"].idxmax()]
                    low_row  = ts.loc[ts["avg_storage_utilization"].idxmin()]
                    ts_mean  = float(ts["avg_storage_utilization"].mean())
                    st.write(f"""
**What this graph is:** A time series of **daily mean storage utilization**.  
- **X-axis:** Calendar date.  
- **Y-axis:** Average storage utilization (%).

**What it shows in your data:** Peak on **{peak_row['day'].date()}** at **{peak_row['avg_storage_utilization']:.2f}%**; lowest on **{low_row['day'].date()}** at **{low_row['avg_storage_utilization']:.2f}%**. Period average = **{ts_mean:.2f}%**.

**Overall:** Sustained rises flag **growth pressure**; dips mark **relief windows**.

**How to read it operationally:**  
1) **Peaks:** Trigger rebalancing/expansion.  
2) **Plateaus:** Maintain alerts (75/85/90%).  
3) **Downswings:** Confirm savings persist (no regressions).  
4) **Mix:** Schedule maintenance during troughs.

**Why this matters:** Anticipating growth prevents **emergency expansions** and **downtime**.
""")

            # Masks and proofs
            low_mask = sto < 30
            high_mask = sto > 80
            n_low = int(low_mask.sum())
            n_high = int(high_mask.sum())

            sto_low_savings = _safe_sum(df.loc[low_mask, "potential_savings_usd"]) if "potential_savings_usd" in df.columns else 0.0
            sto_low_cost    = _safe_sum(df.loc[low_mask, "cost_per_month_usd"])    if "cost_per_month_usd" in df.columns else 0.0
            sto_total_cost  = _safe_sum(df["cost_per_month_usd"])                  if "cost_per_month_usd" in df.columns else 0.0

            sto_peak_evi = f"Peak storage utilization observed at {sto_max:.2f}% with a minimum of {sto_min:.2f}%."
            sto_low_evi  = f"Low-use storage cohort (<30%) includes {n_low} assets; modal band {bin_label} has {bin_count} assets."
            sto_high_evi = f"High-pressure storage cohort (>80%) includes {n_high} assets."
            sto_cost_evi = f"Total recorded monthly cost is {_fmt_cur(sto_total_cost)}."

            sto_cio = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Tier cold data to cheaper storage | **Phase 1 – Detect:** Use utilization and access-frequency metrics to identify volumes below 30 percent utilization that mostly store cold or rarely accessed data. <br><br>**Phase 2 – Migrate:** Move this cold data to lower-cost storage tiers that still meet recovery time and recovery point objectives for those datasets. <br><br>**Phase 3 – Validate:** Monitor latency and access behaviour after migration to confirm that user experience remains acceptable and that the cost savings are real. | - Reduces monthly storage spend by shifting low-activity data off expensive primary or performance tiers onto cheaper archival or capacity tiers.<br><br>- Frees capacity on premium storage tiers so that hot and business-critical datasets can grow without immediate hardware expansion.<br><br>- Makes storage usage patterns easier to explain to stakeholders because cost aligns more closely with how actively data is used.<br><br>- Encourages a culture of lifecycle management where data is deliberately placed on the most appropriate tier instead of growing uncontrolled. | Savings Rate = Σ(potential_savings_usd for Storage<30) / Σ(cost_per_month_usd for Storage<30) = { _fmt_cur(sto_low_savings) } / { _fmt_cur(sto_low_cost) } = **{ _ratio(sto_low_savings, sto_low_cost) }x**. | {sto_low_evi}; histogram left tail confirms cold pools; {sto_cost_evi}. |
| De-duplicate and compress datasets | **Phase 1 – Enable:** Identify storage platforms and datasets where deduplication and compression features are supported but not yet enabled and plan how to introduce them safely. <br><br>**Phase 2 – Measure:** After activation, closely measure logical versus physical space consumption to understand actual savings achieved for each data class. <br><br>**Phase 3 – Retune:** Periodically review deduplication and compression policies so that they remain aligned with workload characteristics and performance needs. | - Increases the effective capacity of existing storage arrays without purchasing additional hardware because more logical data can fit into the same physical space.<br><br>- Defers or avoids capital expenditure on new storage by extracting better utilisation from current investments.<br><br>- Shortens backup and replication windows when less physical data needs to be moved or copied across the network.<br><br>- Provides quantifiable savings that can be tracked and reported to justify continued investment in data efficiency technologies. | Space Reduced (TB) × cost/TB per month; focus on large TB with low utilization in scatter. | Scatter highlights oversized low-utilization volumes that will benefit most from deduplication and compression. |
| Right-size volumes | **Phase 1 – Compare:** For each volume, compare used capacity with provisioned capacity to highlight where a large portion of space is consistently empty. <br><br>**Phase 2 – Shrink:** Work with application owners to safely reduce volume sizes where utilisation is low, while making sure backup and snapshot policies still function correctly. <br><br>**Phase 3 – Alert:** Set up growth thresholds at 75, 85, and 90 percent utilisation so that any future volume growth is visible well before it becomes a risk. | - Avoids paying for large amounts of unused storage capacity that bring no business value.<br><br>- Encourages application teams to request realistic storage allocations instead of defaulting to very large initial sizes.<br><br>- Makes capacity planning more accurate because the reported utilisation levels are closer to actual needs.<br><br>- Reduces the risk of sudden capacity crises by ensuring that growth is tracked and acted on in a structured way. | Over-provisioned TB × cost/TB per month; candidates seen below efficient bands in scatter. | Scatter distribution and low modal band {bin_label} ({bin_count} assets) support pinpointing over-sized volumes. |
| Archive strategy for stale datasets | **Phase 1 – Identify:** Use file age, access logs, and business input to identify datasets that have not been accessed for a long time but are still stored on higher-cost tiers. <br><br>**Phase 2 – Archive:** Move these stale datasets into deep archive or long-term retention storage with defined retrieval SLAs that match business tolerance. <br><br>**Phase 3 – Lifecycle:** Introduce automated retention and deletion policies so that archived data is eventually removed when it is no longer legally or operationally required. | - Lowers storage costs and backup overhead by moving rarely used data to much cheaper, slower storage tiers.<br><br>- Simplifies day-to-day operations on primary storage, as less irrelevant data needs to be scanned or indexed by routine jobs.<br><br>- Supports compliance and data governance by making retention decisions explicit and documented in policies.<br><br>- Reduces the risk of accidental exposure of old and unnecessary data by keeping it in more tightly controlled archive platforms. | Archived TB × (hot tier $/TB − archive $/TB). | Histogram left-most bins indicate cold storage potential by count of low-utilisation volumes. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Hot-data placement on fast tiers | **Phase 1 – Isolate:** Use utilisation, latency, and IOPS metrics to identify volumes that run above 80 percent utilisation and carry critical or frequently accessed data. <br><br>**Phase 2 – Move:** Place those hot datasets on faster storage tiers such as SSD or high-performance arrays that can better handle spikes. <br><br>**Phase 3 – Observe:** Track tail latency and error rates after movement to confirm that performance has improved meaningfully. | - Reduces I/O wait times for critical workloads, leading to faster response times and smoother user experiences.<br><br>- Lowers the number of performance-related incidents caused by overloaded or slow storage volumes.<br><br>- Makes system behaviour more predictable during busy periods because hot data sits on infrastructure built for high throughput.<br><br>- Increases business confidence in the reliability of core transaction paths that depend heavily on storage performance. | Δ I/O latency × IOPS volume on n_high={n_high} hot volumes. | {sto_high_evi}; right-tail histogram points to the highest-risk storage pools. |
| I/O balancing across arrays | **Phase 1 – Detect:** Analyse queue depth, latency, and utilisation metrics to find storage arrays or LUNs that are handling disproportionate amounts of load. <br><br>**Phase 2 – Rebalance:** Redistribute data or workloads across underused arrays or controllers so that I/O demand is spread more evenly. <br><br>**Phase 3 – Validate:** Monitor the rebalanced arrays to ensure queue depths and latency remain within acceptable limits over time. | - Prevents a small number of arrays from becoming chronic bottlenecks that affect many applications.<br><br>- Improves completion times for batch jobs and backup operations by avoiding long queues on a few overloaded devices.<br><br>- Increases the effective lifetime of storage assets because stress is shared rather than concentrated.<br><br>- Helps maintain SLAs for applications that are sensitive to storage response times. | Queue depth reduction × impact per unit on affected LUNs. | Scatter TB vs utilization reveals which volumes are oversized, underused, or overstressed relative to peers. |
| Proactive capacity alerts | **Phase 1 – Thresholds:** Define and configure alerts at key storage utilisation thresholds such as 75, 85, and 90 percent to provide progressive early warnings. <br><br>**Phase 2 – Actions:** Link these alerts to clear actions such as rebalancing, trimming, or capacity expansion so that responses are consistent. <br><br>**Phase 3 – Review:** Regularly review alert outcomes and adjust the thresholds or triggers so that they strike the right balance between noise and risk. | - Reduces the likelihood of sudden storage capacity crises that force emergency expansions or outages.<br><br>- Gives teams enough time to plan and implement rebalancing or expansion activities in a non-disruptive way.<br><br>- Improves overall service reliability since unexpected full-disk events become much less common.<br><br>- Creates a more controlled environment where capacity changes are deliberate and scheduled rather than reactive. | Outage cost avoided × probability reduction, using rise segments in trend. | Trend shows growth episodes that signal when thresholds must trigger early action. |
| Snapshot & replication tuning | **Phase 1 – Audit:** Review snapshot and replication schedules to understand when they run, how long they take, and how they overlay with utilisation peaks. <br><br>**Phase 2 – Tune:** Shift or adjust these schedules so that heavy protection jobs run during lower utilisation periods wherever possible. <br><br>**Phase 3 – Validate:** Confirm that backup and replication objectives are still met and that job durations and interference with live workloads have decreased. | - Reduces contention between protection jobs and live user workloads, especially during peak business hours.<br><br>- Shortens backup and replication windows which frees up capacity for other tasks and reduces risk overrun.<br><br>- Lowers performance incidents where users experience slowness caused by heavy background storage operations.<br><br>- Ensures data protection remains strong while using storage and network resources more intelligently. | Δ Job time × job frequency. | Trend troughs pinpoint safe windows for heavy jobs while peaks around {sto_max:.2f}% indicate periods to avoid. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate storage growth plans | **Phase 1 – Publish:** Prepare simple charts and summaries that show how storage utilisation is growing over time and where capacity is tight. <br><br>**Phase 2 – Plan:** Use these visuals to share expansion plans and highlight the services or business units most affected by growth. <br><br>**Phase 3 – Report:** After expansions or optimisation actions, report back on how utilisation and risk have changed. | - Gives business stakeholders clarity about where storage risks exist and how they are being addressed.<br><br>- Reduces escalations driven by surprise when storage constraints suddenly affect projects or applications.<br><br>- Builds confidence that capacity is being managed proactively instead of reactively.<br><br>- Helps align budget discussions to real utilisation patterns rather than vague concerns about running out of space. | Escalations avoided × handling minutes; align updates to troughs in trend. | Trend establishes a transparent capacity posture that can be shared outside IT. |
| Priority handling for critical datasets | **Phase 1 – Tag:** Identify datasets that support critical customer journeys or regulatory processes and tag them as priority in storage management tools. <br><br>**Phase 2 – Reserve:** Assign these datasets to more resilient, high-performance tiers with stronger protection and recovery objectives. <br><br>**Phase 3 – Watch:** Continuously monitor performance and protection metrics for these priority datasets and act quickly if they deteriorate. | - Ensures the most important customer-facing or regulatory workloads maintain strong storage performance and resilience.<br><br>- Reduces the probability that critical data suffers from slow access or availability problems during periods of stress.<br><br>- Increases trust from business and compliance stakeholders who see that their data is handled with extra care.<br><br>- Provides a clear framework for differentiating storage service levels by business criticality. | Δ High-percentile latency × critical I/O volume. | {sto_high_evi} marks pressure zones that have the biggest impact on key users and datasets. |
| Scheduled maintenance during low I/O | **Phase 1 – Window:** Use utilisation trends and daily patterns to identify times of lower I/O activity as preferred windows for storage maintenance. <br><br>**Phase 2 – Notify:** Inform users and application teams about planned work in these windows, explaining expected impact and timing. <br><br>**Phase 3 – Verify:** Compare incident and performance data during maintenance windows with normal days to confirm that disruption is minimal. | - Lowers the risk that storage maintenance will be blamed for performance issues during busy periods because it runs at quieter times.<br><br>- Reduces user complaints since fewer people experience slowdowns or brief outages when changes are applied.<br><br>- Makes maintenance activities more predictable and easier to coordinate across teams.<br><br>- Provides evidence that careful scheduling is helping to protect user experience while still allowing necessary changes. | Δ Incidents during maintenance windows vs baseline. | Trend troughs (lowest day {low_row['day'].date() if 'low_row' in locals() else '—'}) guide when storage work should be scheduled. |
| Data ownership & cleanup drives | **Phase 1 – Assign:** Assign clear data owners to datasets and volumes with low utilisation so that someone is accountable for deciding what should be kept or removed. <br><br>**Phase 2 – Cleanup:** Run structured cleanup campaigns where owners remove obsolete, duplicate, or non-business-critical data guided by easy reporting. <br><br>**Phase 3 – Sustain:** Track cleanup progress with simple KPIs and repeat the exercise regularly so that clutter does not accumulate again. | - Frees up storage capacity by eliminating data that no longer has value to the organisation.<br><br>- Makes it easier for users to find relevant information because there is less noise and duplication in storage systems.<br><br>- Reduces backup and replication times since fewer unnecessary files need to be processed.<br><br>- Supports better compliance and data governance by ensuring only necessary and justified data remains in primary storage. | GB removed × $/GB-month saved. | Histogram left tail quantifies cold and potentially unused data cohorts that are prime candidates for cleanup. |
"""
            }
            render_cio_tables("Storage Utilization — CIO Recommendations", sto_cio)

        else:
            st.info("Column 'avg_storage_utilization' not found in dataset.")

    # =======================
    # 4) Network Utilization
    # =======================
    with st.expander("📌 Network Utilization and Throughput"):
        if "avg_network_utilization" in df.columns:
            net = pd.to_numeric(df["avg_network_utilization"], errors="coerce")

            # Graph 1: Histogram
            fig_net_hist = px.histogram(
                df,
                x="avg_network_utilization",
                nbins=20,
                title="Network Utilization Distribution (%)",
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig_net_hist, use_container_width=True, key="cap_net_hist")

            # Analysis for Network Histogram
            net_mean = _safe_mean(net)
            net_min = _safe_min(net)
            net_max = _safe_max(net)
            n_assets = int(df["asset_id"].nunique()) if "asset_id" in df.columns else len(df)
            bin_label, bin_count = _modal_bin(net, bins=20)
            st.write(f"""
**What this graph is:** A histogram showing **network utilization distribution**.  
- **X-axis:** Network utilization bands (%).  
- **Y-axis:** Asset count per band.

**What it shows in your data:** Average network utilization = **{net_mean:.2f}%** (range **{net_min:.2f}%–{net_max:.2f}%**) across **{n_assets}** assets. **Modal band** = **{bin_label}** with **{bin_count}** assets.

**Overall:** Reveals whether links are **under-used** or **near saturation**.

**How to read it operationally:**  
1) **Peaks (right tail):** QoS and aggregation for hot links.  
2) **Plateaus:** Keep thresholds and monitoring tuned.  
3) **Downswings (left tail):** Down-tier circuits / remove redundant links.  
4) **Mix:** Cross-check with bandwidth to spot oversizing.

**Why this matters:** Properly sized links cut **carrier spend** and **prevent congestion**.
""")

            # Graph 2: Scatter Bandwidth vs Utilization (if bandwidth exists)
            if "network_bandwidth_gbps" in df.columns:
                fig_net_scatter = px.scatter(
                    df,
                    x="network_bandwidth_gbps",
                    y="avg_network_utilization",
                    title="Provisioned Bandwidth (Gbps) vs Utilization (%)",
                    trendline="ols",
                    color_discrete_sequence=PX_SEQ
                )
                st.plotly_chart(fig_net_scatter, use_container_width=True, key="cap_net_scatter")

                # Analysis for Network Scatter
                st.write(f"""
**What this graph is:** A scatter plot comparing **provisioned bandwidth (Gbps)** to **observed utilization (%)**.  
- **X-axis:** Provisioned bandwidth (Gbps).  
- **Y-axis:** Network utilization (%).

**What it shows in your data:** High bandwidth with low utilization implies **oversizing**; high utilization at low bandwidth suggests **upgrade pressure**. The trendline provides a directional signal.

**Overall:** Surfaces **rightsizing** opportunities and **hotspot risks**.

**How to read it operationally:**  
1) **Peaks:** Aggregate or upgrade constrained links.  
2) **Plateaus:** Keep shaping and QoS aligned.  
3) **Downswings:** Down-tier cost-heavy idle circuits.  
4) **Mix:** Validate redundancy policy before removal.

**Why this matters:** Aligning capacity to demand preserves **performance** and lowers **recurring fees**.
""")

            # Graph 3: Time trend (date-only)
            if "data_timestamp" in df.columns:
                df_ts = df.copy()
                df_ts["data_timestamp"] = pd.to_datetime(df_ts["data_timestamp"], errors="coerce")
                df_ts["day"] = df_ts["data_timestamp"].dt.normalize()
                ts = (
                    df_ts.dropna(subset=["day"])
                    .groupby("day", as_index=False)["avg_network_utilization"].mean()
                    .sort_values("day")
                )
                if not ts.empty and len(ts) > 1:
                    fig_net_trend = px.line(
                        ts,
                        x="day",
                        y="avg_network_utilization",
                        title="Mean Network Utilization Over Time",
                        color_discrete_sequence=PX_SEQ
                    )
                    fig_net_trend.update_traces(mode="lines+markers")
                    fig_net_trend.update_layout(xaxis_title="Date", yaxis_title="Average Network (%)")
                    st.plotly_chart(fig_net_trend, use_container_width=True, key="cap_net_trend")

                    # Analysis for Network Trend
                    peak_row = ts.loc[ts["avg_network_utilization"].idxmax()]
                    low_row  = ts.loc[ts["avg_network_utilization"].idxmin()]
                    ts_mean  = float(ts["avg_network_utilization"].mean())
                    st.write(f"""
**What this graph is:** A time series of **daily mean network utilization**.  
- **X-axis:** Calendar date.  
- **Y-axis:** Average network utilization (%).

**What it shows in your data:** Highest on **{peak_row['day'].date()}** at **{peak_row['avg_network_utilization']:.2f}%**; lowest on **{low_row['day'].date()}** at **{low_row['avg_network_utilization']:.2f}%**. Period average = **{ts_mean:.2f}%**.

**Overall:** Rising segments imply **demand growth**; flat/falling show **stability**.

**How to read it operationally:**  
1) **Peaks:** Aggregate/upgrade and prioritize hot paths.  
2) **Plateaus:** Maintain thresholds (75/85/90%).  
3) **Downswings:** Validate what actions reduced load.  
4) **Mix:** Use troughs for planned change windows.

**Why this matters:** Anticipating congestion prevents **packet loss** and **user-visible slowdowns**.
""")

            # Masks and proofs
            low_mask = net < 30
            high_mask = net > 80
            n_low = int(low_mask.sum())
            n_high = int(high_mask.sum())

            net_low_savings = _safe_sum(df.loc[low_mask, "potential_savings_usd"]) if "potential_savings_usd" in df.columns else 0.0
            net_low_cost    = _safe_sum(df.loc[low_mask, "cost_per_month_usd"])    if "cost_per_month_usd" in df.columns else 0.0
            net_total_cost  = _safe_sum(df["cost_per_month_usd"])                  if "cost_per_month_usd" in df.columns else 0.0

            net_peak_evi = f"Peak network utilization observed at {net_max:.2f}% with a minimum of {net_min:.2f}%."
            net_low_evi  = f"Underutilized interfaces (<30%) include {n_low} assets; modal band {bin_label} has {bin_count} assets."
            net_high_evi = f"High-pressure interfaces (>80%) include {n_high} assets."
            net_cost_evi = f"Total recorded monthly cost is {_fmt_cur(net_total_cost)}."

            net_cio = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Down-tier links with sustained <30 percent utilization | **Phase 1 – Identify:** Use utilisation reports to find network links that remain below 30 percent utilisation over a sustained period rather than only at a single point in time. <br><br>**Phase 2 – Down-tier or aggregate:** For these low-use links, either reduce the contracted bandwidth or aggregate multiple circuits into a fewer number of appropriately sized links. <br><br>**Phase 3 – Monitor:** After changes, monitor performance to confirm that service levels and failover behaviour are still acceptable. | - Reduces monthly carrier costs by cutting back on bandwidth that is not actually needed to support real traffic volumes.<br><br>- Simplifies the link portfolio so that network diagrams and operational procedures are easier to maintain and understand.<br><br>- Ensures capacity still matches business needs because changes are targeted at links with consistently low usage rather than temporary dips.<br><br>- Frees up budget that can be used to strengthen capacity or redundancy where utilisation and business criticality are genuinely higher. | Savings Rate = Σ(potential_savings_usd for Net<30) / Σ(cost_per_month_usd for Net<30) = { _fmt_cur(net_low_savings) } / { _fmt_cur(net_low_cost) } = **{ _ratio(net_low_savings, net_low_cost) }x**. | {net_low_evi}; histogram left tail shows low-use links; {net_cost_evi}. |
| Eliminate idle or redundant links | **Phase 1 – Validate:** Review redundancy designs and failover requirements to determine whether all existing links are truly required for resilience or capacity. <br><br>**Phase 2 – Remove:** Safely decommission or cancel circuits that do not contribute meaningfully to resilience or load handling, following change control processes. <br><br>**Phase 3 – Audit:** Perform regular audits to ensure that redundant or unused links do not creep back into the environment over time. | - Decreases recurring network spend by removing circuits that no longer provide value or that duplicate capability excessively.<br><br>- Simplifies network topology which reduces the cognitive load on engineers handling incidents or performing changes.<br><br>- Lowers operational risk because there are fewer poorly understood links that may behave unpredictably during failover scenarios.<br><br>- Encourages disciplined redundancy design where every remaining link has a clear purpose and justification. | Links removed × fee per month; scope informed by n_low={n_low} low-use candidates. | Many assets occupying the low modal band ({bin_label}, {bin_count} assets) indicate potential over-provisioned redundancy. |
| Right-size peering and transit | **Phase 1 – Profile:** Analyse traffic volumes and patterns across peering and transit links to understand typical and peak loads over time. <br><br>**Phase 2 – Adjust:** Tune contracted bandwidths, peering agreements, or traffic engineering so that capacity aligns with observed peak loads and business forecasts. <br><br>**Phase 3 – Reassess:** Revisit these profiles regularly to ensure capacity remains aligned as traffic mixes and business demands change. | - Aligns network spend with actual usage so that high-cost capacity is not reserved without real demand behind it.<br><br>- Reduces the risk of congestion on key routes by ensuring that truly high-demand paths have enough capacity to handle peaks.<br><br>- Makes budgeting discussions easier because capacity decisions are backed by concrete traffic data.<br><br>- Provides a mechanism to adapt quickly to shifts in user behaviour or new services that change traffic patterns. | Δ Gbps × cost/Gbps-month; candidates seen where high bandwidth meets low utilization in scatter. | Scatter shows oversized links at low utilization levels that can be right-sized safely. |
| Contract renegotiation using utilization evidence | **Phase 1 – Prepare:** Build a fact-based dossier that summarises utilisation, peaks, and low-band cohorts across network links to take into contract conversations. <br><br>**Phase 2 – Negotiate:** Use this evidence to negotiate bandwidth tiers, pricing structures, and flexibility clauses that better match actual usage. <br><br>**Phase 3 – Enforce:** Integrate utilisation monitoring into vendor reviews so that contracts remain aligned with observed behaviour over time. | - Improves unit pricing for connectivity by showing carriers clear data about how links are actually used.<br><br>- Can unlock more flexible contract structures that adjust to changing utilisation instead of locking in over-commitment for long periods.<br><br>- Strengthens the organisation’s negotiation position because decisions are grounded in objective data rather than assumptions.<br><br>- Helps prevent future over-commitment by making utilisation an explicit part of ongoing vendor governance. | Δ Unit price × committed capacity; evidence derived from avg {net_mean:.2f}% and cohort sizes (n_low={n_low}). | Distribution and trend quantify the true demand profile behind existing network contracts. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Hot-path prioritization | **Phase 1 – Identify:** Map out latency-sensitive and business-critical traffic flows so that the most important network paths are clearly known. <br><br>**Phase 2 – QoS:** Apply quality of service policies to prioritise these flows when links approach high utilisation levels, especially near {net_max:.2f} percent. <br><br>**Phase 3 – Validate:** Measure changes in tail latency and error rates for these paths after QoS is implemented to ensure it delivers the expected improvements. | - Keeps key user journeys responsive during busy periods without immediately increasing capacity everywhere.<br><br>- Reduces the number of incidents where customers complain about slow response times even though overall capacity is technically sufficient.<br><br>- Enables more efficient use of network resources because not all traffic is treated equally when the network is stressed.<br><br>- Supports better alignment between technical network behaviour and business priorities. | Δ p95 latency × requests on peak days; peaks observed at {net_max:.2f}%. | Right-tail histogram and trend peaks indicate where prioritisation of hot paths yields the most benefit. |
| Link aggregation for hotspots | **Phase 1 – Aggregate:** For links consistently above 80 percent utilisation, design and implement link aggregation or higher-capacity alternatives to increase headroom. <br><br>**Phase 2 – Rebalance:** Once aggregated, rebalance traffic so that it is spread evenly across the combined capacity rather than overloading a single link. <br><br>**Phase 3 – Verify:** Monitor utilisation, latency, and loss after aggregation to confirm that hotspots have been removed. | - Reduces congestion and packet loss on the most heavily used parts of the network.<br><br>- Improves performance for applications that depend on these paths by providing more consistent bandwidth and reduced queuing.<br><br>- Decreases incident frequency and severity related to network saturation on key links.<br><br>- Makes the network more resilient to bursts in traffic that would previously have overloaded single circuits. | n_high={n_high} links × (Δ loss/latency benefit). | {net_high_evi} defines the set of saturation candidates where aggregation will have clear impact. |
| Proactive capacity thresholds | **Phase 1 – Alerts:** Configure graduated utilisation thresholds, such as 75, 85, and 90 percent, which trigger progressively stronger alerts and actions. <br><br>**Phase 2 – Actions:** For each threshold, define actions such as rerouting, rate limiting, or capacity upgrades so that responses are coordinated. <br><br>**Phase 3 – Review:** Periodically review whether thresholds and action plans are effective in preventing congestion-related incidents and adjust them as needed. | - Prevents unexpected link saturation by signalling problems well before utilisation becomes critical.<br><br>- Gives operations teams enough lead time to act, reducing the need for emergency changes under pressure.<br><br>- Makes incident patterns more predictable because recurring congestion can be tackled methodically rather than reactively.<br><br>- Provides a structure for continuous improvement in how the network responds to growth in traffic. | Outage cost avoided × probability reduction based on rising segments. | Trend provides early warning by contrasting low-day {net_min:.2f}% and high-day {net_max:.2f}% utilisation levels. |
| CDN/offload for bursty traffic | **Phase 1 – Identify:** Analyse traffic profiles to pinpoint endpoints and services that generate sudden spikes in external or content-heavy traffic. <br><br>**Phase 2 – Offload:** Route these flows through a content delivery network or additional edge caching so that less traffic hits core network links. <br><br>**Phase 3 – Measure:** Monitor reductions in origin bandwidth and improvements in response times to confirm the offload effect. | - Reduces pressure on backbone and data centre links during marketing campaigns or other high-traffic events.<br><br>- Improves user experience by serving content from locations that are physically closer to end users.<br><br>- Makes high-traffic periods more predictable and easier to handle without overbuilding core capacity.<br><br>- Lowers risk of congestion-related incidents in the core network by shifting load to external infrastructure designed for bursts. | Δ Origin bandwidth × cost/Gbps. | Peak periods from trend isolate when offloading delivers the highest return. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate network capacity posture | **Phase 1 – Dashboards:** Build simple, non-technical dashboards that show network utilisation, risk levels, and improvement actions in a format that business users can understand. <br><br>**Phase 2 – Actions:** For each highlighted risk, specify who owns the remediation and roughly when they plan to complete it. <br><br>**Phase 3 – Outcomes:** Share updates on these dashboards at regular intervals so that stakeholders can see progress. | - Reduces the number of vague “is the network slow?” escalations because people can see current conditions and remediation plans.<br><br>- Builds trust that network capacity is being actively monitored and managed rather than left unchecked.<br><br>- Helps non-technical stakeholders understand why certain investments or changes are being prioritised.<br><br>- Provides a consistent story about network health that can be reused in management updates and service reviews. | Repeat-contact deflection × minutes/contact; align to troughs. | Distribution and trend together convey network posture clearly to non-technical stakeholders. |
| Safeguard critical customer paths | **Phase 1 – Whitelist:** Identify applications and customer segments that are considered critical and map their traffic across the network. <br><br>**Phase 2 – Reserve:** Reserve capacity or apply QoS and routing rules to ensure that these critical paths receive priority when the network is busy. <br><br>**Phase 3 – Observe:** Monitor response times and failure rates for these paths and trigger rollback or additional protection when metrics deteriorate. | - Keeps the most important customer journeys stable and responsive even when other parts of the network are under stress.<br><br>- Reduces churn and negative sentiment among key customers who are most sensitive to performance problems.<br><br>- Helps prioritise troubleshooting during incidents because critical paths are clearly defined and protected.<br><br>- Demonstrates to business leaders that the network design reflects commercial priorities, not just technical decisions. | Δ latency on critical paths × volume. | {net_high_evi} maps to where users feel pain first and where safeguards are most needed. |
| Planned change communication | **Phase 1 – Window:** Use utilisation trends to choose low-traffic days and times as preferred slots for network changes and maintenance. <br><br>**Phase 2 – Inform:** Communicate clearly to users about what will happen in those windows, how long it will last, and what they might experience. <br><br>**Phase 3 – Verify:** After the window, check incidents and sentiment to ensure the approach minimized user impact and adjust future windows if needed. | - Reduces disruption to users by aligning changes with times when fewer people are relying on the network.<br><br>- Lowers complaint volumes because expectations are set in advance and changes are not perceived as unexpected outages.<br><br>- Helps different teams coordinate their own activities around network maintenance windows.<br><br>- Provides continuous feedback for improving change management practices over time. | Δ incidents during maintenance vs baseline. | Trend troughs show windows for safer change, and modal band {bin_label} supports choosing low-usage times. |
| Real-time status page | **Phase 1 – Expose:** Create a user-facing status page that shows current network incidents and high-level utilisation indicators in simple terms. <br><br>**Phase 2 – Automate:** Integrate the status page with monitoring so that it updates automatically when thresholds are crossed or incidents are opened. <br><br>**Phase 3 – Iterate:** Collect feedback and refine the level of detail and messaging style based on user understanding and behaviour. | - Reduces the volume of tickets opened just to ask whether there is a known network problem because the answer is publicly visible.<br><br>- Builds credibility by showing that the organisation is transparent about network issues and their impact.<br><br>- Helps users plan work around known incidents instead of repeatedly retrying actions that will fail.<br><br>- Shortens communication loops during incidents as many updates can be delivered through the status page instead of one-to-one conversations. | Contact deflection × minutes per ticket. | Peaks at {net_max:.2f}% justify proactive transparency about current network stress and incident state. |
"""
            }
            render_cio_tables("Network Utilization — CIO Recommendations", net_cio)

        else:
            st.info("Column 'avg_network_utilization' not found in dataset.")
