# dashboard_asset.py

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ---- Visual defaults ----
px.defaults.template = "plotly_white"
PX_PALETTE = px.colors.qualitative.Safe
PX_SEQ = PX_PALETTE

# ✅ Use the same colour family as asset_overview.py ONLY for the Asset Overview section
OVERVIEW_SEQ = px.colors.qualitative.Plotly  # default Plotly palette (blue-forward)

# ✅ Match hardware_assets.py palette ONLY for Hardware Assets section
HARDWARE_SEQ = [
    "#004C99",  # navy blue (brand)
    "#0066CC",  # strong blue
    "#007ACC",  # azure
    "#3399FF",  # light blue
    "#66B2FF",  # pale blue
    "#99CCFF",  # very light
]

# ✅ Match Target 3 – Software Assets palette (use Plotly default to mirror the other module)
SOFTWARE_SEQ = px.colors.qualitative.Plotly

# ✅ New: palettes to align Asset Assignments with asset_assignments.py
ASSIGNMENTS_SEQ = px.colors.qualitative.Plotly
MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#99CCFF"]

# =========================
# Helpers
# =========================
def _apply_bar_labels(fig, show_labels: bool, fmt: str = None):
    if not show_labels:
        return fig
    for tr in fig.data:
        t = getattr(tr, "type", None)
        if t == "bar":
            tr.update(texttemplate=fmt if fmt else "%{y}", textposition="outside", cliponaxis=False)
        elif t in ("pie", "funnel", "funnelarea", "waterfall"):
            tr.update(texttemplate=fmt if fmt else "%{value}")
    return fig

@st.cache_data(show_spinner=False)
def _prep_base(df: pd.DataFrame):
    d = df.copy()

    # Common date columns used across asset modules
    date_cols = [
        "warranty_start", "warranty_end", "update_on",
        "purchase_date", "procurement_date", "return_date",
        "latest_to_dispose", "pm_completed", "installation_date",
        "license_expiration_date", "jml_date", "JML Date",
    ]
    for c in date_cols:
        if c in d.columns:
            d[c] = pd.to_datetime(d[c], errors="coerce")

    # Convenience fields
    if "asset_id" in d.columns:
        d["__asset_id__"] = d["asset_id"].astype(str)
    elif "Asset ID" in d.columns:
        d["__asset_id__"] = d["Asset ID"].astype(str)
    else:
        d["__asset_id__"] = np.arange(len(d)).astype(str)

    # Derived age (years) from warranty_start or update_on
    base_age_col = "warranty_start" if "warranty_start" in d.columns else ("update_on" if "update_on" in d.columns else None)
    if base_age_col is not None:
        d["asset_age_years"] = ((pd.Timestamp.today().normalize() - d[base_age_col]).dt.days / 365.25).replace([np.inf, -np.inf], np.nan)
    else:
        d["asset_age_years"] = np.nan

    # Normalize helpful categorical columns if present
    for c in ["asset_status", "Asset Status", "status"]:
        if c in d.columns:
            d["__asset_status__"] = d[c].astype(str)
            break
    for c in ["brand", "Brand"]:
        if c in d.columns:
            d["__brand__"] = d[c].astype(str)
            break
    for c in ["type", "Type", "device_type"]:
        if c in d.columns:
            d["__type__"] = d[c].astype(str)
            break
    for c in ["os", "OS"]:
        if c in d.columns:
            d["__os__"] = d[c].astype(str)
            break
    for c in ["model", "Model"]:
        if c in d.columns:
            d["__model__"] = d[c].astype(str)
            break
    for c in ["location", "Location"]:
        if c in d.columns:
            d["__location__"] = d[c].astype(str)
            break
    for c in ["region", "Region"]:
        if c in d.columns:
            d["__region__"] = d[c].astype(str)
            break
    for c in ["department", "Department"]:
        if c in d.columns:
            d["__department__"] = d[c].astype(str)
            break
    for c in ["Owner", "owner", "Assigned To"]:
        if c in d.columns:
            # ✅ FIX: astype(str) — function call, not subscript
            d["__owner__"] = d[c].astype(str)
            break
    for c in ["software_name", "Software", "application", "product_number"]:
        if c in d.columns:
            d["__software__"] = d[c].astype(str)
            break
    for c in ["license_type", "License Type", "av_status"]:
        if c in d.columns:
            d["__license_type__"] = d[c].astype(str)
            break
    for c in ["version", "Version", "av_version"]:
        if c in d.columns:
            d["__version__"] = d[c].astype(str)
            break

    return d

def _agg_by_granularity(s: pd.Series, how="count", granularity="D"):
    if granularity == "W":
        return s.resample("W-MON").size() if how == "count" else s.resample("W-MON").mean()
    if granularity == "M":
        return s.resample("MS").size() if how == "count" else s.resample("MS").mean()
    return s.resample("D").size() if how == "count" else s.resample("D").mean()

def _safe_timecounts_from_index(idx, granularity, label_out):
    s = idx.to_series().copy()
    s.name = "__dt__"
    out = _agg_by_granularity(s, how="count", granularity=granularity)
    if isinstance(out, pd.Series):
        out = out.rename_axis("__dt__").reset_index(name="count")
    else:
        out = out.reset_index()
    return out.rename(columns={"__dt__": label_out})

# Optional: seasonal decomposition (kept for parity)
try:
    from statsmodels.tsa.seasonal import seasonal_decompose
    _HAS_DECOMP = True
except Exception:
    _HAS_DECOMP = False

# =========================
# Main
# =========================
def dashboard_asset(df: pd.DataFrame):
    st.markdown("## 🖥️ IT Asset Inventory Dashboard")
    df = _prep_base(df)

    # ---------------- Sidebar controls ----------------
    with st.sidebar:
        st.markdown("### 🔎 Filters")

        # Choose a date column for filtering (relevant to asset graphs)
        date_candidates = [
            c for c in [
                "warranty_start", "update_on", "purchase_date", "procurement_date",
                "installation_date", "warranty_end", "return_date", "latest_to_dispose",
                "pm_completed", "jml_date", "JML Date", "license_expiration_date"
            ] if c in df.columns
        ]
        date_col_choice = st.selectbox(
            "Date column for filtering",
            options=date_candidates if date_candidates else ["(none)"],
            index=0 if date_candidates else 0,
            key="asset_flt_date_col"
        )

        if date_col_choice != "(none)" and df[date_col_choice].notna().any():
            min_d = pd.to_datetime(df[date_col_choice]).min()
            max_d = pd.to_datetime(df[date_col_choice]).max()
            date_range = st.date_input(
                "Date range",
                value=(min_d.date(), max_d.date()),
                min_value=min_d.date(), max_value=max_d.date(),
                key="asset_flt_date_range",
            )
        else:
            date_range = None

        def _opt(col_alias_list):
            for c in col_alias_list:
                if c in df.columns:
                    return sorted([v for v in df[c].dropna().astype(str).unique()])
            return []

        # Common asset filters
        typ  = st.multiselect("Type", _opt(["__type__", "type", "Type", "device_type"]), key="asset_flt_type")
        brand= st.multiselect("Brand", _opt(["__brand__", "brand", "Brand"]), key="asset_flt_brand")
        model= st.multiselect("Model", _opt(["__model__", "model", "Model"]), key="asset_flt_model")
        os_  = st.multiselect("OS", _opt(["__os__", "os", "OS"]), key="asset_flt_os")
        ast  = st.multiselect("Asset Status", _opt(["__asset_status__", "asset_status", "Asset Status", "status"]), key="asset_flt_status")
        loc  = st.multiselect("Location", _opt(["__location__", "location", "Location"]), key="asset_flt_location")
        reg  = st.multiselect("Region", _opt(["__region__", "region", "Region"]), key="asset_flt_region")
        dept = st.multiselect("Department", _opt(["__department__", "department", "Department"]), key="asset_flt_dept")
        own  = st.multiselect("Owner", _opt(["__owner__", "Owner", "owner", "Assigned To"]), key="asset_flt_owner")

        # Software-related filters (only if present)
        sw   = st.multiselect("Software", _opt(["__software__", "software_name", "Software", "application", "product_number"]), key="asset_flt_sw")
        lict = st.multiselect("License Type", _opt(["__license_type__", "license_type", "License Type", "av_status"]), key="asset_flt_lictype")
        ver  = st.multiselect("Version", _opt(["__version__", "version", "Version", "av_version"]), key="asset_flt_version")

        st.markdown("---")
        st.markdown("### ⚙️ View options")
        gran = st.radio("Time granularity", ["Daily","Weekly","Monthly"], horizontal=True, key="asset_gran")
        gran_key = {"Daily":"D","Weekly":"W","Monthly":"M"}[gran]
        show_labels = st.toggle("Show bar labels", value=True, key="asset_show_labels")
        show_rangeslider = st.toggle("Show range slider on time-series", value=True, key="asset_show_rangeslider")
        show_smoothing = st.toggle("Show 7-day moving average where relevant", value=False, key="asset_show_smoothing")

        st.markdown("---")
        clear = st.button("Clear all filters", use_container_width=True, key="asset_clear")

    # -------------- Apply filters --------------
    df_filtered = df.copy()

    if clear:
        typ = brand = model = os_ = ast = loc = reg = dept = own = sw = lict = ver = []
        if date_col_choice != "(none)" and date_range and df_filtered[date_col_choice].notna().any():
            date_range = (
                pd.to_datetime(df_filtered[date_col_choice]).min().date(),
                pd.to_datetime(df_filtered[date_col_choice]).max().date()
            )

    if date_range and date_col_choice != "(none)" and date_col_choice in df_filtered.columns:
        start_date, end_date = date_range if isinstance(date_range, tuple) else (date_range, date_range)
        df_filtered = df_filtered[
            (pd.to_datetime(df_filtered[date_col_choice]) >= pd.to_datetime(start_date)) &
            (pd.to_datetime(df_filtered[date_col_choice]) <= pd.to_datetime(end_date))
        ]

    def _apply_multi(df_in, col_alias_list, values):
        if not values:
            return df_in
        for c in col_alias_list:
            if c in df_in.columns:
                return df_in[df_in[c].astype(str).isin(values)]
        return df_in

    df_filtered = _apply_multi(df_filtered, ["__type__", "type", "Type", "device_type"], typ)
    df_filtered = _apply_multi(df_filtered, ["__brand__", "brand", "Brand"], brand)
    df_filtered = _apply_multi(df_filtered, ["__model__", "model", "Model"], model)
    df_filtered = _apply_multi(df_filtered, ["__os__", "os", "OS"], os_)
    df_filtered = _apply_multi(df_filtered, ["__asset_status__", "asset_status", "Asset Status", "status"], ast)
    df_filtered = _apply_multi(df_filtered, ["__location__", "location", "Location"], loc)
    df_filtered = _apply_multi(df_filtered, ["__region__", "region", "Region"], reg)
    df_filtered = _apply_multi(df_filtered, ["__department__", "department", "Department"], dept)
    df_filtered = _apply_multi(df_filtered, ["__owner__", "Owner", "owner", "Assigned To"], own)
    df_filtered = _apply_multi(df_filtered, ["__software__", "software_name", "Software", "application", "product_number"], sw)
    df_filtered = _apply_multi(df_filtered, ["__license_type__", "license_type", "License Type", "av_status"], lict)
    df_filtered = _apply_multi(df_filtered, ["__version__", "version", "Version", "av_version"], ver)

    # ===== KPIs (asset-relevant) =====
    st.markdown("---")
    st.markdown("### 🔹 Key Metrics")
    k1, k2, k3, k4 = st.columns(4)

    # Total assets (nunique of asset_id if present, else row count)
    total_assets = df_filtered["__asset_id__"].nunique() if "__asset_id__" in df_filtered.columns else len(df_filtered)
    k1.metric("Total Assets", f"{total_assets:,}")

    # In-use % (by asset_status-like column)
    inuse_pct = None
    if "__asset_status__" in df_filtered.columns:
        stat = df_filtered["__asset_status__"].str.lower().str.strip()
        denom = (stat.notna()).sum()
        if denom > 0:
            inuse_pct = (stat.eq("in use").sum() / denom) * 100.0
    k2.metric("In-Use (%)", f"{inuse_pct:.1f}%" if inuse_pct is not None else "N/A")

    # Unique brands
    uniq_brands = df_filtered["__brand__"].nunique() if "__brand__" in df_filtered.columns else np.nan
    k3.metric("Unique Brands", int(uniq_brands) if pd.notna(uniq_brands) else "N/A")

    # Warranties expiring next 60 days
    expiring_60 = None
    if "warranty_end" in df_filtered.columns:
        now = pd.Timestamp.today().normalize()
        soon = now + pd.Timedelta(days=60)
        expiring_60 = df_filtered["warranty_end"].between(now, soon, inclusive="both").sum()
    k4.metric("Expiring ≤60 Days", f"{int(expiring_60):,}" if expiring_60 is not None else "N/A")

    cdl1, cdl2 = st.columns([1,1])
    with cdl1:
        st.download_button(
            "⬇️ Download filtered data (CSV)",
            df_filtered.to_csv(index=False).encode("utf-8"),
            file_name="asset_dashboard_filtered.csv",
            mime="text/csv",
            use_container_width=True
        )
    with cdl2:
        kpi_snap = {
            "total_assets": [total_assets],
            "in_use_pct": [inuse_pct if inuse_pct is not None else np.nan],
            "unique_brands": [uniq_brands if pd.notna(uniq_brands) else np.nan],
            "expiring_60d": [expiring_60 if expiring_60 is not None else np.nan],
        }
        st.download_button(
            "⬇️ Download KPI snapshot (CSV)",
            pd.DataFrame(kpi_snap).to_csv(index=False).encode("utf-8"),
            file_name="asset_dashboard_kpis.csv",
            mime="text/csv",
            use_container_width=True
        )

    # =========================================================
    # 1) Asset Overview  (🔵 use OVERVIEW_SEQ to match asset_overview.py)
    # =========================================================
    st.markdown("---")
    st.markdown("### Asset Overview")

    # Row 1: Asset intake over time (area) | Assets by Category (Type/Brand/OS)
    c1, c2 = st.columns(2)
    with c1:
        # Choose best date for intake curve
        intake_col = None
        for c in ["warranty_start", "update_on", "purchase_date", "procurement_date"]:
            if c in df_filtered.columns and df_filtered[c].notna().any():
                intake_col = c
                break
        if intake_col:
            t = df_filtered.dropna(subset=[intake_col]).copy().set_index(intake_col).sort_index()
            ts = _safe_timecounts_from_index(t.index, gran_key, "date").rename(columns={"count":"assets_added"})
            if not ts.empty:
                fig = px.area(
                    ts,
                    x="date",
                    y="assets_added",
                    title=f"Asset Intake Over Time ({intake_col})",
                    color_discrete_sequence=OVERVIEW_SEQ
                )
                if show_rangeslider:
                    fig.update_xaxes(rangeslider_visible=True)
                if show_smoothing and gran_key == "D":
                    ts["MA7"] = ts["assets_added"].rolling(7).mean()
                    fig.add_scatter(x=ts["date"], y=ts["MA7"], mode="lines", name="7-day MA")
                st.plotly_chart(fig, use_container_width=True, key="asset_1a_intake")
    with c2:
        # Category bar: prefer type, else brand, else os
        cat_col = None
        for c in ["__type__", "__brand__", "__os__"]:
            if c in df_filtered.columns and df_filtered[c].notna().any():
                cat_col = c
                break
        if cat_col:
            cat_df = df_filtered[cat_col].value_counts().reset_index()
            cat_df.columns = [cat_col, "count"]
            fig = px.bar(
                cat_df.head(20),
                x=cat_col,
                y="count",
                text="count",
                title=f"Assets by {cat_col.replace('__','').strip('_').upper()}",
                color_discrete_sequence=OVERVIEW_SEQ
            )
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="asset_1b_by_category")

    # =========================================================
    # 2) Hardware Assets  (🔵 use HARDWARE_SEQ to match hardware_assets.py)
    # =========================================================
    st.markdown("---")
    st.markdown("###  Hardware Assets")

    # Row 2: Warranty status pie | Warranty expiries by month
    c3, c4 = st.columns(2)
    with c3:
        wstat_col = None
        for c in ["warranty_status", "Warranty Status"]:
            if c in df_filtered.columns and df_filtered[c].notna().any():
                wstat_col = c; break
        if wstat_col:
            wstat = df_filtered[wstat_col].value_counts().reset_index()
            wstat.columns = ["warranty_status", "count"]
            fig = px.pie(
                wstat,
                names="warranty_status",
                values="count",
                title="Warranty Status Distribution",
                color_discrete_sequence=HARDWARE_SEQ
            )
            st.plotly_chart(fig, use_container_width=True, key="asset_2a_warranty_status")
    with c4:
        if "warranty_end" in df_filtered.columns and df_filtered["warranty_end"].notna().any():
            wexp = df_filtered.dropna(subset=["warranty_end"]).copy()
            wexp["month"] = wexp["warranty_end"].dt.to_period("M").astype(str)
            w_by_month = wexp.groupby("month").size().reset_index(name="expiring")
            fig = px.bar(
                w_by_month,
                x="month",
                y="expiring",
                text="expiring",
                title="Warranty Expiries by Month",
                color_discrete_sequence=HARDWARE_SEQ
            )
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="asset_2b_warranty_expiry")

    # Row 3: Asset status distribution | Age cohorts
    c5, c6 = st.columns(2)
    with c5:
        if "__asset_status__" in df_filtered.columns and df_filtered["__asset_status__"].notna().any():
            stat_cnt = df_filtered["__asset_status__"].value_counts().reset_index()
            stat_cnt.columns = ["asset_status", "count"]
            fig = px.bar(
                stat_cnt,
                x="asset_status",
                y="count",
                text="count",
                title="Asset Status Distribution",
                color_discrete_sequence=HARDWARE_SEQ
            )
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="asset_2c_status_dist")
    with c6:
        # Age cohorts from warranty_start/update_on
        age_base = "warranty_start" if "warranty_start" in df_filtered.columns else ("update_on" if "update_on" in df_filtered.columns else None)
        if age_base and df_filtered[age_base].notna().any():
            base = df_filtered.dropna(subset=[age_base]).copy()
            base["age_years"] = (pd.Timestamp.today().normalize() - base[age_base]).dt.days / 365.25
            bins = [-0.01, 1, 2, 3, 4, 5, 10, np.inf]
            labels = ["<1y","1–2y","2–3y","3–4y","4–5y","5–10y",">10y"]
            base["age_bucket"] = pd.cut(base["age_years"], bins=bins, labels=labels)
            age_counts = base["age_bucket"].value_counts().reindex(labels).fillna(0).reset_index()
            age_counts.columns = ["age_bucket","count"]
            fig = px.bar(
                age_counts,
                x="age_bucket",
                y="count",
                text="count",
                title=f"Asset Age Cohorts (based on {age_base})",
                color_discrete_sequence=HARDWARE_SEQ
            )
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="asset_2d_age_cohorts")

    # Row 4: Location bar | Region bar
    c7, c8 = st.columns(2)
    with c7:
        if "__location__" in df_filtered.columns and df_filtered["__location__"].notna().any():
            loc_ct = df_filtered["__location__"].value_counts().reset_index()
            loc_ct.columns = ["location","count"]
            fig = px.bar(
                loc_ct.head(20),
                x="location",
                y="count",
                text="count",
                title="Top Locations by Asset Count",
                color_discrete_sequence=HARDWARE_SEQ
            )
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="asset_2e_location")
    with c8:
        if "__region__" in df_filtered.columns and df_filtered["__region__"].notna().any():
            reg_ct = df_filtered["__region__"].value_counts().reset_index()
            reg_ct.columns = ["region","count"]
            fig = px.bar(
                reg_ct,
                x="region",
                y="count",
                text="count",
                title="Assets by Region",
                color_discrete_sequence=HARDWARE_SEQ
            )
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="asset_2f_region")

    # Row 5: Brand bar | Brand→Model treemap
    c9, c10 = st.columns(2)
    with c9:
        if "__brand__" in df_filtered.columns and df_filtered["__brand__"].notna().any():
            brand_ct = df_filtered["__brand__"].value_counts().reset_index()
            brand_ct.columns = ["brand","count"]
            fig = px.bar(
                brand_ct,
                x="brand",
                y="count",
                text="count",
                title="Assets by Brand",
                color_discrete_sequence=HARDWARE_SEQ
            )
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="asset_2g_brand")
    with c10:
        if {"__brand__","__model__"} <= set(df_filtered.columns) and df_filtered["__model__"].notna().any():
            bm = df_filtered.groupby(["__brand__","__model__"]).size().reset_index(name="count").sort_values("count", ascending=False)
            fig = px.treemap(
                bm,
                path=["__brand__","__model__"],
                values="count",
                title="Brand → Model Composition",
                color_discrete_sequence=HARDWARE_SEQ
            )
            st.plotly_chart(fig, use_container_width=True, key="asset_2h_brand_model")

    # =========================================================
    # 3) Software Assets  (🔵 use SOFTWARE_SEQ to mirror Target 3 – Software Assets module)
    # =========================================================
    st.markdown("---")
    st.markdown("###  Software Assets")

    # Row 6: Top software installs | Version distribution
    c11, c12 = st.columns(2)
    with c11:
        if "__software__" in df_filtered.columns and df_filtered["__software__"].notna().any():
            sw_counts = df_filtered["__software__"].value_counts().reset_index()
            sw_counts.columns = ["software","count"]
            fig = px.bar(
                sw_counts.head(20), x="software", y="count", text="count",
                title="Top Installed Software", color_discrete_sequence=SOFTWARE_SEQ
            )
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="asset_3a_software")
    with c12:
        if "__version__" in df_filtered.columns and df_filtered["__version__"].notna().any():
            ver_ct = df_filtered["__version__"].value_counts().reset_index()
            ver_ct.columns = ["version","count"]
            fig = px.bar(
                ver_ct.head(15), x="version", y="count", text="count",
                title="Top Versions", color_discrete_sequence=SOFTWARE_SEQ
            )
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="asset_3b_versions")

    # Row 7: License type pie | Installations & expirations timeline
    c13, c14 = st.columns(2)
    with c13:
        if "__license_type__" in df_filtered.columns and df_filtered["__license_type__"].notna().any():
            lic = df_filtered["__license_type__"].value_counts().reset_index()
            lic.columns = ["license_type","count"]
            fig = px.pie(
                lic, names="license_type", values="count",
                title="License Type Distribution", color_discrete_sequence=SOFTWARE_SEQ
            )
            st.plotly_chart(fig, use_container_width=True, key="asset_3c_license_type")
    with c14:
        # Installations by month (installation_date/update_on/warranty_start)
        inst_col = None
        for c in ["installation_date", "update_on", "warranty_start"]:
            if c in df_filtered.columns and df_filtered[c].notna().any():
                inst_col = c; break
        if inst_col:
            t = df_filtered.dropna(subset=[inst_col]).copy()
            t["month"] = t[inst_col].dt.to_period("M").astype(str)
            by_m = t.groupby("month").size().reset_index(name="installed")
            fig = px.area(
                by_m, x="month", y="installed",
                title=f"Installations by Month ({inst_col})",
                color_discrete_sequence=SOFTWARE_SEQ
            )
            st.plotly_chart(fig, use_container_width=True, key="asset_3d_installs")
        # Expirations by month (license_expiration_date or warranty_end)
        exp_col = None
        for c in ["license_expiration_date", "license_end", "warranty_end"]:
            if c in df_filtered.columns and df_filtered[c].notna().any():
                exp_col = c; break
        if exp_col:
            t2 = df_filtered.dropna(subset=[exp_col]).copy()
            t2["month"] = t2[exp_col].dt.to_period("M").astype(str)
            by_m2 = t2.groupby("month").size().reset_index(name="expiring")
            fig2 = px.bar(
                by_m2, x="month", y="expiring", text="expiring",
                title=f"Expirations by Month ({exp_col})",
                color_discrete_sequence=SOFTWARE_SEQ
            )
            fig2 = _apply_bar_labels(fig2, show_labels)
            st.plotly_chart(fig2, use_container_width=True, key="asset_3e_expiring")

    # Row 8: Usage histogram (if any) | Software by department
    c15, c16 = st.columns(2)
    with c15:
        usage_col = None
        for c in ["usage_hours", "usage_metric"]:
            if c in df_filtered.columns and pd.api.types.is_numeric_dtype(df_filtered[c]):
                usage_col = c; break
        if usage_col:
            figh = px.histogram(
                df_filtered.dropna(subset=[usage_col]),
                x=usage_col, nbins=20,
                title=f"Usage Distribution ({usage_col})",
                color_discrete_sequence=SOFTWARE_SEQ
            )
            st.plotly_chart(figh, use_container_width=True, key="asset_3f_usage_hist")
    with c16:
        if {"__software__","__department__"} <= set(df_filtered.columns):
            dept_sw = df_filtered[["__department__","__software__"]].dropna().groupby(["__department__","__software__"]).size().reset_index(name="count")
            if not dept_sw.empty:
                fig = px.bar(
                    dept_sw.head(25), x="__department__", y="count", color="__software__",
                    title="Top Software by Department",
                    color_discrete_sequence=SOFTWARE_SEQ
                )
                st.plotly_chart(fig, use_container_width=True, key="asset_3g_dept_sw")

    # =========================================================
    # 4) Asset Assignments  (aligned with asset_assignments.py)
    # =========================================================
    st.markdown("---")
    st.markdown("###  Asset Assignments")

    # Row 9: Assets per owner | Assets per department
    c17, c18 = st.columns(2)
    with c17:
        if {"__owner__","__asset_id__"} <= set(df_filtered.columns):
            owner_ct = df_filtered.groupby("__owner__").size().reset_index(name="asset_count")
            fig = px.bar(
                owner_ct.sort_values("asset_count", ascending=False).head(25),
                x="__owner__", y="asset_count", text="asset_count",
                title="Top 25 Users by Assigned Assets",
                color_discrete_sequence=ASSIGNMENTS_SEQ
            )
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="asset_4a_owner_assets")
    with c18:
        if {"__department__","__asset_id__"} <= set(df_filtered.columns):
            dept_ct = df_filtered.groupby("__department__").size().reset_index(name="asset_count")
            fig = px.bar(
                dept_ct.sort_values("asset_count", ascending=False),
                x="__department__", y="asset_count", text="asset_count",
                title="Assets by Department",
                color_discrete_sequence=ASSIGNMENTS_SEQ
            )
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="asset_4b_dept_assets")

    # Row 10: JML pie & time trend | Asset status by region (grouped)
    c19, c20 = st.columns(2)
    with c19:
        jml_status_col = "JML Status" if "JML Status" in df_filtered.columns else None
        jml_date_col = "JML Date" if "JML Date" in df_filtered.columns else ("jml_date" if "jml_date" in df_filtered.columns else None)
        if jml_status_col:
            jml_ct = df_filtered[jml_status_col].value_counts().reset_index()
            jml_ct.columns = ["JML Status","count"]
            fig = px.pie(
                jml_ct, names="JML Status", values="count",
                title="Joiner / Mover / Leaver Distribution",
                color_discrete_sequence=MES_BLUE
            )
            st.plotly_chart(fig, use_container_width=True, key="asset_4c_jml_pie")
        if jml_date_col and df_filtered[jml_date_col].notna().any():
            time_tr = df_filtered.dropna(subset=[jml_date_col]).copy()
            time_tr["month"] = time_tr[jml_date_col].dt.to_period("M").astype(str)
            jml_ts = time_tr.groupby("month").size().reset_index(name="count")
            fig = px.line(
                jml_ts, x="month", y="count", markers=True,
                title="JML Activity Over Time", color_discrete_sequence=[MES_BLUE[0]]
            )
            # Optionally enforce exact line/marker color:
            # fig.update_traces(line=dict(color=MES_BLUE[0]), marker=dict(color=MES_BLUE[0]))
            st.plotly_chart(fig, use_container_width=True, key="asset_4d_jml_trend")
    with c20:
        if {"__region__","__asset_status__"} <= set(df_filtered.columns):
            region_ct = df_filtered.groupby(["__region__","__asset_status__"]).size().reset_index(name="count")
            fig = px.bar(
                region_ct, x="__region__", y="count", color="__asset_status__", barmode="group",
                title="Asset Status by Region", color_discrete_sequence=ASSIGNMENTS_SEQ
            )
            st.plotly_chart(fig, use_container_width=True, key="asset_4e_status_by_region")

    # =========================================================
    # 5) Asset Lifecycle  (stay on PX_SEQ)
    # =========================================================
    st.markdown("---")
    st.markdown("###  Asset Lifecycle")

    # Row 11: Procurement timeline | Asset age histogram
    c21, c22 = st.columns(2)
    with c21:
        proc_col = None
        for c in ["purchase_date", "procurement_date", "warranty_start", "jml_date", "JML Date"]:
            if c in df_filtered.columns and df_filtered[c].notna().any():
                proc_col = c; break
        if proc_col:
            t = df_filtered.dropna(subset=[proc_col]).copy()
            t["month"] = t[proc_col].dt.to_period("M").astype(str)
            by_month = t.groupby("month").size().reset_index(name="procured")
            fig = px.bar(
                by_month, x="month", y="procured", text="procured",
                title=f"Assets Procured by Month ({proc_col})",
                color_discrete_sequence=PX_SEQ
            )
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="asset_5a_procurement")
    with c22:
        if df_filtered["asset_age_years"].notna().any():
            fig = px.histogram(
                df_filtered.dropna(subset=["asset_age_years"]),
                x="asset_age_years", nbins=20,
                title="Distribution of Asset Age (Years)",
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig, use_container_width=True, key="asset_5b_age_hist")

    # Row 12: Disposal status pie | Replacement timeline
    c23, c24 = st.columns(2)
    with c23:
        disp_col = None
        for c in ["disposal", "Disposal Status", "disposal_status"]:
            if c in df_filtered.columns and df_filtered[c].notna().any():
                disp_col = c; break
        if disp_col:
            disp_ct = df_filtered[disp_col].value_counts().reset_index()
            disp_ct.columns = ["disposal_status","count"]
            fig = px.pie(
                disp_ct, names="disposal_status", values="count",
                title="Disposal Status Breakdown", color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig, use_container_width=True, key="asset_5c_disposal")
    with c24:
        repl_col = None
        for c in ["warranty_end", "latest_to_dispose", "return_date"]:
            if c in df_filtered.columns and df_filtered[c].notna().any():
                repl_col = c; break
        if repl_col:
            tmp = df_filtered.dropna(subset=[repl_col]).copy()
            tmp["month"] = tmp[repl_col].dt.to_period("M").astype(str)
            timeline = tmp.groupby("month").size().reset_index(name="count")
            fig = px.line(
                timeline, x="month", y="count", markers=True,
                title=f"Upcoming Replacements by {repl_col}",
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig, use_container_width=True, key="asset_5d_replacement")

    return df_filtered
