# file_manager.py
import streamlit as st
import pandas as pd
import os, json, uuid, io, pickle
from datetime import datetime as _dt

DATA_DIR = ".streamlit_data"
CATALOG_PATH = os.path.join(DATA_DIR, "catalog.json")

# ---------- simple uploaded_file-like shim ----------
class _UploadedShim:
    def __init__(self, name: str):
        self.name = name  # provides uploaded_file.name compatibility

# ---------- storage helpers ----------
def _ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)

def _load_catalog():
    _ensure_dirs()
    if os.path.exists(CATALOG_PATH):
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"datasets": {}, "last_active_id": None, "auto_load": True}

def _save_catalog(cat):
    _ensure_dirs()
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(cat, f, indent=2)

def _parquet_available():
    try:
        import pyarrow  # noqa
        return True
    except Exception:
        return False

def _save_df(df: pd.DataFrame, basepath: str):
    # Try Parquet first (best for speed/size), then normalize and retry, then fall back to Pickle.
    if _parquet_available():
        try:
            path = basepath + ".parquet"
            df.to_parquet(path, index=False)
            return path
        except Exception as e1:
            try:
                df2 = _normalize_for_storage(df)
                path = basepath + ".parquet"
                df2.to_parquet(path, index=False)
                return path
            except Exception as e2:
                # Final fallback: Pickle (preserves whatever pandas can hold)
                path = basepath + ".pkl"
                with open(path, "wb") as f:
                    pickle.dump(df, f, protocol=pickle.HIGHEST_PROTOCOL)
                # Let the user know we fell back
                st.sidebar.warning(
                    "Parquet save failed; fell back to Pickle for this dataset.\n"
                    f"Reason: {type(e2).__name__}: {e2}"
                )
                return path
    # No pyarrow: Pickle
    path = basepath + ".pkl"
    with open(path, "wb") as f:
        pickle.dump(df, f, protocol=pickle.HIGHEST_PROTOCOL)
    return path


def _load_df(path: str) -> pd.DataFrame:
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    if path.endswith(".pkl"):
        with open(path, "rb") as f:
            return pickle.load(f)
    if path.endswith(".csv"):
        return pd.read_csv(path)
    raise ValueError(f"Unsupported storage format: {path}")

# ---------- parse uploaded files ----------
def _read_uploaded_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    bytes_data = uploaded_file.read()
    buffer = io.BytesIO(bytes_data)
    if name.endswith(".csv"):
        return pd.read_csv(buffer, encoding_errors="ignore")
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(buffer)
    elif name.endswith(".parquet"):
        return pd.read_parquet(buffer)
    else:
        buffer.seek(0)
        try:
            return pd.read_csv(buffer, encoding_errors="ignore")
        except Exception:
            buffer.seek(0)
            return pd.read_excel(buffer)

# ---------- session bootstrap ----------
def _bootstrap_state():
    if "catalog" not in st.session_state:
        st.session_state.catalog = _load_catalog()
    if "datasets" not in st.session_state:
        st.session_state.datasets = {}  # id -> meta
    if "active_id" not in st.session_state:
        st.session_state.active_id = None

    # re-index persisted datasets
    if not st.session_state.datasets:
        for ds_id, meta in st.session_state.catalog.get("datasets", {}).items():
            if os.path.exists(meta["path"]):
                st.session_state.datasets[ds_id] = meta

        # auto-select last active
        if st.session_state.catalog.get("auto_load") and st.session_state.catalog.get("last_active_id"):
            last_id = st.session_state.catalog["last_active_id"]
            if last_id in st.session_state.datasets and os.path.exists(st.session_state.datasets[last_id]["path"]):
                st.session_state.active_id = last_id

def _add_dataset(df: pd.DataFrame, display_name: str):
    ds_id = str(uuid.uuid4())[:8]
    basepath = os.path.join(DATA_DIR, f"ds_{ds_id}")
    path = _save_df(df, basepath)

    meta = {
        "name": display_name,
        "path": path,
        "created_at": _dt.now().isoformat(timespec="seconds"),
        "shape": list(df.shape),
    }
    st.session_state.datasets[ds_id] = meta
    st.session_state.catalog.setdefault("datasets", {})[ds_id] = meta
    st.session_state.catalog["last_active_id"] = ds_id
    st.session_state.active_id = ds_id
    _save_catalog(st.session_state.catalog)

def _delete_dataset(ds_id: str):
    meta = st.session_state.datasets.get(ds_id)
    if not meta:
        return
    try:
        if os.path.exists(meta["path"]):
            os.remove(meta["path"])
    except Exception:
        pass
    st.session_state.datasets.pop(ds_id, None)
    st.session_state.catalog["datasets"].pop(ds_id, None)
    if st.session_state.active_id == ds_id:
        st.session_state.active_id = None
        st.session_state.catalog["last_active_id"] = None
    _save_catalog(st.session_state.catalog)

@st.cache_data(show_spinner=False)
def _cached_load_df(path: str):
    return _load_df(path)

# ---------- PUBLIC API ----------
def file_manager_ui(label="📂 Data Manager (multi-file + persistent)"):
    """Renders a sidebar uploader (multiple), a dataset selector, and returns the active DataFrame.
       Also stores metadata in session for compatibility helpers below."""
    _bootstrap_state()
    st.sidebar.markdown(f"### {label}")

    uploads = st.sidebar.file_uploader(
        "Add datasets", type=["csv", "xlsx", "xls", "parquet"],
        accept_multiple_files=True, key="uploader_multiple"
    )
    if uploads:
        for up in uploads:
            try:
                df = _read_uploaded_file(up)
                _add_dataset(df, up.name)
                st.sidebar.success(f"Added: {up.name} ({df.shape[0]} rows)")
            except Exception as e:
                st.sidebar.error(f"Failed to load {up.name}: {e}")

    # dataset selector
    options = [(meta["name"], ds_id) for ds_id, meta in st.session_state.datasets.items()]
    if not options:
        st.info("No datasets yet. Upload one or more files from the sidebar.")
        return None

    names = [o[0] for o in options]
    ids = [o[1] for o in options]
    default_idx = 0
    if st.session_state.active_id and st.session_state.active_id in ids:
        default_idx = ids.index(st.session_state.active_id)

    choice = st.sidebar.selectbox("Active dataset", names, index=default_idx)
    chosen_id = ids[names.index(choice)]
    if chosen_id != st.session_state.active_id:
        st.session_state.active_id = chosen_id
        st.session_state.catalog["last_active_id"] = chosen_id
        _save_catalog(st.session_state.catalog)

    colA, colB = st.sidebar.columns(2)
    with colA:
        if st.button("🔄 Reload from disk"):
            st.cache_data.clear()
            st.sidebar.info("Reloaded cache.")
    with colB:
        if st.button("🗑️ Remove dataset"):
            _delete_dataset(st.session_state.active_id)
            st.rerun()

    auto = st.sidebar.toggle(
        "Auto-open last dataset on startup",
        value=st.session_state.catalog.get("auto_load", True)
    )
    if auto != st.session_state.catalog.get("auto_load", True):
        st.session_state.catalog["auto_load"] = auto
        _save_catalog(st.session_state.catalog)

    # show a tiny summary and preview (optional UI sugar)
    meta = st.session_state.datasets[st.session_state.active_id]
    st.caption(f"**Active dataset:** {meta['name']}  |  stored: `{os.path.basename(meta['path'])}`  |  shape: {tuple(meta['shape'])}")
    try:
        df = _cached_load_df(meta["path"])
    except Exception as e:
        st.error(f"Failed to load active dataset: {e}")
        return None

    # stash meta for compatibility helpers
    st.session_state["active_meta"] = meta
    return df

def get_active_uploaded_like():
    """Returns an object with `.name` so legacy code expecting uploaded_file.name keeps working."""
    meta = st.session_state.get("active_meta")
    if not meta:
        return None
    return _UploadedShim(meta["name"])

def _looks_datetime_object_series(s: pd.Series) -> bool:
    if s.dtype != "object":
        return False
    # any real datetime-like python objects hiding in an object column?
    try:
        return s.map(lambda x: isinstance(x, (pd.Timestamp, _dt))).any()
    except Exception:
        return False

def _normalize_for_storage(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        s = out[col]

        # If it's already a pandas datetime dtype, keep it
        if pd.api.types.is_datetime64_any_dtype(s):
            continue

        # If it's an object column containing datetime objects, coerce to pandas datetime
        if _looks_datetime_object_series(s):
            out[col] = pd.to_datetime(s, errors="coerce")
            continue

        # If it's an object column with messy mixed types (strings, numbers, None),
        # cast to "string" dtype (Arrow-friendly) instead of Python-object.
        if s.dtype == "object":
            try:
                out[col] = s.astype("string")
            except Exception:
                out[col] = s.astype(str)

    return out
