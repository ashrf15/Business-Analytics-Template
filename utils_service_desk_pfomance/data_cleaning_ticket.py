import pandas as pd
import streamlit as st
import io
import re

# --------- helpers ---------
def to_snake(name: str) -> str:
    s = str(name).strip()
    s = s.replace("-", " ").replace("/", " ")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s]", "", s)
    s = s.replace(" ", "_").lower()
    return s

def arrow_sanitize_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        s = out[col]
        if pd.api.types.is_object_dtype(s):
            mask_bad = s.map(lambda x: isinstance(x, (list, dict, tuple, set)))
            if mask_bad.any():
                out.loc[mask_bad, col] = s[mask_bad].map(str)
            try:
                ntypes = s.map(lambda x: type(x).__name__).nunique()
            except Exception:
                ntypes = 2
            if ntypes > 1:
                out[col] = s.astype("string")
        elif str(s.dtype) == "Int64":
            out[col] = s.astype("float64")
        elif pd.api.types.is_datetime64_any_dtype(s):
            out[col] = pd.to_datetime(s, errors="coerce").dt.tz_localize(None)
        elif pd.api.types.is_categorical_dtype(s):
            out[col] = s.astype("string")
    return out

def _dtype_table(df: pd.DataFrame, title: str) -> pd.DataFrame:
    return pd.DataFrame({"Column": df.columns, title: [str(t) for t in df.dtypes.values]})

# --------- main cleaning pipeline ---------
def data_cleaning_ticket(df, uploaded_file):
    # keep a RAW snapshot (exactly as uploaded)
    raw_df_snapshot = df.copy(deep=True)

    st.success("✅ File successfully loaded!")

    # ==============================
    # i. BEFORE CLEANING
    # ==============================
    st.subheader("🔍 Before Cleaning")

    col1, col2 = st.columns(2)
    col1.metric("Rows (Raw)", raw_df_snapshot.shape[0])
    col2.metric("Columns (Raw)", raw_df_snapshot.shape[1])

    total_missing_raw = int(raw_df_snapshot.isnull().sum().sum())
    m1, _m2 = st.columns(2)
    m1.metric("Total Missing Values (Raw)", total_missing_raw)

    st.markdown("**Data Types (Raw)**")
    st.dataframe(_dtype_table(raw_df_snapshot, "Raw dtypes"), use_container_width=True)

    col_mv, _ = st.columns([3, 1])
    with col_mv:
        st.markdown("**Missing Values by Column (Raw)**")
        st.dataframe(
            raw_df_snapshot.isnull().sum().reset_index().rename(columns={"index": "Column", 0: "Missing"}),
            use_container_width=True
        )

    dup_count_raw = int(raw_df_snapshot.duplicated().sum())
    st.write(f"**Duplicated Rows (Raw):** {dup_count_raw}")
    if dup_count_raw > 0:
        st.dataframe(raw_df_snapshot[raw_df_snapshot.duplicated()], use_container_width=True)

    raw_datetime_cols = [c for c in raw_df_snapshot.columns if pd.api.types.is_datetime64_any_dtype(raw_df_snapshot[c])]
    st.write("**Datetime Columns Detected (Raw):** " + (", ".join(raw_datetime_cols) if raw_datetime_cols else "None"))

    st.markdown("**Sample Data (Raw):**")
    st.dataframe(raw_df_snapshot.head(), use_container_width=True)

    # =================================================
    # CLEANING LOGIC (with column standardization)
    # =================================================
    df = df.copy()

    # Normalize column names (raw->snake map)
    orig_cols = list(df.columns)
    norm_cols = [to_snake(c) for c in orig_cols]
    col_map = dict(zip(orig_cols, norm_cols))
    df.columns = norm_cols

    example_pair = next(((o, n) for o, n in col_map.items() if o != n), None)
    if example_pair:
        o, n = example_pair
        st.info(f"Column names standardized to **snake_case** (example: “{o}” → “{n}”).")

    # Durations (SLA)
    for col in ['sla_resolution_time', 'sla_response_time', 'on_hold_duration']:
        if col in df.columns:
            df[col] = pd.to_timedelta(df[col], errors='coerce')

    # Datetimes
    for col in ['created_time', 'resolved_time']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)

    # Response durations
    for col in ['response_time_elapsed', 'time_elapsed']:
        if col in df.columns:
            df[col] = pd.to_timedelta(df[col], errors='coerce')

    # Boolean-like
    bool_cols = ['fcr', 'vip_user', 'reopened', 'first_response_overdue_status', 'overdue_status']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().map({'true': True, 'false': False, 'yes': True, 'no': False})

    # Month
    if 'created_time' in df.columns:
        df['month'] = df['created_time'].dt.to_period('M')

    # Drop >50% missing
    missing_ratio = df.isnull().mean()
    dropped_cols = missing_ratio[missing_ratio > 0.5].index.tolist()
    df = df.loc[:, missing_ratio <= 0.5]

    # request_status + resolved_time
    if 'request_status' in df.columns:
        df['request_status'] = df['request_status'].astype(str).str.strip().str.lower()
        if 'resolved_time' in df.columns:
            df['resolved_time'] = pd.to_datetime(df['resolved_time'], errors='coerce')
            df.loc[(df['request_status'] == 'onhold') & (df['resolved_time'].isna()), 'resolved_time'] = pd.NaT

    # resolution_time (hours)
    if 'created_time' in df.columns and 'resolved_time' in df.columns:
        df['resolution_time'] = (df['resolved_time'] - df['created_time']).dt.total_seconds() / 3600

    # ==============================
    # ii. AFTER CLEANING
    # ==============================
    st.subheader("🧼 After Cleaning Overview")

    ac1, ac2 = st.columns(2)
    ac1.metric("Rows (Cleaned)", df.shape[0])
    ac2.metric("Columns (Cleaned)", df.shape[1])

    total_missing_clean = int(df.isnull().sum().sum())
    cm1, _cm2 = st.columns(2)
    cm1.metric("Total Missing Values (Cleaned)", total_missing_clean)

    st.markdown("**Data Types (Cleaned)**")
    st.dataframe(_dtype_table(df, "Cleaned dtypes"), use_container_width=True)

    st.markdown("**Missing Values by Column (Cleaned)**")
    st.dataframe(
        df.isnull().sum().reset_index().rename(columns={"index": "Column", 0: "Missing"}),
        use_container_width=True
    )

    st.write("**Dropped Columns (>50% Missing):** " + (", ".join(dropped_cols) if dropped_cols else "None"))

    cleaned_datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    st.write("**Datetime Columns Detected (Cleaned):** " + (", ".join(cleaned_datetime_cols) if cleaned_datetime_cols else "None"))

    st.markdown("**Sample Cleaned Data:**")
    st.dataframe(df.head(), use_container_width=True)

    # ==============================
    # iii. COMPARE RAW DATA VS CLEANED DATA
    # ==============================
    st.subheader("🔍 Compare Raw Data vs Cleaned Data")

    dtypes_raw = _dtype_table(raw_df_snapshot, "Raw dtypes")
    dtypes_clean = _dtype_table(df, "Cleaned dtypes")

    dtypes_raw["Column (standardized)"] = dtypes_raw["Column"].map(col_map)
    dtypes_clean = dtypes_clean.rename(columns={"Column": "Column (standardized)"})

    dtype_compare = dtypes_raw.merge(dtypes_clean, on="Column (standardized)", how="outer")
    dtype_compare = dtype_compare.rename(columns={"Column": "Raw Column"})
    dropped_mask = dtype_compare["Cleaned dtypes"].isna() & dtype_compare["Raw dtypes"].notna()
    dtype_compare.loc[dropped_mask, "Cleaned dtypes"] = "dropped"
    dtype_compare = dtype_compare[["Raw Column", "Column (standardized)", "Raw dtypes", "Cleaned dtypes"]].fillna("—")

    st.markdown("**Data Types (Aligned by Standardized Name)**")
    st.dataframe(dtype_compare, use_container_width=True)

    st.markdown("**Sample – Raw Data**")
    st.dataframe(raw_df_snapshot.head(), use_container_width=True)
    st.markdown("**Sample – Cleaned Data**")
    st.dataframe(df.head(), use_container_width=True)

    # ==============================
    # iv. EXPORT RAW AND CLEANED DATASET
    # ==============================
    st.subheader("📤 Export Raw and Cleaned Datasets")

    raw_csv = raw_df_snapshot.to_csv(index=False).encode("utf-8")
    clean_csv = df.to_csv(index=False).encode("utf-8")
    exp1, exp2 = st.columns(2)
    exp1.download_button("⬇️ Download RAW as CSV", raw_csv, file_name="tickets_raw.csv", mime="text/csv")
    exp2.download_button("⬇️ Download CLEANED as CSV", clean_csv, file_name="tickets_cleaned.csv", mime="text/csv")

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        raw_df_snapshot.to_excel(xw, index=False, sheet_name="Raw")
        df.to_excel(xw, index=False, sheet_name="Cleaned")
    st.download_button(
        "⬇️ Download RAW+CLEANED Excel (2 sheets)",
        data=buf.getvalue(),
        file_name="tickets_raw_cleaned.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ==============================
    # (Full-table viewer) — NO re-read of uploaded_file
    # ==============================
    with st.expander("🔎 Click to view full table"):
        view_option = st.radio("Select which data to view:", ("Raw Data", "Cleaned Data"), horizontal=True)

        # Use the in-memory snapshots you already have to avoid _UploadedShim issues
        if view_option == "Raw Data":
            st.markdown("### 🗃️ Raw Data (Full Table)")
            st.dataframe(raw_df_snapshot, use_container_width=True)
        else:
            st.markdown("### 🧼 Cleaned Data (Full Table)")
            st.dataframe(df, use_container_width=True)

    return df
