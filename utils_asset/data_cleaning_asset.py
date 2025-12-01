import pandas as pd
import streamlit as st
import io
import re
import numpy as np

# --------- helpers ---------
def to_snake(name: str) -> str:
    """
    Robust snake_case normalizer:
      - trim, collapse whitespace to underscores
      - swap hyphens & slashes to spaces first
      - remove non-word chars except underscores
      - lowercase
    """
    s = str(name).strip()
    s = s.replace("-", " ").replace("/", " ")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s]", "", s)           # drop punctuation
    s = s.replace(" ", "_").lower()
    return s

def arrow_sanitize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make df safe for Streamlit's Arrow bridge:
      - Mixed-type object cols -> string
      - Lists/dicts/tuples in cells -> string
      - Pandas nullable Int64 -> float64 (preserve NaN)
      - datetimes -> naive datetime64[ns]
      - categoricals -> string
    """
    out = df.copy()

    for col in out.columns:
        s = out[col]

        # 1) object columns with exotic values
        if pd.api.types.is_object_dtype(s):
            # turn list/dict/tuple/set into strings
            mask_bad = s.map(lambda x: isinstance(x, (list, dict, tuple, set)))
            if mask_bad.any():
                out.loc[mask_bad, col] = s[mask_bad].map(str)

            # if still mixed types (e.g., numbers + strings), stringify
            try:
                ntypes = s.map(lambda x: type(x).__name__).nunique()
            except Exception:
                ntypes = 2  # be conservative
            if ntypes > 1:
                out[col] = s.astype("string")

        # 2) pandas nullable integer dtype -> float64 (Arrow sometimes chokes)
        elif str(s.dtype) == "Int64":
            out[col] = s.astype("float64")

        # 3) datetimes -> ensure timezone-naive
        elif pd.api.types.is_datetime64_any_dtype(s):
            out[col] = pd.to_datetime(s, errors="coerce").dt.tz_localize(None)

        # 4) categoricals -> string
        elif pd.api.types.is_categorical_dtype(s):
            out[col] = s.astype("string")

    return out

def _dtype_table(df: pd.DataFrame, title: str) -> pd.DataFrame:
    return pd.DataFrame({
        "Column": df.columns,
        title: [str(t) for t in df.dtypes.values]
    })

# --------- asset type classifier ---------
HARDWARE_EXACT = {
    "adapter","all in one","analog tel adapter","apple tv","audio matrix switch","battery accumulator",
    "battery notebook","bluetooth headset","cable lock","cartridge","clicker","compact access","cordless phone",
    "data tape","desktop","desktop switch","display adapter","displayport adapter","displayport to vga adapter",
    "docking station","dot matrix printer","dvd drive","ext dvdrw drive","external dvd drive","external dvd writer",
    "external hdd","fast ethernet converter","fax ink film","hdd","hdmi cable","hdmi ext","hdmi splitter",
    "hdmi to vga adapter","hdmi transmittter","headset deck","hp usb-c to vga adapter","ink film","ip conference",
    "ip pbx","ip phone","ipad","keyboard","lan adapter","lan modem","media converter","mfom","microphone speaker",
    "mobile phone","monitor","mouse","network cable tester","notebook","notebook fan","notebook hdd","phone",
    "plasma tv","poe dc power","poe midspan","port replicator","power adapter","power injector","print server",
    "printer","projector","pvdm card","smart adapter dongle converter","sound blaster","sound station","speaker",
    "speakerphone","storageworks","stylus pen","tape library","tape loader","tv","universal module",
    "usb 2.0 to ide & sata","usb card reader","usb extender","usb to hdmi converter","vc equipment","vga cable",
    "vga splitter","vga to hdmi converter","vid conv","wap","webcam","wireless dual band usb adapter",
    "wireless headset","wireless hub","wireless n usb adapter",
    # common variants
    "laptop","pc","workstation","server","thin client","tablet","smartphone","switch","router","access point",
    "ups","ssd","nvme","ram","memory","gpu","graphics card","motherboard","chassis"
}

HARDWARE_KEYWORDS = {
    "desktop","laptop","notebook","pc","workstation","monitor","printer","projector","scanner","router","switch",
    "firewall","access point","wap","server","rack","blade","hdd","ssd","nvme","storage","nas","san","keyboard",
    "mouse","webcam","headset","dock","docking","adapter","cable","splitter","converter","tv","display","ipad",
    "tablet","phone","ip phone","mobile","smartphone","ups","gpu","graphics","motherboard","ram","memory","chassis"
}

SOFTWARE_KEYWORDS = {
    "software","license","licence","subscription","windows","microsoft 365","office","o365","antivirus","anti-virus",
    "antimalware","endpoint security","defender","crowdstrike","bitdefender","kaspersky","adobe","acrobat","photoshop",
    "autocad","sap","oracle","sql","database","vpn client","vpn","agent","client","driver","os","operating system",
    "jamf","intune","sccm","bigfix","patch","update","application","app","suite","ide","python","r","matlab","stata"
}

ASSET_TYPE_OVERRIDES = {
    # "ms office pro plus": "software",
    # "thin client": "hardware",
}

def _normalize_text(x):
    if pd.isna(x):
        return ""
    return re.sub(r"\s+", " ", str(x).strip().lower())

def _keyword_hit(name: str, keywords: set) -> bool:
    name_l = f" {name} "
    for kw in keywords:
        if f" {kw} " in name_l:
            return True
    return False

def classify_type_from_name(raw_name: str):
    """
    Returns tuple: (category, confidence, rule)
    """
    name = _normalize_text(raw_name)

    if name in ASSET_TYPE_OVERRIDES:
        return ASSET_TYPE_OVERRIDES[name], 1.0, "override"
    if name in HARDWARE_EXACT:
        return "hardware", 1.0, "exact-hw"

    hw = _keyword_hit(name, HARDWARE_KEYWORDS)
    sw = _keyword_hit(name, SOFTWARE_KEYWORDS)

    if hw and not sw:
        return "hardware", 0.8, "kw-hw"
    if sw and not hw:
        return "software", 0.8, "kw-sw"
    if hw and sw:
        if any(tok in name for tok in ["license","licence","subscription","installer","client","agent","driver","os"]):
            return "software", 0.6, "kw-both-tilt-sw"
        return "hardware", 0.6, "kw-both-tilt-hw"
    if any(tok in name for tok in ["device","unit","equipment","module","card","board"]):
        return "hardware", 0.6, "fallback-generic-hw"
    return "unknown", 0.0, "no-signal"

# --------- main cleaning pipeline ---------
def data_cleaning_asset(df, uploaded_file):
    # keep a RAW snapshot (exactly as uploaded)
    raw_df_snapshot = df.copy(deep=True)

    st.success("✅ File successfully loaded!")

    # ==============================
    # i. BEFORE CLEANING
    # ==============================
    st.subheader("🔍 Before Cleaning")

    # a) number of rows and columns
    col1, col2 = st.columns(2)
    col1.metric("Rows (Raw)", raw_df_snapshot.shape[0])
    col2.metric("Columns (Raw)", raw_df_snapshot.shape[1])

    # b) total missing values
    total_missing_raw = int(raw_df_snapshot.isnull().sum().sum())
    m1, _m2 = st.columns(2)
    m1.metric("Total Missing Values (Raw)", total_missing_raw)

    # c) data types
    st.markdown("**Data Types (Raw)**")
    st.dataframe(_dtype_table(raw_df_snapshot, "Raw dtypes"), use_container_width=True)

    # d) missing value table
    col_mv, _ = st.columns([3, 1])
    with col_mv:
        st.markdown("**Missing Values by Column (Raw)**")
        st.dataframe(
            raw_df_snapshot.isnull().sum().reset_index().rename(columns={"index": "Column", 0: "Missing"}),
            use_container_width=True
        )

    # e) duplicated rows
    dup_count_raw = int(raw_df_snapshot.duplicated().sum())
    st.write(f"**Duplicated Rows (Raw):** {dup_count_raw}")
    if dup_count_raw > 0:
        st.dataframe(raw_df_snapshot[raw_df_snapshot.duplicated()], use_container_width=True)

    # f) datetime columns (raw)
    raw_datetime_cols = [c for c in raw_df_snapshot.columns if pd.api.types.is_datetime64_any_dtype(raw_df_snapshot[c])]
    st.write("**Datetime Columns Detected (Raw):** " + (", ".join(raw_datetime_cols) if raw_datetime_cols else "None"))

    # g) sample data
    st.markdown("**Sample Data (Raw):**")
    st.dataframe(raw_df_snapshot.head(), use_container_width=True)

    # =================================================
    # CLEANING LOGIC (with column standardization)
    # =================================================
    df = df.copy()

    # ✅ Normalize column names first (and build a mapping raw->snake)
    orig_cols = list(df.columns)
    norm_cols = [to_snake(c) for c in orig_cols]
    col_map = dict(zip(orig_cols, norm_cols))
    df.columns = norm_cols

    # Notify user with ONE example of the standardization (only if any change occurred)
    example_pair = next(((o, n) for o, n in col_map.items() if o != n), None)
    if example_pair:
        o, n = example_pair
        st.info(f"Column names standardized to **snake_case** (example: “{o}” → “{n}”).")

    # --- Clean placeholder values (replace with NaN) ---
    invalid_placeholders = ['#N/A', 'N/A', 'n/a', 'NA', 'na', 'null', 'NULL', '########', '#####', '', ' ', '#VALUE!']
    df.replace(invalid_placeholders, np.nan, inplace=True)

    # --- Known datetime columns (post-normalization) ---
    dt_candidates = [
        'last_startup', 'last_shutdown', 'agent_installation', 'agent_upgrade',
        'last_virus_scan_manual_', 'last_virus_scan_scheduled_',
        'last_spyware_scan_manual_', 'last_spyware_scan_scheduled_'
    ]
    existing_dt_cols = [c for c in dt_candidates if c in df.columns]
    for col in existing_dt_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # --- Drop columns with >60% missing values (track dropped list) ---
    missing_ratio = df.isnull().mean()
    dropped_cols = missing_ratio[missing_ratio > 0.6].index.tolist()
    df = df.loc[:, missing_ratio <= 0.6]
    st.write("**Dropped Columns (>60% Missing):** " + (", ".join(dropped_cols) if dropped_cols else "None"))

    # --- Derived & normalization logic ---
    if 'vlookup_username' in df.columns:
        df.drop('vlookup_username', axis=1, inplace=True)

    # numeric coercion where it makes sense (keep if >60% become numeric)
    object_cols = df.select_dtypes(include='object').columns
    for col in object_cols:
        try:
            converted = pd.to_numeric(df[col], errors='coerce')
            if converted.notnull().sum() > len(df) * 0.6:
                df[col] = converted
        except Exception:
            pass

    if 'connection_status' in df.columns:
        df['is_online'] = df['connection_status'].astype(str).str.lower().map({'online': True, 'offline': False})

    if {'virus_malware', 'spyware_grayware'}.issubset(df.columns):
        df['has_malware'] = df[['virus_malware', 'spyware_grayware']].fillna(0).sum(axis=1).astype(bool)

    if 'logon_user' in df.columns:
        df[['user_domain', 'username']] = df['logon_user'].astype(str).str.extract(r'(.*)\\(.*)')

    if 'last_startup' in df.columns:
        df['last_seen'] = df['last_startup']

    # --- Hardware / Software classification from `type` column ---
    if "type" in df.columns:
        type_norm = df["type"].astype(str).str.strip()
        out = type_norm.apply(classify_type_from_name)
        df["categories"] = out.apply(lambda t: t[0])
        df["cat_confidence"] = out.apply(lambda t: t[1])
        df["cat_rule"] = out.apply(lambda t: t[2])
        df["asset_label"] = (
            df["categories"]
            .map({"hardware": "Hardware Asset", "software": "Software Asset"})
            .fillna("Unknown Asset")
            .mask(df["categories"] == "unknown", "Unknown Asset")
        )

        st.subheader("🏷️ Asset Label Summary")
        c1, c2, c3 = st.columns(3)
        c1.metric("Hardware Asset", int((df["asset_label"] == "Hardware Asset").sum()))
        c2.metric("Software Asset", int((df["asset_label"] == "Software Asset").sum()))
        c3.metric("Unknown Asset", int((df["asset_label"] == "Unknown Asset").sum()))

        with st.expander("🔎 Review Unknown / Low-Confidence Classifications"):
            review_df = (
                df.loc[(df["categories"] == "unknown") | (df["cat_confidence"] < 0.8),
                       ["type", "categories", "cat_confidence", "cat_rule"]]
                .sort_values(["categories","cat_confidence"], ascending=[True, True])
                .head(200)
            )
            st.caption("Top 200 items that may need override/mapping.")
            st.dataframe(review_df, use_container_width=True)

        st.info(
            "Classification uses curated exact matches, domain keywords, and tie-breakers. "
            "Add tricky labels to ASSET_TYPE_OVERRIDES to lock them without touching raw data."
        )
    else:
        st.warning("`type` column not found after standardization — asset classification skipped.")

    # ==============================
    # ii. AFTER CLEANING
    # ==============================
    st.subheader("🧼 After Cleaning Overview")

    # a) number of rows and columns
    ac1, ac2 = st.columns(2)
    ac1.metric("Rows (Cleaned)", df.shape[0])
    ac2.metric("Columns (Cleaned)", df.shape[1])

    # b) total missing value
    total_missing_clean = int(df.isnull().sum().sum())
    cm1, _cm2 = st.columns(2)
    cm1.metric("Total Missing Values (Cleaned)", total_missing_clean)

    # c) data types
    st.markdown("**Data Types (Cleaned)**")
    st.dataframe(_dtype_table(df, "Cleaned dtypes"), use_container_width=True)

    # d) missing value table
    st.markdown("**Missing Values by Column (Cleaned)**")
    st.dataframe(
        df.isnull().sum().reset_index().rename(columns={"index": "Column", 0: "Missing"}),
        use_container_width=True
    )

    # e) datetime columns after parsing
    cleaned_datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    st.write("**Datetime Columns Detected (Cleaned):** " + (", ".join(cleaned_datetime_cols) if cleaned_datetime_cols else "None"))

    # g) sample data
    st.markdown("**Sample Cleaned Data:**")
    st.dataframe(df.head(), use_container_width=True)

    # ==============================
    # iii. COMPARE RAW DATA VS CLEANED DATA (fixed alignment)
    # ==============================
    st.subheader("🔍 Compare Raw Data vs Cleaned Data")

    # Build dtype tables
    dtypes_raw = _dtype_table(raw_df_snapshot, "Raw dtypes")
    dtypes_clean = _dtype_table(df, "Cleaned dtypes")

    # Add a normalized key for raw columns so they align with cleaned
    dtypes_raw["Column (standardized)"] = dtypes_raw["Column"].map(col_map)
    dtypes_clean = dtypes_clean.rename(columns={"Column": "Column (standardized)"})

    # Merge on the standardized column name
    dtype_compare = dtypes_raw.merge(dtypes_clean, on="Column (standardized)", how="outer")
    dtype_compare = dtype_compare.rename(columns={"Column": "Raw Column"})
    # mark dropped columns in comparison
    dropped_mask = dtype_compare["Cleaned dtypes"].isna() & dtype_compare["Raw dtypes"].notna()
    dtype_compare.loc[dropped_mask, "Cleaned dtypes"] = "dropped"
    # Reorder for readability
    dtype_compare = dtype_compare[["Raw Column", "Column (standardized)", "Raw dtypes", "Cleaned dtypes"]].fillna("—")

    st.markdown("**Data Types (Aligned by Standardized Name)**")
    st.dataframe(dtype_compare, use_container_width=True)

    # b) sample data — STACKED (Raw on top, Cleaned below)
    st.markdown("**Sample – Raw Data**")
    st.dataframe(raw_df_snapshot.head(), use_container_width=True)
    st.markdown("**Sample – Cleaned Data**")
    st.dataframe(df.head(), use_container_width=True)

    # ==============================
    # iv. EXPORT RAW AND CLEANED DATASET
    # ==============================
    st.subheader("📤 Export Raw and Cleaned Datasets")

    # CSV exports
    raw_csv = raw_df_snapshot.to_csv(index=False).encode("utf-8")
    clean_csv = df.to_csv(index=False).encode("utf-8")
    exp1, exp2 = st.columns(2)
    exp1.download_button("⬇️ Download RAW as CSV", raw_csv, file_name="asset_raw.csv", mime="text/csv")
    exp2.download_button("⬇️ Download CLEANED as CSV", clean_csv, file_name="asset_cleaned.csv", mime="text/csv")

    # Excel with two sheets
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        raw_df_snapshot.to_excel(xw, index=False, sheet_name="Raw")
        df.to_excel(xw, index=False, sheet_name="Cleaned")
    st.download_button(
        "⬇️ Download RAW+CLEANED Excel (2 sheets)",
        data=buf.getvalue(),
        file_name="asset_raw_cleaned.xlsx",
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
