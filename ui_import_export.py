# ui_import_export.py

import json
import streamlit as st


def render_import_export(cfg_key="config"):
    """
    Renders the Import/Export UI for build profiles.
    cfg_key: the session_state key where the config dict is stored.
    """

    with st.expander("Build Profile I/O", expanded=False):

        # ---------------------------------------------------------
        # Export JSON
        # ---------------------------------------------------------
        cfg = st.session_state.get(cfg_key, {})
        export_json = json.dumps(cfg, indent=2)

        st.download_button(
            label="Download Build JSON",
            data=export_json,
            file_name="kwad_build.json",
            mime="application/json"
        )

        # ---------------------------------------------------------
        # Import JSON
        # ---------------------------------------------------------
        uploaded = st.file_uploader("Import Build JSON", type=["json"])

        if uploaded:
            try:
                data = json.load(uploaded)

                if not isinstance(data, dict):
                    raise ValueError("JSON root must be an object/dict.")

                # Update session state
                st.session_state[cfg_key] = data

                st.success("Build imported successfully.")
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Failed to import JSON: {e}")
