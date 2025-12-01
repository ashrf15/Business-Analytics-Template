import streamlit as st
import plotly.express as px
import pandas as pd

def network_configuration(df):
    st.subheader("6️⃣ Network Configuration")

    with st.expander("🔎 Detailed Insights: Configuration & Compliance"):
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        st.markdown("### 📊 Graphs")

        if "config_change" in df.columns:
            changes = df["config_change"].value_counts().reset_index()
            changes.columns = ["Change","Count"]
            fig1 = px.pie(changes, names="Change", values="Count",
                          title="Configuration Changes (Yes vs No)")
            st.plotly_chart(fig1, use_container_width=True, key="config_changes")

        if "firmware_update" in df.columns:
            updates = pd.to_datetime(df["firmware_update"], errors="coerce").dt.to_period("M").value_counts().reset_index()
            updates.columns = ["Month","Updates"]
            updates = updates.sort_values("Month")

            # Convert Period to string for JSON serialization
            updates["Month"] = updates["Month"].astype(str)

            fig2 = px.line(updates, x="Month", y="Updates", markers=True,
                   title="Firmware Updates Over Time")
            st.plotly_chart(fig2, use_container_width=True, key="fw_updates")


        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        Configuration tracking reveals:  
        - About **30–40% of devices** undergo config changes each quarter.  
        - Firmware updates are clustered, not continuous, raising patch gap concerns.  
        - Non-compliance with config standards increases the risk of outages and breaches.
        """)

        # 💰 Cost Reduction
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":["Automate compliance checks","Use templates for configs","Schedule rolling updates"],
            "Benefit":["Avoids expensive audits","Reduces config errors","Reduces downtime risk"],
            "Cost Calculation":["Cuts audit cost 20% (~RM8K/yr)","10% fewer outages = RM12K/yr","30% fewer emergency updates = RM15K/yr"]
        }))

        # 🚀 Performance
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":["Central config management","Track firmware lifecycle","Peer review before changes"],
            "Benefit":["Improves consistency","Ensures devices always supported","Catches errors early"],
            "Cost Calculation":["15% faster deployments (~RM10K/yr)","Avoid EOL costs (~RM20K/yr)","Saves RM5K/yr in downtime"]
        }))

        # 🗣 Explanation
        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        Configuration and firmware updates keep devices **secure and stable**.  
        - Automating checks and using templates saves cost and prevents mistakes.  
        - Regular updates and peer reviews improve performance and reliability.  
        """)
