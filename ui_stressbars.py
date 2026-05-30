# ui_stressbars.py

import streamlit as st
from physics import voltage_sag_under_load

def clamp01(x):
    return max(0.0, min(1.0, x))



def heat_bar(label, value):
    pct = int(clamp01(value) * 100)
    pos = pct
    html = f"""
    <div style="margin-bottom:8px;">
      <div style="font-weight:600; margin-bottom:2px;">{label}</div>
      <div style="width: 100%; height: 22px; border-radius: 11px;
           background: linear-gradient(90deg, #7FDBFF 0%, #FFD700 50%, #FF4136 100%);
           position: relative; color: inherit;">
        <div style="position: absolute; top: -4px; left: calc({pos}% - 5px);
                    width: 10px; height: 30px; background: inherit; border-radius: 5px;">
        </div>
      </div>
      <div style="margin-top:2px; font-size:0.85rem;">{pct}%</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_stress_bars(cfg, kwad, perf, fuzz, v_full, r_pack, hover_current):
    st.subheader("Thermal & Reliability Stress")

    motor_count = len(kwad.motors) if kwad.motors else 0

    # Racing profile: 75% of full-throttle current
    ft_current = perf.full_throttle_current_a
    racing_current = ft_current * 0.75
    racing_current_per_motor = racing_current / motor_count if motor_count > 0 else 0.0

    # Battery sag at racing load
    v_sag_race = voltage_sag_under_load(v_full, racing_current, r_pack)
    sag_race_pct = (v_full - v_sag_race) / v_full if v_full > 0 else 0.0

    # ---------------------------------------------------------
    # FC Stress
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

    if hover_current > 0:
        load_factor = min(racing_current / hover_current, 3.0)
        fc_stress *= (0.8 + 0.2 * load_factor)

    fc_stress = clamp01(fc_stress)

    # ---------------------------------------------------------
    # ESC Stress
    # ---------------------------------------------------------

    timing_factor = {"low": 0.9, "med": 1.0, "high": 1.1}[cfg["esc_timing"]]
    pwm_factor = min(cfg["esc_pwm"] / 48000, 1.2)

    esc_rating_eff = kwad.esc.continuous_current_a * 0.8
    esc_stress = clamp01((racing_current_per_motor / esc_rating_eff) ** 1.25)
    esc_stress *= timing_factor * pwm_factor
    esc_stress = clamp01(esc_stress)

    # ---------------------------------------------------------
    # Motor Stress
    # ---------------------------------------------------------

    kv_factor = kwad.motors[0].kv_rpm_per_v / 1950.0 if motor_count > 0 else 1.0
    prop_factor = (cfg["prop_diameter"] / 5.1) * (cfg["prop_pitch"] / 4.3)

    motor_rating_eff = kwad.motors[0].max_current_a * 0.8
    ratio = racing_current_per_motor / motor_rating_eff

    motor_stress = clamp01((ratio ** 0.5) * kv_factor * prop_factor)
    motor_stress *= kv_factor * prop_factor
    motor_stress = clamp01(motor_stress)

    # ---------------------------------------------------------
    # Desync Stress
    # ---------------------------------------------------------

    demag_factor = {"high": 0.7, "med": 1.0, "low": 1.3}[cfg["esc_demag"]]
    timing_desync_factor = {"low": 1.2, "med": 1.0, "high": 0.8}[cfg["esc_timing"]]

    desync_stress = racing_current_per_motor / motor_rating_eff
    desync_stress *= kv_factor * prop_factor
    desync_stress *= demag_factor * timing_desync_factor
    desync_stress *= (1.0 + sag_race_pct * 2.0)
    desync_stress = clamp01(desync_stress)

    # ---------------------------------------------------------
    # Battery Stress
    # ---------------------------------------------------------

    safe_current_theoretical = kwad.battery.c_rating * (kwad.battery.capacity_mah / 1000.0)
    safe_current_real = safe_current_theoretical * 0.5

    batt_stress = racing_current / safe_current_real
    batt_stress *= (1.0 + sag_race_pct * 1.0)

    health_factor = 100.0 / max(cfg["lipo_health"], 1.0)
    batt_stress *= health_factor

    batt_stress = clamp01(batt_stress)

    # ---------------------------------------------------------
    # Overall Stress
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
