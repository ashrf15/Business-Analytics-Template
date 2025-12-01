import streamlit as st
import plotly.express as px
import pandas as pd

# --- Visual identity: blue & white (professional) ---
px.defaults.template = "plotly_white"
PX_SEQ = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#99CCFF"]  # brand-friendly blues


def executive_summary(df):

    with st.expander("📌 Executive Summary"):
        # ================================
        # Key Overview Metrics
        # ================================
        total_assets = df["asset_id"].nunique() if "asset_id" in df.columns else len(df)
        avg_cpu = df["avg_cpu_utilization"].mean().round(2) if "avg_cpu_utilization" in df.columns else 0
        avg_memory = df["avg_memory_utilization"].mean().round(2) if "avg_memory_utilization" in df.columns else 0
        avg_storage = df["avg_storage_utilization"].mean().round(2) if "avg_storage_utilization" in df.columns else 0
        total_cost = df["cost_per_month_usd"].sum().round(2) if "cost_per_month_usd" in df.columns else 0
        potential_savings = df["potential_savings_usd"].sum().round(2) if "potential_savings_usd" in df.columns else 0
        avg_energy = df["energy_consumption_kwh"].mean().round(2) if "energy_consumption_kwh" in df.columns else 0

        # ================================
        # Overview Narrative
        # ================================
        st.markdown(
f"""
The IT Infrastructure Capacity Optimization dataset provides an overview of the organization's 
asset performance, utilization efficiency, and overall cost structure.  

Across all records, the dataset contains **{total_assets:,} active infrastructure assets** 
spanning compute, storage, and network components.  

Key operational highlights include:
- **Average CPU utilization:** {avg_cpu:.2f}%  
- **Average Memory utilization:** {avg_memory:.2f}%  
- **Average Storage utilization:** {avg_storage:.2f}%  
- **Mean Energy Consumption:** {avg_energy:.2f} kWh  
- **Total Monthly Cost:** **USD {total_cost:,.2f}**  
- **Estimated Potential Savings:** **USD {potential_savings:,.2f}**  

These figures establish the baseline performance and financial standing of the current infrastructure environment.
"""
        )

        # ================================
        # Visualization 1: Cost Distribution by Component Type
        # ================================
        if "component_type" in df.columns and "cost_per_month_usd" in df.columns:
            cost_by_type = df.groupby("component_type")["cost_per_month_usd"].sum().reset_index()
            fig = px.pie(
                cost_by_type,
                values="cost_per_month_usd",
                names="component_type",
                title="Cost Distribution by Component Type",
                hole=0.4,
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- Analysis block (clean formatting) ---
            total_cost_all = float(cost_by_type["cost_per_month_usd"].sum())
            top_row = cost_by_type.loc[cost_by_type["cost_per_month_usd"].idxmax()]
            low_row = cost_by_type.loc[cost_by_type["cost_per_month_usd"].idxmin()]
            top_pct = (top_row["cost_per_month_usd"] / total_cost_all * 100.0) if total_cost_all > 0 else 0.0
            low_pct = (low_row["cost_per_month_usd"] / total_cost_all * 100.0) if total_cost_all > 0 else 0.0
            avg_per_type = total_cost_all / len(cost_by_type) if len(cost_by_type) else 0.0

            st.markdown("### Analysis — Cost Distribution by Component Type")
            st.markdown(
f"""
**What the graph shows**

- **Chart type:** Donut chart of monthly cost by component type.  
- **Largest cost share:** **{top_row['component_type']}** — **USD {top_row['cost_per_month_usd']:,.2f}**  
  (about **{top_pct:.1f}%** of total **USD {total_cost_all:,.2f}**).  
- **Smallest cost share:** **{low_row['component_type']}** — **USD {low_row['cost_per_month_usd']:,.2f}**  
  (about **{low_pct:.1f}%** of total).  
- **Average cost per type:** **USD {avg_per_type:,.2f}**.  

**How to interpret it operationally**

1. **Prioritise the largest slices**: Start optimisation with the highest cost component types to unlock faster impact.  
2. **Normalise outliers**: When a type is far above the peer average, review sizing, lifecycle stage, and configuration.  
3. **Align budget with value**: Use this split to decide where to scale up, hold steady, or aggressively rightsize.

**Why it matters**

Cost is concentrated, not evenly spread. Targeting the top cost drivers generates disproportionate savings without touching every component at once.
"""
            )

        # ================================
        # Visualization 2: Average Utilization Comparison
        # ================================
        if {"avg_cpu_utilization", "avg_memory_utilization", "avg_storage_utilization"} <= set(df.columns):
            avg_util = pd.DataFrame(
                {
                    "Metric": ["CPU Utilization", "Memory Utilization", "Storage Utilization"],
                    "Average (%)": [avg_cpu, avg_memory, avg_storage],
                }
            )
            fig2 = px.bar(
                avg_util,
                x="Metric",
                y="Average (%)",
                text="Average (%)",
                title="Average Utilization Across Key Resources",
                color="Metric",
                range_y=[0, 100],
                color_discrete_sequence=PX_SEQ,
            )
            fig2.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
            st.plotly_chart(fig2, use_container_width=True)

            # --- Analysis block (clean formatting) ---
            max_row = avg_util.loc[avg_util["Average (%)"].idxmax()]
            min_row = avg_util.loc[avg_util["Average (%)"].idxmin()]
            overall_avg = float(avg_util["Average (%)"].mean())

            st.markdown("### Analysis — Average Utilization Across Key Resources")
            st.markdown(
f"""
**What the graph shows**

- **Chart type:** Bar chart of average utilisation for CPU, Memory, and Storage.  
- **Highest average utilisation:** **{max_row['Metric']}** — **{max_row['Average (%)']:.2f}%**.  
- **Lowest average utilisation:** **{min_row['Metric']}** — **{min_row['Average (%)']:.2f}%**.  
- **Average across all three metrics:** **{overall_avg:.2f}%**.  

**How to interpret it operationally**

1. **Guard against saturation:** Metrics that sit above roughly **80–85%** for long periods carry higher incident risk.  
2. **Spot over-provisioning:** Very low averages indicate headroom that can be reclaimed by rightsizing or consolidation.  
3. **Identify bottlenecks:** If CPU is high while Memory and Storage are low, workloads are compute-bound; the inverse patterns point to memory-bound or storage-bound constraints.

**Why it matters**

Keeping utilisation in a healthy band protects service levels and stability while avoiding spend on capacity that is never meaningfully used.
"""
            )

        # ================================
        # Summary Conclusion
        # ================================
        st.markdown(
            """
Overall, this executive summary provides a concise snapshot of the organization's 
infrastructure efficiency, cost footprint, and optimisation potential.  
Subsequent sections of this report will dive deeper into utilisation trends, 
capacity planning forecasts, and actionable strategies for improving operational efficiency and cost-effectiveness.
"""
        )
