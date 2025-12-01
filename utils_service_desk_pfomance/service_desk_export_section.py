# ==========================================================
# Service Desk Performance — Executive Report Export Section
# ==========================================================
import streamlit as st
from utils_service_desk_pfomance.report_ticket import report_ticket

def service_desk_export_section(df_filtered, client_name="Write your client name", logo_path="logo.png"):
    """
    Export section for Service Desk dashboard.
    Auto-collects visuals, insights & CIO recommendations from all modules.
    """

    st.markdown("---")
    st.subheader("📤 Export Full Executive Insight Report")

    st.markdown("""
    Generate a professional Service Desk report that includes:
    - All key KPIs (SLA, MTTR, Open Tickets)
    - Visual insights and written analysis
    - CIO recommendation tables (Cost, Performance, Satisfaction)
    - Appendices and data summaries
    """)

    col1, col2 = st.columns(2)
    with col1:
        period = st.text_input("Report Period", "Jan – Sep 2025")
    with col2:
        analyst = st.text_input("Analyst / Author", "AI Business Insight Strategist")

    generate_btn = st.button("⚙️ Generate Executive Report", use_container_width=True)

    if generate_btn:
        if df_filtered is None or df_filtered.empty:
            st.warning("⚠️ Please upload or filter your dataset before generating the report.")
            return

        with st.spinner("Building Service Desk Executive Report... please wait."):
            try:
                pdf_bytes, docx_bytes = report_ticket(
                    df=df_filtered,
                    client_name=client_name,
                    period=period,
                    logo_path=logo_path,
                    author=analyst
                )

                st.success("✅ Executive Report generated successfully!")

                st.download_button(
                    "⬇️ Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"ServiceDesk_ExecutiveReport_{client_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

                if docx_bytes:
                    st.download_button(
                        "⬇️ Download Word (DOCX) Report",
                        data=docx_bytes,
                        file_name=f"ServiceDesk_ExecutiveReport_{client_name}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"❌ Report generation failed: {e}")
    else:
        st.info("Click **Generate Executive Report** to export all Service Desk insights.")
