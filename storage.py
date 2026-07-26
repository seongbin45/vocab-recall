"""
Persistent learning data for Streamlit + CLI.

- Local / CLI: ~/.vocab/data.json (or VOCAB_DATA)
- Streamlit (incl. Community Cloud): browser localStorage (survives refresh)
  plus a local file backup when the filesystem allows it
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import streamlit as st

from vocab import DEFAULT_DATA, ensure_data, save_data

LS_KEY = "vocab_data_v1"
LS_INIT_KEY = "vocab_ls_boot"


def is_streamlit_cloud() -> bool:
    return Path("/mount/src").exists() or os.environ.get(
        "STREAMLIT_RUNTIME_ENVIRONMENT", ""
    ).lower() == "cloud"


def file_data_path() -> Path:
    qp = None
    try:
        qp = st.query_params.get("data")
    except Exception:
        qp = None
    if qp:
        return Path(qp)
    env = os.environ.get("VOCAB_DATA")
    if env:
        return Path(env)
    return DEFAULT_DATA


def _local_storage():
    """Lazy LocalStorage; returns None if the package is unavailable."""
    if st.session_state.get("_ls_disabled"):
        return None
    try:
        from streamlit_local_storage import LocalStorage
    except Exception:
        st.session_state._ls_disabled = True
        return None
    if "_vocab_ls" not in st.session_state:
        try:
            st.session_state._vocab_ls = LocalStorage(key=LS_INIT_KEY)
        except Exception:
            st.session_state._ls_disabled = True
            return None
    return st.session_state._vocab_ls


def _read_local_storage() -> dict[str, Any] | None:
    ls = _local_storage()
    if ls is None:
        return None
    try:
        raw = ls.getItem(LS_KEY)
    except Exception:
        return None
    if raw is None or raw == "":
        return None
    try:
        if isinstance(raw, dict):
            return raw
        return json.loads(raw)
    except Exception:
        return None


def _write_local_storage(data: dict[str, Any]) -> bool:
    ls = _local_storage()
    if ls is None:
        return False
    try:
        n = int(st.session_state.get("_ls_write_n", 0)) + 1
        st.session_state._ls_write_n = n
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        ls.setItem(LS_KEY, payload, key=f"vocab_ls_set_{n}")
        return True
    except Exception:
        return False


def normalize(data: dict[str, Any], default_settings: dict) -> dict[str, Any]:
    data.setdefault("version", 1)
    data.setdefault("last_weekly", None)
    data.setdefault("next_id", 1)
    data.setdefault("items", [])
    data.setdefault("settings", {})
    for k, v in default_settings.items():
        data["settings"].setdefault(k, v)
    n = int(data["settings"].get("batch_size", 5))
    data["settings"]["batch_size"] = max(3, min(5, n))
    return data


def load_progress(default_settings: dict) -> dict[str, Any]:
    """
    Load once per Streamlit session into session_state['data'].
    Order: memory → browser localStorage → disk file → empty.
    """
    if "data" in st.session_state and isinstance(st.session_state.data, dict):
        return normalize(st.session_state.data, default_settings)

    path = file_data_path()
    st.session_state.path = path

    data = _read_local_storage()
    if data is None:
        data = ensure_data(path)
    else:
        # Keep a file copy when possible (local machines / same container)
        try:
            save_data(path, data)
        except Exception:
            pass

    data = normalize(data, default_settings)
    st.session_state.data = data
    # Ensure browser has a copy even if we loaded from disk
    _write_local_storage(data)
    return data


def persist_progress(data: dict[str, Any]) -> None:
    """Write memory + disk + browser localStorage."""
    st.session_state.data = data
    path = st.session_state.get("path") or file_data_path()
    st.session_state.path = path
    try:
        save_data(path, data)
    except Exception:
        pass
    _write_local_storage(data)


def export_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def import_json(text: str, default_settings: dict) -> dict[str, Any] | None:
    try:
        data = json.loads(text)
    except Exception:
        return None
    if not isinstance(data, dict) or "items" not in data:
        return None
    return normalize(data, default_settings)
