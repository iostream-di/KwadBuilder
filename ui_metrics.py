# ui_metrics.py

import streamlit as st
import physics as phys
import engine


# ---------------------------------------------------------
# Helper: Clamp
# ---------------------------------------------------------

def clamp01(x):
    return max(0.0, min(1.0, x))


# ---------------------------------------------------------
# Helper: Heat Bar Renderer
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


# ---------------------------------------------------------
# Main Metrics Renderer
# ---------------------------------------------------------

def render_metrics(cfg, kwad, perf, fuzz):

    st.subheader("Performance Metrics")

    # AUW
    auw_kg = engine.auw_kg(kwad)
    auw_g = auw_kg * 1000.0

    # Max thrust
    max_thrust_g = perf.max_thrust_total_n / phys.GRAVITY * 1000.0

    # TWR
    weight_n = auw_kg * phys.GRAVITY
    twr = perf.max_thrust_total_n / weight_n if weight_n > 0 else 0.0

    # Hover power & current
    v_nom = phys.pack_voltage_nominal(kwad.battery.cells_series, kwad.battery.chemistry)
    hover_power = perf.total_power_hover_w
    hover_current = hover_power / v_nom if v_nom > 0 else 0.0

    # Voltage sag
    v_full = phys.pack_voltage_full(kwad.battery.cells_series, kwad.battery.chemistry)
    r_pack = phys.pack_internal_resistance(kwad.battery.cells_series, kwad.battery.chemistry, fuzz)
    v_sag = phys.voltage_sag_under_load(v_full, hover_current, r_pack)
    sag_pct = (v_full - v_sag) / v_full if v_full > 0 else 0.0

    col1, col2 = st.columns(2)

    with col1:
        st.metric("AUW", f"{auw_g:.0f} g")
        st.metric("Max Thrust", f"{max_thrust_g:.0f} g")
        st.metric("TWR", f"{twr:.2f} : 1")
        st.metric("Hover Throttle", f"{perf.hover_throttle:.2f}")

    with col2:
        st.metric("Hover Power", f"{hover_power:.0f} W")
        st.metric("Hover Current", f"{hover_current:.1f} A")
        st.metric("Flight Time (Hover)", f"{perf.flight_time_min:.1f} min")
        st.metric("Voltage Sag (Hover)", f"{sag_pct * 100:.1f} %")


    # ---------------------------------------------------------
    # Flight Time Breakdown
    # ---------------------------------------------------------

    with st.expander("Flight Time Breakdown", expanded=False):

        profiles = {
            "Loitering": 0.6,
            "Cruise": 1.0,
            "Freestyle": 1.5,
            "Racing": 2.0,
            "Full Throttle": 2.5,
        }

        rows_mode = []
        rows_current = []
        rows_time = []

        energy_wh = phys.energy_wh_from_capacity(kwad.battery.capacity_mah, v_nom)

        for mode, factor in profiles.items():
            p_mode = hover_power * factor
            i_mode = p_mode / v_nom if v_nom > 0 else 0.0
            t_min = phys.ideal_flight_time_minutes(energy_wh, p_mode) if p_mode > 0 else 0.0

            rows_mode.append(mode)
            rows_current.append(f"{i_mode:.1f} A")
            rows_time.append(f"{t_min:.1f} min")

        st.table({
            "Mode": rows_mode,
            "Current Draw": rows_current,
            "Flight Time": rows_time,
        })


    # ---------------------------------------------------------
    # Stress Bars
    # ---------------------------------------------------------

    st.subheader("Thermal & Reliability Stress")

    hover_current_per_motor = hover_current / len(kwad.motors) if kwad.motors else 0.0
    safe_current = kwad.battery.c_rating * (kwad.battery.capacity_mah / 1000.0)

    fc_stress = cfg["fc_cpu"] / 100.0
    esc_stress = hover_current_per_motor / kwad.esc.continuous_current_a if kwad.esc.continuous_current_a > 0 else 0.0
    motor_stress = hover_current_per_motor / kwad.motors[0].max_current_a if kwad.motors and kwad.motors[0].max_current_a > 0 else 0.0
    batt_stress = hover_current / safe_current if safe_current > 0 else 0.0
    desync_stress = clamp01(max(esc_stress, motor_stress) * 1.1)
    overall_stress = clamp01((fc_stress + esc_stress + motor_stress + batt_stress) / 4.0)

    heat_bar("FC Stress", fc_stress)
    heat_bar("ESC Stress", esc_stress)
    heat_bar("Motor Stress", motor_stress)
    heat_bar("Desync Stress", desync_stress)
    heat_bar("Battery Stress", batt_stress)
    heat_bar("Overall Stress", overall_stress)


    # ---------------------------------------------------------
    # Build Style Classification
    # ---------------------------------------------------------

    st.subheader("Build Style Classification")

    style = "Unknown"
    d = cfg["prop_diameter"]

    if d <= 2.0 and auw_g < 80:
        style = "Whoop"
    elif d <= 3.0 and auw_g < 120 and twr > 4:
        style = "Toothpick"
    elif 3.0 <= d <= 5.2 and 200 <= auw_g <= 900 and 4 <= twr <= 8:
        style = "Freestyle"
    elif 4.8 <= d <= 5.3 and 350 <= auw_g <= 650 and twr >= 8:
        style = "Racing"
    elif 6.0 <= d <= 7.5 and twr <= 4 and perf.flight_time_min > 10:
        style = "Long Range"
    elif 2.8 <= d <= 3.5 and auw_g > 250:
        style = "Cinewhoop"
    elif d >= 7.0 and auw_g >= 1500:
        style = "Utility"

    st.write(f"**{style}**")
