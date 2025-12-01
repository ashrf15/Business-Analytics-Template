import streamlit as st
import plotly.express as px
import pandas as pd

# 🔹 Helper function to render CIO tables with 3 nested expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)



def resolution_action(df_filtered):
    # ---------------------- 1a ----------------------
    with st.expander("📌 Number of Tickets Opened"): 
        if "created_time" in df_filtered.columns:
            df_filtered["created_date"] = pd.to_datetime(df_filtered["created_time"], errors="coerce").dt.date
            trend = df_filtered.groupby("created_date").size().reset_index(name="ticket_count")

            # Format dates to Malaysian format (DD/MM/YYYY)
            trend["created_date_str"] = pd.to_datetime(trend["created_date"]).dt.strftime("%d/%m/%Y")

            # --- Graph 1: Tickets opened over time (line chart)
            fig = px.line(trend, x="created_date_str", y="ticket_count", title="Tickets Opened Over Time")
            st.plotly_chart(fig, use_container_width=True)

            # 🔹 Dynamic analysis for tickets opened over time
            if not trend.empty:
                total_tickets = trend["ticket_count"].sum()
                avg_tickets = trend["ticket_count"].mean()
                max_row = trend.loc[trend["ticket_count"].idxmax()]
                min_row = trend.loc[trend["ticket_count"].idxmin()]
                change_pct = ((max_row["ticket_count"] - min_row["ticket_count"]) / max(min_row["ticket_count"], 1)) * 100

                st.markdown("### Analysis – Tickets Opened Over Time")
                st.write(f"""
                The line chart illustrates the daily volume of tickets opened.  
                - **X-axis:** Dates when tickets were created (in DD/MM/YYYY format).  
                - **Y-axis:** Number of tickets opened per day.  

                A total of **{total_tickets} tickets** were logged over the selected period, 
                with an average of **{avg_tickets:.1f} tickets per day**.  
                The highest spike occurred on **{max_row['created_date_str']}** with **{max_row['ticket_count']} tickets**, 
                compared to the lowest point on **{min_row['created_date_str']}** with only **{min_row['ticket_count']} tickets**.  
                This represents a relative change of approximately **{change_pct:.1f}%** between peak and trough.  

                The pattern shows {"consistent demand" if change_pct < 20 else "significant fluctuations"}, 
                suggesting that ticket inflow is {"stable across the timeline" if change_pct < 20 else "influenced by specific events such as incidents, updates, or seasonal workload"}.  

                Decision-makers should pay close attention to the spikes, as they may indicate recurring system problems, 
                user behavior trends, or operational bottlenecks requiring additional resources.
                """)
            else:
                st.info("No data available to generate analysis.")
