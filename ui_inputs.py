# ui_inputs.py

import streamlit as st

# ---------------------------------------------------------
# Default Presets
# ---------------------------------------------------------

DEFAULT_5IN = {
    "prop_diameter": 5.1,
    "prop_pitch": 4.3,
    "prop_blades": 3,
    "prop_weight": 3.5,

    "motor_kv": 1950,
    "motor_stator_d": 22,
    "motor_stator_h": 7,
    "motor_current_rating": 40,
    "motor_weight": 32,

    "lipo_cells": 6,
    "lipo_capacity": 1500,
    "lipo_c": 80,
    "lipo_weight": 253,
    "lipo_health": 100,

    "frame_noise": 20,
    "frame_wheelbase": 225,
    "frame_prop_fit": 5.1,
    "frame_weight": 150,

    "fc_loop": 1000,
    "fc_cpu": 60,
    "fc_dshot": 600,
    "fc_weight": 8,
    "esc_current_rating": 45,

    "esc_pwm": 48000,
    "esc_demag": "low",
    "esc_timing": "med",
    "esc_weight": 14,

    "video_power": 800,
    "video_weight": 30,
    "video_digital": True,

    "rx_weight": 10,
    "rx_elrs": True,

    "cam_weight": 0,

    "motor_count": 4,
    "payload": 0,

    # Fuzz defaults
    "fuzz_air": 1.0,
    "fuzz_drag": 1.0,
    "fuzz_prop": 1.0,
    "fuzz_motor_torque": 1.0,
    "fuzz_motor_eff": 1.0,
    "fuzz_batt_ir": 1.0,
    "fuzz_esc_loss": 1.0,
    "fuzz_thermal_r": 1.0,
    "fuzz_thermal_c": 1.0,
}

DEFAULT_WHOOP = {
    # (same as before)
}


# ---------------------------------------------------------
# Helper: Slider + Buttons
# ---------------------------------------------------------

def slider_with_buttons(label, minv, maxv, step, key, cfg):
    value_key = f"{key}_value"
    key_counter = f"{key}_counter"

    if value_key not in st.session_state:
        st.session_state[value_key] = cfg.get(key, minv)
    if key_counter not in st.session_state:
        st.session_state[key_counter] = 0

    col_minus, col_slider, col_plus = st.columns([1, 6, 1])

    with col_minus:
        if st.button("−", key=f"{key}_minus"):
            st.session_state[value_key] = max(minv, st.session_state[value_key] - step)
            st.session_state[key_counter] += 1

    with col_slider:
        slider_widget_key = f"{key}_slider_{st.session_state[key_counter]}"
        st.session_state[value_key] = st.slider(
            label,
            min_value=minv,
            max_value=maxv,
            value=st.session_state[value_key],
            step=step,
            key=slider_widget_key
        )

    with col_plus:
        if st.button("+", key=f"{key}_plus"):
            st.session_state[value_key] = min(maxv, st.session_state[value_key] + step)
            st.session_state[key_counter] += 1

    cfg[key] = st.session_state[value_key]


# ---------------------------------------------------------
# Main Input Renderer
# ---------------------------------------------------------

def render_inputs():

    if "config" not in st.session_state:
        st.session_state.config = DEFAULT_5IN.copy()

    cfg = st.session_state.config

    # Presets
    colA, colB = st.columns(2)
    with colA:
        if st.button("Load 5\" Freestyle Defaults"):
            st.session_state.config = DEFAULT_5IN.copy()
            st.experimental_rerun()

    with colB:
        if st.button("Load 65mm Tiny Whoop Defaults"):
            st.session_state.config = DEFAULT_WHOOP.copy()
            st.experimental_rerun()

    # Propeller
    with st.expander("Propeller", expanded=False):
        slider_with_buttons("Diameter (in)", 1.0, 17.0, 0.1, "prop_diameter", cfg)
        slider_with_buttons("Pitch (in)", 0.5, 8.0, 0.1, "prop_pitch", cfg)
        slider_with_buttons("Blades", 2, 8, 1, "prop_blades", cfg)
        slider_with_buttons("Prop weight (g)", 0.1, 10.0, 0.1, "prop_weight", cfg)

    # Motors
    with st.expander("Motors", expanded=False):
        slider_with_buttons("Motor KV", 500, 30000, 50, "motor_kv", cfg)
        slider_with_buttons("Stator diameter (mm)", 5, 35, 1, "motor_stator_d", cfg)
        slider_with_buttons("Stator height (mm)", 2, 15, 1, "motor_stator_h", cfg)
        slider_with_buttons("Motor weight (g)", 2, 60, 1, "motor_weight", cfg)
        slider_with_buttons("Motor Current Rating (A)", 5, 80, 1, "motor_current_rating", cfg)
        cfg["motor_count"] = st.selectbox("Motor count", [4, 6, 8, 12],
                                          index=[4, 6, 8, 12].index(cfg["motor_count"]))

    # Battery
    with st.expander("Battery", expanded=False):
        slider_with_buttons("Cells (S)", 1, 8, 1, "lipo_cells", cfg)
        slider_with_buttons("Capacity (mAh)", 200, 20000, 10, "lipo_capacity", cfg)
        slider_with_buttons("C rating", 20, 150, 1, "lipo_c", cfg)
        slider_with_buttons("Battery weight (g)", 5, 600, 1, "lipo_weight", cfg)
        slider_with_buttons("Battery Health (%)", 10, 100, 1, "lipo_health", cfg)

    # Frame
    with st.expander("Frame", expanded=False):
        slider_with_buttons("Frame noise (0–100)", 0, 100, 1, "frame_noise", cfg)
        slider_with_buttons("Wheelbase (mm)", 50, 500, 1, "frame_wheelbase", cfg)
        slider_with_buttons("Max prop size (in)", 1.0, 17.0, 0.1, "frame_prop_fit", cfg)
        slider_with_buttons("Frame weight (g)", 3, 300, 1, "frame_weight", cfg)

    # FC
    with st.expander("Flight Controller", expanded=False):
        cfg["fc_loop"] = st.selectbox(
            "PID loop frequency",
            [100, 200, 250, 333, 400, 500, 666, 800, 1000, 2000, 4000, 8000],
            index=[100, 200, 250, 333, 400, 500, 666, 800, 1000, 2000, 4000, 8000].index(cfg["fc_loop"])
        )
        slider_with_buttons("CPU load (%)", 10, 100, 1, "fc_cpu", cfg)
        cfg["fc_dshot"] = st.selectbox("DShot", [300, 600, 1200],
                                       index=[300, 600, 1200].index(cfg["fc_dshot"]))
        slider_with_buttons("FC weight (g)", 2, 20, 1, "fc_weight", cfg)

    # ESC
    with st.expander("ESC", expanded=False):
        slider_with_buttons("ESC Current Rating (A)", 5, 80, 1, "esc_current_rating", cfg)
        cfg["esc_pwm"] = st.selectbox(
            "PWM frequency",
            [24000, 32000, 48000, 96000, 128000, 192000],
            index=[24000, 32000, 48000, 96000, 128000, 192000].index(cfg["esc_pwm"])
        )
        cfg["esc_demag"] = st.selectbox(
            "Demag compensation",
            ["disabled", "low", "high"],
            index=["disabled", "low", "high"].index(cfg["esc_demag"])
        )
        cfg["esc_timing"] = st.selectbox(
            "Timing",
            ["low", "med-low", "med", "med-high", "high"],
            index=["low", "med-low", "med", "med-high", "high"].index(cfg["esc_timing"])
        )
        slider_with_buttons("ESC weight (g)", 2, 40, 1, "esc_weight", cfg)

    # Video
    with st.expander("Video System", expanded=False):
        slider_with_buttons("VTX power (mW)", 25, 2000, 25, "video_power", cfg)
        slider_with_buttons("Video weight (g)", 2, 50, 1, "video_weight", cfg)
        cfg["video_digital"] = st.checkbox("Digital video", cfg["video_digital"])

    # RX
    with st.expander("Radio Link", expanded=False):
        slider_with_buttons("Receiver weight (g)", 1, 20, 1, "rx_weight", cfg)
        cfg["rx_elrs"] = st.checkbox("ELRS", cfg["rx_elrs"])

    # Action Cam
    with st.expander("Action Camera", expanded=False):
        slider_with_buttons("Action cam weight (g)", 0, 200, 1, "cam_weight", cfg)

    # Payload
    with st.expander("Payload", expanded=False):
        slider_with_buttons("Payload weight (g)", 0, 2000, 5, "payload", cfg)

    # Fuzz
    with st.expander("Fuzz Calibration (Real-World Adjustment)", expanded=False):
        slider_with_buttons("Air Density Multiplier", 0.5, 1.5, 0.01, "fuzz_air", cfg)
        slider_with_buttons("Drag Multiplier", 0.5, 2.0, 0.01, "fuzz_drag", cfg)
        slider_with_buttons("Prop Thrust Multiplier", 0.5, 2.0, 0.01, "fuzz_prop", cfg)
        slider_with_buttons("Motor Torque Multiplier", 0.5, 2.0, 0.01, "fuzz_motor_torque", cfg)
        slider_with_buttons("Motor Efficiency Multiplier", 0.5, 2.0, 0.01, "fuzz_motor_eff", cfg)
        slider_with_buttons("Battery Internal Resistance Multiplier", 0.1, 5.0, 0.01, "fuzz_batt_ir", cfg)
        slider_with_buttons("ESC Loss Multiplier", 0.5, 3.0, 0.01, "fuzz_esc_loss", cfg)
        slider_with_buttons("Thermal Resistance Multiplier", 0.5, 3.0, 0.01, "fuzz_thermal_r", cfg)
        slider_with_buttons("Thermal Capacitance Multiplier", 0.5, 3.0, 0.01, "fuzz_thermal_c", cfg)

    return cfg
