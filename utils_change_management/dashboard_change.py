import streamlit as st
import plotly.express as px
import pandas as pd

def dashboard_change(df):
    # --- Header ---
    st.markdown("""
        <div style='background-color:#0b5394;padding:15px;border-radius:10px'>
            <h2 style='color:white;text-align:center;'>🔧 Change Management Summary Dashboard</h2>
        </div>
    """, unsafe_allow_html=True)

    # --- Date Filter using Implemented_Date ---
    if 'Implemented_Date' in df.columns:
         # Convert to datetime safely
        df['Implemented_Date'] = pd.to_datetime(df['Implemented_Date'], errors='coerce')

        # Drop NaT values before computing min/max
        valid_dates = df['Implemented_Date'].dropna()

        if not valid_dates.empty:
           min_date = valid_dates.min().date()
           max_date = valid_dates.max().date()
        else:
           st.warning("⚠️ No valid Implemented_Date found in dataset.")
           return


        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date, key="start_date_change_dash_start")
        with col2:
            end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date, key="start_date_change_dash_end")

        st.markdown(f"🗓️ **Selected Range:** `{start_date.strftime('%d/%m/%Y')}` → `{end_date.strftime('%d/%m/%Y')}`")
        reset_filter = st.button("🔁 Reset to Default", key="reset_button_change")

        if reset_filter:
            df_filtered = df.copy()
            st.info("Showing all available data (no date filter applied).")
        elif start_date > end_date:
            st.warning("⚠️ Start date is after end date. Please select a valid range.")
            return
        else:
            df_filtered = df[
                (df['Implemented_Date'].dt.date >= start_date) &
                    (df['Implemented_Date'].dt.date <= end_date)
            ]

    else:
        df_filtered = df.copy()

    # --- KPIs ---
    st.markdown("### 🔹 Key Change Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    total_changes = len(df_filtered)
    implemented = df_filtered['status'].astype(str).str.lower().eq('implemented').sum()
    backlog = total_changes - implemented
    emergency = df_filtered['Emergency_Flag'].astype(str).str.lower().eq('yes').sum() if 'Emergency_Flag' in df_filtered.columns else 0

    col1.metric("Total Changes", f"{total_changes:,}")
    col2.metric("Implemented", f"{implemented:,}")
    col3.metric("Backlog", f"{backlog:,}")
    col4.metric("Emergency Changes", f"{emergency:,}")
    col5.metric("Avg Approval Time (days)", f"{df_filtered['Approval_Duration'].mean():.1f}" if 'Approval_Duration' in df_filtered.columns else "N/A")

    st.markdown("---")

    # --- Change Type & Category Breakdown ---
    st.markdown("### 🗂️ Change Type & Category Breakdown")
    row1_col1, row1_col2 = st.columns(2)
    if 'Category' in df_filtered.columns:
        with row1_col1:
            cat_counts = df_filtered['Category'].value_counts().reset_index()
            cat_counts.columns = ['Category', 'Count']
            fig = px.bar(cat_counts, x='Count', y='Category', orientation='h', title="Change Requests by Category", color='Count', color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)

    if 'Change_Type' in df_filtered.columns:
        with row1_col2:
            type_counts = df_filtered['Change_Type'].value_counts().reset_index()
            type_counts.columns = ['Change_Type', 'Count']
            fig = px.pie(type_counts, names='Change_Type', values='Count', title="Change Type Distribution", color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)

    # --- Approval Duration ---
    if 'Approval_Duration' in df_filtered.columns:
        st.markdown("### ⏳ Approval Duration Analysis")
        fig = px.histogram(df_filtered, x='Approval_Duration', nbins=20, title="Distribution of Approval Duration (days)", color_discrete_sequence=['#1f77b4'])
        st.plotly_chart(fig, use_container_width=True)

    # --- Status Distribution ---
    if 'Status' in df_filtered.columns:
        st.markdown("### 📋 Status Distribution")
        status_counts = df_filtered['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig = px.bar(status_counts, x='Status', y='Count', title="Change Request Status Overview", color='Count', color_continuous_scale='Blues')
        st.plotly_chart(fig, use_container_width=True)

    # --- Monthly Trend ---
    if 'Implemented_Date' in df_filtered.columns:
        st.markdown("### 🕒 Monthly Change Implementation Trend")
        df_filtered['Month'] = pd.to_datetime(df_filtered['Implemented_Date'], errors='coerce').dt.to_period("M").astype(str)
        monthly = df_filtered.groupby('Month').size().reset_index(name='Count')
        fig = px.line(monthly, x='Month', y='Count', markers=True, title="Monthly Change Volume", color_discrete_sequence=['#0b5394'])
        st.plotly_chart(fig, use_container_width=True)

    # --- Emergency Changes ---
    if 'Emergency_Flag' in df_filtered.columns:
        st.markdown("### 🚨 Emergency Change Breakdown")
        emer_counts = df_filtered['Emergency_Reason'].value_counts().reset_index() if 'Emergency_Reason' in df_filtered.columns else pd.DataFrame()
        if not emer_counts.empty:
            emer_counts.columns = ['Emergency_Reason', 'Count']
            fig = px.bar(emer_counts, x='Count', y='Emergency_Reason', orientation='h', title="Top Emergency Change Reasons", color='Count', color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)

    # --- Technician or Approver Breakdown ---
    if 'Approver' in df_filtered.columns:
        st.markdown("### 👨‍💼 Top Approvers by Volume")
        app_counts = df_filtered['Approver'].value_counts().head(10).reset_index()
        app_counts.columns = ['Approver', 'Count']
        fig = px.bar(app_counts, x='Approver', y='Count', title="Top 10 Approvers", color='Count', color_continuous_scale='Blues')
        st.plotly_chart(fig, use_container_width=True)

    return df_filtered
