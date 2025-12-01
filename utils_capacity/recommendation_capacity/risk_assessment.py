import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# --- Visual identity: professional blue & white (global) ---
px.defaults.template = "plotly_white"
PX_SEQ = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#99CCFF"]
px.defaults.color_discrete_sequence = PX_SEQ  # apply globally

# 🔹 Helper to render CIO tables with 3 nested expanders (Option A format)
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)


def risk_assessment(df):

    # ======================================================
    # Subtarget 1: Capacity Risk Heatmap
    # ======================================================
    with st.expander("📌 Capacity Risk Heatmap"):
        if {"avg_cpu_utilization", "avg_memory_utilization"} <= set(df.columns):
            df = df.copy()
            df["avg_cpu_utilization"] = pd.to_numeric(df["avg_cpu_utilization"], errors="coerce")
            df["avg_memory_utilization"] = pd.to_numeric(df["avg_memory_utilization"], errors="coerce")
            df["risk_score"] = (df["avg_cpu_utilization"] * 0.6) + (df["avg_memory_utilization"] * 0.4)

            # Graph 1: Heatmap of risk (blue scale)
            fig1 = px.density_heatmap(
                df,
                x="avg_cpu_utilization",
                y="avg_memory_utilization",
                z="risk_score",
                nbinsx=20,
                nbinsy=20,
                color_continuous_scale="Blues",
                title="Risk Heatmap by CPU & Memory Load",
                labels={"avg_cpu_utilization": "CPU Utilization (%)", "avg_memory_utilization": "Memory Utilization (%)"}
            )
            st.plotly_chart(fig1, use_container_width=True, key="risk_heatmap")

            # --- Analysis for Graph 1 (Heatmap) ---
            max_risk = float(df["risk_score"].max())
            min_risk = float(df["risk_score"].min())
            avg_risk = float(df["risk_score"].mean())
            high_risk_assets = int((df["risk_score"] > 85).sum())
            low_risk_assets = int((df["risk_score"] < 30).sum())

            st.write(f"""
What this graph is: A density heatmap showing combined capacity risk based on CPU and Memory utilization across all assets.

X-axis: CPU utilization (%).
Y-axis: Memory utilization (%).
What it shows in your data: The highest observed risk score is {max_risk:.2f}, the lowest is {min_risk:.2f}, and the average across the estate is {avg_risk:.2f}. There are {high_risk_assets} assets above the critical threshold higher than 85 and {low_risk_assets} assets in the safe zone below 30. Darker cells clustered toward the upper right corner indicate assets experiencing high CPU and high Memory at the same time which is where capacity risk is most acute.

Overall: Capacity risk is not evenly spread and is concentrated in a subset of assets that operate under sustained CPU and Memory pressure. The heatmap makes it clear where combined stress is highest so that risk reduction work can be focused instead of spread thinly across low risk areas.

How to read it operationally:

Peaks: Treat the darkest cells near the top right as immediate candidates for mitigation by scaling capacity, shifting workloads, or throttling bursty processing so they do not continue running at extreme levels.

Plateaus: Interpret medium blue bands as manageable but watch zones where CPU and Memory are both moderately high and keep autoscaling and alerting tuned so they do not drift into the danger area.

Downswings: Expect the cluster of hot cells to shrink and move toward lower CPU and Memory values after remediation work and track that movement month over month to confirm lasting improvement.

Mix: Combine this heatmap with information about business criticality and incident history so that the riskiest and most important services are tackled first rather than only the noisiest assets.

Why this matters: Persistent hotspots substantially increase the chance of outages and SLA breaches and reducing those hotspots is one of the most direct ways to protect cost performance and customer satisfaction at the same time.
""")

            # Graph 2: Histogram of risk distribution (blue)
            fig2 = px.histogram(
                df,
                x="risk_score",
                nbins=25,
                title="Distribution of Risk Scores Across All Assets",
                labels={"risk_score": "Risk Score"}
            )
            fig2.update_traces(marker_color=PX_SEQ[1])
            st.plotly_chart(fig2, use_container_width=True, key="risk_hist")

            # --- Analysis for Graph 2 (Histogram) ---
            p90_risk = float(df["risk_score"].quantile(0.90))
            high_tail = int((df["risk_score"] >= p90_risk).sum())
            p50_risk = float(df["risk_score"].median())

            st.write(f"""
What this graph is: A histogram showing how the calculated risk scores are distributed across the entire asset fleet.

X-axis: Risk score bands.
Y-axis: Number of assets in each band.
What it shows in your data: The median risk score sits at {p50_risk:.2f} which represents the middle of the estate and the top ten percent risk threshold starts at {p90_risk:.2f} with {high_tail} assets sitting in that highest risk band. A long or tall right tail indicates that a relatively small group of assets carries a large portion of the overall risk profile while a more compact central hump indicates that risk is more evenly distributed and easier to manage.

Overall: The distribution reveals whether risk is concentrated in a minority of assets or spread more broadly across the environment. A pronounced right tail means you can get large resilience gains by improving a small set of assets while a flatter distribution suggests that policies and standards need to be tightened across the board.

How to read it operationally:

Peaks: Use the tallest bars toward the right end of the chart to quickly identify how many assets fall into the highest risk bands and treat them as priority for targeted mitigation plans.

Plateaus: Use a wide mid band to judge how stable your typical operating conditions are and maintain existing guardrails so that this central group does not drift upward into high risk territory.

Downswings: After remediation and policy changes expect the extreme right tail to shrink and for the bulk of the distribution to shift slightly left which indicates a healthier risk posture.

Mix: Segment the histogram by component type or location to see which parts of the estate contribute most to the high end of the risk distribution and assign clear ownership to those domains.

Why this matters: The shape of the distribution shows where a small number of assets create a disproportionate amount of instability and resolving those assets first gives the best resilience gain for the effort spent.
""")

            # --- CIO tables ---
            cio_heatmap = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Focus remediation on high-risk clusters | Phase 1: Identify all assets with a risk score above 85 using the heatmap and histogram and validate with technical teams that the high values are consistent over time rather than one off spikes.<br><br>Phase 2: Design and implement remediation plans that target only these high risk assets at first such as capacity upgrades configuration tuning or workload redistribution and align timelines with business stakeholders.<br><br>Phase 3: After remediation is complete remeasure the risk scores and operational metrics for the same assets review whether risk has reduced as expected and capture lessons to refine the next remediation cycle.<br><br> | - Reduces overall remediation spending by concentrating work and budget on the small group of assets that contribute most to capacity risk instead of applying generic fixes everywhere.<br><br>- Lowers the cost of change by avoiding unnecessary upgrades and interventions on low risk systems that are already performing within acceptable limits.<br><br>- Speeds up visible risk reduction because addressing the highest risk assets first produces noticeable improvements in stability and headroom quicker than broad untargeted work.<br><br>- Makes funding requests easier to justify since the link between spend and reduction in critical risk is clearly demonstrated in both the heatmap and histogram views.<br><br> | Formula: Savings = (Total Assets − High Risk Assets) × Average Mitigation Cost<br>Dataset: {high_risk_assets} out of {len(df)} assets require immediate attention while the remainder can be deferred.<br> | Heatmap shows clearly delineated high risk clusters at the upper end of CPU and Memory load which justifies focusing remediation on that subset first. |
| Optimize workload distribution | Phase 1: Use capacity and utilization metrics to identify overloaded nodes that sit in high risk zones and neighboring nodes that have spare capacity in CPU or Memory and confirm which workloads can be moved safely.<br><br>Phase 2: Execute workload moves or rebalance jobs between hot and cool nodes in planned waves while tracking any changes in response times and error rates during and after migration.<br><br>Phase 3: Recalculate risk scores post distribution and compare the new heatmap and histogram to confirm that pressure has been spread more evenly and that no new hotspot has emerged.<br><br> | - Reduces unplanned downtime risk because overloaded assets are no longer constantly running near capacity which lowers the chance of performance collapse during peaks.<br><br>- Decreases financial exposure to outage related costs since better balanced workloads are less likely to trigger SLA penalties or emergency expansions.<br><br>- Extends the useful life of existing hardware or virtual capacity by using idle resources on cooler nodes instead of immediately purchasing additional capacity.<br><br>- Improves user experience because spreading load more evenly helps keep response times more stable during busy periods across the estate.<br><br> | Formula: Downtime cost avoided = Reduction in downtime hours × Monetary cost per hour<br>Dataset: Peak risk value of {max_risk:.2f} indicates assets that are currently overloaded and can benefit from redistribution.<br> | Histogram right tail and hot spots on the heatmap confirm a small set of nodes carrying disproportionate risk and therefore prime candidates for workload rebalance. |
| Automate scheduled maintenance | Phase 1: Categorize assets into risk bands using the histogram and define maintenance policies that defer changes on high risk systems to windows where impact will be lowest while scheduling routine tasks for low risk systems during standard windows.<br><br>Phase 2: Automate maintenance workflows such as patching configuration checks and health validations so that low risk systems are handled with minimal manual intervention and high risk systems follow stricter controlled procedures.<br><br>Phase 3: Track maintenance success rates incidents and resource usage over time and adjust maintenance schedules and automation coverage based on observed outcomes and updated risk distributions.<br><br> | - Frees up engineering time by allowing low risk systems to be maintained through automated workflows while human effort is focused on the more complex and sensitive high risk assets.<br><br>- Reduces the chance of accidental outages because maintenance on risky systems is handled during carefully planned windows with appropriate safeguards and validation steps.<br><br>- Improves predictability of maintenance effort and cost as teams can align staffing and scheduling patterns with the known risk profile of the environment.<br><br>- Enhances auditability and compliance since automated and risk based maintenance policies create a clear record of when and how each class of asset is serviced.<br><br> | Formula: Maintenance labor savings = Maintenance Hours shifted to automation × Average hourly rate<br>Dataset: {low_risk_assets} low risk systems are suitable for automated maintenance and safe deferral of intensive manual work.<br> | Histogram demonstrates a sizable cohort of low risk assets that can safely take advantage of automated or lower touch maintenance policies without increasing instability. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Implement predictive monitoring | Phase 1: Deploy monitoring rules or models that analyze CPU and Memory trends over time and estimate when an asset’s risk score is likely to move into the high risk band before it actually crosses the threshold.<br><br>Phase 2: Integrate these predictive alerts with incident and change workflows so that teams can act on early warnings through tuning or scaling actions instead of waiting for user impacting incidents.<br><br>Phase 3: Evaluate the accuracy of predictions by comparing expected risk movements versus actual outcomes and refine thresholds and models so that alerts are timely and reliable.<br><br> | - Increases uptime by catching and resolving capacity issues before they escalate into full outages or critical slowdowns that users notice.<br><br>- Reduces the number of fire fighting incidents because more issues are handled proactively as planned changes rather than urgent escalations.<br><br>- Improves confidence in monitoring systems when stakeholders see that alerts correlate closely with real risk and performance conditions.<br><br>- Helps prioritize engineering work by highlighting which assets need attention first based on forecasted risk rather than only current raw utilization levels.<br><br> | Formula: Downtime avoided value = Downtime hours prevented × SLA cost per hour<br>Dataset: {high_risk_assets} critical nodes already cross 85 percent risk and similar nodes approaching that band can be predicted in advance.<br> | Heatmap highlights the risk regions where predictive monitoring should focus and the histogram shows how many assets are close to entering the high risk band. |
| Introduce proactive load balancing | Phase 1: Continuously monitor real time CPU and Memory utilization across nodes and detect when load starts to cluster in a way that pushes certain assets into higher risk zones.<br><br>Phase 2: Use load balancing rules or orchestration tools to shift incoming requests or batch workloads away from stressed assets toward those with more free capacity while keeping latency and locality requirements in mind.<br><br>Phase 3: Review system throughput, error metrics, and new risk scores after balancing changes to confirm that the environment is operating more smoothly and adjust rules where needed.<br><br> | - Prevents systems from reaching saturation by smoothing out spikes across multiple assets which keeps response times more consistent for end users.<br><br>- Increases overall throughput because more of the available capacity is actively used instead of having some nodes overloaded and others idle.<br><br>- Reduces the need for emergency performance fixes since load is automatically redistributed before thresholds are exceeded in a critical way.<br><br>- Provides a repeatable and automated way to manage performance under changing traffic patterns which reduces reliance on manual interventions during busy times.<br><br> | Formula: Performance value = Increase in processed workload at acceptable latency × Value per unit of work<br>Dataset: Highest risk of {max_risk:.2f} is currently linked to nodes with pronounced CPU spikes and uneven load distribution.<br> | Density zones in the heatmap validate where hotspots occur and show how balancing actions should reduce concentration in those regions. |
| Conduct scenario stress testing | Phase 1: Design stress test scenarios that simulate realistic peak usage conditions and apply them to different combinations of assets to see how risk scores behave under controlled load.<br><br>Phase 2: Monitor risk scores, utilization metrics, and response times during each scenario to identify which assets or groups are most vulnerable to overload under specific patterns of demand.<br><br>Phase 3: Tune capacity thresholds, autoscaling policies, and configuration parameters based on test insights and rerun key scenarios to validate that risk levels and performance have improved.<br><br> | - Boosts resilience by revealing weaknesses in capacity planning before they are exposed by live production traffic.<br><br>- Improves confidence in thresholds and policies because their effectiveness is proven through deliberate testing rather than assumed.<br><br>- Enables better prioritization of infrastructure investments by showing which components fail or degrade fastest during stress events.<br><br>- Reduces the chance of unexpected cascading failures since stress tests highlight dependency and bottleneck chains that can be addressed in advance.<br><br> | Formula: Stress related benefit = Increase in SLA adherence during real peaks × Business value of protected transactions<br>Dataset: An average risk of {avg_risk:.2f} suggests generally sustainable load but the histogram tail highlights where targeted stress tests should focus.<br> | Histogram midrange supports calibration of thresholds while the high score tail highlights assets where stress testing will reveal the most about resilience gaps. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate capacity readiness | Phase 1: Prepare simple summaries that explain current capacity risk levels and recent changes in non technical language and distribute them as part of regular service reporting.<br><br>Phase 2: Include clear statements of how much risk has been reduced over time and how these improvements support better uptime and responsiveness for customers.<br><br>Phase 3: Periodically revisit and refresh these communications as new risk assessments are completed so stakeholders always see an up to date picture.<br><br> | - Builds confidence among customers and business stakeholders because they can see that capacity risks are understood measured and actively managed.<br><br>- Reduces anxiety around peak periods and growth events since stakeholders know that capacity has been assessed and reinforced where necessary.<br><br>- Encourages constructive dialogue between technical and business teams by providing a shared language and set of metrics for discussing risk and readiness.<br><br>- Supports stronger relationships with key accounts and internal sponsors who value transparency about operational posture and future plans.<br><br> | Formula: Capacity communication benefit = Improvement in satisfaction scores attributable to perceived readiness × Estimated value per satisfaction point<br>Dataset: Average risk score of {avg_risk:.2f} after optimization provides a simple headline indicator for reporting.<br> | Histogram trend over time should show a shrinking high risk tail which can be used as evidence in capacity readiness communications. |
| Provide customer assurance reports | Phase 1: Incorporate capacity and risk indices from the heatmap and histogram into customer facing or stakeholder reports with clear explanations of what has changed quarter over quarter.<br><br>Phase 2: Visualize the trajectory of improvement for high risk clusters and call out major remediation steps that have been completed on critical systems.<br><br>Phase 3: Validate the content of these reports against audit and monitoring data so that external and internal readers can rely on their accuracy.<br><br> | - Increases trust by showing stakeholders that risk is quantified and regularly reviewed rather than handled informally.<br><br>- Demonstrates accountability for infrastructure health and provides assurance that identified issues lead to documented actions and measurable outcomes.<br><br>- Helps satisfy audit and compliance expectations where evidence of capacity and risk management practices is required.<br><br>- Differentiates the service in the eyes of customers who value transparent operational reporting and continuous improvement.<br><br> | Formula: Assurance value proxy = Retention uplift from improved trust × Revenue or contract value at risk<br>Dataset: {high_risk_assets} assets have been mitigated out of the very high risk band and this shift is visible in the historical heatmaps.<br> | Heatmap color changes across reporting periods underscore the risk reduction story communicated in assurance reports. |
| Improve incident communication strategy | Phase 1: Use risk scores and hotspot locations to identify areas where issues are more likely and prepare early communication templates that can be used when risk indicators rise even before full incidents occur.<br><br>Phase 2: When capacity risk begins to spike inform affected customers or business units about potential impact and outline what mitigation steps are being taken and what alternative options exist.<br><br>Phase 3: After incidents or near misses document what happened how communication was handled and how improved capacity management will reduce similar events in the future.<br><br> | - Reduces customer frustration by avoiding surprises and letting users know early that a risk is being watched and managed.<br><br>- Lowers escalation volumes because clear proactive updates reduce the need for customers to chase support for explanations.<br><br>- Shows maturity in incident handling by linking technical risk management directly with structured communication practices.<br><br>- Enhances long term satisfaction and loyalty as customers observe that problems lead to better monitoring and clearer communication over time.<br><br> | Formula: Escalation cost reduction = Number of escalations avoided × Handling cost per escalation<br>Dataset: High risk zones identified in the heatmap correlate with past support ticket clusters and provide a basis for targeted communication triggers.<br> | Density clusters that align with downtime and ticket patterns highlight where proactive communication about capacity risk will have the most impact on customer perception. |
"""
            }
            render_cio_tables("Capacity Risk Heatmap — CIO Recommendations", cio_heatmap)

    # ======================================================
    # Subtarget 2: Top 10 High-Risk Assets
    # ======================================================
    with st.expander("📌 Top 10 High-Risk Assets"):
        if "risk_score" not in df.columns and {"avg_cpu_utilization", "avg_memory_utilization"} <= set(df.columns):
            df["risk_score"] = (df["avg_cpu_utilization"] * 0.6) + (df["avg_memory_utilization"] * 0.4)

        if "risk_score" in df.columns:
            df = df.copy()
            top10 = df.nlargest(10, "risk_score")[["asset_id", "avg_cpu_utilization", "avg_memory_utilization", "risk_score"]]

            # Graph 1: Bar chart of top 10 risk assets (blue)
            fig3 = px.bar(
                top10,
                x="asset_id",
                y="risk_score",
                text="risk_score",
                title="Top 10 High-Risk Assets by Combined Utilization Score",
                labels={"asset_id": "Asset ID", "risk_score": "Risk Score"}
            )
            fig3.update_traces(texttemplate="%{text:.2f}", textposition="outside", marker_color=PX_SEQ[0])
            st.plotly_chart(fig3, use_container_width=True, key="top10_risk")

            # --- Analysis for Graph 1 (Bar) ---
            top_asset = top10.iloc[0]
            min_asset = top10.iloc[-1]
            avg_top = float(top10["risk_score"].mean())

            st.write(f"""
What this graph is: A bar chart ranking the top ten assets by risk score based on combined CPU and Memory utilization.

X-axis: Asset IDs.
Y-axis: Risk score.
What it shows in your data: The highest risk asset is {top_asset['asset_id']} with a score of {top_asset['risk_score']:.2f} while the lowest risk asset within this top ten group is {min_asset['asset_id']} with a score of {min_asset['risk_score']:.2f}. The average risk across the top ten assets is {avg_top:.2f}. The tallest bars mark the most stressed and fragile systems that are most likely to cause serious incidents if they fail.

Overall: Risk is heavily concentrated in a small number of named assets at the top of the chart. This makes it straightforward to define a concrete remediation backlog that targets these specific systems first before moving on to the broader estate.

How to read it operationally:

Peaks: Prioritize the tallest bars for immediate actions such as scaling, replatforming, or adding redundancy so that they no longer sit at the extreme end of the risk spectrum.

Plateaus: Where several assets share similarly high risk scores, sequence their fixes carefully so that maintenance windows do not overlap and create compounded risk.

Downswings: After remediation and tuning, revisit this chart and confirm that the gap between the highest and lowest bars has narrowed and that overall top ten risk has fallen.

Mix: Map each asset to the business services and customers it supports so that the remediation sequence protects the most critical outcomes first.

Why this matters: Concentrating attention on the few highest risk assets yields a large reduction in outage probability and impact relative to the effort invested and provides a clear story for stakeholders about where work is focused.
""")

            # Graph 2: Scatter plot of CPU vs Memory for Top 10 (blue)
            fig4 = px.scatter(
                top10,
                x="avg_cpu_utilization",
                y="avg_memory_utilization",
                size="risk_score",
                color="risk_score",
                color_continuous_scale="Blues",
                title="CPU vs Memory Utilization among Top 10 High-Risk Assets",
                labels={"avg_cpu_utilization": "CPU Utilization (%)", "avg_memory_utilization": "Memory Utilization (%)"}
            )
            st.plotly_chart(fig4, use_container_width=True, key="top10_scatter")

            # --- Analysis for Graph 2 (Scatter) ---
            diff = (top10["avg_cpu_utilization"] - top10["avg_memory_utilization"]).abs()
            within10 = int((diff <= 10).sum())
            pct_within10 = (within10 / len(top10) * 100) if len(top10) else 0
            max_cpu = float(top10["avg_cpu_utilization"].max())
            max_mem = float(top10["avg_memory_utilization"].max())
            min_cpu = float(top10["avg_cpu_utilization"].min())
            min_mem = float(top10["avg_memory_utilization"].min())

            st.write(f"""
What this graph is: A scatter plot showing CPU versus Memory utilization for the same top ten high risk assets with point size and color reflecting their risk score.

X-axis: CPU utilization (%).
Y-axis: Memory utilization (%).
What it shows in your data: {within10} of {len(top10)} assets which is {pct_within10:.2f}% sit within plus or minus ten percentage points of the diagonal indicating balanced CPU and Memory usage while the remaining assets show a mismatch between CPU and Memory load. CPU utilization across the group ranges from {min_cpu:.2f}% to {max_cpu:.2f}% and Memory utilization ranges from {min_mem:.2f}% to {max_mem:.2f}%. Larger darker bubbles clustered toward the upper right indicate assets where both CPU and Memory are high at the same time and therefore carry the greatest risk.

Overall: The plot reveals whether high risk assets are under pressure from both CPU and Memory or whether one resource tends to be the dominant driver of risk. Balanced points near the diagonal suggest templates that can be reused while unbalanced points show sizing or workload allocation issues that should be corrected.

How to read it operationally:

Peaks: Focus on bubbles near the top right especially those close to ninety to one hundred percent on both axes and treat them as urgent candidates for scaling and offloading to prevent resource exhaustion.

Plateaus: For assets near the diagonal with moderate utilization treat their configurations as good patterns and consider using them as reference builds for similar workloads.

Downswings: After corrective actions expect risky bubbles to shrink and move down and left toward safer utilization zones and reassess whether the group still contains extreme points.

Mix: Combine this scatter view with incident and ticket data to see which points correspond to user visible problems and use that combination to prioritize the next wave of remediation.

Why this matters: Bringing CPU and Memory into a more balanced and sustainable range for the highest risk assets reduces volatility during peaks and directly improves the stability experienced by users.
""")

            # --- CIO tables ---
            cio_top10 = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Prioritize remediation on top 10 risky assets | Phase 1: Use the bar chart to clearly identify the ten assets with the highest risk scores and document the specific capacity or configuration issues affecting each one.<br><br>Phase 2: Develop and implement targeted remediation actions for these ten systems such as hardware upgrades configuration tuning or workload redistribution while coordinating with business owners.<br><br>Phase 3: After changes are implemented recalculate risk scores and compare them with the original top ten to confirm that risk has dropped and to determine whether new assets now appear in the highest risk group.<br><br> | - Concentrates remediation spending on the set of systems that create the largest share of overall risk so that budget delivers maximum impact.<br><br>- Reduces the likelihood of major incidents originating from the worst performing assets which lowers potential outage costs and SLA penalties.<br><br>- Provides a clear and manageable scope of work for engineering teams since they can focus on a short prioritized list instead of the whole environment at once.<br><br>- Creates a strong narrative for management and customers about how limited resources are being invested in the most critical risk reduction opportunities first.<br><br> | Formula: Savings = Number of non critical fixes deferred × Average fix cost<br>Dataset: Top risk score is {top_asset['risk_score']:.2f} and defines the upper bound of initial focus for remediation activities.<br> | Bar chart reveals a concentrated distribution of risk within the top ten assets which supports focused remediation instead of broad upgrades. |
| Avoid blanket upgrades | Phase 1: Use the full risk distribution to explicitly separate high risk assets from low and medium risk systems and document which ones can safely be excluded from immediate upgrade plans.<br><br>Phase 2: Communicate a policy that upgrades and capacity increases are directed first to the high risk group and that low risk assets will only be changed when there is a clear business case or when they move up the risk scale.<br><br>Phase 3: Periodically review risk scores and adjust the list of systems eligible for upgrades so that effort remains focused as conditions change.<br><br> | - Avoids unnecessary capital or operational spending on assets that are already performing well and do not need additional capacity yet.<br><br>- Reduces change related risk by minimizing the number of systems being modified at any given time which lowers the chance of introducing new issues.<br><br>- Frees up engineering time and attention to work on the systems that genuinely need remediation instead of distributing effort across low value changes.<br><br>- Supports more predictable and defensible budgeting because proposed upgrades can be tied directly to measurable risk levels rather than generic refresh cycles.<br><br> | Formula: Cost avoided = (Total assets − 10) × Average upgrade cost for systems not upgraded in the current cycle<br>Dataset: Risk spread in the top ten versus the rest of the fleet validates the use of a narrow targeting approach for upgrades.<br> | Bar chart shows a clear gap between risk scores in the top ten and lower risk systems which supports avoiding blanket upgrades across the estate. |
| Schedule upgrades based on risk severity | Phase 1: Rank all assets in the top risk group by their exact risk scores and map them to business impact so that a risk and impact combined priority order is created.<br><br>Phase 2: Plan and schedule upgrades or remediation work in phases following this priority order to ensure that the most severe and business critical risks are addressed first.<br><br>Phase 3: Reassess risk scores at least quarterly and adjust the schedule to account for newly emerging high risk systems or successfully mitigated ones.<br><br> | - Reduces the chance that a severe capacity related failure occurs while lower impact systems are being improved first which optimizes use of limited maintenance windows.<br><br>- Helps operations and project teams coordinate change calendars so that heavy work is spread out and does not overload resources in a single period.<br><br>- Provides transparency to stakeholders about when specific high risk systems will be addressed supporting better planning and alignment.<br><br>- Supports continuous risk reduction rather than one time campaigns because the schedule is refreshed based on updated measurements.<br><br> | Formula: Risk reduction value = Change in risk score across remediated assets × Cost per risk point as agreed with stakeholders<br>Dataset: Top ten risk scores all sit above {min_asset['risk_score']:.2f} providing a natural cut off for initial phases of the schedule.<br> | Scatter plot confirms how close many of these assets operate to CPU and Memory saturation which underpins the recommended scheduling and prioritization. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Implement redundancy for top assets | Phase 1: Identify which of the top ten high risk assets support critical services that are not currently protected by robust failover or redundancy mechanisms.<br><br>Phase 2: Design and deploy redundant instances or alternative paths for these services such as additional nodes clusters or standby systems that can take over if the primary asset fails.<br><br>Phase 3: Test failover procedures under realistic load conditions and monitor both performance and risk scores to verify that resilience has improved.<br><br> | - Prevents single points of failure at the top of the risk ranking from causing major outages that impact many users at once.<br><br>- Shortens recovery time when a failure does occur because redundant systems can take over quickly without lengthy manual intervention.<br><br>- Increases confidence in the stability of critical services which supports stronger SLAs and fewer emergency escalations.<br><br>- Provides a foundation for further optimization since resilient architectures are more tolerant of tuning and change activity.<br><br> | Formula: Downtime cost reduction = Decrease in outage hours for critical services × SLA rate per hour<br>Dataset: Top risk asset {top_asset['asset_id']} is operating near extreme utilization levels and is a clear candidate for redundancy investment.<br> | Scatter plot identifies which top assets are closest to saturation while the bar chart shows their high overall risk scores which justifies building redundancy first. |
| Enable intelligent auto-scaling | Phase 1: For the top ten assets configure auto scaling rules that respond to sustained high CPU or Memory utilization by adding additional instances or capacity within defined limits.<br><br>Phase 2: Integrate these auto scaling actions with monitoring and logging so that teams can analyze when and why scaling occurs and adjust thresholds to avoid oscillations.<br><br>Phase 3: Assess performance metrics and cost impact over several weeks to ensure that auto scaling is providing smoother performance without overspending on excess capacity.<br><br> | - Helps maintain stable performance during demand spikes by automatically adding capacity around the highest risk systems when they start to struggle.<br><br>- Reduces the need for manual capacity interventions during peak periods which lowers operational load for support engineers.<br><br>- Keeps systems closer to their optimal utilization band since capacity can grow and shrink in response to real demand instead of remaining fixed.<br><br>- Supports better alignment between resource usage and business demand which improves both user experience and cost efficiency.<br><br> | Formula: SLA improvement value = Increase in time spent within SLA thresholds × Estimated revenue or value protected per unit time<br>Dataset: Cluster of points close to full utilization in the scatter and high bars in the risk chart underline the need for dynamic scaling.<br> | Bar chart confirms consistent overuse among the top ranked systems and the scatter plot shows where additional capacity would most improve performance. |
| Enhance monitoring precision | Phase 1: Extend monitoring on the top ten high risk assets to capture more granular metrics such as per process CPU and Memory usage and detailed queue or latency statistics.<br><br>Phase 2: Implement anomaly detection or refined alert rules that distinguish between normal busy behavior and early signs of abnormal strain on these systems.<br><br>Phase 3: Evaluate alert performance over at least thirty days and refine thresholds and detection logic to balance sensitivity with noise reduction.<br><br> | - Reduces unexpected performance dips by catching specific problematic behaviors on high risk assets before they escalate into full incidents.<br><br>- Improves diagnostic speed because detailed metrics make it easier to understand exactly which component or workload is driving the risk score.<br><br>- Lowers operational noise by tuning alerts so that teams spend less time chasing false positives and more time on meaningful signals.<br><br>- Provides richer data for capacity and optimization planning by revealing patterns that are invisible in coarse aggregate metrics.<br><br> | Formula: Alert value = Increase in correctly predicted incidents × Cost avoided per prevented incident<br>Dataset: {len(top10)} high risk cases justify targeted investment in deeper monitoring rather than estate wide changes.<br> | Visual correlation between CPU and Memory pressure in the scatter and high risk rankings in the bar chart supports more precise instrumentation on these assets. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Provide transparent service health updates | Phase 1: Summarize key risk and remediation information for the top ten assets in a format that business stakeholders and customers can easily understand and distribute it as part of regular service updates.<br><br>Phase 2: Highlight completed and planned improvements on these high risk systems and explain how those changes are expected to improve availability and performance.<br><br>Phase 3: Report back on measured outcomes in subsequent updates to show whether risk has reduced and how that correlates with incident and uptime trends.<br><br> | - Increases customer confidence because they can see that the systems most likely to affect them are being actively monitored and improved.<br><br>- Reduces speculation and rumor during periods of instability since transparent updates provide clear information and planned actions.<br><br>- Strengthens relationships with key stakeholders by showing that risk management is handled as a shared concern rather than hidden from view.<br><br>- Supports renewal and growth discussions where demonstrable operational improvements are important for trust.<br><br> | Formula: Satisfaction uplift proxy = Change in CSAT linked to improved communication × Relative importance of affected services<br>Dataset: Improved risk scores for the top ten assets post action can be referenced directly in updates.<br> | Bar chart before and after remediation validates the risk drop that underpins service health communications. |
| Maintain proactive escalation alerts | Phase 1: Configure targeted alerts for the top ten high risk assets so that support and account teams are notified when risk or utilization crosses predefined thresholds.<br><br>Phase 2: Establish a communication protocol for informing affected users or customers when these alerts trigger and outlining planned actions even if service has not yet degraded.<br><br>Phase 3: Review alert history and escalation patterns to see whether proactive engagement is reducing the number of urgent reactive escalations over time.<br><br> | - Enhances trust because customers see that the provider is watching key systems closely and engaging them before serious issues arise.<br><br>- Reduces the volume and intensity of escalations that are initiated by customers who feel uninformed about emerging problems.<br><br>- Provides internal teams with early warning signals so they can coordinate responses with less time pressure and more context.<br><br>- Builds a culture of proactive service management rather than purely reactive firefighting.<br><br> | Formula: Escalation handling savings = Number of escalations avoided × Average handling cost per escalation<br>Dataset: {high_risk_assets} flagged systems across the estate justify targeted alerting to protect sensitive services.<br> | Scatter plot shows real time pressure zones and the risk ranking highlights which assets should have proactive escalation alerts attached. |
| Showcase capacity risk reduction outcomes | Phase 1: Collect quantitative metrics such as changes in risk scores incident counts and uptime for the top risk assets before and after remediation and prepare them for external or internal presentations.<br><br>Phase 2: Share these results with clients and stakeholders in reports or review meetings to demonstrate how investment in capacity management has improved service reliability.<br><br>Phase 3: Use feedback from these sessions to refine which metrics are tracked and how they are presented so that future updates answer stakeholder questions more directly.<br><br> | - Strengthens stakeholder relations by making it clear that capacity and risk work leads to tangible and measured improvements rather than abstract claims.<br><br>- Encourages further collaboration and investment in resilience since stakeholders can see the return from previous optimization efforts.<br><br>- Provides positive evidence for account and relationship managers who must explain operational performance to customers and executives.<br><br>- Helps differentiate the service versus competitors who may not provide such detailed visibility into risk reduction outcomes.<br><br> | Formula: Communication ROI proxy = Value of retained or expanded contracts attributable to demonstrated reliability × Estimated probability of retention uplift<br>Dataset: Risk has been reduced by {max_risk - avg_risk:.2f} points at the high end which is a clear and quantifiable outcome to highlight.<br> | Charts show measurable improvements in both risk scores and utilization patterns which can be showcased as proof points in stakeholder communications. |
"""
            }
            render_cio_tables("Top 10 High-Risk Assets — CIO Recommendations", cio_top10)
