import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# 🔹 Helper to render CIO tables with 3 nested expanders (Option A format)
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction", expanded=True):
        st.markdown(cio_data.get("cost", "_No content_"), unsafe_allow_html=True)
    with st.expander("Performance Improvement", expanded=True):
        st.markdown(cio_data.get("performance", "_No content_"), unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement", expanded=True):
        st.markdown(cio_data.get("satisfaction", "_No content_"), unsafe_allow_html=True)


def _require_cols(df, cols, block_title):
    cols = set(cols)
    have = set(df.columns)
    missing = sorted(list(cols - have))
    if missing:
        st.warning(
            f"**{block_title}** not rendered — missing columns: `{', '.join(missing)}`. "
            f"Available columns: {', '.join(sorted(have))}"
        )
        return False
    return True


def network_capacity(df):

    # ------------------------------------------------------
    # Normalise / derive columns to match the expected schema
    # ------------------------------------------------------
    d = df.copy()

    # 1) Create a 'date' column from 'data_timestamp' if needed
    if "date" not in d.columns:
        if "data_timestamp" in d.columns:
            d["date"] = pd.to_datetime(d["data_timestamp"], errors="coerce")
        else:
            # fallback: no time dimension, we'll handle later via _require_cols
            pass

    # 2) Create network_capacity_gbps from network_bandwidth_gbps if missing
    if "network_capacity_gbps" not in d.columns and "network_bandwidth_gbps" in d.columns:
        d["network_capacity_gbps"] = pd.to_numeric(
            d["network_bandwidth_gbps"], errors="coerce"
        )

    # 3) Create network_bandwidth_usage_gbps from bandwidth * avg_network_utilization
    if "network_bandwidth_usage_gbps" not in d.columns:
        if {"network_bandwidth_gbps", "avg_network_utilization"} <= set(d.columns):
            bw = pd.to_numeric(d["network_bandwidth_gbps"], errors="coerce")
            util = pd.to_numeric(d["avg_network_utilization"], errors="coerce")
            d["network_bandwidth_usage_gbps"] = bw * (util / 100.0)

    # ======================================================
    # Subtarget 1: Network Bandwidth Utilization
    # ======================================================
    with st.expander("📌 Network Bandwidth Utilization Over Time", expanded=True):
        needed = {"date", "network_bandwidth_usage_gbps", "network_capacity_gbps"}
        if not _require_cols(d, needed, "Network Utilization"):
            pass
        else:
            d1 = d.copy()
            d1["date"] = pd.to_datetime(d1["date"], errors="coerce")
            d1 = d1.dropna(subset=["date"])

            if d1.empty:
                st.info("No valid dates to plot after parsing. Check your 'date' or 'data_timestamp' values.")
            else:
                # utilisation (%) from usage / capacity
                d1["network_utilization_pct"] = (
                    d1["network_bandwidth_usage_gbps"] /
                    d1["network_capacity_gbps"].replace(0, np.nan)
                ) * 100

                # Guard against all-NaN utilization
                if d1["network_utilization_pct"].dropna().empty:
                    st.info("Network utilization is all NaN (capacity may be 0 or missing).")
                else:
                    # Basic stats
                    peak = float(d1["network_utilization_pct"].max())
                    low = float(d1["network_utilization_pct"].min())
                    avg = float(d1["network_utilization_pct"].mean())
                    n_points = int(d1["network_utilization_pct"].dropna().shape[0])
                    high_util = int((d1["network_utilization_pct"] > 80).sum())
                    low_util = int((d1["network_utilization_pct"] < 30).sum())
                    total_cost = float(d1["cost_per_month_usd"].sum()) if "cost_per_month_usd" in d1.columns else 0.0
                    total_sav = float(d1["potential_savings_usd"].sum()) if "potential_savings_usd" in d1.columns else 0.0

                    # ------- Graph 1: Utilization trend line -------
                    fig_util = px.line(
                        d1,
                        x="date",
                        y="network_utilization_pct",
                        title="Network Utilization Trend Over Time (%)",
                        labels={"date": "Date", "network_utilization_pct": "Utilization (%)"},
                    )
                    st.plotly_chart(fig_util, use_container_width=True, key="net_util_line")

                    st.write(f"""
What this graph is: A line chart showing network utilization as a percentage of total capacity for each point in time.

X-axis: Calendar date for each measurement point.
Y-axis: Network utilization expressed as a percentage of available bandwidth.

What it shows in your data:
Peak utilization: {peak:.2f}%.
Lowest utilization: {low:.2f}%.
Average utilization across all measured points: {avg:.2f}%.
Out of {n_points} valid time points, {high_util} sit above 80% utilization while {low_util} sit below 30%, indicating both high pressure windows and over-provisioned periods.

Overall: When the line hugs the upper part of the chart for extended periods, the environment is running close to saturation and is more vulnerable to congestion and packet loss. When the line drifts along the bottom for long stretches, capacity is likely over-provisioned and not earning its cost.

How to read it operationally:
Peaks: Treat repeated spikes above roughly 80% as congestion risk zones where you should consider QoS tuning, traffic shaping, or targeted capacity uplift.
Plateaus: Long flat sections at moderate utilization reflect stable demand patterns where current capacity is well sized but must still be monitored for growth.
Downswings: Sustained dips to very low utilization highlight links or time windows that may be oversized or candidates for consolidation and contract optimisation.
Mix: Overlay business calendar events, change windows, and incident timelines to understand which peaks are predictable and which are caused by unplanned demand.

Why this matters: The balance between high and low utilization periods is the heartbeat of network capacity planning; staying out of sustained red zones avoids user pain and SLA breaches, while trimming chronic low zones protects budget from idle capacity.
""")

                    # ------- Graph 2: Utilization histogram -------
                    fig_hist = px.histogram(
                        d1,
                        x="network_utilization_pct",
                        nbins=20,
                        title="Distribution of Network Utilization (%)",
                        labels={"network_utilization_pct": "Utilization (%)"},
                    )
                    st.plotly_chart(fig_hist, use_container_width=True, key="net_util_hist")

                    st.write(f"""
What this graph is: A histogram showing how often the network operates at different utilization percentages.

X-axis: Network utilization buckets in percentage bands.
Y-axis: Count of time points that fall into each utilization band.

What it shows in your data:
Utilization ranges from a low of {low:.2f}% to a peak of {peak:.2f}%, with an overall average of {avg:.2f}%.
There are {high_util} observations above 80% utilization that represent high stress windows and {low_util} observations below 30% that represent potential over-capacity.
Most of the distribution mass indicates where the network spends the majority of its time, revealing the true operating band rather than just extremes.

Overall: A right-heavy tail indicates an environment that frequently pushes into high utilization territory, while a left-heavy shape reveals an estate that spends much of its time underused.
A compact, central distribution around a healthy mid-range band is a sign of balanced capacity and demand.

How to read it operationally:
Peaks: High bars towards the right side of the chart mean you often run very hot and should prioritise QoS, adaptive routing, or targeted upgrades there.
Plateaus: A broad central plateau shows the normal operating regime that should guide capacity planning, thresholds, and contract negotiations.
Downswings: Thin tails at either extreme indicate rare events; if the right tail grows over time, risk is increasing, and if the left tail is dominant, capacity is likely oversized.
Mix: Compare this histogram quarter by quarter to see whether optimisation efforts are shifting the distribution towards a more efficient and safer utilization band.

Why this matters: The shape of the utilization distribution exposes whether the network is mainly over-stretched, mainly over-sized, or well-balanced, which directly drives both cost efficiency and the likelihood of congestion-driven user issues.
""")

                    # ------- CIO tables (unchanged logic) -------
                    cio_util = {
                        "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Decommission low-traffic links | Phase 1: Identify circuits where utilisation is below 30% over a sustained period and confirm that these links are truly non critical or have alternative paths available. <br><br>**Phase 2 :** Work with providers and network teams to decommission, merge, or downgrade these low utilisation circuits while capturing the change in fixed charges. <br><br>**Phase 3 :** Perform a quarterly audit to ensure that retired capacity has not created hidden bottlenecks and to identify any new links that fall into the low utilisation range. | - Reduces carrier and maintenance cost by eliminating links that deliver little business value.<br><br>- Simplifies the network footprint so that fewer links need to be monitored, patched, and supported.<br><br>- Frees up budget that can be redirected to resilience or performance improvements on heavily used paths. | Savings Ratio = Σ potential_savings ÷ Σ cost. Calculated as ${total_sav:,.2f}/${total_cost:,.2f} = {(total_sav/total_cost if total_cost else 0):.2f}. | The utilisation histogram shows **{low_util}** data points where utilisation is below 30%, indicating clear candidates for consolidation or decommissioning. |
| Transition to shared circuits | Phase 1: Map application and site traffic patterns to understand which low usage locations can be moved from dedicated lines to shared MPLS or SD WAN connectivity without impacting service levels. <br><br>**Phase 2 :** Migrate these sites onto shared or aggregated circuits while monitoring latency, packet loss, and user feedback to confirm that the shared design behaves as expected. <br><br>**Phase 3 :** Validate the new cost structure and periodically review whether additional low volume sites can be folded into the shared model. | - Lowers recurring lease and access costs by replacing multiple underused dedicated links with shared bandwidth solutions.<br><br>- Improves utilisation of core network infrastructure by pooling capacity instead of isolating it per site.<br><br>- Supports more flexible growth because shared circuits can often be scaled more easily than many individual dedicated lines. | Estimated Savings = (Original dedicated link cost − Shared circuit cost) × number of migrated sites. | The left side of the utilisation histogram contains many low usage points, showing that several links are consistently underused and are good candidates for a shared circuit model. |
| Dynamic bandwidth provisioning | Phase 1: Engage providers to enable elastic or burstable bandwidth contracts where capacity can scale up and down based on actual usage rather than fixed, over provisioned limits. <br><br>**Phase 2 :** Configure monitoring and alerting so that when utilisation remains below agreed thresholds, contracted bandwidth levels can be safely reduced without harming performance. <br><br>**Phase 3 :** Review utilisation and invoices regularly to ensure that capacity levels and charges track real demand, and adjust thresholds as business patterns change. | - Avoids paying for idle capacity by aligning contracted bandwidth more closely to observed utilisation over time.<br><br>- Preserves the ability to handle short lived peaks without committing to high fixed capacity all month.<br><br>- Improves budget predictability because spend follows real demand rather than worst case assumptions. | Idle Capacity Cost = (Average unused GBps × Cost per GBps × Number of hours in billing period). | The utilisation line chart shows extended periods of low usage while the average utilisation remains at **{avg:.2f}%**, which strongly suggests excess capacity that can be tied to elastic provisioning models. |
""",
                        "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| QoS prioritization | Phase 1: Classify applications and traffic types into critical, important, and best effort categories based on business impact and SLA requirements. <br><br>**Phase 2 :** Configure quality of service policies on network devices so that critical traffic receives priority in queues during periods of high utilisation. <br><br>**Phase 3 :** Review QoS behaviour and SLA performance regularly to fine tune class definitions and queue settings. | - Reduces packet loss and latency for critical services during busy periods so key applications remain usable even when links are near saturation.<br><br>- Prevents non critical traffic such as large file transfers or backups from degrading end user experience.<br><br>- Supports clearer SLA guarantees because high priority classes are explicitly protected in policy. | Performance Gain ≈ (Reduction in packet loss and latency for critical flows × volume of critical transactions). | The utilisation analysis shows **{high_util}** time windows where utilisation exceeds 80%, indicating a real risk of contention that QoS can mitigate. |
| Link aggregation | Phase 1: Identify links and sites where peak demand regularly approaches the limit of a single physical circuit and where additional physical paths are feasible. <br><br>**Phase 2 :** Deploy link aggregation (such as LACP) to combine multiple physical links into a single logical interface and distribute traffic across them. <br><br>**Phase 3 :** Monitor the aggregated link for balanced load sharing and adjust hashing or path selection rules where necessary. | - Increases effective bandwidth and resilience without requiring a forklift upgrade of individual links.<br><br>- Provides automatic failover within the aggregated group so that a single link failure does not immediately impact service.<br><br>- Smooths utilisation by spreading flows across multiple physical paths. | Capacity Uplift = (Aggregated bandwidth − Original single link bandwidth), multiplied by the value of avoided congestion and outages. | Repeated plateaus near peak utilisation in the trend line highlight where single links are frequently close to exhaustion and would benefit from additional aggregated capacity. |
| Adaptive routing | Phase 1: Enable or enhance dynamic routing or SD WAN policies that can choose alternative paths when primary routes become congested or suffer high latency. <br><br>**Phase 2 :** Integrate real time measurements such as round trip time, jitter, and loss into routing decisions so that traffic automatically shifts to the best available path. <br><br>**Phase 3 :** Periodically validate that routing decisions align with performance objectives and adjust policies as traffic patterns evolve. | - Prevents localised bottlenecks by shifting traffic away from congested links to healthier ones in near real time.<br><br>- Improves average and tail latency for users by avoiding paths that are temporarily degraded.<br><br>- Reduces the need for manual intervention when specific links or regions are under stress. | Benefit ≈ (Reduction in average latency and loss × number of affected transactions or sessions). | Spikes in utilisation on particular paths suggest contention that adaptive routing can help bypass by steering flows to underused capacity. |
""",
                        "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Real-time visibility dashboards | Phase 1: Build and deploy dashboards that show live and historical network utilisation, availability, and incident status in a format that non technical stakeholders can understand. <br><br>**Phase 2 :** Share these dashboards or regular snapshots with business owners and service managers so they can see how the network behaves during peaks and planned events. <br><br>**Phase 3 :** Collect feedback on which views are most useful and refine the dashboards over time. | - Increases transparency and trust because stakeholders can see how network capacity is actually being used.<br><br>- Reduces unnecessary escalations driven by perception rather than data, since users can correlate their experience with objective metrics.<br><br>- Helps align expectations around what is normal versus abnormal utilisation. | Value ≈ (Number of complaints or ad hoc status requests avoided × average handling cost per request). | Periods of high utilisation in the line chart correlate with known user pain points, and making this visible helps explain and contextualise those events. |
| Off-peak maintenance | Phase 1: Use the utilisation histogram and time series to identify time windows and days of the week where network utilisation is consistently lowest. <br><br>**Phase 2 :** Schedule planned maintenance, upgrades, and testing activities into these low demand windows and communicate the plans in advance to users. <br><br>**Phase 3 :** After each window, review whether users experienced minimal impact and fine tune the chosen slots if necessary. | - Minimises disruption to business operations because most maintenance occurs when fewer users are active or traffic volumes are low.<br><br>- Reduces the number of complaints and perceived outages associated with change activity.<br><br>- Improves customer satisfaction scores by demonstrating that maintenance is planned thoughtfully. | Avoided Impact = (Number of incidents or SLA penalties avoided by shifting work to low utilisation periods × estimated cost per incident or penalty). | The lowest utilisation observed at **{low:.2f}%** in the trend and histogram clearly marks the best candidates for maintenance windows. |
| Redundancy at thresholds | Phase 1: Identify links or paths that regularly exceed defined utilisation thresholds such as 80% and map which services rely on them most heavily. <br><br>**Phase 2 :** Design and implement redundant links, backup paths, or secondary providers for these high risk circuits and test automatic failover. <br><br>**Phase 3 :** Periodically validate failover readiness and adjust capacity as traffic grows. | - Increases resilience by ensuring that the failure or saturation of a single heavily used link does not cause widespread service outages.<br><br>- Protects user experience during peak times or fault conditions by providing alternative routes for traffic.<br><br>- Supports higher confidence in SLAs and external commitments that depend on network reliability. | Outage Cost Avoided ≈ (Expected downtime without redundancy × business impact per hour) minus the cost of additional redundancy. | Sustained utilisation above 80% in multiple windows shows that some circuits operate close to their limits and merit additional redundancy to reduce risk. |
"""
                    }
                    render_cio_tables("Network Bandwidth Utilization — CIO Recommendations", cio_util)

    # ======================================================
    # Subtarget 2: Top 10 High-Traffic Nodes
    # ======================================================
    with st.expander("📌 Top 10 High-Traffic Network Nodes", expanded=True):
        needed = {"asset_id", "network_bandwidth_usage_gbps"}
        if not _require_cols(d, needed, "Top 10 Nodes"):
            pass
        else:
            d2 = d.copy()
            d2["network_bandwidth_usage_gbps"] = pd.to_numeric(
                d2["network_bandwidth_usage_gbps"], errors="coerce"
            )

            if d2["network_bandwidth_usage_gbps"].dropna().empty:
                st.info("No bandwidth usage values to rank.")
                return

            top10 = d2.nlargest(10, "network_bandwidth_usage_gbps")[["asset_id", "network_bandwidth_usage_gbps"]].copy()
            total_bw = float(d2["network_bandwidth_usage_gbps"].sum())
            if total_bw == 0:
                st.info("Total bandwidth usage is 0; cannot compute shares.")
                return

            top10["traffic_share_pct"] = (top10["network_bandwidth_usage_gbps"] / total_bw) * 100

            peak_row = top10.loc[top10["network_bandwidth_usage_gbps"].idxmax()]
            low_row  = top10.loc[top10["network_bandwidth_usage_gbps"].idxmin()]
            avg_node = float(top10["network_bandwidth_usage_gbps"].mean())
            top_share = float(top10["traffic_share_pct"].max())
            low_share = float(top10["traffic_share_pct"].min())
            total_top_share = float(top10["traffic_share_pct"].sum())

            # ------- Graph 1: Bar – top 10 nodes by usage -------
            fig_top = px.bar(
                top10,
                x="asset_id",
                y="network_bandwidth_usage_gbps",
                text="network_bandwidth_usage_gbps",
                title="Top 10 Network Nodes by Bandwidth Usage (Gbps)",
                labels={"asset_id": "Network Node", "network_bandwidth_usage_gbps": "Bandwidth Usage (Gbps)"},
            )
            fig_top.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
            st.plotly_chart(fig_top, use_container_width=True, key="net_top_nodes")

            st.write(f"""
What this graph is: A bar chart ranking the top 10 network nodes by raw bandwidth usage in Gbps.

X-axis: Network nodes (asset IDs) ordered by bandwidth consumption.
Y-axis: Bandwidth usage in Gbps for each node.

What it shows in your data:
The highest traffic node '{peak_row['asset_id']}' consumes {peak_row['network_bandwidth_usage_gbps']:.2f} Gbps.
The lowest node within the top 10 '{low_row['asset_id']}' still uses {low_row['network_bandwidth_usage_gbps']:.2f} Gbps.
On average, each of the top 10 nodes carries {avg_node:.2f} Gbps of traffic, indicating that even the smallest bar in this set is a significant contributor to load.

Overall: The tall leading bars show that a small subset of nodes act as concentration points for traffic and therefore represent both risk and opportunity.
Flattening the bar profile over time means traffic is spreading more evenly across the estate instead of piling up on a few critical chokepoints.

How to read it operationally:
Peaks: Focus optimisation, redundancy, and monitoring on the tallest bars first because they are the most likely to cause performance issues if they fail or saturate.
Plateaus: A relatively flat bar profile among the rest of the top 10 indicates balanced sharing of traffic across several key nodes and a healthier risk distribution.
Downswings: If remediation efforts are successful, the highest bars should gradually move closer to the rest rather than continuing to grow disproportionately.
Mix: Link each bar to its hosted services and user segments so that you understand which business areas are affected if that particular node experiences degradation.

Why this matters: Understanding which nodes are carrying the most bandwidth lets you target spend, engineering effort, and risk controls where they deliver maximum reduction in incident probability and impact.
""")

            # ------- Graph 2: Pie – share of total traffic -------
            fig_pie = px.pie(
                top10,
                names="asset_id",
                values="network_bandwidth_usage_gbps",
                title="Top 10 Nodes — Share of Total Network Traffic (%)",
            )
            st.plotly_chart(fig_pie, use_container_width=True, key="net_top_pie")

            st.write(f"""
What this graph is: A pie chart showing how much of the total measured network traffic is carried by each of the top 10 nodes.

X-axis: Not applicable for a pie chart; each slice represents a single network node.
Y-axis: Not applicable for a pie chart; the area of each slice encodes the node’s share of total bandwidth.

What it shows in your data:
The largest slice corresponds to '{peak_row['asset_id']}', which alone accounts for {top_share:.2f}% of total traffic.
The smallest node in the top 10 '{low_row['asset_id']}' still represents {low_share:.2f}% of all traffic.
Together, the top 10 nodes carry {total_top_share:.2f}% of total bandwidth usage, confirming that a small portion of the estate handles most of the load.

Overall: The more uneven the slices, the more your traffic is concentrated in a handful of nodes, which amplifies both operational risk and optimisation leverage.
Moving towards more balanced slice sizes spreads risk and can improve resilience, but extreme fragmentation might increase management complexity.

How to read it operationally:
Peaks: Very large slices indicate nodes that should receive priority for redundancy, QoS protection, and capacity planning because their failure or congestion would affect a large fraction of users.
Plateaus: Several similarly sized slices show a core mesh of important nodes that collectively shoulder the majority of traffic and should be treated as a cluster of critical assets.
Downswings: Shrinking the largest slices over time by offloading traffic to caches, CDNs, or additional nodes is a sign that risk and load are being better distributed.
Mix: Combine this view with geographic and business context so you can see whether a particular region, data centre, or service function is over-represented in the top traffic set.

Why this matters: The traffic share pattern determines how fragile or robust your network is to localised issues; heavy concentration in a few slices raises blast radius risk, while carefully managed distribution improves user experience stability during failures or spikes.
""")

            # High utilisation windows from earlier, if capacity exists
            if {"network_bandwidth_gbps", "network_capacity_gbps"} <= set(d.columns):
                util_pct_series = (
                    pd.to_numeric(d["network_bandwidth_usage_gbps"], errors="coerce") /
                    pd.to_numeric(d["network_capacity_gbps"], errors="coerce").replace(0, np.nan)
                ) * 100
                high_util_nodes = int((util_pct_series > 80).sum())
            else:
                high_util_nodes = 0

            cio_nodes = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Reallocate traffic-heavy workloads | Phase 1: Identify the applications and services that are driving high bandwidth on the top 10 nodes and map their traffic flows. <br><br>**Phase 2 :** Re distribute or load balance those workloads across additional nodes or paths to reduce saturation on the heaviest nodes. <br><br>**Phase 3 :** Monitor the new distribution to confirm that no new hotspots are created and that overall utilisation is more balanced. | - Lowers the risk that a single overloaded node will trigger performance issues or outages.<br><br>- Can defer or reduce the need to upgrade expensive links by making better use of existing capacity.<br><br>- Improves resilience because traffic is no longer concentrated on a small number of choke points. | Cost Avoided ≈ (Bandwidth upgrade cost that can be postponed or reduced because of better distribution). | The bar chart shows a top heavy distribution where nodes such as **'{peak_row['asset_id']}'** consume a disproportionately high share of total bandwidth. |
| Bandwidth caps for non-critical nodes | Phase 1: Classify the top 10 nodes by business criticality and identify those that host mainly non critical or background workloads. <br><br>**Phase 2 :** Apply bandwidth caps or rate limits on these non critical nodes so they cannot consume excessive bandwidth during busy periods. <br><br>**Phase 3 :** Review behaviour monthly to ensure that caps do not introduce side effects and adjust limits as demand patterns change. | - Prevents non critical traffic from monopolising bandwidth and starving higher priority services.<br><br>- Encourages more efficient use of the network by low value workloads.<br><br>- Helps keep peak utilisation levels under control without immediately increasing capacity. | Savings ≈ (Reduction in peak bandwidth charges or avoided penalties × contracted rate). | The pie chart shows uneven traffic shares, indicating that some nodes that are not business critical may still be using a large portion of available bandwidth. |
| Use CDN or cache for heavy content | Phase 1: Identify heavy, frequently accessed content or services that are responsible for a large portion of traffic through the highest usage nodes. <br><br>**Phase 2 :** Deploy content delivery networks, edge caches, or local proxies so that repeated requests are served closer to users. <br><br>**Phase 3 :** Track the reduction in core network traffic and adjust cache rules or CDN coverage based on hit and miss rates. | - Reduces traffic on core links and data centre nodes, which can delay or avoid expensive capacity upgrades.<br><br>- Improves user response times because content is served from closer or less congested locations.<br><br>- Supports better scalability during traffic spikes as load is spread across distributed caches. | Benefit ≈ (Bandwidth reduction on core links × cost per Gbps or per GB transferred). | The dominance of a few slices in the pie chart signals that offloading recurring content from those nodes will have an outsized impact on total network demand. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Traffic shaping on top nodes | Phase 1: Analyse traffic patterns for the top 10 nodes to identify bursty flows, long-lived flows, and interactive traffic. <br><br>**Phase 2 :** Apply traffic shaping policies that smooth bursts and prioritise interactive or latency sensitive traffic over bulk transfers on these nodes. <br><br>**Phase 3 :** Measure latency, jitter, and throughput before and after shaping to fine tune the policies. | - Produces smoother throughput and more predictable performance for critical applications hosted on or behind the top nodes.<br><br>- Reduces the impact of sudden bursts from a single source that might otherwise overwhelm shared links.<br><br>- Improves user experience during busy periods without requiring immediate capacity upgrades. | Performance Value ≈ (Reduction in latency or jitter × number of affected sessions or transactions). | Spikes and tall bars in the top node chart highlight where bursty and heavy flows exist and where shaping will have the best effect. |
| Intelligent routing (SD-WAN) for heavy nodes | Phase 1: For the top 10 nodes, map available network paths and measure latency, loss, and utilisation on each path. <br><br>**Phase 2 :** Configure SD WAN or dynamic routing rules so that traffic from heavily loaded nodes is sent along the best performing paths rather than always using a fixed route. <br><br>**Phase 3 :** Periodically reassess path quality and adjust the routing policy to keep traffic on optimal links. | - Increases effective path efficiency by using healthier links when primary paths become congested.<br><br>- Reduces end to end response times and variability for key applications relying on the busiest nodes.<br><br>- Improves resilience to transient link problems without requiring manual intervention. | Benefit ≈ (Latency reduction × transaction volume routed over improved paths). | The fact that the leading node accounts for **{top_share:.2f}%** of total traffic supports the case for giving it smarter path selection logic so it can use the best available network routes. |
| QoS for services on top nodes | Phase 1: Identify which critical business services run on or traverse each of the top 10 nodes and assign them appropriate QoS markings and SLA targets. <br><br>**Phase 2 :** Implement QoS policies along the full end to end path for these services, ensuring consistency across routers, switches, and WAN edges. <br><br>**Phase 3 :** Review SLA performance, fine tune class priorities, and adjust capacity planning based on observed behaviour. | - Ensures that the most important services maintain good performance even when the heaviest nodes are highly loaded.<br><br>- Reduces the number of SLA breaches that are caused by contention on a few critical network chokepoints.<br><br>- Provides a clearer mapping between technical QoS classes and business level SLAs. | SLA Benefit ≈ (Number of avoided SLA breaches × penalty or business impact per breach). | High utilisation windows and concentration of traffic on a few nodes highlight where QoS has the greatest potential to protect business services. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate optimisation on top nodes | Phase 1: Summarise which top nodes have been optimised, rebalanced, or upgraded and explain which user groups or applications benefit from these changes. <br><br>**Phase 2 :** Share this summary with stakeholders through service reviews or newsletters to show that specific performance pain points are being addressed. <br><br>**Phase 3 :** Collect feedback on perceived improvements and incorporate it into future optimisation plans. | - Increases user and stakeholder confidence that the most important and heavily used parts of the network are actively managed and improved.<br><br>- Links technical optimisation work directly to visible improvements in response times or reliability.<br><br>- Reduces scepticism or frustration around network issues because remediation steps are clearly communicated. | Perceived Value ≈ (Reduction in complaints or repeated queries about known problem areas × handling cost). | The top node charts clearly identify which nodes were causing the most load and therefore provide a simple before and after story to communicate. |
| Use top 10 list as a standing risk register | Phase 1: Treat the list of top 10 high traffic nodes as a living risk register and review it in regular operations and governance meetings. <br><br>**Phase 2 :** Track which nodes remain on the list, which drop off after remediation, and which new nodes appear as traffic patterns evolve. <br><br>**Phase 3 :** Base future investment and capacity planning decisions on how this risk register changes over time. | - Improves transparency and shared understanding of where network risk is concentrated at any point in time.<br><br>- Helps prevent surprises by making it obvious when new nodes are becoming hot spots before they cause incidents.<br><br>- Aligns technical planning with business priorities because risk discussions are grounded in concrete data. | Risk Reduction Value ≈ (Decrease in chronic high risk nodes × average impact per node if an issue occurs). | The ranked bar chart and its evolution over time show how risk is concentrated and how effectively remediation efforts reduce that concentration. |
| Tie user feedback to specific high-traffic nodes | Phase 1: Correlate user complaints, low satisfaction scores, or slow application reports with the applications and services hosted on the top 10 nodes. <br><br>**Phase 2 :** Prioritise optimisation work on those nodes where there is a clear relationship between technical load and negative user feedback. <br><br>**Phase 3 :** After optimisation, review whether complaints and satisfaction scores improve for those services. | - Directly connects network optimisation work to the aspects of service quality that matter most to users.<br><br>- Provides evidence that resolving capacity or performance issues on specific nodes leads to measurable user experience gains.<br><br>- Supports more targeted and defensible investment cases because spend is tied to customer impact. | Feedback Impact ≈ (Reduction in complaints linked to services on top nodes × handling cost per complaint). | The top 10 node list, combined with feedback data, highlights which heavy network nodes are most strongly associated with poor user experience and therefore where fixes will pay off fastest. |
"""
            }
            render_cio_tables("Top 10 High-Traffic Nodes — CIO Recommendations", cio_nodes)
