import pandas as pd
import streamlit as st

def data_cleaning(df, uploaded_file):
        st.success("✅ File successfully loaded!")
        st.subheader("🔍 Before Cleaning")
        col1, col2 = st.columns(2)
        col1.metric("Number of Rows", df.shape[0])
        col2.metric("Number of Columns", df.shape[1])
         
        st.write("**Column Data Types:**")
        st.write(df.dtypes)
        st.write("**Missing Values:**")
        st.write(df.isnull().sum())
        st.write("**Sample Data:**")
        st.dataframe(df.head())

        duplicate_rows = df[df.duplicated()]
        st.write(f"🔁 **Duplicate Rows Found:** {duplicate_rows.shape[0]}")
        if not duplicate_rows.empty:
            st.dataframe(duplicate_rows)

        for col in ['SLA resolution time', 'SLA response time', 'On Hold Duration']:
            if col in df.columns:
                df[col] = pd.to_timedelta(df[col], errors='coerce')

        for col in ['Created Time', 'Resolved Time']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)

        for col in ['Response time elapsed', 'Time Elapsed']:
            if col in df.columns:
                df[col] = pd.to_timedelta(df[col], errors='coerce')

        bool_cols = ['FCR', 'VIP User', 'ReOpened', 'First Response Overdue Status', 'Overdue Status']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.lower().map({'true': True, 'false': False, 'yes': True, 'no': False})

        if 'Created Time' in df.columns:
            df['Month'] = df['Created Time'].dt.to_period('M')

        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
        df = df.loc[:, df.isnull().mean() <= 0.5]

        if 'request_status' in df.columns:
            df['request_status'] = df['request_status'].astype(str).str.strip().str.lower()
            df['resolved_time'] = pd.to_datetime(df['resolved_time'], errors='coerce')
            df.loc[(df['request_status'] == 'onhold') & (df['resolved_time'].isna()), 'resolved_time'] = pd.NaT

        df['created_time'] = pd.to_datetime(df['created_time'], errors='coerce')
        df['resolved_time'] = pd.to_datetime(df['resolved_time'], errors='coerce')
        df['resolution_time'] = (df['resolved_time'] - df['created_time']).dt.total_seconds() / 3600

        st.subheader("🧼 After Cleaning Overview")
        st.write(f"**Number of Rows:** {df.shape[0]}")
        st.write(f"**Number of Columns:** {df.shape[1]}")
        st.write("**Missing Values:**")
        st.write(df.isnull().sum())
        st.write("**Sample Cleaned Data:**")
        st.dataframe(df.head())

        st.subheader("🔍 Compare Full Raw vs Cleaned Data")

        view_option = st.radio("Select which data to view:", ("Raw Data", "Cleaned Data"), horizontal=True)

        with st.expander("🔎 Click to view full table"):
            if view_option == "Raw Data":
                raw_df = pd.read_excel(uploaded_file, engine='openpyxl')
                st.markdown("### 🗃️ Raw Data (Full Table)")
                st.dataframe(raw_df)
            else:
                st.markdown("### 🧼 Cleaned Data (Full Table)")
                st.dataframe(df)

        return df
