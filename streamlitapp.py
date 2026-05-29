import json
import streamlit as st
from basekwad import (
    Propeller, Motor, LiPo, Frame, Flight_Controller,
    Electronic_Speed_Controller, All_In_One, Video_System,
    Radio_Link, Action_Cam, Kwad, clamp01
)

st.set_page_config(page_title="Theoretical FPV Build Explorer", layout="centered")

st.title("Theoretical FPV Build Explorer")
st.write("A physics‑based quadcopter modeling tool powered by the BaseKwad engine.")


# ---------------------------------------------------------
# Default Presets
# ---------------------------------------------------------

DEFAULT_5IN = {
    "prop_diameter": 5.1,
    "prop_pitch": 4.3,
    "prop_blades": 3,
    "prop_weight": 3.5,

    "motor_kv": 1950,
    "motor_stator_h": 7,
    "motor_stator_d": 23,
    "motor_weight": 32,

    "lipo_cells": 6,
    "lipo_capacity": 1500,
    "lipo_c": 80,
    "lipo_weight": 190,

    "frame_noise": 20,
    "frame_wheelbase": 225,
    "frame_prop_fit": 5.1,
    "frame_weight": 120,

    "fc_loop": 1000,
    "fc_cpu": 60,
    "fc_dshot": 600,
    "fc_weight": 8,

    "esc_pwm": 48000,
    "esc_demag": "disabled",
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
    "motor_stator_h": 2,
    "motor_stator_d": 8,
    "motor_weight": 3,

    "lipo_cells": 1,
    "lipo_capacity": 300,
    "lipo_c": 60,
    "lipo_weight": 8,

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
# UI – Preset Buttons
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
# UI – Component Inputs
# ---------------------------------------------------------

st.subheader("Propeller")

cfg["prop_diameter"] = st.slider("Diameter (in)", 1.0, 17.0, cfg["prop_diameter"], 0.1)
cfg["prop_pitch"] = st.slider("Pitch (in)", 0.5, 8.0, cfg["prop_pitch"], 0.1)
cfg["prop_blades"] = st.slider("Blades", 2, 8, cfg["prop_blades"])
cfg["prop_weight"] = st.slider("Prop weight (g)", 0.1, 10.0, cfg["prop_weight"], 0.1)

st.subheader("Motors")

cfg["motor_kv"] = st.slider("Motor KV", 500, 30000, cfg["motor_kv"], 50)
cfg["motor_stator_h"] = st.slider("Stator height (mm)", 2, 15, cfg["motor_stator_h"])
cfg["motor_stator_d"] = st.slider("Stator diameter (mm)", 5, 35, cfg["motor_stator_d"])
cfg["motor_weight"] = st.slider("Motor weight (g)", 2, 60, cfg["motor_weight"])
cfg["motor_count"] = st.selectbox("Motor count", [4, 6, 8, 12], index=[4,6,8,12].index(cfg["motor_count"]))

st.subheader("Battery")

cfg["lipo_cells"] = st.slider("Cells (S)", 1, 8, cfg["lipo_cells"])
cfg["lipo_capacity"] = st.slider("Capacity (mAh)", 200, 20000, cfg["lipo_capacity"], 10)
cfg["lipo_c"] = st.slider("C rating", 20, 150, cfg["lipo_c"])
cfg["lipo_weight"] = st.slider("Battery weight (g)", 5, 600, cfg["lipo_weight"])

st.subheader("Frame")

cfg["frame_noise"] = st.slider("Frame noise (0–100)", 0, 100, cfg["frame_noise"])
cfg["frame_wheelbase"] = st.slider("Wheelbase (mm)", 50, 500, cfg["frame_wheelbase"])
cfg["frame_prop_fit"] = st.slider("Max prop size (in)", 1.0, 17.0, cfg["frame_prop_fit"], 0.1)
cfg["frame_weight"] = st.slider("Frame weight (g)", 3, 300, cfg["frame_weight"])

st.subheader("Flight Controller")

cfg["fc_loop"] = st.selectbox("PID loop frequency", [100,200,250,333,400,500,666,800,1000,2000,4000,8000],
                              index=[100,200,250,333,400,500,666,800,1000,2000,4000,8000].index(cfg["fc_loop"]))
cfg["fc_cpu"] = st.slider("CPU load (%)", 10, 100, cfg["fc_cpu"])
cfg["fc_dshot"] = st.selectbox("DShot", [300, 600, 1200], index=[300,600,1200].index(cfg["fc_dshot"]))
cfg["fc_weight"] = st.slider("FC weight (g)", 2, 20, cfg["fc_weight"])

st.subheader("ESC")

cfg["esc_pwm"] = st.selectbox("PWM frequency", [24000,32000,48000,96000,128000,192000],
                              index=[24000,32000,48000,96000,128000,192000].index(cfg["esc_pwm"]))
cfg["esc_demag"] = st.selectbox("Demag compensation", ["disabled","low","high"],
                                index=["disabled","low","high"].index(cfg["esc_demag"]))
cfg["esc_timing"] = st.selectbox("Timing", ["low","med-low","med","med-high","high"],
                                 index=["low","med-low","med","med-high","high"].index(cfg["esc_timing"]))
cfg["esc_weight"] = st.slider("ESC weight (g)", 2, 40, cfg["esc_weight"])

st.subheader("Video System")

cfg["video_power"] = st.slider("VTX power (mW)", 25, 2000, cfg["video_power"])
cfg["video_weight"] = st.slider("Video weight (g)", 2, 50, cfg["video_weight"])
cfg["video_digital"] = st.checkbox("Digital video", cfg["video_digital"])

st.subheader("Radio Link")

cfg["rx_weight"] = st.slider("Receiver weight (g)", 1, 20, cfg["rx_weight"])
cfg["rx_elrs"] = st.checkbox("ELRS", cfg["rx_elrs"])

st.subheader("Action Camera")

cfg["cam_weight"] = st.slider("Action cam weight (g)", 0, 200, cfg["cam_weight"])

st.subheader("Payload")

cfg["payload"] = st.slider("Payload weight (g)", 0, 2000, cfg["payload"], 5)


# ---------------------------------------------------------
# Build Kwad Object
# ---------------------------------------------------------

prop = Propeller(cfg["prop_diameter"], cfg["prop_pitch"], cfg["prop_blades"], cfg["prop_weight"])
motors = [Motor(cfg["motor_stator_h"], cfg["motor_stator_d"], cfg["motor_kv"], cfg["motor_weight"], prop)
          for _ in range(cfg["motor_count"])]

lipo = LiPo(cfg["lipo_cells"], cfg["lipo_capacity"], cfg["lipo_c"], cfg["lipo_weight"])
frame = Frame(cfg["frame_noise"], cfg["frame_wheelbase"], cfg["frame_prop_fit"], cfg["frame_weight"])
fc = Flight_Controller(cfg["fc_loop"], cfg["fc_cpu"], cfg["fc_dshot"], cfg["fc_weight"])
esc = Electronic_Speed_Controller(cfg["esc_pwm"], cfg["esc_demag"], cfg["esc_timing"], cfg["esc_weight"])
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
    st.metric("Cruise Current", f"{quad.cruise_current():.1f} A")
    st.metric("Battery Safe Current", f"{quad.batt_safe_current():.1f} A")
    st.metric("Flight Time", f"{quad.flight_time():.1f} min")
    st.metric("Voltage Sag", f"{quad.voltage_sag()*100:.1f} %")


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
# Import / Export
# ---------------------------------------------------------

st.subheader("Build Profile I/O")

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
# Theory Section
# ---------------------------------------------------------

with st.expander("FPV Theory, Math & Community Reference"):
    st.write("This section mirrors the formulas and reference tables from the BaseKwad engine.")
    st.write("Use it to understand how the model works internally.")
