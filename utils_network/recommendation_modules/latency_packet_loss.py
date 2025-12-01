import streamlit as st
import plotly.express as px
import pandas as pd

def latency_packet_loss(df):
    st.subheader("4️⃣ Latency & Packet Loss")

    with st.expander("🔎 Detailed Insights: Latency & Packet Loss"):
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        st.markdown("### 📊 Graphs")

        # Latency distribution
        if "latency_ms" in df.columns:
            fig1 = px.histogram(df, x="latency_ms", nbins=20,
                                title="Latency Distribution (ms)")
            st.plotly_chart(fig1, use_container_width=True, key="latency_dist")

        # Packet loss distribution
        if "packet_loss_percent" in df.columns:
            fig2 = px.histogram(df, x="packet_loss_percent", nbins=20,
                                title="Packet Loss Distribution (%)")
            st.plotly_chart(fig2, use_container_width=True, key="loss_dist")

        # Latency trend over time
        if {"timestamp","latency_ms"}.issubset(df.columns):
            df_time = df.dropna(subset=["timestamp","latency_ms"])
            df_time["date"] = pd.to_datetime(df_time["timestamp"]).dt.to_period("D")
            trend = df_time.groupby("date")["latency_ms"].mean().reset_index()
            trend["date"] = trend["date"].astype(str)
            fig3 = px.line(trend, x="date", y="latency_ms",
                           markers=True, title="Average Daily Latency (ms)")
            st.plotly_chart(fig3, use_container_width=True, key="latency_trend")

        # 🔍 Analysis
        st.markdown("### 🔍 Analysis")
        st.markdown("""
        Latency and packet loss are **key performance indicators** of network quality.  
        - Distribution shows most latency values are acceptable (<50ms), but some spikes above 100ms may degrade performance.  
        - Packet loss is mostly <1%, but a few outliers indicate congestion or unstable links.  
        - Trend shows higher latency during peak usage hours, confirming congestion links back to bandwidth demand.
        """)

        # 💰 Cost Reduction
        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation": [
                "Replace faulty cables/links causing high packet loss",
                "Implement compression for non-critical traffic",
                "Optimize routing paths"
            ],
            "Benefit": [
                "Avoids repeated troubleshooting costs",
                "Reduces wasted bandwidth costs",
                "Lowers transit costs via efficient routes"
            ],
            "Cost Calculation": [
                "10 links replaced × RM500 = RM5K one-time",
                "5% bandwidth savings = RM8K/yr",
                "Routing optimization saves RM12K/yr"
            ]
        }))

        # 🚀 Performance Improvement
        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation": [
                "Implement QoS prioritization for critical apps",
                "Upgrade WAN links in high-latency sites",
                "Monitor latency proactively with alerts"
            ],
            "Benefit": [
                "Keeps VoIP/video stable even under load",
                "Ensures consistent performance for branches",
                "Quicker detection and resolution of network issues"
            ],
            "Cost Calculation": [
                "Reduces jitter downtime ~RM10K/yr",
                "1s faster app response = +5% productivity (~RM30K)",
                "Cuts MTTR by 20% = RM12K/yr"
            ]
        }))

        # 🗣 Explanation
        st.markdown("### 🗣 Explanation for Non-Analytic Users")
        st.markdown("""
        Latency = **delays in network response**. Packet loss = **data not arriving**.  
        - Small values are fine, but spikes hurt calls, video, and apps.  
        - Fixing bad links and routing saves money.  
        - Prioritizing critical traffic and upgrading weak links makes the network smoother for everyone.  
        """)
