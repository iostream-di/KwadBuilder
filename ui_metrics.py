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
    # Stress Bars (Racing Profile)
    # ---------------------------------------------------------

    st.subheader("Thermal & Reliability Stress")

    # Racing profile = 2.0 × hover power
    racing_power = hover_power * 2.0
    racing_current = racing_power / v_nom if v_nom > 0 else 0.0
    racing_current_per_motor = racing_current / len(kwad.motors) if kwad.motors else 0.0

    # Battery sag at racing load
    v_sag_race = phys.voltage_sag_under_load(v_full, racing_current, r_pack)
    sag_race_pct = (v_full - v_sag_race) / v_full if v_full > 0 else 0.0

    # ---------------------------------------------------------
    # FC Stress (realistic CPU model)
    # ---------------------------------------------------------

    loop_factor = cfg["fc_loop"] / 4000.0          # 1k = 0.25, 4k = 1.0
    dshot_factor = cfg["fc_dshot"] / 1200.0        # 600 = 0.5
    noise_factor = cfg["frame_noise"] / 50.0       # noisy frames = more filtering
    motor_factor = len(kwad.motors) / 4.0          # hex/octo scale

    fc_stress = (
        loop_factor * 0.40 +
        dshot_factor * 0.20 +
        noise_factor * 0.20 +
        motor_factor * 0.20
    )
    fc_stress = clamp01(fc_stress)

    # ---------------------------------------------------------
    # ESC Stress (prop + motor + ESC + battery @ racing load)
    # ---------------------------------------------------------

    timing_factor = {"low": 0.9, "med": 1.0, "high": 1.1}[cfg["esc_timing"]]
    pwm_factor = min(cfg["esc_pwm"] / 48000, 1.2)

    esc_stress = racing_current_per_motor / kwad.esc.continuous_current_a
    esc_stress *= timing_factor * pwm_factor
    esc_stress = clamp01(esc_stress)

    # ---------------------------------------------------------
    # Motor Stress (battery + ESC + motor limits + props @ racing)
    # ---------------------------------------------------------

    kv_factor = kwad.motors[0].kv_rpm_per_v / 1950.0
    prop_factor = (cfg["prop_diameter"] / 5.1) * (cfg["prop_pitch"] / 4.3)

    motor_stress = racing_current_per_motor / kwad.motors[0].max_current_a
    motor_stress *= kv_factor * prop_factor
    motor_stress = clamp01(motor_stress)

    # ---------------------------------------------------------
    # Desync Stress (KV + pitch + demag + timing + sag @ racing)
    # ---------------------------------------------------------

    demag_factor = {"high": 0.7, "med": 1.0, "low": 1.3}[cfg["esc_demag"]]
    timing_desync_factor = {"low": 1.2, "med": 1.0, "high": 0.8}[cfg["esc_timing"]]

    desync_stress = racing_current_per_motor / kwad.motors[0].max_current_a
    desync_stress *= kv_factor * prop_factor
    desync_stress *= demag_factor * timing_desync_factor
    desync_stress *= (1.0 + sag_race_pct * 2.0)  # sag increases desync risk
    desync_stress = clamp01(desync_stress)

    # ---------------------------------------------------------
    # Battery Stress (props + motors + ESC + battery @ racing)
    # ---------------------------------------------------------

    safe_current = kwad.battery.c_rating * (kwad.battery.capacity_mah / 1000.0)
    batt_stress = racing_current / safe_current if safe_current > 0 else 0.0

    # IR + sag penalty
    batt_stress *= (1.0 + sag_race_pct * 2.0)

    # battery health penalty
    health_factor = 100.0 / max(cfg["lipo_health"], 1.0)
    batt_stress *= health_factor

    batt_stress = clamp01(batt_stress)

    # ---------------------------------------------------------
    # Overall Stress (average-high)
    # ---------------------------------------------------------

    stress_list = [fc_stress, esc_stress, motor_stress, desync_stress, batt_stress]

    overall_stress = max(
        0.5 * max(stress_list),
        0.5 * (sum(stress_list) / len(stress_list))
    )
    overall_stress = clamp01(overall_stress)

    # ---------------------------------------------------------
    # Render Bars
    # ---------------------------------------------------------

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
