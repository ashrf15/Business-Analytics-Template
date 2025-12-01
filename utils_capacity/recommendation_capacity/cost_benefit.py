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


def cost_benefit(df):

    # ======================================================
    # Subtarget 1: Cost vs Utilization
    # ======================================================
    with st.expander("📌 Monthly Cost vs Utilization"):
        if {"cost_per_month_usd", "avg_cpu_utilization"} <= set(df.columns):
            df = df.copy()
            df["avg_cpu_utilization"] = pd.to_numeric(df["avg_cpu_utilization"], errors="coerce")
            df["cost_per_month_usd"] = pd.to_numeric(df["cost_per_month_usd"], errors="coerce")

            # Graph 1: Scatter plot
            fig1 = px.scatter(
                df,
                x="avg_cpu_utilization",
                y="cost_per_month_usd",
                trendline="ols",
                title="Monthly Cost vs CPU Utilization per Asset",
                labels={"avg_cpu_utilization": "CPU Utilization (%)", "cost_per_month_usd": "Monthly Cost (USD)"}
            )
            fig1.update_traces(marker=dict(color=PX_SEQ[0]))
            st.plotly_chart(fig1, use_container_width=True, key="cost_util_scatter")

            # --- Analysis for Graph 1 (Scatter) ---
            n_assets = len(df)
            avg_cost_sc = float(df["cost_per_month_usd"].mean())
            max_cost_sc = float(df["cost_per_month_usd"].max())
            min_cost_sc = float(df["cost_per_month_usd"].min())
            avg_util_sc = float(df["avg_cpu_utilization"].mean())
            hi_cost_q3 = df["cost_per_month_usd"].quantile(0.75)
            hi_cost_low_util_cnt = int(((df["avg_cpu_utilization"] < 30) & (df["cost_per_month_usd"] >= hi_cost_q3)).sum())

            st.write(f"""
What this graph is: A scatter plot showing monthly infrastructure cost against CPU utilization for each asset.

X-axis: CPU utilization (%).
Y-axis: Monthly cost (USD).
What it shows in your data: Monthly costs range from ${min_cost_sc:,.2f} to ${max_cost_sc:,.2f} with an average of ${avg_cost_sc:,.2f}, while the average CPU utilization across assets is {avg_util_sc:.2f}%.  
There are {hi_cost_low_util_cnt} assets in the upper left area of the chart that combine high monthly cost with low utilization below around 30%, which highlights clear overspend risk on those nodes.

Overall: The cloud of points shows a wide spread of cost for similar utilization levels rather than a tight cost to utilization relationship.  
That pattern indicates that some assets deliver good value at their current utilization, while others consume significant budget without being used effectively, especially in the low utilization high cost region.

How to read it operationally:

Peaks: Focus detailed review on high cost points with low utilization and decide whether to terminate those assets, right size them, or repack their workloads onto cheaper or better utilized platforms.  
Plateaus: Treat the mid band cluster as the current standard sizing baseline and ensure autoscaling or provisioning policies keep new assets close to this area instead of drifting into high cost low use zones.  
Downswings: After optimization work, the dots representing previously inefficient assets should move to the right as utilization increases and in some cases move downwards if cheaper tiers or instance types are adopted.  
Mix: Join this view with cost center tags, environment labels, and workload criticality so that you can safely prioritize non critical high cost low utilization assets before touching essential services.

Why this matters: Misaligned cost to utilization creates direct financial drag because budget is locked in hardware or cloud instances that deliver little value, and correcting that misalignment preserves budget headroom while strengthening confidence that performance spending is under control.
""")

            # Graph 2: Histogram of cost distribution
            fig2 = px.histogram(
                df,
                x="cost_per_month_usd",
                nbins=20,
                title="Distribution of Monthly Infrastructure Cost (USD)",
                labels={"cost_per_month_usd": "Monthly Cost (USD)"}
            )
            fig2.update_traces(marker_color=PX_SEQ[1])
            st.plotly_chart(fig2, use_container_width=True, key="cost_hist")

            # --- Analysis for Graph 2 (Histogram) ---
            avg_cost = float(df["cost_per_month_usd"].mean())
            max_cost = float(df["cost_per_month_usd"].max())
            min_cost = float(df["cost_per_month_usd"].min())
            p90_cost = float(df["cost_per_month_usd"].quantile(0.90))
            high_tail_cnt = int((df["cost_per_month_usd"] >= p90_cost).sum())

            st.write(f"""
What this graph is: A bar style histogram showing how monthly infrastructure costs are distributed across all assets.

X-axis: Monthly cost (USD) grouped into buckets.
Y-axis: Number of assets in each monthly cost bucket.
What it shows in your data: Monthly cost per asset ranges from ${min_cost:,.2f} to ${max_cost:,.2f} with an average of ${avg_cost:,.2f}.  
The top ten percent cost band at and above ${p90_cost:,.2f} contains {high_tail_cnt} assets, which are the small group that drives a disproportionate share of total spend.

Overall: The shape of the histogram reveals how concentrated your infrastructure budget is in a relatively small number of expensive assets compared to the wider base of lower cost nodes.  
That concentration means a focused review on the right hand tail will have far more impact on total OPEX than spreading effort evenly across all assets.

How to read it operationally:

Peaks: Investigate the far right buckets where spend is concentrated, and audit licensing, sizing, placement, and commitment types for those assets before touching the middle of the distribution.  
Plateaus: Treat the broad middle hump of regular costs as the baseline recurring spend that you watch over time for slow drifts upward or downward to confirm that optimizations are sticking.  
Downswings: After targeted optimization or contract changes, you should see the right tail shrink and some assets migrate into lower cost buckets, with the whole distribution shifting gently to the left.  
Mix: Overlay utilization bands or service criticality onto this view to separate assets that are expensive for good reason from those that are both expensive and underused.

Why this matters: Understanding where cost is concentrated enables you to direct optimization effort to the small set of assets that move total operating expenditure the most, rather than chasing minor savings in low impact parts of the estate.
""")

            # Dynamic analysis for CIO tables (kept as-is, uses combined context)
            ineff = df[(df["avg_cpu_utilization"] < 30) & (df["cost_per_month_usd"] > df["cost_per_month_usd"].mean())]
            avg_cost_combo = float(df["cost_per_month_usd"].mean())
            avg_util_combo = float(df["avg_cpu_utilization"].mean())
            ineff_count = len(ineff)

            # CIO Recommendations
            cio_cost_util = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Decommission underutilized high-cost assets | **Phase 1 – Identify:** Identify systems that consistently run below 30 percent utilization over a reasonable time window by using trend data rather than a single snapshot so that you focus on truly underutilized assets instead of temporary dips.<br><br>**Phase 2 – Validate:** Validate workload dependencies and ownership for each candidate system to confirm that no critical services, integrations, or compliance obligations depend on it before any shutdown is planned.<br><br>**Phase 3 – Decommission or Merge:** Decommission idle assets or merge their remaining workloads onto better utilized platforms and update inventory, monitoring, and cost allocation records so that there are no hidden ghost systems left consuming spend. | - Eliminates recurring maintenance and license costs for servers that are no longer required which directly reduces monthly infrastructure and software bills.<br><br>- Reduces the time engineers spend patching, backing up, and monitoring low value assets which frees up capacity for modernization and higher impact work.<br><br>- Shrinks the physical and logical footprint of the estate which lowers complexity in capacity planning and simplifies security and compliance checks.<br><br>- Creates clear and traceable cost savings that can be reported to finance and reinvested into initiatives that improve resilience, automation, or user experience.<br><br> | Formula: Σ (Monthly cost × # inefficient assets). Dataset: {ineff_count} inefficient assets costing above ${avg_cost_combo:,.2f}. | Scatter shows a dense cluster of low-utilization, high-cost assets in the upper-left quadrant. |
| Consolidate workloads across servers | **Phase 1 – Plan Consolidation:** Identify low load workloads that can safely coexist on shared hosts by reviewing performance requirements, data sensitivity, and fault tolerance so that consolidation does not create new risk.<br><br>**Phase 2 – Execute Migration:** Migrate selected workloads to shared or more efficient hosts in a controlled manner and ensure that monitoring, backups, and access controls are updated to reflect the new placement.<br><br>**Phase 3 – Power Down and Review:** Power down redundant systems that no longer host active workloads and review cost and utilization after one month to verify that savings and performance expectations are being met. | - Reduces total operational costs by lowering the number of active servers that require power, cooling, support contracts, and cloud subscription fees.<br><br>- Increases utilization of the remaining servers which means money spent on infrastructure is converted into more useful work instead of idle capacity.<br><br>- Decreases the number of platforms that teams need to manage which simplifies patching, incident response, and configuration management activities.<br><br>- Provides a measurable before and after picture that demonstrates optimization success to stakeholders and strengthens the case for further consolidation rounds.<br><br> | Formula: (Power saved × $/kWh) + (Support hours saved × Rate). Dataset: low CPU assets demonstrate waste potential. | Scatter’s low utilization region with non trivial monthly cost reflects excess cost opportunity. |
| Renegotiate vendor contracts | **Phase 1 – Audit High-Cost Nodes:** Audit the set of highest cost nodes and their associated licenses, reserved instances, and support contracts so that you understand exactly what is being paid for and at what unit rate.<br><br>**Phase 2 – Review Contract Terms:** Review contract duration, commitment levels, and usage patterns against actual demand to uncover mismatches such as over sized reservations or underused premium tiers.<br><br>**Phase 3 – Negotiate and Realign:** Negotiate volume discounts, reshape commitments, or switch to more appropriate tiers and ensure that procurement, finance, and technical teams are aligned on the new structure. | - Lowers fixed costs by aligning contract terms and license levels more closely with actual usage which reduces waste in overpriced or unnecessary entitlements.<br><br>- Improves long term cost predictability because negotiated discounts and right sized reservations create a more stable monthly spend profile.<br><br>- Unlocks budget that can be redirected to optimization, resilience, or innovation instead of being locked into inefficient contract shapes.<br><br>- Strengthens the organization’s negotiating position with vendors by demonstrating clear understanding of usage data and internal optimization efforts.<br><br> | Formula: Δ Rate × Total Subscription Cost. Dataset: Cost distribution is skewed toward a small number of high spend nodes. | Histogram confirms that a few nodes consume a large portion of total spend which justifies focused contract review. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Implement cost-performance monitoring dashboards | **Phase 1 – Integrate Metrics:** Integrate CPU utilization, memory load, and cost metrics into a unified dashboard so that each asset and service can be evaluated on both performance and cost dimensions at the same time.<br><br>**Phase 2 – Configure Alerts:** Configure alerts that trigger when cost rises without a corresponding increase in utilization or when utilization falls while cost remains high so that anomalies are quickly visible.<br><br>**Phase 3 – Act and Iterate:** Use these signals to adjust capacity, resize instances, or move workloads in near real time and iteratively refine thresholds as patterns become clearer. | - Improves resource to cost alignment by making it clear which systems are delivering strong performance relative to their cost and which are not.<br><br>- Shortens the time between overspend conditions appearing and remediation actions being taken which reduces the duration of financial waste.<br><br>- Gives operations and finance teams a shared view of performance and cost which improves cross functional decision making and prioritization.<br><br>- Supports continuous optimization because teams can see the impact of changes quickly and adjust strategies based on real data rather than guesswork.<br><br> | Formula: Δ Avg Utilization × SLA Uptime Benefit. Dataset: average utilization is {avg_util_combo:.2f}%. | Scatter correlation and outliers indicate capacity misalignment that dashboards can surface. |
| Optimize resource allocation policy | **Phase 1 – Define Utilization Targets:** Define target CPU utilization bands such as 50 to 70 percent for steady state operation based on reliability, performance, and cost objectives so that teams know what good looks like.<br><br>**Phase 2 – Enable Auto-Scaling:** Implement auto scaling or automated placement rules that increase or decrease capacity to keep assets within this target band under changing workload conditions.<br><br>**Phase 3 – Review and Adjust:** Review policy performance quarterly by comparing actual utilization and error rates to targets and adjust thresholds or scaling aggressiveness where needed. | - Prevents chronic overprovisioning while still sustaining performance because capacity is automatically trimmed when demand is low and increased when demand grows.<br><br>- Reduces manual intervention for routine scaling activities which frees engineers to focus on complex issues and strategic improvements.<br><br>- Improves predictability of performance as systems operate in a well defined and monitored utilization zone rather than swinging between extremes.<br><br>- Creates a repeatable and transparent policy framework that can be communicated to stakeholders and applied consistently across services.<br><br> | Formula: Reduction% × Monthly cost. Dataset: the gap below and above the desired utilization range suggests a tuning opportunity. | Scatter shows some assets with flat cost profiles beyond efficient utilization levels. |
| Apply FinOps best practices | **Phase 1 – Assign Ownership:** Allocate cost ownership to specific teams or product lines so that every dollar of infrastructure spend has a clear accountable owner who can act on it.<br><br>**Phase 2 – Build Accountability Routines:** Introduce regular reviews where teams examine their cost and utilization metrics, learn from anomalies, and agree actions to optimize spend and performance.<br><br>**Phase 3 – Automate Guardrails:** Implement automated alerts, budgets, and anomaly detection that notify owners when spending or utilization patterns deviate from expected baselines. | - Drives cost transparency and accountability because teams can clearly see which resources they are paying for and how effectively those resources are being used.<br><br>- Encourages proactive optimization behaviour as teams are incentivized to keep their own cost profiles healthy while safeguarding performance for their users.<br><br>- Reduces the frequency and size of unplanned cost spikes since anomalies are detected early and addressed before they grow large.<br><br>- Supports a culture where financial efficiency and technical performance are treated as shared objectives rather than competing concerns.<br><br> | Formula: Δ Cost Anomalies × Avoidance rate. Dataset: high-cost anomalies are visible in the right side of the cost distribution. | Histogram highlights periodic overspend pockets where FinOps guardrails would trigger. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Redirect savings to user-impact initiatives | **Phase 1 – Quantify Savings:** Quantify savings from decommissioning, consolidation, and contract optimization and earmark a portion of these funds specifically for user experience or service quality improvements.<br><br>**Phase 2 – Invest in UX and Reliability:** Direct the recovered budget into initiatives such as performance tuning, interface enhancements, or additional support coverage that have a visible effect on end users.<br><br>**Phase 3 – Measure and Report:** Measure changes in customer satisfaction, NPS, or service ratings after these investments and report back on how infrastructure optimization has funded better user outcomes. | - Boosts customer satisfaction by turning behind the scenes cost reductions into tangible improvements in speed, reliability, or usability that users can feel.<br><br>- Provides a clear narrative that optimization is not just about cutting costs but about reinvesting in better experiences for customers and internal stakeholders.<br><br>- Strengthens support for future optimization work because users and leaders can see direct links between technical efficiencies and service improvements.<br><br>- Creates a virtuous cycle where each round of savings helps fund the next wave of user facing enhancements, steadily lifting service quality.<br><br> | Formula: Savings × ROI on UX programs. Dataset: identified {ineff_count} cost-saving opportunities that can be redirected. | Cost vs Utilization analysis highlights where savings can free budget for user-impact initiatives. |
| Improve transparency via financial reporting | **Phase 1 – Build Cost-Performance Summaries:** Build simple monthly reports that summarize cost, utilization, and key performance indicators in language that non technical stakeholders can easily understand.<br><br>**Phase 2 – Communicate with Users and Leaders:** Share these summaries with business leaders and, where appropriate, with user groups so that they understand how infrastructure is being managed on their behalf.<br><br>**Phase 3 – Gather Feedback and Iterate:** Gather feedback on which metrics and explanations are most helpful and refine the reports to keep them relevant and trustworthy over time. | - Increases customer and stakeholder confidence that the organization is managing infrastructure spend responsibly while protecting performance for critical services.<br><br>- Reduces confusion and speculation about the causes of performance issues because cost and utilization context is available whenever questions arise.<br><br>- Encourages constructive dialogue between IT and business units based on shared data rather than assumptions or incomplete information.<br><br>- Helps set realistic expectations about trade offs between cost, risk, and performance which can improve support for necessary investments.<br><br> | Formula: Complaint reduction × Response time. Dataset: cost tracking combined with utilization patterns enhances visibility for stakeholders. | Scatter and histogram patterns together reflect measurable optimization progress that can be communicated. |
| Reinforce brand sustainability narrative | **Phase 1 – Connect Efficiency to ESG:** Connect infrastructure efficiency gains such as shutting down idle systems or reducing energy use to the organization’s environmental, social, and governance goals in internal and external messaging.<br><br>**Phase 2 – Share Results Publicly:** Share selected optimization results and energy reductions in sustainability reports, customer communications, or marketing materials where appropriate.<br><br>**Phase 3 – Track Engagement and Impact:** Track how customers, partners, and employees respond to these sustainability improvements and adjust the narrative to highlight the aspects they value most. | - Enhances trust and reputation among customers and regulators who expect organizations to manage energy and resource usage responsibly.<br><br>- Differentiates the brand in markets where sustainability is an important decision criterion which can support sales and retention efforts.<br><br>- Motivates internal teams by showing that their optimization work contributes not only to cost goals but also to environmental and social impact objectives.<br><br>- Provides additional justification for efficiency projects because they support both financial outcomes and publicly visible ESG commitments.<br><br> | Formula: Savings mapped to ESG rating uplift or reported emissions reduction. Dataset: movement of assets toward lower cost and more efficient nodes reflects energy efficiency gains. | Distribution shift toward lower average costs over time supports a sustainability and efficiency narrative. |
"""
            }
            render_cio_tables("Cost vs Utilization — CIO Recommendations", cio_cost_util)

    # ======================================================
    # Subtarget 2: ROI Projection on Optimization
    # ======================================================
    with st.expander("📌 ROI Projection on Optimization Initiatives"):
        if {"estimated_cost_savings_usd", "optimization_investment_usd"} <= set(df.columns):
            df = df.copy()
            df["estimated_cost_savings_usd"] = pd.to_numeric(df["estimated_cost_savings_usd"], errors="coerce")
            df["optimization_investment_usd"] = pd.to_numeric(df["optimization_investment_usd"], errors="coerce")
            df["roi"] = (df["estimated_cost_savings_usd"] / df["optimization_investment_usd"].replace(0, np.nan)) * 100

            # Graph 1: Bar chart ROI by Asset
            fig3 = px.bar(
                df,
                x="asset_id" if "asset_id" in df.columns else df.index,
                y="roi",
                title="ROI by Optimization Initiative (%)",
                labels={"asset_id": "Asset ID", "roi": "ROI (%)"}
            )
            fig3.update_traces(texttemplate="%{y:.2f}%", textposition="outside", marker_color=PX_SEQ[0])
            st.plotly_chart(fig3, use_container_width=True, key="roi_bar")

            # --- Analysis for Graph 1 (Bar) ---
            avg_roi_bar = float(df["roi"].mean())
            max_roi_bar = float(df["roi"].max())
            min_roi_bar = float(df["roi"].min())
            above_100 = int((df["roi"] > 100).sum())
            below_50 = int((df["roi"] < 50).sum())

            st.write(f"""
What this graph is: A bar chart ranking the return on investment for each optimization initiative or asset.

X-axis: Optimization initiatives or assets, each represented as a bar.
Y-axis: Return on investment in percent for each initiative.
What it shows in your data: Average ROI across all initiatives is {avg_roi_bar:.2f}%, with a range from {min_roi_bar:.2f}% up to {max_roi_bar:.2f}%.  
There are {above_100} initiatives delivering ROI above 100 percent which indicates very fast payback, and {below_50} initiatives with ROI below 50 percent which are candidates for redesign or retirement.

Overall: The tallest bars show a relatively small group of initiatives that create outsized value compared to their cost while shorter bars at the left tail represent capital that is working less effectively.  
That contrast highlights where to double down and where to pause or redirect investment to improve the overall portfolio return.

How to read it operationally:

Peaks: Expand or replicate the initiatives represented by the tallest bars because they have proven economics and can often be scaled with similar or better returns.  
Plateaus: For the cluster of mid height bars, refine scope, reduce delivery cost, or sharpen benefits so that these initiatives can be lifted closer to top performers.  
Downswings: Retire, redesign, or strictly limit initiatives with ROI below 50 percent and track whether the bar profile shifts upward as low performers are removed or improved.  
Mix: Map each bar to its associated services and customer journeys so that financial wins are aligned with real improvements in service quality rather than isolated cost cutting.

Why this matters: Capital should be directed to the work that generates the highest sustainable return, and this ranking makes it clear where every invested dollar is working hardest for the business and its customers.
""")

            # Graph 2: Histogram ROI distribution
            fig4 = px.histogram(
                df,
                x="roi",
                nbins=20,
                title="Distribution of ROI across Optimization Projects (%)",
                labels={"roi": "Return on Investment (%)"}
            )
            fig4.update_traces(marker_color=PX_SEQ[1])
            st.plotly_chart(fig4, use_container_width=True, key="roi_hist")

            # --- Analysis for Graph 2 (Histogram) ---
            avg_roi = float(df["roi"].mean())
            max_roi = float(df["roi"].max())
            min_roi = float(df["roi"].min())
            high_roi = int((df["roi"] > 100).sum())
            low_roi = int((df["roi"] < 50).sum())

            st.write(f"""
What this graph is: A histogram showing how ROI values are distributed across all optimization initiatives.

X-axis: ROI percentage grouped into value bands.
Y-axis: Number of initiatives that fall into each ROI band.
What it shows in your data: The average ROI is {avg_roi:.2f}%, with individual initiatives ranging from {min_roi:.2f}% up to {max_roi:.2f}%.  
There are {high_roi} initiatives above 100 percent ROI that behave like capital engines and {low_roi} initiatives below 50 percent ROI that act as capital drag.

Overall: The shape of the distribution shows how much of the portfolio sits in high return territory versus low or marginal return territory.  
A right leaning distribution with a visible peak in the higher ROI bands suggests a healthy optimization portfolio, while a left heavy distribution signals that capital is underperforming.

How to read it operationally:

Peaks: A dominant peak toward the right side signals that several initiatives consistently generate strong returns, and these should be scaled, cloned, or used as patterns for new work.  
Plateaus: A wide mid band around average ROI shows steady but improvable performance and should be targeted with better delivery practices or sharper benefit realization.  
Downswings: The left tail represents low ROI initiatives that should be stopped, re scoped, or brought under stricter gating so that they no longer consume disproportionate budget.  
Mix: Segment the distribution by domain, team, or program to see where coaching, standards, or architectural reuse would lift returns the fastest.

Why this matters: The distribution separates capital engines from capital drag so that leadership can tilt investment toward the projects that accelerate business impact and away from those that dilute returns and stakeholder confidence.
""")

            # CIO Recommendations
            cio_roi = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Terminate low-ROI initiatives | **Phase 1 – Identify Underperformers:** Identify projects and initiatives that consistently show ROI below 50 percent by using the ROI data from the bar and histogram views so that decisions are based on evidence and not opinion.<br><br>**Phase 2 – Reallocate Funds:** Decide which of these low ROI efforts should be stopped entirely and which can have scope reduced, then reallocate the freed funds toward higher return initiatives or essential capabilities.<br><br>**Phase 3 – Track New Portfolio ROI:** Track the overall portfolio ROI after reallocation to confirm that capital is now concentrated in higher yield areas and adjust the portfolio mix if results are not improving as expected. | - Redirects resources away from low yield initiatives and into high yield work which increases the overall financial return of the optimization portfolio.<br><br>- Reduces waste on projects that consume time, attention, and budget without delivering sufficient benefit which frees teams to focus on more impactful efforts.<br><br>- Sends a clear signal that ongoing investment is contingent on demonstrated value which encourages better planning and benefit tracking from the start of new initiatives.<br><br>- Improves the credibility of cost optimization programs with executives because decisions to stop work are clearly linked to quantifiable ROI metrics.<br><br> | Formula: Σ Cost saved × % Reallocation. Dataset: {low_roi} projects are underperforming below 50%. | ROI histogram shows a visible left tail of low performing initiatives. |
| Scale successful initiatives | **Phase 1 – Select High Performers:** Identify initiatives with ROI above 100 percent where the benefits have been validated and are repeatable so that you focus scaling on proven patterns rather than one off successes.<br><br>**Phase 2 – Plan and Execute Scale-Up:** Develop scale up plans that extend these high ROI changes to additional services, regions, or customer segments while preserving the key design principles that drove the original returns.<br><br>**Phase 3 – Validate Scaled ROI:** Measure ROI again at the new scale to confirm that returns remain strong and to understand how diminishing returns or new constraints might affect further expansion. | - Maximizes the value of high return initiatives by applying them more broadly, turning a few strong wins into a larger and more sustained stream of savings or revenue protection.<br><br>- Increases confidence that optimization work can deliver repeatable outcomes rather than isolated successes because scaled results are tracked and reported.<br><br>- Builds a library of tested patterns and practices that can be reused in future projects which reduces the risk and cost of future optimization waves.<br><br>- Demonstrates to stakeholders that successful initiatives are not left small and isolated but are deliberately grown to benefit more of the organization.<br><br> | Formula: ROI growth × Expansion value. Dataset: {high_roi} projects currently sit above 100% ROI. | Bar chart highlights the top performing initiatives that are strong candidates for scale up. |
| Review investment strategy | **Phase 1 – Reassess Allocation Mix:** Reassess how capital is currently allocated across different initiative types, domains, and risk levels by using ROI distribution and project cost data.<br><br>**Phase 2 – Prioritize High Impact Areas:** Prioritize future investments toward automation, reliability, and user facing improvements where historical ROI and business impact have been strongest.<br><br>**Phase 3 – Adjust Forecasts and Guardrails:** Update financial forecasts, approval thresholds, and governance criteria so that new investments must meet or exceed target ROI expectations before proceeding. | - Prevents capital from remaining locked into low return areas by systematically shifting investment toward initiatives with stronger financial and strategic outcomes.<br><br>- Aligns optimization spending with the organization’s most important performance and customer experience goals which improves both cost and value realization.<br><br>- Encourages more disciplined business cases for new initiatives since teams know their proposals will be judged against clear ROI thresholds and portfolio needs.<br><br>- Improves planning accuracy for finance teams because forecasts are based on a more realistic mix of high and moderate return initiatives rather than optimistic assumptions.<br><br> | Formula: ROI uplift × Δ Investment. Dataset: mean ROI is {avg_roi:.2f}%, which shows room for improvement in allocation strategy. | ROI distribution reveals the span of returns and where shifting investment could raise the average. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Implement continuous ROI tracking | **Phase 1 – Automate Calculations:** Automate ROI calculations for each initiative by connecting cost, savings, and benefit data into a single model so that values are updated without manual spreadsheet work.<br><br>**Phase 2 – Refresh Dashboards Frequently:** Refresh ROI dashboards on a weekly or monthly basis depending on project cadence so that decision makers always see a current view of performance.<br><br>**Phase 3 – Act on Signals:** Use emerging ROI trends to accelerate, slow, or stop initiatives and to quickly replicate patterns from high performers across the portfolio. | - Improves performance accountability because teams know that their initiatives are being continuously measured on value delivery, not just on activity or completion status.<br><br>- Reduces the lag between performance problems and corrective action since low or dropping ROI is visible early and can be addressed before large amounts of budget are consumed.<br><br>- Increases the likelihood that optimization work stays aligned with changing business priorities because ROI signals reveal when certain areas are no longer providing sufficient benefit.<br><br>- Supports more agile portfolio management where resources can be reallocated based on up to date information rather than annual reviews alone.<br><br> | Formula: Δ ROI × #Projects. Dataset: ROI range of {min_roi:.2f}% to {max_roi:.2f}% indicates significant variance worth monitoring continuously. | Histogram shows wide performance variance that continuous tracking can help manage. |
| Reinvest savings into performance tools | **Phase 1 – Identify Savings Pool:** Identify savings generated by high ROI initiatives and create a dedicated pool of funds to invest in performance tooling such as AIOps, observability, or automation platforms.<br><br>**Phase 2 – Deploy Tools Strategically:** Deploy these tools into the most critical or noisy parts of the environment where improved detection and automation will remove recurring performance issues and toil.<br><br>**Phase 3 – Measure Tool Impact:** Measure how the new tools change incident rates, mean time to resolve, and stability, and include this impact in future ROI analyses. | - Enhances predictive capability by using savings from prior optimizations to fund advanced tooling that can detect and prevent performance problems before they affect users.<br><br>- Reduces manual workload on operations teams as more issues are detected, triaged, or fixed automatically which improves overall engineering productivity.<br><br>- Raises the baseline reliability of services since better monitoring and automation reduces the frequency and impact of performance incidents.<br><br>- Creates a reinforcing loop where early optimization projects make it easier and cheaper to deliver future improvements by strengthening the platform and its observability.<br><br> | Formula: Savings × Tool ROI. Dataset: {high_roi} high yield cases could provide enough savings to fund performance tooling. | Bar chart confirms a set of consistently high ROI initiatives that can be used as funding sources. |
| Optimize resource deployment timing | **Phase 1 – Analyse Timing Patterns:** Analyse historical ROI and benefit realization to identify periods or conditions where investments have produced better returns such as certain quarters, demand cycles, or technology waves.<br><br>**Phase 2 – Align New Investments:** Time new resource deployments and optimization efforts to align with these high impact periods so that benefits accrue faster and are easier to capture.<br><br>**Phase 3 – Reduce Idle Capital:** Monitor for situations where capital is deployed far in advance of benefit realization and adjust future plans to minimize the amount of idle or underutilized investment. | - Improves project velocity in terms of realized value because work is scheduled when it is most likely to produce strong and timely returns rather than at arbitrary times.<br><br>- Reduces wasted capital tied up in early or poorly timed investments that do not produce benefits until much later than planned.<br><br>- Aligns optimization cycles with known business events or seasonal demand patterns which makes improvements more visible and relevant to stakeholders.<br><br>- Supports more precise financial planning because cash outflows for investments and inflows from savings or revenue protection occur in closer alignment.<br><br> | Formula: Δ ROI × Duration savings. Dataset: ROI spikes that align with specific periods in the charts indicate timing effects that can be exploited. | Chart reveals cyclical or clustered ROI patterns that suggest better deployment timing. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate ROI outcomes to stakeholders | **Phase 1 – Build Clear ROI Reports:** Build simple quarterly ROI reports that highlight which initiatives delivered the highest returns, how much was saved or protected, and how those savings were used.<br><br>**Phase 2 – Highlight Reinvestment Impact:** Clearly show how high ROI initiatives enabled reinvestment in reliability, user experience, or innovation so that stakeholders see a direct link between optimization and business value.<br><br>**Phase 3 – Capture Feedback and Expectations:** Collect feedback from business leaders and key users about which outcomes matter most and use that input to guide future optimization priorities. | - Builds transparency and stakeholder confidence because leaders can see concrete financial and operational results instead of abstract claims about optimization benefits.<br><br>- Reinforces the perception that the optimization program is disciplined and value driven which makes it easier to secure support for future waves of work.<br><br>- Helps align expectations around what good looks like for ROI and timelines which reduces friction when some initiatives must be stopped or reshaped.<br><br>- Encourages collaborative ownership of value outcomes since both technical and business teams are involved in reviewing and celebrating results.<br><br> | Formula: CSAT uplift × ROI visibility factor. Dataset: initiatives with ROI above 100% demonstrate visible value creation worth communicating. | Charts show tangible improvement metrics that can be communicated in stakeholder forums. |
| Use ROI success stories for marketing | **Phase 1 – Develop Case Studies:** Develop anonymized case studies that describe high ROI optimization stories in terms of the business problems solved, actions taken, and quantifiable outcomes achieved.<br><br>**Phase 2 – Share Success in Market Channels:** Share these stories through appropriate marketing, sales, and recruitment channels to demonstrate operational excellence and efficiency to customers and partners.<br><br>**Phase 3 – Measure Engagement:** Track how prospects, customers, and potential hires engage with these stories and refine the narrative to emphasize the aspects that resonate most. | - Enhances brand perception by showing that the organization manages its technology and cost base intelligently while still improving service quality.<br><br>- Supports sales and account management teams with concrete examples they can use to reassure customers that the platform is efficient, stable, and continuously improving.<br><br>- Strengthens the employer brand by demonstrating that teams work on meaningful optimization projects that deliver measurable impact rather than purely reactive tasks.<br><br>- Encourages internal pride and motivation when teams see their work recognised and celebrated externally as part of the organization’s success story.<br><br> | Formula: Engagement rate × ROI improvement. Dataset: average ROI of {avg_roi:.2f}% across initiatives provides a strong foundation for positive case studies. | Bar data validates strong project outcomes that can be turned into external success stories. |
| Link ROI to customer-impact KPIs | **Phase 1 – Map ROI to KPIs:** Map each high ROI initiative to specific customer impact KPIs such as response time, availability, error rate, or satisfaction so that the link between financial return and user benefit is clear.<br><br>**Phase 2 – Measure Operational Changes:** Measure how these KPIs change as initiatives go live and stabilise, and attribute part of the improvement to the optimization work where evidence supports that conclusion.<br><br>**Phase 3 – Publish Combined Metrics:** Publish combined views that show ROI and associated KPI improvements side by side for key initiatives to reinforce the connection between cost efficiency and service quality. | - Converts internal ROI improvements into stories that resonate with customers and users because they can see how optimization leads directly to better experiences for them.<br><br>- Helps prevent optimization from being perceived as pure cost cutting by clearly demonstrating that the aim is to improve reliability, performance, and satisfaction at the same time.<br><br>- Gives leadership a more balanced scorecard when deciding which initiatives to pursue since they can weigh financial return and user impact together.<br><br>- Encourages teams to design optimization work in ways that explicitly consider downstream customer outcomes rather than focusing only on internal metrics.<br><br> | Formula: Δ ROI × Δ Response Time or related KPI improvements. Dataset: {high_roi} initiatives show strong financial results that can be paired with service KPI gains. | Visual ROI trends provide the financial half of the story that can be linked to customer-impact KPIs for a complete narrative. |
"""
            }
            render_cio_tables("ROI Projection — CIO Recommendations", cio_roi)
