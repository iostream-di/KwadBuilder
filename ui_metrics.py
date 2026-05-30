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

    # Voltage sag (hover)
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
    # Flight Time Breakdown (physics-derived)
    # ---------------------------------------------------------

    with st.expander("Flight Time Breakdown", expanded=False):

        rows_mode = []
        rows_current = []
        rows_time = []

        energy_wh = phys.energy_wh_from_capacity(kwad.battery.capacity_mah, v_nom)

        # Real full-throttle from engine
        ft_current = perf.full_throttle_current_a
        ft_power = perf.full_throttle_power_w

        # Derive a realistic racing current (~75% of full throttle)
        racing_current = ft_current * 0.75
        racing_power = racing_current * v_nom if v_nom > 0 else 0.0

        # Loitering: light load below hover
        loiter_current = hover_current * 0.6
        loiter_power = loiter_current * v_nom if v_nom > 0 else 0.0

        # Cruise: hover
        cruise_current = hover_current
        cruise_power = hover_power

        # Freestyle: mid between hover and racing
        freestyle_current = 0.5 * (hover_current + racing_current)
        freestyle_power = freestyle_current * v_nom if v_nom > 0 else 0.0

        # Full throttle: from engine
        full_current = ft_current
        full_power = ft_power

        modes = [
            ("Loitering", loiter_current, loiter_power),
            ("Cruise", cruise_current, cruise_power),
            ("Freestyle", freestyle_current, freestyle_power),
            ("Racing", racing_current, racing_power),
            ("Full Throttle", full_current, full_power),
        ]

        for mode, i_mode, p_mode in modes:
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
    # Stress Bars (Racing Profile, physics-based)
    # ---------------------------------------------------------

    st.subheader("Thermal & Reliability Stress")

    motor_count = len(kwad.motors) if kwad.motors else 0

    # Racing profile: 75% of full-throttle current
    ft_current = perf.full_throttle_current_a
    racing_current = ft_current * 0.75
    racing_current_per_motor = racing_current / motor_count if motor_count > 0 else 0.0

    # Battery sag at racing load
    v_sag_race = phys.voltage_sag_under_load(v_full, racing_current, r_pack)
    sag_race_pct = (v_full - v_sag_race) / v_full if v_full > 0 else 0.0

    # ---------------------------------------------------------
    # FC Stress (realistic CPU model, scaled by racing load)
    # ---------------------------------------------------------

    loop_factor = cfg["fc_loop"] / 4000.0
    dshot_factor = cfg["fc_dshot"] / 1200.0
    noise_factor = cfg["frame_noise"] / 50.0
    motor_factor = motor_count / 4.0 if motor_count > 0 else 0.0

    fc_stress = (
        loop_factor * 0.40 +
        dshot_factor * 0.20 +
        noise_factor * 0.20 +
        motor_factor * 0.20
    )

    # Increase FC stress under heavy racing load
    if hover_current > 0:
        load_factor = min(racing_current / hover_current, 3.0)
        fc_stress *= (0.8 + 0.2 * load_factor)

    fc_stress = clamp01(fc_stress)

    # ---------------------------------------------------------
    # ESC Stress (prop + motor + ESC + battery @ racing load)
    # ---------------------------------------------------------

    timing_factor = {"low": 0.9, "med": 1.0, "high": 1.1}[cfg["esc_timing"]]
    pwm_factor = min(cfg["esc_pwm"] / 48000, 1.2)

    esc_rating_eff = kwad.esc.continuous_current_a * 0.8  # derate to realistic continuous
    esc_stress = clamp01((racing_current_per_motor / esc_rating_eff) ** 1.25)
    esc_stress *= timing_factor * pwm_factor

    esc_stress = clamp01(esc_stress)

    # ---------------------------------------------------------
    # Motor Stress (battery + ESC + motor limits + props @ racing)
    # ---------------------------------------------------------

    kv_factor = kwad.motors[0].kv_rpm_per_v / 1950.0 if motor_count > 0 else 1.0
    prop_factor = (cfg["prop_diameter"] / 5.1) * (cfg["prop_pitch"] / 4.3)

    motor_rating_eff = kwad.motors[0].max_current_a * 0.8 if motor_count > 0 else 1.0
    ratio = racing_current_per_motor / motor_rating_eff
    motor_stress = clamp01((ratio ** 1.6) * kv_factor * prop_factor)
    motor_stress *= kv_factor * prop_factor
    motor_stress = clamp01(motor_stress)

    # ---------------------------------------------------------
    # Desync Stress (KV + pitch + demag + timing + sag @ racing)
    # ---------------------------------------------------------

    demag_factor = {"high": 0.7, "med": 1.0, "low": 1.3}[cfg["esc_demag"]]
    timing_desync_factor = {"low": 1.2, "med": 1.0, "high": 0.8}[cfg["esc_timing"]]

    desync_stress = racing_current_per_motor / motor_rating_eff if motor_rating_eff > 0 else 0.0
    desync_stress *= kv_factor * prop_factor
    desync_stress *= demag_factor * timing_desync_factor
    desync_stress *= (1.0 + sag_race_pct * 2.0)
    desync_stress = clamp01(desync_stress)

    # ---------------------------------------------------------
    # Battery Stress (props + motors + ESC + battery @ racing)
    # ---------------------------------------------------------

    safe_current_theoretical = kwad.battery.c_rating * (kwad.battery.capacity_mah / 1000.0)
    safe_current_real = safe_current_theoretical * 0.5  # derate C-rating to realistic value

    batt_stress = racing_current / safe_current_real if safe_current_real > 0 else 0.0
    batt_stress *= (1.0 + sag_race_pct * 1.0)

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
