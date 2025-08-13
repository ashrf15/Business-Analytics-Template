import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np

from utils1.utils2.ticket_volume import ticket_volume
from utils1.utils2.resolution_time import resolution_time
from utils1.utils2.technician_performance import technician_performance
from utils1.utils2.incident_trends import incident_trends
from utils1.utils2.sla import sla

def recommendation(df):
    st.markdown("## 📊 Data Analysis Recommendation")
    st.markdown("---")
    st.subheader("Select Date Range")

    if 'created_time' in df.columns and not df['created_time'].isna().all():
        df['created_time'] = pd.to_datetime(df['created_time'], errors='coerce')
        df['created_date'] = df['created_time'].dt.date
        min_date = df['created_date'].min()
        max_date = df['created_date'].max()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date, key="start_date_picker")
        with col2:
            end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date, key="end_date_picker")

        st.markdown(f"🗓️ **Selected Range:** `{start_date.strftime('%d/%m/%Y')}` → `{end_date.strftime('%d/%m/%Y')}`")

        reset_filter = st.button("🔁 Reset to Default", key="reset_button_2")

        if reset_filter:
            df_filtered = df.copy()
            st.info("Showing all available data (no date filter applied).")
        elif start_date > end_date:
            st.warning("⚠️ Start date is after end date. Please select a valid range.")
            return
        else:
            df_filtered = df[(df['created_date'] >= start_date) & (df['created_date'] <= end_date)]
    else:
        df_filtered = df.copy()

    st.markdown("---")

    st.subheader("📌 Overview Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tickets", len(df_filtered))
    col2.metric("Avg Resolution Time (hrs)", f"{df_filtered['resolution_time'].mean():.2f}")
    col3.metric("Departments Involved", df_filtered['department'].nunique())

    st.markdown("---")

    # 📦 TICKET VOLUME ANALYSIS
    st.header("📦 Ticket Volume Analysis")
    ticket_volume(df)
#----------------------------------------------------------------------------------------------------

    #🎯 Response & Resolution Time
    st.header("🎯 Response & Resolution Time")
    resolution_time(df)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 Technician Workload Analysis
    st.header("Agent/Technician Performance")
    technician_performance(df)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Incident Trends
    st.header("Incident Trends")
    incident_trends(df)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Incident Trends
    st.header("Service Level Agreements (SLAs)")
    sla(df)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    st.markdown("---")


    # --- SLA (Optional) ---
    if 'sla_hours' in df_filtered.columns:
            df_filtered['sla_met'] = df_filtered['resolution_time'] <= df_filtered['sla_hours']
            sla_rate = df_filtered['sla_met'].mean() * 100
            st.markdown(f"**SLA Compliance**: {sla_rate:.2f}%")

            average_resolution = df_filtered['resolution_time'].mean()
            median_resolution = df_filtered['resolution_time'].median()

            with st.expander("📌 SLA Recommendation"):
                if sla_rate < 80:
                    st.markdown(f"""
        ### ⚠️ SLA Compliance Below Target

        The SLA compliance rate is currently **{sla_rate:.2f}%**, which indicates that a significant number of tickets are not being resolved within the expected timeframe.

        ---

        ### 🎯 Precise Recommendations for Optimizing SLA Compliance

        #### 1. Contextualizing the Resolution Time Distribution

        While the **average resolution time is {average_resolution:.2f} hours**, the distribution shows a strong left-skew with most tickets resolved far more quickly. The **median resolution time is {median_resolution:.2f} hours**, confirming that **a small number of extreme outliers are inflating the average**.

        This suggests that instead of widespread inefficiency, the **focus should be on addressing the long-tail of exceptionally delayed tickets.**

        ---

        #### 2. Identify and Analyze Extreme Outliers

        **Action**: Define a threshold for "extreme" resolution times (e.g., tickets over 200 hours or in the top 5% of delays).

        **Action**: For these outliers, investigate:
        - **Ticket Type**: Are certain types consistently delayed?
        - **Assigned Department**: Do delays cluster in certain teams?
        - **Dependencies**: Were tickets held up by vendor/customer input?
        - **Status Lifecycle**: Which status consumed the most time?
        - **Ownership Gaps**: Was the ticket unassigned or bounced between agents?

        **Deliverable**: A report listing high-resolution-time tickets and the root causes for delay.

        **Why it Matters**: Targets the key drivers of SLA violations with precision.

        ---

        #### 3. Standardize Escalation and Handover Processes

        **Action**: Audit and enhance current escalation procedures:
        - Define **SLA thresholds per status** (e.g., “pending approval > 48 hours” triggers escalation).
        - **Automate alerts** for tickets approaching SLA limits.
        - **Formalize handoff SLAs** between departments or teams.
        - **Route aged tickets** to specialized resolution squads.

        **Deliverable**: Documented escalation matrix, revised SLAs, and automated workflows in the ticketing system.

        **Why it Matters**: Ensures high-risk tickets get prioritized before SLA breach.

        ---

        #### 4. Leverage High-Performing Teams & Individuals

        **Action**: Analyze consistently fast-resolving agents (e.g., Eddy Razlan Abdul Latiff) and extract their best practices:
        - Troubleshooting shortcuts or templates
        - Communication techniques for faster customer input
        - Smart use of ticketing features (e.g., macros, internal notes)

        **Action**: Create training and knowledge base content from these insights.

        **Deliverable**: Best practices playbook, agent guides, and onboarding materials.

        **Why it Matters**: Democratizes success tactics across all teams to raise baseline performance.

        ---

        ### 📈 Strategic Considerations

        #### A. Track Median Resolution Time

        **Action**: Supplement SLA tracking with **median resolution time** to provide a more realistic view of efficiency unaffected by outliers.

        #### B. Proactive Problem Management

        **Action**: Analyze recurring themes in outlier tickets and elevate them into **root cause analysis** and **problem resolution initiatives**.

        #### C. Map the Customer Journey

        **Action**: For common long-running tickets, map the end-to-end customer experience to locate pain points or information gaps.

        **Why it Matters**: Enhances user satisfaction and highlights non-technical delays (like poor follow-up or approvals).
                    """)
                else:
                    st.markdown(f"""
        ### ✅ SLA Compliance is Healthy

        With a compliance rate of **{sla_rate:.2f}%**, the support process is currently performing well.

        ---

        ### 🧠 Recommendation

        Maintain current SLA workflows while:

        - Implementing **continuous monitoring dashboards**
        - Exploring automation for **alerts and escalations**
        - Introducing **median resolution time** as a supplementary metric to understand day-to-day efficiency

        These measures will help maintain and gradually enhance SLA compliance beyond current levels.
                    """)


    # --- Resolution Time Distribution ---
    if 'resolution_time' in df_filtered.columns:
        fig = px.histogram(
            df_filtered, 
            x='resolution_time', 
            nbins=30, 
            marginal="box", 
            title="Distribution of Resolution Time", 
            color_discrete_sequence=['#1f77b4']
        )
        fig.update_layout(
            xaxis_title="Resolution Time (hrs)", 
            yaxis_title="Ticket Count"
        )
        st.plotly_chart(fig, use_container_width=True)

        avg_res = df_filtered['resolution_time'].mean()
        median_res = df_filtered['resolution_time'].median()
        
        st.markdown(f"**Average Resolution Time**: {avg_res:.2f} hrs")
        st.markdown(f"**Median Resolution Time**: {median_res:.2f} hrs")

        if avg_res > 48:
            loss = (avg_res - 48) * len(df_filtered) * 50  # Assuming RM50/hour cost
            st.markdown(f"""
        ### ⚠️ High Average Resolution Time Detected

        The current **average resolution time is {avg_res:.2f} hours**, exceeding the 48-hour benchmark. Notably, the **median is {median_res:.2f} hours**, suggesting that most tickets are resolved faster, but a **small number of outliers are significantly inflating the average**.

        Estimated cost impact of this delay: **~RM {loss:,.0f}**.

        ---

        ### 🎯 Precise Recommendations for Optimizing Resolution Time

        #### 1. Identify and Address Outliers

        **Action**: Define a resolution time threshold (e.g., 200 hours or top 5%) to isolate long-tail tickets.

        **Action**: Analyze these for:
        - Common ticket types or categories
        - Frequent assignment to specific teams or agents
        - Time spent in specific statuses (e.g., "Pending", "Waiting Approval")
        - Ownership issues or reassignment loops

        **Deliverable**: Root cause report on long-tail resolution delays.

        **Why it Matters**: Tackles the primary factor skewing resolution metrics.

        ---

        #### 2. Enhance Escalation & Workflow Efficiency

        **Action**: Implement stricter SLA-based triggers to flag idle or aged tickets.

        **Action**: Automate escalation or reassignment for:
        - Tickets exceeding X hours in a single status
        - Reassigned more than N times

        **Action**: Introduce status duration tracking to pinpoint bottlenecks.

        **Deliverable**: Automated alerts, dashboard views by SLA breach risk.

        **Why it Matters**: Ensures timely resolution and prevents ticket stagnation.

        ---

        #### 3. Upskill & Standardize Through Top Performers

        **Action**: Extract behaviors and shortcuts from fast-resolving agents like Eddy.

        **Action**: Document:
        - Ticket diagnosis workflows
        - High-efficiency knowledge base use
        - Customer communication styles

        **Action**: Roll out structured coaching or training modules.

        **Deliverable**: Standard operating procedures and training content.

        **Why it Matters**: Drives consistency and raises overall performance baseline.

        ---

        #### 4. Invest in Self-Service Deflection

        **Action**: Analyze high-volume, low-complexity tickets (e.g., access issues, resets).

        **Action**: Deploy or improve:
        - Chatbots
        - Guided self-resolution flows
        - FAQ-based resolution routing

        **Deliverable**: Reduction in inbound volume and average resolution time.

        **Why it Matters**: Reduces load on teams and speeds up user experience.

        ---

        #### 5. Forecast & Align Support with Demand

        **Action**: Use historical volume data to build monthly or seasonal forecasts.

        **Action**: Adjust workforce planning and training ahead of known peaks (e.g., January).

        **Deliverable**: Dynamic support model that prevents overload-driven delays.

        **Why it Matters**: Ensures you’re not solving performance with overtime alone.
                """)
        st.markdown(f"""
        ### ✅ Resolution Performance is Healthy

        With an **average resolution time of {avg_res:.2f} hours** and a **median of {median_res:.2f} hours**, resolution performance is strong and efficient.

        ---

        ### 🧠 Recommendation

        - **Maintain current workflows**, especially the factors contributing to fast median resolution.
        - **Extract and document best practices** from consistently high performers.
        - **Monitor long-tail tickets periodically** to prevent outliers from degrading overall metrics.
        - **Consider introducing a Median Resolution Time KPI** alongside the average for more representative tracking.

        This ensures continued efficiency while proactively preventing performance regression.
                """)

    # Monthly Volume
    # --- Monthly Ticket Volume ---
    if 'created_time' in df_filtered.columns:
        df_filtered['created_month'] = df_filtered['created_time'].dt.to_period("M").dt.to_timestamp()
        monthly = df_filtered.groupby('created_month').size().reset_index(name='count')
        fig = px.line(monthly, x='created_month', y='count', title="Monthly Ticket Volume", markers=True)
        fig.update_layout(xaxis_title="Created Month", yaxis_title="Ticket Count")
        fig.update_xaxes(dtick="M1", tickformat="%Y-%m-%d")
        st.plotly_chart(fig, use_container_width=True)

        # Surge detection
        mean_vol = monthly['count'].mean()
        std_vol = monthly['count'].std()
        surge_months = monthly[monthly['count'] > mean_vol + std_vol]
        surge_list = surge_months['created_month'].dt.strftime('%Y-%m-%d').tolist()

        # Identify highest volume month
        highest_row = monthly.loc[monthly['count'].idxmax()]
        highest_month = highest_row['created_month'].strftime('%Y-%m-%d')
        highest_count = highest_row['count']

        if surge_list:
            st.markdown(f"**High-Volume Periods Detected**: {', '.join(surge_list)}")
            st.markdown(f"📈 **Highest Volume Month**: {highest_month} with **{highest_count} tickets**")
            
            st.markdown(f"""
        ### 🎯 Priority Recommendations for Managing Ticket Volume and Triage Quality

        #### 1. Conduct a Granular Audit of "Service Request" Tickets

        **Action**: Randomly sample ~10–20% of recently closed “Service Request” tickets (e.g., from **{highest_month}**) for manual review.

        **Review Criteria**:
        - Was it actually a system outage or security event?
        - Were multiple users affected?
        - Did it impact business continuity?

        **Deliverable**: A risk report showing the % of misclassified tickets and recurring patterns.

        **Why it Matters**: Misclassification delays response to critical issues. Identifying high-impact tickets masked as low-priority helps avoid future operational or security risks.

        ---

        #### 2. Refine & Standardize Priority Definitions

        **Action**: Update your priority matrix (P1–P5, Service Request) to include:
        - Clear business impact thresholds
        - Practical examples (e.g., “P1 = Payroll system down for entire region”)
        - How to distinguish Service Requests vs. Incidents

        **Deliverable**: A documented and distributed "Ticket Priority Matrix."

        **Why it Matters**: Clear, consistent rules improve triage accuracy and reduce dependency on individual interpretation.

        ---

        #### 3. Targeted Training & QA Process for Triage Teams

        **Action**:
        - Deliver mandatory refresher training on ticket prioritization to all triage staff.
        - Implement QA audits on newly submitted tickets, focused on priority accuracy.
        - Use feedback loops and performance tracking.

        **Bonus**: Gamify with recognition for consistently accurate triage.

        **Deliverables**: Training attendance logs, triage audit dashboards, and KPIs for priority accuracy.

        **Why it Matters**: Enhances frontline accuracy and reduces escalations or SLA breaches due to misprioritization.

        ---

        #### 4. Enhance Self-Service & Automated Triage (Strategic)

        **Action**: Use AI or rules-based classifiers to suggest or assign ticket priorities automatically based on content and context (keywords, affected systems, user role).

        **Action**: Improve self-service portal for true low-priority tasks (e.g., password resets, onboarding requests) with embedded workflows.

        **Why it Matters**: Reduces triage load and improves resolution time for truly critical issues.

        ---

        #### 5. Link Prioritization to SLOs and Operational Outcomes

        **Action**: Establish and enforce SLOs tied to each priority (e.g., P1 = 4 hours, Service Request = 5 business days).

        **Action**: Monitor SLO adherence over time and review quarterly.

        **Why it Matters**: Aligns service performance with business expectations and improves accountability.
    
        """)
        else:
            st.markdown("**No significant surges detected** in ticket volume.")
            st.markdown("**Recommendation**: Maintain current staffing and triage protocols. Continue proactive monitoring of ticket distribution, especially in months like "
                        f"{highest_month}, which had the highest volume (**{highest_count} tickets**).")

    # Priority Distribution
    if 'priority' in df_filtered.columns:
        pri_counts = df_filtered['priority'].value_counts().reset_index()
        pri_counts.columns = ['Priority', 'Count']
        
        # Bar Chart
        fig = px.bar(
            pri_counts,
            x='Priority',
            y='Count',
            title="Tickets by Priority",
            color='Count',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            xaxis_title="Priority Level",
            yaxis_title="Ticket Count"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Most Frequent Priority
        dominant_priority = pri_counts.iloc[0]['Priority']
        dominant_count = pri_counts.iloc[0]['Count']
        
        st.markdown(f"**Most Used Priority**: `{dominant_priority}`")
        st.markdown(f"**Count**: `{dominant_count}`")

        st.markdown(f"""
        ### 🎯 Recommendation Based on `{dominant_priority}` Priority Dominance

        **1. Implement Granular Staffing Aligned with Peak Patterns**
        - **Action:** Adjust technician schedules to match ticket inflow — ensure agents are ready by **7:45 AM**, peaking through **9:00 AM**.
        - **Action:** Maintain higher staffing during **10:00–11:00 AM** and **2:00–4:00 PM**.
        - **Deliverable:** Updated technician roster aligned with high-volume hours.
        - **Why it Matters:** Aligning supply (staff) with demand (tickets marked as `{dominant_priority}`) directly improves response times and SLA compliance.

        **2. Strategically Deploy Senior Resources During Peaks**
        - **Action:** Assign senior staff like **Eddy Razlan Abdul Latiff** to critical hours: **8:00–11:00 AM**.
        - **Action:** Use senior staff for triage and quick resolution of `{dominant_priority}` issues.
        - **Deliverable:** Senior resource duty plan targeting priority `{dominant_priority}` tickets.
        - **Why it Matters:** Increases First Contact Resolution (FCR) and avoids escalation delays for `{dominant_priority}`-type tickets.

        **3. Proactive Readiness & "Shift Start" Protocols**
        - **Action:** Conduct a pre-shift briefing at **7:45 AM** for technicians starting at 8:00 AM.
        - **Action:** Include system checks and knowledge base refresh focused on `{dominant_priority}`-level incidents.
        - **Deliverable:** Formal "Peak Readiness" checklist for `{dominant_priority}`-ticket management.
        - **Why it Matters:** Reduces ramp-up time and ensures immediate effectiveness.

        **4. Future-Proofing: Automation & Metrics Integration**
        - **Action:** Analyze `{dominant_priority}` tickets for resolution time and customer satisfaction scores by hour.
        - **Action:** Automate responses for common `{dominant_priority}` issues using FAQs, bots, and self-service.
        - **Why it Matters:** Enhances both efficiency and customer satisfaction, especially during `{dominant_priority}` volume spikes.
        """)

    #---------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    summary_text = f"""
    Total Tickets: {len(df_filtered)}
    Avg Resolution Time: {df_filtered['resolution_time'].mean():.2f} hrs
    Unique Departments: {df_filtered['department'].nunique() if 'department' in df_filtered.columns else 'N/A'}
    SLA Compliance: {(df_filtered.get('resolution_time', 0) <= df_filtered.get('sla_hours', 9999)).mean() * 100:.2f}%
    Top Technician: {df_filtered['technician'].value_counts().idxmax() if 'technician' in df_filtered.columns else 'N/A'}
    Peak Hour: {df_filtered['created_time'].dt.hour.mode()[0] if 'created_time' in df_filtered.columns else 'N/A'}
    """

    return df_filtered

