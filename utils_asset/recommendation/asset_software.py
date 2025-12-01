import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ============================================================
# Helpers
# ============================================================
def _safe_nunique(df, col):
    return df[col].nunique() if col in df.columns else 0

def _exists(df, col):
    return col in df.columns and df[col].notna().any()

def _choose_first_present(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def _fmt_int(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return "0"

def _fmt_float(x, places=1):
    try:
        return f"{float(x):.{places}f}"
    except Exception:
        return "0"

def _period_month(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.to_period("M").astype(str)

def render_cio_tables(title, cio):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio.get("cost", "Data not available."), unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio.get("performance", "Data not available."), unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio.get("satisfaction", "Data not available."), unsafe_allow_html=True)


# ============================================================
# Target 3 – Software Assets
# ============================================================
def asset_software(df_filtered: pd.DataFrame):
    df = df_filtered.copy()

    # Normalize
    for c in ["os", "av_status", "av_version", "warranty_end", "department",
              "software_name", "version", "license_type", "license_key",
              "installation_date", "license_expiration_date"]:
        if c in df.columns and df[c].dtype == "O":
            df[c] = df[c].astype(str).str.strip().replace({"nan": np.nan, "": np.nan})
    for c in ["warranty_end", "installation_date", "license_expiration_date", "update_on", "warranty_start"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    # Column proxies
    col_software = _choose_first_present(df, ["software_name", "os", "product_number", "model"])
    col_version = _choose_first_present(df, ["version", "av_version"])
    col_lic_type = _choose_first_present(df, ["license_type", "av_status"])
    col_lic_count = _choose_first_present(df, ["license_count"])
    col_inst_date = _choose_first_present(df, ["installation_date", "update_on", "warranty_start"])
    col_exp_date = _choose_first_present(df, ["license_expiration_date", "license_end", "warranty_end"])
    col_usage = _choose_first_present(df, ["usage_hours", "usage_metric"])
    col_dept = _choose_first_present(df, ["department"])

    # --------------------------------------------------------------------
    # Software Inventory Overview
    # --------------------------------------------------------------------
    with st.expander("📌 Software Inventory Overview (Name & License Count)"):
        evidence_bits = []
        if col_software:
            sw_counts = (
                df[col_software]
                .fillna("(unknown)")
                .value_counts(dropna=False)
                .reset_index()
            )
            sw_counts.columns = [col_software, "count"]
            sw_counts = sw_counts.sort_values("count", ascending=False)

            if not sw_counts.empty:
                fig = px.bar(
                    sw_counts.head(20), x=col_software, y="count", text="count",
                    title=f"Top 20 Installed Software ({col_software})"
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

                total = int(sw_counts["count"].sum())
                top = sw_counts.iloc[0]
                low = sw_counts.iloc[-1]
                peak_share = (top["count"] / max(total, 1)) * 100

                # ---------- Analysis (standard format) ----------
                st.markdown("#### Analysis – Installed Software Distribution")
                st.write(f"""
**What this graph is:** A bar chart showing **installed software volume** by `{col_software}`.  
**X-axis:** Software titles.  
**Y-axis:** Installation counts (number of records per title).

**What it shows in your data:**  
- Largest title: **{top[col_software]}** with **{_fmt_int(top['count'])} installs** (share **{_fmt_float(peak_share)}%** of **{_fmt_int(total)}** total).  
- Smallest title: **{low[col_software]}** with **{_fmt_int(low['count'])} installs**.  

**Overall:** A steep drop from the first few bars signals **standardization leverage**; a flatter shape indicates **sprawl** and higher support variance.

**How to read it operationally:**  
- **Focus:** Standardize images on top titles; negotiate volume pricing.  
- **Clean:** Remove fringe/duplicate titles to cut complexity.  
- **Align:** Map titles to role bundles to improve fit and patching cadence.  

**Why this matters:** Software sprawl inflates **license cost, support effort, and risk**. A curated stack preserves cost, performance, and satisfaction.
""")

                evidence_bits.append(f"Top title: {top[col_software]} ({_fmt_int(top['count'])}); total installs={_fmt_int(total)}; top share={_fmt_float(peak_share)}%.")

                # ---------- CIO table with expanded Explanation & Benefits ----------
                cio_3a = {
                    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Standardize dominant titles** | **Phase 1 – Identify:** - Build a clear list of core applications starting with **{top[col_software]}** and explain exactly which roles require each title and why they need it to perform their job effectively.<br><br>- Map current distributions and document overlaps so decision makers can see where consolidation is safe and where exceptions are justified.<br><br>**Phase 2 – Negotiate:** - Use the footprint of **{_fmt_int(top['count'])}** installs to request tiered pricing and support concessions that are explicitly tied to our usage profile and renewal timelines.<br><br>- Prepare competitive benchmarks and highlight switching costs to strengthen our position without committing prematurely.<br><br>**Phase 3 – Enforce:** - Publish a golden image and restrict ad-hoc installs so devices remain within the approved stack and policy violations are caught early.<br><br>- Monitor drift with monthly reports and assign owners to remediate any deviations within a fixed timeframe. | - Reduced unit price improves run-rate savings and creates budget headroom for higher-impact initiatives.<br><br>- Fewer software variants shrink testing scope which lowers engineering workload and shortens change windows.<br><br>- Consistent configurations cut incident volume from misaligned versions and reduce mean time to repair because playbooks fit more endpoints.<br><br>- A smaller catalog accelerates onboarding and decreases training time for both users and support teams. | **Savings = (Discount % × {_fmt_int(top['count'])} seats × unit price).** | Top bar shows **{top[col_software]}** has **{_fmt_int(top['count'])} installs** (share **{_fmt_float(peak_share)}%** of **{_fmt_int(total)}**). |
| **Decommission fringe titles** | **Phase 1 – Detect:** - Identify titles under 1% share and verify if their capabilities are already covered by standardized tools to avoid duplicate spend.<br><br>- Confirm business owners and usage patterns so removals do not disrupt critical workflows unexpectedly.<br><br>**Phase 2 – Replace:** - Offer a clear like-for-like pathway into the standard tool with data migration guidance and training to minimize resistance.<br><br>- Schedule change windows that avoid peak business periods and communicate expected outcomes in advance.<br><br>**Phase 3 – Reclaim:** - Uninstall superseded packages, revoke keys, and remove installers from the catalog to prevent re-growth.<br><br>- Track reclaimed seats and report realized savings so stakeholders see tangible results. | - Direct license reclamation lowers cash outlay without harming productivity when alternatives are in place.<br><br>- Fewer unique tools reduce cognitive load for agents and users which translates into faster ticket handling and fewer how-to queries.<br><br>- Consolidation reduces the attack surface and lowers patching complexity which decreases security exposure and compliance risk.<br><br>- Catalog hygiene prevents the same problem from returning which sustains savings over time. | **Savings = (Reclaimed installs × license unit price).** | Long tail of small bars indicates low-usage titles suitable for removal. |
| **Rightsize license pools** | **Phase 1 – Compare:** - Reconcile installation counts against active users and telemetry so we know exactly which seats are idle or underutilized.<br><br>- Validate exceptions with business owners to avoid reclaiming seats that are temporarily quiet due to seasonal work.<br><br>**Phase 2 – Reallocate:** - Move unused keys to teams with demonstrated demand and document the handover for audit purposes.<br><br>- Cap new purchases until the pool is fully utilized to avoid unnecessary spend.<br><br>**Phase 3 – Monitor:** - Publish monthly exception reports and set a target utilization rate so leaders can track progress.<br><br>- Trigger automatic reviews when usage drops below thresholds to keep pools right-sized. | - Avoided purchases convert immediately to savings while keeping productivity intact because surplus seats are redeployed where needed.<br><br>- Higher utilization raises return on existing contracts and delays true-ups which stabilizes the budget profile across quarters.<br><br>- Continuous monitoring reduces surprise overages and improves audit readiness which lowers operational risk.<br><br>- Transparent reporting builds trust with stakeholders and speeds up approvals for future optimizations. | **Savings = (Unused seats × unit price).** | Total installs **{_fmt_int(total)}** give baseline to match against usage. 
""",
                    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Golden images for top titles** | **Phase 1 – Build:** - Create a hardened base image that includes **{top[col_software]}** with vetted settings and extensions that reflect real user workflows.<br><br>- Document installation order and dependencies so rebuilds are deterministic and repeatable across sites.<br><br>**Phase 2 – Validate:** - Pilot with power users and collect stability metrics and task completion times to verify the image actually improves throughput.<br><br>- Fix discovered issues and update the image before scaling to avoid rework later.<br><br>**Phase 3 – Rollout:** - Deploy organization-wide in waves and lock versions to prevent configuration drift.<br><br>- Track adoption and incident deltas to confirm the rollout is delivering the expected performance gains. | - Faster provisioning shortens device lead time and gets new hires productive sooner which boosts overall throughput.<br><br>- Consistent builds reduce misconfigurations which lowers ticket volume and smooths patching windows.<br><br>- Known-good states improve support diagnostics and reduce time to resolution because troubleshooting paths are standardized.<br><br>- Rollbacks become simpler since baseline snapshots are predictable and well documented. | **Hours saved = (Setup time saved per device × {_fmt_int(top['count'])}).** | Dominant bar confirms high coverage impact from standardization. |
| **Patch baseline cadence** | **Phase 1 – Catalog:** - Define supported versions for top titles along with end-of-life dates so teams know what is compliant and what must be upgraded.<br><br>- Record application dependencies to minimize conflicts during change windows.<br><br>**Phase 2 – Window:** - Execute monthly patch sprints with clear rollback points and communication plans that set user expectations.<br><br>- Stage media in advance to reduce network spikes and failed installations.<br><br>**Phase 3 – Telemetry:** - Measure crash rate, performance changes, and ticket trends after each sprint to tune cadence.<br><br>- Use findings to retire unstable versions faster and promote stable ones sooner. | - Predictable cadence lowers unplanned downtime and reduces firefighting which stabilizes operations.<br><br>- Smaller test matrices improve engineering productivity and shorten validation cycles which speeds delivery of fixes.<br><br>- Data-driven tuning increases confidence in changes which raises success rates over time.<br><br>- Consistency across teams improves collaboration because everyone works from the same assumptions. | **Hours avoided = (ΔIncidents after patch × avg MTTR).** | Concentration around few titles simplifies patching. |
| **Role-based bundles** | **Phase 1 – Map:** - Associate titles with roles and specify the business scenarios each tool enables so approvals are quick and defensible.<br><br>- Identify sensitive roles that need enhanced controls to ensure compliance from day one.<br><br>**Phase 2 – Approvals:** - Pre-approve bundles in the catalog and integrate with HR triggers to auto-provision on join or change of role.<br><br>- Provide optional add-ons with clear criteria to keep exceptions manageable.<br><br>**Phase 3 – Audit:** - Review bundle drift quarterly and remove unauthorized tools to maintain clarity and reduce support noise.<br><br>- Publish adoption and satisfaction metrics to guide future bundle refinements. | - Faster onboarding reduces time to productivity for new and transitioning employees which improves business throughput.<br><br>- Standardized bundles decrease access requests and follow-up tickets which lightens service desk load.<br><br>- Clear entitlements reduce confusion for managers and employees which improves perceived service quality.<br><br>- Ongoing audits keep environments clean which sustains performance benefits. | **Time saved = (Requests avoided × handling time).** | Distribution highlights which titles belong in core bundles.
""",
                    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Self-service install for baseline titles** | **Phase 1 – Portal:** - Provide one-click installs for baseline apps and show entitlement checks so users understand eligibility without contacting IT.<br><br>- Surface estimated install time and restart requirements to set expectations clearly.<br><br>**Phase 2 – Guardrails:** - Validate license availability and device readiness before installation to avoid failed attempts and user frustration.<br><br>- Offer fallback guidance if prerequisites are missing so users are not blocked.<br><br>**Phase 3 – Feedback:** - Capture quick satisfaction ratings and record time to fulfill so the catalog continuously improves.<br><br>- Use feedback to refine descriptions and fix confusing steps. | - Faster fulfillment reduces waiting and helps users continue work with minimal disruption which raises satisfaction.<br><br>- Clear guardrails reduce failed installs which prevents avoidable tickets and negative experiences.<br><br>- Transparent progress and feedback loops build trust in IT services and encourage self-service adoption.<br><br>- Higher self-service usage frees up agents to handle complex requests which improves overall service quality. | **Value = (Tickets deflected × cost/ticket).** | High install share on baseline titles supports portal ROI. |
| **Sunset announcement for fringe titles** | **Phase 1 – Notify:** - Communicate timelines and supported alternatives early so users have time to adapt and plan transitions.<br><br>- Provide a simple explanation of why the change is happening to reduce resistance.<br><br>**Phase 2 – Support:** - Offer migration guides and short help sessions to resolve common questions in bulk.<br><br>- Track issues raised during migration and update guidance accordingly.<br><br>**Phase 3 – Closure:** - Remove deprecated packages and block new requests to stop reintroduction of retired tools.<br><br>- Confirm completion with owners so accountability is clear. | - Early and clear communication reduces confusion which lowers complaint volume during change.<br><br>- Structured support speeds up adoption of the replacement tool which minimizes productivity dips.<br><br>- Formal closure prevents backsliding which keeps the environment standardized and easier to support.<br><br>- Better user understanding increases acceptance and strengthens partnership with IT. | **Value = (Follow-ups avoided × cost/call).** | Long tail evidences low-value titles. |
| **Usage tips & training** | **Phase 1 – Quick tips:** - Publish short guides that focus on frequent tasks so users see immediate value from the tools they already have.<br><br>- Keep content lightweight and searchable so answers are easy to find in the flow of work.<br><br>**Phase 2 – Microlearning:** - Tailor learning modules by department to reflect real job tasks and reduce context switching.<br><br>- Offer bite-sized lessons that can be completed without disrupting daily work.<br><br>**Phase 3 – Measure:** - Track changes in ticket types and usage to confirm learning is helping and adjust content where gaps remain.<br><br>- Share outcomes with leaders to reinforce the importance of ongoing enablement. | - Better proficiency lowers how-to tickets which reduces service desk queues and improves user confidence.<br><br>- Department-specific tips help users complete tasks faster which improves perceived tool value.<br><br>- Continuous measurement keeps the program relevant which sustains satisfaction improvements over time.<br><br>- Short, targeted content respects user time which increases engagement and completion rates. | **Benefit = (How-to tickets avoided × cost).** | Focus training where installs are highest (**{_fmt_int(top['count'])}** units).
"""
                }
                render_cio_tables("CIO – Software Inventory Overview", cio_3a)

            else:
                st.info("No rows available.")
        else:
            st.warning("No software column found.")

    # --------------------------------------------------------------------
    # Version Distribution
    # --------------------------------------------------------------------
    with st.expander("📌 Version Distribution"):
        ev_bits = []
        if col_version:
            ver_df = (
                df[col_version].fillna("(unknown)").value_counts(dropna=False).reset_index()
            )
            ver_df.columns = ["version", "count"]
            ver_df = ver_df.sort_values("count", ascending=False)

            if not ver_df.empty:
                fig = px.bar(ver_df.head(15), x="version", y="count", text="count", title=f"Top Versions ({col_version})")
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

                diversity = _safe_nunique(df, col_version)
                topv = ver_df.iloc[0]
                lowv = ver_df.iloc[-1]
                total_v = int(ver_df["count"].sum())
                topv_share = (topv["count"] / max(total_v, 1)) * 100
                avg_v = float(ver_df["count"].mean())

                # ---------- Analysis ----------
                st.markdown("#### Analysis – Version Mix")
                st.write(f"""
**What this graph is:** A bar chart showing **installed version counts** for `{col_version}`.  
**X-axis:** Version identifiers.  
**Y-axis:** Install counts per version.

**What it shows in your data:**  
- Most common version: **{topv['version']}** with **{_fmt_int(topv['count'])} installs** (**{_fmt_float(topv_share)}%** of **{_fmt_int(total_v)}**).  
- Least common (in shown set): **{lowv['version']}** with **{_fmt_int(lowv['count'])} installs**.  
- **Unique versions:** {_fmt_int(diversity)}; **Avg installs/version:** {_fmt_float(avg_v)}.

**Overall:** High diversity implies **patch/testing overhead**; concentration around a baseline implies **easier governance**.

**How to read it operationally:**  
- **Baseline:** Pick a target version and migrate stragglers.  
- **Windows:** Schedule upgrades by department to reduce blast radius.  
- **Telemetry:** Track regression rate after each wave.

**Why this matters:** Version drift drives **incidents, incompatibilities, and audit risk**. A tight baseline protects stability and speed.
""")

                ev_bits.append(f"Top version {topv['version']} ({_fmt_int(topv['count'])}); total={_fmt_int(total_v)}; unique={_fmt_int(diversity)}; avg/vers={_fmt_float(avg_v)}.")

                cio_3b = {
                    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Deprecate legacy versions** | **Phase 1 – Identify:** - List all versions below the target baseline and attach vendor support status so risks are visible to stakeholders.<br><br>- Quantify how many endpoints sit on each legacy version to prioritize batches logically.<br><br>**Phase 2 – Migrate:** - Upgrade in grouped waves with pre-checks for storage, compatibility, and backups so failures are rare and recoverable.<br><br>- Validate post-upgrade health to ensure functionality before closing the batch.<br><br>**Phase 3 – Retire:** - Remove legacy installers and permissions that enable rollbacks so the environment does not fragment again.<br><br>- Record final counts and savings so benefits are transparent. | - Smaller version spread reduces test effort which makes changes cheaper and faster to ship.<br><br>- Fewer unsupported versions decrease compliance exposure which lowers audit remediation costs.<br><br>- System stability improves as edge-case defects are retired which reduces incident frequency and effort to resolve.<br><br>- Predictable migration waves let teams plan staffing and avoid overtime. | **Savings = (Legacy installs × Δsupport time × rate).** | Many versions ({_fmt_int(diversity)}) with leader **{topv['version']} ({_fmt_int(topv['count'])})**. |
| **Co-term upgrades** | **Phase 1 – Align:** - Group upgrades by department or site so maintenance windows are shared and communication is simpler for local leaders.<br><br>- Document cross-team dependencies so sequencing avoids clashes with other changes.<br><br>**Phase 2 – Stage:** - Pre-cache media and approvals to remove waiting time and limit bandwidth spikes during execution.<br><br>- Prepare quick-win fixes for common issues so teams can recover fast if something goes wrong.<br><br>**Phase 3 – Validate:** - Smoke test critical workflows and verify support tools before closing the window.<br><br>- Capture lessons learned to improve the next wave immediately. | - Coordinated windows reduce downtime across teams which protects business operations.<br><br>- Staged assets increase success rates and shorten change durations which improves throughput.<br><br>- Early validation lowers the chance of prolonged outages which reduces user disruption.<br><br>- Repeatable patterns accumulate efficiencies across subsequent waves. | **Benefit = (ΔMTTR × Upgraded installs).** | Concentration enables wave-based planning. |
| **Baseline pinning** | **Phase 1 – Define:** - Publish the exact target version with compatibility notes and known caveats so expectations are aligned.<br><br>- List approved exceptions and their expiry dates to keep variance temporary and controlled.<br><br>**Phase 2 – Enforce:** - Apply device policy that blocks non-baseline installs and alerts owners when drift occurs so remediation is timely.<br><br>- Integrate checks into software deployment tools so violations are prevented at source.<br><br>**Phase 3 – Monitor:** - Track compliance weekly and escalate persistent gaps to owners for action.<br><br>- Review baseline quarterly to incorporate stable improvements without creating churn. | - Pinning reduces configuration drift which prevents many avoidable incidents and speeds troubleshooting.<br><br>- Automated control lowers manual effort which frees engineers to focus on higher-value tasks.<br><br>- Regular monitoring sustains compliance which stabilizes performance over the long term.<br><br>- Clear exceptions policy maintains flexibility without losing control. | **Avoided rework = (Drift events × time × rate).** | Top version share **{_fmt_float(topv_share)}%** suggests a viable baseline.
""",
                    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Phased rollout** | **Phase 1 – Pilot:** - Start with a small cohort that mirrors real usage patterns and capture objective metrics like crash rate and task timing.<br><br>- Use pilot feedback to fix blockers so the scaled rollout is smoother.<br><br>**Phase 2 – Scale:** - Roll out in waves that align to departments to keep support focused and knowledge transferable.<br><br>- Communicate timelines and what success looks like so teams are ready.<br><br>**Phase 3 – Lock:** - Close gaps, freeze on the stable baseline, and document operational learnings for future changes.<br><br>- Measure outcomes against pre-defined targets to validate success. | - Fewer regressions increase delivery confidence and reduce rework which improves velocity.<br><br>- Departmental waves concentrate expertise which accelerates issue resolution during the rollout.<br><br>- Defined end state prevents drift and preserves the gains achieved by the program.<br><br>- Measured outcomes create a feedback loop that improves subsequent changes. | **Throughput gain = (Resolved/day ↑ × days).** | Version bars reveal target cohorts by size. |
| **Automated compliance checks** | **Phase 1 – Detect:** - Continuously identify devices off baseline and tag them with owners so accountability is clear.<br><br>- Prioritize the largest or riskiest gaps first to maximize impact quickly.<br><br>**Phase 2 – Remediate:** - Schedule upgrades in maintenance windows or enforce auto-updates for low-risk changes so compliance improves with minimal disruption.<br><br>- Confirm success and retry failures with clear error context.<br><br>**Phase 3 – Report:** - Publish weekly compliance percentages and trend lines to keep leaders informed.<br><br>- Tie results to objectives so teams stay motivated to close gaps. | - Faster detection shortens the window of risk and reduces the number of support paths to maintain.<br><br>- Automated remediation lowers manual effort which reduces cost per fix and speeds progress.<br><br>- Transparent reporting aligns teams and sustains momentum which protects performance gains.<br><br>- Prioritized work ensures the biggest risks are addressed first which improves reliability sooner. | **Time saved = (Manual checks avoided × rate).** | Diversity vs leader highlights non-compliant pockets. |
| **Rollback readiness** | **Phase 1 – Snapshot:** - Back up critical state before upgrades so reversals are safe if issues appear in production.<br><br>- Verify restoration steps so teams practice the path before it is needed.<br><br>**Phase 2 – Script:** - Provide one-click rollback scripts that are easy to run under pressure and include checks to confirm success.<br><br>- Store scripts where responders can access them quickly during incidents.<br><br>**Phase 3 – Review:** - After any rollback, capture root causes and integrate fixes to reduce the chance of repeat events.<br><br>- Update documentation so lessons learned are durable. | - Reliable recovery reduces downtime which preserves user productivity during issues.<br><br>- Prepared responders resolve incidents faster which lowers MTTR and stress on the team.<br><br>- Systematic reviews improve future rollouts which compounds performance benefits.<br><br>- Confidence in recovery enables more frequent incremental upgrades which keeps environments healthier. | **Benefit = (Δdowntime × users).** | Concentration suggests high impact of any regression—rollback is essential.
""",
                    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Pre-communication** | **Phase 1 – Notify:** - Tell users what is changing, who is affected, and when it will happen so they can plan around it.<br><br>- Provide a concise summary of the value so the change feels meaningful rather than arbitrary.<br><br>**Phase 2 – Guides:** - Share short what’s-new notes and tips that cover the most common tasks users care about.<br><br>- Keep guidance easy to scan so answers are fast to find.<br><br>**Phase 3 – Support:** - Offer hypercare channels during big waves so help is accessible when needed most.<br><br>- Close the loop on common questions by improving the guidance promptly. | - Clear expectations reduce anxiety and complaints which improves perceived service quality.<br><br>- Practical tips shorten adaptation time which minimizes productivity dips after changes.<br><br>- Focused support during peaks keeps queues manageable and users satisfied.<br><br>- Continuous updates to guidance maintain trust that feedback is acted upon. | **Value = (Complaints avoided × cost/case).** | Clear waves from version counts guide comms cadence. |
| **Feature highlights** | **Phase 1 – Summarize:** - Explain the tangible benefits of the baseline so users know why upgrading helps them.<br><br>- Highlight improvements that remove common pain points to create quick wins.<br><br>**Phase 2 – Train:** - Provide micro-videos or cheat sheets that teach tasks users perform every day so adoption climbs naturally.<br><br>- Offer office hours for teams with specialized workflows to remove blockers.<br><br>**Phase 3 – Measure:** - Track usage of new features and link improvements to specific outcomes so value is visible.<br><br>- Share results to reinforce participation. | - Users understand the reason for change which reduces resistance and increases engagement.<br><br>- Targeted training accelerates skill building which reduces how-to tickets and frustration.<br><br>- Measuring outcomes validates the program and helps prioritize future enhancements.<br><br>- Publicized wins build momentum across departments. | **Value = (How-to tickets avoided × cost).** | Leader **{topv['version']}** provides consistent experience post-upgrade. |
| **Targeted support hours** | **Phase 1 – Staff:** - Add help desk capacity in the weeks that align to the largest upgrade cohorts so response times stay healthy.<br><br>- Prepare responders with known-issue guides so triage is quick and accurate.<br><br>**Phase 2 – Triage:** - Use fast lanes for upgrade-related issues so users get to the right expert immediately.<br><br>- Track categories to spot patterns that deserve proactive fixes.<br><br>**Phase 3 – Exit:** - Ramp down temporary staffing once stability returns and capture what worked for next time.<br><br>- Share a summary so stakeholders see the benefit of the investment. | - Extra capacity keeps queues moving which improves satisfaction during busy periods.<br><br>- Better routing reduces repeat contacts which shortens resolution time and effort.<br><br>- Structured wind-down optimizes cost while maintaining service quality.<br><br>- Documented learnings make the next peak smoother and cheaper. | **Benefit = (Wait time ↓ × sessions).** | Peak version cohorts indicate when to staff.
"""
                }
                render_cio_tables("CIO – Version Distribution", cio_3b)
        else:
            st.warning("No version column found.")

    # --------------------------------------------------------------------
    # License Type Distribution
    # --------------------------------------------------------------------
    with st.expander("📌 License Type Distribution"):
        ev_bits = []
        if col_lic_type:
            lic = df[col_lic_type].fillna("(unknown)").value_counts(dropna=False).reset_index()
            lic.columns = ["license_type", "count"]
            lic = lic.sort_values("count", ascending=False)
            if not lic.empty:
                fig = px.pie(lic, names="license_type", values="count", title=f"License Type Distribution ({col_lic_type})")
                st.plotly_chart(fig, use_container_width=True)

                largest = lic.iloc[0]
                smallest = lic.iloc[-1]
                total_lic = int(lic["count"].sum())
                largest_share = (largest["count"]/max(total_lic,1))*100

                # ---------- Analysis ----------
                st.markdown("#### Analysis – License Composition")
                st.write(f"""
**What this graph is:** A pie chart showing **license composition** by `{col_lic_type}`.  
**X-axis:** *Not applicable (pie).*  
**Y-axis:** *Not applicable (pie).*  

**What it shows in your data:**  
- Largest slice: **{largest['license_type']}** with **{_fmt_int(largest['count'])}** licenses (**{_fmt_float(largest_share)}%** of **{_fmt_int(total_lic)}** total).  
- Smallest slice (in data): **{smallest['license_type']}** (**{_fmt_int(smallest['count'])}**).

**Overall:** Big slices mark **cost/negotiation leverage**; small slices may indicate **underused or specialized** entitlements.

**How to read it operationally:**  
- **Rightsize:** Compare entitlements vs active users to reclaim.  
- **Co-term:** Align renewal windows for buying power.  
- **Govern:** Block ad-hoc requests that create tiny, expensive slices.

**Why this matters:** License mix drives **OPEX and compliance risk**. Clean composition = lower waste and smoother audits.
""")

                ev_bits.append(f"Largest license: {largest['license_type']} ({_fmt_int(largest['count'])}); total={_fmt_int(total_lic)}; share={_fmt_float(largest_share)}%.")
                cio_3c = {
                    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Rightsize inactive entitlements** | **Phase 1 – Detect:** - Cross-reference license allocations with active directory and usage telemetry to find seats with little or no activity.<br><br>- Confirm with managers before reclaiming to avoid interrupting legitimate seasonal work patterns.<br><br>**Phase 2 – Reclaim:** - Downgrade or remove inactive entitlements and document approvals so audits are straightforward.<br><br>- Reallocate recovered seats to teams with proven demand before purchasing new ones.<br><br>**Phase 3 – Monitor:** - Run a monthly reconciliation that highlights newly dormant seats so savings continue accruing.<br><br>- Track utilization KPIs by license type to guide future negotiations. | - Reclaiming idle seats prevents unnecessary purchases which reduces operating costs immediately.<br><br>- Better alignment between entitlements and usage lowers waste which improves ROI on existing contracts.<br><br>- Regular monitoring prevents drift back to over-allocation which protects savings across the year.<br><br>- Clear records simplify audit responses which reduces disruption to day-to-day work. | **Savings = (Unused seats × unit price) per license type.** Largest slice **{largest['license_type']}** = **{_fmt_int(largest['count'])}**. |
| **Co-term renewals** | **Phase 1 – Align:** - Shift scattered renewal dates toward common windows so volumes are aggregated for stronger vendor negotiations.<br><br>- Map dependencies to avoid clashes with major business events so risk stays low.<br><br>**Phase 2 – Negotiate:** - Use the combined seat count of **{_fmt_int(total_lic)}** to secure tier discounts and price caps that protect future budgets.<br><br>- Request support concessions tied to the larger commitment to improve service quality at the same time.<br><br>**Phase 3 – Lock:** - Prefer multi-year terms where suitable and record commercial protections so forecasting is stable.<br><br>- Embed reminders and owners to ensure actions happen on time. | - Consolidated renewals increase buying power which reduces unit prices and contains inflation over the term.<br><br>- Predictable cycles lower administrative workload which frees staff for higher-value work.<br><br>- Price caps and terms stability improve budget accuracy which reduces surprise spend spikes.<br><br>- Stronger vendor relationships can unlock better support which reduces operational friction. | **Savings = (Discount % × {_fmt_int(total_lic)} seats × unit price).** | Pie concentration indicates leverage. |
| **Eliminate micro-slices** | **Phase 1 – Identify:** - Find license types with very small populations and check if a baseline tier can meet the same need at lower cost.<br><br>- Engage owners to understand any compliance or feature constraints that must be preserved.<br><br>**Phase 2 – Consolidate:** - Migrate users to baseline tiers with clear change notes and training so disruption is minimal.<br><br>- Sunset niche SKUs from the catalog to prevent re-creation of tiny expensive pools.<br><br>**Phase 3 – Prevent:** - Add guardrails to approval flows that route requests to standard tiers by default.<br><br>- Review exceptions quarterly to keep the portfolio simple. | - Consolidation reduces per-user cost while keeping necessary functionality which protects productivity.<br><br>- A simpler tier structure reduces admin effort which speeds provisioning and renewals.<br><br>- Prevention controls stop fragmentation from returning which sustains savings over time.<br><br>- Clearer choices make it easier for requesters to pick the right option which reduces rework. | **Savings = (Micro-slice seats × (premium – baseline price)).** | Small slices in pie point to consolidation targets.
""",
                    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Automated entitlement checks** | **Phase 1 – Sync:** - Continuously sync HR and directory status with licensing data so departures and role changes are reflected quickly.<br><br>- Flag anomalies where users hold multiple overlapping licenses so teams can correct them fast.<br><br>**Phase 2 – Alert:** - Notify owners when thresholds are exceeded so action is taken before renewals or audits.<br><br>- Provide remediation steps within the alert so corrections are simple to execute.<br><br>**Phase 3 – Auto-fix:** - After a grace period, reclaim or downgrade automatically to keep pools healthy.<br><br>- Log every change to maintain a clean audit trail. | - Faster detection and correction of errors reduces waste and avoids last-minute scrambles which improves operational stability.<br><br>- Automation cuts manual spreadsheet work which reduces processing time and frees analysts for strategic tasks.<br><br>- Clear ownership and logging strengthen governance which improves trust in reported numbers.<br><br>- Healthier pools ensure licenses are available where they create the most value which supports productivity. | **Time saved = (Manual audit hours × rate).** | Clear type counts enable rules. |
| **License pool governance** | **Phase 1 – Approvals:** - Assign approvers per license type and define what criteria must be met to authorize requests so decisions are consistent.<br><br>- Publish SLAs to set expectations for response times and documentation needs.<br><br>**Phase 2 – Justify:** - Require a short business justification and expected usage so the right tier is selected from the start.<br><br>- Encourage sharing of existing seats before buying new ones when needs are temporary.<br><br>**Phase 3 – Review:** - Run quarterly pool reviews to validate utilization and adjust allocations where demand changed.<br><br>- Close unused requests so records remain accurate. | - Standardized approvals eliminate guesswork which speeds legitimate requests and filters unnecessary ones.<br><br>- Better upfront choices reduce later rework which improves throughput for support teams.<br><br>- Regular reviews keep allocations aligned with reality which sustains performance and cost control.<br><br>- Clear SLAs improve stakeholder satisfaction because timelines are predictable. | **Benefit = (Overage avoided × unit price).** | Dominant types suggest pooling. |
| **Usage telemetry** | **Phase 1 – Instrument:** - Capture frequency and duration of use per license type so entitlement matches value delivered.<br><br>- Protect privacy by aggregating appropriately so adoption remains high.<br><br>**Phase 2 – Score:** - Classify users into active and dormant categories using transparent thresholds that leaders can understand.<br><br>- Revisit thresholds if behavior patterns change over time.<br><br>**Phase 3 – Act:** - Reclaim or resize based on scores and notify users of changes so surprises are avoided.<br><br>- Track impact on utilization and savings to refine the model. | - Telemetry-driven decisions reduce contention over allocations which speeds agreements with stakeholders.<br><br>- Right-sized entitlements lift utilization which increases the value extracted from contracts.<br><br>- Regular action on the data prevents waste from creeping back which safeguards gains.<br><br>- Clear communication increases trust which improves satisfaction with IT processes. | **Benefit = (Dormant seats reduced × unit price).** | Composition + activity = precise rightsize.
""",
                    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Self-service renewals** | **Phase 1 – Portal:** - Offer a guided renewal and upgrade path that checks entitlements and budgets so users know what is possible instantly.<br><br>- Display impact on cost and features in plain language so choices are informed.<br><br>**Phase 2 – Policy:** - Auto-approve baseline renewals within quotas to keep work flowing while routing exceptions to reviewers.<br><br>- Provide clear timelines on exceptions so expectations are set.<br><br>**Phase 3 – SLA:** - Publish response targets and track them publicly so accountability is visible.<br><br>- Improve the flow when targets are missed to raise satisfaction. | - Users resolve routine renewals without waiting which reduces frustration and ticket volume.<br><br>- Transparent rules and timelines increase trust which improves perceived service quality.<br><br>- Exceptions get the attention they deserve without blocking standard cases which balances speed and control.<br><br>- Public SLAs create a virtuous cycle of improvement which sustains satisfaction. | **Value = (Tickets avoided × cost/ticket).** | Dominant types are ideal for self-service flows. |
| **Transparent entitlements** | **Phase 1 – My licenses:** - Show users their current licenses, expiry dates, and pending requests so they can plan proactively.<br><br>- Provide links to request changes directly to reduce back-and-forth.<br><br>**Phase 2 – Alerts:** - Send reminders well before expiry so renewals happen calmly rather than under pressure.<br><br>- Include simple call to action that takes users to the right page instantly.<br><br>**Phase 3 – Coaching:** - Offer guidance on which tier fits common needs so users pick correctly the first time.<br><br>- Update recommendations using recent usage where available. | - Fewer surprises reduce downtime and avoid frantic last-minute requests which keeps work moving smoothly.<br><br>- Better self-selection reduces correction tickets which lightens support load.<br><br>- Early visibility improves planning which increases confidence in IT services.<br><br>- Contextual coaching helps users feel supported which improves satisfaction. | **Value = (Complaints avoided × cost/case).** | Pie shows type mix to communicate. |
| **Department-level dashboards** | **Phase 1 – Share:** - Provide leaders with seats versus usage by department so they can manage their portfolio actively.<br><br>- Include trends and comparisons to highlight where attention is needed most.<br><br>**Phase 2 – Targets:** - Agree on utilization targets and show progress so improvement is visible and motivating.<br><br>- Highlight risks ahead of renewals so action is timely.<br><br>**Phase 3 – Review:** - Hold monthly check-ins to unblock issues and capture wins so practices spread.<br><br>- Adjust dashboards based on feedback so insights remain useful. | - Clear ownership drives faster decisions which improves responsiveness to changing needs.<br><br>- Visibility encourages stewardship which reduces waste without central micromanagement.<br><br>- Regular cadence builds a habit of proactive management which sustains performance and satisfaction.<br><br>- Better alignment between departments and IT strengthens partnership and trust. | **Benefit = (Overage avoided × unit price).** | Type counts + trends support dashboards.
"""
                }
                render_cio_tables("CIO – License Type", cio_3c)
        else:
            st.warning("No license type column found.")

    # --------------------------------------------------------------------
    # Installation & Expiry Timeline
    # --------------------------------------------------------------------
    with st.expander("📌 Installation & License Expiry Timeline"):
        ev_bits = []

        # Installations
        if col_inst_date:
            t_inst = df[df[col_inst_date].notna()].copy()
            if not t_inst.empty:
                t_inst["month"] = _period_month(t_inst[col_inst_date])
                by_m_inst = t_inst.groupby("month").size().reset_index(name="installed")
                fig = px.area(by_m_inst, x="month", y="installed", title="Installations by Month",
                              labels={"month":"Month","installed":"Installed"})
                st.plotly_chart(fig, use_container_width=True)

                inst_peak = by_m_inst.loc[by_m_inst["installed"].idxmax()]
                inst_low = by_m_inst.loc[by_m_inst["installed"].idxmin()]
                inst_total = int(by_m_inst["installed"].sum())
                inst_avg = float(by_m_inst["installed"].mean())

                # ---------- Analysis for Installations ----------
                st.markdown("#### Analysis – Monthly Installations")
                st.write(f"""
**What this graph is:** An area chart showing **monthly installations** based on `{col_inst_date}`.  
**X-axis:** Calendar month.  
**Y-axis:** Number of installations in that month.

**What it shows in your data:**  
- Peak install month: **{inst_peak['month']}** with **{_fmt_int(inst_peak['installed'])} installs**.  
- Lowest month: **{inst_low['month']}** with **{_fmt_int(inst_low['installed'])} installs**.  
- **Total installs:** {_fmt_int(inst_total)}; **Average:** {_fmt_float(inst_avg)} per month.

**Overall:** Rising envelope ⇒ **rollout acceleration** and future support load; flat/falling ⇒ **stabilization**.

**How to read it operationally:**  
- **Capacity:** Staff imaging/support ahead of peaks.  
- **Procurement:** Align deliveries before big waves.  
- **Quality:** Watch early-failure rate post big months.

**Why this matters:** Install surges determine **near-term workload and cost**; planning reduces overtime and incident spikes.
""")
                ev_bits.append(f"Install peak {inst_peak['month']} ({_fmt_int(inst_peak['installed'])}); total installs={_fmt_int(inst_total)}; avg/month={_fmt_float(inst_avg)}.")
        # Expirations
        if col_exp_date:
            t_exp = df[df[col_exp_date].notna()].copy()
            if not t_exp.empty:
                t_exp["month"] = _period_month(t_exp[col_exp_date])
                by_m_exp = t_exp.groupby("month").size().reset_index(name="expiring")
                fig2 = px.bar(by_m_exp, x="month", y="expiring", text="expiring", title="Expirations by Month",
                              labels={"month":"Month","expiring":"Expiring"})
                fig2.update_traces(textposition="outside")
                st.plotly_chart(fig2, use_container_width=True)

                exp_peak = by_m_exp.loc[by_m_exp["expiring"].idxmax()]
                exp_low = by_m_exp.loc[by_m_exp["expiring"].idxmin()]
                exp_total = int(by_m_exp["expiring"].sum())
                exp_avg = float(by_m_exp["expiring"].mean())

                # ---------- Analysis for Expirations ----------
                st.markdown("#### Analysis – Monthly Expirations")
                st.write(f"""
**What this graph is:** A bar chart showing **monthly license expirations** based on `{col_exp_date}`.  
**X-axis:** Calendar month.  
**Y-axis:** Number of licenses expiring in that month.

**What it shows in your data:**  
- Peak expiry month: **{exp_peak['month']}** with **{_fmt_int(exp_peak['expiring'])} expirations**.  
- Lowest month: **{exp_low['month']}** with **{_fmt_int(exp_low['expiring'])}** expirations.  
- **Total expirations:** {_fmt_int(exp_total)}; **Average:** {_fmt_float(exp_avg)} per month.

**Overall:** High bars signal **renewal risk** and vendor negotiation windows; low bars are **catch-up opportunities**.

**How to read it operationally:**  
- **Renew:** Co-term + bundle in peak months.  
- **Protect:** Prioritize critical apps before expiry.  
- **Smooth:** Use quiet months to clear backlog.

**Why this matters:** Expiry clusters drive **OPEX spikes and disruption risk**. Planning renewals preserves continuity and budget.
""")
                ev_bits.append(f"Expiry peak {exp_peak['month']} ({_fmt_int(exp_peak['expiring'])}); total expiries={_fmt_int(exp_total)}; avg/month={_fmt_float(exp_avg)}.")

        ev_3d = " | ".join(ev_bits) if ev_bits else "Data not available."

        # CIO tables referencing real peak/avg numbers (when available)
        inst_ev = f"Peak installs **{inst_peak['month']} = {_fmt_int(inst_peak['installed'])}**, avg **{_fmt_float(inst_avg)}**/month." if "inst_peak" in locals() else "Install timeline not available."
        exp_ev = f"Peak expiries **{exp_peak['month']} = {_fmt_int(exp_peak['expiring'])}**, avg **{_fmt_float(exp_avg)}**/month." if "exp_peak" in locals() else "Expiry timeline not available."

        cio_3d = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Co-term renewals** | **Phase 1 – Align:** - Move disparate expiry dates into shared windows so purchasing power increases and planning becomes easier for all teams.<br><br>- Document which applications are critical so their renewals anchor the calendar without risk to operations.<br><br>**Phase 2 – Negotiate:** - Use aggregated demand to ask for multi-year discounts and service improvements that reflect our combined scale.<br><br>- Seek protections like price caps to shield the budget from unexpected increases over the term.<br><br>**Phase 3 – Track:** - Maintain a renewal calendar with named owners and status so tasks are visible and nothing is missed.<br><br>- Review outcomes after each window to improve the next cycle. | - Aggregating renewals reduces per-unit cost which frees budget for higher priority work.<br><br>- Predictable windows reduce administrative burden which shortens cycle time and lowers stress on teams.<br><br>- Price protections stabilize future spend which improves financial planning accuracy.<br><br>- Clear ownership reduces last-minute escalations which protects service continuity. | **Savings = (Discount % × {_fmt_int(exp_total) if 'exp_total' in locals() else 'expiring seats'} × unit price).** | {exp_ev} |
| **Stage resources for install peaks** | **Phase 1 – Plan:** - Schedule imaging and support capacity ahead of **{inst_peak['month'] if 'inst_peak' in locals() else 'peak month'}** so onboarding throughput matches demand.<br><br>- Reserve loaner equipment and logistics so failed builds do not delay users.<br><br>**Phase 2 – Cache:** - Pre-stage media, drivers, and configs on local networks to reduce download time and avoid bandwidth contention.<br><br>- Test unattended scripts so installs are reliable at scale.<br><br>**Phase 3 – Hypercare:** - Provide elevated support for the first week after large waves so issues are resolved quickly.<br><br>- Track common faults and update images to prevent repeats. | - Better staffing reduces overtime and rework which lowers operational cost during busy periods.<br><br>- Pre-staged assets shorten build times which gets users productive faster.<br><br>- Hypercare reduces disruption for new deployments which improves user perception of IT.<br><br>- Rapid feedback into images improves quality for the next wave which compounds benefits. | **Benefit = (Overtime hours avoided × rate) using peak {_fmt_int(inst_peak['installed']) if 'inst_peak' in locals() else 'install count'}.** | {inst_ev} |
| **License pooling across low months** | **Phase 1 – Reclaim:** - During quiet months, identify idle licenses and recover them with approval so pools are healthy before demand spikes return.<br><br>- Confirm business seasonality to avoid unnecessary churn.<br><br>**Phase 2 – Reassign:** - Allocate reclaimed seats to upcoming projects and document the transfers so audits remain simple.<br><br>- Hold back a small buffer for urgent needs so users are not blocked.<br><br>**Phase 3 – Verify:** - After reassignment, confirm users can access what they need and that compliance systems reflect reality.<br><br>- Review pool utilization and tune thresholds for the next cycle. | - Reusing existing seats avoids purchases which reduces spend without slowing projects.<br><br>- Documented transfers maintain audit readiness which lowers the cost of compliance work.<br><br>- A small buffer reduces urgent buying under pressure which prevents premium pricing.<br><br>- Regular verification prevents pool decay which sustains savings. | **Savings = (Reclaimed seats × unit price) derived from off-peak counts.** | {exp_ev}
""",
            "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Renewal calendar sprints** | **Phase 1 – Sprint:** - Organize renewal work into focused sprints around **{exp_peak['month'] if 'exp_peak' in locals() else 'peak month'}** with a clear backlog and owners.<br><br>- Visualize dependencies so blockers are surfaced early and resolved promptly.<br><br>**Phase 2 – Kanban:** - Track tasks with visible boards so status is transparent and context switching is minimized.<br><br>- Limit work in progress so the team finishes items faster with fewer handoffs.<br><br>**Phase 3 – Retro:** - After each sprint, review what slowed progress and implement fixes before the next cycle starts.<br><br>- Share metrics so improvements are measurable. | - Focused execution improves throughput and on-time completion which reduces risk of service interruption.<br><br>- Visual management lowers coordination overhead which speeds decision making.<br><br>- Continuous improvement compounds gains which stabilizes performance across quarters.<br><br>- Transparency increases stakeholder confidence which reduces escalations. | **Throughput gain = (On-time renewals ↑ × avg handling time).** | {exp_ev} |
| **Hypercare after install peaks** | **Phase 1 – Staff:** - Add service desk capacity for **{inst_peak['month'] if 'inst_peak' in locals() else 'peak'}** plus one week so response times stay healthy during the surge.<br><br>- Brief teams on known issues so triage is accurate from the first contact.<br><br>**Phase 2 – Playbooks:** - Provide short resolution guides and escalation paths to speed handling of repeated problems.<br><br>- Update playbooks daily based on live data so fixes improve quickly.<br><br>**Phase 3 – Metrics:** - Track incident rate and MTTR to confirm when to stand down and what to adjust in the image.<br><br>- Feed lessons into future rollout plans. | - Extra capacity keeps queues short which maintains productivity for newly onboarded users.<br><br>- Playbooks standardize resolutions which lowers handling time and variance across agents.<br><br>- Measured outcomes ensure support scales back at the right moment which optimizes cost.<br><br>- Closed-loop learning improves the next rollout which enhances operational stability. | **Benefit = (ΔMTTR × {_fmt_int(inst_peak['installed']) if 'inst_peak' in locals() else 'install volume'}).** | {inst_ev} |
| **Automated reminders** | **Phase 1 – Alerts:** - Send reminders at 60, 30, and 7 days before expiry so owners act with time to spare and avoid emergency renewals.<br><br>- Include a simple checklist so the next action is obvious.<br><br>**Phase 2 – Tasks:** - Create tasks with due dates and watchers so progress is tracked and accountability is shared.<br><br>- Escalate overdue items to reduce risk exposure.<br><br>**Phase 3 – SLA:** - Aim to complete renewals before T-7 unless there is a clear exception and record the reason for governance.<br><br>- Review adherence monthly to reinforce habits. | - Early prompts prevent service lapses which protects user access and business operations.<br><br>- Task tracking reduces dropped balls which improves reliability of the renewal process.<br><br>- Clear SLAs reduce last-minute rush which keeps costs and stress lower.<br><br>- Regular reviews reinforce discipline which stabilizes performance across cycles. | **Benefit = (Missed renewals avoided × downtime cost).** | {exp_ev}
""",
            "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Notify owners early** | **Phase 1 – Calendar:** - Send personalized notifications that list impacted systems and the steps required so owners can plan calmly.<br><br>- Provide a single place to track all actions so updates are easy to follow.<br><br>**Phase 2 – Options:** - Clearly present renew, upgrade, or drop choices with implications so decisions are quick and informed.<br><br>- Offer guidance based on prior usage where available to reduce uncertainty.<br><br>**Phase 3 – Confirm:** - Request acknowledgement and capture approvals so responsibilities are unambiguous.<br><br>- Provide status visibility to stakeholders to reduce follow-ups. | - Predictable communication reduces surprise access issues which keeps teams productive and satisfied.<br><br>- Clear options empower owners which speeds decisions and reduces second guessing.<br><br>- Formal confirmations prevent misunderstandings which lowers friction between teams.<br><br>- Shared visibility reduces status chasing which improves the overall experience. | **Value = (Complaints avoided × cost/case).** | {exp_ev} |
| **Self-service activation windows** | **Phase 1 – Portal:** - Allow installs and activations during low-risk windows so users can help themselves without waiting for manual processing.<br><br>- Show eligibility and prerequisites so attempts succeed on the first try.<br><br>**Phase 2 – Guardrails:** - Check license and device readiness to prevent errors and provide remediation tips when checks fail.<br><br>- Record outcomes so recurring issues can be fixed at the source.<br><br>**Phase 3 – Support:** - Offer contextual knowledge base and chat options so help is a click away when needed.<br><br>- Capture feedback to refine the flow. | - Self-service reduces wait time which boosts satisfaction and keeps work moving.<br><br>- Guardrails reduce failed attempts which cuts frustration and support tickets.<br><br>- Embedded help lowers effort to get unstuck which improves user confidence in the system.<br><br>- Feedback-driven iteration keeps the portal effective over time which sustains value. | **Value = (Tickets deflected × cost/ticket).** | {inst_ev} |
| **Publish renewal progress** | **Phase 1 – Dashboard:** - Show progress by application and risk flags so leaders know where attention is needed most.<br><br>- Include owners and due dates so follow-up is targeted and efficient.<br><br>**Phase 2 – Risk:** - Highlight blockers like legal review or vendor delays and suggest actions so issues move forward.<br><br>- Provide history so bottlenecks can be addressed structurally.<br><br>**Phase 3 – Updates:** - Provide regular ETAs and completion notes so stakeholders feel informed without chasing status.<br><br>- Archive outcomes to improve future planning. | - Transparent status reduces inbound queries which saves time for both IT and business teams.<br><br>- Early risk visibility prevents last-minute crises which improves user trust in the process.<br><br>- Regular updates create a calm cadence which enhances the overall experience.<br><br>- Historical data supports better forecasting next cycle which continues to reduce friction. | **Benefit = (Follow-ups avoided × cost/call).** | {exp_ev}
"""
        }
        render_cio_tables("CIO – Install & Expiry Timeline", cio_3d)

    # --------------------------------------------------------------------
    # Usage & Department Mix
    # --------------------------------------------------------------------
    with st.expander("📌 Usage & Department Mix"):
        ev_bits = []

        # Usage distribution
        if col_usage and col_usage in df.columns:
            usage = df[[col_usage]].dropna()
            if not usage.empty:
                fig = px.histogram(usage, x=col_usage, nbins=20, title=f"Usage Distribution ({col_usage})")
                st.plotly_chart(fig, use_container_width=True)
                mean = usage[col_usage].mean()
                p95 = float(np.percentile(usage[col_usage], 95)) if len(usage[col_usage]) > 0 else 0.0
                count_u = int(usage.shape[0])

                # ---------- Analysis for Usage ----------
                st.markdown("#### Analysis – Usage Distribution")
                st.write(f"""
**What this graph is:** A histogram showing **user/application usage intensity** measured by `{col_usage}`.  
**X-axis:** Usage metric values (bins).  
**Y-axis:** Number of observations per bin.

**What it shows in your data:**  
- Mean usage: **{_fmt_float(mean)}**; 95th percentile: **{_fmt_float(p95)}**; samples: **{_fmt_int(count_u)}**.

**Overall:** Right tail (high-usage) users indicate **premium tier** candidates; low tail suggests **over-licensing** or training gaps.

**How to read it operationally:**  
- **Tiering:** Assign higher tiers to sustained high users.  
- **Coaching:** Train low users or reclaim underused seats.  
- **Monitoring:** Watch drift across months.

**Why this matters:** Aligning license tiers with **actual usage** trims cost and boosts productivity.
""")
                ev_bits.append(f"Usage mean={_fmt_float(mean)}, p95={_fmt_float(p95)}, samples={_fmt_int(count_u)}.")

        # Department x Software
        if col_software and col_dept and (col_dept in df.columns):
            dept = (
                df[[col_dept, col_software]]
                .fillna({col_dept: "(unknown)", col_software: "(unknown)"})
                .groupby([col_dept, col_software])
                .size()
                .reset_index(name="count")
            )
            if not dept.empty:
                dept_sorted = dept.sort_values("count", ascending=False)
                fig2 = px.bar(dept_sorted.head(25), x=col_dept, y="count", color=col_software,
                              title=f"Top {col_software} by Department",
                              labels={col_dept:"Department","count":"Installs", col_software:"Software"})
                st.plotly_chart(fig2, use_container_width=True)
                top = dept_sorted.iloc[0]
                total_d = int(dept_sorted["count"].sum())
                avg_d = float(dept_sorted["count"].mean())

                # ---------- Analysis for Dept x Software ----------
                st.markdown("#### Analysis – Departmental Mix")
                st.write(f"""
**What this graph is:** A stacked bar showing **software installs by department** for top `{col_software}` titles.  
**X-axis:** Departments.  
**Y-axis:** Install counts per department, colored by software.

**What it shows in your data:**  
- Peak pairing: **{top[col_dept]} × {top[col_software]}** with **{_fmt_int(top['count'])} installs**.  
- **Total shown:** {_fmt_int(total_d)}; **Average per bar:** {_fmt_float(avg_d)}.

**Overall:** Tall stacks indicate **heavy dependency**; color dominance shows **department–title alignment**.

**How to read it operationally:**  
- **Bundle:** Pre-approve bundles per department.  
- **Prioritize:** Patch/upgrade windows by business criticality.  
- **Balance:** Watch for departments with too many unique titles.

**Why this matters:** Department alignment ensures **right tools for the job**, minimizing request churn and context switching.
""")
                ev_bits.append(f"Peak dept/software: {top[col_dept]} × {top[col_software]} ({_fmt_int(top['count'])}); total shown={_fmt_int(total_d)}; avg/bar={_fmt_float(avg_d)}.")

        ev_3e = " | ".join(ev_bits) if ev_bits else "Data not available."

        cio_3e = {
            "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Tier by usage** | **Phase 1 – Segment:** - Define usage cohorts using histogram metrics such as mean **{_fmt_float(mean) if 'mean' in locals() else '—'}** and p95 **{_fmt_float(p95) if 'p95' in locals() else '—'}** so thresholds are data-driven.<br><br>- Validate cohorts with business leaders to ensure tier assignments reflect real work patterns.<br><br>**Phase 2 – Assign:** - Map cohorts to premium, standard, and basic tiers with clear rules so entitlements are consistent and defensible.<br><br>- Document exceptions and review dates so temporary needs do not become permanent cost creep.<br><br>**Phase 3 – Review:** - Recalculate cohorts quarterly and adjust tiers as behavior shifts so the model stays accurate.<br><br>- Publish results and savings to maintain engagement. | - Paying for higher tiers only where usage warrants it reduces license spend while maintaining performance for power users.<br><br>- Transparent rules reduce negotiation friction which speeds approvals and entitlement changes.<br><br>- Regular reviews prevent over-licensing from creeping back which preserves savings over time.<br><br>- Clear mapping improves forecasting because demand by tier is well understood. | **Savings = (Downgraded seats × (premium−standard price)).** | {ev_3e} |
| **Reclaim underused seats** | **Phase 1 – Detect:** - Set a low-usage threshold over a rolling window and flag candidates for reclamation with owner context so discussions are efficient.<br><br>- Exclude temporary dips linked to seasonal work to avoid unnecessary churn.<br><br>**Phase 2 – Reassign:** - Move reclaimed seats to teams with active demand and record the transfer so audit trails remain clean.<br><br>- Hold a small buffer for urgent needs so projects are not delayed while purchasing catches up.<br><br>**Phase 3 – Automate:** - Send notifications before reclaim and perform changes automatically after grace periods so pools stay healthy without manual effort.<br><br>- Track outcomes to refine thresholds. | - Reallocation turns unused spend into productive capacity which raises ROI without new purchases.<br><br>- Automated enforcement keeps pools optimized with minimal labor which reduces administrative cost.<br><br>- Buffers reduce emergency buying which prevents premium pricing and stress for teams.<br><br>- Clean records simplify audits which saves time and avoids disruption. | **Savings = (Reclaimed seats × unit price).** | {ev_3e} |
| **Bundle by department** | **Phase 1 – Curate:** - Identify top titles by department such as **{top[col_dept] if 'top' in locals() else '—'}** and define why each is included so bundles are purposeful.<br><br>- Engage champions in each department to validate the set fits real workflows.<br><br>**Phase 2 – Pre-approve:** - Publish catalog bundles with entitlements and limits so requests are fast and predictable.<br><br>- Integrate with onboarding to auto-provision on day one so users start ready to work.<br><br>**Phase 3 – Lock:** - Add guardrails to prevent off-bundle installs and review exceptions monthly so standards remain clean.<br><br>- Refresh bundles as tools evolve so relevance stays high. | - Department bundles reduce ad-hoc requests which cuts ticket volume and processing effort.<br><br>- Auto-provisioning speeds time to productivity for new hires and role changes which benefits business throughput.<br><br>- Guardrails keep environments consistent which lowers support variance and troubleshooting time.<br><br>- Regular refresh keeps tools aligned with needs which maintains satisfaction and adoption. | **Value = (Requests avoided × handling time).** | {ev_3e}
""",
            "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Baseline per dept** | **Phase 1 – Define:** - Establish department-specific software baselines that reflect core workflows so support is optimized for what people actually use.<br><br>- Capture dependency maps so testing is focused and reliable.<br><br>**Phase 2 – Patch:** - Coordinate patch windows by department and test plans that mirror real tasks so changes land smoothly.<br><br>- Track pass rates and fix patterns quickly to improve future cycles.<br><br>**Phase 3 – Metrics:** - Measure incident deltas and stability trends after changes and adjust baselines based on evidence.<br><br>- Share results with leaders to align future priorities. | - Tailored baselines reduce regressions which improves stability and throughput for each department.<br><br>- Focused testing saves time which accelerates delivery of improvements.<br><br>- Evidence-based adjustments keep environments efficient which sustains performance gains.<br><br>- Shared metrics foster collaboration which improves execution quality. | **Benefit = (ΔIncidents × avg MTTR).** | {ev_3e} |
| **Auto-provisioning** | **Phase 1 – Templates:** - Build deployment templates for each department bundle so installs are consistent and repeatable at scale.<br><br>- Include health checks so failures are detected early with actionable messages.<br><br>**Phase 2 – Workflow:** - Use endpoint management to drive zero-touch deployments and track status through to completion.<br><br>- Integrate with HR events so changes trigger automatically when people join or move roles.<br><br>**Phase 3 – Audit:** - Remove drift automatically and reconcile inventory so records match reality.<br><br>- Report compliance to leaders so accountability is visible. | - Zero-touch deployment cuts manual effort which frees engineers to focus on complex tasks.<br><br>- Faster setup shortens downtime during device changes which improves team productivity.<br><br>- Automated drift correction keeps devices healthy which reduces ticket volume.<br><br>- Accurate records improve planning and compliance which reduces administrative work. | **Time saved = (Setup time saved × deployments).** | {ev_3e} |
| **Usage coaching** | **Phase 1 – Identify:** - Use telemetry to find low-usage cohorts who still need the tool so coaching is targeted where it will help most.<br><br>- Confirm with managers that low usage reflects a skill gap rather than role misfit.<br><br>**Phase 2 – Train:** - Deliver short, task-based sessions that address the most common sticking points and measure completion.<br><br>- Provide follow-up guides so learning is reinforced after training.<br><br>**Phase 3 – Measure:** - Track changes in usage and related ticket types to confirm the intervention worked and iterate where it did not.<br><br>- Share wins to encourage participation from other teams. | - Practical coaching improves adoption which raises productivity and reduces how-to tickets.<br><br>- Targeting keeps effort efficient which focuses resources on the biggest opportunities.<br><br>- Measured outcomes show what works which improves the next round of enablement.<br><br>- Shared success stories build momentum which spreads good practices quickly. | **Benefit = (How-to tickets avoided × cost).** | {ev_3e}
""",
            "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Self-service upgrades** | **Phase 1 – Gate:** - Allow upgrades for users whose usage meets defined thresholds so decisions feel fair and data-based.<br><br>- Explain criteria in plain language so expectations are clear.<br><br>**Phase 2 – Approvals:** - Auto-approve within thresholds and route exceptions to managers so most requests complete fast while oversight remains for edge cases.<br><br>- Provide timelines so users know when to expect outcomes.<br><br>**Phase 3 – Feedback:** - Ask users about post-upgrade experience and monitor performance to validate the benefits.<br><br>- Tune thresholds as patterns evolve. | - Fast access for power users removes bottlenecks which keeps high-value work moving.<br><br>- Clear criteria reduce back-and-forth which improves user experience and lowers handling time.<br><br>- Post-upgrade checks ensure the program delivers value which maintains trust.<br><br>- Adaptive thresholds keep the system fair as needs change. | **Value = (Wait time reduced × requests).** | {ev_3e} |
| **Transparent catalog** | **Phase 1 – Publish:** - Show department bundles and the rationale behind each item so users choose correctly from the start.<br><br>- Keep descriptions concise and focused on outcomes to reduce confusion.<br><br>**Phase 2 – Rationale:** - Explain when to request each tool and what alternatives exist so unnecessary tickets are avoided.<br><br>- Provide quick comparisons so decisions are simple.<br><br>**Phase 3 – Review:** - Update the catalog quarterly with feedback and usage trends so it stays relevant and helpful.<br><br>- Announce changes so users know what improved. | - Clarity reduces help-seeking which lowers ticket load and response times.<br><br>- Better choices mean fewer corrections which improves satisfaction with the process.<br><br>- Regular updates keep guidance fresh which sustains trust in the catalog.<br><br>- Simple comparisons increase confidence which accelerates self-service adoption. | **Value = (Inquiries avoided × cost/call).** | {ev_3e} |
| **Dept success stories** | **Phase 1 – Share:** - Publish short case studies that show outcomes from adopting bundles so peers see concrete benefits.<br><br>- Highlight the steps that made change easy so others can replicate them.<br><br>**Phase 2 – Recognize:** - Acknowledge champions who led improvements so participation is rewarded and visible.<br><br>- Invite them to share tips at team forums to spread practical advice.<br><br>**Phase 3 – Replicate:** - Package the approach and offer help to similar departments so wins scale quickly.<br><br>- Track adoption and impact to verify results. | - Seeing peers succeed builds confidence which increases willingness to adopt standards.<br><br>- Recognition encourages proactive behavior which accelerates improvement across teams.<br><br>- Replication reduces time to benefit for others which raises organization-wide satisfaction.<br><br>- Measured impact proves value which sustains support for the program. | **Benefit = (Adoption uplift × users).** | {ev_3e}
"""
        }
        render_cio_tables("CIO – Usage & Department Mix", cio_3e)
