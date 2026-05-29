"""
streamlitapp.py

Streamlit UI for Kwadstream.
This file contains NO physics and NO computation.

It:
- Collects user input
- Builds a Kwad object
- Builds a Fuzz object
- Passes both to engine.evaluate_kwad()
- Displays results
"""

import streamlit as st

from basekwad import (
    Frame, Motor, Propeller, ESC, FlightController, VTX,
    Camera, Receiver, Battery, ActionCam, Kwad
)

import physics as phys
import engine


# ============================================================
# UI Setup
# ============================================================

st.title("Kwadstream — Physics-Based FPV Simulator")


# ============================================================
# Fuzz Controls
# ============================================================

st.header("Fuzz Calibration (Real-World Adjustment)")

fuzz = phys.Fuzz(
    air_density_multiplier = st.slider("Air Density Multiplier", 0.5, 1.5, 1.0, 0.01),
    drag_multiplier = st.slider("Drag Multiplier", 0.5, 2.0, 1.0, 0.01),
    prop_thrust_multiplier = st.slider("Prop Thrust Multiplier", 0.5, 2.0, 1.0, 0.01),

    motor_torque_multiplier = st.slider("Motor Torque Multiplier", 0.5, 2.0, 1.0, 0.01),
    motor_efficiency_multiplier = st.slider("Motor Efficiency Multiplier", 0.5, 2.0, 1.0, 0.01),

    battery_ir_multiplier = st.slider("Battery Internal Resistance Multiplier", 0.1, 5.0, 1.0, 0.01),

    esc_loss_multiplier = st.slider("ESC Loss Multiplier", 0.5, 3.0, 1.0, 0.01),

    thermal_resistance_multiplier = st.slider("Thermal Resistance Multiplier", 0.5, 3.0, 1.0, 0.01),
    thermal_capacitance_multiplier = st.slider("Thermal Capacitance Multiplier", 0.5, 3.0, 1.0, 0.01),
)


# ============================================================
# Component Inputs
# ============================================================

st.header("Build Your Kwad")

# Frame
frame = Frame(
    name = st.text_input("Frame Name", "Example Frame"),
    dry_weight_g = st.number_input("Frame Weight (g)", 50.0),
    arm_length_mm = st.number_input("Arm Length (mm)", 150.0),
    motor_mount_pattern = st.text_input("Motor Mount Pattern", "16x16"),
    max_prop_size_in = st.number_input("Max Prop Size (in)", 5.0),
)

# Motor
motor = Motor(
    name = st.text_input("Motor Name", "2207 Motor"),
    kv_rpm_per_v = st.number_input("Motor Kv", 1750.0),
    stator_size = st.text_input("Stator Size", "2207"),
    weight_g = st.number_input("Motor Weight (g)", 30.0),
    resistance_ohm = st.number_input("Motor Resistance (Ω)", 0.05),
    no_load_current_a = st.number_input("No-Load Current (A)", 1.0),
    max_current_a = st.number_input("Max Current (A)", 40.0),
)

# Prop
prop = Propeller(
    name = st.text_input("Prop Name", "5x4.3x3"),
    diameter_in = st.number_input("Prop Diameter (in)", 5.0),
    pitch_in = st.number_input("Prop Pitch (in)", 4.3),
    blades = st.number_input("Prop Blades", 3),
)

# Battery
battery = Battery(
    name = st.text_input("Battery Name", "LiPo 6S 1300mAh"),
    cells_series = st.number_input("Cells (S)", 6),
    capacity_mah = st.number_input("Capacity (mAh)", 1300.0),
    weight_g = st.number_input("Battery Weight (g)", 200.0),
    c_rating = st.number_input("C Rating", 100.0),
    chemistry = phys.LIPO_DEFAULT,
)

# ESC
esc = ESC(
    name = st.text_input("ESC Name", "45A ESC"),
    continuous_current_a = st.number_input("ESC Continuous Current (A)", 45.0),
    burst_current_a = st.number_input("ESC Burst Current (A)", 55.0),
    weight_g = st.number_input("ESC Weight (g)", 15.0),
    mosfet_resistance_ohm = st.number_input("ESC MOSFET Resistance (Ω)", 0.002),
)

# FC
fc = FlightController(
    name = st.text_input("FC Name", "F7 FC"),
    weight_g = st.number_input("FC Weight (g)", 8.0),
    cpu = st.text_input("FC CPU", "F7"),
    gyro = st.text_input("FC Gyro", "BMI270"),
)

# VTX
vtx = VTX(
    name = st.text_input("VTX Name", "800mW VTX"),
    power_levels_mw = [25, 200, 400, 800],
    weight_g = st.number_input("VTX Weight (g)", 10.0),
)

# Camera
camera = Camera(
    name = st.text_input("Camera Name", "FPV Cam"),
    weight_g = st.number_input("Camera Weight (g)", 6.0),
    sensor = st.text_input("Camera Sensor", "1/3 CMOS"),
    resolution = st.text_input("Camera Resolution", "720p"),
)

# Receiver
receiver = Receiver(
    name = st.text_input("Receiver Name", "ELRS RX"),
    protocol = st.text_input("Receiver Protocol", "ELRS 2.4GHz"),
    weight_g = st.number_input("Receiver Weight (g)", 3.0),
)

# Optional Action Cam
use_action_cam = st.checkbox("Add Action Camera?")
action_cam = None
if use_action_cam:
    action_cam = ActionCam(
        name = st.text_input("Action Cam Name", "GoPro"),
        weight_g = st.number_input("Action Cam Weight (g)", 120.0),
        resolution = st.text_input("Action Cam Resolution", "4K"),
    )


# ============================================================
# Build Kwad Object
# ============================================================

kwad = Kwad(
    name="User Kwad",
    frame=frame,
    motors=[motor] * 4,
    props=[prop] * 4,
    esc=esc,
    fc=fc,
    vtx=vtx,
    camera=camera,
    receiver=receiver,
    battery=battery,
    action_cam=action_cam,
)


# ============================================================
# Run Simulation
# ============================================================

if st.button("Evaluate Kwad"):
    perf = engine.evaluate_kwad(kwad, fuzz)

    st.header("Performance Results")

    st.write(f"**Hover Throttle:** {perf.hover_throttle:.2f}")
    st.write(f"**Max Thrust (N):** {perf.max_thrust_total_n:.1f}")
    st.write(f"**Hover Power (W):** {perf.total_power_hover_w:.1f}")
    st.write(f"**Estimated Flight Time (min):** {perf.flight_time_min:.1f}")
    st.write(f"**Motor Temp Rise (°C after 60s):** {perf.motor_temp_rise_c:.1f}")
    st.write(f"**ESC Temp Rise (°C after 60s):** {perf.esc_temp_rise_c:.1f}")
