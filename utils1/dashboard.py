import streamlit as st
import plotly.express as px
import pandas as pd

def dashboard(df):
    st.markdown("## 📊 Executive Visual Dashboard")

    # --- Date Filter within Dashboard ---
    if 'created_time' in df.columns and not df['created_time'].isna().all():
        df['created_time'] = pd.to_datetime(df['created_time'], errors='coerce')
        df['created_date'] = df['created_time'].dt.date
        min_date = df['created_date'].min()
        max_date = df['created_date'].max()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date, key="start_date_picker_dash")
        with col2:
            end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date, key="end_date_picker_dash")

        st.markdown(f"🗓️ **Selected Range:** `{start_date.strftime('%d/%m/%Y')}` → `{end_date.strftime('%d/%m/%Y')}`")

        reset_filter = st.button("🔁 Reset to Default", key="reset_button_1")

        if reset_filter:
            df_filtered = df.copy()
            st.info("Showing all available data (no date filter applied).")
        elif start_date > end_date:
            st.warning("⚠️ Start date is after end date. Please select a valid range.")
            return
        else:
            df_filtered = df[(df['created_date'] >= start_date) & (df['created_date'] <= end_date)]
    else:
        df_filtered = df.copy()

    # --- KPI Cards ---
    st.markdown("### 🔹 Key Metrics")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Tickets", f"{len(df_filtered):,}")
    kpi2.metric("Avg Resolution Time (hrs)", f"{df_filtered['resolution_time'].mean():.2f}")
    kpi3.metric("Unique Departments", df_filtered['department'].nunique() if 'department' in df.columns else "N/A")
    st.markdown("---")

    # --- Row 1: Technicians + Departments ---
    st.markdown("### 🎯 Performance by Role & Department")
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        if 'technician' in df_filtered.columns:
            tech_counts = df_filtered['technician'].value_counts().head(10).reset_index()
            tech_counts.columns = ['Technician', 'count']
            fig = px.bar(tech_counts, x='Technician', y='count', title="Top 10 Technicians", color='count', color_continuous_scale='Blues')
            fig.update_layout(xaxis_title="Technician", yaxis_title="Ticket Count")
            st.plotly_chart(fig, use_container_width=True, key="top_techs_dashboard")

    with row1_col2:
        if 'department' in df_filtered.columns:
            dept_counts = df_filtered['department'].value_counts().head(10).reset_index()
            dept_counts.columns = ['Department', 'count']
            fig = px.bar(dept_counts, x='count', y='Department', orientation='h', title="Top 10 Departments", color='count', color_continuous_scale='Blues')
            fig.update_layout(xaxis_title="Ticket Count", yaxis_title="Department")
            st.plotly_chart(fig, use_container_width=True, key="top_departments_dashboard")

    # --- Row 2: Time Analysis ---
    st.markdown("### ⏳ Resolution Time Analysis")
    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        if 'priority' in df_filtered.columns and 'resolution_time' in df_filtered.columns:
            fig = px.box(df_filtered, x='priority', y='resolution_time', title="Resolution Time by Priority", color_discrete_sequence=['#1f77b4'])
            fig.update_layout(xaxis_title="Priority", yaxis_title="Resolution Time (hrs)")
            st.plotly_chart(fig, use_container_width=True, key="resolution_time_priority")

    with row2_col2:
        if 'resolution_time' in df_filtered.columns:
            fig = px.histogram(df_filtered, x='resolution_time', nbins=30, marginal="box", title="Resolution Time Distribution", color_discrete_sequence=['#1f77b4'])
            fig.update_layout(xaxis_title="Resolution Time (hrs)", yaxis_title="Ticket Count")
            st.plotly_chart(fig, use_container_width=True, key="resolution_time_distribution")

    # --- Row 3: Category and Site ---
    st.markdown("### 🗂️ Category and Site Trends")
    row3_col1, row3_col2 = st.columns(2)
    with row3_col1:
        if 'category' in df_filtered.columns:
            cat_counts = df_filtered['category'].value_counts().reset_index()
            cat_counts.columns = ['Category', 'count']
            fig = px.bar(cat_counts, x='count', y='Category', orientation='h', title="Tickets by Category", color='count', color_continuous_scale='Blues')
            fig.update_layout(xaxis_title="Ticket Count", yaxis_title="Category")
            st.plotly_chart(fig, use_container_width=True, key="tickets_by_category")

    with row3_col2:
        if 'site' in df_filtered.columns:
            site_counts = df_filtered['site'].value_counts().head(10).reset_index()
            site_counts.columns = ['Site', 'count']
            fig = px.bar(site_counts, x='Site', y='count', title="Top Sites by Ticket Volume", color='count', color_continuous_scale='Blues')
            fig.update_layout(xaxis_title="Site", yaxis_title="Ticket Count")
            st.plotly_chart(fig, use_container_width=True, key="top_sites")

    # --- Row 4: Time Trends ---
    st.markdown("### 🕒 Time-Based Trends")
    row4_col1, row4_col2 = st.columns(2)
    with row4_col1:
        if 'created_time' in df_filtered.columns:
            df_filtered['created_time'] = pd.to_datetime(df_filtered['created_time'], errors='coerce')
            df_filtered['created_month'] = df_filtered['created_time'].dt.to_period("M").dt.to_timestamp()
            monthly = df_filtered.groupby('created_month').size().reset_index(name='count')
            fig = px.line(monthly, x='created_month', y='count', markers=True, title="Monthly Ticket Volume")
            fig.update_layout(
                xaxis_title="Created Month",
                yaxis_title="Ticket Count",
                xaxis=dict(tickformat="%Y-%m-%d", dtick="M1")
            )
            st.plotly_chart(fig, use_container_width=True, key="monthly_ticket_volume")

    with row4_col2:
        if 'created_time' in df_filtered.columns:
            df_filtered['created_hour'] = df_filtered['created_time'].dt.hour
            hour_counts = df_filtered['created_hour'].value_counts().sort_index().reset_index()
            hour_counts.columns = ['Hour', 'Count']
            fig = px.bar(hour_counts, x='Hour', y='Count', title="Tickets by Hour of Day", color='Count', color_continuous_scale='Blues')
            fig.update_layout(xaxis_title="Hour of Day", yaxis_title="Ticket Count")
            st.plotly_chart(fig, use_container_width=True, key="ticket_hours")

    # --- Row 5: Priority Overview ---
    if 'priority' in df_filtered.columns:
        st.markdown("### ⚠️ Priority Distribution")
        pri_counts = df_filtered['priority'].value_counts().reset_index()
        pri_counts.columns = ['Priority', 'Count']
        fig = px.bar(pri_counts, x='Priority', y='Count', title="Tickets by Priority", color='Count', color_continuous_scale='Blues')
        fig.update_layout(xaxis_title="Priority", yaxis_title="Ticket Count")
        st.plotly_chart(fig, use_container_width=True, key="dashboard")

    return df_filtered