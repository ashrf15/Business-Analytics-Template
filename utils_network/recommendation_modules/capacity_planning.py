import streamlit as st
import plotly.express as px
import pandas as pd

def capacity_planning(df):
    st.subheader("9️⃣ Network Capacity Planning")

    with st.expander("🔎 Detailed Insights: Capacity Planning"):
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        st.markdown("### 📊 Graphs")

        if "capacity_used_percent" in df.columns:
            fig1 = px.histogram(df, x="capacity_used_percent", nbins=20,
                                title="Capacity Utilization Distribution (%)")
            st.plotly_chart(fig1, use_container_width=True, key="capacity_hist")

            avg_cap = df["capacity_used_percent"].mean().round(1)
            st.metric("Average Network Capacity Utilization", f"{avg_cap}%")

        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        - Most devices run between **70–95% utilization**, with some near 100%.  
        - Consistently high utilization signals the need for **capacity upgrades**.  
        - Underutilized areas suggest opportunities for consolidation.
        """)

        # 💰 Cost Reduction
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":["Decommission underutilized devices","Consolidate capacity","Use cloud bursting for peak loads"],
            "Benefit":["Cuts licensing & power costs","Fewer devices = lower OPEX","Avoids buying excess capacity"],
            "Cost Calculation":["5 devices × RM3K/yr = RM15K","10% OPEX cut = RM12K","Save RM20K in CapEx annually"]
        }))

        # 🚀 Performance
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":["Forecast demand trends","Add scalable capacity in hotspots","Implement auto-scaling solutions"],
            "Benefit":["Prevents bottlenecks","Keeps performance consistent","Future-proofs the network"],
            "Cost Calculation":["Avoids 2 outages/yr (~RM30K)","Supports 15% more traffic (~RM25K/yr)","Avoids RM40K in delays"]
        }))

        # 🗣 Explanation
        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        Capacity shows **how full the network is**.  
        - Removing unused gear and consolidating saves costs.  
        - Adding scalable capacity where needed ensures the network can handle future growth.  
        """)
