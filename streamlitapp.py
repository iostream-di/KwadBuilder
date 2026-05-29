import streamlit as st
import math

st.set_page_config(page_title="Theoretical FPV Build Explorer", layout="centered")

st.title("🛠️ Theoretical FPV Build Explorer")
st.write("Play with sliders to get a **feel** for how a build might behave.")


# -----------------------------
# Helper functions
# -----------------------------

def nominal_voltage(s_cells: int) -> float:
    return 3.8 * s_cells


def rpm_no_load(kv: float, voltage: float) -> float:
    return kv * voltage


def rpm_loaded(no_load_rpm: float) -> float:
    return no_load_rpm * 0.78


def prop_disk_area(diameter_in: float) -> float:
    d_m = diameter_in * 0.0254
    r_m = d_m / 2
    return math.pi * r_m * r_m


def pitch_speed_mps(pitch_in: float, rpm: float) -> float:
    return pitch_in * 0.0254 * rpm / 60.0


def estimate_thrust_per_motor_g(diameter_in, pitch_in, blades, rpm, stator_d, stator_h):
    area = prop_disk_area(diameter_in)
    motor_factor = (stator_d * stator_h) / (23 * 6)
    blade_factor = 1 + (blades - 3) * 0.12
    rpm_factor = (rpm / 40000) ** 0.9

    base = 900  # tuned for 5" reference
    thrust = base * area / prop_disk_area(5.0)
    thrust *= (pitch_in / 4.5) ** 0.4
    thrust *= blade_factor
    thrust *= motor_factor
    thrust *= rpm_factor

    return max(thrust, 10.0)


def estimate_current_per_motor_a(thrust_g: float, efficiency_factor: float = 0.8) -> float:
    return (thrust_g / 150.0) ** 1.25 / efficiency_factor


def estimate_flight_time_min(capacity_mah, avg_current_a):
    if avg_current_a <= 0:
        return 0.0
    usable_mah = capacity_mah * 0.8
    return (usable_mah / 1000.0) / avg_current_a * 60.0


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def heat_from_current(load_current, safe_current):
    if safe_current <= 0:
        return 1.0
    ratio = load_current / safe_current
    if ratio <= 0.5:
        return 0.3 * (ratio / 0.5)
    elif ratio <= 1.0:
        return 0.3 + 0.4 * ((ratio - 0.5) / 0.5)
    else:
        return clamp01(0.7 + 0.3 * ((ratio - 1.0) / 0.5))


def build_style_label(twr, flight_time, prop_size, auw):
    if twr < 2:
        adjective = "Mild"
    elif twr < 4:
        adjective = "Average"
    elif twr < 7:
        adjective = "Aggressive"
    else:
        adjective = "Extreme"

    if prop_size <= 2.5 and auw < 80:
        style = "Whoop"
    elif prop_size <= 3.5 and auw < 200:
        style = "Freestyle"
    elif prop_size <= 4.5 and flight_time > 8:
        style = "Cinelog"
    elif prop_size >= 5 and flight_time > 10:
        style = "Long Range"
    elif prop_size >= 5 and twr > 6:
        style = "Racing"
    else:
        style = "General Purpose"

    return f"{adjective} {style}"


def heat_color(heat_0_1: float) -> str:
    if heat_0_1 <= 0.5:
        t = heat_0_1 / 0.5
        c1 = (0x7F, 0xDB, 0xFF)
        c2 = (0xFF, 0xD7, 0x00)
    else:
        t = (heat_0_1 - 0.5) / 0.5
        c1 = (0xFF, 0xD7, 0x00)
        c2 = (0xFF, 0x41, 0x36)

    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return f"#{r:02X}{g:02X}{b:02X}"


def colored_percentage(label, value):
    pct = int(value * 100)
    if pct < 40:
        color = "🟦"
    elif pct < 70:
        color = "🟨"
    else:
        color = "🟥"
    st.metric(label, f"{color} {pct}%")


# -----------------------------
# UI – sliders (one per line)
# -----------------------------

st.subheader("Build parameters")

prop_size = st.slider("Prop size (inches)", 1.0, 8.0, 5.0, 0.5)
prop_pitch = st.slider("Prop pitch (inches)", 0.8, 8.0, 4.5, 0.1)
prop_blades = st.slider("Prop blades", 2, 8, 3, 1)
motor_kv = st.slider("Motor KV", 300, 30000, 1950, 50)
stator_d = st.slider("Motor stator diameter (mm)", 7, 52, 23, 1)
stator_h = st.slider("Motor stator height (mm)", 2, 15, 6, 1)
lipo_s = st.slider("LiPo cells (S)", 1, 8, 6, 1)
lipo_capacity = st.slider("LiPo capacity (mAh)", 260, 20000, 1500, 10)
lipo_c = st.slider("LiPo C rating", 20, 150, 80, 1)
auw = st.slider("All-up weight (g)", 15, 2000, 700, 5)
motor_count = st.selectbox("Motor count", [4, 6, 8, 12], index=0)


# -----------------------------
# Computations
# -----------------------------

V = nominal_voltage(lipo_s)
rpm_nl = rpm_no_load(motor_kv, V)
rpm_ld = rpm_loaded(rpm_nl)

thrust_per_motor_g = estimate_thrust_per_motor_g(
    prop_size, prop_pitch, prop_blades, rpm_ld, stator_d, stator_h
)
total_thrust_g = thrust_per_motor_g * motor_count
twr = total_thrust_g / auw if auw > 0 else 0.0

max_payload_g = max(total_thrust_g / 2.0 - auw, 0.0)

max_speed_mps = pitch_speed_mps(prop_pitch, rpm_ld)
max_speed_kph = max_speed_mps * 3.6

current_per_motor_a = estimate_current_per_motor_a(thrust_per_motor_g)
total_current_a = current_per_motor_a * motor_count

cruise_current_a = total_current_a * 0.35
flight_time_min = estimate_flight_time_min(lipo_capacity, cruise_current_a)

battery_safe_a = (lipo_capacity / 1000.0) * lipo_c

fc_heat = clamp01(0.1 + 0.2 * (lipo_s - 1) / 7 + 0.2 * (motor_kv / 30000))
esc_safe_a = battery_safe_a / motor_count
esc_heat = heat_from_current(current_per_motor_a, esc_safe_a)
motor_heat = heat_from_current(current_per_motor_a, 25.0)
desync_potential = clamp01(0.2 + 0.4 * (motor_kv / 30000) + 0.2 * (prop_pitch / 8.0))

overall_heat = clamp01((fc_heat + esc_heat + motor_heat + desync_potential) / 4.0)


# -----------------------------
# Output
# -----------------------------

st.subheader("Theoretical metrics")

colA, colB = st.columns(2)

with colA:
    st.metric("Max speed", f"{max_speed_kph:0.1f} km/h")
    st.metric("Total max thrust", f"{total_thrust_g:0.0f} g")
    st.metric("Thrust-to-weight ratio", f"{twr:0.2f} : 1")
    st.metric("Max payload (TWR≈2)", f"{max_payload_g:0.0f} g")

with colB:
    st.metric("Total max current", f"{total_current_a:0.1f} A")
    st.metric("Cruise current (est.)", f"{cruise_current_a:0.1f} A")
    st.metric("Battery safe current", f"{battery_safe_a:0.1f} A")
    st.metric("Expected flight time", f"{flight_time_min:0.1f} min")


st.subheader("Thermal & reliability potentials")

colH1, colH2, colH3, colH4 = st.columns(4)

with colH1:
    colored_percentage("FC overheat", fc_heat)

with colH2:
    colored_percentage("ESC overheat", esc_heat)

with colH3:
    colored_percentage("Motor overheat", motor_heat)

with colH4:
    colored_percentage("Desync risk", desync_potential)


# -----------------------------
# Build style & HEAT bar
# -----------------------------

style_label = build_style_label(twr, flight_time_min, prop_size, auw)
st.subheader("Build style")
st.write(f"**Theoretical feel:** `{style_label}`")

st.write("**Overall HEAT rating**")

heat_percent = int(overall_heat * 100)
indicator_pos = heat_percent

heat_bar_html = f"""
<div style="width: 100%; height: 28px; border-radius: 14px;
     background: linear-gradient(90deg, #7FDBFF 0%, #FFD700 50%, #FF4136 100%);
     position: relative;">
  <div style="position: absolute; top: -6px; left: calc({indicator_pos}% - 6px);
              width: 12px; height: 40px; background: black; border-radius: 3px;">
  </div>
</div>
<p style="margin-top: 4px; font-size: 0.9rem;">Heat: <b>{heat_percent}%</b></p>
"""

st.markdown(heat_bar_html, unsafe_allow_html=True)
