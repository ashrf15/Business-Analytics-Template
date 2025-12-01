import streamlit as st
import plotly.express as px
import pandas as pd

# 🔹 Mesiniaga theme
px.defaults.template = "plotly_white"
PX_SEQ = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#99CCFF"]
px.defaults.color_discrete_sequence = PX_SEQ

# 🔹 Helper function to render CIO tables with 3 nested expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

def bottleneck_identification(df):
    # ==========================
    # 1️⃣ Identify Bottlenecks by Component
    # ==========================
    with st.expander("📌 Identify Performance Bottlenecks by Component"):
        if {"component_type", "avg_cpu_utilization", "avg_memory_utilization"} <= set(df.columns):

            df = df.copy()
            df["bottleneck_score"] = (
                pd.to_numeric(df["avg_cpu_utilization"], errors="coerce")
                + pd.to_numeric(df["avg_memory_utilization"], errors="coerce")
            ) / 2
            bottlenecks = df.groupby("component_type")["bottleneck_score"].mean().reset_index()

            # Graph 1: Average bottleneck score by component type
            fig_bar = px.bar(
                bottlenecks.sort_values("bottleneck_score", ascending=False),
                x="component_type",
                y="bottleneck_score",
                title="Average Bottleneck Score by Component Type",
                text="bottleneck_score",
                color_discrete_sequence=PX_SEQ
            )
            fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            st.plotly_chart(fig_bar, use_container_width=True, key="bottleneck_comp_bar")

            top = bottlenecks.loc[bottlenecks["bottleneck_score"].idxmax()]
            low = bottlenecks.loc[bottlenecks["bottleneck_score"].idxmin()]
            avg = bottlenecks["bottleneck_score"].mean()

            st.write(f"""
What this graph is: A bar chart showing average bottleneck score per component type based on the mean of CPU and memory utilization.

X-axis: Component type.  
Y-axis: Mean bottleneck score (%).

What it shows in your data: {top['component_type']} has the highest average bottleneck score at {top['bottleneck_score']:.2f}%. {low['component_type']} has the lowest average bottleneck score at {low['bottleneck_score']:.2f}%. The overall mean bottleneck score across all component types is {avg:.2f}%. The tallest bars highlight where resource contention is most severe and where performance interventions will deliver the strongest impact.

Overall: Component types with higher bottleneck scores are consistently running closer to their limits and are more likely to create slowdowns and instability. Focusing effort on these high scoring component types helps you remove systemic performance constraints instead of chasing isolated incidents.

How to read it operationally:

Hotspot triage: Remediate {top['component_type']} and other high scoring component types first with scale up, workload redistribution, or configuration tuning to reduce pressure on the most constrained areas.

Policy: When several bars cluster at a high bottleneck score, introduce stronger guardrails and standard templates across those families to prevent further drift and saturation.

Effect validation: After remediation, the highest bars should move closer to the overall mean. Track this movement monthly to confirm that actions are reducing stress rather than simply shifting it elsewhere.

Business mapping: Map critical business services to the underlying component types so that hidden pain in mid tier bars is surfaced and prioritised before it turns into visible user issues.

Why this matters: Concentrated bottlenecks are leading indicators of future incidents and cost spikes. Addressing the component types with the tallest bars first maximises performance gains and improves return on investment for capacity and optimisation work.
""")

            # Graph 2: Bottleneck distribution histogram
            fig_hist = px.histogram(
                df,
                x="bottleneck_score",
                nbins=20,
                title="Distribution of Bottleneck Scores Across All Assets",
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig_hist, use_container_width=True, key="bottleneck_hist")

            max_score = pd.to_numeric(df["bottleneck_score"], errors="coerce").max()
            min_score = pd.to_numeric(df["bottleneck_score"], errors="coerce").min()

            st.write(f"""
What this graph is: A histogram showing the distribution of bottleneck scores across all individual assets.

X-axis: Bottleneck score (%).  
Y-axis: Asset count.

What it shows in your data: Bottleneck scores for assets range from {min_score:.2f}% to {max_score:.2f}%. A concentration of assets in the higher score bins on the right side indicates a group of nodes that are under frequent CPU and memory stress, while the central mass represents typical load behaviour.

Overall: A heavy right side tail in the histogram signals a cluster of assets that regularly operate close to their limits. The broader the distribution, the more uneven your estate is in terms of resource pressure and stability.

How to read it operationally:

Urgent cohort: Tall bars in the right side bins form an immediate burn down list of assets that require relief through scaling, optimisation, or workload moves.

Policy tuning: A wide middle range suggests that thresholds and reservations may not be well calibrated. Adjusting these policies can reduce unnecessary alerts while still protecting service quality.

Impact check: After you implement remediation on the worst offenders, the right side tail should become shorter and move left. Monitoring this shift over time shows whether your actions are actually reducing risk.

Prioritisation: Cross reference the assets in the highest score bins with cost per month and business criticality so that fixes are prioritised for the nodes with both high risk and high business impact.

Why this matters: A large group of assets with high bottleneck scores represents accumulated operational risk. Reducing this risk debt lowers the likelihood of SLA breaches, unplanned outages, and user complaints.
""")

            # ==========================
            # CIO Recommendations for Component Bottlenecks
            # ==========================
            total_cost = float(pd.to_numeric(df.get("cost_per_month_usd", 0), errors="coerce").fillna(0).sum())
            pot_savings = float(pd.to_numeric(df.get("potential_savings_usd", 0), errors="coerce").fillna(0).sum())
            savings_ratio = (pot_savings / total_cost) if total_cost else 0

            cio_component = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Prioritise remediation for top bottleneck components | **Phase 1 – Rank:** Sort all component types by mean bottleneck score and verify that the underlying data for the highest ranked families is complete and reliable for decision making. <br><br>**Phase 2 – Invest:** Design and execute remediation actions such as scaling up, redistributing workloads, or tuning configurations on the top twenty percent of components with the highest bottleneck scores and track the implementation steps. <br><br>**Phase 3 – Validate:** Recalculate bottleneck scores on a quarterly basis and update the remediation list as components move up or down the ranking to ensure that effort continues to focus on the most constrained areas. | - Concentrates improvement spend on the components where performance gains and risk reduction are likely to be the largest.<br><br>- Reduces the number of high bottleneck components that can trigger widespread slowdowns across multiple services.<br><br>- Helps create a clear and defensible roadmap for where capacity and optimisation budget should be allocated first. | Savings Ratio = Σ(potential_savings_usd) / Σ(cost_per_month_usd) = ${pot_savings:,.2f} / ${total_cost:,.2f} = **{savings_ratio:.2f}x**. | Bar chart shows **{top['component_type']}** leading at **{top['bottleneck_score']:.2f}%**, while **{low['component_type']}** is lowest at **{low['bottleneck_score']:.2f}%**. |
| Consolidate into low-bottleneck families | **Phase 1 – Identify:** Highlight component families with the lowest mean bottleneck scores and confirm that they have sufficient spare capacity and resilience to absorb additional workloads without creating new hotspots. <br><br>**Phase 2 – Reallocate:** Move workloads away from high bottleneck component types into these lower stress families, starting with non critical workloads, and continuously monitor performance and risk indicators during the transition. <br><br>**Phase 3 – Retire:** Once workloads are successfully migrated and stable, decommission or repurpose surplus high bottleneck nodes so that cost and operational effort are no longer spent maintaining them. | - Reduces wasted spend on stressed and inefficient components by consolidating demand onto more stable and efficient families.<br><br>- Shrinks the overall number of nodes that must be supported, patched, licensed, and monitored in day to day operations.<br><br>- Creates a more homogeneous and predictable estate where performance and capacity are easier to manage. | Avoided Cost ≈ (nodes retired × monthly node cost), using cost_per_month_usd for each retired node. | Lowest family **{low['component_type']}** at **{low['bottleneck_score']:.2f}%** provides clear headroom for consolidation relative to the highest bars. |
| Predictive maintenance on high-score nodes | **Phase 1 – Model:** Use historical incident data and bottleneck scores to estimate failure or incident likelihood for component types and nodes that repeatedly show high bottleneck scores over time. <br><br>**Phase 2 – Schedule:** Plan targeted preventive maintenance, rebalancing, or hardware refresh activities for these high risk components before visible degradation or service impact occurs. <br><br>**Phase 3 – Measure:** Track how incident rates, outage minutes, and bottleneck scores change after interventions and refine the modelling thresholds and schedules based on observed results. | - Avoids expensive emergency repair work and unplanned downtime by intervening before stressed components fail during peak demand.<br><br>- Stabilises service levels on the most at risk families and reduces unplanned escalations to operations and engineering teams.<br><br>- Allows maintenance windows and remediation work to be planned and communicated instead of triggered by critical failures. | Outage Cost Avoided ≈ (reduction in incident count × average outage cost per incident). | The tallest bars in the bottleneck chart act as a simple risk proxy that highlights where predictive maintenance will produce the most impact on stability. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Introduce dynamic throttling and rate limits | **Phase 1 – Baseline:** Measure current response time, throughput, and error rates across component types at different bottleneck score ranges so that you understand how stress affects performance. <br><br>**Phase 2 – Implement:** Apply rate limiting or throttling on non critical workloads when bottleneck scores exceed defined thresholds, ensuring that capacity is reserved for critical services during high load periods. <br><br>**Phase 3 – Refine:** Continuously adjust thresholds, policies, and exception rules based on observed impact so that throttling protects performance without unnecessarily blocking legitimate demand. | - Improves overall performance during peak periods by protecting capacity for the most important business traffic and critical applications.<br><br>- Stabilises latency and user experience when the estate is operating close to saturation and prevents total slowdowns.<br><br>- Reduces the frequency of cascading failures that are triggered when overloaded components cannot handle surges in demand. | Performance Gain = (reduction in duration of high bottleneck periods × average performance impact cost per hour). | High bottleneck scores on specific component types indicate where throttling and rate limits will have the strongest stabilising effect. |
| Apply CPU and memory guardrails per component type | **Phase 1 – Design:** Define safe operating ranges for CPU and memory utilisation for each major component type by using bottleneck scores and historical performance patterns as guidance. <br><br>**Phase 2 – Enforce:** Configure monitoring alerts and automated actions when guardrails are breached for sustained periods, such as scaling actions, workload shedding, or priority changes. <br><br>**Phase 3 – Review:** Periodically review how often guardrails are breached, what actions were taken, and the resulting performance, then tighten or relax thresholds where necessary to balance stability and efficiency. | - Reduces performance incidents caused by silent resource saturation that is not visible until users are already impacted.<br><br>- Creates repeatable and automated patterns for handling overload situations instead of relying on manual, ad hoc interventions by engineers.<br><br>- Encourages consistent behaviour across similar component types, making performance easier to predict and manage. | Guardrail Benefit ≈ (number of avoided saturation events × estimated average incident impact cost). | Components with the highest bars in the bottleneck chart are the top candidates for early rollout of guardrails to prevent recurring performance issues. |
| Optimise workload placement and scheduling | **Phase 1 – Analyse:** Correlate high bottleneck scores with workload types, schedules, and seasonal patterns for each component family to identify when and why stress occurs. <br><br>**Phase 2 – Rebalance:** Reschedule flexible or batch workloads to off peak windows or move them to components and families with lower bottleneck scores while monitoring behaviour during and after the shift. <br><br>**Phase 3 – Track:** Monitor changes in average bottleneck scores, response times, and incident counts after rebalancing to confirm that the new placement and schedule reduces stress and improves stability. | - Smooths utilisation across the estate, which improves throughput and leads to more consistent performance during business hours.<br><br>- Reduces the chance that critical tasks and customer facing services are starved of resources by noisy neighbour workloads running at the same time.<br><br>- Increases the effective capacity of existing infrastructure without immediate hardware investment by using time and placement more intelligently. | Improvement Value = (reduction in average bottleneck score × estimated performance impact per percentage point improvement). | Bottleneck score distribution and bar heights reveal which components and time windows are currently overloaded and therefore need scheduling optimisation. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate risk and remediation plans for high bottleneck types | **Phase 1 – Explain:** Prepare simple and visual summaries that show which component types have the highest bottleneck scores and clearly explain why these hotspots matter to user experience and business services. <br><br>**Phase 2 – Commit:** Share remediation priorities, planned actions, and timelines for the top bottleneck component types with key stakeholders in language they can understand. <br><br>**Phase 3 – Update:** Provide follow up updates that show how bottleneck scores and related performance metrics have improved after remediation work has been completed. | - Builds confidence that infrastructure constraints are understood, tracked, and actively being addressed by the technology team.<br><br>- Reduces anxiety and unplanned escalations from business users because they can see that risky areas are known and are being handled.<br><br>- Creates a clear link between infrastructure investments and the improvements that customers and internal users can feel. | Perceived Value ≈ (reduction in escalations and urgent complaints × average handling cost per escalation). | The bar chart clearly shows which component types are congestion hotspots and supports transparent communication of the remediation roadmap. |
| Align SLAs with bottleneck-informed capacity | **Phase 1 – Assess:** Compare current SLAs and service level objectives with the effective capacity implied by bottleneck scores for each major component type and identify misalignments. <br><br>**Phase 2 – Adjust:** Where there is a gap, either invest in additional capacity and optimisation or adjust SLAs so that they reflect what the infrastructure can sustainably deliver. <br><br>**Phase 3 – Monitor:** Track SLA performance over time in relation to changes in bottleneck scores to validate that commitments and technical reality remain aligned. | - Prevents repeated SLA breaches that erode trust and damage the relationship between technology teams and customers.<br><br>- Ensures that customer commitments are based on sustainable service levels supported by actual data rather than optimistic assumptions.<br><br>- Provides a framework for discussing trade offs between cost, risk, and service levels with stakeholders. | SLA Risk Reduction ≈ (reduction in SLA breaches × penalty or business impact per breach). | Persistent high bottleneck scores on key components highlight where current SLAs may be unrealistic unless remediation is completed. |
| Use bottleneck trends in customer-facing status updates | **Phase 1 – Integrate:** Include simplified bottleneck trend indicators in regular service status pages or monthly performance reports so that customers see how risk is being managed. <br><br>**Phase 2 – Educate:** Explain in straightforward language how reductions in bottleneck scores translate into fewer incidents and better performance for end users, using examples where possible. <br><br>**Phase 3 – Reinforce:** Continue highlighting positive trends and remaining hotspots in follow up reports so customers can see ongoing improvement and understand residual risk. | - Strengthens the narrative that infrastructure improvements are directly supporting better user experience and reliability.<br><br>- Helps customers connect technical efforts to visible outcomes such as faster response times and fewer disruptions.<br><br>- Encourages more constructive conversations about risk and investment because decisions are grounded in shared data. | Communication Impact ≈ (improvement in satisfaction scores attributable to clearer and more transparent status reporting). | The histogram and bar chart provide intuitive visuals that support messages about current risk levels, capacity headroom, and improvement over time. |
"""
            }
            render_cio_tables("Bottleneck by Component — CIO Recommendations", cio_component)

    # ==========================
    # 2️⃣ Top Bottlenecked Assets
    # ==========================
    with st.expander("📌 Top 10 Bottlenecked Assets"):
        if "bottleneck_score" in df.columns:
            top10 = df.nlargest(10, "bottleneck_score")[["asset_id", "bottleneck_score"]]
            fig_top10 = px.bar(
                top10,
                x="asset_id",
                y="bottleneck_score",
                title="Top 10 Bottlenecked Assets",
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig_top10, use_container_width=True, key="bottleneck_top10")

            peak_asset = top10.iloc[0]
            low_asset = top10.iloc[-1]
            mean_score = pd.to_numeric(top10["bottleneck_score"], errors="coerce").mean()

            st.write(f"""
What this graph is: A ranked bar chart showing the top ten assets by bottleneck score.

X-axis: Asset ID.  
Y-axis: Bottleneck score (%).

What it shows in your data: The most constrained asset is {peak_asset['asset_id']} with a bottleneck score of {peak_asset['bottleneck_score']:.2f}%. The tenth asset on the list has a bottleneck score of {low_asset['bottleneck_score']:.2f}%. The average bottleneck score across these top ten assets is {mean_score:.2f}%. Risk is heavily concentrated toward the assets on the left side of the chart, which represent the most stressed and fragile nodes.

Overall: A small number of assets account for a large share of bottleneck risk in the estate. Focusing on these top ten assets first can deliver outsized improvements in stability and performance without needing to change every node.

How to read it operationally:

Rapid triage: Fix the top three assets first through load shedding, capacity upgrades, or configuration changes to deliver immediate relief to the most constrained points.

Plateau management: If many bars in the top ten cluster at similar high scores, introduce orchestration, automation, and guardrails to manage these assets as a group rather than only one by one.

Churn metric: After remediation work, assets should either drop off this top ten list or move down the ranking. Track this churn over time as a measure of how effectively risk is being reduced.

Service view: Map each asset to its supported applications and SLAs so that investment decisions can be prioritised based on both technical risk and business criticality.

Why this matters: The top ten bottlenecked assets form a practical risk ledger. Clearing items from this list reduces mean time to recovery, lowers the chance of SLA penalties, and improves perceived stability for users.
""")

            # CIO Recommendations for Top Bottlenecked Assets
            total_cost = float(pd.to_numeric(df.get("cost_per_month_usd", 0), errors="coerce").fillna(0).sum())
            pot_savings = float(pd.to_numeric(df.get("potential_savings_usd", 0), errors="coerce").fillna(0).sum())
            savings_ratio = (pot_savings / total_cost) if total_cost else 0

            cio_top = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Focus remediation on top 10 bottleneck assets | **Phase 1 – Address:** Tackle the assets with the highest bars first by applying targeted actions such as capacity upgrades, workload moves, or configuration tuning, and document each action taken. <br><br>**Phase 2 – Validate:** Confirm that utilisation, bottleneck scores, and latency for these assets decrease after changes and verify that issues do not simply move to other nodes. <br><br>**Phase 3 – Scale:** Apply the most successful remediation patterns from the top ten assets to the next most stressed asset cohort so that improvements scale across the estate. | - Maximises return on remediation spend by concentrating effort on the small set of assets that drive the largest share of bottleneck risk.<br><br>- Accelerates estate wide stability because fixing the worst offenders quickly removes recurring sources of incidents and slowdowns.<br><br>- Provides a clear and trackable action list that can be discussed and reported in operational and executive forums. | Savings Ratio = ${pot_savings:,.2f} / ${total_cost:,.2f} = **{savings_ratio:.2f}x**. | Chart explicitly lists assets by severity. The top asset sits at **{peak_asset['bottleneck_score']:.2f}%** while the tenth asset is at **{low_asset['bottleneck_score']:.2f}%**. |
| Targeted hardware only where ROI is proven | **Phase 1 – Model:** Estimate the potential performance and incident reduction benefits versus the hardware or platform upgrade cost for each of the top ten assets, using historical data where available. <br><br>**Phase 2 – Upgrade:** Proceed with hardware or tier upgrades only for those assets where the estimated benefit clearly outweighs the cost and document the rationale for each decision. <br><br>**Phase 3 – Recheck:** Reassess bottleneck scores, incident rates, and user experience one month after upgrade to validate ROI assumptions and update the investment model. | - Avoids blanket capital expenditure across all assets and ensures that significant hardware spend is focused only where it truly matters.<br><br>- Delivers visible performance gains on the most critical and constrained assets, which supports stronger justification for future budget requests.<br><br>- Prevents sunk cost on low impact nodes where cheaper optimisation or workload moves would have been sufficient. | ROI per Asset = (estimated benefit value ÷ upgrade cost) using incident reduction, performance improvement, and business impact metrics. | Bars quantify expected benefit concentration, which allows clear selection of which assets should receive the most expensive interventions. |
| Reduce monitoring on very stable nodes | **Phase 1 – Focus:** Identify stable assets that rarely appear in the top ten list or in high risk histogram tails and classify them as low risk for intensive monitoring. <br><br>**Phase 2 – Streamline:** Reduce non essential checks, dashboards, and alert rules for these stable assets in order to free up monitoring and engineering capacity for more critical nodes. <br><br>**Phase 3 – Reinvest:** Redirect monitoring effort, alert tuning, and engineering time to the top bottlenecked assets and the next most severe group so that attention follows risk. | - Lowers operational toil and alert noise for assets that consistently behave well, which improves team focus and reduces fatigue.<br><br>- Increases attention on the assets most likely to cause incidents and SLA breaches, which leads to faster and more effective responses in those areas.<br><br>- Helps monitoring tooling remain scalable and targeted by reducing unnecessary overhead on low risk assets. | Man Hours Saved ≈ (reduction in checks and alerts on stable assets × time spent per check or alert). | The distribution of top ten assets shows where risk is concentrated. Nodes that never appear in these charts are candidates for lighter monitoring policies. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Create runbooks for top 10 assets | **Phase 1 – Document:** Build asset specific runbooks for the top ten bottlenecked assets that describe known failure modes, early warning signs, remediation steps, and clear escalation paths. <br><br>**Phase 2 – Train:** Walk operations and support teams through these runbooks so they are familiar with the procedures and can act quickly when alerts are triggered. <br><br>**Phase 3 – Iterate:** Update runbooks after each significant incident or change affecting these assets so that the documentation reflects current reality and lessons learned. | - Reduces mean time to resolve issues on the most critical and fragile assets because responders have a prepared playbook to follow.<br><br>- Enables more consistent and predictable recovery behaviour during incidents and reduces dependence on individual heroics.<br><br>- Improves knowledge sharing across the team by capturing practical experience in a standard format. | MTTR Improvement Value = (reduction in MTTR for top assets × incident volume × business impact per incident). | The ranked bar chart shows exactly which assets should have bespoke runbooks because of their higher risk profile and frequent appearance at the top of the list. |
| Implement fine-grained telemetry on top assets | **Phase 1 – Enhance:** Add deeper metrics and logs on the top ten bottlenecked assets to capture queue lengths, specific resource waits, application level indicators, and dependency health. <br><br>**Phase 2 – Integrate:** Feed this richer telemetry into existing dashboards and alert systems, and define clear thresholds that distinguish between normal variation and genuine problems. <br><br>**Phase 3 – Review:** Use this detailed data to pinpoint root causes during investigations and adjust capacity, configuration, or code for the worst offenders as patterns emerge. | - Leads to faster and more accurate diagnosis when performance problems occur on the highest risk assets, because teams can see more than basic CPU and memory charts.<br><br>- Reduces guesswork and trial and error fixes, which lowers time spent in incident bridges and follow up investigations.<br><br>- Supports continuous improvement by revealing recurring bottlenecks and failure patterns that can be addressed structurally. | Benefit ≈ (reduction in time spent troubleshooting issues on top assets × engineer cost per hour). | The top ten chart indicates which assets justify the extra telemetry and dashboard investment because of their outsized contribution to risk. |
| Stagger maintenance on top 10 assets | **Phase 1 – Plan:** Ensure that maintenance work on the top bottlenecked assets is planned carefully so that multiple high risk assets are not taken down in the same window without adequate fallback. <br><br>**Phase 2 – Execute:** Sequence maintenance tasks so that alternative capacity or failover paths are available whenever a top asset is offline for upgrades or fixes. <br><br>**Phase 3 – Evaluate:** After each maintenance cycle, review whether performance, bottleneck scores, and incident behaviour improved as expected and adjust future plans accordingly. | - Prevents simultaneous impact from maintenance on multiple high risk assets, which could otherwise cause avoidable performance degradation or outages.<br><br>- Protects performance and capacity for critical services while still allowing necessary upgrades and remediation work to proceed.<br><br>- Improves confidence in maintenance windows by reducing the chance that they introduce more risk than they remove. | Maintenance Impact Avoided ≈ (avoidance of overlapping outages on top assets × estimated outage cost). | The chart highlights which assets must never be maintained in parallel if performance and stability risk are to be controlled effectively. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate remediation of top assets to stakeholders | **Phase 1 – Identify:** Link each of the top ten assets to the applications, business processes, and user groups they support so that the impact of work on these assets is clearly understood. <br><br>**Phase 2 – Inform:** Brief relevant stakeholders on planned remediation steps for these assets and describe the expected improvements in stability and performance in user centric terms. <br><br>**Phase 3 – Report:** After changes are implemented, share simple before and after metrics such as response time, incident counts, or error rates tied to these assets and the services they support. | - Increases stakeholder confidence that the most critical technical risks are being addressed in a structured and transparent way.<br><br>- Visibly connects infrastructure work to user experience improvements, which helps justify future investment and prioritisation decisions.<br><br>- Reduces confusion and speculation during and after remediation by providing clear context and outcomes. | Perceived Benefit ≈ (improvement in satisfaction scores or reduction in complaints for services tied to the top assets). | The top ten chart offers a clear narrative that these assets were fixed first because they had the highest bottleneck scores and therefore posed the greatest risk. |
| Use top 10 list as a standing risk register | **Phase 1 – Publish:** Treat the list of top bottlenecked assets as a live risk register and share it regularly in operations reviews and governance meetings so that everyone understands where technical risk sits. <br><br>**Phase 2 – Track:** Show which assets drop off or reappear on the list over time as remediation is carried out and as new stress patterns emerge in the environment. <br><br>**Phase 3 – Align:** Use the trend in this list to prioritise future investments and to ensure that discussions about risk and funding are grounded in objective data. | - Improves transparency of infrastructure risk and makes progress on remediation visible and measurable to non technical stakeholders.<br><br>- Aligns technology, operations, and business teams on which areas of risk are acceptable and which require immediate action.<br><br>- Provides a simple framework for ongoing risk management that can be updated as the environment and priorities change. | Risk Reduction Value ≈ (decrease in the number of chronic problem assets × estimated average impact per asset). | The ranked chart and its evolution over time visualise how risk is concentrated and how effectively it is being reduced through remediation work. |
| Tie user feedback to specific bottlenecked assets | **Phase 1 – Map:** Correlate user complaints, tickets, or low satisfaction scores with the applications and services that run on the top ten assets so that technical and user data are linked. <br><br>**Phase 2 – Focus:** Prioritise remediation actions on the assets most frequently associated with poor user feedback and document which complaints are expected to be addressed by each fix. <br><br>**Phase 3 – Validate:** After changes, check whether user feedback, complaint volume, and satisfaction scores improve for the services associated with those assets. | - Directly targets the technical causes of user dissatisfaction instead of treating only the symptoms reported at the service desk.<br><br>- Shows customers and internal users that complaints are taken seriously and resolved at the root where infrastructure is part of the problem.<br><br>- Provides evidence that technical remediation work is delivering tangible improvements that users can feel. | Feedback Impact ≈ (reduction in complaints linked to these assets × handling cost per complaint). | The top ten list combined with feedback data highlights which technical fixes will yield the biggest improvement in user perception and satisfaction. |
"""
            }
            render_cio_tables("Top Bottlenecked Assets — CIO Recommendations", cio_top)
