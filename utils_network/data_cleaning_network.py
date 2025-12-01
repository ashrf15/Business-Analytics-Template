import pandas as pd
import streamlit as st

def data_cleaning_network(df, uploaded_file):
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

    # ✅ Normalize column names
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Convert dates
    for col in ["timestamp","firmware_update"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Normalize boolean-like columns
    def _to_bool(x):
        if pd.isna(x): return pd.NA
        s = str(x).strip().lower()
        if s in {"true","yes","y","1"}: return True
        if s in {"false","no","n","0"}: return False
        return pd.NA

    for bcol in ["config_change","qos_policy_violation"]:
        if bcol in df.columns:
            df[bcol] = df[bcol].map(_to_bool)

    # Drop very sparse columns
    df = df.loc[:, df.isnull().mean() <= 0.5]

    st.subheader("🧼 After Cleaning Overview")
    st.write(f"**Number of Rows:** {df.shape[0]}")
    st.write(f"**Number of Columns:** {df.shape[1]}")
    st.write("**Missing Values:**")
    st.write(df.isnull().sum())
    st.dataframe(df.head())

    # Compare raw vs cleaned
    st.subheader("🔍 Compare Full Raw vs Cleaned Data")
    view_option = st.radio("Select which data to view:", ("Raw Data","Cleaned Data"), horizontal=True)
    with st.expander("🔎 Click to view full table"):
        if view_option == "Raw Data" and uploaded_file is not None:
            uploaded_file.seek(0)
            if uploaded_file.name.endswith((".xlsx",".xls")):
                raw_df = pd.read_excel(uploaded_file, engine="openpyxl")
            else:
                raw_df = pd.read_csv(uploaded_file)
            st.dataframe(raw_df)
        else:
            st.dataframe(df)

    return df
