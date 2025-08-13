import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np


def incident_trends(df_filtered):

    #1. Ticket assigned per agent
    with st.expander("📅 Ticket Trend Analysis: Daily, Weekly & Monthly"):

            with st.expander("📊 Daily Ticket Volume by Hour (Average over All Days)"):
                daily_avg = df_filtered.groupby(['hour']).size().reset_index(name='ticket_count')
                fig = px.line(daily_avg, x='hour', y='ticket_count',
                            title="Average Daily Ticket Volume by Hour (24H)",
                            markers=True)
                fig.update_layout(xaxis_title="Hour of Day", yaxis_title="Average Tickets")
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("""
        **Analysis**  
        Most tickets are submitted during specific peak hours of the day. These hours indicate the times when support demand is highest.

        **Recommendation**  
        Shift technician schedules to start slightly before peak hours to ensure rapid response times. Avoid scheduling breaks during these critical windows to reduce overtime and backlogs.

        **Impact on Yearly Cost**  
        Aligning support availability with actual demand can significantly reduce overstaffing during slow periods and reduce escalations or SLA breaches caused by delayed responses.
                    """)
                

            with st.expander("📊 Weekly Ticket Volume Trend"):
                weekly = df_filtered.groupby('week').size().reset_index(name='ticket_count')
                fig = px.bar(weekly, x='week', y='ticket_count',
                            title="Weekly Ticket Volume Over the Year")
                fig.update_layout(xaxis_title="Week Number", yaxis_title="Tickets")
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("📌 Analysis & Cost-Cutting Recommendation"):
                    st.markdown("""
                **Analysis**  
                Ticket volume may fluctuate throughout the weeks, often peaking after holidays, system changes, or project rollouts.

                **Recommendation**  
                Forecast demand using historical weekly patterns. During high-demand weeks, temporarily increase staffing or automate responses with pre-set templates or knowledge base deflection.

                **Impact on Yearly Cost**  
                Proactive resource planning avoids unnecessary overtime, contract hires, and improves SLA compliance, directly reducing operational support costs.
                            """)

            with st.expander("📊 Monthly Ticket Volume Trend"):
                monthly = df_filtered.groupby('month_name').size().reset_index(name='ticket_count')
                # Optional: sort months in calendar order
                month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                            'July', 'August', 'September', 'October', 'November', 'December']
                monthly['month_name'] = pd.Categorical(monthly['month_name'], categories=month_order, ordered=True)
                monthly = monthly.sort_values('month_name')
                fig = px.line(monthly, x='month_name', y='ticket_count',
                            title="Monthly Ticket Volume",
                            markers=True)
                fig.update_layout(xaxis_title="Month", yaxis_title="Tickets")
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("📌 Analysis & Cost-Cutting Recommendation"):
                    st.markdown("""
                **Analysis**  
                Monthly ticket trends reveal seasonal spikes and dips—such as increased IT issues during system rollouts or after fiscal-year changes.

                **Recommendation**  
                Plan large IT changes during months with historically lower ticket volumes. Introduce preventive maintenance and system audits during quiet months to minimize future peak load.

                **Impact on Yearly Cost**  
                Avoiding unplanned overtime and high-stress escalations during peak months reduces burnout, turnover, and external vendor costs.
                            """)
                    
            #Seaosonal or Recurring Patterns in Ticket Volume
            with st.expander("Seasonal or Recurring Patterns in Ticket Volume 🗓️"):
                if 'created_time' in df_filtered.columns:
                    # Extract month and year
                    df_filtered['Year'] = df_filtered['created_time'].dt.year
                    df_filtered['Month'] = df_filtered['created_time'].dt.month

                    # Group by Year-Month
                    monthly_counts = df_filtered.groupby(['Year', 'Month']).size().reset_index(name='Ticket Count')

                    # Pivot for multi-line chart (Month on X, Year as separate lines)
                    monthly_pivot = monthly_counts.pivot(index='Month', columns='Year', values='Ticket Count').reset_index()

                    # Create line chart
                    fig = px.line(
                        monthly_counts,
                        x='Month',
                        y='Ticket Count',
                        color='Year',
                        markers=True,
                        title="Monthly Ticket Volume by Year",
                    )
                    fig.update_layout(
                        xaxis_title="Month",
                        yaxis_title="Ticket Count",
                        xaxis=dict(tickmode='array', tickvals=list(range(1, 13)), ticktext=[
                            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
                        ])
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Identify peak recurring month
                    avg_monthly = monthly_counts.groupby('Month')['Ticket Count'].mean().reset_index()
                    peak_month_num = avg_monthly.loc[avg_monthly['Ticket Count'].idxmax(), 'Month']
                    peak_month_name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][peak_month_num - 1]

                    st.markdown(f"**Highest Average Ticket Volume Month:** {peak_month_name}")

                    # Analysis, Recommendation, and Explanation
                    st.markdown(f"""
                    **Analysis**:  
                    This visualization compares monthly ticket volumes across multiple years, helping identify predictable patterns and seasonal spikes. For instance, if {peak_month_name} consistently records the highest ticket count, it signals a recurring peak period that may strain support resources if not anticipated. Recognizing these patterns allows you to forecast workload more accurately, proactively adjust staffing, and prepare resources ahead of demand surges. Conversely, identifying historically low-volume months helps pinpoint periods where resources can be reallocated to proactive initiatives like system upgrades, preventive maintenance, or team training.

                    **Recommendation**:  
                    1. **Align Staffing with Seasonal Demand**: Increase agent availability and limit vacation leave during high-volume months like {peak_month_name}. Conversely, scale back staffing during low-volume periods and reassign agents to training or process improvement.  
                    2. **Resolve Recurring Issues Before They Spike**: Investigate ticket categories that consistently rise in specific months and address the root causes permanently. This eliminates avoidable ticket volumes in future cycles.  
                    3. **Deploy Pre-emptive Self-Service Resources**: Before the anticipated peak month, release targeted FAQs, knowledge base articles, or customer email campaigns for the most common seasonal issues. This can reduce ticket inflow before it happens.  
                    4. **Budget and Plan Strategically**: Use historical trends to predict resource requirements and allocate budget efficiently. This minimizes surprise costs and supports a stable support operation year-round.

                    **Explanation**:  
                    By anticipating ticket volume peaks and troughs, your team can prevent costly overtime, reduce SLA breaches, and maintain a consistent customer experience. Addressing recurring seasonal issues before they arise removes an entire category of predictable workload, directly lowering yearly operational costs. Pre-emptive self-service not only deflects repetitive tickets but also frees agents to focus on complex, revenue-impacting cases. Combining predictive staffing, problem elimination, and proactive knowledge sharing turns your support function into a lean, well-prepared operation that delivers high service quality at a reduced cost per ticket.
                    """)