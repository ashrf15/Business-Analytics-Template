# ================================================================
# utils_security_metrics/recommendation_performance/security_metrics.py
# ================================================================
import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import re

# ---------------- Mesiniaga palette (blue/white) ----------------
MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#9BD1FF"]
PRIMARY_BLUE = "#007ACC"

# ============================================================
# Helper
# ============================================================
def render_cio_tables(title, cio):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio.get("cost", ""), unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio.get("performance", ""), unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio.get("satisfaction", ""), unsafe_allow_html=True)

def _fmt(d):
    try:
        return pd.to_datetime(d).strftime("%d/%m/%Y")
    except Exception:
        return str(d)

def _fmt_i(x):
    try:
        return f"{int(x):,}"
    except Exception:
        return "0"

def _fmt_f(x, d=1):
    try:
        return f"{float(x):.{d}f}"
    except Exception:
        return "0.0"

# ============================================================
# MAIN
# ============================================================
def security_metrics(df_filtered: pd.DataFrame):

    # ---------------- 7.1 Security Incidents ----------------
    with st.expander("📌 Security Incidents Detected and Resolved"):
        need = {"report_date", "security_incidents"}
        if need.issubset(df_filtered.columns):
            df = df_filtered.dropna(subset=["security_incidents"]).copy()
            df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
            daily = (
                df.groupby(df["report_date"].dt.date)["security_incidents"]
                .sum()
                .reset_index()
            )

            fig = px.line(
                daily,
                x="report_date",
                y="security_incidents",
                title="Security Incidents Over Time",
                labels={"report_date": "Date", "security_incidents": "Number of Incidents"},
                markers=True,
                color_discrete_sequence=MES_BLUE,
                template="plotly_white",
            )
            st.plotly_chart(fig, use_container_width=True)

            if not daily.empty:
                total = int(daily["security_incidents"].sum())
                avg = daily["security_incidents"].mean()
                peak = daily.loc[daily["security_incidents"].idxmax()]
                low  = daily.loc[daily["security_incidents"].idxmin()]
                change = ((peak["security_incidents"] - max(low["security_incidents"], 0)) /
                          max(low["security_incidents"], 1)) * 100

                st.markdown("### Analysis")
                st.write(f"""
**What this graph is:** A daily **throughput line chart** of **security incidents detected/resolved**.  
**X-axis:** Calendar date.  
**Y-axis:** Count of incidents per day.

**What it shows in your data:**  
- **Largest incident day:** **{_fmt(peak['report_date'])}** with **{_fmt_i(peak['security_incidents'])}** incidents.  
- **Lowest incident day:** **{_fmt(low['report_date'])}** with **{_fmt_i(low['security_incidents'])}** incidents.  
- **Average over period:** **{_fmt_f(avg,1)} incidents/day**; **Total:** **{_fmt_i(total)}** incidents.  
- **Relative spread (peak vs low):** **{_fmt_f(change,1)}%**.

**Overall:** Sustained declines imply **effective prevention/hardening**; sudden spikes usually reflect **campaigns, scans, or misconfigurations**.

**How to read it operationally:**  
- **Gap = risk surface:** The height difference between peak and average shows **excess response load** that needs surge capacity.  
- **Lead–lag with changes:** Overlay change calendar; post-change spikes flag **release regressions**.  
- **Recovery strength:** Faster drops after spikes mean **better containment and playbooks**.

**Why this matters:** Every spike burns analyst hours and increases **MTTR (mean time to recover)** risk; smoothing this curve cuts cost and stabilizes posture.
""")

                evidence = (
                    f"Peak {_fmt(peak['report_date'])}: {_fmt_i(peak['security_incidents'])}; "
                    f"Low {_fmt(low['report_date'])}: {_fmt_i(low['security_incidents'])}; "
                    f"Average {_fmt_f(avg,1)}/day; Total {_fmt_i(total)}."
                )

                # --- CIO tables (>=3 recs each, phased, with real values) — Benefits expanded; Phases elaborated
                cio = {
                    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Patch fast-lane for peak-day services** | **Phase 1:** Identify the exact services and assets implicated on **{_fmt(peak['report_date'])}** by correlating incident tickets, SIEM events, and CMDB ownership. Produce a short list of high-impact candidates with known vulnerabilities or misconfigurations. **Phase 2:** Prioritize emergency patching and baseline configuration hardening for those candidates and schedule changes in the earliest safe window with backout plans prepared. **Phase 3:** Re-scan the affected assets and monitor for 48–72 hours to confirm that daily incident counts drop back toward the average by the next reporting cycle. | - Reduces the number of repeatable incidents which directly lowers the analyst time spent on triage and containment. <br><br> - Lowers overtime requirements during surge periods because fixes are applied to the assets that drive the highest incident volume. <br><br> - Improves infrastructure stability which reduces unplanned service interruptions and protects downstream teams from disruption. | **Analyst minutes avoided** ≈ (excess incidents on peak **{_fmt_i(peak['security_incidents'] - max(int(avg),0))}** × avg triage mins). | {evidence} |
| **Consolidate redundant detection rules** | **Phase 1:** Review SIEM and EDR content to find overlapping correlation rules and signatures that trigger on the same benign patterns and document their sources and thresholds. **Phase 2:** Tune thresholds and de-duplicate or retire rules that add noise without new signal while keeping coverage for true positives. **Phase 3:** Run a monthly false positive review using sampled alerts to ensure noise remains under the agreed control limit. | - Cuts alert fatigue for analysts which improves focus on genuine threats and reduces burnout. <br><br> - Frees engineering time that was previously spent chasing non-actionable alerts which increases capacity for proactive improvements. <br><br> - Lowers tooling and operational overhead because fewer alerts pass through downstream enrichment and ticketing. | **Time saved** = (alerts removed × avg review mins) derived from spike vs mean gap **{_fmt_i(peak['security_incidents'])}−{_fmt_f(avg,1)}**. | {evidence} |
| **Blocklist surge automation** | **Phase 1:** During spike conditions automatically enrich indicators of compromise using threat intel and asset context so decisions to block are fast and evidence based. **Phase 2:** Push temporary block rules to the relevant controls such as firewalls, proxies, or EDR with expiries to avoid long term drift. **Phase 3:** Validate that incident counts taper and expire or refine rules once the wave subsides to maintain a clean ruleset. | - Speeds up containment during high volume waves which reduces the total number of incidents that need full investigation. <br><br> - Shrinks the spike area above the average which stabilizes service levels during campaigns. <br><br> - Protects analyst capacity so strategic work continues even when the environment is noisy. | **Containment mins saved** = (Δincidents post-automation × avg response mins). | Spike magnitude indicates urgent containment need. |
""",
                    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Incident templates & playbooks** | **Phase 1:** Mine recurring incident signatures and group them by pattern such as phishing, brute force, and malware to establish clear categories. **Phase 2:** Pre-fill playbooks with containment, eradication, and validation steps including example commands and success criteria. **Phase 3:** Train analysts and enforce the use of templates during spikes with quick retros to update steps after each wave. | - Lowers mean time to acknowledge and mean time to recover because analysts follow a proven path without hesitation. <br><br> - Produces consistent outcomes across shifts which reduces variance and rework. <br><br> - Improves recovery speed on peak days which prevents backlog growth in security operations queues. | **MTTR reduction mins** = (baseline mins − templated mins) × incidents on **{_fmt(peak['report_date'])}** (**{_fmt_i(peak['security_incidents'])}**). | {evidence} |
| **Correlate spikes with change windows** | **Phase 1:** Overlay the change calendar onto the incident trend to detect temporal correlations between deployments and spikes. **Phase 2:** When correlations are found implement pre-deploy checks such as configuration linting and security tests to catch regressions earlier. **Phase 3:** Gate risky changes with additional approvals or canary rollouts when the environment already shows elevated incident levels. | - Prevents release driven regressions which directly reduces incident spikes and stabilizes service. <br><br> - Improves cross team accountability which accelerates corrective actions when a change is implicated. <br><br> - Protects SLAs by avoiding stacked failures during already stressful periods. | **Incidents avoided** = (peak − mean) ≈ **{_fmt_i(peak['security_incidents'] - int(round(avg)))}**. | {evidence} |
| **Threat-intel driven suppression** | **Phase 1:** Tag known benign scanners and internal synthetic probes so their events are recognized by analytics as non-actionable. **Phase 2:** Suppress or downgrade alerts originating from these benign sources while maintaining the ability to audit the decision. **Phase 3:** Audit the suppression list quarterly to ensure that no malicious behaviors are accidentally hidden. | - Increases the signal to noise ratio so analysts spend time on incidents that matter most. <br><br> - Shortens triage time because benign patterns are filtered automatically before they reach the queue. <br><br> - Builds a cleaner dataset for threat hunting and reporting which improves overall detection quality. | **Noise cut mins** = (suppressed alerts × review mins). | Repeating small spikes imply benign sources. |
""",
                    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Real-time stakeholder status during spikes** | **Phase 1:** Automatically notify the owners of affected services on **{_fmt(peak['report_date'])}** with a concise status including scope, impact, and initial actions. **Phase 2:** Publish a live dashboard with ETA to containment and key indicators so stakeholders can self serve updates. **Phase 3:** Issue a short post mortem the next business day to close the loop and capture lessons learned. | - Reduces panic calls to support because stakeholders have timely and credible information. <br><br> - Improves trust in the security response process which calms operational teams during tense periods. <br><br> - Cuts ad hoc briefing time for leaders which allows responders to focus on remediation. | **Tickets/queries avoided** = (pre post avg × spike day delta **{_fmt_i(peak['security_incidents'] - int(round(avg)))}**). | {evidence} |
| **Executive incident digest** | **Phase 1:** Provide a daily one pager that lists counts, likely causes, and top actions using non technical language. **Phase 2:** Highlight current risks and the specific decisions or approvals required from leadership. **Phase 3:** Track the trend to closure so leadership sees progress without repeated meetings. | - Aligns leaders quickly which accelerates approvals for containment and remediation. <br><br> - Reduces the number of ad hoc briefings needed which saves time for both executives and responders. <br><br> - Increases organisational confidence because communication is predictable and clear. | **Hours saved** = (#briefings replaced × mins per briefing). | {evidence} |
| **User guidance on common threats** | **Phase 1:** After each spike publish quick tips focused on the observed vector such as phishing or credential stuffing. **Phase 2:** Target the guidance to the user groups most exposed and include screenshots of what to look for. **Phase 3:** Refresh and redistribute monthly to maintain awareness as tactics evolve. | - Lowers user driven incident rates because people can recognize and report suspicious activity earlier. <br><br> - Improves hygiene such as password and patching behavior which reduces exploitable surface area. <br><br> - Supports a culture of shared responsibility which strengthens overall security posture. | **Incidents avoided** from user vectors × avg handling mins. | Peaks tied to phishing or misconfig can be reduced with guidance. |
"""
                }
                render_cio_tables("Security Incidents", cio)
        else:
            st.warning("Missing columns: 'report_date' and/or 'security_incidents'.")

    # ---------------- 7.2 Vulnerability Scans ----------------
    with st.expander("📌 Vulnerabilities Found"):
        need = {"report_date", "vulnerabilities_found"}
        if need.issubset(df_filtered.columns):
            df = df_filtered.dropna(subset=["vulnerabilities_found"]).copy()
            df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
            daily = (
                df.groupby(df["report_date"].dt.date)["vulnerabilities_found"]
                .sum()
                .reset_index()
            )

            fig = px.line(
                daily,
                x="report_date",
                y="vulnerabilities_found",
                title="Vulnerabilities Found Over Time",
                labels={"report_date": "Date", "vulnerabilities_found": "Count"},
                markers=True,
                color_discrete_sequence=MES_BLUE,
                template="plotly_white",
            )
            st.plotly_chart(fig, use_container_width=True)

            if not daily.empty:
                total = int(daily["vulnerabilities_found"].sum())
                avg = daily["vulnerabilities_found"].mean()
                peak = daily.loc[daily["vulnerabilities_found"].idxmax()]
                low  = daily.loc[daily["vulnerabilities_found"].idxmin()]
                change = ((peak["vulnerabilities_found"] - max(low["vulnerabilities_found"], 0)) /
                          max(low["vulnerabilities_found"], 1)) * 100

                st.markdown("### Analysis")
                st.write(f"""
**What this graph is:** A daily **findings trend** from vulnerability scans.  
**X-axis:** Calendar date.  
**Y-axis:** Number of findings.

**What it shows in your data:**  
- **Largest finding day:** **{_fmt(peak['report_date'])}** with **{_fmt_i(peak['vulnerabilities_found'])}** findings.  
- **Lowest finding day:** **{_fmt(low['report_date'])}** with **{_fmt_i(low['vulnerabilities_found'])}** findings.  
- **Average/Total:** **{_fmt_f(avg,1)} per day**, **{_fmt_i(total)}** findings overall.  
- **Relative spread:** **{_fmt_f(change,1)}%** between extremes.

**Overall:** Downward slope indicates **risk burn-down**; sudden jumps often reflect **new assets**, **policy changes**, or **scanner scope drift**.

**How to read it operationally:**  
- **Gap targeting:** Prioritize the **asset cohorts** driving peaks for fastest risk reduction.  
- **Signal quality:** Check for duplicated jobs when small oscillations persist.  
- **Velocity:** Track weekly burn-down to ensure **fix rate ≥ find rate**.

**Why this matters:** Findings convert directly into **remediation workload** and **audit exposure**; sustained peaks inflate backlog and compliance risk.
""")

                evidence = (
                    f"Peak {_fmt(peak['report_date'])}: {_fmt_i(peak['vulnerabilities_found'])}; "
                    f"Low {_fmt(low['report_date'])}: {_fmt_i(low['vulnerabilities_found'])}; "
                    f"Average {_fmt_f(avg,1)}/day; Total {_fmt_i(total)}."
                )

                cio = {
                    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Prioritize hardening of peak-day assets** | **Phase 1:** Identify the specific hosts and applications that contributed to **{_fmt_i(peak['vulnerabilities_found'])}** findings on **{_fmt(peak['report_date'])}** using scanner asset maps and tags. **Phase 2:** Apply secure baseline templates and critical patches to those assets with change windows aligned to business impact. **Phase 3:** Re-scan within the next cycle and verify that findings drop toward the mean and that exceptions are documented. | - Lowers repeated remediation effort by addressing the assets that generate the most findings first. <br><br> - Reduces the number of tickets that flow into ITSM because common baseline issues are fixed at source. <br><br> - Decreases audit remediation cost because evidence shows targeted burn down of the highest risk cohorts. | **Fix minutes saved** = (peak − mean ≈ **{_fmt_i(peak['vulnerabilities_found'] - int(round(avg)))}**) × avg fix mins. | {evidence} |
| **Merge overlapping scanner jobs** | **Phase 1:** Consolidate scan schedules and scopes to eliminate duplicated coverage across networks and tags while preserving critical depth. **Phase 2:** Remove duplicate or conflicting jobs and standardize credential use so results are consistent. **Phase 3:** Publish a weekly coverage report that shows gaps and overlaps to keep the plan optimized. | - Reduces compute and licensing consumption because fewer redundant scans are executed across the same assets. <br><br> - Cuts duplicate findings which shortens analyst time spent on deduplication and triage. <br><br> - Produces cleaner pipelines so downstream ticketing and reporting are more accurate. | **Time saved** = (duplicated runs × avg scan duration). | Small, regular oscillations imply overlap. |
| **Golden image refresh cadence** | **Phase 1:** Update base images at an agreed quarterly cadence with the latest patches and security controls built in. **Phase 2:** Bake standard configurations into the images and enforce provenance checks during build and deployment. **Phase 3:** Monitor the proportion of new hosts created from approved images and investigate deviations. | - Reduces baseline vulnerabilities on newly provisioned systems which shrinks the inflow of findings. <br><br> - Speeds provisioning because secure defaults are pre applied and require fewer post build fixes. <br><br> - Minimizes configuration drift which keeps environments closer to the target standard. | **Findings avoided** = (% drop on new images × volume). | Peaks tied to new host onboarding. |
""",
                    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Automate scan→ticket de-duplication** | **Phase 1:** Integrate the scanner with ITSM so each unique vulnerability instance maps to a single ticket across re scans. **Phase 2:** Use hashing or signature based deduplication to merge repeats and preserve history within one record. **Phase 3:** Track backlog shrinkage and SLA performance to verify throughput gains. | - Speeds triage because analysts work on consolidated records rather than many duplicates for the same issue. <br><br> - Stabilizes queues which improves the ability to focus on the highest risk items. <br><br> - Improves SLA adherence because effort is concentrated on closing actual exposures. | **Tickets avoided** = (duplicates before − after) proxied by (peak − mean **{_fmt_i(peak['vulnerabilities_found'] - int(round(avg)))}**). | {evidence} |
| **Risk burn-down dashboard** | **Phase 1:** Build a weekly trend view that shows new findings, closures, and net movement with filters by owner and asset group. **Phase 2:** Tag owners and due dates directly on items and surface breaches automatically. **Phase 3:** Provide an executive view that highlights risk reduction and blockers for decision making. | - Maintains focus on sustained reduction so fixes outpace new findings over time. <br><br> - Improves accountability by making ownership visible and time bound. <br><br> - Enables quicker decisions on blockers which accelerates burn down. | **Velocity uplift** = (findings closed per week increase). | {evidence} |
| **SLA tiers by severity** | **Phase 1:** Define fix windows by CVSS or business criticality with clear timing for critical, high, medium, and low issues. **Phase 2:** Trigger auto alerts as items approach breach and include clear next actions for owners. **Phase 3:** Escalate overdue items and review exceptions weekly. | - Raises the fix rate for the most dangerous issues which lowers exploit windows. <br><br> - Provides predictable expectations for teams which improves planning and compliance. <br><br> - Reduces last minute firefighting because owners act before breaches occur. | **Breach mins avoided** = (critical overdue × avg overdue mins). | Peaks dominated by severe items demand tiers. |
""",
                    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Monthly “risk reduction” snapshot** | **Phase 1:** Create an executive friendly summary that explains the trend and highlights top risk reductions. **Phase 2:** Show the percentage drop from the peak of **{_fmt_i(peak['vulnerabilities_found'])}** to make progress tangible. **Phase 3:** Link to assurance notes that describe how residual risks are being managed. | - Builds confidence that vulnerabilities are being reduced in a measurable way which improves stakeholder support. <br><br> - Lowers the volume of clarification requests because the core story is delivered proactively. <br><br> - Clarifies priorities so teams focus on the areas that move the needle. | **Queries avoided** = (pre post average inquiries). | {evidence} |
| **Recognize teams closing most vulns** | **Phase 1:** Publish simple leaderboards that credit teams for closing findings quickly and completely. **Phase 2:** Share best practices from top performers so others can adopt the same methods. **Phase 3:** Replicate successes across similar environments and track the resulting improvement. | - Encourages consistent remediation behavior which accelerates overall burn down. <br><br> - Improves morale by acknowledging effective work which helps sustain velocity. <br><br> - Spreads proven techniques which raises the average performance of all teams. | **Throughput uplift** = (findings closed increase per team). | Downtrend after recognition validates effect. |
| **Stakeholder education on root causes** | **Phase 1:** Brief application and infrastructure teams on whether findings are driven by patching gaps, misconfigurations, or dependency issues. **Phase 2:** Provide concise checklists for the top two causes so prevention becomes routine. **Phase 3:** Track adoption and adjust the materials based on feedback. | - Reduces repeat findings from the same cause because teams learn how to prevent them in daily work. <br><br> - Smooths audit cycles because evidence shows preventive practices are embedded. <br><br> - Improves cross team collaboration by giving everyone the same language and expectations. | **Repeat findings avoided** × avg fix mins. | Recurrent categories drive peaks. |
"""
                }
                render_cio_tables("Vulnerability Scan Results", cio)
        else:
            st.warning("Missing columns: 'report_date' and/or 'vulnerabilities_found'.")

    # ---------------- 7.3 Compliance ----------------
    with st.expander("📌 Compliance with Security Policies"):
        # 1) Normalize column names in-scope to be extra safe
        norm_map = {c: re.sub(r"[^\w]+", "_", c.strip().lower()) for c in df_filtered.columns}
        df_sec = df_filtered.rename(columns=norm_map).copy()

        required = ["report_date", "compliance_status"]
        missing = [c for c in required if c not in df_sec.columns]

        if missing:
            st.error(f"Missing required column(s): {', '.join(missing)}")
            st.caption(f"Available columns: {', '.join(df_sec.columns)}")
        else:
            # 2) Parse date safely
            df_sec["report_date"] = pd.to_datetime(df_sec["report_date"], errors="coerce")

            # 3) Map compliance_status → boolean
            status_map = {
                "compliant": True, "yes": True, "pass": True, "true": True, "1": True,
                "non-compliant": False, "non compliant": False, "no": False, "fail": False, "false": False, "0": False
            }
            df_sec["is_compliant"] = (
                df_sec["compliance_status"]
                .astype(str).str.strip().str.lower()
                .map(status_map)
            )

            # 4) Drop rows without date or mapped status
            df_sec = df_sec.dropna(subset=["report_date", "is_compliant"])

            if df_sec.empty:
                st.info("No valid compliance records after parsing date and status. Check source values (e.g., 'Compliant' / 'Non-Compliant').")
            else:
                # 5) Aggregate daily compliance rate
                daily = (
                    df_sec
                    .groupby(df_sec["report_date"].dt.date, as_index=False)["is_compliant"]
                    .mean()
                    .rename(columns={"report_date": "date", "is_compliant": "compliance_rate"})
                )
                daily["compliance_rate"] *= 100.0

                # 6) Plot
                fig = px.line(
                    daily,
                    x="date", y="compliance_rate",
                    title="Compliance Rate Over Time",
                    labels={"date": "Date", "compliance_rate": "Compliance (%)"},
                    markers=True,
                    color_discrete_sequence=MES_BLUE,
                    template="plotly_white",
                )
                st.plotly_chart(fig, use_container_width=True)

                # 7) Dynamic analysis (safe formatting)
                if not daily.empty:
                    mean_val = daily["compliance_rate"].mean()
                    peak_row = daily.loc[daily["compliance_rate"].idxmax()]
                    low_row  = daily.loc[daily["compliance_rate"].idxmin()]

                    peak_date = pd.to_datetime(peak_row["date"]).strftime("%d/%m/%Y")
                    low_date  = pd.to_datetime(low_row["date"]).strftime("%d/%m/%Y")
                    change_pct = ((peak_row["compliance_rate"] - low_row["compliance_rate"]) /
                                  max(low_row["compliance_rate"], 1.0)) * 100.0

                    st.markdown("### Analysis")
                    st.write(f"""
**What this graph is:** A **daily line chart** of **policy compliance (%)**.  
**X-axis:** Calendar date.  
**Y-axis:** Compliance rate (higher is better).

**What it shows in your data:**  
- **Peak compliance:** **{_fmt_f(peak_row['compliance_rate'],1)}%** on **{peak_date}**.  
- **Lowest compliance:** **{_fmt_f(low_row['compliance_rate'],1)}%** on **{low_date}**.  
- **Average:** **{_fmt_f(mean_val,1)}%**; **Spread:** **{_fmt_f(change_pct,1)}%** between extremes.

**Overall:** Sustained high compliance implies strong governance; dips often coincide with **patch windows** or **audit remediation**.

**How to read it operationally:**  
- **Control banding:** Keep daily values within a narrow band around the average to reduce audit surprises.  
- **Owner variance:** Break down by owner/unit to find chronic under-performance.  
- **Drift detection:** Add alerts when falling below **policy threshold**.

**Why this matters:** Compliance slippage drives **audit findings**, **penalties**, and **manual rework**—stability saves money and reputation.
""")

                    evidence = (
                        f"Peak {peak_date}: {_fmt_f(peak_row['compliance_rate'],1)}% vs "
                        f"Low {low_date}: {_fmt_f(low_row['compliance_rate'],1)}%; "
                        f"Mean {_fmt_f(mean_val,1)}%."
                    )

                    cio = {
                        "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Auto-remediate common drifts** | **Phase 1:** Detect repeat deviations at their source by tagging the configuration keys that most often fall out of policy and linking them to the responsible teams. **Phase 2:** Script automated fixes using policy as code so standard deviations can be corrected without manual effort in a controlled way. **Phase 3:** Schedule weekly runs and validate that the low day of **{low_date}** moves closer to the mean in subsequent weeks. | - Reduces manual audit checks because standard drifts are corrected automatically before auditors request evidence. <br><br> - Lowers engineer time spent on repetitive remediation tasks which frees capacity for higher value work. <br><br> - Decreases audit costs by presenting a consistent record of automatic correction and improvement. | **Manual checks avoided** = (pre post drift count × avg mins per check) concentrated around low **{low_date}** (**{_fmt_f(low_row['compliance_rate'],1)}%**). | {evidence} |
| **Centralize policy configuration** | **Phase 1:** Consolidate scattered policy configurations into golden repositories with code review and version control. **Phase 2:** Apply the templates at build time so new assets inherit compliant settings by default and deviations require explicit exceptions. **Phase 3:** Monitor drift rate against the baseline and report units with recurring variance. | - Reduces misconfiguration events which helps the daily compliance trend remain closer to the average. <br><br> - Speeds recovery to the mean after changes because standard templates are easy to reapply. <br><br> - Simplifies reviews since auditors can trace policy provenance and approvals quickly. | **Config errors avoided** × avg remediation mins, comparing to mean **{_fmt_f(mean_val,1)}%** baseline. | {evidence} |
| **Backfill & enforce metadata** | **Phase 1:** Ensure that all assets have owners and tags so non compliant items can be routed accurately to accountable teams. **Phase 2:** Block commits and infrastructure changes that lack required metadata so gaps do not grow. **Phase 3:** Publish a weekly completeness report and chase long tail assets until coverage reaches the target. | - Speeds root cause analysis because responsible teams are known and can act quickly. <br><br> - Lowers audit toil because evidence can be grouped and retrieved by owner without manual searching. <br><br> - Enables targeted fixes that close gaps faster which lifts the overall compliance rate. | **Lookup mins avoided** = (assets without owner × mins per lookup). | Dips often track unmapped ownership. |
""",
                        "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Owner-level compliance dashboards** | **Phase 1:** Expose per owner compliance rates with drill downs to asset lists so teams can see precisely where to act. **Phase 2:** Hold a short monthly review with each owner to agree actions and deadlines for improvement. **Phase 3:** Recognize improvements publicly to reinforce the right behavior. | - Drives faster response to deviations because accountability is clear and progress is visible. <br><br> - Sustains compliance levels near the peak which reduces volatility across the period. <br><br> - Encourages a healthy competition that raises the overall baseline. | **Potential uplift** ≈ (peak − mean) = **{_fmt_f(peak_row['compliance_rate'] - mean_val,1)} pp**. | {evidence} |
| **Compliance SLO alerts** | **Phase 1:** Set a clear daily target such as ninety five percent with thresholds for warning and breach. **Phase 2:** Send automatic alerts to owners when their rate falls below the target with a link to the affected assets. **Phase 3:** Review breaches weekly and record the actions that brought the rate back into the control band. | - Maintains steady adherence by prompting action as soon as drift begins. <br><br> - Enables earlier interventions that are cheaper and less disruptive than large corrections. <br><br> - Improves predictability for audits because fewer days fall below the target. | **Breaches reduced** = (days below target before versus after). | {evidence} |
| **Pre-change compliance gating** | **Phase 1:** Add a control that checks team and environment compliance before deployment and records the result on the change ticket. **Phase 2:** Block or require additional approvals for changes when the rate is below the threshold so risk does not compound. **Phase 3:** Provide a fast fix path for minor drifts to minimize delays. | - Prevents dips after changes by ensuring risky environments are corrected before further modifications. <br><br> - Protects the overall trend from unnecessary volatility which keeps the average high. <br><br> - Reduces rework because fewer changes need to be rolled back due to policy violations. | **Dips avoided** around low **{low_date}**. | {evidence} |
""",
                        "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Plain-language compliance reports** | **Phase 1:** Summarize compliance in non technical terms that describe risk and impact for business stakeholders. **Phase 2:** Share a monthly report that includes the main drivers of change and the plan for the next month. **Phase 3:** List concrete next steps with owners so readers know what will happen next. | - Builds confidence in governance because stakeholders can understand the message without translation. <br><br> - Reduces clarification requests which saves time for security and audit teams. <br><br> - Helps managers plan work because expectations are clear and time bound. | **Queries avoided** = (pre post information requests). | {evidence} |
| **Quarterly compliance briefings** | **Phase 1:** Present the trend graphs showing peaks lows and the average using a consistent format. **Phase 2:** Highlight the most important improvements achieved and the remaining gaps with realistic timelines. **Phase 3:** Agree on the remediation priorities and record decisions to track in the next briefing. | - Increases transparency which lowers concern and resistance to governance changes. <br><br> - Improves stakeholder alignment because decisions are made with shared data. <br><br> - Reduces the need for ad hoc meetings because cadence and content are predictable. | **Meeting hours saved** from ad hoc reviews. | {evidence} |
| **Self-service owner views** | **Phase 1:** Provide a portal where each team can view their compliance rate and drill down to affected assets and controls. **Phase 2:** Allow owners to download action lists with due dates to streamline execution. **Phase 3:** Include an SLA to remediate items and show timers to encourage timely closure. | - Clarifies ownership which reduces delays caused by uncertainty about who should act. <br><br> - Speeds fixes because teams have direct access to accurate lists and deadlines. <br><br> - Lowers escalations since progress is visible and measurable by everyone involved. | **Escalations avoided** after below target days near **{low_date}**. | {evidence} |
"""
                    }
                    render_cio_tables("Compliance with Security Policies", cio)
