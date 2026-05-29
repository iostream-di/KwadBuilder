import streamlit as st
import math

st.set_page_config(page_title="Theoretical FPV Build Explorer", layout="centered")

st.title("Theoretical FPV Build Explorer")
st.write("Play with sliders to get a **feel** for how a build might behave.")


# -----------------------------
# Helper functions (toy models)
# -----------------------------

def nominal_voltage(s_cells: int) -> float:
    return 3.8 * s_cells  # nominal per-cell voltage


def rpm_no_load(kv: float, voltage: float) -> float:
    return kv * voltage


def rpm_loaded(no_load_rpm: float) -> float:
    return no_load_rpm * 0.78  # 78% of no-load as a rough average


def prop_disk_area(diameter_in: float) -> float:
    # diameter in inches → meters
    d_m = diameter_in * 0.0254
    r_m = d_m / 2
    return math.pi * r_m * r_m


def pitch_speed_mps(pitch_in: float, rpm: float) -> float:
    # pitch in inches, rpm → m/s
    # pitch speed (m/s) ≈ pitch(in) * 0.0254 * rpm / 60
    return pitch_in * 0.0254 * rpm / 60.0


def estimate_thrust_per_motor_g(diameter_in, pitch_in, blades, rpm, stator_d, stator_h):
    """
    Very rough heuristic thrust model.
    Scales with prop area, pitch, blades, rpm, and motor size.
    Returns grams of thrust per motor.
    """
    area = prop_disk_area(diameter_in)
    motor_factor = (stator_d * stator_h) / (14 * 7)  # normalize vs ~1407
    blade_factor = 1 + (blades - 2) * 0.12          # more blades = more thrust, less efficiency
    rpm_factor = (rpm / 40000) ** 0.9               # normalize around 40k rpm

    base = 400  # base thrust in grams for a "typical" 3-4" motor at 40k rpm
    thrust = base * area / prop_disk_area(3.0)      # scale vs 3" reference
    thrust *= (pitch_in / 3.0) ** 0.4
    thrust *= blade_factor
    thrust *= motor_factor
    thrust *= rpm_factor

    return max(thrust, 5.0)


def estimate_current_per_motor_a(thrust_g: float, efficiency_factor: float = 0.8) -> float:
    """
    Toy model: current roughly scales with thrust^1.2.
    """
    return (thrust_g / 100.0) ** 1.2 / efficiency_factor


def estimate_flight_time_min(capacity_mah, avg_current_a):
    if avg_current_a <= 0:
        return 0.0
    usable_mah = capacity_mah * 0.8  # 80% usable
    return (usable_mah / 1000.0) / avg_current_a * 60.0


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def heat_from_current(load_current, safe_current):
    if safe_current <= 0:
        return 1.0
    ratio = load_current / safe_current
    # soft knee: 0.5 → 30%, 1.0 → 70%, 1.5+ → 100%
    if ratio <= 0.5:
        return 0.3 * (ratio / 0.5)
    elif ratio <= 1.0:
        return 0.3 + 0.4 * ((ratio - 0.5) / 0.5)
    else:
        return clamp01(0.7 + 0.3 * ((ratio - 1.0) / 0.5))


def build_style_label(twr, flight_time, prop_size, auw):
    """
    Very rough classification:
    - TWR: <2, 2–4, 4–7, >7
    - Flight time: <3, 3–6, 6–12, >12
    - Prop size & AUW bias style.
    """
    # Aggression from TWR
    if twr < 2:
        adjective = "Mild"
    elif twr < 4:
        adjective = "Average"
    elif twr < 7:
        adjective = "Aggressive"
    else:
        adjective = "Extreme"

    # Style from prop size, AUW, and flight time
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
        # fallback based on TWR vs time
        if flight_time > 10:
            style = "Long Range"
        elif twr > 5:
            style = "Freestyle"
        else:
            style = "General Purpose"

    return f"{adjective} {style}"


def heat_color(heat_0_1: float) -> str:
    """
    Map 0–1 heat to hex color from light blue → yellow → red.
    """
    # 0: #7FDBFF (light blue), 0.5: #FFD700 (gold), 1: #FF4136 (red)
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


# -----------------------------
# UI – sliders
# -----------------------------

st.subheader("Build parameters")

col1, col2 = st.columns(2)

with col1:
    prop_size = st.slider("Prop size (inches)", 1.0, 8.0, 3.0, 0.5)
    prop_pitch = st.slider("Prop pitch (inches)", 0.8, 8.0, 3.0, 0.1)
    prop_blades = st.slider("Prop blades", 2, 8, 3, 1)
    motor_kv = st.slider("Motor KV", 300, 30000, 4000, 50)
    stator_d = st.slider("Motor stator diameter (mm)", 7, 52, 14, 1)
    stator_h = st.slider("Motor stator height (mm)", 2, 15, 7, 1)

with col2:
    lipo_s = st.slider("LiPo cells (S)", 1, 8, 4, 1)
    lipo_capacity = st.slider("LiPo capacity (mAh)", 260, 20000, 850, 10)
    lipo_c = st.slider("LiPo C rating", 20, 150, 75, 1)
    auw = st.slider("All-up weight (g)", 15, 2000, 250, 5)
    motor_count = st.slider("Motor count", 2, 8, 4, 1)


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

# Max payload where TWR ~ 2 (still flyable)
max_payload_g = max(total_thrust_g / 2.0 - auw, 0.0)

# Max speed from pitch speed
max_speed_mps = pitch_speed_mps(prop_pitch, rpm_ld)
max_speed_kph = max_speed_mps * 3.6

# Current draw estimates
current_per_motor_a = estimate_current_per_motor_a(thrust_per_motor_g)
total_current_a = current_per_motor_a * motor_count

# Assume cruise at ~35% of max current
cruise_current_a = total_current_a * 0.35
flight_time_min = estimate_flight_time_min(lipo_capacity, cruise_current_a)

# Battery safe current
battery_safe_a = (lipo_capacity / 1000.0) * lipo_c

# Heat potentials
fc_heat = clamp01(0.1 + 0.2 * (lipo_s - 1) / 7 + 0.2 * (motor_kv / 30000))
esc_safe_a = battery_safe_a / motor_count
esc_heat = heat_from_current(current_per_motor_a, esc_safe_a)
motor_heat = heat_from_current(current_per_motor_a, 25.0)  # assume 25A "comfortable"
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

colH1.metric("FC overheat potential", f"{fc_heat * 100:0.0f} %")
colH2.metric("ESC overheat potential", f"{esc_heat * 100:0.0f} %")
colH3.metric("Motor overheat potential", f"{motor_heat * 100:0.0f} %")
colH4.metric("Motor desync potential", f"{desync_potential * 100:0.0f} %")


# -----------------------------
# Build style & HEAT bar
# -----------------------------

style_label = build_style_label(twr, flight_time_min, prop_size, auw)
st.subheader("Build style")

st.write(f"**Theoretical feel:** `{style_label}`")

st.write("**Overall HEAT rating**")

heat_color_hex = heat_color(overall_heat)
heat_percent = int(overall_heat * 100)

heat_bar_html = f"""
<div style="
    width: 100%;
    height: 24px;
    border-radius: 12px;
    background: linear-gradient(90deg, #7FDBFF 0%, #FFD700 50%, #FF4136 100%);
    position: relative;
    overflow: hidden;
">
  <div style="
      position: absolute;
      top: 0;
      left: 0;
      height: 100%;
      width: {heat_percent}%;
      background-color: {heat_color_hex};
      opacity: 0.8;
  "></div>
</div>
<p style="margin-top: 4px; font-size: 0.9rem;">Heat: <b>{heat_percent}%</b></p>
"""

st.markdown(heat_bar_html, unsafe_allow_html=True)

st.caption(
    "All models here are intentionally approximate. Tune the coefficients to match your own logs, "
    "thrust-stand data, and gut feel."
)
