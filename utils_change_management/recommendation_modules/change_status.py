import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose

# 🔹 Helper function to render CIO tables with 3 nested expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("💰 Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("⚙️ Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("💬 Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)


# 🔹 Module 4: Change Status & Progress
def change_status(df_filtered):

    
    st.markdown("""
    This section examines the **current lifecycle position of changes** (e.g., Submitted, Approved, In Progress, Implemented), 
    highlights **where items get stuck**, and quantifies **backlog risk** across time, priority, and department.
    """)

    # ---------------------- Subtarget 4a ----------------------
    with st.expander("📌 Current Status Distribution & Backlog Ratio"):
        if "Status" in df_filtered.columns:
            df_filtered["status_clean"] = df_filtered["status"].astype(str).str.strip().str.title()
            status_counts = df_filtered["status_clean"].value_counts(dropna=False).reset_index()
            status_counts.columns = ["status", "count"]
        
            # Graph 1: Current status distribution (bar)
            fig_status = px.bar(
                status_counts, x="Status", y="Count", color="Count",
                color_continuous_scale="Blues", title="Current Change Status Distribution"
            )
            st.plotly_chart(fig_status, use_container_width=True)

            # Backlog = anything not Implemented
            total = len(df_filtered)
            implemented = df_filtered["status_clean"].eq("implemented").sum()
            backlog = total - implemented
            backlog_ratio = (backlog / total * 100) if total > 0 else 0

            st.markdown("#### Analysis – Status Snapshot & Backlog")
            st.write(f"""
            - Total changes: **{total}**  
            - Implemented: **{implemented}**  
            - Backlog (not implemented): **{backlog}**  
            - Backlog ratio: **{backlog_ratio:.1f}%**  

            📊 **Client takeaway:** A high backlog ratio signals **approval or execution bottlenecks**. 
            Prioritizing quick wins (low-risk items) and tightening approval SLAs reduce status stagnation.
            """)

            # CIO Table for 4a
            cio_4a = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation (Formula & Numeric Example) | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|----------------------------------------------|--------------------------------|
                | Introduce “Fast-Track” lane for low-risk changes | Phase 1: define low-risk criteria → Phase 2: parallel queue → Phase 3: auto-approve with audit trail | Cuts waiting time & admin effort | If 30% of 200 backlogged items get 1.5h faster processing → 0.3×200×1.5 = **90h saved** | Bar shows large non-Implemented share → ideal for fast-track. |
                | Batch-approve repetitive changes weekly | Phase 1: group similar items → Phase 2: batch-CAB → Phase 3: monthly review | Reduces meeting overhead | 20 items × 0.5h CAB savings = **10h/week** | Status skew indicates many small items awaiting approval. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Define status SLAs & auto-escations | Phase 1: SLA thresholds per status → Phase 2: auto reminders → Phase 3: escalation path | Improves flow-through time | 25% reduction in time-in-status → shorter cycle time overall | Backlog ratio suggests slow transitions between statuses. |
                | Visual WIP limits per status column | Phase 1: Kanban limits → Phase 2: enforce max items → Phase 3: rebalance weekly | Avoids overload & thrashing | Fewer context switches; +15% throughput | Excessive counts in early columns indicate WIP overload. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Publish status dashboards to requestors | Phase 1: expose live status → Phase 2: add expected SLA timer → Phase 3: enable notifications | Lowers uncertainty & follow-ups | Indirect: fewer “status check” tickets | Bar reveals many items waiting → transparency reduces anxiety. |
                """
            }
            render_cio_tables("CIO Recommendations – Status Distribution & Backlog", cio_4a)

        else:
            st.warning("⚠️ 'Status' column not found in dataset.")


    # ---------------------- Subtarget 4b ----------------------
    with st.expander("📌 Status Progress Over Time (Monthly Trend)"):
        if {"status", "implemented_date"}.issubset(df_filtered.columns):
            df_filtered["implemented_Date"] = pd.to_datetime(df_filtered["implemented_Date"], errors="coerce")
            df_filtered["month"] = df_filtered["implemented_Date"].dt.to_period("M").astype(str)
            df_filtered["status_clean"] = df_filtered["status"].astype(str).str.strip().str.title()

            monthly_status = df_filtered.groupby(["month", "status_clean"]).size().reset_index(name="Count")

            # Graph 2: Monthly trend by status (line)
            fig_trend = px.line(
                monthly_status, x="Month", y="Count", color="status_clean", markers=True,
                title="Monthly Trend by Change Status"
            )
            st.plotly_chart(fig_trend, use_container_width=True)

            if not monthly_status.empty:
                # Find status with biggest month spike
                idxmax = monthly_status["count"].idxmax()
                spike = monthly_status.loc[idxmax]
                avg_month = monthly_status.groupby("status_clean")["Count"].mean().mean()

                st.markdown("#### Analysis – Monthly Status Trajectory")
                st.write(f"""
                - Largest single-month spike: **{spike['status_clean']}** in **{spike['Month']}** with **{spike['Count']}** changes.  
                - Average monthly volume per status ≈ **{avg_month:.1f}**.  
                - Observable **seasonal behavior** suggests either change freezes or large release waves during certain months.

                📊 **Client takeaway:** Understanding when statuses pile up (e.g., more in *Approved* vs *In Progress*) 
                allows targeted interventions like **pre-staging resources** or **enforcing release calendars**.
                """)

            # CIO Table for 4b
            cio_4b = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Align staffing with monthly status spikes | Phase 1: forecast based on trend → Phase 2: reschedule shifts → Phase 3: track overtime | Cuts unmanaged overtime | 20% overtime reduction in spike months → RM savings | Trend lines show recurring spikes by status/month. |
                | Pre-approve standard changes ahead of spike months | Phase 1: template standards → Phase 2: batch pre-approval → Phase 3: audit sampling | Reduces CAB time & delays | 50 std changes × 0.3h saved = 15h | Visible pre-implementation queue increases before peaks. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Enforce release windows with freeze periods | Phase 1: define windows → Phase 2: align infra/app teams → Phase 3: compliance reporting | Smoother flow & fewer rollbacks | Indirect: lower failure restores | Status waves suggest poorly controlled releases. |
                | Introduce “Ready for Implementation” gate checklist | Phase 1: pre-req checks → Phase 2: evidence attachment → Phase 3: spot audits | Reduces rework and handover friction | 10% cycle time drop across *In Progress* | Month-on-month pileups imply handoff friction. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Inform business of planned status spikes | Phase 1: publish calendar → Phase 2: notify critical stakeholders → Phase 3: feedback loop | Reduces surprise, improves trust | Low cost; fewer escalation calls | Trend spikes correlate with business change windows. |
                """
            }
            render_cio_tables("CIO Recommendations – Monthly Status Trend", cio_4b)
        else:
            st.warning("⚠️ Required columns ('Status', 'Implemented_Date') not found.")


    # ---------------------- Subtarget 4c ----------------------
    with st.expander("📌 Pending Backlog by Priority & Department"):
        # Guard: need Status, Priority, optionally Department
        needed = {"status", "priority"}
        if needed.issubset(df_filtered.columns):
            df_filtered["status_clean"] = df_filtered["status"].astype(str).str.strip().str.title()
            df_filtered["pending_flag"] = df_filtered["status_clean"].ne("Implemented")

            # Graph 3a: Pending by Priority
            pend_priority = df_filtered[df_filtered["pending_flag"]].groupby("Priority").size().reset_index(name="Count")
            if not pend_priority.empty:
                fig_p1 = px.bar(
                    pend_priority, x="Priority", y="Count", color="Count",
                    color_continuous_scale="Reds", title="Pending Backlog by Priority"
                )
                st.plotly_chart(fig_p1, use_container_width=True)

            # Graph 3b: Pending by Department (if available)
            if "Department" in df_filtered.columns:
                pend_dept = df_filtered[df_filtered["pending_flag"]].groupby("Department").size().reset_index(name="Count")
                if not pend_dept.empty:
                    fig_p2 = px.bar(
                        pend_dept, x="Department", y="Count", color="Count",
                        color_continuous_scale="Oranges", title="Pending Backlog by Department"
                    )
                    st.plotly_chart(fig_p2, use_container_width=True)

            # Analysis
            if not pend_priority.empty:
                worst_pri = pend_priority.loc[pend_priority["Count"].idxmax()]
                st.markdown("#### Analysis – Backlog Concentration")
                st.write(f"""
                - Largest pending backlog by **priority**: **{worst_pri['Priority']}** with **{worst_pri['Count']}** items.  
                - Departments (if shown) with persistent pending counts require **targeted unblocking** and resource allocation.

                📊 **Client takeaway:** Prioritization drift (too many highs) and departmental bottlenecks increase risk of **slippage**, 
                **firefighting**, and **budget leakage** through rework.
                """)

            # CIO Table for 4c
            cio_4c = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Cap the % of High priority in backlog | Phase 1: define cap (e.g., ≤30%) → Phase 2: reclassify with SME review → Phase 3: audit | Prevents priority inflation → lowers “urgent” handling costs | If 20 items downgraded save 0.5h each → **10h saved** | Priority bar shows disproportionate High backlog. |
                | Cross-staff backlog swarms | Phase 1: weekly swarm on top dept → Phase 2: rotate SMEs → Phase 3: close/report | Clears bottlenecks without hiring | 12 items × 1h faster closure = **12h** | Dept bar pinpoints a single backlog-heavy team. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Auto-aging alerts + WIP dashboards | Phase 1: age buckets → Phase 2: alert after threshold → Phase 3: review weekly | Improves time-to-implement | 25% drop in items >14 days | Persistent pending bars evidence aging risk. |
                | Define unblock owner for each pending cluster | Phase 1: assign owner → Phase 2: daily standup → Phase 3: measure throughput | Faster cross-team coordination | 15% higher weekly completions | Dept chart shows clusters; ownership resolves “stuck” items. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Notify impacted requestors of aging changes | Phase 1: automated comms → Phase 2: ETA & mitigation → Phase 3: feedback channel | Reduces escalations & anxiety | Indirect benefit via fewer complaints | Pending concentration highlights user-impact risk; comms offsets it. |
                """
            }
            render_cio_tables("CIO Recommendations – Backlog by Priority & Department", cio_4c)
        else:
            st.warning("⚠️ Required columns ('Status', 'Priority') not found.")
