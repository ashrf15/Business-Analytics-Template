import streamlit as st
import pandas as pd
import plotly.express as px
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

# 🔧 Guard: shout if columns are missing
def _need(df, cols, title):
    missing = set(cols) - set(df.columns)
    if missing:
        st.warning(f"**{title}** not rendered — missing columns: `{', '.join(sorted(missing))}`.")
        return False
    return True

def implementation_plan(df):

    # ======================================================
    # Subtarget 1: Roadmap Timeline
    # (derived from last_maintenance_date + next_maintenance_due)
    # ======================================================
    with st.expander("📌 Capacity Optimization Roadmap Timeline", expanded=True):
        # Use existing capacity dataset columns instead of non-existent initiative/start_date/end_date
        required_cols = {"last_maintenance_date", "next_maintenance_due", "location", "component_type"}
        if not _need(df, required_cols, "Roadmap Timeline"):
            pass
        else:
            d = df.copy()
            d["start_date"] = pd.to_datetime(d["last_maintenance_date"], errors="coerce")
            d["end_date"] = pd.to_datetime(d["next_maintenance_due"], errors="coerce")

            # Build a synthetic initiative label per location + component type
            d["initiative"] = (
                d["location"].astype(str).fillna("Unknown Location")
                + " – "
                + d["component_type"].astype(str).fillna("Unknown Component")
            )

            # Aggregate to one row per initiative for a cleaner Gantt
            d_tl = (
                d.dropna(subset=["start_date", "end_date"])
                 .groupby("initiative", as_index=False)
                 .agg(
                     start_date=("start_date", "min"),
                     end_date=("end_date", "max"),
                 )
            )

            if d_tl.empty:
                st.info("No valid start/end dates after parsing last_maintenance_date and next_maintenance_due.")
            else:
                # Duration (used by both graphs)
                d_tl["duration_days"] = (d_tl["end_date"] - d_tl["start_date"]).dt.days
                if d_tl["duration_days"].dropna().empty:
                    st.info("Unable to compute durations (empty after parsing).")
                else:
                    avg_duration = float(d_tl["duration_days"].mean())
                    max_duration = int(d_tl["duration_days"].max())
                    min_duration = int(d_tl["duration_days"].min())
                    earliest_start = d_tl["start_date"].min()
                    latest_end = d_tl["end_date"].max()
                    n_initiatives = len(d_tl)

                    # Graph 1: Gantt-style timeline
                    fig1 = px.timeline(
                        d_tl,
                        x_start="start_date",
                        x_end="end_date",
                        y="initiative",
                        title="Implementation Roadmap Timeline",
                        color="initiative",
                    )
                    fig1.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig1, use_container_width=True, key="roadmap_timeline_impl")

                    st.write(f"""
What this graph is: A Gantt-style timeline showing the start and end windows for each capacity optimisation initiative derived from location and component type.  
X-axis: Calendar date representing when each initiative starts and ends.  
Y-axis: Synthetic initiative labels combining location and component family.  
What it shows in your data:  
Earliest initiative start date: {earliest_start.strftime("%Y-%m-%d")}.  
Latest initiative end date: {latest_end.strftime("%Y-%m-%d")}.  
Total number of initiatives in the roadmap: {n_initiatives}.  
Overall: The stacked and overlapping bars show where workstreams run in parallel across different locations and components, highlighting periods of intense activity versus quieter windows.  
How to read it operationally:  
Gap and overlap: Long stretches of overlapping bars indicate heavy multi-stream execution that may compete for resources.  
Critical path: Initiatives with the longest spans define the backbone of the roadmap and are at higher risk of delaying dependent work.  
Phasing: Grouping initiatives into logical waves or phases can be read directly from how bars cluster along the timeline.  
Why this matters: A clear timeline view helps prevent over-commitment, exposes scheduling risks early, and supports realistic communication of when capacity improvements will land for the business.
""")

                    # Graph 2: Duration distribution
                    fig2 = px.histogram(
                        d_tl,
                        x="duration_days",
                        nbins=10,
                        title="Distribution of Initiative Durations (Days)",
                        labels={"duration_days": "Duration (Days)"},
                    )
                    st.plotly_chart(fig2, use_container_width=True, key="duration_hist_impl")

                    st.write(f"""
What this graph is: A histogram showing how long initiatives run, grouped into buckets of duration in days.  
X-axis: Initiative duration in days from earliest start to latest end per initiative.  
Y-axis: Number of initiatives that fall into each duration bucket.  
What it shows in your data:  
Shortest initiative window: {min_duration:.0f} days.  
Longest initiative window: {max_duration:.0f} days.  
Average initiative duration: {avg_duration:.0f} days.  
Overall: The shape of the histogram shows whether your roadmap is dominated by short, tactical changes or by long-running strategic programmes and how mixed that portfolio is.  
How to read it operationally:  
Short tail: A cluster of short-duration initiatives points to many quick wins that can be scheduled early to build momentum.  
Long tail: A heavy tail of long initiatives indicates where governance, phasing, and risk management need more attention.  
Balance: A healthy mix of short and medium durations supports a balanced roadmap that can deliver both fast gains and deeper structural improvements.  
Why this matters: Understanding duration spread allows you to sequence work intelligently, avoid overwhelming teams with only long projects, and show stakeholders when to expect early benefits versus longer-term changes.
""")

                    # crude overlap signal: initiatives sharing identical start dates
                    overlap_count = int(d_tl["start_date"].duplicated(keep=False).sum())

                    cio_roadmap = {
                        "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Consolidate overlapping initiatives | Phase 1: Detect overlapping windows by looking at initiatives whose start and end dates overlap in the timeline. <br><br>**Phase 2**: Merge activities that touch the same location or component type into a single coordinated stream with shared planning. <br><br>**Phase 3**: Share resources such as engineers, tools, and budget across these merged initiatives and remove duplicate tasks. | - Reduces redundant work across similar initiatives and avoids paying twice for the same type of change.<br><br>- Lowers overall project management and coordination cost by running one combined programme instead of many fragmented efforts.<br><br>- Improves utilisation of shared resources such as specialist engineers or tools because they are scheduled once and used across multiple locations. | Savings = (Merged Initiatives × Avg Cost/Project). Dataset: {overlap_count} overlapping starts detected when aggregating by location and component type. | Timeline shows concurrent bars for different initiatives that share similar time windows, highlighting where consolidation is possible. |
| Prioritize high-impact, short-duration projects | Phase 1: Filter initiatives whose duration is below the median number of days and estimate their expected capacity or stability impact. <br><br>**Phase 2**: Execute these short, high-impact initiatives early in the roadmap to deliver quick improvements in efficiency or reliability. <br><br>**Phase 3**: Realign resources from completed quick wins towards longer initiatives that require more sustained effort. | - Delivers visible benefits quickly which helps justify continued investment in capacity optimisation work.<br><br>- Reduces risk by proving approaches on smaller, shorter efforts before scaling to larger programmes.<br><br>- Improves stakeholder confidence because they see concrete progress rather than only long-running projects. | ROI = Savings ÷ Duration, using the expected financial or capacity benefit divided by the duration in days. Dataset: average initiative duration is {avg_duration:.0f} days. | Histogram of initiative durations shows how many items sit in the short-duration range and can be treated as quick wins. |
| Adopt phased funding | Phase 1: Break long-running initiatives into clearly defined phases with separate objectives and measurable milestones. <br><br>**Phase 2**: Approve and fund each phase individually, only releasing budget when previous phases meet agreed outcomes. <br><br>**Phase 3**: Stop, adjust, or expand initiatives based on the performance of each phase and update the roadmap accordingly. | - Improves financial control by preventing large, multi-year spend from being committed without periodic review.<br><br>- Lowers delivery risk because underperforming initiatives can be halted or redesigned before consuming full budget.<br><br>- Increases alignment between finance and operations, as funding decisions are linked directly to delivered outcomes. | Funding Efficiency = Approved Phases ÷ Total Phases, showing how effectively phases progress to completion versus being paused or cancelled. | Very long bars in the timeline suggest initiatives that are naturally suited to being broken into multiple funded phases. |
""",
                        "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Align timelines to dependencies | Phase 1: Map technical and business dependencies between initiatives at each location and component family, identifying which work must happen first. <br><br>**Phase 2**: Adjust sequencing so that dependent initiatives only start once prerequisite work is complete or stable. <br><br>**Phase 3**: Track dependency-related delays in regular reviews and refine the schedule to minimise slippage. | - Reduces schedule overruns caused by starting dependent work before prerequisites are ready.<br><br>- Improves quality of delivery because teams are not forced to build on unstable or incomplete foundations.<br><br>- Makes project progression more predictable for stakeholders who depend on downstream outcomes. | Delay Reduction = Dependency Hours × Number of Projects where blocked work is reduced or eliminated. | Overlapping bars in the timeline around similar periods indicate where unmanaged dependencies may be increasing schedule risk. |
| Balance workload across phases | Phase 1: Split extremely long initiatives into smaller phases and estimate resource demand for each phase. <br><br>**Phase 2**: Assign teams and individuals so that no single group carries a disproportionate number of concurrent phases. <br><br>**Phase 3**: Validate that milestones are being hit without overloading key roles and adjust assignments as needed. | - Prevents burnout of critical staff who might otherwise be tied to long, intense projects without breaks.<br><br>- Maintains healthy throughput across the roadmap because all phases receive enough attention to stay on track.<br><br>- Allows smoother scaling up or down of work as priorities shift throughout the year. | Productivity Gain = Change in Milestone Completion Rate before and after balancing workload. | The longest initiative spans {max_duration:.0f} days, signalling where phase splitting and rebalance can have the biggest effect on team load. |
| Use agile delivery | Phase 1: Organise initiatives into smaller increments that can be delivered in short cycles such as two-week sprints. <br><br>**Phase 2**: Hold monthly or quarterly reviews to reassess priorities using feedback from each sprint and update the roadmap. <br><br>**Phase 3**: Dynamically reallocate capacity from lower-priority items to initiatives that show strong results or emerging urgency. | - Increases responsiveness to new information, incidents, or business requests that arise mid-roadmap.<br><br>- Reduces the likelihood of investing time in features or improvements that no longer align with current needs.<br><br>- Encourages continuous improvement because teams get frequent opportunities to adjust their approach. | Cycle Efficiency = Delivered Work ÷ Planned Work per sprint or review cycle. | Shorter-duration initiatives in the histogram naturally align with agile cycles and can demonstrate quick outcomes each iteration. |
""",
                        "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Publish roadmap dashboards | Phase 1: Build simple visuals based on the Gantt-style timeline that show key initiatives, start dates, and expected completion dates. <br><br>**Phase 2**: Update the dashboard regularly so stakeholders can see which items are on track, delayed, or newly added. <br><br>**Phase 3**: Provide a feedback channel where stakeholders can ask questions or flag dependencies that may not be visible to IT. | - Increases stakeholder confidence by making the capacity optimisation roadmap transparent and easy to understand.<br><br>- Reduces ad-hoc status requests and meetings because progress is visible in one place.<br><br>- Helps align expectations about when improvements in performance or capacity will land. | CSAT Uplift = Change in satisfaction scores attributed to improved communication and transparency. | The Gantt chart itself can be used as a live, visual roadmap to support regular steering meetings and updates. |
| Communicate milestones externally | Phase 1: Identify milestones within each initiative that have clear customer or business impact such as new capacity, reduced latency, or improved stability. <br><br>**Phase 2**: Notify internal and external stakeholders before and after major milestones with simple messages explaining what has changed. <br><br>**Phase 3**: Share performance or capacity metrics that prove the benefits delivered by those milestones. | - Builds trust with business units and customers who can see that promised improvements are being delivered.<br><br>- Improves coordination with other teams that depend on capacity changes to plan their own projects.<br><br>- Reduces friction and surprise when service behaviour changes as the result of optimisation work. | SLA Adherence = Change in response or resolution time performance linked to communicated milestones. | Overlapping initiatives and their start/end points in the timeline highlight where communications need to be aligned to avoid confusion. |
| Highlight quick wins | Phase 1: Select short-duration, high-impact initiatives that can be completed in a relatively small number of days. <br><br>**Phase 2**: Execute these items early and ensure their results are clearly measured and documented. <br><br>**Phase 3**: Publicise the outcomes such as reduced incidents or improved response times and reinvest the goodwill into support for larger initiatives. | - Boosts morale in delivery teams by showing that their work is quickly making a difference.<br><br>- Encourages executives and stakeholders to continue backing the capacity optimisation roadmap.<br><br>- Demonstrates that the roadmap is capable of producing tangible business value, not just long-term plans. | ROI Boost = (Number of Quick Wins × Perceived Value of Each Win) divided by the effort required. | The timeline and duration histogram reveal which initiatives are natural candidates to be treated and communicated as quick wins. |
"""
                    }
                    render_cio_tables("Roadmap Timeline — CIO Recommendations", cio_roadmap)

    # ======================================================
    # Subtarget 2: Responsible Parties
    # (map “owner” to location in this dataset)
    # ======================================================
    with st.expander("📌 Responsible Parties and Workload Distribution", expanded=True):
        # For this capacity dataset, treat location as the responsible party
        if not _need(df, {"location"}, "Responsible Parties"):
            pass
        else:
            d2 = df.copy()
            if d2["location"].dropna().empty:
                st.info("No location values to analyze as responsible parties.")
            else:
                owner_count = d2["location"].value_counts().reset_index()
                owner_count.columns = ["owner", "initiative_count"]

                if owner_count.empty:
                    st.info("No initiatives per owner to display.")
                else:
                    # Graph 1: Bar chart of initiatives per owner
                    fig3 = px.bar(
                        owner_count,
                        x="owner",
                        y="initiative_count",
                        text="initiative_count",
                        title="Initiatives Managed per Responsible Location",
                        labels={"initiative_count": "Number of Assets/Initiatives", "owner": "Responsible Party (Location)"},
                    )
                    fig3.update_traces(textposition="outside", cliponaxis=False)
                    st.plotly_chart(fig3, use_container_width=True, key="owner_workload_impl")

                    avg_load = float(owner_count["initiative_count"].mean())
                    max_owner = owner_count.iloc[0]["owner"]
                    max_load = int(owner_count.iloc[0]["initiative_count"])
                    min_owner = owner_count.iloc[-1]["owner"]
                    min_load = int(owner_count.iloc[-1]["initiative_count"])

                    st.write(f"""
What this graph is: A bar chart showing how many assets or capacity items are associated with each responsible location.  
X-axis: Responsible party represented by location name.  
Y-axis: Count of assets or capacity items associated with each location.  
What it shows in your data:  
Highest workload location: {max_owner} with {max_load} items.  
Lowest workload location: {min_owner} with {min_load} items.  
Average number of items per location: {avg_load:.2f}.  
Overall: Tall bars indicate locations that carry a large share of the capacity and operational workload, while short bars highlight locations with spare capacity or smaller scopes.  
How to read it operationally:  
Load hotspots: Locations with very tall bars are at higher risk of overload and may need additional support or redistribution of work.  
Underused capacity: Locations with very low bars may be able to take on more responsibility to balance the estate.  
Role design: The pattern of bar heights helps define which locations should be considered primary hubs versus satellite or specialised sites.  
Why this matters: Understanding how responsibility is distributed by location is essential for planning staffing, training, and investment so that no site becomes a single point of failure or a bottleneck for capacity work.
""")

                    # Graph 2: Pie chart workload share
                    fig4 = px.pie(
                        owner_count,
                        names="owner",
                        values="initiative_count",
                        title="Workload Share by Responsible Location",
                    )
                    st.plotly_chart(fig4, use_container_width=True, key="owner_pie_impl")

                    owner_shares = owner_count.copy()
                    owner_shares["share_pct"] = owner_shares["initiative_count"] / owner_shares["initiative_count"].sum() * 100.0
                    top_share_row = owner_shares.iloc[0]
                    top_share_owner = top_share_row["owner"]
                    top_share_pct = float(top_share_row["share_pct"])
                    lowest_share_row = owner_shares.iloc[-1]
                    lowest_share_owner = lowest_share_row["owner"]
                    lowest_share_pct = float(lowest_share_row["share_pct"])

                    st.write(f"""
What this graph is: A pie chart showing the percentage share of total workload held by each responsible location.  
X-axis: Not applicable, as this is a pie chart; slices represent locations.  
Y-axis: Not applicable; slice size represents percentage of total workload.  
What it shows in your data:  
Largest workload share: {top_share_owner} with {top_share_pct:.2f}% of all items.  
Smallest workload share: {lowest_share_owner} with {lowest_share_pct:.2f}% of all items.  
Overall distribution: A few locations hold a significant proportion of total workload while others account for small slices.  
Overall: The pie shape makes it easy to see whether the estate is dominated by a small number of key locations or more evenly balanced across many sites.  
How to read it operationally:  
Concentration: Very large slices indicate locations that are critical for day-to-day operations and should have stronger resilience, staffing, and succession planning.  
Equity: Very small slices indicate locations that may be underutilised, offering opportunities to rebalance tasks and responsibilities.  
Scenario planning: The distribution informs impact analysis if a particular location is disrupted, because you can see what portion of the estate it represents.  
Why this matters: A clear view of workload share by location supports risk management, succession planning, and targeted investment in locations that truly carry the business.
""")

                    cio_responsible = {
                        "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Redistribute workload | Phase 1: Identify locations that are responsible for a very high number of assets compared to the average, using the bar chart as a guide. <br><br>**Phase 2**: Reassign some capacity optimisation tasks or support responsibilities from these overburdened locations to sites with fewer assets. <br><br>**Phase 3**: Validate that handovers are complete and that documentation and monitoring are updated for the new responsible locations. | - Optimises internal capacity by ensuring work is not concentrated on a small number of locations or teams.<br><br>- Reduces the need for overtime and reactive firefighting at overloaded sites.<br><br>- Helps sites with spare capacity contribute more, improving overall utilisation of skills and tools. | Savings = (Reduction in Overtime Hours × Average Hourly Rate) across locations as workload becomes more balanced. Dataset: the gap between {max_owner} and {min_owner} illustrates current imbalance. | The bar chart clearly shows the difference in initiative or asset counts between heavily loaded and lightly loaded locations. |
| Cross-train members | Phase 1: Identify critical locations that own many assets and would create risk if key staff were unavailable. <br><br>**Phase 2**: Train backup staff from other locations or teams to handle core capacity and incident tasks for these critical sites. <br><br>**Phase 3**: Rotate responsibilities or run joint exercises periodically to keep backup skills current and validated. | - Lowers the risk of a single point of failure in knowledge or operational capability at any one location.<br><br>- Improves resilience because more people are able to step in when incidents or spikes in demand occur.<br><br>- Facilitates smoother collaboration across sites, as teams understand each other’s environments. | Cost Avoidance = (Potential Downtime Hours × Cost per Hour) that are avoided by having cross-trained backups ready to respond. | The pie chart indicates which locations are concentrated risk points and therefore require stronger cross-training and backup coverage. |
| Automate coordination tasks | Phase 1: Review repetitive administrative activities such as status updates, ticket routing, and simple capacity checks across all locations. <br><br>**Phase 2**: Deploy automation or workflow tools to handle these tasks centrally instead of manually at each responsible site. <br><br>**Phase 3**: Track reductions in manual hours and reassign freed-up time to higher-value analysis or optimisation work. | - Lowers administrative cost by removing low-value, repetitive work from local teams.<br><br>- Allows technical staff at each location to focus more on diagnostics and improvements rather than coordination overhead.<br><br>- Standardises how tasks are tracked and reported, improving accuracy and comparability between locations. | Time Saved = (Manual Hours Eliminated per Month × Average Wage Rate) summed across all locations. | Clusters of ownership in the charts highlight where coordination tasks are most dense and therefore prime candidates for automation. |
""",
                        "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Accountability metrics | Phase 1: Assign clear performance and delivery KPIs to each responsible location, such as incident resolution time or capacity optimisation progress. <br><br>**Phase 2**: Align roles and responsibilities so it is clear who within each site owns these KPIs. <br><br>**Phase 3**: Review performance metrics monthly and coach or support locations that fall behind. | - Creates clear ownership of outcomes, not just activities, leading to faster and more focused execution.<br><br>- Allows targeted support and remediation for locations that struggle to meet their targets.<br><br>- Encourages proactive behaviour as locations see how they compare with peers. | KPI Completion Rate × Number of Initiatives per Location, showing how reliably each site delivers on its commitments. | The number of locations analysed ({len(owner_count)}) combined with initiative counts gives a baseline for understanding accountability spread. |
| Dynamic task management | Phase 1: Implement real-time dashboards that show task queues, incident loads, and capacity work in progress by location. <br><br>**Phase 2**: Use these dashboards to adjust workload distribution across sites when certain locations are overloaded. <br><br>**Phase 3**: Periodically review how dynamic management has changed completion times and backlog. | - Makes operations more responsive to sudden changes in demand such as spikes in incidents or urgent capacity changes.<br><br>- Reduces bottlenecks where one location is stuck with too many tasks while others have capacity.<br><br>- Improves the overall completion rate of tasks across the entire footprint. | Efficiency Gain = Change in Task Completion Rate divided by Total Tasks, before and after dynamic task management is introduced. | Uneven initiative counts across locations in the bar chart show where dynamic task management can help smooth the load. |
| Workload forecasting | Phase 1: Use historical incident, capacity, and project data per location to forecast future workload trends. <br><br>**Phase 2**: Allocate new initiatives and staffing based on these forecasts rather than only on current load. <br><br>**Phase 3**: Refresh the forecast quarterly and adjust allocations accordingly. | - Moves the organisation from reactive to proactive capacity planning at the location level.<br><br>- Reduces surprise overload events because expected growth in work is considered in advance.<br><br>- Supports better hiring and training decisions as demand trends become clearer. | Forecast Accuracy × Load Variance, indicating how well forecasted workloads match actual demand and how much volatility is reduced. | The average initiative or asset load per location ({avg_load:.2f}) provides a starting point for forecasting future distribution of responsibilities. |
""",
                        "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Recognize top contributors | Phase 1: Use charts and KPIs to identify locations that consistently handle many initiatives or assets while maintaining strong performance. <br><br>**Phase 2**: Acknowledge these locations publicly and consider incentives or rewards for their teams. <br><br>**Phase 3**: Share their practices with other locations as examples of effective execution. | - Increases morale and engagement for teams that see their hard work recognised.<br><br>- Encourages healthy competition and adoption of best practices across different sites.<br><br>- Helps retain high-performing staff who feel valued for their contributions. | Productivity Uplift = Improvement in output or KPI scores after recognition programmes compared with before. | The fact that {max_owner} stands out with the highest initiative or asset count makes it a natural candidate for focused recognition. |
| Boost cross-dept collaboration | Phase 1: Form cross-functional squads that include representatives from multiple locations and disciplines to tackle shared capacity or optimisation initiatives. <br><br>**Phase 2**: Hold monthly collaboration sessions to review progress, discuss issues, and coordinate upcoming work. <br><br>**Phase 3**: Measure impact on incident rates, change success, and stakeholder satisfaction. | - Strengthens collaboration between locations and teams, breaking down silos that slow progress.<br><br>- Improves solution quality by incorporating diverse perspectives from different environments.<br><br>- Increases consistency in how capacity and performance issues are addressed across the estate. | CSAT Uplift = Improvement in stakeholder satisfaction scores correlated with increased cross-location and cross-department collaboration. | The spread of owners in the bar and pie charts shows that many locations are involved, creating opportunities for better synergy. |
| Transparent ownership dashboards | Phase 1: Publish dashboards that show which locations own which assets, initiatives, and KPIs so there is no confusion about responsibilities. <br><br>**Phase 2**: Update these dashboards weekly to reflect changes in ownership or workload distribution. <br><br>**Phase 3**: Provide a feedback mechanism for teams to flag incorrect assignments or suggest redistributions. | - Increases trust and visibility because everyone can see who is responsible for what and how busy each location is.<br><br>- Reduces friction and finger-pointing during incidents or delays because ownership is clear.<br><br>- Encourages continuous optimisation of workload distribution as teams can propose data-backed changes. | Engagement × Transparency Index, which links improvements in engagement or satisfaction to greater clarity of ownership. | The imbalance visible in the charts provides a compelling reason to maintain transparent, shared views of responsibility across locations. |
"""
                    }
                    render_cio_tables("Responsible Parties — CIO Recommendations", cio_responsible)

# ✅ Thin wrapper so your existing call works
def network_capacity(df):
    implementation_plan(df)
