import io
import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import tempfile
from PIL import Image
import base64
import io
import re
import types
import datetime as _dt

from file_manager import file_manager_ui, get_active_uploaded_like

#-----------------------------------------------------------------------------------------------------------------------------------------

#ticketing
from utils_service_desk_pfomance.data_cleaning_ticket import data_cleaning_ticket as ticket_data_cleaning
from utils_service_desk_pfomance.recommendation_ticketing import recommendation_ticketing
from utils_service_desk_pfomance.dashboard_ticket import dashboard_ticket
from utils_service_desk_pfomance.report_ticket import report_ticket as generate_service_desk_report

#asset
from utils_asset.data_cleaning_asset import data_cleaning_asset as asset_data_cleaning
from utils_asset.recommendation_asset import recommendation_asset
from utils_asset.dashboard_asset import dashboard_asset
from utils_asset.report_asset import report_asset as generate_asset_report

#incident
from utils_incident.recommendation_incident import recommendation_incident
from utils_incident.data_cleaning_incident import data_cleaning_incident as incident_data_cleaning
from utils_incident.dashboard_incident import dashboard_incident
from utils_incident.report_incident import report_incident as generate_incident_report

#scorecard
from utils_scorecard.recommendation_scorecard import recommendation_scorecard
from utils_scorecard.data_cleaning_scorecard import data_cleaning_scorecard as scorecard_data_cleaning
from utils_scorecard.dashboard_scorecard import dashboard_scorecard
from utils_scorecard.report_scorecard import report_scorecard

#service_availability
from utils_service_availability.recommendation_service import recommendation_service
from utils_service_availability.data_cleaning_service_availability import data_cleaning_service_availability as service_data_cleaning
from utils_service_availability.dashboard_service import dashboard_service
from utils_service_availability.report_service import report_service as generate_service_report

#capacity_optimization
from utils_capacity.recommendations_capacity import recommendations_capacity
from utils_capacity.data_cleaning_capacity import data_cleaning_capacity as data_cleaning_capacity
from utils_capacity.dashboard_capacity import dashboard_capacity
from utils_capacity.report_capacity import report_capacity as generate_capacity_report

# change management
from utils_change_management.data_cleaning_change import data_cleaning_change
from utils_change_management.recommendation_change import recommendation_change
from utils_change_management.dashboard_change import dashboard_change
from utils_change_management.report_change import report_change

# SLA Compliance
from utils_sla.data_cleaning_sla import data_cleaning_sla
from utils_sla.recommendation_sla import recommendation_sla
from utils_sla.dashboard_sla import dashboard_sla
from utils_sla.report_sla import report_sla

# Network Performance
from utils_network.data_cleaning_network import data_cleaning_network
from utils_network.recommendation_network import recommendation_network
from utils_network.dashboard_network import dashboard_network
from utils_network.report_network import report_network

# Server Performance
from utils_server_performance.data_cleaning_server import data_cleaning_server
from utils_server_performance.recommendation_server import recommendation_server
from utils_server_performance.dashboard_server import dashboard_server
from utils_server_performance.report_server import report_server

#template
from utils_template.recommendation import recommendation
from utils_template.data_cleaning import data_cleaning as data_cleaning
from utils_template.dashboard import dashboard
from utils_template.report import report

import plotly.io as pio


#---------------------------------------------------------------------------------------------------------------

pio.templates["mesiniaga_white"] = pio.templates["plotly_white"]
pio.templates["mesiniaga_white"]["layout"].update({
    "colorway": ["#004C99", "#007ACC", "#FF9F1C", "#2ECC71", "#E15F99"],
    "font": {"color": "black"},
    "paper_bgcolor": "white",
    "plot_bgcolor": "white",
})
pio.templates.default = "mesiniaga_white"


# Set page config
st.set_page_config(page_title="Data Cleaner & Analyzer", layout="wide")
st.title("📊 Multi-System Data Cleaner & Analyzer")
st.markdown("Select your data type, upload your dataset, and view cleaning summary, insights, and reports.")

#-------------------------------------------------------------------------------------------------------------------------------------------

# Sidebar – dataset type selection
with st.sidebar:
    st.sidebar.image("logo.png")
    st.header("🪪 Choose Data Type")
    data_type = st.selectbox(
        "Select Dataset Type:",
        (
            "IT Service Desk Performance Dashboard",  
            "Incident Management Report",
            "IT Asset Inventory Report",
            "IT Service Delivery Scorecard",
            "Change Management Summary",
            "Service Level Agreement (SLA) Compliance Report",
            "Network Performance Dashboard",
            "Server Performance Report",
            "IT Operations Dashboard",
            "IT Service Availability Report",
            "Service Level Agreement (SLA) Performance Analysis",
            "IT Infrastructure Capacity Optimization Analysis",
            "IT Service Portfolio Optimization Dashboard",
        ),
        key="dataset_select"
    )
    st.divider()

# NEW: compatibility for your existing code paths that expect uploaded_file.name
df_active = file_manager_ui("📂 Data Manager")
uploaded_file = get_active_uploaded_like()


#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Use the active dataset from the manager
if df_active is None:
    st.info("Upload/select a dataset from the Data Manager to proceed.")
    st.stop()

df = df_active

# Optional sanity pings while testing
st.sidebar.caption(f"Active DF shape: {df.shape}")
st.sidebar.caption(f"Active name: {uploaded_file.name if uploaded_file else 'None'}")

#------------------------------------------------------------------------------------------------------------------------------------------------------------

# =========================
# Export UI + Caching (self-contained)
# Place this ABOVE where you call export_report_ui(...)
# =========================
import io as _io_again  # harmless duplicate to preserve "do not change anything else"
import re as _re_again
import types as _types_again
import datetime as _dt_again
import pandas as _pd
import streamlit as _st_again

@st.cache_data(
    show_spinner=False,
    # Safety net: treat function objects as a constant hash so cache never chokes on them
    hash_funcs={types.FunctionType: lambda _: "FUNC-IGNORED"}
)
def _generate_report_cached(_generator_func, df, client_name, period, logo_path):
    """
    Leading underscore on `_generator_func` tells Streamlit NOT to hash this arg.
    """
    return _generator_func(
        df,
        client_name=client_name,
        period=period,
        logo_path=logo_path,
    )

def _make_filename(default_filename: str | None, client_name: str | None, period: str | None, ext: str) -> str:
    """Build a safe filename given defaults/client/period and the desired extension."""
    if default_filename and str(default_filename).strip():
        base = str(default_filename).strip()
    else:
        cn = (client_name or "Report").strip()
        pr = (period or "period").strip()
        base = f"{cn}_{pr}"
    base = re.sub(r"\s+", "_", base)
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    if not base.lower().endswith(f".{ext}"):
        base = f"{base}.{ext}"
    return base

def export_report_ui(
    generator_func,
    df,
    client_name: str,
    period: str,
    logo_path: str | None = None,
    *,
    default_filename: str | None = None,
    btn_label_pdf: str = "⬇️ Download PDF",
    btn_label_docx: str = "⬇️ Download DOCX",
    key_prefix: str = "export_report",
):
    """
    Renders buttons to export PDF/DOCX. `generator_func` must return (pdf_bytes, docx_bytes).
    """
    st.markdown("### 📄 Export — Executive Report")

    # Generate (cached)
    pdf_bytes, docx_bytes = _generate_report_cached(
        generator_func, df, client_name, period, logo_path
    )

    # PDF
    if isinstance(pdf_bytes, (bytes, bytearray, io.BytesIO)):
        data_pdf = pdf_bytes.getvalue() if hasattr(pdf_bytes, "getvalue") else pdf_bytes
        pdf_name = _make_filename(default_filename, client_name, period, "pdf")
        st.download_button(
            label=btn_label_pdf,
            data=data_pdf,
            file_name=pdf_name,
            mime="application/pdf",
            key=f"{key_prefix}_pdf",
        )
    else:
        st.warning("PDF stream was not produced by the report generator.")

    # DOCX
    if docx_bytes:
        data_docx = docx_bytes.getvalue() if hasattr(docx_bytes, "getvalue") else docx_bytes
        docx_name = _make_filename(default_filename, client_name, period, "docx")
        st.download_button(
            label=btn_label_docx,
            data=data_docx,
            file_name=docx_name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"{key_prefix}_docx",
        )
    else:
        st.info("DOCX export not available (library missing or generator skipped DOCX).")

# (Optional) helper to infer a human-friendly period from your DF
def _infer_period_from_df(df: _pd.DataFrame) -> str:
    try:
        if "created_time" in df.columns:
            s = _pd.to_datetime(df["created_time"], errors="coerce").dropna()
        elif "created_date" in df.columns:
            s = _pd.to_datetime(df["created_date"], errors="coerce").dropna()
        else:
            s = _pd.Series([], dtype="datetime64[ns]")
        if not s.empty:
            dmin, dmax = s.min().date(), s.max().date()
            if dmin.year == dmax.year:
                return dmin.strftime("%b %Y") if dmin.month == dmax.month else f"{dmin.strftime('%b')}–{dmax.strftime('%b %Y')}"
            return f"{dmin.strftime('%b %Y')} – {dmax.strftime('%b %Y')}"
    except Exception:
        pass
    return _dt.date.today().strftime("%b %Y")

# ---------------------------------------------------------------------------
# Define client_name / period inputs once, for all flows
_default_client = st.session_state.get("client_name_default", "UEMS")
_default_period = st.session_state.get("report_period_default", _infer_period_from_df(df))
client_name = st.text_input("Client Name", value=_default_client, key="ui_client_name").strip() or "Client"
period = st.text_input("Report Period Label", value=_default_period, key="ui_report_period").strip() or _default_period
st.session_state["client_name_default"] = client_name
st.session_state["report_period_default"] = period

#-----------------------------------------------------------------------------------------------------------------------------------

# Service Desk workflow
if data_type == "IT Service Desk Performance Dashboard":
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧺 Cleaning Summary", 
        "📈 Recommendation", 
        "📊 Dashboard Overview", 
        "📅 Export"
    ])

    with tab1:
        df = ticket_data_cleaning(df, uploaded_file)

    with tab2:
        st.markdown("## 📊 IT Service Desk Performance Dashboard")
        recommendation_ticketing(df)

    with tab3:
        dashboard_ticket(df)

    with tab4:
        export_report_ui(
            generator_func=generate_service_desk_report,
            df=df,
            client_name=client_name,
            period=period,
            logo_path="logo.png",
            default_filename="IT_Service_Desk_Report"  # optional
        )

#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
# Asset Data workflow
if data_type == "IT Asset Inventory Report":
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧺 Cleaning Summary", 
        "📈 Recommendation", 
        "📊 Dashboard Overview", 
        "📅 Export"
    ])

    with tab1:
        df = asset_data_cleaning(df, uploaded_file)

    with tab2:
        st.markdown("## 📊 IT Asset Inventory Report")
        recommendation_asset(df)

    with tab3:
        dashboard_asset(df)

    with tab4:
        export_report_ui(
            generator_func=generate_asset_report,
            df=df,
            client_name=client_name,
            period=period,
            logo_path="logo.png",
            default_filename="IT_Asset_Inventory_Report"  # optional
        )
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Incident Data workflow
if data_type == "Incident Management Report":
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧺 Cleaning Summary", 
        "📈 Recommendation", 
        "📊 Dashboard Overview", 
        "📅 Export"
    ])

    with tab1:
        st.subheader("🧺 Cleaning Summary")
        df = incident_data_cleaning(df, uploaded_file)
        st.dataframe(df.head())  # Show preview after cleaning
    
    with tab2:
        st.markdown("## 📊 Incident Management Report Recommendation")
        recommendation_incident(df)

    with tab3:
        dashboard_incident(df)

    with tab4:
        export_report_ui(
            generator_func=generate_incident_report,
            df=df,
            client_name=client_name,
            period=period,
            logo_path="logo.png",
            default_filename="Incident_Management_Report"  # optional
        )
#-----------------------------------------------------------------------------------------------------------------------------------

# Change Management Summary
if data_type == "Change Management Summary":
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧺 Cleaning Summary", 
        "📈 Recommendation", 
        "📊 Dashboard Overview", 
        "📅 Export"
    ])

    with tab1:
        df = ticket_data_cleaning(df, uploaded_file)

    with tab2:
        st.markdown("## 📊 Change Management Summary")
        recommendation_ticketing(df)

    with tab3:
        dashboard(df)

    with tab4:
        st.subheader("📅 Download Cleaned Dataset")
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        st.download_button("📅 Download CSV", output, file_name="cleaned_file.csv", mime="text/csv")

        st.subheader("📄 Export PDF Report")
        if st.button("📄 Generate PDF Report"):
            pdf_buffer = report(df, uploaded_file)
            st.success("✅ PDF report generated.")
            base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
            pdf_display = f"""<iframe src="data:application/pdf;base64,{base64_pdf}" 
                            width="100%" height="800px"></iframe>"""
            st.markdown("### 📄 Preview PDF")
            st.components.v1.html(pdf_display, height=800)
            st.download_button("⬇️ Download PDF", pdf_buffer, file_name="ticket_report.pdf", mime="application/pdf")

#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
# Service Level Agreement (SLA) Compliance Report
if data_type == "Service Level Agreement (SLA) Compliance Report":
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧺 Cleaning Summary", 
        "📈 Recommendation", 
        "📊 Dashboard Overview", 
        "📅 Export"
    ])

    with tab1:
        df = data_cleaning_sla(df, uploaded_file)   # ✅ use SLA cleaner

    with tab2:
        recommendation_sla(df)

    with tab3:
        dashboard_sla(df)

    with tab4:
        st.subheader("📅 Download Cleaned Dataset")
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        st.download_button("📅 Download CSV", output, file_name="cleaned_sla_file.csv", mime="text/csv")

        st.subheader("📄 Export PDF Report")
        if st.button("📄 Generate PDF Report"):
            pdf_buffer = report_sla(df, uploaded_file)
            st.success("✅ PDF report generated.")
            import base64
            base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
            pdf_display = f"""<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px"></iframe>"""
            st.markdown("### 📄 Preview PDF")
            st.components.v1.html(pdf_display, height=800)
            st.download_button("⬇️ Download PDF", pdf_buffer, file_name="sla_report.pdf", mime="application/pdf")


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Network Performance Dashboard
if data_type == "Network Performance Dashboard":
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧺 Cleaning Summary", 
        "📈 Recommendation", 
        "📊 Dashboard Overview", 
        "📅 Export"
    ])

    with tab1:
        df = data_cleaning_network(df, uploaded_file)

    with tab2:
        recommendation_network(df)

    with tab3:
        dashboard_network(df)

    with tab4:
        st.subheader("📅 Download Cleaned Dataset")
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        st.download_button("📅 Download CSV", output, file_name="cleaned_network_file.csv", mime="text/csv")

        st.subheader("📄 Export PDF Report")
        if st.button("📄 Generate PDF Report"):
            pdf_buffer = report_network(df, uploaded_file)
            st.success("✅ PDF report generated.")
            import base64
            base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
            pdf_display = f"""<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px"></iframe>"""
            st.markdown("### 📄 Preview PDF")
            st.components.v1.html(pdf_display, height=800)
            st.download_button("⬇️ Download PDF", pdf_buffer, file_name="network_report.pdf", mime="application/pdf")

#-----------------------------------------------------------------------------------------------------------------------------------

# Server Performance Report
if data_type == "Server Performance Report":
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧺 Cleaning Summary", 
        "📈 Recommendation", 
        "📊 Dashboard Overview", 
        "📅 Export"
    ])

    with tab1:
        df = data_cleaning_server(df, uploaded_file)

    with tab2:
        recommendation_server(df)

    with tab3:
        dashboard_server(df)

    with tab4:
        st.subheader("📅 Download Cleaned Dataset")
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        st.download_button("📅 Download CSV", output, file_name="cleaned_server_file.csv", mime="text/csv")

        st.subheader("📄 Export PDF Report")
        if st.button("📄 Generate PDF Report"):
            pdf_buffer = report_server(df, uploaded_file)
            st.success("✅ PDF report generated.")
            import base64
            base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
            pdf_display = f"""<iframe src="data:application/pdf;base64,{base64_pdf}" 
                            width="100%" height="800px"></iframe>"""
            st.markdown("### 📄 Preview PDF")
            st.components.v1.html(pdf_display, height=800)
            st.download_button("⬇️ Download PDF", pdf_buffer, file_name="server_report.pdf", mime="application/pdf")


#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
# IT Service Delivery Scorecard
if data_type == "IT Service Delivery Scorecard":
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧺 Cleaning Summary", 
        "📈 Recommendation", 
        "📊 Dashboard Overview", 
        "📅 Export"
    ])

    with tab1:
        df = scorecard_data_cleaning(df, uploaded_file)

    with tab2:
        st.markdown("## 📊 IT Service Delivery Scorecard")
        recommendation_scorecard(df)

    with tab3:
        dashboard_scorecard(df)

    with tab4:
        st.subheader("📅 Download Cleaned Dataset")
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        st.download_button("📅 Download CSV", output, file_name="cleaned_asset_file.csv", mime="text/csv")

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------

# IT Service Availability Report
if data_type == "IT Service Availability Report":
    tab1, tab2, tab3, tab4= st.tabs([
        "🧺 Cleaning Summary", 
        "📈 Recommendation", 
        "📊 Dashboard Overview", 
        "📅 Export"
    ])

    with tab1:
        st.subheader("🧺 Cleaning Summary")
        df = service_data_cleaning(df, uploaded_file)
        st.dataframe(df.head())  # Show preview after cleaning
    
    with tab2:
        st.markdown("## 📊 IT Service Availability Report")
        recommendation_service(df)

    with tab3:
        dashboard_service(df)

    with tab4:
        export_report_ui(
            generator_func=generate_service_report,
            df=df,
            client_name=client_name,
            period=period,
            logo_path="logo.png",
            default_filename="IT_Service_Availability_Report_Report"  # optional
        )
#-----------------------------------------------------------------------------------------------------------------------------------

# Service Level Agreement (SLA) Performance Analysis
if data_type == "Service Level Agreement (SLA) Performance Analysis":
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧺 Cleaning Summary", 
        "📈 Recommendation", 
        "📊 Dashboard Overview", 
        "📅 Export"
    ])

    with tab1:
        df = data_cleaning(df, uploaded_file)

    with tab2:
        st.markdown("## 📊 Service Level Agreement (SLA) Performance Analysis")
        recommendation(df)

    with tab3:
        dashboard(df)

    with tab4:
        st.subheader("📅 Download Cleaned Dataset")
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        st.download_button("📅 Download CSV", output, file_name="cleaned_file.csv", mime="text/csv")

        st.subheader("📄 Export PDF Report")
        if st.button("📄 Generate PDF Report"):
            pdf_buffer = report(df, uploaded_file)
            st.success("✅ PDF report generated.")
            base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
            pdf_display = f"""<iframe src="data:application/pdf;base64,{base64_pdf}" 
                            width="100%" height="800px"></iframe>"""
            st.markdown("### 📄 Preview PDF")
            st.components.v1.html(pdf_display, height=800)
            st.download_button("⬇️ Download PDF", pdf_buffer, file_name="ticket_report.pdf", mime="application/pdf")

#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
# IT Infrastructure Capacity Optimization Analysis
if data_type == "IT Infrastructure Capacity Optimization Analysis":
    tab1, tab2, tab3, tab4= st.tabs([
        "🧺 Cleaning Summary", 
        "📈 Recommendation", 
        "📊 Dashboard Overview", 
        "📅 Export"
        ])

    with tab1:
        df = data_cleaning_capacity(df, uploaded_file)

    with tab2:
        st.markdown("## 📊 IT Infrastructure Capacity Optimization Analysis")
        recommendations_capacity(df)

    with tab3:
        dashboard_capacity(df)

    with tab4:
        export_report_ui(
            generator_func=generate_capacity_report,
            df=df,
            client_name=client_name,
            period=period,
            logo_path="logo.png",
            default_filename="IT_Infrastructure_Capacity_Optimization_Report"  # optional
        )

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------

# IT Service Portfolio Optimization Dashboard
if data_type == "IT Service Portfolio Optimization Dashboard":
    tab1, tab2, tab3, tab4= st.tabs([
        "🧺 Cleaning Summary", 
        "📈 Recommendation", 
        "📊 Dashboard Overview", 
        "📅 Export"
    ])

    with tab1:
        st.subheader("🧺 Cleaning Summary")
        df = data_cleaning(df, uploaded_file)
        st.dataframe(df.head())  # Show preview after cleaning
    
    with tab2:
        st.markdown("## 📊 IT Service Portfolio Optimization Dashboard")
        recommendation(df)

    with tab3:
        dashboard(df)

    with tab4:
        st.subheader("📅 Download Cleaned Dataset")
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        st.download_button("📅 Download CSV", output, file_name="cleaned_file.csv", mime="text/csv")

        st.subheader("📄 Export PDF Report")
        if st.button("📄 Generate PDF Report"):
            pdf_buffer = report(df, uploaded_file)
            st.success("✅ PDF report generated.")
            base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
            pdf_display = f"""<iframe src="data:application/pdf;base64,{base64_pdf}" 
                            width="100%" height="800px"></iframe>"""
            st.markdown("### 📄 Preview PDF")
            st.components.v1.html(pdf_display, height=800)
            st.download_button("⬇️ Download PDF", pdf_buffer, file_name="ticket_report.pdf", mime="application/pdf")

#-----------------------------------------------------------------------------------------------------------------------------------
