import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np


def technician_performance(df_filtered):

    #1. Ticket assigned per agent
    with st.expander("Tickets Assigned per Agent"):
        if 'technician' in df_filtered.columns and 'request_id' in df_filtered.columns:

            # Count all technicians, no limit
            tech_counts = df_filtered['technician'].value_counts().reset_index()
            tech_counts.columns = ['Technician', 'count']

            # Bar chart
            fig = px.bar(
                tech_counts,
                x='Technician',
                y='count',
                color='count',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                xaxis_title="Technician",
                yaxis_title="Ticket Count",
                xaxis_tickangle=-45  # rotate labels if many technicians
            )
            st.plotly_chart(fig, use_container_width=True)

            # Get top technician for reference (optional)
            top_tech = tech_counts.iloc[0]
            top_name = top_tech['Technician']
            top_count = top_tech['count']

            # Box Plot: Distribution of Tickets per Technician by Group (if group column exists)
            if 'group' in df_filtered.columns:
                tickets_by_group = df_filtered.groupby(['group', 'technician'])['request_id'].nunique().reset_index()

                fig_box = px.box(
                    tickets_by_group,
                    x='group',
                    y='request_id',
                    points='all',
                    title='Distribution of Tickets per Technician by Group',
                    labels={'request_id': 'Ticket Count'},
                )
                fig_box.update_layout(xaxis_title='Group', yaxis_title='Tickets per Technician')
                st.plotly_chart(fig_box, use_container_width=True)

            with st.expander("## 📌 Insights, Recommendations & Explanations"):
                st.markdown("""
                ### **📈 Analysis**
                - Some technicians handle significantly more tickets than others.
                - Certain groups show a wide variation in technician workloads, indicating possible inefficiencies.
                - Imbalanced workload distribution may result in overworked agents (burnout risk) or underutilized staff (wasted cost).

                ### **✅ Recommendation**
                - **Dynamic Workload Balancing:** Use real-time workload data to distribute tickets more evenly. Consider open tickets and priority levels before assigning new ones.
                - **Cross-Training:** If one technician frequently gets specific request_types or categories, train others to reduce bottlenecks.

                ### **💡 Cost Reduction Insight**
                By balancing workloads:
                - Agents handle tickets faster, reducing open ticket time.
                - Burnout and turnover are minimized, reducing rehiring/training costs.
                - Underused staff become productive, maximizing payroll efficiency.
                        """)


    #2. Agent workload (open ticketes per agent)
    with st.expander("Agent Workload: Open Tickets Per Agent"):
        if 'technician' in df_filtered.columns and 'request_status' in df_filtered.columns:

            # Filter for open tickets only (not closed or resolved)
            open_tickets = df_filtered[~df_filtered['request_status'].astype(str).str.lower().isin(['closed', 'resolved'])].copy()

            # Normalize technician names and handle missing
            open_tickets['technician'] = open_tickets['technician'].fillna('Unassigned')

            # Vectorized ticket_state creation (robust to different representations)
            onhold_flag = open_tickets['on_hold_status'].astype(str).str.lower().str.strip().isin(['yes', 'true', '1'])
            pending_flag = open_tickets['pending_status'].astype(str).str.lower().str.strip().isin(['yes', 'true', '1'])

            open_tickets['ticket_state'] = np.where(onhold_flag, 'On-Hold',
                                            np.where(pending_flag, 'Pending', 'Active'))

            # Use pivot_table to aggregate counts and fill missing with 0
            agent_pivot = open_tickets.pivot_table(
                index='technician',
                columns='ticket_state',
                values='request_id',
                aggfunc='nunique',   # or 'count' depending on whether request_id is unique per ticket row
                fill_value=0
            )

            # Ensure expected columns exist
            states = ['Active', 'On-Hold', 'Pending']
            for s in states:
                if s not in agent_pivot.columns:
                    agent_pivot[s] = 0

            # Reorder columns consistently
            agent_pivot = agent_pivot[states]

            # Sort by Active tickets descending (safe because column exists)
            agent_pivot = agent_pivot.sort_values(by='Active', ascending=False)

            # Optional: show top N technicians for readability
            TOP_N = 40
            agent_pivot = agent_pivot.head(TOP_N).reset_index()

            # Plot stacked bar chart
            fig = px.bar(
                agent_pivot,
                x='technician',
                y=states,
                title='Open Tickets per Technician (Stacked by Status)',
                labels={'value': 'Number of Tickets', 'technician': 'Technician', 'variable': 'Ticket Status'},
                barmode='stack',
                height=500
            )
            fig.update_layout(xaxis_tickangle=-45, margin=dict(t=50, b=150))
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("📈 Analysis & 💡 Recommendations for Cost Reduction", expanded=True):
                st.markdown("""
                ### 📊 **Analysis**
                - This graph shows the current open workload of each technician.
                - The color stack differentiates tickets actively worked on (Active) from those that are on-hold or pending.
                - Technicians with many **Active** tickets may be overloaded; many **On-Hold/Pending** tickets often signal external blockers or slow follow-ups.

                ### 💡 **Recommendations**
                - **Queue Management Training** — ensure agents keep statuses up to date so dashboards reflect real work.
                - **Dynamic Load Balancing** — reassign tickets from overloaded technicians to underutilized ones.
                - **Automation**:
                - Automated reminders for tickets in an agent's queue beyond a threshold.
                - Auto-close stale tickets after a business rule (e.g., 7 days no response).

                ### 💰 **Cost Reduction Impact**
                - Faster resolution reduces SLA breaches and costly escalations.
                - Balanced queues reduce burnout and turnover, lowering hiring/training costs.
                        """)


    #3. Average Resolution Time Per Technician
    with st.expander("Average Resolution Time Per Technician"):
        if 'resolution_time' in df_filtered.columns and 'technician' in df_filtered.columns:
            st.subheader("🕒 Average Resolution Time Per Technician")

            avg_resolution = df_filtered.groupby('technician')['resolution_time'].mean().reset_index()
            avg_resolution = avg_resolution.sort_values(by='resolution_time', ascending=False)

            fig = px.bar(
                avg_resolution,
                x='technician',
                y='resolution_time',
                title='Average Resolution Time per Technician',
                labels={'technician': 'Technician', 'resolution_time': 'Avg. Resolution Time (hrs)'},
                text=avg_resolution['resolution_time'].round(2)
            )

            fig.update_traces(textposition='outside')
            fig.update_layout(
                xaxis_tickangle=-45,
                yaxis_title="Avg. Resolution Time (hrs)",
                xaxis_title="Technician"
            )

            st.plotly_chart(fig, use_container_width=True)

            with st.expander("📉 Analysis & Cost Reduction Insights: Average Resolution Time"):
                st.markdown("""
                **🔍 Analysis:**
                - The bar chart above shows the **average resolution time for each technician**.
                - Longer resolution times can indicate inefficiencies, either due to **lack of knowledge**, **complex categories**, or **poor internal processes**.
                - This metric helps to pinpoint which technicians may need **further training**, and who are already performing efficiently.

                **💡 Recommendation:**
                - **Skill-Based Training:** Identify technicians with the highest resolution times. Review their ticket categories to provide targeted training.
                - **Knowledge Base Improvement:** Ensure technicians have quick access to guides and past solutions to reduce time spent searching for answers.
                - **Mentorship Program:** Use data from technicians with consistently low resolution times to extract their approach and share it as best practices.
                - **Efficient Tools:** Investigate if certain teams/technicians lack automation or have outdated systems contributing to delays.

                **💰 Cost Reduction Impact:**
                - Shortening average resolution time reduces the number of labor hours per ticket, directly cutting support costs.
                - Improving agent productivity allows handling more tickets without increasing headcount.
                """)

    #4. Average Resolution Time Per Technician
    with st.expander("Average Resolution Time Per Technician"):
        if 'created_time' in df_filtered.columns:
            df_filtered['created_time'] = pd.to_datetime(df_filtered['created_time'], errors='coerce')
            df_filtered['day_of_week'] = df_filtered['created_time'].dt.day_name()
            df_filtered['hour'] = df_filtered['created_time'].dt.hour
            df_filtered['week'] = df_filtered['created_time'].dt.isocalendar().week
            df_filtered['month_name'] = df_filtered['created_time'].dt.strftime('%B')
            df_filtered['date'] = df_filtered['created_time'].dt.date
