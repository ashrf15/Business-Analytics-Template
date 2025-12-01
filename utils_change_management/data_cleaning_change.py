import pandas as pd
import streamlit as st

def data_cleaning_change(df, uploaded_file):
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

    
    # --- Convert date and duration fields ---
    for col in ['implemented_date', 'approval_date', 'request_date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    for col in ['approval_duration', 'implementation_duration']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- Clean boolean-like columns ---
    bool_cols = ['emergency_flag', 'success', 'window_compliance']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().map({
                'true': True, 'false': False, 'yes': True, 'no': False
            })

    # --- Add Month column ---
    if 'implemented_date' in df.columns:
        df['month'] = df['implemented_date'].dt.to_period('M')

    # --- Drop columns with too many missing values ---
    df = df.loc[:, df.isnull().mean() <= 0.5]

    # --- Compute derived KPIs ---
    if 'implemented_date' in df.columns and 'approval_date' in df.columns:
        df['approval_lead_time'] = (df['implemented_date'] - df['approval_date']).dt.total_seconds() / 86400

    if 'implemented_date' in df.columns and 'request_date' in df.columns:
        df['total_change_lead_time'] = (df['implemented_date'] - df['request_date']).dt.total_seconds() / 86400

    # --- Post-cleaning Summary ---
    st.subheader("🧼 After Cleaning Overview")
    st.write(f"**Number of Rows:** {df.shape[0]}")
    st.write(f"**Number of Columns:** {df.shape[1]}")
    st.write("**Missing Values:**")
    st.write(df.isnull().sum())
    st.write("**Sample Cleaned Data:**")
    st.dataframe(df.head())

    # --- Compare Raw vs Cleaned Data ---
    st.subheader("🔍 Compare Full Raw vs Cleaned Data")
    view_option = st.radio("Select which data to view:", ("Raw Data", "Cleaned Data"), horizontal=True)

    with st.expander("🔎 Click to view full table"):
        if view_option == "Raw Data":
            file_name = uploaded_file.name.lower() if hasattr(uploaded_file, "name") else ""
            try:
                if file_name.endswith(".csv"):
                    raw_df = pd.read_csv(uploaded_file)
                elif file_name.endswith((".xlsx", ".xls")):
                    raw_df = pd.read_excel(uploaded_file, engine="openpyxl")
                else:
                    st.error("❌ Unsupported file format. Please upload CSV or Excel.")
                    raw_df = None
                if raw_df is not None:
                    st.markdown("### 🗃️ Raw Data (Full Table)")
                    st.dataframe(raw_df)
            except Exception as e:
                st.error(f"⚠️ Could not read raw file: {e}")
        else:
            st.markdown("### 🧼 Cleaned Data (Full Table)")
            st.dataframe(df)

    return df
