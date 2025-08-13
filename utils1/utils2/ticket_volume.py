import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np



def ticket_volume(df_filtered):

    # 1. Ticket Type Breakdown
    with st.expander("🎫 Total Number of Tickets Opened"):
    
        #by request type
        with st.expander("Tickets Opened by Request Type"):
            if 'request_type' in df_filtered.columns:
                            type_counts = df_filtered['request_type'].value_counts().reset_index()
                            type_counts.columns = ['Request Type', 'Count']

                            fig = px.bar(
                                type_counts,
                                x='Request Type',
                                y='Count',
                                title="Ticket Type Breakdown",
                                color='Count',
                                color_continuous_scale='Blues'
                            )
                            fig.update_layout(xaxis_title="Request Type", yaxis_title="Number of Tickets")
                            st.plotly_chart(fig, use_container_width=True)

                            total_tickets = df_filtered.shape[0]
                            top_ticket_type = type_counts.iloc[0]['Request Type']
                            top_ticket_count = type_counts.iloc[0]['Count']
                            top_ticket_pct = (top_ticket_count / total_tickets) * 100

                            with st.expander("## 📌 Insights, Recommendations & Explanations"):
                                st.markdown("---")
                                st.markdown(f"""
                                    ### 🔍 Analysis
                                    - **`{top_ticket_type}`** accounts for **{top_ticket_pct:.2f}%** of {total_tickets} tickets — indicating a repetitive, systemic issue.
                                    - This type likely stems from user misunderstanding, infrastructure issues, or insufficient self-help tools.

                                    ### ✅ Recommendation
                                    - Conduct root cause analysis (RCA) for `{top_ticket_type}`.
                                    - Automate common resolutions, improve knowledge base access, and investigate system gaps.
                                    - Aim to reduce volume in this category by 20–30% through long-term fixes.

                                    ### 💡 Explanation
                                    - Frequent tickets in this category cost more to manage and strain agent resources.
                                    - Addressing the root cause boosts efficiency, cuts costs, and improves user experience.
                                    """)
            
        #by hour of day
        with st.expander("Tickets Opened by Hour of Day (24H)"):
            # Created Hour
            if 'created_time' in df_filtered.columns:
                    df_filtered['created_hour'] = df_filtered['created_time'].dt.hour
                    hour_counts = df_filtered['created_hour'].value_counts().sort_index().reset_index()
                    hour_counts.columns = ['Hour', 'Count']
                    fig = px.bar(hour_counts, x='Hour', y='Count', title="Tickets by Hour of Day", color='Count', color_continuous_scale='Blues')
                    fig.update_layout(xaxis_title="Hour of Day", yaxis_title="Ticket Count")
                    st.plotly_chart(fig, use_container_width=True)
                    peak = hour_counts.iloc[hour_counts['Count'].idxmax()]['Hour']
                    st.markdown(f"**Peak Support Hour**: {peak}:00")
                    st.markdown("""
                **Analysis**:  
                This chart visualizes the exact distribution of ticket submissions throughout the day, allowing us to identify patterns in customer behavior. The data clearly reveals which hours see the heaviest ticket inflow and which periods experience lower activity. This is critical for understanding the natural rhythm of your support workload. High peaks can indicate a mismatch between customer needs and available support resources, often leading to slower responses, missed SLAs, and customer dissatisfaction. On the other hand, extended low-activity periods may suggest potential opportunities to reallocate resources or assign agents to other productive tasks, such as proactive customer outreach or preventive maintenance work. Recognizing these patterns provides the foundation for improving service delivery efficiency while controlling operational costs.

                **Recommendation**:  
                1. **Optimize Staffing Levels**: Allocate more agents during high-demand hours to ensure prompt responses and avoid backlog buildup. During low-demand periods, reduce active staffing or assign agents to value-adding activities, such as training or knowledge base improvements.  
                2. **Implement Targeted Self-Service Options**: Analyze the most common ticket categories during peak times and create simple, accessible self-help content like step-by-step articles, FAQs, or AI-driven chatbots to handle repetitive issues without manual intervention.  
                3. **Use Predictive Scheduling**: Incorporate historical ticket volume data into workforce planning so that staffing levels are forecasted and adjusted automatically based on expected demand patterns, preventing both overstaffing and understaffing.  

                **Explanation**:  
                Aligning workforce availability with actual demand is one of the most effective ways to reduce yearly operating costs without compromising service quality. By ensuring that the right number of agents are available during peak hours, you lower the risk of SLA breaches, improve first-contact resolution rates, and prevent repeat interactions — all of which reduce labor hours per ticket. Similarly, avoiding overstaffing during low-activity periods eliminates unnecessary payroll expenses while keeping your team focused on tasks that bring long-term value. Furthermore, self-service tools for recurring issues during high-demand periods can significantly reduce ticket volumes, freeing agents to focus on complex, high-priority cases. Predictive scheduling, powered by historical data, ensures these improvements become part of a sustained, data-driven operational model. The result is a leaner, more agile support operation that directly reduces the cost per ticket and boosts customer satisfaction.
                """)

            #by department
            with st.expander("Tickets Opened by Department"):
                    st.subheader("Top 10 Departments")
                    if 'department' in df_filtered.columns:
                        dept_counts = df_filtered['department'].value_counts().head(10).reset_index()
                        dept_counts.columns = ['Department', 'count']

                        fig = px.bar(
                            dept_counts,
                            x='Department',
                            y='count',
                            title="Top 10 Departments",
                            color='count',
                            color_continuous_scale='Blues'
                        )
                        fig.update_layout(xaxis_title="Department", yaxis_title="Ticket Count")
                        st.plotly_chart(fig, use_container_width=True)

                        # Get slowest resolution department
                        slow_dept = (
                            df_filtered.groupby('department')['resolution_time']
                            .mean()
                            .reset_index()
                            .sort_values('resolution_time', ascending=False)
                            .iloc[0]
                        )
                        slowest_dept_name = slow_dept['department']
                        slowest_avg_time = slow_dept['resolution_time']

                        st.markdown(f" ##### **Slowest Resolution Dept**: {slowest_dept_name} with an average of {slowest_avg_time:.2f} hrs.")
                        st.markdown(f"""
                **Analysis**:
                1.  The chart identifies the departments that generate the most tickets, highlighting where your support demand is concentrated. This is crucial for understanding the overall workload distribution across the organization.
                2.  A critical finding is that while **"{slowest_dept_name}"** may not generate the highest volume of tickets, it has the slowest average resolution time. This points to a significant operational bottleneck, as the prolonged time to close tickets in this department can have costly downstream effects.

                **Recommendation**:
                1.  **Conduct a Root Cause Analysis**: Perform a deep dive into the tickets handled by **"{slowest_dept_name}"** to identify the specific reasons for the delays. This includes analyzing the **`category`** and **`subcategory`** of these tickets to determine if they are inherently complex or if there are recurring issues.
                2.  **Audit the Workflow**: Map the entire resolution process for tickets in this department, from ticket creation to closure. Identify every step, handoff, and approval point to pinpoint exactly where the time is being lost.
                3.  **Implement Targeted Automation**: Based on the audit, look for opportunities to automate parts of the workflow. For example, use templates for common responses or automate notifications for approvals to other departments.
                4.  **Provide Skill-Based Training**: If the analysis reveals that agents lack the necessary skills for certain types of tickets, provide focused training to enhance their expertise and confidence, enabling faster resolutions.
                5.  **Improve Cross-Departmental Collaboration**: If delays are caused by dependencies on other teams, establish clear Service Level Agreements (SLAs) or communication protocols to streamline the handoff process.

                **Explanation**:
                1.  By addressing the underlying issues in **"{slowest_dept_name}"**, you can achieve significant yearly cost reductions. An elongated resolution time directly increases the labor costs associated with each ticket because it ties up agent resources for longer periods.
                2.  Fixing this bottleneck prevents customer dissatisfaction, which can lead to costly ticket escalations or customer churn. A more efficient resolution process means happier requesters and fewer follow-up inquiries.
                3.  This proactive approach shifts the focus from managing a backlog to preventing it. By optimizing the workflow, you not only reduce the cost per ticket in this department but also create a more resilient and efficient support operation for the entire company.
                """)

    # 2. Tickets Closed
    with st.expander("📫 Tickets Closed"):
            
        #Closure vs Opening Rate
        with st.expander("Closure vs Opening Rate"):
            if 'request_status' in df_filtered.columns and 'created_time' in df_filtered.columns:

                    # Ensure created_time is datetime
                    df_filtered['created_time'] = pd.to_datetime(df_filtered['created_time'], errors='coerce')

                    # Extract month-year for grouping
                    df_filtered['month_year'] = df_filtered['created_time'].dt.to_period('M').astype(str)

                    # Tickets Opened per Month
                    opened_counts = df_filtered.groupby('month_year').size().reset_index(name='opened')

                    # Tickets Closed per Month
                    closed_counts = df_filtered[df_filtered['request_status'].str.lower() == 'closed'] \
                        .groupby('month_year').size().reset_index(name='closed')

                    # Merge opened & closed data
                    monthly_trend = pd.merge(opened_counts, closed_counts, on='month_year', how='outer').fillna(0)

                    # Sort by date
                    monthly_trend['month_year'] = pd.to_datetime(monthly_trend['month_year'], format='%Y-%m')
                    monthly_trend = monthly_trend.sort_values('month_year')

                    # Plot line chart
                    fig = px.line(
                        monthly_trend,
                        x='month_year',
                        y=['opened', 'closed'],
                        markers=True,
                        title="Tickets Opened vs. Tickets Closed (Monthly)",
                        labels={'value': 'Number of Tickets', 'month_year': 'Month', 'variable': 'Ticket Type'}
                    )
                    fig.update_layout(xaxis_tickformat='%b %Y')
                    st.plotly_chart(fig, use_container_width=True)

                    # Analysis & Recommendations in Expander
                    with st.expander("📈 Analysis & 💡 Recommendations for Yearly Cost Reduction", expanded=True):
                        st.markdown("""
                        ### 📊 **Analysis**
                        - The chart compares the number of tickets opened and closed each month.
                        - When the **Closed** line consistently falls below the **Opened** line, it signals a growing backlog.
                        - Sustained backlogs increase resolution delays, leading to SLA breaches, lower customer satisfaction, and higher long-term costs.
                        - A close alignment—or even more tickets closed than opened—indicates a healthy, well-managed queue.

                        ### 💡 **Recommendations**
                        1. **Balance Ticket Inflow & Outflow**  
                        - Match team capacity with the volume of new requests.  
                        - If ticket inflow spikes, implement short-term measures like overtime, reallocation of staff, or faster escalation paths.

                        2. **Prevent Rework with Quality Closures**  
                        - Review tickets that are reopened or have low First Contact Resolution (FCR).  
                        - Provide technicians with targeted guidance to ensure tickets are fully resolved the first time.

                        3. **Automate Simple Closures**  
                        - Analyze closure reasons (e.g., "Duplicate" or "Information Provided").  
                        - Automate these with scripts or bots to reduce manual workload.

                        ### 💰 **Cost Reduction Impact**
                        - Preventing backlog growth reduces SLA penalties and prevents customer churn.
                        - High-quality closures minimize rework, freeing technician time for new issues.
                        - Automation of simple closures allows the same team size to handle more tickets annually without increasing payroll.
                                """)
                        
        #Closure Rate per Agent
        with st.expander("Closure Rate per Agent"):
            if all(col in df_filtered.columns for col in ['technician', 'completed_time', 'created_time']):
                    
                    # Convert date columns
                    df_filtered['completed_time'] = pd.to_datetime(df_filtered['completed_time'], errors='coerce')
                    df_filtered['created_time'] = pd.to_datetime(df_filtered['created_time'], errors='coerce')
                    
                    # Filter out rows without technician info
                    df_agents = df_filtered.dropna(subset=['technician'])
                    
                    # Calculate closure rate per technician
                    # Closure Rate = tickets closed / tickets assigned
                    tickets_assigned = df_agents.groupby('technician').size().reset_index(name='Tickets Assigned')
                    tickets_closed = df_agents.dropna(subset=['completed_time']).groupby('technician').size().reset_index(name='Tickets Closed')
                    
                    closure_rate_df = pd.merge(tickets_assigned, tickets_closed, on='technician', how='left')
                    closure_rate_df['Tickets Closed'] = closure_rate_df['Tickets Closed'].fillna(0)
                    closure_rate_df['Closure Rate (%)'] = (closure_rate_df['Tickets Closed'] / closure_rate_df['Tickets Assigned']) * 100
                    
                    # Sort by closure rate
                    closure_rate_df = closure_rate_df.sort_values('Closure Rate (%)', ascending=False)
                    
                    # Plot bar chart
                    fig = px.bar(
                        closure_rate_df,
                        x='technician',
                        y='Closure Rate (%)',
                        color='Closure Rate (%)',
                        color_continuous_scale='Blues',
                        title="Closure Rate per Technician",
                        labels={'technician': 'Technician', 'Closure Rate (%)': 'Closure Rate (%)'}
                    )
                    fig.update_layout(xaxis_title="Technician", yaxis_title="Closure Rate (%)")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Expander for analysis & recommendations
                    with st.expander("📊 Analysis, Recommendations & Cost-Saving Insights"):
                        st.markdown("""
                        ### **Analysis**
                        - This chart shows the percentage of tickets each technician successfully closed.
                        - Higher closure rates indicate efficient workload management and strong resolution capability.
                        - Consistently low closure rates may point to:
                        - Bottlenecks (too many open tickets for one technician)
                        - Lack of skills/training in certain ticket categories
                        - Poor workload distribution

                        ### **Recommendations**
                        1. **Targeted Support for Low Performers**  
                        - Pair low-closure technicians with mentors.
                        - Provide skill-based training on the types of tickets they struggle with.

                        2. **Workload Balancing**  
                        - Distribute tickets more evenly to avoid overloading certain technicians.
                        - Use real-time dashboards to reassign tickets if one technician falls behind.

                        3. **Integrate Quality Metrics**  
                        - Combine closure rate tracking with reopened ticket analysis to ensure quality isn't sacrificed for speed.

                        4. **Recognize High Performers**  
                        - Reward consistently high closure rates combined with low reopened rates to motivate best practices.

                        ### **Why This Reduces Yearly Costs**
                        - Improving closure rates reduces backlog, avoiding SLA breaches and escalation costs.
                        - Balanced workloads prevent burnout and turnover, which are expensive to replace.
                        - Higher quality closures lower the need for rework, freeing up capacity for new issues.
                        """)

    # 4. Tickets currently open
    with st.expander("📭 Tickets Currently Open"):

        #Age distribution of open tickets
        with st.expander("📅 Age Distribution of Open Tickets"):
            if 'request_status' in df_filtered.columns and 'created_time' in df_filtered.columns:
                    df_filtered['request_status'] = df_filtered['request_status'].astype(str).str.lower().str.strip()
                    df_open = df_filtered[df_filtered['request_status'] == 'open'].copy()
                    df_open['created_time'] = pd.to_datetime(df_open['created_time'], errors='coerce')
                    df_open = df_open[df_open['created_time'].notna()]
                    df_open['ticket_age_days'] = (datetime.now() - df_open['created_time']).dt.days

                    bins = [-1, 0, 3, 7, 10000]
                    labels = ['<24 hours', '1–3 days', '3–7 days', '>1 week']
                    df_open['age_category'] = pd.cut(df_open['ticket_age_days'], bins=bins, labels=labels)
                    age_counts = df_open['age_category'].value_counts().sort_index()

                    fig = px.bar(
                        x=age_counts.index,
                        y=age_counts.values,
                        labels={'x': 'Ticket Age Category', 'y': 'Open Ticket Count'},
                        title='Age Distribution of Currently Open Tickets'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    with st.expander("## 📌 Insights, Recommendations & Explanations"):
                        st.markdown(f"""
                            ### 🧠 Analysis
                            - **Total open tickets:** {len(df_open)}
                            - Majority in **'{age_counts.idxmax()}'** category.
                            - **{age_counts['>1 week'] if '>1 week' in age_counts else 0} tickets** over 7 days old — possible SLA risk.

                            ### ✅ Recommendations
                            - Escalate tickets older than 7 days.
                            - Add automated reminders at 3 and 7-day marks.
                            - Optimize workflows to prevent ticket aging.

                            ### 💰 Cost Impact
                            - Reduces SLA violations and churn.
                            - Lowers effort spent re-processing stale tickets.
                            """)
                        
        #idk
        with st.expander("📂 Currently Open Tickets Analysis"):
            # Filter for tickets that are not closed or resolved
            open_tickets = df_filtered[
                    ~df_filtered['request_status'].str.lower().isin(['closed', 'resolved'])
                    ].copy()

            if not open_tickets.empty:
                    # Calculate ticket age in days
                    open_tickets['ticket_age_days'] = (pd.Timestamp.now() - pd.to_datetime(open_tickets['created_time'])).dt.days

                    # Define age bins
                    bins = [0, 3, 7, 30, 9999]
                    labels = ['0-3 days', '4-7 days', '8-30 days', '30+ days']
                    open_tickets['age_range'] = pd.cut(open_tickets['ticket_age_days'], bins=bins, labels=labels, right=True)

                    # Group by group & age range for stacked bar chart
                    age_group_counts = open_tickets.groupby(['group', 'age_range']).size().reset_index(name='count')

                    # Plot stacked bar chart
                    fig_age_group = px.bar(
                            age_group_counts,
                            x='group',
                            y='count',
                            color='age_range',
                            title="Age of Open Tickets by Group",
                            color_discrete_sequence=px.colors.sequential.Blues,
                            barmode='stack'
                        )
                    fig_age_group.update_layout(
                            xaxis_title="Group",
                            yaxis_title="Number of Open Tickets",
                            legend_title="Ticket Age"
                        )
                    st.plotly_chart(fig_age_group, use_container_width=True)

                        # Basic metrics for insights
                    overdue_count = open_tickets[
                            open_tickets['overdue_status'].astype(str).str.lower() == 'yes'
                        ].shape[0]
                    high_priority_count = open_tickets[open_tickets['priority'].str.lower().isin(['high', 'urgent'])].shape[0]

                    with st.expander("## 📌 Insights, Recommendations & Explanation"):
                            st.markdown(f"""
                                ### 🧠 Analysis
                                - There are **{len(open_tickets)}** open tickets in total.
                                - **{overdue_count} tickets** have already missed their deadline.
                                - **{high_priority_count} tickets** are marked as *High* or *Urgent* priority.
                                - A large share of tickets in the **30+ days** category signals a backlog that’s not being actively resolved.
                                - Certain groups have significantly more aged tickets than others — this may indicate workload imbalance or bottlenecks.

                                ### ✅ Recommendations (Cost Reduction Focus)
                                - **Tackle Old Tickets First**: Closing tickets stuck in the 30+ day range frees up agent time for new, revenue-generating tasks.
                                - **Rebalance Workloads**: Reassign tickets from overloaded groups/agents to those with spare capacity.
                                - **Proactive SLA Management**: Monitor tickets approaching their due date (dueby_time) to avoid SLA penalties and dissatisfied customers.
                                - **Automate Stagnant Ticket Follow-Ups**: For tickets pending customer responses, send automatic reminders to speed closure.

                                ### 💰 How This Saves Money
                                - Clearing old tickets reduces wasted labor hours on prolonged cases.
                                - Balancing workloads prevents overtime and reduces burnout-related turnover costs.
                                - Avoiding SLA breaches saves potential penalties and preserves customer trust.
                            """)


    # 4. Unresolved Tickets (Backlog)
    with st.expander("🧾 Ticket Backlog (Unresolved Tickets)"):

        #by pending status
        with st.expander("Unresolved Tickets by Pending Status"):
            if 'request_status' in df_filtered.columns and 'pending_status' in df_filtered.columns:
                    unresolved_df = df_filtered[df_filtered['request_status'].str.lower() != 'resolved']
                    
                    if not unresolved_df.empty:
                        backlog_reason_counts = unresolved_df['pending_status'].fillna('Unknown').value_counts().reset_index()
                        backlog_reason_counts.columns = ['Pending Reason', 'Count']

                        fig = px.bar(
                            backlog_reason_counts,
                            x='Pending Reason',
                            y='Count',
                            title="Unresolved Tickets by Pending Status",
                            text='Count'
                        )
                        fig.update_layout(
                            xaxis_title="Pending Status",
                            yaxis_title="Number of Unresolved Tickets"
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        with st.expander("## 📌 Insights, Recommendations & Explanations"):
                            st.markdown("""
                                ### 📍 Analysis
                                - Tickets in backlog are mostly due to delays in customer response, internal teams, or misrouting.
                                - High volume in any category points to a different operational issue.

                                ### ✅ Recommendation
                                - **Waiting on customer:** Auto-reminders + auto-close after X days.
                                - **Waiting on team:** Investigate cross-team coordination or capacity.
                                - **Wrong assignment:** Improve routing logic using ticket keywords.

                                ### 💰 Cost Impact
                                - Clears old tickets = frees agent time
                                - Prevents backlog from growing into systemic inefficiency.
                                """)

        #most frequent ticket types
        with st.expander("Top Most Frequent Ticket Types"):
            if 'category' in df_filtered.columns and 'subcategory' in df_filtered.columns:
                    
                    # Group and get top 10 frequent ticket combinations
                    top_combos = (
                        df_filtered.groupby(['category', 'subcategory'])
                        .size()
                        .reset_index(name='ticket_count')
                        .sort_values(by='ticket_count', ascending=False)
                        .head(10)
                    )
                    
                    # Create combined label for x-axis
                    top_combos['category_subcategory'] = top_combos['category'] + ' > ' + top_combos['subcategory']
                    
                    # Plot
                    fig = px.bar(
                        top_combos,
                        x='category_subcategory',
                        y='ticket_count',
                        title='Top 10 Most Frequent Ticket Types (Category > Subcategory)',
                        labels={'ticket_count': 'Ticket Count', 'category_subcategory': 'Category > Subcategory'}
                    )
                    fig.update_layout(
                        xaxis_tickangle=45,
                        yaxis_title='Number of Tickets',
                        xaxis_title='Category > Subcategory',
                        height=500
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Expander with analysis, recommendation, explanation
                    with st.expander("## 📌 Insights, Recommendations & Explanations"):
                        st.markdown("### 🔍 Analysis")
                        st.markdown(
                                """
                                The chart above shows the most common types of tickets raised by users. These top 10 combinations contribute significantly to overall ticket volume.
                                This repetition often indicates opportunities for automation, process optimization, or better user guidance.
                                """
                            )

                        st.markdown("### ✅ Recommendation")
                        st.markdown(
                                """
                                - **Automate repetitive issues:** Implement chatbots or knowledge base articles for high-volume, low-complexity issues like *password reset* or *Wi-Fi connection problems*.
                                - **Fix root causes:** If a subcategory frequently appears due to a known issue (e.g., VPN errors), collaborate with relevant teams to resolve it permanently.
                                - **Enhance self-service:** For categories with many phone-based tickets, improve in-app help, UX design, or FAQs to encourage digital self-resolution.
                                """
                            )

                        st.markdown("### 📌 Explanation")
                        st.markdown(
                                """
                                Each bar in the graph represents a problem area users frequently ask for help with.
                                If we reduce or prevent these tickets from happening — by fixing the cause or letting users help themselves — we save staff time and reduce yearly costs.
                                This shift from reacting to problems to preventing them can lead to major savings.
                                """
                            )
