# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 David Martinez

"""
streamlitapp.py — Front-End UI for the FPV Build Explorer
================================================================

This module defines the Streamlit-based user interface for the FPV Build
Explorer. It orchestrates:

    1. Rendering all user inputs (via ui_inputs.py)
    2. Building the Kwad + Fuzz objects (via build_kwad.py)
    3. Running the performance engine (via engine.py)
    4. Rendering metrics, stress bars, and build classification
    5. Import/export of JSON build profiles
    6. Displaying the full FPV theory and community reference section

This file intentionally contains **no physics, no computation, and no data
models**. It serves purely as the UI controller for the application.

All heavy lifting is delegated to:
    - physics.py
    - engine.py
    - build_kwad.py
    - ui_inputs.py
    - ui_metrics.py
    - ui_import_export.py
    - theory_section.py
"""

import streamlit as st

from ui_inputs import render_inputs
from build_kwad import build_kwad_and_fuzz
from ui_metrics import render_metrics
from ui_import_export import render_import_export
from theory_section import render_theory_section

import engine


# ============================================================
# Page Setup
# ============================================================

st.set_page_config(
    page_title="MartyMayhem's FPV Build Explorer",
    layout="centered"
)

st.title("MartyMayhem's FPV Build Explorer")
st.write("A physics‑based FPV Drone build modeling tool.")


# ============================================================
# 1. Render all user inputs → returns cfg dict
# ============================================================

cfg = render_inputs()


# ============================================================
# 2. Build Kwad + Fuzz objects from cfg
# ============================================================

kwad, fuzz = build_kwad_and_fuzz(cfg)


# ============================================================
# 3. Evaluate quad performance
# ============================================================

perf = engine.evaluate_kwad(kwad, fuzz)


# ============================================================
# 4. Render metrics, stress bars, classification
# ============================================================

render_metrics(cfg, kwad, perf, fuzz)


# ============================================================
# 5. Import / Export JSON
# ============================================================

render_import_export()


# ============================================================
# 6. FPV Theory Section
# ============================================================

with st.expander("FPV Theory, Math & Community Reference", expanded=False):
    render_theory_section()
