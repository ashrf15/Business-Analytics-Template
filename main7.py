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
import streamlit as st
from utils1.report import report


from utils1.data_cleaning import data_cleaning
from utils1.recommendation import recommendation
from utils1.dashboard import dashboard
from utils1.report import report

st.set_page_config(page_title="Incident Ticket Cleaner & Analyzer", layout="wide")
st.title("📊 Incident Ticket Cleaner & Analyzer")
st.markdown("Upload your dataset, view cleaning summary, explore insights, and download the cleaned file.")

with st.sidebar:
    st.sidebar.image("logo.png")
    st.header("📂 Upload Data")
    uploaded_file = st.file_uploader("Upload Incident Excel File", type=["xlsx"])
    st.markdown("""<small>Required columns: Created Time, Resolved Time, Technician, Department, etc.</small>""", unsafe_allow_html=True)

if uploaded_file:
    df = pd.read_excel(uploaded_file, engine='openpyxl')
    

    tab1, tab2, tab3, tab4 = st.tabs(["🧺 Cleaning Summary", "📈 Recommendation", "Dashboard Overview", "📅 Export"])
  
    with tab1:
        df=data_cleaning(df, uploaded_file)

    with tab2:
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
            pdf_buffer = report(df, uploaded_file)  # Now only returns buffer
            st.success("✅ PDF report generated.")

            # --- PDF Preview ---
            base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
            pdf_display = f"""
            <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>
            """
            st.markdown("### 📄 Preview PDF")
            st.components.v1.html(pdf_display, height=800)

            # --- Download Button ---
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_buffer,
                file_name="ticket_report.pdf",
                mime="application/pdf"
            )