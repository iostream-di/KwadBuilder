# streamlitapp.py
import json
import streamlit as st
from basekwad import (
    Propeller, Motor, LiPo, Frame, Flight_Controller,
    Electronic_Speed_Controller, Video_System,
    Radio_Link, Action_Cam, Kwad, clamp01
)

st.set_page_config(page_title="MartyMayhem's FPV Build Explorer", layout="centered")

st.title("Theoretical FPV Build Explorer")
st.write("A physics‑based quadcopter modeling tool.")


# ---------------------------------------------------------
# Default Presets
# ---------------------------------------------------------

DEFAULT_5IN = {
    "prop_diameter": 5.1,
    "prop_pitch": 4.3,
    "prop_blades": 3,
    "prop_weight": 3.5,

    "motor_kv": 1950,
    "motor_stator_d": 23,
    "motor_stator_h": 7,
    "motor_current_rating": 40,
    "motor_weight": 32,

    "lipo_cells": 6,
    "lipo_capacity": 1500,
    "lipo_c": 80,
    "lipo_weight": 190,
    "lipo_health": 100,

    "frame_noise": 20,
    "frame_wheelbase": 225,
    "frame_prop_fit": 5.1,
    "frame_weight": 120,

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
    "video_weight": 10,
    "video_digital": True,

    "rx_weight": 4,
    "rx_elrs": True,

    "cam_weight": 0,

    "motor_count": 4,
    "payload": 0,
}

DEFAULT_WHOOP = {
    "prop_diameter": 1.6,
    "prop_pitch": 0.8,
    "prop_blades": 3,
    "prop_weight": 0.3,

    "motor_kv": 19000,
    "motor_stator_d": 8,
    "motor_stator_h": 2,
    "motor_current_rating": 5,
    "motor_weight": 3,

    "lipo_cells": 1,
    "lipo_capacity": 300,
    "lipo_c": 60,
    "lipo_weight": 8,
    "lipo_health": 100,

    "frame_noise": 40,
    "frame_wheelbase": 65,
    "frame_prop_fit": 1.6,
    "frame_weight": 4,

    "fc_loop": 4000,
    "fc_cpu": 70,
    "fc_dshot": 300,
    "fc_weight": 4,

    "esc_pwm": 96000,
    "esc_demag": "low",
    "esc_timing": "med-high",
    "esc_weight": 3,
    "esc_current_rating": 12,


    "video_power": 25,
    "video_weight": 3,
    "video_digital": False,

    "rx_weight": 1,
    "rx_elrs": True,

    "cam_weight": 0,

    "motor_count": 4,
    "payload": 0,
}


# ---------------------------------------------------------
# Session State
# ---------------------------------------------------------

if "config" not in st.session_state:
    st.session_state.config = DEFAULT_5IN.copy()


def load_preset(preset):
    st.session_state.config = preset.copy()
    st.experimental_rerun()


# ---------------------------------------------------------
# Preset Buttons
# ---------------------------------------------------------

colA, colB = st.columns(2)
with colA:
    if st.button("Load 5\" Freestyle Defaults"):
        load_preset(DEFAULT_5IN)

with colB:
    if st.button("Load 65mm Tiny Whoop Defaults"):
        load_preset(DEFAULT_WHOOP)


cfg = st.session_state.config


# ---------------------------------------------------------
# Helper: Slider + Buttons
# ---------------------------------------------------------

def slider_with_buttons(label, minv, maxv, step, key):
    value_key = f"{key}_value"
    key_counter = f"{key}_counter"

    if value_key not in st.session_state:
        st.session_state[value_key] = cfg[key]
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
# UI Sections
# ---------------------------------------------------------

with st.expander("Propeller", expanded=False):
    slider_with_buttons("Diameter (in)", 1.0, 17.0, 0.1, "prop_diameter")
    slider_with_buttons("Pitch (in)", 0.5, 8.0, 0.1, "prop_pitch")
    slider_with_buttons("Blades", 2, 8, 1, "prop_blades")
    slider_with_buttons("Prop weight (g)", 0.1, 10.0, 0.1, "prop_weight")

with st.expander("Motors", expanded=False):
    slider_with_buttons("Motor KV", 500, 30000, 50, "motor_kv")
    slider_with_buttons("Stator diameter (mm)", 5, 35, 1, "motor_stator_d")
    slider_with_buttons("Stator height (mm)", 2, 15, 1, "motor_stator_h")
    slider_with_buttons("Motor weight (g)", 2, 60, 1, "motor_weight")
    slider_with_buttons("Motor Current Rating (A)", 5, 80, 1, "motor_current_rating")
    cfg["motor_count"] = st.selectbox("Motor count", [4, 6, 8, 12],
                                      index=[4, 6, 8, 12].index(cfg["motor_count"]))

with st.expander("Battery", expanded=False):
    slider_with_buttons("Cells (S)", 1, 8, 1, "lipo_cells")
    slider_with_buttons("Capacity (mAh)", 200, 20000, 10, "lipo_capacity")
    slider_with_buttons("C rating", 20, 150, 1, "lipo_c")
    slider_with_buttons("Battery weight (g)", 5, 600, 1, "lipo_weight")
    slider_with_buttons("Battery Health (%)", 10, 100, 1, "lipo_health")

with st.expander("Frame", expanded=False):
    slider_with_buttons("Frame noise (0–100)", 0, 100, 1, "frame_noise")
    slider_with_buttons("Wheelbase (mm)", 50, 500, 1, "frame_wheelbase")
    slider_with_buttons("Max prop size (in)", 1.0, 17.0, 0.1, "frame_prop_fit")
    slider_with_buttons("Frame weight (g)", 3, 300, 1, "frame_weight")

with st.expander("Flight Controller", expanded=False):
    cfg["fc_loop"] = st.selectbox(
        "PID loop frequency",
        [100, 200, 250, 333, 400, 500, 666, 800, 1000, 2000, 4000, 8000],
        index=[100, 200, 250, 333, 400, 500, 666, 800, 1000, 2000, 4000, 8000].index(cfg["fc_loop"])
    )
    slider_with_buttons("CPU load (%)", 10, 100, 1, "fc_cpu")
    cfg["fc_dshot"] = st.selectbox("DShot", [300, 600, 1200],
                                   index=[300, 600, 1200].index(cfg["fc_dshot"]))
    slider_with_buttons("FC weight (g)", 2, 20, 1, "fc_weight")

with st.expander("ESC", expanded=False):
    slider_with_buttons("ESC Current Rating (A)", 5, 80, 1, "esc_current_rating")
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
    slider_with_buttons("ESC weight (g)", 2, 40, 1, "esc_weight")

with st.expander("Video System", expanded=False):
    slider_with_buttons("VTX power (mW)", 25, 2000, 25, "video_power")
    slider_with_buttons("Video weight (g)", 2, 50, 1, "video_weight")
    cfg["video_digital"] = st.checkbox("Digital video", cfg["video_digital"])

with st.expander("Radio Link", expanded=False):
    slider_with_buttons("Receiver weight (g)", 1, 20, 1, "rx_weight")
    cfg["rx_elrs"] = st.checkbox("ELRS", cfg["rx_elrs"])

with st.expander("Action Camera", expanded=False):
    slider_with_buttons("Action cam weight (g)", 0, 200, 1, "cam_weight")

with st.expander("Payload", expanded=False):
    slider_with_buttons("Payload weight (g)", 0, 2000, 5, "payload")


# ---------------------------------------------------------
# Build Kwad Object
# ---------------------------------------------------------

prop = Propeller(cfg["prop_diameter"], cfg["prop_pitch"], cfg["prop_blades"], cfg["prop_weight"])
motors = [
    Motor(
        cfg["motor_stator_h"],
        cfg["motor_stator_d"],
        cfg["motor_kv"],
        cfg["motor_weight"],
        prop,
        current_rating=cfg["motor_current_rating"]
    )
    for _ in range(cfg["motor_count"])
]


lipo = LiPo(
    cfg["lipo_cells"],
    cfg["lipo_capacity"],
    cfg["lipo_c"],
    cfg["lipo_weight"],
    hv=False,
    health=cfg["lipo_health"] / 100.0
)
frame = Frame(cfg["frame_noise"], cfg["frame_wheelbase"], cfg["frame_prop_fit"], cfg["frame_weight"])
fc = Flight_Controller(cfg["fc_loop"], cfg["fc_cpu"], cfg["fc_dshot"], cfg["fc_weight"])
esc = Electronic_Speed_Controller(
    cfg["esc_pwm"],
    cfg["esc_demag"],
    cfg["esc_timing"],
    cfg["esc_weight"],
    current_rating=cfg["esc_current_rating"]
)
video = Video_System(cfg["video_power"], cfg["video_weight"], cfg["video_digital"])
rx = Radio_Link(cfg["rx_weight"], cfg["rx_elrs"])
cam = Action_Cam(cfg["cam_weight"])

quad = Kwad()
quad.motors = motors
quad.lipo = lipo
quad.frame = frame
quad.fc = fc
quad.esc = esc
quad.video = video
quad.rx = rx
quad.action_cam = cam
quad.payload = cfg["payload"]


# ---------------------------------------------------------
# Metrics
# ---------------------------------------------------------

st.subheader("Performance Metrics")

col1, col2 = st.columns(2)

with col1:
    st.metric("AUW", f"{quad.auw():.0f} g")
    st.metric("Max Thrust", f"{quad.max_thrust():.0f} g")
    st.metric("TWR", f"{quad.max_twr():.2f} : 1")
    st.metric("Max Current", f"{quad.max_current():.1f} A")

with col2:
    st.metric("Cruise Current", f"{quad.flight_profile_currents()['Cruise']:.1f} A")
    st.metric("Battery Safe Current", f"{quad.lipo.safe_current:.1f} A")
    st.metric("Flight Time (Cruise)", f"{quad.flight_time():.1f} min")
    st.metric("Voltage Sag", f"{quad.voltage_sag() * 100:.1f} %")


# ---------------------------------------------------------
# Flight Time Breakdown
# ---------------------------------------------------------

with st.expander("Flight Time Breakdown", expanded=False):
    profiles = quad.flight_profile_currents()
    modes = ["Loitering", "Cruise", "Freestyle", "Racing", "Full Throttle"]

    rows_mode = []
    rows_current = []
    rows_time = []

    for mode in modes:
        amps = profiles.get(mode, 0.0)
        minutes = quad.flight_time_profile(mode)
        rows_mode.append(mode)
        rows_current.append(f"{amps:.1f} A")
        rows_time.append(f"{minutes:.1f} min")

    st.table({
        "Mode": rows_mode,
        "Current Draw": rows_current,
        "Flight Time": rows_time,
    })


# ---------------------------------------------------------
# Heat / Stress Bars
# ---------------------------------------------------------

def heat_bar(label, value):
    pct = int(clamp01(value) * 100)
    pos = pct
    html = f"""
    <div style="margin-bottom:8px;">
      <div style="font-weight:600; margin-bottom:2px;">{label}</div>
      <div style="width: 100%; height: 22px; border-radius: 11px;
           background: linear-gradient(90deg, #7FDBFF 0%, #FFD700 50%, #FF4136 100%);
           position: relative;">
        <div style="position: absolute; top: -4px; left: calc({pos}% - 5px);
                    width: 10px; height: 30px; background: black; border-radius: 3px;">
        </div>
      </div>
      <div style="margin-top:2px; font-size:0.85rem;">{pct}%</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


st.subheader("Thermal & Reliability Stress")

heat_bar("FC Stress", quad.overstressed_fc())
heat_bar("ESC Stress", quad.overstressed_esc())
heat_bar("Motor Stress", quad.overstressed_motor())
heat_bar("Desync Risk", quad.overstressed_desync())
heat_bar("Voltage Sag Severity", quad.overstressed_voltage_sag())
heat_bar("Overall Stress", quad.overstressed_overall())


# ---------------------------------------------------------
# Build Style
# ---------------------------------------------------------

st.subheader("Build Style Classification")
st.write(f"**{quad.build_style()}**")


# ---------------------------------------------------------
# Import / Export (Collapsible)
# ---------------------------------------------------------

with st.expander("Build Profile I/O", expanded=False):
    export_json = json.dumps(cfg, indent=2)
    st.download_button("Download Build JSON", export_json, "kwad_build.json", "application/json")

    uploaded = st.file_uploader("Import Build JSON", type=["json"])
    if uploaded:
        try:
            data = json.load(uploaded)
            st.session_state.config = data
            st.success("Build imported successfully.")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Failed to import JSON: {e}")


# ---------------------------------------------------------
# FPV Theory Section (Fully Populated)
# ---------------------------------------------------------

with st.expander("FPV Theory, Math & Community Reference", expanded=False):

    st.markdown("## Motor Physics")

    st.latex(r"RPM_{no\_load} = KV \cdot V")
    st.latex(r"RPM_{loaded} \approx 0.78 \cdot RPM_{no\_load}")
    st.latex(r"\tau \propto V_{stator} = \pi \cdot \left(\frac{D}{2}\right)^2 \cdot H")

    st.write("""
    - KV determines RPM per volt.
    - Loaded RPM is typically ~78% of no‑load RPM.
    - Torque scales with stator volume (diameter × height).
    - Higher KV → more RPM, less torque.
    - Lower KV → more torque, less RPM.
    """)

    st.markdown("## Propeller Physics")

    st.latex(r"A_{disk} = \pi \left(\frac{D}{2}\right)^2")
    st.latex(r"Thrust \propto A_{disk}^{1.15} \cdot Pitch^{0.75} \cdot RPM^{1.15}")
    st.latex(r"Pitch\ Speed = Pitch \cdot \frac{RPM}{60}")

    st.write("""
    - Disk area determines thrust potential.
    - Higher pitch increases speed but also current draw.
    - More blades increase thrust but reduce efficiency.
    - Small props are inefficient at high thrust.
    """)

    st.markdown("## Battery Physics")

    st.latex(r"V_{nominal} = 3.8 \cdot S")
    st.latex(r"I_{safe} = C \cdot Capacity_{Ah}")
    st.latex(r"V_{sag} = I \cdot R_{internal}")

    st.write("""
    - Voltage sag reduces RPM and thrust.
    - Higher C rating reduces sag.
    - Larger packs sag less but weigh more.
    """)

    st.markdown("## ESC Physics")

    st.write("""
    - Higher PWM frequency increases smoothness but can increase heat.
    - Demag compensation prevents desync under high load.
    - Timing affects torque and efficiency:
        - Low timing = efficient, cooler
        - High timing = more torque, more heat
    """)

    st.markdown("## Flight Controller Physics")

    st.latex(r"Loop\ Frequency = \frac{1}{Loop\ Time}")
    st.write("""
    - Higher loop frequency improves responsiveness.
    - Higher CPU load increases FC heat.
    - Frame noise affects filtering load.
    - DShot rate affects motor update speed.
    """)

    st.markdown("## Build Style Definitions")

    st.write("""
    - **Whoop:** 1.6–2.0" props, <80g AUW  
    - **Toothpick:** 2.5–3" props, <120g AUW, TWR > 4  
    - **Freestyle:** 3–5" props, 200–800g AUW, TWR 4–8  
    - **Racing:** 5" props, 400–600g AUW, TWR 8–12  
    - **Long Range:** 6–7" props, TWR 2–4, flight time > 10 min  
    - **Cinewhoop:** 3–3.5" props, ducts, stable flight  
    - **Kamikaze:** 7–10" props, 1–2kg AUW, 6–10 min  
    - **Utility:** 7–17" props, 1.5–4kg AUW, payload‑focused  
    """)

    st.markdown("## Community Reference Tables")

    st.write("### Typical AUW Ranges")
    st.table({
        "Build": ["Whoop", "Toothpick", "3\"", "5\" Freestyle", "5\" Racing", "7\" LR", "Utility"],
        "AUW (g)": ["20–45", "55–120", "120–200", "650–800", "430–550", "650–1100", "1500–4000+"]
    })

    st.write("### Typical TWR Ranges")
    st.table({
        "Build": ["Whoop", "Toothpick", "Freestyle", "Racing", "Long Range", "Utility"],
        "TWR": ["2–3", "4–7", "5–8", "8–12", "2–3", "1.5–3"]
    })

    st.write("### Typical RPM Ranges")
    st.table({
        "Build": ["Whoop", "Toothpick", "3\"", "5\"", "7\""],
        "Loaded RPM": ["28–45k", "32–48k", "38–48k", "28–36k", "18–26k"]
    })

    st.write("### Typical Flight Times")
    st.table({
        "Build": ["Whoop", "Toothpick", "Freestyle", "Racing", "Long Range"],
        "Flight Time": ["3–5 min", "3–6 min", "4–7 min", "1.5–3 min", "12–25 min"]
    })
