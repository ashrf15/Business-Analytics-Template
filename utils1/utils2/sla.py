import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np


def sla(df_filtered):

    # 1. SLA Performance Metrics
    with st.expander("SLA Performance Metrics"):
            if 'first_response_overdue_status' in df_filtered.columns and 'overdue_status' in df_filtered.columns:
                # Calculate overall SLA adherence
                sla_met = df_filtered[
                    (df_filtered['first_response_overdue_status'] == 'No') &
                    (df_filtered['overdue_status'] == 'No')
                ]
                sla_adherence = (len(sla_met) / len(df_filtered)) * 100 if len(df_filtered) > 0 else 0

                # SLA adherence by priority and request_type
                sla_df = df_filtered.copy()
                sla_df['SLA_Met'] = np.where(
                    (sla_df['first_response_overdue_status'] == 'No') &
                    (sla_df['overdue_status'] == 'No'),
                    'Yes', 'No'
                )
                adherence_group = sla_df.groupby(['priority', 'request_type', 'SLA_Met']).size().reset_index(name='Count')

                fig = px.bar(
                    adherence_group,
                    x='priority',
                    y='Count',
                    color='SLA_Met',
                    barmode='stack',
                    facet_col='request_type',
                    title=f"SLA Adherence by Priority and Request Type (Overall SLA Adherence: {sla_adherence:.1f}%)",
                    color_discrete_map={'Yes': 'steelblue', 'No': 'lightcoral'}
                )
                fig.update_layout(xaxis_title="Priority", yaxis_title="Ticket Count")
                st.plotly_chart(fig, use_container_width=True)

                # Insights
                st.markdown(f"**Overall SLA Adherence:** {sla_adherence:.1f}%")

                with st.expander("📊 Analysis, Recommendation & Cost Reduction Explanation"):
                    st.markdown(f"""
        **Analysis:**  
        This chart shows your SLA adherence rates, broken down by priority and request type. The overall SLA adherence is **{sla_adherence:.1f}%**, which represents the percentage of tickets resolved within the agreed service times. High adherence means customers are getting timely responses, while low adherence—especially in High priority tickets—indicates risks of dissatisfaction and costly escalations.  
        By looking at the colored segments, you can quickly see where SLA breaches are concentrated, allowing you to focus on the most problematic areas.

        **Recommendation:**  
        1. **Prioritize High-Impact SLAs** – Ensure High priority tickets meet their SLAs consistently to prevent disruptions.  
        2. **Reward SLA Success** – Recognize and incentivize teams or technicians who consistently meet SLA targets, encouraging efficient work habits.  
        3. **Optimize Resolution Workflows** – Identify bottlenecks for SLA-missed tickets and introduce automation, faster approval paths, or improved knowledge base resources.

        **Cost Reduction Explanation:**  
        Meeting SLAs—especially for critical tickets—prevents business disruptions that often require costly emergency interventions. By improving workflows and rewarding high adherence, you reduce the hidden costs of repeated customer contact, overtime, and escalations. This proactive approach also stabilizes operational performance, lowering the average cost per ticket over the year.
        """)

    # 2. SLA Breaches and Reasons
    with st.expander("SLA Breaches and Reasons"):
        if 'first_response_overdue_status' in df_filtered.columns and 'overdue_status' in df_filtered.columns:
                # Filter for breached tickets
                breached_df = df_filtered[
                    (df_filtered['first_response_overdue_status'] == 'Yes') |
                    (df_filtered['overdue_status'] == 'Yes')
                ]

        if not breached_df.empty:
                    # Count breaches by category
                    breach_category = breached_df['category'].value_counts().reset_index()
                    breach_category.columns = ['Category', 'Count']

                    fig = px.bar(
                        breach_category,
                        x='Category',
                        y='Count',
                        color='Count',
                        color_continuous_scale='Reds',
                        title="SLA Breaches by Category"
                    )
                    fig.update_layout(xaxis_title="Category", yaxis_title="Number of Breaches")
                    st.plotly_chart(fig, use_container_width=True)

                    with st.expander("📊 Analysis, Recommendation & Cost Reduction Explanation"):
                        st.markdown(f"""
        **Analysis:**  
        This chart highlights which categories are most frequently responsible for SLA breaches. These breaches indicate that tickets in these categories are not being resolved within the agreed timeframe.  
        Frequent breaches—especially in high-impact categories—often result in higher operational costs due to repeated work, escalations, and customer dissatisfaction. Identifying these categories provides a clear starting point for targeted improvements.

        **Recommendation:**  
        1. **Proactive Monitoring** – Track open tickets nearing their SLA deadlines in real-time and reassign or escalate before breaches occur.  
        2. **Targeted Training** – Provide additional resources or training to agents working on high-breach categories to help them resolve tickets faster.  
        3. **Automate Alerts** – Set up automated notifications for tickets close to their SLA due time to ensure they are prioritized.

        **Cost Reduction Explanation:**  
        Preventing SLA breaches minimizes expensive escalations and reduces the labor hours spent on managing repeated or reopened tickets. Real-time monitoring and automated alerts cost little to implement but can significantly improve SLA adherence. By resolving root causes through targeted training and workflow optimization, you save on long-term labor costs and improve customer retention, further reducing the yearly operational cost.
        """)
