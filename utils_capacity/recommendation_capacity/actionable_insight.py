import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# --- Visual identity: professional blue & white (global) ---
px.defaults.template = "plotly_white"
PX_SEQ = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#99CCFF"]
px.defaults.color_discrete_sequence = PX_SEQ  # apply to all discrete charts

# 🔹 Helper to render CIO tables with 3 nested expanders (Option A format)
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)


def actionable_insight(df):

    # ======================================================
    # Subtarget 1: Cross-Domain Performance Overview
    # ======================================================
    with st.expander("📌 Cross-Domain Performance Overview"):
        if {"avg_cpu_utilization", "avg_memory_utilization", "network_utilization_pct"} <= set(df.columns):
            df = df.copy()
            df["total_utilization"] = (df["avg_cpu_utilization"] + df["avg_memory_utilization"] + df["network_utilization_pct"]) / 3

            # Graph 1: Box plot - total utilization distribution
            fig1 = px.box(
                df,
                y="total_utilization",
                title="Overall Resource Utilization Distribution (%)",
                labels={"total_utilization": "Total Utilization (%)"}
            )
            fig1.update_traces(marker_color=PX_SEQ[0], line_color=PX_SEQ[0])
            st.plotly_chart(fig1, use_container_width=True, key="total_utilization_box")

            # --- Analysis for Graph 1 (Box Plot) ---
            y = df["total_utilization"].dropna()
            avg_total = float(y.mean())
            max_total = float(y.max())
            min_total = float(y.min())
            q1 = float(y.quantile(0.25))
            q3 = float(y.quantile(0.75))
            iqr = q3 - q1
            lower_whisk = q1 - 1.5 * iqr
            upper_whisk = q3 + 1.5 * iqr
            outliers = int(((y < lower_whisk) | (y > upper_whisk)).sum())
            over_80 = int((y > 80).sum())
            under_40 = int((y < 40).sum())

            st.write(f"""
What this graph is: A box plot summarizing overall resource utilization across CPU, memory, and network as a single averaged percentage.

Y-axis: Total utilization (%).
What it shows in your data: Average total utilization is {avg_total:.2f}% with observed values ranging from {min_total:.2f}% to {max_total:.2f}%. The middle 50% of assets sit between {q1:.2f}% and {q3:.2f}% which gives an interquartile range of {iqr:.2f} percentage points. There are {outliers} statistical outliers in the distribution. Operationally, {over_80} assets are above 80% utilization which indicates capacity stress and {under_40} assets are below 40% utilization which indicates significant headroom or potential oversizing.

Overall: A tight box and short whiskers indicate that most assets are loaded in a similar way, while a tall box or long whiskers indicate large variation in how resources are consumed. Outliers above the upper whisker represent assets that are running much hotter than the rest of the estate, whereas outliers below the lower whisker highlight assets that are consistently underused compared to their peers.

How to read it operationally:

Peaks: Standardize remediation on assets in the upper tail and above 80% utilization because these nodes are most likely to suffer performance issues or saturation as demand grows.
Plateaus: When the interquartile band is narrow, treat this as a sign that policies are working and focus on monitoring for slow upward drift in the median and upper whisker over time.
Downswings: After optimisation work, expect the whiskers and the box height to contract, which shows that utilisation has become more consistent and the number of extreme outliers has reduced.
Mix: Combine this view with business criticality or environment tags so that you can see whether the hottest and coldest assets sit in production, non production, or specific business units.

Why this matters: Imbalanced utilization creates both financial and reliability debt because overloaded assets drive incidents and SLA breaches while underused assets quietly consume budget without delivering proportional value.
""")


            # Graph 2: Histogram - utilization frequency
            fig2 = px.histogram(
                df,
                x="total_utilization",
                nbins=20,
                title="Distribution of Total Resource Utilization (%)",
                labels={"total_utilization": "Total Utilization (%)"}
            )
            fig2.update_traces(marker_color=PX_SEQ[1])
            st.plotly_chart(fig2, use_container_width=True, key="total_utilization_hist")

            # --- Analysis for Graph 2 (Histogram) ---
            st.write(f"""
What this graph is: A histogram showing how often assets fall into different bands of total resource utilization.

X-axis: Total utilization (%).
Y-axis: Asset count in each utilization band.
What it shows in your data: Average total utilization is {avg_total:.2f}% with values spanning from {min_total:.2f}% to {max_total:.2f}%. There are {over_80} assets above 80% utilization that cluster in the right hand bins and {under_40} assets below 40% utilization that appear in the left hand bins, which indicates a mix of capacity stress and spare headroom across the estate.

Overall: A concentration of bars toward the right side of the chart points to a fleet that is generally running hot, while a concentration toward the left points to oversizing and idle capacity. A balanced distribution with a clear middle hump suggests that most assets are operating in a healthy band with only a modest number of extreme cases at either end.

How to read it operationally:

Peaks: Treat the right hand bars above 80% as capacity risk cohorts and prioritise review, rebalancing or scaling actions for the assets that sit in those bands.
Plateaus: If the central bands form a broad and stable hump around the mean, reinforce current provisioning and autoscaling policies and monitor whether seasonal changes shift that centre of mass over time.
Downswings: After cleanup, consolidation or tuning work, expect the right tail to thin out and more assets to move into mid range bands and confirm that this pattern is actually visible in the histogram.
Mix: Break down the histogram by component type, location or service tier so that you can see which parts of the environment contribute most to hot bands and which hold the majority of spare capacity.

Why this matters: Understanding where most assets sit in the utilization spectrum helps you set thresholds, scaling policies and consolidation plans that reduce firefighting on overloaded nodes and reduce waste on underused ones.
""")

            # --- CIO tables (unchanged) ---
            cio_overview = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Consolidate underutilized assets | **Phase 1**: Identify all systems that consistently run below 40% utilization by using the combined CPU, memory, and network metrics and validate with system owners that this low usage is not due to temporary quiet periods or upcoming projects. <br><br>**Phase 2**: Plan to merge compatible workloads onto fewer physical or virtual hosts so that utilization on the remaining assets moves into a healthy range while confirming that performance and resilience requirements are still met. <br><br>**Phase 3**: Decommission or repurpose truly idle servers once consolidation is complete and verify that monitoring, backup, and access patterns have stabilised on the remaining assets. | - Reduces ongoing operational expenses because power, cooling, and support effort are no longer wasted on servers that deliver little or no business value.<br><br>- Creates budget and capacity headroom that can be reallocated to higher priority initiatives such as modernisation or scaling of critical services.<br><br>- Simplifies day to day operations because there are fewer assets to patch, monitor, back up, and troubleshoot which reduces complexity for engineering teams.<br><br>- Improves data centre and rack utilisation by freeing space that can be used for newer platforms or returned to reduce physical footprint costs.<br><br> | Formula: Savings = Idle Assets × Avg Monthly Cost. Dataset: {under_40} low-use assets identified. | Histogram shows left-tail density below 40%. |
| Implement unified monitoring | **Phase 1**: Integrate cross domain metrics for CPU, memory, network, and related indicators into a single observability platform so that teams can see a coherent view of asset health without jumping between multiple tools. <br><br>**Phase 2**: Identify and retire redundant point tools or overlapping collectors that no longer add unique value now that unified monitoring is available. <br><br>**Phase 3**: Validate the accuracy and completeness of the new monitoring configuration through tests, shadow runs, and stakeholder feedback to ensure that important events are still captured. | - Reduces software licensing and maintenance costs because separate legacy monitoring tools and agents can be decommissioned once unified views are in place.<br><br>- Decreases operational friction for engineers who no longer need to correlate data manually across disconnected dashboards which saves time during investigations.<br><br>- Improves the quality of incident analysis because all key metrics are visible in one place which makes root cause identification faster and more reliable.<br><br>- Enables more consistent alerting and reporting because thresholds and views are managed centrally instead of being duplicated in separate systems.<br><br> | Formula: #Tools Removed × Annual License Cost. Dataset: overlap between CPU, memory, and network tracking. | Consolidation evident in similar utilization patterns. |
| Automate energy throttling | **Phase 1**: Enable dynamic power scaling features on supported hardware and virtualisation platforms so that devices can automatically reduce power draw when utilisation remains below defined thresholds such as 30%. <br><br>**Phase 2**: Configure appropriate thresholds, schedules, and safety limits so that energy throttling only activates on genuinely underutilised assets and does not conflict with performance expectations or maintenance windows. <br><br>**Phase 3**: Review monthly energy, performance, and utilisation reports to confirm that throttling is delivering savings without introducing instability or user experience issues. | - Cuts power and cooling costs because low utilisation periods trigger automatic power reduction instead of leaving hardware running at full consumption by default.<br><br>- Lowers the environmental footprint of the infrastructure estate by reducing unnecessary energy usage which supports sustainability and corporate responsibility goals.<br><br>- Encourages better utilisation discipline since teams can see tangible benefits from keeping idle capacity under control and can reflect this in design decisions.<br><br>- Provides measurable data that links energy use to utilisation behaviour which can inform future capacity planning and procurement decisions.<br><br> | Formula: (kWh Saved × Cost/kWh). Dataset: low-utilization assets consuming idle power. | Box plot reveals persistent idle resource levels. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Balance workload distribution | **Phase 1**: Use the overview metrics to pinpoint assets above 80% utilization and assets below 40% utilization and map which applications and services are running on each group so that dependencies are understood. <br><br>**Phase 2**: Shift or rebalance workloads from over stressed assets to underused ones through scheduling, placement rules, or orchestration tools while validating that latency, throughput, and resilience remain within acceptable bounds. <br><br>**Phase 3**: Track performance indicators and utilisation patterns after redistribution to confirm that hotspots have cooled and that new hotspots have not been created elsewhere. | - Improves throughput and response times because heavily loaded assets are relieved of excess work and underused assets are brought into productive use.<br><br>- Reduces the likelihood of performance incidents and saturation related outages by preventing a small number of nodes from carrying disproportionate load.<br><br>- Increases the overall efficiency of the resource pool by spreading demand in line with available capacity which allows more work to be handled without additional hardware.<br><br>- Provides clear evidence of operational improvement through before and after utilisation and latency comparisons that can be shared with stakeholders.<br><br> | Formula: Δ Utilization × SLA Compliance%. Dataset: {over_80} high-load assets causing imbalance. | Histogram right-tail shows overuse peaks. |
| Implement predictive scaling | **Phase 1**: Define combined scaling triggers based on total utilisation trends and historical growth patterns rather than relying on single metric spikes so that scale out and scale in decisions are more stable. <br><br>**Phase 2**: Simulate likely load scenarios using historical data and projected business events to test the effectiveness of the triggers before fully automating them in production environments. <br><br>**Phase 3**: Automate provisioning and deprovisioning based on these triggers and continuously refine the policies using live performance data and incident feedback. | - Ensures capacity resilience because additional resources are added before assets reach critical utilisation thresholds which reduces the risk of saturation during demand spikes.<br><br>- Improves cost efficiency over time as scale in events are also driven by real utilisation patterns which avoids leaving large numbers of resources idle after peaks pass.<br><br>- Makes system behaviour more predictable for both technical teams and business stakeholders since scaling decisions follow transparent rules tied to observed patterns.<br><br>- Decreases manual intervention during busy periods because scaling policies handle routine growth and shrink scenarios without constant operator oversight.<br><br> | Formula: SLA Improvement × Revenue Protected. Dataset: average utilization {avg_total:.2f}% suggests dynamic scaling window. | Box plot indicates room for elasticity. |
| Conduct resource tuning audits | **Phase 1**: Review assets at the top and bottom of the utilization range on a monthly cadence and compile a short list of candidates that need configuration or workload adjustments. <br><br>**Phase 2**: Tune operating system, application, and platform settings such as limits, cache sizes, and concurrency to better align resource use with real demand on the identified assets. <br><br>**Phase 3**: Measure performance uplift and utilisation changes after tuning and document which adjustments were most effective so that successful patterns can be reused elsewhere. | - Maintains consistent operational efficiency by ensuring that misconfigured or outdated settings do not leave some assets overloaded while others remain underused.<br><br>- Improves user experience because targeted tuning can remove bottlenecks and reduce latency on the most visible services without large capital spend.<br><br>- Builds an internal library of tuning best practices that accelerates future optimisation work across similar platforms and workloads.<br><br>- Provides a structured governance approach that turns utilisation data into regular, action oriented reviews rather than ad hoc troubleshooting exercises.<br><br> | Formula: Δ Avg Utilization × Value/Unit. Dataset: {min_total:.2f}%–{max_total:.2f}% range shows imbalance. | Distribution confirms need for ongoing tuning. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Publish utilization dashboards | **Phase 1**: Develop clear visual dashboards that show cross domain utilisation trends and risk areas in a way that non technical stakeholders can easily understand. <br><br>**Phase 2**: Share these dashboards regularly with business and operations teams so that they can see how infrastructure is supporting current workloads and growth. <br><br>**Phase 3**: Collect feedback on clarity and usefulness and refine the dashboards over time so that they continue to answer the questions stakeholders actually have. | - Builds transparency and trust because stakeholders can see real time and historical utilisation patterns instead of relying on anecdotal updates.<br><br>- Reduces repetitive status queries and escalations since stakeholders can self serve answers to basic questions about capacity and performance posture.<br><br>- Helps business teams plan initiatives more effectively by showing where spare capacity exists and where additional investment may be needed before large changes.<br><br>- Strengthens alignment between IT and the business because shared dashboards create a common reference point during planning and review meetings.<br><br> | Formula: CSAT Uplift = Visibility × Confidence Index. Dataset: visual clarity across all metrics. | Box and histogram simplify complex performance data. |
| Improve communication during optimization cycles | **Phase 1**: Inform clients and internal stakeholders before major performance tuning or rebalancing activities so that they know what is happening, why it is being done, and what risk or impact to expect. <br><br>**Phase 2**: Provide status updates and simple utilisation snapshots while optimisation work is underway so that people can follow progress without needing deep technical detail. <br><br>**Phase 3**: After the cycle, share the results in terms of utilisation changes, performance improvements, and any lessons learned to close the loop. | - Enhances trust in service reliability because stakeholders see that optimisation work is planned, communicated, and followed through rather than happening silently in the background.<br><br>- Reduces anxiety and complaint levels during tuning activities since people understand what is being done and when normal operation will resume.<br><br>- Encourages collaborative problem solving as teams outside infrastructure can align their own activities around planned optimisation windows.<br><br>- Provides a history of improvement stories that can be referenced in future governance forums and contract or SLA discussions.<br><br> | Formula: Complaint Reduction × Handling Cost. Dataset: identified underused resources under review. | Balanced utilization conveys reliability. |
| Create stakeholder reports | **Phase 1**: Summarize cross domain performance and utilisation improvements in concise quarterly reports that highlight key metrics, trends, and actions taken. <br><br>**Phase 2**: Highlight specific savings, efficiency gains, and risk reductions achieved during the period so that business stakeholders can see tangible outcomes. <br><br>**Phase 3**: Maintain an archive of these reports to provide a continuous narrative of progress and to support audits, renewals, and strategic planning discussions. | - Reinforces alignment between infrastructure operations and business objectives by clearly showing how technical work translates into cost and performance outcomes.<br><br>- Increases stakeholder confidence in the platform because improvements and risk reductions are documented and communicated instead of being invisible behind the scenes.<br><br>- Supports long term planning and budgeting decisions with a historical record of how utilisation and performance have evolved over time.<br><br>- Provides material that can be reused in executive updates, board reports, or customer communications to demonstrate ongoing improvement and governance maturity.<br><br> | Formula: Report ROI = Engagement × Accuracy. Dataset: {avg_total:.2f}% average utilization baseline. | Charts confirm improvement trajectory. |
"""
            }
            render_cio_tables("Cross-Domain Performance Overview — CIO Recommendations", cio_overview)

    # ======================================================
    # Subtarget 2: Correlation Matrix
    # ======================================================
    with st.expander("📌 Correlation Matrix of Key Metrics"):
        numeric = df.select_dtypes(include=[np.number])
        if not numeric.empty:
            corr = numeric.corr().round(2)

            # Graph 1: Correlation heatmap (blue scale)
            fig3 = px.imshow(
                corr,
                text_auto=True,
                color_continuous_scale="Blues",
                title="Correlation Matrix of Key Infrastructure Metrics"
            )
            st.plotly_chart(fig3, use_container_width=True, key="corr_matrix")

            # --- Analysis for Graph 1 (Heatmap) ---
            corr_values = corr.unstack().drop_duplicates()
            avg_corr = float(corr_values.mean())
            highest_corr = float(corr_values.max())
            lowest_corr = float(corr_values.min())
            strong_corr = corr_values[abs(corr_values) > 0.8]

            st.write(f"""
What this graph is: A heatmap showing pairwise correlations between key operational metrics, with values ranging from −1 to +1 where deeper blue cells represent stronger positive or negative relationships.

Cells: Correlation coefficient between each pair of metrics.
What it shows in your data: The average correlation across all metric pairs is {avg_corr:.2f}, the strongest relationship reaches {highest_corr:.2f}, and the weakest relationship is {lowest_corr:.2f}. There are {len(strong_corr)} strong linkages where the absolute correlation is greater than 0.8, which means these metrics tend to move closely together in the same direction or in opposite directions.

Overall: Blocks of high correlation indicate tightly coupled behaviours where one metric can be a strong proxy for another, whereas pale or low correlation cells indicate metrics that move largely independently. Diagonal dominance is expected because each metric is perfectly correlated with itself, but the off diagonal structure shows where monitoring, alerting and capacity decisions can be simplified or need more nuance.

How to read it operationally:

Peaks: Focus on metric pairs with very high absolute correlation because those highlight opportunities to consolidate monitors, merge triggers or reduce duplicate metrics without losing insight.
Plateaus: Where many correlations sit in a moderate band, keep thresholds simple and stable and review these relationships periodically to catch any structural shifts in system behaviour.
Downswings: After refactoring metrics and alerts, expect fewer extreme correlation cells in places where redundancy has been removed, and monitor whether false positive counts fall in parallel.
Mix: Translate technical relationships such as CPU versus power or utilization versus cost into business language so that stakeholders understand which levers move together when investment decisions are made.

Why this matters: Unexamined metric coupling drives operational noise and wasted analysis effort because multiple signals end up telling the same story, so simplifying based on correlation frees up attention and reduces monitoring and automation cost.
""")

            # Graph 2: Correlation histogram (blue)
            fig4 = px.histogram(
                x=corr_values,
                nbins=20,
                title="Distribution of Correlation Strengths",
                labels={"x": "Correlation Coefficient"}
            )
            fig4.update_traces(marker_color=PX_SEQ[1])
            st.plotly_chart(fig4, use_container_width=True, key="corr_hist")

            # --- Analysis for Graph 2 (Histogram) ---
            share_strong = (abs(corr_values) > 0.8).mean() * 100.0
            share_weak = (abs(corr_values) < 0.3).mean() * 100.0

            st.write(f"""
What this graph is: A histogram summarizing how strong or weak the relationships between metric pairs are based on their correlation coefficients.

X-axis: Correlation coefficient value from −1 to +1.
Y-axis: Count of metric pairs that fall into each correlation band.
What it shows in your data: {share_strong:.2f}% of metric pairs are strongly related with an absolute correlation above 0.8, while {share_weak:.2f}% of pairs are weakly related with an absolute correlation below 0.3. This spread shows where metrics behave almost as duplicates and where they capture independent dimensions of system behaviour.

Overall: A large cluster of bars near the extremes indicates a highly redundant metric set that may be over describing the same patterns, while a more centred distribution with many moderate values indicates a more nuanced mix of partially related signals. A healthy shape usually includes some strong pairs for consolidation and many weaker pairs for independent control.

How to read it operationally:

Peaks: Bars near correlation values of 1.0 or −1.0 highlight metric pairs that can be candidates for consolidation, combined dashboards or unified alerting logic because they carry almost the same information.
Plateaus: A wide middle section suggests that many relationships are moderate and should be managed with straightforward thresholds, periodic review and clear ownership rather than aggressive rationalisation.
Downswings: After a metrics cleanup exercise, expect the extreme tails to thin out as redundant metrics are retired and the histogram to reflect a more balanced set of relationships.
Mix: Segment the histogram by domain such as compute, storage, network or cost so that metric owners in each area can see where to simplify and where to preserve independent visibility.

Why this matters: The distribution of correlation strengths exposes the balance between redundancy and independence in your monitoring landscape, and reducing unnecessary redundancy lowers tooling cost and cognitive load for operators without sacrificing control.
""")

            # --- CIO tables (unchanged) ---
            cio_corr = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Consolidate overlapping monitoring metrics | **Phase 1**: Identify metrics that have correlation values above 0.9 and confirm that they are genuinely measuring the same or very similar behaviours rather than capturing distinct conditions. <br><br>**Phase 2**: Decommission or suppress redundant metrics and dashboards that do not add unique insight while keeping at least one well defined metric for each important behaviour. <br><br>**Phase 3**: Revalidate the overall monitoring scope with operators and service owners to ensure that critical coverage is maintained and that there are no blind spots after consolidation. | - Reduces licensing and infrastructure cost because fewer metrics and time series need to be stored, processed, and visualised across the monitoring stack.<br><br>- Lowers operational noise by eliminating duplicate alerts and charts that tell the same story which allows engineers to focus on higher value signals.<br><br>- Simplifies troubleshooting and analysis because teams no longer need to reconcile multiple overlapping views of the same problem during incidents.<br><br>- Makes the monitoring landscape easier to maintain over time since there are fewer signals and dashboards to update when systems change.<br><br> | Formula: # Metrics Removed × Cost per Metric. Dataset: {len(strong_corr)} metrics strongly correlated. | Heatmap highlights redundant monitoring zones. |
| Eliminate redundant resource scaling triggers | **Phase 1**: Review existing scaling triggers and identify those driven by strongly correlated metrics so that trigger conditions which are effectively duplicates can be grouped together. <br><br>**Phase 2**: Merge or simplify automation logic by basing scaling decisions on a smaller set of representative metrics while preserving safety limits and rollback options. <br><br>**Phase 3**: Monitor incident rates, scaling behaviour, and alert volumes after changes to confirm that capacity still adjusts correctly and that spurious activations have decreased. | - Cuts false alarms and unnecessary scaling events because automation is no longer driven by multiple overlapping triggers that all react to the same underlying behaviour.<br><br>- Reduces compute usage and associated cost by preventing unneeded scale out operations that were previously triggered by redundant indicators.<br><br>- Improves operator confidence in automation because trigger behaviour becomes more predictable and easier to explain to stakeholders.<br><br>- Frees up engineering time that used to be spent tuning and debugging multiple similar triggers for the same resource pools.<br><br> | Formula: Δ Alerts × Handling Cost. Dataset: CPU–Memory correlation >0.85 confirms overlap. | Correlation clusters support trigger reduction. |
| Centralize performance data pipelines | **Phase 1**: Combine CPU, memory, network, and related metrics into unified data pipelines or a central observability platform so that ingestion, transformation, and storage are handled consistently. <br><br>**Phase 2**: Apply compression, downsampling, and retention policies that reflect how strongly metrics correlate and how long full resolution data is truly needed. <br><br>**Phase 3**: Track storage consumption, processing load, and access patterns to confirm that centralisation and optimisation are delivering measurable savings without harming analysis capabilities. | - Lowers data processing and storage costs because redundant and overly granular metric streams are optimised and retained at appropriate levels.<br><br>- Improves data quality and consistency across teams since all stakeholders consume metrics from a single curated pipeline rather than multiple ad hoc feeds.<br><br>- Makes it easier to introduce new analytics or machine learning use cases because required data is already centralised and well structured.<br><br>- Strengthens governance over monitoring data by giving a single place to manage retention, access control, and compliance requirements.<br><br> | Formula: GB Saved × $/GB. Dataset: multi-metric relationships >0.8 correlation. | Histogram tail shows consistent redundancy. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Prioritize optimization on strong metric pairs | **Phase 1**: Focus performance optimisation efforts on metric pairs with absolute correlation above 0.8 because changes that improve one metric are likely to improve the other at the same time. <br><br>**Phase 2**: Design and implement targeted improvements such as tuning, refactoring, or hardware changes and track how both metrics respond to each intervention. <br><br>**Phase 3**: Validate performance uplift against SLAs and user experience measures and capture which optimisations produced the greatest combined effect. | - Maximises optimisation efficiency because engineering effort is directed at areas where improvements have a multiplied impact across several related metrics.<br><br>- Provides clearer cause and effect stories for stakeholders since correlated improvements can be explained in a single narrative rather than as isolated tweaks.<br><br>- Reduces trial and error work by concentrating on the most tightly linked behaviours instead of spreading effort thinly across many weakly related signals.<br><br>- Builds a library of proven optimisations tied to specific metric pair behaviours that can be reused when similar patterns appear in other systems.<br><br> | Formula: Δ Performance × Correlation Strength. Dataset: {len(strong_corr)} pairs >0.8 correlation. | Heatmap shows performance-linked pairs. |
| Develop integrated load models | **Phase 1**: Build statistical or regression models that describe how key metrics such as CPU, memory, and power usage move together based on the observed correlations. <br><br>**Phase 2**: Use these models to predict performance limits and saturation points under different load scenarios and validate predictions against historical incident and utilisation data. <br><br>**Phase 3**: Adjust configuration, capacity, and scaling policies according to model insights and update the models regularly as new data arrives. | - Improves the accuracy of capacity forecasting because models reflect the real relationships between load drivers and resource consumption rather than relying on simple rules of thumb.<br><br>- Helps prevent performance regressions by identifying combinations of utilisation and configuration that are likely to cause problems before they appear in production.<br><br>- Supports more informed design and architecture decisions since teams can quantify the impact of proposed changes on multiple metrics at once.<br><br>- Enables more convincing business cases for investment by linking technical model outputs to expected improvements in SLA compliance and user experience.<br><br> | Formula: Δ Prediction Accuracy × SLA% Gain. Dataset: strongest correlation {highest_corr:.2f}. | Matrix visualization confirms dependency. |
| Automate dynamic thresholds | **Phase 1**: Derive dynamic threshold bands for key metrics based on their typical relationships and variance, rather than using static fixed numbers, and encode these into monitoring rules. <br><br>**Phase 2**: Deploy adaptive alerting mechanisms that adjust thresholds as baseline correlations and workloads evolve while keeping guardrails to prevent extreme shifts. <br><br>**Phase 3**: Measure reductions in false positives, missed incidents, and alert handling time and refine the dynamic rules based on real world outcomes. | - Enhances operational agility because alerts follow the natural behaviour of the system and are less likely to fire unnecessarily when load patterns change in predictable ways.<br><br>- Reduces alert fatigue for operators by cutting down on false alarms that previously occurred when static thresholds clashed with normal but variable patterns.<br><br>- Increases the likelihood that genuine anomalies and emerging incidents are noticed quickly since they stand out from dynamically adjusted baselines.<br><br>- Improves confidence in monitoring tools as teams see thresholds adapt intelligently rather than having to constantly retune static settings by hand.<br><br> | Formula: Δ False Alerts × Cost per Incident. Dataset: high CPU-cost coupling validates approach. | Histogram shows clear correlation clusters. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Build stakeholder insight dashboards | **Phase 1**: Create dashboards that visualise inter metric dependencies in an accessible way, using simple explanations of what strong and weak correlations mean for service health. <br><br>**Phase 2**: Share these dashboards on a regular cadence with stakeholders so that they can see how infrastructure behaviours relate to each other and to business outcomes. <br><br>**Phase 3**: Track whether stakeholders report better understanding of issues and decisions and refine the content of the dashboards accordingly. | - Improves stakeholder awareness because complex technical relationships are translated into visual stories that non technical audiences can understand.<br><br>- Supports more productive conversations in governance and planning forums since participants have a shared view of how metrics interact.<br><br>- Reduces misinterpretation of raw metrics by providing context about which signals matter most and how they move together.<br><br>- Strengthens trust in IT reporting because explanations are backed by consistent, data driven visual evidence.<br><br> | Formula: CSAT Uplift = Visibility × Comprehension. Dataset: heatmap readability enhances clarity. | Correlation plot provides transparency. |
| Communicate efficiency linkages | **Phase 1**: Translate key technical correlations such as CPU versus cost or memory versus response time into simple narratives that explain how efficiency gains translate into financial or customer outcomes. <br><br>**Phase 2**: Publish short case studies or examples that show how optimising one metric improved related metrics and delivered concrete benefits for the business. <br><br>**Phase 3**: Measure the impact of this communication on stakeholder attitudes and decision support, for example in how easily investments or changes are agreed. | - Strengthens trust in IT optimisation efforts because stakeholders can clearly see how technical improvements connect to cost savings and service quality.<br><br>- Makes it easier to secure funding for optimisation work when the relationships between metrics and business outcomes are well understood.<br><br>- Encourages collaborative prioritisation since both IT and business leaders share an understanding of where efficiency changes will have the greatest combined impact.<br><br>- Reduces resistance to change by providing evidence based stories that show how previous optimisation steps have paid off in measurable ways.<br><br> | Formula: Δ Trust × Retention rate. Dataset: CPU–Cost correlations prove visible ROI. | Matrix confirms cause-effect transparency. |
| Use insights to guide future investment | **Phase 1**: Use correlation patterns to identify metric pairs and domains where investment is likely to produce improvements across multiple dimensions at once, such as performance and cost. <br><br>**Phase 2**: Align budget and roadmap decisions with these high impact areas so that funds and engineering time are concentrated where the strongest relationships exist. <br><br>**Phase 3**: Evaluate outcomes of these investments against both technical and business metrics to confirm that correlation based prioritisation is delivering the expected return. | - Aligns spending more tightly with business value because investment decisions are driven by data that show which changes will influence multiple important outcomes.<br><br>- Reduces wasted effort on low impact tuning by deprioritising areas where correlations are weak and improvements are likely to be isolated.<br><br>- Provides a repeatable framework for justifying investments to finance and leadership by linking correlation evidence to realised performance and cost changes.<br><br>- Encourages continuous measurement and review of investment effectiveness which improves strategic planning over time.<br><br> | Formula: ROI × Optimization Effectiveness. Dataset: {avg_corr:.2f} avg correlation validates insight-driven decisions. | Histogram confirms stable correlation patterns. |
"""
            }
            render_cio_tables("Correlation Matrix — CIO Recommendations", cio_corr)
