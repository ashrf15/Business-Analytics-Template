import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# 🔹 Helper to render CIO tables with 3 nested expanders (Option A format)
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)


def energy_efficiency(df):
    # ======================================================
    # Subtarget 1: Energy Consumption vs Utilization
    # ======================================================
    with st.expander("📌 Energy Consumption vs Utilization"):
        if {"avg_cpu_utilization", "energy_consumption_kwh"} <= set(df.columns):
            df = df.copy()
            df["avg_cpu_utilization"] = pd.to_numeric(df["avg_cpu_utilization"], errors="coerce")
            df["energy_consumption_kwh"] = pd.to_numeric(df["energy_consumption_kwh"], errors="coerce")

            # Graph 1: Scatter — Energy vs CPU Utilization
            fig1 = px.scatter(
                df,
                x="avg_cpu_utilization",
                y="energy_consumption_kwh",
                trendline="ols",
                title="Energy Consumption vs CPU Utilization",
                labels={"avg_cpu_utilization": "Average CPU Utilization (%)", "energy_consumption_kwh": "Energy Consumption (kWh)"}
            )
            st.plotly_chart(fig1, use_container_width=True, key="energy_vs_util")

            # Dynamic analysis
            corr = df["avg_cpu_utilization"].corr(df["energy_consumption_kwh"])
            max_kwh = float(df["energy_consumption_kwh"].max())
            min_kwh = float(df["energy_consumption_kwh"].min())
            avg_kwh = float(df["energy_consumption_kwh"].mean())
            high_util = df.loc[df["avg_cpu_utilization"].idxmax()]
            low_util = df.loc[df["avg_cpu_utilization"].idxmin()]
            st.write(f"""
**What this graph is:** A scatter plot showing **energy draw vs. compute load** for each asset.  
- **X-axis:** Average CPU utilization (%).  
- **Y-axis:** Energy consumption (kWh).

**What it shows in your data:** Correlation is **{corr:.2f}**. Energy ranges from **{min_kwh:.2f} kWh** (around **{low_util['avg_cpu_utilization']:.2f}%** CPU) to **{max_kwh:.2f} kWh** (around **{high_util['avg_cpu_utilization']:.2f}%** CPU). Average draw is **{avg_kwh:.2f} kWh** per asset/interval.

**Overall:** A steeper upward trend implies **power scales with load**; visible points with **low CPU but non-trivial kWh** indicate **baseline energy waste** (idling cost).

**How to read it operationally:**  
1) **Peaks:** For points at high CPU + high kWh, ensure **power-aware scheduling** and cooling capacity.  
2) **Plateaus:** If many points sit at low CPU but notable kWh, **consolidate** and enable **idle shutdown**.  
3) **Downswings:** After right-sizing, the cloud of points should **tighten** toward lower kWh at similar CPU—verify impact.  
4) **Mix:** Pair with **hardware age/efficiency** to target refresh of worst kWh-per-%CPU outliers.

**Why this matters:** Idle/inefficient power use is **debt**. It compounds into higher bills, thermal load, and ESG drag. Cutting waste preserves **cost**, **performance headroom**, and **satisfaction**.
""")

            # Graph 2: Histogram — Energy Distribution
            fig2 = px.histogram(
                df,
                x="energy_consumption_kwh",
                nbins=20,
                title="Distribution of Energy Consumption (kWh)",
                labels={"energy_consumption_kwh": "Energy Consumption (kWh)"}
            )
            st.plotly_chart(fig2, use_container_width=True, key="energy_hist")

            high_idle = int((df["avg_cpu_utilization"] < 20).sum())
            st.write(f"""
**What this graph is:** A histogram showing **how energy usage is distributed** across assets/intervals.  
- **X-axis:** Energy consumption (kWh).  
- **Y-axis:** Count of assets/intervals in each kWh bucket.

**What it shows in your data:** Average energy draw sits at **{avg_kwh:.2f} kWh**. There are **{high_idle}** records below **20%** CPU—**idle or lightly loaded** systems still consuming power.

**Overall:** A right-heavy tail signals **power-hungry outliers**; a left-heavy tail with many low-CPU records exposes **oversizing/idle waste**.

**How to read it operationally:**  
1) **Peaks:** Identify the highest kWh buckets and **target those assets** for tuning or refresh.  
2) **Plateaus:** A stable center mass is fine—**monitor drift** and seasonal shifts.  
3) **Downswings:** After consolidation, the right tail should **shrink**—confirm savings on the bill.  
4) **Mix:** Cross-tab buckets by **CPU% bands** to quantify **kWh at idle** vs at load.

**Why this matters:** Unchecked tails are **debt**—you pay for heat and watts that don’t translate to service value. Right-sizing protects **budget**, **resilience**, and **user experience**.
""")

            # CIO Tables for Energy vs Utilization
            total_cost = float(df["cost_per_month_usd"].sum()) if "cost_per_month_usd" in df.columns else 0.0
            total_sav = float(df["potential_savings_usd"].sum()) if "potential_savings_usd" in df.columns else 0.0
            cio_energy = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Power off idle servers | **Phase 1**: Identify servers with CPU utilization below 20 percent by analysing monitoring data and confirming that these assets do not support critical workloads during off peak periods. <br><br>**Phase 2**: Configure and test automation policies that shut down or hibernate non critical servers during off peak hours while ensuring that they can be brought back online safely when demand returns. <br><br>**Phase 3**: Review monthly energy use and server state reports to verify that shutdown policies are working as intended and refine the list of candidates over time. | - Reduces power and cooling expenses by eliminating energy draw from servers that are not doing useful work.<br><br>- Lowers ongoing utility bills in a way that is visible on monthly and quarterly cost reports.<br><br>- Decreases thermal load in the data centre which can extend hardware lifespan and reduce the likelihood of heat related failures. | Formula: Savings Ratio = Σ potential_savings_usd ÷ Σ cost_per_month_usd = ${total_sav:,.2f}/${total_cost:,.2f} = {(total_sav/total_cost if total_cost else 0):.2f}. | Histogram shows high idle server count below 20% utilization. |
| Consolidate workloads to fewer servers | **Phase 1**: Identify underused servers and group workloads that can safely share capacity without breaching performance or resilience requirements. <br><br>**Phase 2**: Migrate and consolidate workloads from these underused servers onto a smaller number of well utilised hosts while monitoring performance and stability as changes are applied. <br><br>**Phase 3**: Decommission or repurpose redundant nodes and measure the decline in total energy use and hardware footprint after consolidation. | - Eliminates waste created by lightly loaded hardware that continues to consume full baseline power.<br><br>- Improves overall data centre efficiency by increasing utilisation on the remaining servers while lowering the total number of machines that must be powered and cooled.<br><br>- Reduces maintenance, support, and licensing overhead because there are fewer physical assets to manage. | Formula: Δ Energy × Cost per kWh. Dataset: Average {avg_kwh:.2f} kWh can be reduced across {high_idle} idle systems. | Scatter plot confirms baseline consumption persists even at low CPU. |
| Upgrade to energy-efficient hardware | **Phase 1**: Identify older servers and power supplies that show high energy consumption relative to their workload and compare them with current generation options. <br><br>**Phase 2**: Plan and execute replacement of these inefficient systems with modern energy efficient hardware while ensuring capacity and compatibility are preserved. <br><br>**Phase 3**: Track energy consumption before and after the upgrade to confirm that the expected savings and efficiency gains are realised. | - Delivers long term cost savings through lower electricity consumption for the same or higher compute capacity.<br><br>- Reduces the environmental footprint of the infrastructure by lowering total energy use and associated emissions.<br><br>- Improves reliability and supportability by replacing ageing equipment with newer and more robust platforms. | Formula: Δ kWh × Electricity Rate. Dataset: older servers consume {max_kwh:.2f} kWh per unit under load. | Upper scatter outliers reflect inefficient devices. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Implement power-aware scheduling | **Phase 1**: Review current workload patterns and enable dynamic scaling features so that compute resources adjust based on utilisation and demand profiles. <br><br>**Phase 2**: Consolidate off peak workloads onto fewer servers and place non critical tasks in time windows where spare capacity is available. <br><br>**Phase 3**: Review performance, utilisation, and energy metrics quarterly to confirm that throughput is maintained while power consumption trends downward. | - Maintains or improves throughput while avoiding unnecessary energy consumption during low demand periods.<br><br>- Reduces the need to run a large fleet of servers at partial load which helps prevent resource waste.<br><br>- Allows capacity and energy strategies to respond to real workloads instead of static assumptions. | Formula: Δ Energy Saved × Cost per kWh. Dataset: correlation {corr:.2f} indicates power increases with CPU load. | Scatter shows proportional scaling opportunity. |
| Monitor and tune CPU performance states | **Phase 1**: Enable support for processor performance states such as dynamic voltage and frequency scaling across eligible servers and ensure that monitoring covers these settings. <br><br>**Phase 2**: Tune thresholds and policies for stepping CPU frequency up or down to balance performance needs with energy savings under different types of load. <br><br>**Phase 3**: Validate efficiency by comparing baseline and tuned energy consumption and checking that user facing performance remains acceptable. | - Reduces wasted energy by lowering CPU frequency when full performance is not required while still meeting service expectations.<br><br>- Helps smooth thermal and power demand which can stabilise facility operations and cooling requirements.<br><br>- Optimises resource use automatically without relying on manual interventions by operations teams. | Formula: (Baseline – Tuned kWh) × Duration. Dataset: idle systems sustain high base power. | Histogram demonstrates inefficiency baseline. |
| Optimize data placement | **Phase 1**: Analyse where batch jobs, analytics workloads, and storage intensive tasks are running and identify servers that operate more efficiently at similar load levels. <br><br>**Phase 2**: Schedule energy intensive or flexible workloads on the most efficient servers and data centre zones while keeping critical services on appropriately resilient platforms. <br><br>**Phase 3**: Reassess workload placement regularly and reallocate tasks as hardware efficiency profiles and demand patterns change. | - Reduces overall facility energy demand by matching heavy workloads to hardware that delivers more work per unit of energy consumed.<br><br>- Improves predictability of power and cooling needs because workloads are aligned with known efficiency characteristics.<br><br>- Can delay the need for additional capacity investments by extracting more useful work from existing infrastructure. | Formula: Δ workload energy × $/kWh. Dataset: high variation in scatter indicates imbalance. | Scatter pattern exposes non-linear efficiency. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate energy-efficiency metrics | **Phase 1**: Build and publish a sustainability dashboard that shows key metrics such as total energy use, savings achieved, and efficiency ratios over time. <br><br>**Phase 2**: Highlight power savings and major optimisation initiatives in internal and external communications so stakeholders understand the progress being made. <br><br>**Phase 3**: Report these metrics on a quarterly basis and invite feedback to improve the clarity and usefulness of the information presented. | - Builds public and customer trust by demonstrating that the organisation manages energy use in a transparent and responsible way.<br><br>- Strengthens ESG reputation by providing concrete numbers rather than general statements about sustainability.<br><br>- Encourages internal teams to continue improving efficiency because progress is visible and recognised. | Formula: Emission Reduction = Δ kWh × 0.0007 (tons CO₂). Dataset: energy decline measurable post-optimization. | Scatter trend confirms efficiency improvements. |
| Establish green procurement policy | **Phase 1**: Define procurement standards that prioritise energy rated servers, storage, and network devices and document these requirements in sourcing policies. <br><br>**Phase 2**: Require suppliers to provide energy efficiency certifications and lifecycle information for proposed equipment and use this data during selection. <br><br>**Phase 3**: Track the impact of these purchasing decisions on overall energy consumption and refresh plans. | - Ensures that new infrastructure entering the environment supports long term sustainability and cost reduction goals.<br><br>- Reduces future energy and cooling requirements because newer assets are more efficient from day one.<br><br>- Aligns IT lifecycle management with broader organisational environmental objectives. | Formula: (Legacy power – New power) × Fleet size. Dataset: {high_idle} low-utilization systems justify hardware refresh. | Low-efficiency outliers demonstrate replacement need. |
| Promote awareness through reporting | **Phase 1**: Create clear summaries of annual sustainability and energy efficiency results and distribute them to customers, partners, and internal stakeholders. <br><br>**Phase 2**: Engage users and business units by explaining how their behaviours and workload patterns influence energy consumption and invite ideas for improvement. <br><br>**Phase 3**: Recognize teams or projects that contribute to meaningful efficiency gains and share their practices across the organisation. | - Strengthens the organisation brand image as a responsible and forward looking technology operator.<br><br>- Encourages a culture where everyone understands their role in managing resource use and supporting sustainability targets.<br><br>- Helps maintain momentum on efficiency initiatives because achievements are highlighted and celebrated. | Formula: CSAT increase correlated with transparency. Dataset: improved energy profile boosts perception. | Charts show visible efficiency trend. |
"""
            }
            render_cio_tables("Energy vs Utilization — CIO Recommendations", cio_energy)

    # ======================================================
    # Subtarget 2: Facility Power Usage Effectiveness (PUE)
    # ======================================================
    with st.expander("📌 Facility Power Usage Effectiveness (PUE)"):
        if "pue" in df.columns:
            df = df.copy()
            df["pue"] = pd.to_numeric(df["pue"], errors="coerce")
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")

            # Graph 1: Line chart — PUE trend
            fig3 = px.line(
                df,
                x="date",
                y="pue",
                title="Data Center Power Usage Effectiveness (PUE) Trend",
                labels={"date": "Date", "pue": "PUE Value"}
            )
            st.plotly_chart(fig3, use_container_width=True, key="pue_trend")

            # Graph 2: Histogram — PUE distribution
            fig4 = px.histogram(
                df,
                x="pue",
                nbins=15,
                title="Distribution of Facility PUE",
                labels={"pue": "Power Usage Effectiveness"}
            )
            st.plotly_chart(fig4, use_container_width=True, key="pue_hist")

            avg_pue = float(df["pue"].mean())
            max_pue = float(df["pue"].max())
            min_pue = float(df["pue"].min())
            st.write(f"""
**What this graph is:**  
1) A line chart tracking **PUE over time** (facility efficiency).  
   - **X-axis:** Calendar date.  
   - **Y-axis:** Power Usage Effectiveness (PUE).  
2) A histogram showing **how often** each PUE band occurs.  
   - **X-axis:** PUE value.  
   - **Y-axis:** Frequency.

**What it shows in your data:** Average PUE is **{avg_pue:.2f}**, ranging from **{min_pue:.2f}** to **{max_pue:.2f}**. Values closer to **1.2–1.3** indicate strong efficiency; readings above **~1.8** suggest **cooling/airflow** or **power conditioning** inefficiencies.

**Overall:** A **rising** PUE line signals **worsening efficiency** (more non-IT power per IT watt); a **flat/falling** line shows **catch-up and stabilization**. A right-heavy histogram tail highlights **inefficient periods**.

**How to read it operationally:**  
1) **Peaks:** Investigate **cooling setpoints, containment, and airflow** when PUE spikes.  
2) **Plateaus:** Maintain gains—optimize **economization** and **fan curves**; monitor drift.  
3) **Downswings:** After HVAC/airflow tweaks, PUE should **decline**—verify with trend.  
4) **Mix:** Correlate PUE with **IT load** and **weather** to separate structural vs seasonal effects.

**Why this matters:** Excess facility overhead is **debt**. It inflates utility bills and ESG footprint without adding service value. Keeping PUE low preserves **cost**, **resilience**, and **stakeholder confidence**.
""")

            cio_pue = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Optimize cooling systems | **Phase 1**: Review HVAC configuration and efficiency by checking setpoints, airflow patterns, and current control strategies against best practices. <br><br>**Phase 2**: Implement hot aisle and cold aisle containment or similar approaches so that cold air and hot exhaust are separated and delivered more efficiently. <br><br>**Phase 3**: Automate cooling based on sensor feedback and continuously fine tune control logic using real time temperature and PUE data. | - Reduces overall energy costs by lowering the amount of power required to cool the data centre for the same IT load.<br><br>- Decreases wear on cooling equipment which can reduce maintenance frequency and lengthen equipment life.<br><br>- Improves thermal stability which protects hardware and supports consistent performance. | Formula: Δ PUE × Total kWh × Rate. Dataset: average {avg_pue:.2f}, max {max_pue:.2f} indicates inefficiency. | Line trend shows rising PUE periods. |
| Deploy free cooling solutions | **Phase 1**: Evaluate the feasibility of using outside air economisation or other free cooling methods based on local climate and facility design. <br><br>**Phase 2**: Enable and tune economiser thresholds so that free cooling is used whenever conditions allow without compromising required temperature ranges. <br><br>**Phase 3**: Measure energy savings and PUE improvements after deployment and adjust control parameters to maximise benefit. | - Cuts power consumption by leveraging naturally cool air or other low cost cooling sources when conditions are suitable.<br><br>- Reduces reliance on mechanical cooling systems which can lower both energy use and equipment runtime hours.<br><br>- Supports sustainability and environmental goals by lowering indirect emissions from the power used for cooling. | Formula: Reduced kWh × $/kWh. Dataset: PUE >1.8 intervals mark high-cost cooling. | Histogram tail validates inefficient cycles. |
| Conduct periodic energy audits | **Phase 1**: Schedule structured energy audits at least once per quarter that review facility, cooling, and power distribution efficiency using standard frameworks. <br><br>**Phase 2**: Benchmark current performance against industry standards and comparable facilities to identify where the largest gaps and opportunities lie. <br><br>**Phase 3**: Implement corrective measures that target the most significant findings and document the savings realised after each cycle. | - Identifies hidden energy waste that may not be visible through routine operational monitoring alone.<br><br>- Creates a regular cycle of review and improvement that keeps efficiency efforts active instead of one-off projects.<br><br>- Provides documented evidence of improvement that can be used in internal reporting and external ESG disclosures. | Formula: Δ Audit savings × $/month. Dataset: PUE deviation range {min_pue:.2f}–{max_pue:.2f}. | Variability supports audit need. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Real-time PUE monitoring | **Phase 1**: Deploy sensors and metering to capture total facility power and IT load in near real time with sufficient granularity for decision making. <br><br>**Phase 2**: Integrate these readings into a central dashboard that operations teams can use to observe PUE trends alongside other facility metrics. <br><br>**Phase 3**: Use this dashboard to adjust cooling and power configurations dynamically when PUE drifts away from target levels. | - Improves facility responsiveness by allowing teams to spot and correct efficiency problems as they arise rather than after the fact.<br><br>- Helps maintain stable operating conditions which supports more predictable IT performance.<br><br>- Enables data driven tuning of facility systems rather than relying on static settings and manual checks. | Formula: Δ efficiency × Load. Dataset: PUE fluctuates between {min_pue:.2f}–{max_pue:.2f}. | Line chart shows deviations indicating tuning need. |
| Optimize rack airflow design | **Phase 1**: Reassess rack layout, cable management, and venting to ensure that cold air is delivered to equipment in a consistent and unobstructed way. <br><br>**Phase 2**: Install blanking panels, floor grommets, or containment where needed to prevent hot and cold air from mixing unnecessarily. <br><br>**Phase 3**: Verify temperature uniformity across racks and aisles using thermal scans or sensors and adjust layout where hotspots persist. | - Enhances thermal efficiency by ensuring that cooling air reaches equipment directly instead of being wasted in bypass flows.<br><br>- Reduces the risk of local hotspots that can impact server performance and reliability.<br><br>- May allow cooling setpoints to be raised slightly while maintaining safe temperatures which further reduces energy use. | Formula: Δ Cooling load × kWh rate. Dataset: inefficiency visible in high PUE intervals. | Histogram outliers align with airflow issues. |
| Integrate DCIM tools | **Phase 1**: Deploy a data centre infrastructure management platform that can collect, store, and visualise power, temperature, capacity, and PUE data in one place. <br><br>**Phase 2**: Analyse utilisation patterns and correlations between PUE, IT load, and facility conditions to identify optimisation opportunities. <br><br>**Phase 3**: Automate key reports and alerts so that teams receive actionable information without manual data gathering. | - Enhances data driven control of the facility by bringing together operational information that is often scattered across systems.<br><br>- Improves capacity planning and helps avoid over provisioning of power and cooling for future expansions.<br><br>- Reduces manual effort required to assemble reports and enables faster feedback loops for optimisation actions. | Formula: Reduced energy × $/kWh. Dataset: PUE mean {avg_pue:.2f} indicates improvement potential. | Consistent monitoring refines performance. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Publicly share sustainability performance | **Phase 1**: Compile quarterly PUE metrics and related efficiency indicators into a clear and accessible format suitable for external audiences. <br><br>**Phase 2**: Include these metrics in ESG reports, customer communications, or on corporate websites to show commitment to sustainable operations. <br><br>**Phase 3**: Track how customers and partners respond to this transparency and adjust the level of detail or frequency to maximise value. | - Builds customer confidence that the organisation is managing infrastructure responsibly and investing in efficiency.<br><br>- Strengthens competitive positioning in markets where sustainability is an important buying criterion.<br><br>- Supports brand differentiation by providing concrete evidence of environmental performance rather than generic claims. | Formula: CSAT improvement linked to transparency. Dataset: {avg_pue:.2f} PUE average publicly reportable. | Charts confirm steady improvement trend. |
| Implement environmental goals | **Phase 1**: Set specific and measurable targets such as achieving a PUE of less than or equal to 1.5 within a defined time frame and communicate these goals internally. <br><br>**Phase 2**: Measure PUE and supporting indicators on a quarterly basis and compare results to the targets to understand progress and gaps. <br><br>**Phase 3**: Adjust strategy, investments, and operational practices when metrics show that progress is falling behind the desired trajectory. | - Aligns IT and facility operations with broader organisational ESG targets and commitments.<br><br>- Provides a clear direction for energy and efficiency initiatives which helps prioritise projects and funding.<br><br>- Makes it easier to communicate progress and challenges to executives and external stakeholders in a structured way. | Formula: Target Δ PUE × Annual kWh. Dataset: current {avg_pue:.2f} >1.5 shows scope. | Line trend supports reduction potential. |
| Conduct green certification | **Phase 1**: Assess eligibility and requirements for certifications such as ISO 50001 or LEED and determine which standards best fit the facility and organisation. <br><br>**Phase 2**: Implement the process, procedural, and technical changes required to meet efficiency and management criteria for the chosen certification. <br><br>**Phase 3**: Complete certification audits and communicate the achievement and ongoing commitments to customers and stakeholders. | - Enhances brand reputation by demonstrating that an independent body has validated the organisation energy management and efficiency practices.<br><br>- Encourages continuous improvement because certifications typically require ongoing monitoring and periodic recertification.<br><br>- May unlock access to incentives, partnerships, or customer opportunities that prioritise certified facilities. | Formula: Certification ROI = Energy saved × $/kWh. Dataset: PUE reduction visible post-optimization. | Graph trends validate continuous improvement. |
"""
            }
            render_cio_tables("Facility PUE — CIO Recommendations", cio_pue)
