import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# Mesiniaga theme
MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#9BD1FF"]

def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data.get("cost","_No cost recommendations._"), unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data.get("performance","_No performance recommendations._"), unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data.get("satisfaction","_No satisfaction recommendations._"), unsafe_allow_html=True)

def _p75_excess(series):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return np.nan, 0.0
    p75 = np.nanpercentile(s, 75)
    return float(p75), float((s[s > p75] - p75).sum())

def _fmt_int(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return "0"

def _fmt_float(x, d=2):
    try:
        return f"{float(x):.{d}f}"
    except Exception:
        return "0.00"

def service_response_resolution_time(df_filtered):

    # ---------------------- 3(a) Average Response Time ----------------------
    with st.expander("📌 Average Response Time for Service Requests"):
        if "avg_response_time_mins" in df_filtered.columns:
            # Chart
            fig = px.histogram(
                df_filtered, x="avg_response_time_mins", nbins=40,
                title="Distribution: Response Time (mins)",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            s = pd.to_numeric(df_filtered["avg_response_time_mins"], errors="coerce").dropna()
            if not s.empty:
                desc = s.describe()
                p75, excess = _p75_excess(s)

                mean_v = float(desc["mean"])
                median_v = float(desc["50%"])
                min_v = float(desc["min"])
                max_v = float(desc["max"])

                st.markdown("### Analysis – Response Time Distribution")
                st.write(f"""
**What this graph is:** A histogram showing the **distribution of first-response times** in minutes.  
**X-axis:** Response time (mins).  
**Y-axis:** Number of tickets in each time bucket.

**What it shows in your data:**  
- **Mean / Median:** **{_fmt_float(mean_v)} / {_fmt_float(median_v)} mins**  
- **Min / Max:** **{_fmt_float(min_v)} / {_fmt_float(max_v)} mins**  
- **75th percentile (p75):** **{_fmt_float(p75)} mins**  
- **Minutes above p75 (improvement surface):** **{_fmt_int(excess)} mins**

**Overall:** A long right tail indicates **pockets of delay**; compressing that tail yields immediate, measurable savings.

**How to read it operationally:**  
- **Tail attacks:** Target cases above **p75 = {_fmt_float(p75)} mins** first.  
- **Playbooks:** Standardize responses for the most common intents in the heavy bins.  
- **Control:** Live wallboard to spot tail growth during peak hours.

**Why this matters:** Tail minutes translate into **overtime, escalations, and lower CSAT**. Reducing tail area frees capacity without hiring.
""")

                evidence_resp = (
                    f"Mean/Median **{_fmt_float(mean_v)} / {_fmt_float(median_v)}**; "
                    f"p75 **{_fmt_float(p75)}**; minutes above p75 **{_fmt_int(excess)}**."
                )

                cio = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Auto-acknowledgement + triage macros** | **Phase 1 – Templates:** - Create category specific first replies that ask for the exact details agents need so the second touch is avoided and the case can move immediately.<br><br>- Write prompts that guide users to attach screenshots and logs so diagnosis starts faster without waiting for follow ups.<br><br>**Phase 2 – Trigger:** - Send the acknowledgement and data capture message the moment a ticket is created so perceived wait time drops and users feel attended to.<br><br>- Ensure the macro sets initial priority and routing tags so the right queue receives the case without manual edits.<br><br>**Phase 3 – Tune:** - Review the top intents every quarter and update the templates using recent tickets so wording stays relevant and reduces back and forth.<br><br>- Retire low value macros and promote the highest performing replies so the catalog stays sharp. | - Users get immediate clarity on what happens next which reduces anxiety and cuts the number of chaser messages that consume agent time.<br><br>- Agents spend fewer minutes per ticket because critical information arrives upfront which accelerates investigation and reduces idle wait time.<br><br>- Standard messages ensure consistent quality which reduces rework and speeds onboarding of new agents who can rely on proven wording.<br><br>- During surges the automated first touch absorbs volume which lowers overtime risk and stabilizes handling cost. | **Tail surface = {_fmt_int(excess)} mins** above p75; shaving even 30% yields **{_fmt_int(excess*0.30)} mins saved**. | {evidence_resp} |
| **Peak-hour staffing alignment** | **Phase 1 – Observe:** - Identify the hours that generate the heaviest histogram bins and confirm if they correlate with known business events so the signal is real.<br><br>- Quantify the gap between arrivals and available agent minutes so the required shift changes are data driven.<br><br>**Phase 2 – Shift:** - Move start times and break schedules so capacity covers the busiest hours and reduces queue growth before it becomes a tail problem.<br><br>- Pilot the new roster for two weeks and measure the change in tail minutes to validate impact.<br><br>**Phase 3 – Review:** - Compare before and after metrics and keep the improvements that shrink the right tail while preserving agent wellbeing.<br><br>- Revisit the plan quarterly as seasonality changes so coverage remains optimal. | - Better alignment reduces queue buildup which prevents expensive overtime and reduces burnout for agents who no longer face large backlogs at shift start.<br><br>- Shorter waits lower the number of outliers which directly improves SLA performance and reduces penalty exposure in managed contracts.<br><br>- A steady flow creates more predictable work which improves accuracy and reduces error rates that would otherwise add rework minutes.<br><br>- Data informed scheduling builds trust with stakeholders because changes are justified by measurable results. | **OT savings** = (OT hrs avoided × rate). Use tail minutes as the avoidable pool (**{_fmt_int(excess)}**). | Heavier right-side bins indicate peak misalignment. |
| **Skill-based first routing** | **Phase 1 – Map:** - Define the most common intents and link them to the teams with the right skills so tickets land with the correct solver on the first touch.<br><br>- Document clear fallbacks for ambiguous intents so routing remains fast even when the signal is weak.<br><br>**Phase 2 – Route:** - Implement rules in the service desk tool so misroutes are minimized and handoffs are avoided as much as possible.<br><br>- Add a rapid reclassify shortcut so agents can correct the path in seconds when needed.<br><br>**Phase 3 – Audit:** - Track reassignment rate and investigate the patterns that cause misroutes so taxonomy and forms can be improved.<br><br>- Share findings with teams so quality of intake rises over time. | - Fewer handoffs reduce waiting and keep momentum which shortens the path to first response for complex intents where speed matters most.<br><br>- Correct placement lowers cognitive switching for agents which improves focus and reduces mistakes that would extend handling time.<br><br>- Reassignment auditing reveals training gaps and taxonomy issues which unlocks further cycle time reductions without adding headcount.<br><br>- A cleaner routing model makes performance predictable which simplifies capacity planning and stabilizes cost. | **Minutes saved** = (handoff mins avoided × #tickets). Use p75 threshold **{_fmt_float(p75)}** as trigger. | Misrouted/late cases inflate the right tail beyond p75. |
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **CDF target on response** | **Phase 1 – Set:** - Define a cumulative distribution target where at least seventy five percent of tickets receive the first response within **{_fmt_float(p75)} mins** so the team has a clear benchmark from real data.<br><br>- Publish the target by queue so expectations are aligned across all stakeholders.<br><br>**Phase 2 – Monitor:** - Track a live CDF and alert leaders when the curve drifts so action is taken before breaches accumulate.<br><br>- Display queue age bands so agents can self correct in real time.<br><br>**Phase 3 – Improve:** - Drill into the drivers of the tail and run small fixes such as a new macro or a better form field so the curve shifts left over time.<br><br>- Refresh the target quarterly using new data so goals remain realistic and motivating. | - Predictable first response times increase user confidence which reduces escalations and improves perceived reliability of the service desk.<br><br>- Real time visibility enables fast adjustments which keeps the queue healthy during daily fluctuations without heavy managerial overhead.<br><br>- A data anchored target creates focus which guides improvement efforts to the highest impact issues first.<br><br>- Continual calibration prevents target decay which sustains performance gains across the year. | **SLA uplift** = (tickets moved below p75 × mins saved per ticket). | p75 is derived from your data (**{_fmt_float(p75)} mins**). |
| **Real-time wallboard** | **Phase 1 – Visualize:** - Build a simple board that shows queues by intent and age so the team can see pressure building before it becomes a breach problem.<br><br>- Include alerts for long waiting bins to prompt action quickly.<br><br>**Phase 2 – Act:** - Swarm the oldest items when the tail grows so aging is cut off early and the histogram shifts left the same day.<br><br>- Rotate a coordinator role that triggers the swarm to avoid diffusion of responsibility.<br><br>**Phase 3 – Learn:** - Run short post mortems after visible spikes and implement one fix per spike so noise slowly declines.<br><br>- Track which visualizations drive action so the board improves. | - Earlier interventions reduce queue age which improves throughput and lowers the number of SLA at risk cases that demand expensive escalations.<br><br>- Shared situational awareness helps agents self organize which reduces dependency on constant supervision and speeds decisions.<br><br>- Continuous learning from spikes makes the environment calmer which improves accuracy and reduces rework across shifts.<br><br>- A focused wallboard becomes a lightweight control system which increases resilience during peak periods. | **Minutes saved** from earlier intervention compared to tail minutes (**{_fmt_int(excess)}**). | Batches and tail growth visible in the histogram. |
| **Intent playbooks** | **Phase 1 – Identify:** - Use the heavy bins to find the top intents that repeatedly slow first response so effort targets the most valuable fixes.<br><br>- Confirm with agents which steps create friction so the playbook addresses real obstacles.<br><br>**Phase 2 – Script:** - Write step by step guides and ready to send templates that remove guesswork and reduce typing time so responses are fast and consistent.<br><br>- Store the playbooks where agents work so access is instant.<br><br>**Phase 3 – Train:** - Run short refreshers monthly and test two improvements each cycle so the playbooks stay current and practical.<br><br>- Retire steps that add no value so the guides stay lean. | - Faster first touches reduce queue growth which keeps performance stable through the day and improves SLA compliance for the most frequent issues.<br><br>- Consistent handling improves quality which reduces follow up contacts and lowers cost per ticket.<br><br>- Lightweight training keeps skills fresh which reduces reliance on senior staff and improves resilience when staffing changes.<br><br>- Well placed guides reduce agent cognitive load which increases speed and accuracy under pressure. | **Handle-time delta × volume** for those intents. | Distribution shows repeated patterns suitable for templating. |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **ETA messaging by priority** | **Phase 1 – Define:** - Set clear ETA bands for each priority so users know what to expect and can plan their work with fewer interruptions.<br><br>- Align ETAs with actual performance so promises are realistic and credible.<br><br>**Phase 2 – Notify:** - Send an automatic message at intake that includes the ETA and the next action so users feel informed from the start.<br><br>- Provide a link to add details so cases do not stall while waiting for clarifications.<br><br>**Phase 3 – Calibrate:** - Review adherence weekly and adjust the bands so communication remains accurate as volumes change.<br><br>- Share metrics with owners so accountability is reinforced. | - Clear expectations reduce chaser messages which lowers noise and frees agents to work on resolutions rather than status updates.<br><br>- Perceived fairness improves because similar tickets receive similar timelines which reduces complaints about unequal treatment.<br><br>- Better planning by users reduces context switching and follow up contacts which lifts overall productivity and satisfaction.<br><br>- Regular calibration keeps promises aligned to reality which preserves trust over time. | **Complaints avoided × mins/case**, anchored to tail minutes (**{_fmt_int(excess)}**). | Long waits beyond **{_fmt_float(p75)}** drive dissatisfaction. |
| **Self-service for trivial intents** | **Phase 1 – Route:** - Detect low complexity requests and guide users to a knowledge base or bot flow that solves the issue without agent intervention.<br><br>- Make the route visible but optional so users feel supported rather than blocked.<br><br>**Phase 2 – Guide:** - Prompt for the right attachments or screenshots so the answer is actionable and users do not return with the same question.<br><br>- Offer a path to human help if the self service step fails so confidence remains high.<br><br>**Phase 3 – Measure:** - Track deflection rate and monitor repeat contacts to ensure quality remains strong and update content that underperforms.<br><br>- Celebrate the best performing articles so authors are motivated to improve content. | - Fast self resolution reduces waiting which raises satisfaction for simple issues that users prefer to fix immediately.<br><br>- Deflected contacts cut agent workload which reduces cost and preserves capacity for complex cases where human expertise matters most.<br><br>- Better guidance lowers failed attempts which avoids frustration and reduces repeat contacts that would otherwise add to the tail.<br><br>- Quality tracking ensures the self service channel remains effective which keeps trust high. | **Cost avoidance** = (# self-resolved × avg agent mins). | Lower-bin clusters indicate simple, repeatable requests. |
| **Priority-aware status pings** | **Phase 1 – Cadence:** - Define time boxed updates for slow moving queues so users hear from you before they need to ask and concerns are addressed proactively.<br><br>- Tailor cadence by priority so critical users get tighter follow ups while lower priorities are not overloaded with noise.<br><br>**Phase 2 – Content:** - Include the next action and the owner in each update so accountability is clear and users know what to expect next.<br><br>- Provide a way to add information directly so progress is accelerated without extra tickets.<br><br>**Phase 3 – Review:** - Analyze feedback and CSAT comments to tune the cadence and wording so messages feel helpful rather than repetitive.<br><br>- Adjust rules when the tail shrinks so updates remain proportional to risk. | - Proactive updates reduce escalations because users see movement and understand the plan which improves confidence in the service team.<br><br>- Clear ownership reduces duplicated contacts because users know who is handling the issue which lowers total communication load.<br><br>- Right sized cadence keeps users informed without adding noise which improves satisfaction and reduces stress for agents.<br><br>- A living policy adapts as performance improves which keeps communications efficient and effective. | **Escalation cost avoided** per delayed ticket beyond p75 (**{_fmt_float(p75)}**). | Tail cases correlate with negative feedback. |
"""
                }
                render_cio_tables("CIO — Response Time", cio)
        else:
            st.warning("Column 'avg_response_time_mins' not found.")

    # ---------------------- 3(b) Average Resolution Time ----------------------
    with st.expander("📌 Average Resolution Time for Incidents and Service Requests"):
        if "avg_resolution_time_mins" in df_filtered.columns:
            fig = px.histogram(
                df_filtered, x="avg_resolution_time_mins", nbins=40,
                title="Distribution: Resolution Time (mins)",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            s = pd.to_numeric(df_filtered["avg_resolution_time_mins"], errors="coerce").dropna()
            if not s.empty:
                desc = s.describe()
                p75, excess = _p75_excess(s)

                mean_v = float(desc["mean"])
                median_v = float(desc["50%"])
                min_v = float(desc["min"])
                max_v = float(desc["max"])

                st.markdown("### Analysis – Resolution Time Distribution")
                st.write(f"""
**What this graph is:** A histogram showing the **distribution of full-resolution times** in minutes.  
**X-axis:** Resolution time (mins).  
**Y-axis:** Number of tickets in each time bucket.

**What it shows in your data:**  
- **Mean / Median:** **{_fmt_float(mean_v)} / {_fmt_float(median_v)} mins**  
- **Min / Max:** **{_fmt_float(min_v)} / {_fmt_float(max_v)} mins**  
- **75th percentile (p75):** **{_fmt_float(p75)} mins**  
- **Minutes above p75:** **{_fmt_int(excess)} mins**

**Overall:** This right tail is the **largest measurable efficiency opportunity**.

**How to read it operationally:**  
- **Tail collapse:** Swarm and expert-lane everything above **p75 = {_fmt_float(p75)}**.  
- **Segmentation:** Separate complex vs routine streams to reduce cross-blocking.  
- **Control:** Weekly review of top aged 10 to remove recurrent drag.

**Why this matters:** Resolution time drives **SLA, MTTR, and customer patience**. Shrinking the tail improves all three at once.
""")

                evidence_res = (
                    f"Mean/Median **{_fmt_float(mean_v)} / {_fmt_float(median_v)}**; "
                    f"p75 **{_fmt_float(p75)}**; minutes above p75 **{_fmt_int(excess)}**."
                )

                cio = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **KB requirement for top repeats** | **Phase 1 – Identify:** - Use the tail to find high volume repeat problems and verify that their steps are stable enough to document clearly so the content will actually be used.<br><br>- Rank by resolution minutes and business impact so writing effort focuses on the biggest wins first.<br><br>**Phase 2 – Enforce:** - Add a link to close rule that requires agents to attach a relevant article before resolving the case so knowledge sharing becomes part of the workflow.<br><br>- Provide a quick create template so agents can capture new knowledge in the moment without friction.<br><br>**Phase 3 – Maintain:** - Review articles monthly and retire or merge duplicates so the library stays accurate and easy to search.<br><br>- Track article usage and update low performing content so quality rises over time. | - Documented fixes shorten resolution steps for repeat problems which reduces minutes per ticket and compresses the right tail for those categories.<br><br>- Agents spend less time rediscovering solutions which lowers cognitive load and improves consistency for users who receive clear instructions each time.<br><br>- A living knowledge base accelerates onboarding for new hires which protects productivity when staffing changes occur.<br><br>- Better reuse of content reduces escalations which lowers cost and protects SLA outcomes. | Target tail **{_fmt_int(excess)} mins**; even 25% reduction ≈ **{_fmt_int(excess*0.25)} mins saved**. | {evidence_res} |
| **Aging swarm rule (>p75)** | **Phase 1 – Trigger:** - Automatically summon subject matter experts when a case crosses **p75** so expertise is applied at the moment of risk rather than after a breach occurs.<br><br>- Tag the case with a visible banner so the team knows it is time critical and ownership is clear.<br><br>**Phase 2 – Act:** - Run a short daily swarm focused on aged items to accelerate root cause discovery and unblock dependencies quickly.<br><br>- Limit the swarm to twenty minutes to keep the intervention efficient and repeatable.<br><br>**Phase 3 – Track:** - Measure changes in p80 age and tail minutes so the effectiveness of the swarm is quantified and improvements are retained.<br><br>- Share insights from resolved items so upstream fixes can prevent similar aging in the future. | - Early expert attention collapses extreme outliers which reduces breach risk and improves overall SLA performance for complex cases.<br><br>- Short targeted swarms clear bottlenecks without pulling people into long meetings which protects delivery on other work.<br><br>- Tracking the p80 age creates an objective signal that guides whether to continue or adjust the practice so effort is used wisely.<br><br>- Knowledge captured from aged cases improves future triage and prevents repeat delays which compounds savings. | **Saved minutes** on >p75 cohort directly subtract from **{_fmt_int(excess)}**. | Tail cohort is defined by p75 **{_fmt_float(p75)}**. |
| **Root-cause templates** | **Phase 1 – Standardize:** - Create stepwise templates for known faults that include evidence to collect, likely fixes, and validation checks so agents do not miss critical steps.<br><br>- Keep templates lightweight and focused so they are fast to use during live work.<br><br>**Phase 2 – Validate:** - Peer review the templates with senior engineers to confirm accuracy and adjust wording so instructions are unambiguous.<br><br>- Pilot on a small set of tickets and refine based on actual outcomes so adoption is high.<br><br>**Phase 3 – Rollout:** - Coach lower performers to use the templates consistently and make adherence visible so habits stick.<br><br>- Retire outdated templates quickly so noise does not reappear. | - Standard steps reduce variance which shortens average resolution time and makes outcomes more predictable for users and managers.<br><br>- Fewer loops and handoffs reduce total effort which lowers cost and frees senior staff to focus on genuinely novel problems.<br><br>- Clear validation checks reduce reopenings which protect CSAT and avoid extra minutes being added back into the tail.<br><br>- Coaching turns individual improvements into team wide gains which sustains performance. | **Cycle-time delta × case count** in targeted patterns. | Clustered buckets hint at repeatable patterns. |
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Aging SLO tiers** | **Phase 1 – Define:** - Create intervention tiers at p50 p75 and p90 ages so teams know exactly when to escalate actions before a breach occurs.<br><br>- Document who is paged at each tier so responsibility is immediate and unambiguous.<br><br>**Phase 2 – Automate:** - Build alerts and automatic escalations in the tool so the process runs without manual checking and delays.<br><br>- Provide a quiet hours policy for low risk items so noise does not overwhelm responders.<br><br>**Phase 3 – Review:** - Track breach trends and adjust thresholds as the distribution improves so attention remains on the true risk points.<br><br>- Publish outcomes to keep momentum and reinforce good behaviors. | - Earlier interventions prevent breaches which raises SLA attainment and reduces penalty exposure for contracted services.<br><br>- Automation reduces manual monitoring effort which lowers overhead and improves reaction speed when queues grow unexpectedly.<br><br>- Clear tiers reduce confusion during incidents which cuts wasted time and keeps the case moving forward.<br><br>- Continuous review ensures the policy evolves with the data which sustains gains. | **Breach hours avoided** = (# pre-empted × overage hrs). | Tail length represents breach risk surface **{_fmt_int(excess)} mins**. |
| **Queue segmentation by complexity** | **Phase 1 – Split:** - Separate a fast lane for routine fixes from a deep diagnosis lane for complex investigations so simple work does not wait behind difficult items.<br><br>- Define eligibility rules so routing remains quick and fair to users.<br><br>**Phase 2 – Staff:** - Assign skills and tools to each lane so agents handle the right kind of work and avoid context switching that slows them down.<br><br>- Cross train selectively so coverage remains resilient during leave and peaks.<br><br>**Phase 3 – Measure:** - Track cycle time by lane and adjust eligibility if the fast lane slows down so the model remains effective.<br><br>- Share insights across lanes so complex cases benefit from fast lane learnings where applicable. | - Routine tickets resolve faster which lifts overall throughput and reduces average wait time across the board.<br><br>- Complex work gets the focused attention it needs which increases fix quality and reduces reopenings that would extend the tail.<br><br>- Better skill alignment improves agent satisfaction which supports retention and stable performance over time.<br><br>- Measurement ensures the design stays fit for purpose as volumes shift which keeps benefits durable. | **CT delta × volume** per lane. | Mixed queue inflates variance seen in distribution. |
| **After-action reviews (Top 10 aged)** | **Phase 1 – Weekly:** - Review the ten most aged cases every week and capture what specifically blocked progress so fixes can be targeted at real causes.<br><br>- Involve both engineering and process owners so solutions address technical and procedural gaps together.<br><br>**Phase 2 – Fix:** - Implement small changes such as access improvements or vendor escalation paths so recurring blockers disappear quickly.<br><br>- Track the time from fix to impact so successful interventions are repeated faster.<br><br>**Phase 3 – Bake-in:** - Turn recurring lessons into playbooks or policy updates so improvements persist beyond the original cases.<br><br>- Verify that the same problem does not return in the next cycle so learning sticks. | - Continuous improvement reduces the number of extreme outliers which shrinks the right tail and protects SLA performance.<br><br>- Cross functional fixes prevent the same delays from reappearing which lowers cost and saves agent time across many tickets.<br><br>- Quick measurable wins build confidence which increases participation and momentum in the review process.<br><br>- Institutionalized learning raises team capability which improves future incident handling speed. | **Repeat delay mins reduced** across recurring patterns. | Recurring long cases appear in tail buckets. |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Closure quality checklist** | **Phase 1 – Define:** - Specify the essential closure elements including cause fix and validation notes so users understand what changed and why the issue is resolved.<br><br>- Keep the checklist short so compliance is easy during busy periods.<br><br>**Phase 2 – Enforce:** - Introduce reviewer spot checks that give quick feedback so quality rises without slowing throughput.<br><br>- Provide examples of good notes so expectations are concrete for all agents.<br><br>**Phase 3 – Tune:** - Use reopening reasons and survey themes to refine the checklist so it addresses real gaps in communication.<br><br>- Update the template when new failure modes appear so coverage stays complete. | - Clear closure notes reduce confusion which decreases reopenings and the extra minutes they would add back into the queue.<br><br>- Users feel informed which improves satisfaction and reduces follow up questions asking for more details about the fix.<br><br>- Consistent communication builds trust which lowers escalation rate and improves the perception of professionalism.<br><br>- Better records speed future troubleshooting which saves time when similar issues reoccur. | **CSAT uplift × volume**; reopening reduction lowers minutes. | Better notes reduce reopenings that add to the tail. |
| **Appointment windows** | **Phase 1 – Offer:** - Provide scheduled callbacks for complex fixes so coordination happens once and agents do not waste cycles on missed contacts.<br><br>- Present several time options so users can pick a slot that fits their day easily.<br><br>**Phase 2 – Coordinate:** - Confirm user availability and prerequisites in advance so the session can be productive from the first minute.<br><br>- Share a checklist of what to prepare so time is not lost during the call.<br><br>**Phase 3 – Track:** - Monitor no show rate and reschedule speed so the process stays efficient and does not create new delays.<br><br>- Use insights to adjust slot length by issue type so calls are the right size. | - Scheduled contact reduces idle chasing time which accelerates resolution and lowers frustration on both sides of the conversation.<br><br>- Users feel in control which improves satisfaction and reduces complaints about missed communications.<br><br>- Prepared sessions complete faster which shrinks the right tail for complex work and improves SLA outcomes.<br><br>- Measuring the process keeps the experience reliable which maintains confidence in the service. | **Follow-ups avoided × mins** (cuts tail minutes **{_fmt_int(excess)}**). | Long waits frustrate users; scheduled slots reduce friction. |
| **Post-resolution pulse survey** | **Phase 1 – Trigger:** - Send a very short survey at closure so response rates are high and feedback is fresh and specific.<br><br>- Ask one open question so themes are easy to analyze for improvement actions.<br><br>**Phase 2 – Analyze:** - Tag detractor themes and correlate with ticket metadata so fixes target the highest impact issues first.<br><br>- Share a rolling dashboard so trends are visible to teams and leaders.<br><br>**Phase 3 – Act:** - Implement small targeted fixes quickly and call out the changes so users see that feedback leads to improvements.<br><br>- Re measure after changes to verify that perception improves and that tail minutes actually shrink. | - Rapid signals allow fast corrections which improves user perception and reduces repeat dissatisfaction on similar tickets.<br><br>- Focused actions address the root of frustration which lowers complaint volume and improves net promoter tendencies.<br><br>- Visible responsiveness strengthens the relationship between IT and users which increases cooperation during future incidents.<br><br>- Measured loops ensure fixes deliver results which keeps the survey useful rather than perfunctory. | **Detractors flipped × impact**; monitor tail shrink vs CSAT. | Tail reductions should correlate with CSAT improvement. |
"""
                }
                render_cio_tables("CIO — Resolution Time", cio)
        else:
            st.warning("Column 'avg_resolution_time_mins' not found.")

    # ---------------------- 3(c) SLA Adherence (Response & Resolution) ----------------------
    with st.expander("📌 SLA Adherence for Response & Resolution"):
        # Normalize if raw exists
        if "sla_response_resolution" in df_filtered.columns and "sla_rr_norm" not in df_filtered.columns:
            def norm_sla(x):
                if pd.isna(x): return np.nan
                s = str(x).strip().lower()
                if s in {"met","met."}: return "Met"
                if s in {"not met","not_met","not-met","notmet"}: return "Not Met"
                return np.nan
            df_filtered["sla_rr_norm"] = df_filtered["sla_response_resolution"].apply(norm_sla)

        if "sla_rr_norm" in df_filtered.columns:
            sla = df_filtered["sla_rr_norm"].value_counts(dropna=False).reset_index()
            sla.columns = ["SLA_Adherence","records"]
            fig = px.bar(
                sla, x="SLA_Adherence", y="records",
                title="SLA Adherence (Response/Resolution)",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            total = int(sla["records"].sum()) if not sla.empty else 0
            met = int(sla.loc[sla["SLA_Adherence"]=="Met","records"].sum()) if not sla.empty else 0
            not_met = int(sla.loc[sla["SLA_Adherence"]=="Not Met","records"].sum()) if not sla.empty else 0
            miss = int(sla.loc[sla["SLA_Adherence"].isna(),"records"].sum()) if not sla.empty and sla["SLA_Adherence"].isna().any() else 0

            st.markdown("### Analysis – SLA Adherence")
            st.write(f"""
**What this graph is:** A bar chart showing **SLA outcomes** for response/resolution.  
**X-axis:** Outcome (Met / Not Met / Missing).  
**Y-axis:** Number of records.

**What it shows in your data:**  
- **Total rows:** **{_fmt_int(total)}**  
- **Met:** **{_fmt_int(met)}**  
- **Not Met:** **{_fmt_int(not_met)}**  
- **Missing:** **{_fmt_int(miss)}**

**Overall:** A non-trivial **Missing** segment undermines auditability; the **Not Met** bar indicates process and capacity gaps.

**How to read it operationally:**  
- **Plug data holes:** Make SLA fields mandatory at intake.  
- **Chase misses:** Daily owner scorecards for “Not Met”.  
- **Control:** Trend the Met% monthly and tie actions to drift.

**Why this matters:** Clean, high Met% strengthens **trust, compliance, and penalties avoidance**.
""")

            ev_sla = (
                f"Met **{_fmt_int(met)}**, Not Met **{_fmt_int(not_met)}**, Missing **{_fmt_int(miss)}**, Total **{_fmt_int(total)}**."
            )

            cio = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Enforce SLA fields on intake** | **Phase 1 – Validate:** - Make SLA selection mandatory for each service so tickets are born with the correct target and reporting remains accurate from day one.<br><br>- Provide friendly error messages that instruct users how to choose the right SLA so completion is easy.<br><br>**Phase 2 – Block:** - Prevent saving a ticket without the SLA fields so missing data cannot enter the system and create downstream cleanup work.<br><br>- Offer a limited default only for approved emergency paths so rare edge cases do not block operations.<br><br>**Phase 3 – Audit:** - Run a weekly missing data check and notify owners so corrections happen quickly and habits improve over time.<br><br>- Track the missing rate trend so leaders can verify that the process is fixing the root cause. | - Clean intake data reduces rework minutes that would otherwise be spent hunting for targets and updating reports which lowers operational cost.<br><br>- Accurate SLAs enable trustworthy dashboards which supports better decisions and fewer manual reconciliations at month end.<br><br>- Blocking bad saves prevents long tail quality issues which protects analyst time and avoids audit findings later.<br><br>- Regular audits reinforce discipline which sustains the gains beyond the initial rollout. | **Rework minutes avoided** = {_fmt_int(miss)} × lookup mins (your standard). | {ev_sla} |
| **SLA templates by category** | **Phase 1 – Define:** - Establish standard response and resolution targets per service class so similar work receives consistent expectations and compliance is easier to manage.<br><br>- Document exceptions with clear criteria so flexibility exists without sacrificing control.<br><br>**Phase 2 – Default:** - Auto populate SLAs based on the selected category so most tickets are correct without manual effort and agents can focus on solving the issue.<br><br>- Keep the mapping table simple and versioned so changes are safe and auditable.<br><br>**Phase 3 – Exceptions:** - Route deviations through an approval path so leaders can balance business needs against compliance impact in a structured way.<br><br>- Review exceptions quarterly and retire outdated ones so templates remain clean. | - Faster ticket setup reduces handle time which lowers cost and improves speed to first action for users who just want progress quickly.<br><br>- Consistent targets reduce confusion which improves perceived fairness and increases adherence across teams.<br><br>- Automated defaults cut data entry errors which improves reporting accuracy and reduces last minute fixes during audits.<br><br>- Controlled exceptions preserve agility without losing visibility which improves governance quality. | **Setup mins saved × services** configured with templates. | Distribution suggests inconsistency (presence of Missing/Not Met). |
| **Auto-populate from service map** | **Phase 1 – Map:** - Create a service to SLA lookup that reflects contractual commitments so the right target is selected every time a ticket is created.<br><br>- Include ownership and renewal dates so responsibilities are transparent.<br><br>**Phase 2 – Integrate:** - Fill SLA fields automatically during ticket creation using the map so speed and accuracy improve together.<br><br>- Provide a quick override flag for genuine exceptions so the workflow remains smooth.<br><br>**Phase 3 – Monitor:** - Track override rate and investigate categories with frequent changes so root causes are fixed and mappings are updated promptly.<br><br>- Publish a change log so stakeholders understand adjustments. | - Automatic population eliminates manual lookup which saves time and reduces the risk of incorrect targets that would skew compliance metrics.<br><br>- Reliable data improves the credibility of SLA dashboards which reduces disputes and speeds leadership decisions.<br><br>- Monitoring overrides reveals where processes or catalog definitions need improvement which lifts overall system quality.<br><br>- Transparent change history supports audit requirements which reduces compliance workload. | **Lookups avoided × mins** on **{_fmt_int(total)}** records. | Deterministic mapping feasible for standard services. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Owner SLA scorecards** | **Phase 1 – Publish:** - Provide each owner with a scorecard that shows Met and Not Met counts so accountability is visible and progress is trackable by individual and team.<br><br>- Include trends so owners see whether actions are working over time.<br><br>**Phase 2 – Coach:** - Meet with owners whose metrics lag and agree on specific improvements such as routing changes or playbook updates so support is practical.<br><br>- Share quick wins from peers so ideas spread fast.<br><br>**Phase 3 – Incent:** - Link parts of objectives to SLA results so focus remains strong and improvements are rewarded appropriately.<br><br>- Revisit targets annually so they stay challenging and fair. | - Clear ownership drives faster corrective action which improves adherence and reduces the pool of tickets at risk of penalties.<br><br>- Coaching converts weak spots into capability which raises the performance median for the entire team.<br><br>- Positive incentives maintain momentum which protects results long after the initial push.<br><br>- Transparent reporting reduces surprises at review time which strengthens trust. | **SLA uplift** = ΔMet% × {_fmt_int(total)} tickets. | Variation across buckets requires targeted action. |
| **Miss trend tracking** | **Phase 1 – Chart:** - Visualize the miss percentage monthly so leaders can spot drift early and avoid end of quarter surprises that are costly to fix.<br><br>- Segment by category and priority so actions are focused not generic.<br><br>**Phase 2 – Correlate:** - Compare misses with staffing change logs and release calendars so root causes are found and confirmed rather than guessed.<br><br>- Share correlations with teams so fixes have buy in.<br><br>**Phase 3 – Fix:** - Implement targeted interventions such as schedule changes or vendor escalations and track the impact so improvements are proven.<br><br>- Retire ineffective actions quickly so effort is not wasted. | - Early warning prevents prolonged underperformance which protects customer commitments and reduces escalation management effort.<br><br>- Correlation to real events improves problem solving quality which leads to durable fixes rather than short term patches.<br><br>- Targeted actions make better use of limited resources which increases throughput on the work that matters most.<br><br>- Measured impact encourages continuous improvement which stabilizes delivery over time. | **Drift avoidance** measured as reduced Not Met count (**{_fmt_int(not_met)}**). | Miss clusters often align with operational events. |
| **Root-cause loops for misses** | **Phase 1 – Sample:** - Select a representative sample of Not Met cases and analyze why they failed including data quality issues process gaps and technical blockers so the real drivers are understood.<br><br>- Involve both frontline and engineering teams so perspectives are complete.<br><br>**Phase 2 – Remedy:** - Create playbooks policy tweaks or engineering fixes that address the specific causes and implement them with owners and timelines so responsibility is clear.<br><br>- Communicate the change to all affected teams so adoption is rapid.<br><br>**Phase 3 – Verify:** - Re measure the same cohorts after the fixes land so the reduction in misses is visible and attributable to the action.<br><br>- Capture the learning in documentation so improvements persist. | - Systematic analysis replaces guesswork which yields higher quality fixes and more consistent SLA achievement across categories.<br><br>- Targeted remedies reduce repeat misses which lowers customer complaints and reduces time spent on escalations.<br><br>- Verification creates confidence that actions work which motivates teams to keep improving the process.<br><br>- Documented learning spreads improvements to adjacent areas which multiplies the effect of each root cause effort. | **Repeat miss mins reduced** across studied cohort. | Not Met bar (**{_fmt_int(not_met)}**) marks improvement pool. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **External SLA visibility** | **Phase 1 – Portal:** - Give stakeholders a simple page that shows the current SLA state for their tickets so they do not need to chase updates and can self serve status at any time.<br><br>- Include clear legends so non technical users understand what they are seeing quickly.<br><br>**Phase 2 – Alerts:** - Provide risk warnings when a ticket approaches breach so users can help unblock dependencies and feel included in the solution.<br><br>- Allow opt in levels so noise remains manageable for different audiences.<br><br>**Phase 3 – Reports:** - Send monthly summaries that show trends and wins so confidence grows and conversations are based on the same numbers.<br><br>- Archive reports so history is available for governance reviews. | - Visibility reduces inbound queries which saves time for both users and agents while improving the sense of transparency and partnership.<br><br>- Early warnings enable collaborative action which reduces breaches and improves user perception of control and fairness.<br><br>- Regular summaries keep leadership aligned which reduces conflict over the facts and speeds decision making.<br><br>- Historical access supports compliance reviews which reduces the effort required during audits. | **Queries avoided × mins** over **{_fmt_int(total)}** records. | Visibility reduces confusion around Met/Not Met counts. |
| **Breach communications** | **Phase 1 – Notify:** - When a breach is inevitable send a proactive notice that explains the situation and the next steps so expectations are managed and trust is preserved.<br><br>- Provide a realistic new ETA and action plan so the user knows the path forward.<br><br>**Phase 2 – Offer:** - Offer mitigations such as workarounds or temporary access so the business impact is reduced while the root cause is fixed.<br><br>- Record acceptance of the plan so everyone remains aligned.<br><br>**Phase 3 – Track:** - Monitor complaint rates and follow through on post breach actions so confidence is rebuilt and the same issue does not repeat unnoticed.<br><br>- Share lessons in a brief note so transparency remains high. | - Proactive updates lower frustration which reduces the likelihood of formal complaints and escalation time that would otherwise consume leadership attention.<br><br>- Offering mitigations protects the user’s ability to work which preserves productivity and reduces perceived severity of the breach.<br><br>- Clear tracking after the event shows accountability which repairs trust and improves future interactions with the service team.<br><br>- Documented lessons help prevent similar breaches which raises satisfaction over time. | **Complaints avoided × mins**; link to **{_fmt_int(not_met)}** misses. | Miss clusters demand comms to protect CSAT. |
| **Celebrate SLA wins** | **Phase 1 – Share:** - Publicize teams and individuals who consistently hit targets so good behaviors are visible and reinforced by leadership recognition.<br><br>- Include specific practices they used so others can adopt them quickly.<br><br>**Phase 2 – Replicate:** - Turn these practices into simple checklists or scripts and roll them out to similar teams so standards rise across the board.<br><br>- Provide coaching sessions where peers explain how they applied the practices in real scenarios.<br><br>**Phase 3 – Sustain:** - Recognize achievements monthly and rotate focus so multiple groups are encouraged to participate and keep improving.<br><br>- Track whether replication closes gaps so recognition is tied to outcomes not just activity. | - Positive recognition boosts morale which encourages sustained adherence and reduces turnover that would otherwise reset team performance.<br><br>- Replication accelerates improvement across teams which raises the overall Met percentage and stabilizes service reliability for users.<br><br>- Practical checklists make success easy to copy which converts isolated wins into standard practice without heavy process overhead.<br><br>- Ongoing celebration keeps attention on the right behaviors which maintains satisfaction even as targets get tougher. | **Retention uplift** where tracked. | Met bucket (**{_fmt_int(met)}**) supports positive comms. |
"""
            }
            render_cio_tables("CIO — SLA (Response & Resolution)", cio)
        else:
            st.info("SLA adherence not available/normalized.")
