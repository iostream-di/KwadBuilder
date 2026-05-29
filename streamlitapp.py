import math
import json
import streamlit as st

st.set_page_config(page_title="Theoretical FPV Build Explorer", layout="centered")

st.title("Theoretical FPV Build Explorer")
st.write("Play with sliders and theory to explore how an FPV build might behave.")


# -----------------------------
# Helpers – core math
# -----------------------------

def nominal_voltage(s_cells: int) -> float:
    return 3.8 * s_cells


def pack_internal_resistance_ohm(s_cells: int, capacity_mah: int) -> float:
    capacity_ah = capacity_mah / 1000.0
    base_per_cell = 0.010  # 10 mΩ per cell baseline
    scale = 1.0 / max(capacity_ah, 0.5)
    return s_cells * base_per_cell * scale


def loaded_voltage(v_nom: float, current_a: float, r_pack: float) -> float:
    sag = current_a * r_pack
    return max(v_nom - sag, v_nom * 0.7)


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


def motor_kt_nm_per_a(kv_rpm_per_v: float) -> float:
    if kv_rpm_per_v <= 0:
        return 0.0
    return 60.0 / (2 * math.pi * kv_rpm_per_v)


def prop_inertia_relative(diameter_in: float, pitch_in: float, blades: int) -> float:
    area = prop_disk_area(diameter_in)
    return area * pitch_in * blades


def esc_thermal_response(load_current_a: float, esc_rating_a: float) -> float:
    if esc_rating_a <= 0:
        return 1.0
    ratio = (load_current_a ** 2) / (esc_rating_a ** 2)
    return clamp01(0.4 * ratio)


def build_style_label(twr, flight_time, prop_size, auw, max_payload_g):
    if twr < 2:
        adjective = "Mild"
    elif twr < 4:
        adjective = "Average"
    elif twr < 7:
        adjective = "Aggressive"
    else:
        adjective = "Extreme"

    # Toothpick
    if prop_size <= 3.0 and auw < 120 and twr > 4:
        style = "Toothpick"
    # Whoop
    elif prop_size <= 2.5 and auw < 80:
        style = "Whoop"
    # Kamikaze: 7–10", 1–2 kg AUW, 1–2 kg payload, 6–10 min
    elif 7.0 <= prop_size <= 10.0 and 1000 <= auw <= 2000 and 1000 <= max_payload_g <= 2000 and 6 <= flight_time <= 10:
        style = "Kamikaze"
    # Utility: 7–17", heavy AUW, heavy payload, long flight time
    elif 7.0 <= prop_size <= 17.0 and auw >= 1200 and max_payload_g >= 1500 and flight_time >= 12:
        style = "Utility"
    # Freestyle
    elif 3.0 <= prop_size <= 5.1 and 200 <= auw <= 800 and 4 <= twr <= 8:
        style = "Freestyle"
    # Racing
    elif abs(prop_size - 5.0) < 0.2 and 400 <= auw <= 600 and twr >= 8:
        style = "Racing"
    # Cinelog
    elif 3.0 <= prop_size <= 4.5 and 180 <= auw <= 350 and flight_time > 8 and twr < 4:
        style = "Cinelog"
    # Long Range
    elif prop_size >= 6.0 and 2 <= twr <= 4 and flight_time > 10:
        style = "Long Range"
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
        color = "#2E86DE"
    elif pct < 70:
        color = "#F1C40F"
    else:
        color = "#E74C3C"
    st.markdown(
        f"**{label}:** "
        f"<span style='color:{color}; font-weight:bold;'>{pct}%</span>",
        unsafe_allow_html=True,
    )


# -----------------------------
# Session state & defaults
# -----------------------------

PROP_SIZE_OPTIONS = [
    1.6, 1.8, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5,
    5.0, 5.1, 5.5, 6.0, 6.5, 7.0, 8.0, 9.0,
    10.0, 12.0, 13.0, 15.0, 17.0
]

DEFAULT_BUILD = {
    "prop_size": 5.0,
    "prop_pitch": 4.5,
    "prop_blades": 3,
    "motor_kv": 1950,
    "stator_d": 23,
    "stator_h": 6,
    "lipo_s": 6,
    "lipo_capacity": 1500,
    "lipo_c": 80,
    "auw": 700,
    "motor_count": 4,
}

if "build" not in st.session_state:
    st.session_state.build = DEFAULT_BUILD.copy()


# -----------------------------
# UI – sliders (one per line)
# -----------------------------

st.subheader("Build parameters")

b = st.session_state.build

# Ensure prop size is valid; if not, snap to nearest option
if b["prop_size"] not in PROP_SIZE_OPTIONS:
    b["prop_size"] = min(PROP_SIZE_OPTIONS, key=lambda x: abs(x - b["prop_size"]))

prop_size = st.selectbox(
    "Prop size (inches)",
    PROP_SIZE_OPTIONS,
    index=PROP_SIZE_OPTIONS.index(b["prop_size"]),
    key="prop_size",
)
prop_pitch = st.slider("Prop pitch (inches)", 0.8, 8.0, b["prop_pitch"], 0.1, key="prop_pitch")
prop_blades = st.slider("Prop blades", 2, 8, b["prop_blades"], 1, key="prop_blades")
motor_kv = st.slider("Motor KV", 300, 30000, b["motor_kv"], 50, key="motor_kv")
stator_d = st.slider("Motor stator diameter (mm)", 7, 52, b["stator_d"], 1, key="stator_d")
stator_h = st.slider("Motor stator height (mm)", 2, 15, b["stator_h"], 1, key="stator_h")
lipo_s = st.slider("LiPo cells (S)", 1, 8, b["lipo_s"], 1, key="lipo_s")
lipo_capacity = st.slider("LiPo capacity (mAh)", 260, 20000, b["lipo_capacity"], 10, key="lipo_capacity")
lipo_c = st.slider("LiPo C rating", 20, 150, b["lipo_c"], 1, key="lipo_c")
auw = st.slider("All-up weight (g)", 15, 4000, b["auw"], 5, key="auw")
motor_count = st.selectbox(
    "Motor count",
    [4, 6, 8, 12],
    index=[4, 6, 8, 12].index(b["motor_count"]),
    key="motor_count",
)

st.session_state.build.update(
    dict(
        prop_size=prop_size,
        prop_pitch=prop_pitch,
        prop_blades=prop_blades,
        motor_kv=motor_kv,
        stator_d=stator_d,
        stator_h=stator_h,
        lipo_s=lipo_s,
        lipo_capacity=lipo_capacity,
        lipo_c=lipo_c,
        auw=auw,
        motor_count=motor_count,
    )
)


# -----------------------------
# Computations (with advanced modeling)
# -----------------------------

V_nom = nominal_voltage(lipo_s)

# First pass: assume no sag to estimate current
rpm_nl_nom = rpm_no_load(motor_kv, V_nom)
rpm_ld_nom = rpm_loaded(rpm_nl_nom)
thrust_per_motor_nom = estimate_thrust_per_motor_g(
    prop_size, prop_pitch, prop_blades, rpm_ld_nom, stator_d, stator_h
)
current_per_motor_nom = estimate_current_per_motor_a(thrust_per_motor_nom)
total_current_nom = current_per_motor_nom * motor_count

# Voltage sag
r_pack = pack_internal_resistance_ohm(lipo_s, lipo_capacity)
V_loaded = loaded_voltage(V_nom, total_current_nom, r_pack)

# Recompute with sagged voltage
rpm_nl = rpm_no_load(motor_kv, V_loaded)
rpm_ld = rpm_loaded(rpm_nl)
thrust_per_motor_g = estimate_thrust_per_motor_g(
    prop_size, prop_pitch, prop_blades, rpm_ld, stator_d, stator_h
)
total_thrust_g = thrust_per_motor_g * motor_count
twr = total_thrust_g / auw if auw > 0 else 0.0

# Max payload where TWR ≈ 2
max_payload_g = max(total_thrust_g / 2.0 - auw, 0.0)

max_speed_mps = pitch_speed_mps(prop_pitch, rpm_ld)
max_speed_kph = max_speed_mps * 3.6

current_per_motor_a = estimate_current_per_motor_a(thrust_per_motor_g)
total_current_a = current_per_motor_a * motor_count

cruise_current_a = total_current_a * 0.35
flight_time_min = estimate_flight_time_min(lipo_capacity, cruise_current_a)

battery_safe_a = (lipo_capacity / 1000.0) * lipo_c

# Advanced: Kt, inertia, desync
kt = motor_kt_nm_per_a(motor_kv)
prop_inertia_rel = prop_inertia_relative(prop_size, prop_pitch, prop_blades)
desync_potential = clamp01(
    0.2
    + 0.4 * (motor_kv / 30000)
    + 0.2 * (prop_pitch / 8.0)
    + 0.2 * (prop_inertia_rel / prop_inertia_relative(5.0, 4.5, 3))
)

# FC, ESC, motor heat
fc_heat = clamp01(0.1 + 0.2 * (lipo_s - 1) / 7 + 0.2 * (motor_kv / 30000))

esc_safe_a = battery_safe_a / motor_count
esc_heat_current = heat_from_current(current_per_motor_a, esc_safe_a)
esc_heat_thermal = esc_thermal_response(current_per_motor_a, esc_safe_a)
esc_heat = clamp01(0.5 * esc_heat_current + 0.5 * esc_heat_thermal)

motor_heat = heat_from_current(current_per_motor_a, 25.0)

overall_heat = clamp01((fc_heat + esc_heat + motor_heat + desync_potential) / 4.0)


def twr_at_throttle(throttle: float) -> float:
    thrust = total_thrust_g * (throttle ** 1.1)
    return thrust / auw if auw > 0 else 0.0


twr_curve = {
    "Throttle %": [25, 50, 75, 100],
    "TWR": [twr_at_throttle(x / 100.0) for x in [25, 50, 75, 100]],
}


# -----------------------------
# Output – main metrics
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

style_label = build_style_label(twr, flight_time_min, prop_size, auw, max_payload_g)
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


# -----------------------------
# Dynamic TWR curve
# -----------------------------

with st.expander("Dynamic TWR vs throttle"):
    st.line_chart(twr_curve, x="Throttle %", y="TWR")
    st.caption("TWR is estimated at different throttle levels using a simple non-linear scaling.")


# -----------------------------
# Export build profile
# -----------------------------

st.subheader("Export build profile")

export_data = {
    "build": st.session_state.build,
    "metrics": {
        "max_speed_kph": max_speed_kph,
        "total_thrust_g": total_thrust_g,
        "twr": twr,
        "max_payload_g": max_payload_g,
        "flight_time_min": flight_time_min,
        "overall_heat": overall_heat,
        "style_label": style_label,
    },
}

export_json = json.dumps(export_data, indent=2)
st.download_button(
    label="Download current build as JSON",
    data=export_json,
    file_name="fpv_build_profile.json",
    mime="application/json",
)


# -----------------------------
# FPV THEORY & FORMULAS SECTION (expandable)
# -----------------------------

with st.expander("FPV Theory, Math & Community Reference", expanded=False):

    st.subheader("Core math formulas used")

    st.markdown("**1. Motor RPM**")
    st.latex(r"RPM_{NL} = KV \cdot V")
    st.latex(r"RPM_{L} \approx RPM_{NL} \cdot 0.78")

    st.markdown("---")
    st.markdown("**2. Pitch speed (ideal, no drag)**")
    st.latex(r"V_{pitch} = Pitch_{in} \cdot 0.0254 \cdot \frac{RPM}{60}")

    st.markdown("---")
    st.markdown("**3. Prop disk area**")
    st.latex(r"A = \pi r^2 = \pi \left(\frac{D_{in} \cdot 0.0254}{2}\right)^2")

    st.markdown("---")
    st.markdown("**4. Thrust estimation (heuristic)**")
    st.latex(r"T \propto A \cdot Pitch^{0.4} \cdot RPM^{0.9} \cdot Blades \cdot MotorFactor")

    st.markdown("---")
    st.markdown("**5. Current draw (heuristic)**")
    st.latex(r"I \propto \left(\frac{Thrust}{150\,g}\right)^{1.25}")

    st.markdown("---")
    st.markdown("**6. Battery safe current**")
    st.latex(r"I_{\text{safe}} = C \cdot Ah")

    st.markdown("---")
    st.markdown("**7. Flight time estimate**")
    st.latex(r"t = \frac{0.8 \cdot Capacity_{Ah}}{I_{\text{cruise}}} \cdot 60")

    st.markdown("---")
    st.markdown("**8. Thrust-to-weight ratio**")
    st.latex(r"TWR = \frac{T_{\text{total}}}{W}")

    st.markdown("---")
    st.markdown("**9. Motor torque constant**")
    st.latex(r"K_t \,[Nm/A] \approx \frac{60}{2\pi \cdot KV}")

    st.markdown("---")
    st.markdown("**10. Prop inertia (relative)**")
    st.latex(r"I_{\text{prop}} \propto A \cdot Pitch \cdot Blades")

    st.subheader("Community reference values")

    st.markdown("**Typical loaded RPM ranges**")
    st.table({
        "Build Type": [
            "Whoop (1–2\")",
            "Toothpick (2.5–3\")",
            "3\" Freestyle",
            "5\" Freestyle",
            "5\" Racing",
            "7\" Long Range",
            "Kamikaze",
            "Utility",
        ],
        "Prop Size": [
            "1.6–2.0\"",
            "2.5–3.0\"",
            "3.0\"",
            "5.0\"",
            "5.0\"",
            "7.0\"",
            "7–10\"",
            "7–17\"",
        ],
        "Loaded RPM Range": [
            "28,000–45,000",
            "32,000–48,000",
            "38,000–48,000",
            "28,000–36,000",
            "34,000–42,000",
            "18,000–26,000",
            "18,000–26,000",
            "12,000–22,000",
        ],
    })

    st.markdown("---")
    st.markdown("**Typical AUW by build type**")
    st.table({
        "Build Type": [
            "Whoop",
            "Toothpick",
            "3\" Freestyle",
            "5\" Freestyle",
            "5\" Racing",
            "7\" Long Range",
            "Cinewhoop (3–3.5\")",
            "Kamikaze",
            "Utility",
        ],
        "AUW Range": [
            "20–45 g",
            "55–120 g",
            "120–200 g",
            "650–800 g",
            "430–550 g",
            "650–1100 g",
            "180–320 g",
            "1000–2000 g",
            "1500–4000 g (or more)",
        ],
    })

    st.markdown("---")
    st.markdown("**Typical TWR ranges**")
    st.table({
        "Build Type": [
            "Whoop",
            "Toothpick",
            "3\" Freestyle",
            "5\" Freestyle",
            "5\" Racing",
            "Cinematic",
            "Kamikaze",
            "Utility",
            "Long Range",
        ],
        "TWR Range": [
            "2–3",
            "4–7",
            "4–6",
            "5–8",
            "8–12",
            "2–4",
            "2.5–4",
            "1.5–3",
            "2–3",
        ],
        "Notes": [
            "Flips, limited punch",
            "Very high for weight",
            "Snappy, responsive",
            "Classic “feel good” zone",
            "Brutal acceleration",
            "Smooth, stable",
            "Maneuverable with 1–2 kg payload",
            "Heavy lift, sluggish, payload-focused",
            "Efficiency-focused cruising",
        ],
    })

st.write("---")
st.caption(
    "This FPV Build Explorer is a theoretical modeling tool. "
    "All values are approximations tuned to community experience, not laboratory measurements. "
    "Use it to understand trends and relationships, then validate with real-world testing."
)
