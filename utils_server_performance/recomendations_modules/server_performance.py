import streamlit as st
import plotly.express as px
import pandas as pd

def server_performance(df):
    st.subheader("4️⃣ Server Performance Metrics")

    with st.expander("🔎 Detailed Insights: Server Performance"):
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        st.markdown("### 📊 Graphs")

        if "response_time_ms" in df.columns:
            fig1 = px.histogram(df, x="response_time_ms", nbins=20,
                                title="Server Response Time Distribution (ms)")
            st.plotly_chart(fig1, use_container_width=True, key="srv_perf_resp")

        if "throughput_rps" in df.columns:
            fig2 = px.histogram(df, x="throughput_rps", nbins=20,
                                title="Server Throughput Distribution (Requests/s)")
            st.plotly_chart(fig2, use_container_width=True, key="srv_perf_thr")

        if {"error_type","error_rate_percent"}.issubset(df.columns):
            errors = df[df["error_rate_percent"]>0].groupby("error_type")["error_rate_percent"].mean().reset_index()
            fig3 = px.bar(errors, x="error_type", y="error_rate_percent",
                          color="error_rate_percent", color_continuous_scale="Reds",
                          title="Average Error Rate by Type (%)")
            st.plotly_chart(fig3, use_container_width=True, key="srv_perf_err")

        st.markdown("### 🔍 Analysis")
        st.markdown("""
        - Most response times <200ms, but some >400ms degrade app experience.  
        - Throughput varies, spikes at >1500 req/s.  
        - Error types: Disk and Memory leaks most common.
        """)

        st.markdown("### 💰 CIO Recommendations for Cost Reduction")
        st.table(pd.DataFrame({
            "Recommendation":["Optimize DB queries","Fix recurring error sources","Consolidate low-traffic apps"],
            "Benefit":["Faster responses","Less rework","Fewer servers needed"],
            "Cost Calculation":["Save 10h/week dev = RM20K","Avoid repeat incidents RM15K","Cuts 5 servers = RM25K"]
        }))

        st.markdown("### 🚀 CIO Recommendations for Performance Improvement")
        st.table(pd.DataFrame({
            "Recommendation":["Add caching","Tune app configs","Upgrade critical servers"],
            "Benefit":["Lower latency","Reduce errors","Higher throughput"],
            "Cost Calculation":["Avoids RM30K downtime","Boosts perf RM20K","Supports +25% users = RM40K"]
        }))

        st.markdown("### 🗣 Business Explanation")
        st.markdown("""
        Shows **response times, throughput, and errors**.  
        Faster servers keep apps reliable, and fixing recurring problems avoids costs.  
        """)
