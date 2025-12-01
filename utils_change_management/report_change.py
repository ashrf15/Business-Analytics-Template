from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import datetime
import pandas as pd
import numpy as np


def _kpi_row(label: str, value: str):
    return [label, value]


def report_change(df: pd.DataFrame, uploaded_file=None, start_date=None, end_date=None):
    """
    PDF Export — Change Management Summary
    Aligned with your Service Desk export format:
    - Blue title bar / header info
    - Date range
    - KPI table
    - Narrative + condensed recommendation summary
    """
    d = df.copy()
    d.columns = [c.strip().lower().replace(" ", "_") for c in d.columns]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Change Management Summary Report")
    styles = getSampleStyleSheet()
    content = []

    # ---------------------------
    # HEADER (Blue-styled title)
    # ---------------------------
    title = styles["Heading1"]
    title.textColor = colors.HexColor("#0b5394")
    content.append(Paragraph("<b>Change Management Summary Report</b>", title))
    content.append(Spacer(1, 12))

    now = datetime.datetime.now().strftime("%d %B %Y, %H:%M")
    content.append(Paragraph(f"Generated on: <b>{now}</b>", styles["Normal"]))
    if start_date and end_date:
        content.append(Paragraph(f"Reporting Period: <b>{start_date}</b> – <b>{end_date}</b>", styles["Normal"]))
    if uploaded_file is not None:
        content.append(Paragraph(f"Source File: <b>{uploaded_file.name}</b>", styles["Normal"]))
    content.append(Spacer(1, 12))

    # ---------------------------
    # KPI TABLE
    # ---------------------------
    total_changes = len(d)
    implemented = d[d.get("status", "").astype(str).str.lower().eq("implemented")].shape[0]
    success_rate = d[d.get("success") == True].shape[0] / total_changes * 100 if total_changes > 0 else 0.0
    emergency_share = d[d.get("emergency_flag") == True].shape[0] / total_changes * 100 if total_changes > 0 else 0.0
    avg_approval = d["approval_time"].mean() if "approval_time" in d.columns else np.nan
    backlog = d[d.get("status", "").astype(str).str.lower().isin(["open", "pending_approval", "pending approval", "in_progress", "in progress"])].shape[0]

    kpi_data = [
        ["Metric", "Value"],
        _kpi_row("Total Changes", f"{total_changes:,}"),
        _kpi_row("Implemented", f"{implemented:,}"),
        _kpi_row("Success Rate", f"{success_rate:.1f}%"),
        _kpi_row("Emergency Share", f"{emergency_share:.1f}%"),
        _kpi_row("Average Approval Time (hrs)", "N/A" if np.isnan(avg_approval) else f"{avg_approval:.1f}"),
        _kpi_row("Backlog Items", f"{backlog:,}"),
    ]

    kpi_table = Table(kpi_data, colWidths=[200, 180])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b5394")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BOX", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    content.append(kpi_table)
    content.append(Spacer(1, 18))

    # ---------------------------
    # NARRATIVE
    # ---------------------------
    narrative = f"""
    <b>Executive Overview</b><br/>
    This report consolidates change performance for the period
    <b>{start_date}</b> to <b>{end_date}</b>. The KPIs reflect governance agility (approval time),
    operational stability (success rate), and risk posture (emergency share, downtime impact).<br/><br/>
    Maturity indicators include: improving success rates across categories, decreasing emergency share,
    and better adherence to change windows — each contributing to lower rework cost and stronger business trust.
    Targeted actions are summarized below to guide cost control, performance uplift, and client experience.
    """
    content.append(Paragraph(narrative, styles["Normal"]))
    content.append(Spacer(1, 14))

    # ---------------------------
    # RECOMMENDATION SUMMARY (concise)
    # ---------------------------
    rec_summary = [
        ["Focus Area", "Strategic Recommendation", "Expected Impact"],
        ["Approval Process", "Automate low-risk approvals & escalate breaches to SLA.", "Reduce approval cycle time by 25%."],
        ["Impact Control", "Phased rollouts & simulation for high-risk changes.", "Cut downtime by ~30%."],
        ["Window Compliance", "Calendar sync & readiness automation.", "Increase compliance by 20%."],
        ["Emergency Handling", "Predictive monitoring + E-CAB protocols.", "Lower emergency share by 30–35%."],
        ["Change Quality", "Post-change RCA on rollbacks; regression automation.", "Reduce rework cost by RM30–50K/qtr."],
    ]
    rec_table = Table(rec_summary, colWidths=[120, 240, 120])
    rec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b5394")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BOX", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    content.append(rec_table)
    content.append(Spacer(1, 18))

    # ---------------------------
    # FOOTER
    # ---------------------------
    footer = """
    <b>Prepared by Mesiniaga Business Analytics Template</b><br/>
    This document is system-generated for internal governance and executive decision-making.
    """
    content.append(Paragraph(footer, styles["Italic"]))

    doc.build(content)
    buffer.seek(0)
    return buffer
