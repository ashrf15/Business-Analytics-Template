# utils_capacity_scalability/recommendation_performance/capacity_scalability.py

import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# ============================================================
# Mesiniaga palette (blue/white)
# ============================================================
MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#9BD1FF"]

# ============================================================
# Helpers
# ============================================================
def render_cio_tables(title, cio):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio.get("cost", ""), unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio.get("performance", ""), unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio.get("satisfaction", ""), unsafe_allow_html=True)

def _to_dt(s):
    return pd.to_datetime(s, errors="coerce")

def _fmt_date(d):
    try:
        return pd.to_datetime(d).strftime("%d/%m/%Y")
    except Exception:
        return str(d)

def _safe_mean(series, nd=2):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty: return None
    return round(float(s.mean()), nd)

def _safe_std(series, nd=2):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty: return None
    return round(float(s.std(ddof=0)), nd)

def _pchange(first, last, nd=1):
    try:
        if first is None or pd.isna(first) or first == 0:
            return None
        return round((last - first) / abs(first) * 100.0, nd)
    except Exception:
        return None

def _series_peak_low(daily_df, date_col, val_col):
    if daily_df.empty or daily_df[val_col].dropna().empty:
        return None
    peak = daily_df.loc[daily_df[val_col].idxmax()]
    low  = daily_df.loc[daily_df[val_col].idxmin()]
    return {
        "peak_val": float(peak[val_col]),
        "peak_date": _fmt_date(peak[date_col]),
        "low_val": float(low[val_col]),
        "low_date": _fmt_date(low[date_col]),
    }

def _quartile_gap(series, direction="up"):
    """
    direction='up'  -> Q3 - Mean  (uplift potential; for metrics where higher is 'pressure')
    direction='down'-> Mean - Q1  (reduction potential; minutes/latency/etc.)
    """
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty: return 0.0
    mean = s.mean()
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    return max(0.0, (q3 - mean) if direction == "up" else (mean - q1))


# ============================================================
# MAIN: Target 8 – Capacity & Scalability
# ============================================================
def capacity_scalability(df_filtered: pd.DataFrame):

    # Guard & parse date
    df = df_filtered.copy()
    if "report_date" not in df.columns:
        st.warning("⚠️ Column 'report_date' is required for time-based capacity visuals.")
        df["report_date"] = pd.NaT
    else:
        df["report_date"] = _to_dt(df["report_date"])

    # =======================================================
    # 8.1 Capacity Assessment for Critical Services (Q3 ranks)
    # =======================================================
    with st.expander("📌 Capacity Assessment for Critical Services"):
        need = {"report_date","service_name","service_category",
                "cpu_utilization","memory_utilization","disk_utilization","network_utilization"}
        if need.issubset(df.columns):
            util = df.dropna(subset=["service_name"]).copy()

            # Compute per-service 75th percentile (Q3) per metric → average as pressure score
            grp = (util.groupby(["service_name","service_category"])
                        [["cpu_utilization","memory_utilization","disk_utilization","network_utilization"]]
                        .quantile(0.75)
                        .reset_index())
            if grp.empty:
                st.info("No utilization data available to compute Q3 utilization per service.")
            else:
                grp["q3_avg_util"] = grp[["cpu_utilization","memory_utilization","disk_utilization","network_utilization"]].mean(axis=1)
                # Rank top 12 as "critical capacity candidates" (data-derived; no external assumption)
                top = grp.sort_values("q3_avg_util", ascending=False).head(12)

                fig = px.bar(
                    top,
                    x="service_name",
                    y="q3_avg_util",
                    color="service_category",
                    title="Critical Capacity Candidates — Top Services by Q3 Average Utilization",
                    labels={"service_name":"Service","q3_avg_util":"Q3 Avg Utilization (%)"},
                    color_discrete_sequence=MES_BLUE,
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)

                # Dynamic analysis (strict template)
                mean_q3 = _safe_mean(grp["q3_avg_util"])
                std_q3  = _safe_std(grp["q3_avg_util"])
                peak_svc = top.iloc[0] if not top.empty else None
                low_svc  = top.iloc[-1] if len(top) > 0 else None
                fleet_median_q3 = grp["q3_avg_util"].median() if not grp.empty else None

                st.markdown("### Analysis")
                if peak_svc is not None and fleet_median_q3 is not None:
                    st.write(f"""
**What this graph is:** A ranked **bar chart** of services by **Q3 (75th percentile) average utilization** across CPU, Memory, Disk, and Network.  
**X-axis:** Service names.  
**Y-axis:** Q3 average utilization (%), higher means more sustained pressure.

**What it shows in your data:**  
- **Highest bar (top service):** **{peak_svc['service_name']}** at **{peak_svc['q3_avg_util']:.1f}%**.  
- **Lowest within top set:** **{low_svc['service_name']}** at **{low_svc['q3_avg_util']:.1f}%**.  
- **Fleet statistics:** Mean **{mean_q3:.1f}%**, Std Dev **{std_q3:.1f}**, Median **{fleet_median_q3:.1f}%**.  

**Overall:** Services with Q3 averages far above **{fleet_median_q3:.1f}%** experience **sustained high load** and are prime targets for right-sizing, caching, or architectural changes.

**How to read it operationally:**  
- **Gap = pressure delta:** The vertical distance above the fleet median is **capacity pressure** to relieve first.  
- **Lead–lag vs incidents:** Overlay with incident spikes; top services often correlate with performance complaints.  
- **Recovery strength:** Post-change, these bars should move closer to the fleet median, indicating headroom recovery.

**Why this matters:** Prioritizing the **upper decile** delivers **maximum headroom per unit effort**, preventing slowdowns and avoiding expensive over-provisioning.
""")
                    # Evidence & CIO (dataset-only)
                    pressure_pp = (top["q3_avg_util"] - fleet_median_q3).clip(lower=0).sum()
                    calc_text = f"Pressure above fleet median (top set) = Σ(max(Q3_avg − Median_Q3, 0)) = **{int(pressure_pp)}** %-points"
                    evidence = (f"Top service **{peak_svc['service_name']}** at **{peak_svc['q3_avg_util']:.1f}%** "
                                f"vs fleet median Q3 **{fleet_median_q3:.1f}%**; top-set spread indicates persistent pressure.")

                    # ---------- CIO TABLES (Expanded explanation + benefits) ----------
                    cio_8_1 = {
                        "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Right-size top-pressure services** | **Phase 1:** Rank services by Q3 average utilization and select the highest pressure cohort so effort focuses where load is persistent. <br><br> **Phase 2:** Move these services to more cost-efficient instance, storage and network tiers while documenting new limits and rollback options so risk is controlled. <br><br> **Phase 3:** Verify the reduction in Q3 average and compare old versus new run costs so savings and performance are proven. | - Reduces spend in the exact hotspots where premium capacity is being consumed continuously and wastefully. <br><br> - Lowers idle buffer requirements because services run closer to right-sized limits without chronic contention. <br><br> - Improves cost to performance alignment so money is spent only where users feel the benefit. <br><br> - Increases budgeting accuracy because capacity is engineered to measured demand. | {calc_text} | {evidence} |
| **Consolidate bursty workloads** | **Phase 1:** Identify services that show high Q3 but moderate median and confirm that traffic is bursty rather than sustained. <br><br> **Phase 2:** Co schedule or co locate compatible bursts to share headroom and apply queueing where separation is safer so peaks flatten. <br><br> **Phase 3:** Monitor the shrinkage between Q3 and median after consolidation so the policy is objectively validated. | - Decreases scale up events that are triggered only by short lived spikes which directly reduces peak premiums. <br><br> - Shrinks the infrastructure footprint because shared headroom covers multiple services efficiently. <br><br> - Smooths monthly bills because burst costs are contained and predictable. <br><br> - Improves engineering focus because fewer surprise peaks demand urgent tuning. | Peak spread reduction = pre–post Σ(Q3 − Median). | Bars well above median Q3 signal burst-prone services. |
| **Storage/IO tier normalization** | **Phase 1:** Map IO intensive paths and match each to an appropriate storage and throughput tier based on measured Q3 needs. <br><br> **Phase 2:** Upgrade hot paths and downgrade cold paths while keeping change scope narrow so risk is limited to the right components. <br><br> **Phase 3:** Re benchmark latency and throughput to ensure performance targets are met at lower cost. | - Stops paying premium IO prices across entire services when only a few paths are truly hot. <br><br> - Keeps critical transactions fast by focusing upgrades where contention hurts users most. <br><br> - Reduces operational complexity because tiers are consistent with actual load profiles. <br><br> - Improves auditability because the rationale for each tier is tied to data. | %-points trimmed from Q3 on targeted paths × unit cost. | Top bars suggest hot IO contention worth isolating. |
""",
                        "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Targeted caching/indexing** | **Phase 1:** Trace hot read patterns and identify cache misses and slow queries so the biggest wins are obvious. <br><br> **Phase 2:** Add caches or indexes to the specific routes and tables that dominate load while setting TTL and eviction rules. <br><br> **Phase 3:** Measure the reduction in Q3 utilization and response time to confirm that pressure has been removed. | - Lowers peak contention on shared resources which protects p95 latency during busy hours. <br><br> - Increases stability under load because repeated hot paths become cheaper to serve. <br><br> - Improves developer velocity because fewer incidents interrupt work during peaks. <br><br> - Extends the life of current hardware because efficiency increases. | Δ(Q3_avg_util) on treated services vs baseline. | Highest bars indicate sustained contention suitable for caching gains. |
| **Split read/write or queue burst load** | **Phase 1:** Detect services with mixed read write traffic or sudden bursts and document the contention points. <br><br> **Phase 2:** Separate read and write pipelines or buffer work via durable queues so components scale independently. <br><br> **Phase 3:** Tune back pressure and retry policies so the system sheds load gracefully under stress. | - Removes shared bottlenecks that throttle throughput when different workloads collide. <br><br> - Raises the overall throughput ceiling so more transactions complete within SLO during peaks. <br><br> - Reduces incident volume related to timeouts because pressure is decoupled. <br><br> - Improves observability because each lane exposes its own limits. | TPS uplift at comparable utilization; backlog tail shortened. | High Q3 implies shared bottlenecks benefiting from decoupling. |
| **Autoscaling guardrails** | **Phase 1:** Define autoscale policies that react to rolling Q3 utilization rather than raw spikes so scaling is meaningful. <br><br> **Phase 2:** Add cooldowns and minimum step sizes that prevent oscillations and cost whiplash during noisy periods. <br><br> **Phase 3:** Audit scale events weekly to refine thresholds and verify that performance targets stay green. | - Keeps p95 latency stable during demand bursts because capacity arrives on time and in the right amount. <br><br> - Avoids thrashing that wastes money and destabilises caches because scale decisions are damped. <br><br> - Improves incident response because scaling is predictable and observable. <br><br> - Increases service resilience because headroom automatically returns after spikes. | Pressure hours above rolling Q3 reduced (pre–post). | Top-set services are prime for policy-based scaling. |
""",
                        "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Prioritize UX-facing top services** | **Phase 1:** Tag which of the top ranked services are directly user facing and confirm business critical journeys. <br><br> **Phase 2:** Apply the quickest technical wins such as caching or tier changes to these services first to shorten time to value. <br><br> **Phase 3:** Track CSAT and NPS for the affected journeys so improvements are visible to stakeholders. | - Reduces user perceived slowness during busy periods which protects conversion and satisfaction. <br><br> - Decreases complaint volume because the most visible pain points improve first. <br><br> - Builds stakeholder confidence because performance fixes land where customers notice. <br><br> - Strengthens the case for further investment because metrics show real impact. | CSAT/NPS delta on treated vs untreated cohorts. | Peak Q3 bars typically map to perceived slowness. |
| **Capacity posture snapshots** | **Phase 1:** Publish a monthly snapshot that shows which services sit above the fleet median and what actions were taken. <br><br> **Phase 2:** Record the before and after metrics so progress is transparent and repeatable. <br><br> **Phase 3:** Keep a running log to align expectations with leaders and audit teams. | - Lowers escalation frequency because stakeholders can see the plan and its outcomes. <br><br> - Improves cross team alignment because priorities are justified by data. <br><br> - Increases trust in the roadmap because progress is documented consistently. <br><br> - Enhances accountability because owners and due dates are visible. | Queries avoided after snapshot cadence starts. | Clear ranking + actions reassure stakeholders. |
| **Business-hour headroom alerts** | **Phase 1:** Generate alerts when rolling Q3 utilization crosses thresholds during business hours and route them to service owners. <br><br> **Phase 2:** Include runbook links and suggested mitigations so action starts immediately. <br><br> **Phase 3:** Review alert quality weekly to reduce noise and refine thresholds. | - Prevents user visible degradation by catching pressure early when customers are active. <br><br> - Speeds triage because alerts contain actionable steps and context. <br><br> - Reduces duplicate tickets because teams act before customers report issues. <br><br> - Improves operational calm because alerts are precise and credible. | Complaints avoided during threshold breaches. | Top bars near business peaks warrant alerts. |
"""
                    }
                    render_cio_tables("Capacity Assessment — CIO Table", cio_8_1)
        else:
            miss = need - set(df.columns)
            st.warning(f"Missing columns for this subtarget: {', '.join(sorted(miss))}.")

    # =======================================================
    # 8.2 Resource Utilization (CPU, Memory, Disk, Network)
    # =======================================================
    with st.expander("📌 Resource Utilization (Fleet Trend)"):
        need = {"report_date","cpu_utilization","memory_utilization","disk_utilization","network_utilization"}
        if need.issubset(df.columns) and df["report_date"].notna().any():
            util = df.dropna(subset=["report_date"]).copy()
            # Daily fleet average per metric
            daily = (util.groupby(util["report_date"].dt.date)[
                        ["cpu_utilization","memory_utilization","disk_utilization","network_utilization"]
                     ].mean()
                     .reset_index()
                     .rename(columns={"report_date":"date"}))

            daily_long = daily.melt(id_vars=["date"], var_name="metric", value_name="util_pct")
            fig = px.line(
                daily_long, x="date", y="util_pct", color="metric",
                title="Fleet Average Utilization Over Time (CPU / Memory / Disk / Network)",
                labels={"date":"Date", "util_pct":"Utilization (%)", "metric":"Metric"},
                color_discrete_sequence=MES_BLUE,
                template="plotly_white",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)

            # Dynamic analysis — strict template
            st.markdown("### Analysis")
            analysis_lines = []
            evidence_bits = []
            for metric in ["cpu_utilization","memory_utilization","disk_utilization","network_utilization"]:
                mdf = daily[["date", metric]].dropna()
                if not mdf.empty:
                    stats = _series_peak_low(mdf, "date", metric)
                    mean_val = _safe_mean(mdf[metric])
                    std_val  = _safe_std(mdf[metric])
                    start_val = mdf[metric].iloc[0] if not mdf.empty else None
                    end_val   = mdf[metric].iloc[-1] if not mdf.empty else None
                    change_pct = _pchange(start_val, end_val)
                    analysis_lines.append(
                        f"- **{metric.replace('_',' ').title()}** — Peak **{stats['peak_val']:.1f}%** on **{stats['peak_date']}**, "
                        f"Low **{stats['low_val']:.1f}%** on **{stats['low_date']}**, Mean **{mean_val:.1f}%**, "
                        f"Std **{std_val:.1f}**, Start→End change {f'{change_pct:.1f}%' if change_pct is not None else 'n/a'}."
                    )
                    evidence_bits.append(
                        f"{metric.split('_')[0].upper()}: {stats['peak_val']:.1f}%@{stats['peak_date']} vs "
                        f"{stats['low_val']:.1f}%@{stats['low_date']} (mean {mean_val:.1f}%)."
                    )

            if analysis_lines:
                st.write(f"""
**What this graph is:** A **multi-line time series** showing **daily fleet-average utilization** for CPU, Memory, Disk, and Network.  
**X-axis:** Calendar date.  
**Y-axis:** Utilization (%) for each metric.

**What it shows in your data:**  
{chr(10).join(analysis_lines)}

**Overall:** Rising lines indicate pressure building; flat/declining lines imply regained headroom.

**How to read it operationally:**  
- **Gap = backlog/pressure delta:** Taller segments above the mean mark **hot periods** needing scale or tuning.  
- **Lead–lag:** If Memory/IO peak after CPU, you have **cascading contention**; address upstream.  
- **Recovery strength:** Faster return to the mean after peaks = **healthier capacity posture**.

**Why this matters:** Keeping resource utilization in a **controlled band** prevents latency spikes and unexpected cost from emergency scaling.
""")
            else:
                st.info("Not enough valid utilization data to compute analysis.")

            # CIO (dataset-only formulas) — EXPANDED EXPLANATIONS & BENEFITS
            cost_rows = []
            perf_rows = []
            sat_rows  = []
            for metric in ["cpu_utilization","memory_utilization","disk_utilization","network_utilization"]:
                if metric not in df.columns: continue
                s = pd.to_numeric(df[metric], errors="coerce").dropna()
                if s.empty: continue
                median = s.median()
                excess = (s - median).clip(lower=0).sum()   # %-points above median across records
                idle   = (median - s).clip(lower=0).sum()   # %-points below median across records
                calc_text = f"{metric.replace('_',' ').title()} — Excess above median = **{int(excess)}** pp; Idle below median = **{int(idle)}** pp"
                ev = [e for e in evidence_bits if e.startswith(metric.split('_')[0].upper()+":")]
                ev_text = ev[0] if ev else f"{metric.title()}: see trend lines."

                cost_rows.append((
                    f"Right-size {metric.split('_')[0].upper()} tiers",
                    f"**Phase 1:** Identify services that sit persistently above the fleet median for {metric.replace('_',' ')} and validate that the demand is real rather than a monitoring artefact.<br><br>"
                    f"**Phase 2:** Move qualified services to optimized capacity tiers that match measured load while writing down new limits and rollback steps so the change is reversible.<br><br>"
                    f"**Phase 3:** Re measure the spread relative to the median and record the monthly run cost so savings are evidenced.",
                    "- Reduces over provisioning because capacity matches measured demand rather than worst case assumptions.<br><br>"
                    "- Trims premium spend on hotspots because only the components that need higher tiers retain them.<br><br>"
                    "- Stabilises monthly spend because load is engineered into predictable envelopes.<br><br>"
                    "- Improves financial governance because decisions are tied to metrics rather than guesswork.",
                    calc_text,
                    ev_text
                ))
                perf_rows.append((
                    f"Auto-scale by rolling Q3 ({metric.split('_')[0].upper()})",
                    f"**Phase 1:** Compute a rolling Q3 threshold for {metric.replace('_',' ')} per service so policy reflects current behaviour.<br><br>"
                    f"**Phase 2:** Trigger scale events when the threshold is breached and capture context for later tuning.<br><br>"
                    f"**Phase 3:** Tune cooldowns and min max step sizes to avoid oscillation and ensure stability.",
                    "- Maintains performance during spikes because capacity expands at the moment sustained pressure appears.<br><br>"
                    "- Prevents prolonged high utilisation windows because automatic scale downs return headroom after peaks.<br><br>"
                    "- Reduces firefighting because scaling behaviour is predictable and measurable.<br><br>"
                    "- Improves SLO attainment because p95 and p99 latency stay within target under load.",
                    "Pressure time reduced = pre–post hours above rolling Q3 (service-level).",
                    ev_text
                ))
                perf_rows.append((
                    f"Hot-path optimization for {metric.split('_')[0].upper()}",
                    f"**Phase 1:** Profile workloads to locate the exact functions queries or routes that consume the most {metric.split('_')[0].upper()} and confirm impact on user journeys.<br><br>"
                    f"**Phase 2:** Implement targeted fixes such as caching indexing batching or queueing on those paths while keeping scope small to limit risk.<br><br>"
                    f"**Phase 3:** Validate latency and utilisation reductions with A B or before after measurements.",
                    "- Shortens p95 latency on busy journeys because the hottest paths become cheaper to execute.<br><br>"
                    "- Increases throughput within the same capacity because units of work consume fewer resources.<br><br>"
                    "- Lowers incident frequency tied to timeouts because contention is removed at the source.<br><br>"
                    "- Extends hardware life because efficiency gains defer upgrades.",
                    "Δ(util %) × request volume on treated services.",
                    ev_text
                ))
                sat_rows.append((
                    f"Prioritize UX-facing near-peak {metric.split('_')[0].upper()} services",
                    "**Phase 1:** Rank services by proximity to peak and mark which ones are user facing with high business impact.<br><br>"
                    "**Phase 2:** Apply the fastest improvements for these services first to deliver visible relief quickly.<br><br>"
                    "**Phase 3:** Track CSAT and NPS specifically for affected journeys to prove customer value.",
                    "- Reduces slow interactions that customers notice during business hours which protects satisfaction scores.<br><br>"
                    "- Lowers complaint volume because the most visible slowness is addressed early in the plan.<br><br>"
                    "- Builds trust with stakeholders because improvements are targeted and measured.<br><br>"
                    "- Improves adoption of new features because performance blockers are removed.",
                    "CSAT/NPS uplift on treated cohort vs control.",
                    ev_text
                ))
                sat_rows.append((
                    f"Status comms during high {metric.split('_')[0].upper()} windows",
                    "**Phase 1:** Trigger communication when fleet averages cross thresholds and include the likely impact and time to mitigate.<br><br>"
                    "**Phase 2:** Provide ETA and practical mitigation steps for users such as retry guidance and off peak suggestions.<br><br>"
                    "**Phase 3:** Publish a short post mortem that explains what changed to prevent recurrence.",
                    "- Reduces anxiety and inbound tickets because people know what is happening and when it will improve.<br><br>"
                    "- Maintains trust because updates arrive on a predictable cadence with concrete actions.<br><br>"
                    "- Improves agent efficiency because fewer duplicate queries reach the service desk.<br><br>"
                    "- Increases transparency which helps partners plan around temporary constraints.",
                    "Queries avoided during threshold breaches.",
                    ev_text
                ))

            def _mk_table(rows):
                if not rows: return "No data available."
                header = "| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |\n|---|---|---|---|---|"
                body = "\n".join([f"| {a} | {b} | {c} | {d} | {e} |" for (a,b,c,d,e) in rows])
                return header + "\n" + body

            cio_8_2 = {
                "cost": _mk_table(cost_rows),
                "performance": _mk_table(perf_rows),
                "satisfaction": _mk_table(sat_rows),
            }
            render_cio_tables("Resource Utilization — CIO Table", cio_8_2)
        else:
            miss = need - set(df.columns)
            st.warning(f"Missing columns for this subtarget: {', '.join(sorted(miss))}.")

    # =======================================================
    # 8.3 Capacity Planning Recommendations (Roll-up plan)
    # =======================================================
    with st.expander("📌 Capacity Planning Recommendations"):
        need = {"report_date","service_name","service_category",
                "cpu_utilization","memory_utilization","disk_utilization","network_utilization"}
        if need.issubset(df.columns):
            util = df.dropna(subset=["service_name"]).copy()
            grp = (util.groupby(["service_name","service_category"])
                        [["cpu_utilization","memory_utilization","disk_utilization","network_utilization"]]
                        .quantile(0.75)
                        .reset_index())
            if grp.empty:
                st.info("No utilization data available to build capacity plan.")
            else:
                grp["q3_avg_util"] = grp[["cpu_utilization","memory_utilization","disk_utilization","network_utilization"]].mean(axis=1)
                top = grp.sort_values("q3_avg_util", ascending=False).head(15)

                fig = px.bar(
                    top, x="service_name", y="q3_avg_util", color="service_category",
                    title="Capacity Plan Focus — Top 15 by Q3 Average Utilization",
                    labels={"q3_avg_util":"Q3 Avg Utilization (%)","service_name":"Service"},
                    hover_data=["cpu_utilization","memory_utilization","disk_utilization","network_utilization"],
                    color_discrete_sequence=MES_BLUE,
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)

                # Dynamic analysis (strict template)
                overall_median_q3 = grp["q3_avg_util"].median()
                top_peak = top.iloc[0]
                top_low  = top.iloc[-1]
                st.markdown("### Analysis")
                st.write(f"""
**What this graph is:** A **priority bar chart** highlighting services that most need capacity actions based on **Q3 average utilization**.  
**X-axis:** Service names (top 15 by Q3 average).  
**Y-axis:** Q3 average utilization (%).

**What it shows in your data:**  
- **Top service:** **{top_peak['service_name']}** at **{top_peak['q3_avg_util']:.1f}%**.  
- **Lowest within top 15:** **{top_low['service_name']}** at **{top_low['q3_avg_util']:.1f}%**.  
- **Fleet median Q3:** **{overall_median_q3:.1f}%**.

**Overall:** Focus the plan where the bars sit far above **{overall_median_q3:.1f}%** to yield the **biggest headroom gains** first.

**How to read it operationally:**  
- **Gap = headroom to reclaim:** The bar height above the median is the **immediate capacity opportunity**.  
- **Lead–lag with complaints:** Cross-reference with response-time/CSAT dips to prioritize user-facing services.  
- **Recovery strength:** Post-action bars should trend down toward the median, demonstrating regained headroom.

**Why this matters:** A targeted plan avoids blanket upgrades and **maximizes ROI** by treating the **highest-pressure services** first.
""")

                # Dataset-only cost metric: sum of pressure above median for these services
                pressure_pp = (top["q3_avg_util"] - overall_median_q3).clip(lower=0).sum()
                calc_text = f"Σ(max(Q3_avg − Median_Q3, 0)) for focus set = **{int(pressure_pp)}** %-points"
                evidence = (f"Top service **{top_peak['service_name']}** at **{top_peak['q3_avg_util']:.1f}%**; "
                            f"focus bars sit above median **{overall_median_q3:.1f}%** indicating persistent pressure.")

                # ---------- CIO TABLES (Expanded explanation + benefits) ----------
                cio_8_3 = {
                    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Migrate focus-set to cost-efficient tiers** | **Phase 1:** Plan migrations for the highest pressure services and document risk, rollback and validation so stakeholders agree on the approach. <br><br> **Phase 2:** Execute migrations in controlled waves with monitoring and backout checkpoints so customer impact is minimised. <br><br> **Phase 3:** Verify the drop in Q3 average and record the cost delta to quantify savings. | - Cuts spend exactly where persistent pressure forces premium capacity and therefore generates avoidable cost. <br><br> - Avoids blanket upgrades because action is limited to services that show sustained load. <br><br> - Improves financial outcomes without eroding performance because migrations are measured and reversible. <br><br> - Provides clear proof of value because pre and post numbers are captured. | {calc_text} | {evidence} |
| **Decommission/merge idle neighbors** | **Phase 1:** Identify low utilisation sibling services and components that sit adjacent to hotspots and confirm that business risk is low. <br><br> **Phase 2:** Consolidate or retire these components and rebalance resources so headroom shifts to where it is needed. <br><br> **Phase 3:** Re validate safety margins and monitor for any unintended side effects. | - Eliminates waste by removing capacity that delivers little value to users. <br><br> - Keeps hot paths supplied with headroom because reclaimed resources are redirected intelligently. <br><br> - Simplifies the platform which lowers maintenance effort and defect surface area. <br><br> - Improves change velocity because fewer systems must be coordinated. | Idle pp reclaimed = Σ(max(Median − Util, 0)). | Contrast of high bars vs fleet shows skew worth rebalancing. |
| **License/IO tier reallocation** | **Phase 1:** Match license levels and storage IO tiers to measured load categories with explicit rules per tier. <br><br> **Phase 2:** Reassign premium tiers only to hot services and shift cold paths to standard tiers so spend aligns to usage. <br><br> **Phase 3:** Audit the savings and verify that performance SLOs remain green. | - Stops overspending on cold paths because premium entitlements are reserved for real demand. <br><br> - Maintains hot path performance because premium capacity is focused where latency matters. <br><br> - Creates predictable licensing costs because entitlements track measured need. <br><br> - Strengthens compliance because allocation logic is documented and repeatable. | %-points trimmed × unit cost per tier step. | High bars point to where premium tiers pay off. |
""",
                    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Autoscaling tied to rolling Q3** | **Phase 1:** Compute rolling Q3 thresholds per service so policies adapt as behaviour changes over time. <br><br> **Phase 2:** Trigger scale up and down events from these thresholds and record each event for review. <br><br> **Phase 3:** Tune cooldowns and hysteresis so scaling is smooth and avoids oscillation. | - Keeps latency stable during bursts because capacity reacts to sustained load not noise. <br><br> - Reduces firefighting because automatic control handles predictable peaks. <br><br> - Increases availability because overload windows become shorter. <br><br> - Improves forecasting because event logs show where permanent capacity is justified. | Peak time reduced = pre–post hours above rolling Q3. | Focus bars represent sustained peaks that autoscaling can smooth. |
| **Architecture tuning for top services** | **Phase 1:** Profile CPU IO and memory bottlenecks for each top ranked service and list the most effective interventions. <br><br> **Phase 2:** Apply caching queueing or indexing changes in small, controlled increments so risk stays low. <br><br> **Phase 3:** Measure the change in Q3 utilisation and response time to confirm that headroom improved. | - Increases throughput and resilience by removing the exact bottlenecks that cap performance. <br><br> - Lowers peak contention which protects user journeys during business hours. <br><br> - Reduces incident recurrence because known hot spots are engineered out. <br><br> - Enhances developer productivity because fewer performance fires interrupt delivery. | Δ(Q3_avg_util) and Δ(response time) on treated services. | If Q3 bars shrink post-tuning, headroom improved. |
| **Stress/regression test harness** | **Phase 1:** Build repeatable high load tests that mimic real traffic patterns for the focus services. <br><br> **Phase 2:** Run tests before and after major changes and capture full metrics and traces. <br><br> **Phase 3:** Gate deployments on passing results so regressions do not reach production. | - Prevents performance regressions that inflate peaks and cause outages. <br><br> - Improves signal quality because failures are detected in a controlled environment first. <br><br> - Shortens recovery time because defects are isolated with good diagnostics. <br><br> - Raises confidence in releases which accelerates safe delivery. | Incidents/perf dips avoided after tests in place. | Peaks often follow untested changes. |
""",
                    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Communicate capacity plan outcomes** | **Phase 1:** Share the expected improvements and the timeline for each focus service with stakeholders so they know when benefits arrive. <br><br> **Phase 2:** Publish before and after graphs that show utilisation and latency shifts so gains are visible. <br><br> **Phase 3:** Collect feedback and adjust priorities to keep alignment tight. | - Reduces performance escalations because customers understand what is being improved and when. <br><br> - Increases confidence in the roadmap because progress is demonstrated with data. <br><br> - Strengthens collaboration because stakeholders can shape priorities with evidence. <br><br> - Improves adoption because teams plan around upcoming gains. | CSAT/NPS delta post-plan vs pre-plan. | Visible prioritization of top bars aligns with user-perceived speed. |
| **Fast-track user-facing hot services** | **Phase 1:** Tag which of the top 15 services are customer facing and quantify their impact on key journeys. <br><br> **Phase 2:** Prioritise fixes for these services and set short feedback loops so improvements land quickly. <br><br> **Phase 3:** Validate improvements with real user metrics not just synthetic tests. | - Delivers a direct uplift to end-user experience where delays are most damaging. <br><br> - Cuts complaint volume because the most painful slowdowns are addressed first. <br><br> - Protects revenue moments because high impact journeys stay responsive. <br><br> - Builds organisational support for the capacity programme because results are visible. | Complaints avoided = pre–post performance complaint volume. | Top-ranked user-facing services drive perceived responsiveness. |
| **Proactive status during high-load windows** | **Phase 1:** Notify stakeholders ahead of planned capacity work and explain the expected risk and mitigation. <br><br> **Phase 2:** Provide ETAs and practical guidance during the window so users can plan their activities. <br><br> **Phase 3:** Close with a short summary of results and next actions so confidence increases after each cycle. | - Reduces anxiety and support calls because people know what to expect and how to adapt temporarily. <br><br> - Maintains trust because communication is proactive and consistent. <br><br> - Improves coordination with dependent teams because timelines are clear. <br><br> - Enhances satisfaction because users see steady improvement backed by updates. | Queries avoided during maintenance windows. | Clear communication tempers expectations at peak times. |
"""
                }
                render_cio_tables("Capacity Planning — CIO Table", cio_8_3)
        else:
            miss = need - set(df.columns)
            st.warning(f"Missing columns for this subtarget: {', '.join(sorted(miss))}.")
