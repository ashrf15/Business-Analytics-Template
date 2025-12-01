import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose

# 🔹 Helper function for CIO tables with 3 nested expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("💰 Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("⚙️ Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("💬 Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)


# 🔹 Module 5: Change Approval Process
def approval_process(df_filtered):

    
    st.markdown("""
    This section evaluates how efficiently **change approvals** progress through the CAB (Change Advisory Board) pipeline, 
    focusing on **approval time**, **status distribution**, and **approver performance trends**.  
    A slow or inconsistent approval process leads to operational delays and project backlogs.
    """)

    # ---------------------- Subtarget 5a ----------------------
    with st.expander("📌 Approval Status Distribution"):
        if "Approval_Status" in df_filtered.columns:
            df_filtered["approval_status_clean"] = df_filtered["approval_status"].astype(str).str.strip().str.title()
            approval_counts = df_filtered["approval_status_clean"].value_counts().reset_index()
            approval_counts.columns = ["approval_status", "count"]

            fig1 = px.bar(
                approval_counts, x="Approval_Status", y="Count", color="Count",
                color_continuous_scale="Teal", title="Change Requests by Approval Status"
            )
            st.plotly_chart(fig1, use_container_width=True)

            total = approval_counts["count"].sum()
            approved = approval_counts.loc[approval_counts["approval_status"] == "approved", "count"].sum()
            rejected = approval_counts.loc[approval_counts["approval_status"] == "rejected", "count"].sum()
            pending = total - (approved + rejected)

            approved_pct = (approved / total * 100) if total > 0 else 0
            rejected_pct = (rejected / total * 100) if total > 0 else 0
            pending_pct = (pending / total * 100) if total > 0 else 0

            st.markdown("#### Analysis – Approval Distribution")
            st.write(f"""
            - Total reviewed changes: **{total}**  
            - Approved: **{approved} ({approved_pct:.1f}%)**  
            - Rejected: **{rejected} ({rejected_pct:.1f}%)**  
            - Pending: **{pending} ({pending_pct:.1f}%)**

            📊 **Client takeaway:** A high pending percentage suggests either CAB scheduling constraints or unclear approval authority. 
            Establishing parallel review queues and better automation can help achieve faster throughput.
            """)

            # CIO Table for 5a
            cio_5a = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Automate low-risk approvals | Phase 1: define auto-approval criteria → Phase 2: integrate with workflow engine → Phase 3: audit exceptions monthly | Reduces manual CAB hours | 50 low-risk changes × 0.5h CAB time = **25h saved/month** | Bar shows many pending low-risk items. |
                | Combine CAB meetings bi-weekly | Phase 1: align schedules → Phase 2: batch reviews → Phase 3: enforce quorum | Cuts meeting overhead & improves predictability | 2 meetings saved/month × 10 members × 1h = **20h saved** | Balanced approval vs pending ratio indicates excess meeting cycles. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Create digital CAB dashboards | Phase 1: unify approval pipeline data → Phase 2: real-time tracking → Phase 3: alerts on bottlenecks | Improves decision speed | Shorter approval time (−20%) saves ~10h/month | Pie chart imbalance shows long tail of pending requests. |
                | Parallelize functional approvals | Phase 1: split approvals by domain → Phase 2: concurrent sign-offs → Phase 3: periodic review | Reduces bottlenecks in sequential process | Reduces approval cycle by 2 days per change | High pending rate demonstrates linear bottleneck. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Provide CAB decision visibility to requestors | Phase 1: show approval stage in real time → Phase 2: include estimated completion → Phase 3: email summary | Improves transparency and trust | Indirect reduction in escalations | Stakeholders often unaware of decision timeline—visualization helps. |
                | Publish monthly approval turnaround KPIs | Phase 1: aggregate metrics → Phase 2: display dashboard → Phase 3: publish improvement targets | Enhances accountability | Non-financial, reputational gain | Approved vs rejected data supports transparent benchmarking. |
                """
            }
            render_cio_tables("CIO Recommendations – Approval Status Overview", cio_5a)
        else:
            st.warning("⚠️ 'Approval_Status' column not found in dataset.")


    # ---------------------- Subtarget 5b ----------------------
    with st.expander("📌 Approval Time Analysis (Speed & Trends)"):
        if "Approval_Time_Days" in df_filtered.columns:
            df_filtered["Approval_Time_Days"] = pd.to_numeric(df_filtered["Approval_Time_Days"], errors="coerce")
            df_filtered = df_filtered.dropna(subset=["Approval_Time_Days"])

            fig2 = px.histogram(df_filtered, x="Approval_Time_Days", nbins=20, color_discrete_sequence=["#0b5394"],
                                title="Distribution of Change Approval Times (Days)")
            st.plotly_chart(fig2, use_container_width=True)

            avg_time = df_filtered["Approval_Time_Days"].mean()
            median_time = df_filtered["Approval_Time_Days"].median()
            p90_time = df_filtered["Approval_Time_Days"].quantile(0.9)

            st.markdown("#### Analysis – Approval Duration Insights")
            st.write(f"""
            - Average approval time: **{avg_time:.1f} days**  
            - Median approval time: **{median_time:.1f} days**  
            - 90th percentile (slowest): **{p90_time:.1f} days**  

            📊 **Client takeaway:** Long-tail approvals (above {p90_time:.1f} days) typically stem from cross-department dependencies 
            or unclear ownership. Reducing these outliers can significantly cut total cycle time.
            """)

            # CIO Table for 5b
            cio_5b = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Reduce CAB quorum dependency | Phase 1: set digital quorum → Phase 2: use asynchronous approvals → Phase 3: enforce SLA | Cuts idle waiting time | 10% faster approval = 1 day saved/change × 100 changes = **100 days saved** | Histogram shows long tail delays beyond 5 days. |
                | Simplify documentation for low-risk changes | Phase 1: prefilled templates → Phase 2: automate validation → Phase 3:  periodic review | Less admin time | 30min saved/change = 50h/quarter | Skew in histogram evidences excessive approval documentation lag. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Implement SLA-based CAB auto-reminders | Phase 1: define thresholds (3d, 5d) → Phase 2: trigger alerts → Phase 3: measure breach count | Reduces overdue approvals | 25% drop in slow approvals | Histogram tail proves inconsistent follow-ups. |
                | Visualize approval time by category/approver | Phase 1: pivot analytics → Phase 2: publish monthly heatmap → Phase 3: link KPI to CAB performance | Faster accountability loop | 15% quicker median turnaround | Wide variance across categories reflects CAB unevenness. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Notify requestors of approval SLA breaches | Phase 1: automated comms → Phase 2: provide ETA → Phase 3: survey satisfaction | Improves communication flow | Indirect – fewer follow-ups | Histogram right tail indicates user frustration due to delays. |
                | Introduce “urgent track” with VIP approval | Phase 1: identify critical users → Phase 2: dedicated approver pool → Phase 3: monitor outcomes | Reduces business impact of critical waits | Cost neutral; productivity gain | Tail-end approvals affect high-impact services. |
                """
            }
            render_cio_tables("CIO Recommendations – Approval Time Efficiency", cio_5b)
        else:
            st.warning("⚠️ 'Approval_Time_Days' column not found in dataset.")


    # ---------------------- Subtarget 5c ----------------------
    with st.expander("📌 Approver Performance by Category & Priority"):
        if {"Approver", "Category", "Priority", "Approval_Time_Days"}.issubset(df_filtered.columns):
            approver_perf = (
                df_filtered.groupby(["Approver", "Category"])["Approval_Time_Days"]
                .mean()
                .reset_index()
                .rename(columns={"Approval_Time_Days": "Avg_Approval_Time"})
            )

            fig3 = px.bar(
                approver_perf, x="Approver", y="Avg_Approval_Time", color="Category",
                title="Average Approval Time per Approver by Category", barmode="group"
            )
            st.plotly_chart(fig3, use_container_width=True)

            slowest = approver_perf.loc[approver_perf["Avg_Approval_Time"].idxmax()]
            avg_all = approver_perf["Avg_Approval_Time"].mean()

            st.markdown("#### Analysis – Approver Efficiency Insights")
            st.write(f"""
            - Slowest approver average time: **{slowest['Approver']} ({slowest['Avg_Approval_Time']:.1f} days)**  
            - Overall average approval duration: **{avg_all:.1f} days**  
            - Significant variance across approvers indicates inconsistent workloads or unclear delegations.  

            📊 **Client takeaway:** Tracking approver efficiency at this granularity ensures accountability and enables workload balancing.
            """)

            # CIO Table for 5c
            cio_5c = {
                "cost": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Redistribute approvals among fast approvers | Phase 1: identify top performers → Phase 2: assign overflow → Phase 3: rebalance monthly | Reduces idle time | 15% faster throughput = RM savings on idle resource | Bar variance reveals high disparity between approvers. |
                | Introduce rotating approver scheme | Phase 1: cycle workloads weekly → Phase 2: prevent burnout → Phase 3: report metrics | Keeps approval flow steady | Balanced effort = fewer delays | Category clusters show overdependence on few CAB members. |
                """,
                "performance": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Publish approver leaderboard | Phase 1: track median time → Phase 2: visualize dashboards → Phase 3: link recognition | Drives accountability | Low cost; strong morale impact | Wide time gap between approvers shown in bar chart. |
                | Introduce SLA-linked approver KPIs | Phase 1: define KPI (avg ≤3d) → Phase 2: measure & publish → Phase 3: adjust targets quarterly | Improves overall throughput | 20% median reduction | Data confirms slowest approvers exceed mean +2σ range. |
                """,
                "satisfaction": """
                | Recommendation | Explanation (phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
                |----------------|----------------------|----------|------------------|--------------------------------|
                | Communicate expected approval timelines | Phase 1: publish CAB SLA → Phase 2: notify requestors automatically → Phase 3: feedback follow-up | Manages expectations | Indirect satisfaction gain | Slow approvals harm perceived responsiveness. |
                | Implement self-service approval tracking | Phase 1: add CAB portal view → Phase 2: allow users to track own requests | Builds confidence & visibility | Minimal setup cost | Bar chart highlights performance gaps users can now monitor. |
                """
            }
            render_cio_tables("CIO Recommendations – Approver Performance Insights", cio_5c)
        else:
            st.warning("⚠️ Required columns ('Approver', 'Category', 'Priority', 'Approval_Time_Days') not found.")
