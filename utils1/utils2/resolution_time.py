import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np



def resolution_time(df_filtered):

    # 1. Ticket Resolution Performance
    with st.expander("⏱️ Ticket Resolution Performance"):

        df_filtered = df_filtered.copy()

        if 'resolution_time' in df_filtered.columns and 'fcr' in df_filtered.columns:
            # Ensure numeric resolution_time in hours
            if not pd.api.types.is_numeric_dtype(df_filtered['resolution_time']):
                try:
                    df_filtered['resolution_time'] = pd.to_timedelta(df_filtered['resolution_time'], errors='coerce').dt.total_seconds() / 3600
                except Exception as e:
                    st.error(f"Could not convert resolution_time: {e}")

            # Drop rows with no resolution time
            df_filtered = df_filtered.dropna(subset=['resolution_time'])

            if not df_filtered.empty:
                # Proceed with plotting
                fig_ttr = px.histogram(
                    df_filtered,
                    x='resolution_time',
                    nbins=30,
                    marginal="box",
                    title="Distribution of Resolution Time",
                    color_discrete_sequence=['#636EFA']
                )
                fig_ttr.update_layout(
                    xaxis_title="Resolution Time (Hours)",
                    yaxis_title="Ticket Count"
                )
                st.plotly_chart(fig_ttr, use_container_width=True)

            avg_ttr = df_filtered['resolution_time'].mean()
            fcr_rate = df_filtered['fcr'].mean() * 100

            with st.expander("## 📌 Insights, Recommendations & Explanations"):
                st.markdown(f""" 
                    ### 🧠 Analysis      
                    - **Average resolution time:** {avg_ttr:.2f} hours  
                    - **FCR rate:** {fcr_rate:.2f}%

                    {"- High resolution time indicates bottlenecks." if avg_ttr > 48 else "- Resolution time is within acceptable range."}
                    {"- FCR below 50% is a red flag. Investigate training and routing." if fcr_rate < 50 else "- FCR is healthy and contributes to user satisfaction."}
                    """)

                st.markdown("### ✅ Recommendation")
                st.markdown("""
                    - Use templates and checklists to reduce resolution time.
                    - Improve ticket routing using intelligent classification.
                    - Train agents in low-FCR areas and automate repetitive resolutions.
                    """)

                st.markdown("### 💰 Cost Impact")
                st.markdown("""
                    - Better FCR = fewer touchpoints per ticket.
                    - Faster resolution = fewer resources consumed = reduced operational cost.
                    """)
                
    #2. Average resolution time by fcr & non-fcr :
    with st.expander("Average Resolution Time"):
        if 'fcr' in df_filtered.columns and 'resolution_time' in df_filtered.columns:
            
            
            # Bar Chart: Average Resolution Time for FCR vs Non-FCR
            avg_res_time_fcr = df_filtered.groupby('fcr')['resolution_time'].mean().reset_index()
            avg_res_time_fcr['fcr'] = avg_res_time_fcr['fcr'].replace({True: 'FCR: Resolved on First Contact', False: 'Non-FCR: Multiple Contacts'})

            fig = px.bar(
                avg_res_time_fcr,
                x='fcr',
                y='resolution_time',
                text='resolution_time',
                color='fcr',
                title='Average Resolution Time: FCR vs Non-FCR',
                labels={'fcr': 'FCR Status', 'resolution_time': 'Avg Resolution Time (hrs)'},
            )
            fig.update_traces(texttemplate='%{text:.2f} hrs', textposition='outside')
            fig.update_layout(
                xaxis_title="FCR Status",
                yaxis_title="Average Resolution Time (hours)",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

            # Expander for Insights and Recommendations
            with st.expander("🧠 Insights, Recommendations & Cost-Saving Explanation"):
                st.markdown("""
            ### 📊 **Analysis**  
            From the chart above, we observe that tickets resolved on **first contact (FCR)** consistently have **lower average resolution times** compared to those requiring multiple follow-ups. This suggests that tickets not resolved on the first attempt tend to **consume significantly more technician hours**.

            Furthermore, the labor and processing cost per ticket grows when resolution is delayed or involves multiple handovers.

            ---

            ### 🛠️ **Recommendations**  

            **1. Increase FCR Rate:**  
            Invest in agent training focused on common ticket types. Use historical data to create internal playbooks, checklists, or AI-assisted prompts to guide agents to faster resolution.

            **2. Build a Smarter Knowledge Base:**  
            Integrate patterns from past tickets to build an internal system of FAQs, resolutions, and scripts that technicians can follow. Aim for making these tools accessible at the first point of contact.

            **3. Use Ticket Triage Automation:**  
            Auto-assign certain ticket categories to specialists or groups with the shortest historical resolution time. Smart routing reduces delay from misassignments.

            ---

            ### 💸 **Cost Reduction Impact**  
            - A reduction in average resolution time per ticket directly lowers the hourly wage burden across support teams.
            - Fewer follow-up interactions mean fewer communication costs, system loads, and time spent on non-value-adding back-and-forths.
            - Improving FCR by just 10–15% can yield substantial cost savings annually when scaled across thousands of tickets.

            This kind of operational optimization aligns with scalable cost reduction without sacrificing customer experience.
                    """)

    #3. SLA adherence (percentage of tickets resolved within defined SLAs).
    with st.expander("SLA adherence (percentage of tickets resolved within defined SLAs)."):
        if all(col in df_filtered.columns for col in ['first_response_overdue_status', 'request_mode', 'priority', 'vip_user']):
            
            st.markdown("## ⏱️ SLA Adherence & Open Ticket Risk by Request Mode")
            
            # Prepare data
            overdue_counts = df_filtered[df_filtered['first_response_overdue_status'] == 'Yes'].groupby(
                ['request_mode', 'priority', 'vip_user']
            ).size().reset_index(name='Overdue Count')
            
            total_counts = df_filtered.groupby(['request_mode', 'priority', 'vip_user']).size().reset_index(name='Total Count')
            
            merged_df = pd.merge(total_counts, overdue_counts, on=['request_mode', 'priority', 'vip_user'], how='left')
            merged_df['Overdue Count'] = merged_df['Overdue Count'].fillna(0)
            merged_df['Overdue Rate (%)'] = round((merged_df['Overdue Count'] / merged_df['Total Count']) * 100, 2)

            # Visualization
            fig = px.bar(
                merged_df,
                x='request_mode',
                y='Overdue Rate (%)',
                color='priority',
                facet_col='vip_user',
                barmode='group',
                title='First Response SLA Breaches by Request Mode, Priority & VIP Status'
            )
            fig.update_layout(
                xaxis_title='Request Mode',
                yaxis_title='Overdue Response Rate (%)',
                legend_title='Priority Level'
            )
            
            st.plotly_chart(fig, use_container_width=True)

            # Analysis & Recommendation
            with st.expander("📌 Analysis & Recommendations: Reducing SLA Breaches and Controlling Cost"):
                st.markdown("""
                ### 🔍 Analysis
                This graph shows the percentage of tickets that missed the **first response SLA** grouped by `request_mode`, `priority`, and `vip_user` status.
                
                - A high **overdue rate** indicates delays in responding to tickets.
                - VIP users with high-priority tickets should **never** be overdue — this can lead to dissatisfaction and potential client churn.
                - Certain channels (like Phone or Email) might show higher SLA violations, revealing staffing or triage inefficiencies.

                ### 💡 Recommendations
                1. **Prioritize VIP and High Priority Cases**  
                Ensure the support system flags these tickets for immediate attention. Assign senior agents or fast-track queues to reduce delay.

                2. **Optimize Staffing Based on Patterns**  
                If most overdue tickets originate from a specific time range (you can analyze this via `created_time`), consider reallocating or increasing staff during those periods.

                3. **Automate Acknowledgments**  
                Automatically acknowledge tickets when received, especially via Email, to improve perception and buy time for response.

                4. **Real-Time SLA Dashboards**  
                Set up a live monitor (like the one here) in your ops center to highlight tickets that are nearing their SLA limit. This enables proactive reallocation of resources.

                ### 💰 Cost-Saving Impact
                Staying within SLA targets reduces:
                - Penalties or contract violations
                - Escalation costs (involving senior personnel)
                - Customer dissatisfaction and churn risk  
                
                Every overdue ticket avoided improves efficiency and reduces operational risk.
                """)

        else:
            st.warning("Required columns for SLA breach analysis not found in the dataset.")

  
        if (
            'request_status' in df_filtered.columns
            and 'on_hold_status' in df_filtered.columns
            and 'on_hold_duration' in df_filtered.columns
        ):
            st.markdown("## 🧹 Eliminate Backlog & Prevent Accumulation")

            with st.expander("📉 View Backlog Insights Chart", expanded=True):
                unresolved = df_filtered[
                    ~df_filtered['request_status'].str.lower().isin(['closed', 'resolved'])
                ]
                
                fig = px.box(
                    unresolved,
                    x='on_hold_status',
                    y='on_hold_duration',
                    title='On Hold Duration for Unresolved Tickets by Onhold Status',
                    labels={'onhold_status': 'On Hold Status', 'on_hold_duration': 'On Hold Duration (Days)'}
                )
                fig.update_layout(
                    xaxis_title='On Hold Status (Yes / No)',
                    yaxis_title='Duration on Hold (Days)',
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)

            with st.expander("## 📌 Insights, Recommendations & Explanations"):
                st.markdown("""
                ### 🔍 **Analysis**
                - The box plot shows how long unresolved tickets are being held, based on their `onhold_status`.
                - Long `on_hold_duration` values, especially where `onhold_status = yes`, suggest tickets are stuck in internal bottlenecks.
                - Many unresolved tickets with `onhold_status = no` but still high durations might indicate lack of follow-up or improper routing.

                ### ✅ **Recommendations**
                1. **Automate 'Waiting on Requester' Tickets**:
                    - If `pending_status = true` and `on_hold_duration > 3 days`, auto-email reminders.
                    - After 2 reminders with no response, close ticket automatically with a note.

                2. **Fix Internal Delays**:
                    - Investigate tickets where `onhold_status = yes` and `on_hold_duration` is very high.
                    - Cross-check with `group` column to identify where handoffs are stuck.
                    - Consider allocating more resources or refining escalation paths.

                3. **Improve Ticket Routing**:
                    - Tickets with null or empty `technician` or `group` values might be misrouted or ignored.
                    - Analyze patterns based on `category`, `subcategory`, and `subject` to fine-tune auto-routing logic.

                ### 💰 **Cost Reduction Impact**
                - Backlogs create hidden costs: duplicate follow-ups, ticket reopenings, and frustrated users.
                - By closing stale tickets and optimizing routing, agents can focus on real, active issues—resulting in fewer total tickets and more efficient staffing.
                """)