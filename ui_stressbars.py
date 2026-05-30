import streamlit as st
from physics import voltage_sag_under_load, GRAVITY
from math import sqrt
import math

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
           position: relative; color: currentColor;">
        <div style="position: absolute; top: -4px; left: calc({pos}% - 5px);
                    width: 10px; height: 30px; background: currentColor; border-radius: 5px;">
        </div>
      </div>
      <div style="margin-top:2px; font-size:0.85rem;">{pct}%</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_stress_bars(cfg, kwad, perf, fuzz, v_full, r_pack, hover_current):
    st.subheader("Thermal & Reliability Stress")

    # ---------------------------------------------------------
    # Extract live values from kwad/perf
    # ---------------------------------------------------------

    motor_count = len(kwad.motors) if kwad.motors else 0
    motor = kwad.motors[0] if motor_count > 0 else None
    esc = kwad.esc
    battery = kwad.battery
    props = kwad.props[0] if kwad.props else None

    # FC values
    fc_loop = getattr(kwad.fc, "loop_rate_hz", 2000)
    fc_dshot = getattr(kwad.fc, "dshot_rate", 600)
    frame_noise = getattr(kwad.frame, "noise_factor", 10)
    fc_cpu = getattr(kwad.fc, "cpu_load_pct", None)  # NEW

    # ESC config
    esc_timing = getattr(esc, "timing", "med")
    esc_pwm = getattr(esc, "pwm_rate_hz", 48000)
    esc_demag = getattr(esc, "demag", "med")

    # Props
    prop_diameter = props.diameter_in if props else 5.1
    prop_pitch = props.pitch_in if props else 4.3

    # Battery health (user input)
    lipo_health = cfg.get("lipo_health", 100)

    # ---------------------------------------------------------
    # Racing load
    # ---------------------------------------------------------

    ft_current = perf.full_throttle_current_a
    racing_current = ft_current * 0.75
    racing_current_per_motor = racing_current / motor_count if motor_count > 0 else 0.0

    v_sag_race = voltage_sag_under_load(v_full, racing_current, r_pack)
    sag_race_pct = (v_full - v_sag_race) / v_full if v_full > 0 else 0.0

    # =========================================================
    # FC STRESS (CPU load dominates)
    # =========================================================

    loop_factor = fc_loop / 4000.0
    dshot_factor = fc_dshot / 1200.0
    noise_factor = frame_noise / 50.0
    motor_factor = motor_count / 4.0 if motor_count > 0 else 0.0

    fc_stress = (
        0.25 * loop_factor +
        0.15 * dshot_factor +
        0.15 * noise_factor +
        0.15 * motor_factor
    )

    # CPU load dominates if available
    if fc_cpu is not None:
        cpu_factor = clamp01(fc_cpu / 100.0)
        fc_stress = 0.6 * cpu_factor + 0.4 * fc_stress

    # Load influence
    if hover_current > 0:
        load_factor = min(racing_current / hover_current, 3.0)
        fc_stress *= (0.8 + 0.2 * load_factor)

    fc_stress = clamp01(fc_stress)

    # =========================================================
    # ESC STRESS (battery health penalty added)
    # =========================================================

    timing_factor = {"low": 0.9, "med": 1.0, "high": 1.1}.get(esc_timing, 1.0)
    pwm_factor = min(esc_pwm / 48000, 1.2)

    esc_safe = esc.continuous_current_a * 0.8
    esc_stress = (racing_current_per_motor / esc_safe)

    # Battery health penalty (NEW)
    health_penalty = 1.0 + (1.0 - (lipo_health / 100.0)) * 0.5
    esc_stress *= timing_factor * pwm_factor * health_penalty

    esc_stress = clamp01(esc_stress)

    # =========================================================
    # MOTOR STRESS
    # =========================================================

    kv_factor = motor.kv_rpm_per_v / 1950.0 if motor else 1.0
    prop_factor = (prop_diameter / 5.1) * (prop_pitch / 4.3)

    motor_safe = motor.max_current_a * 0.8 if motor else 30
    motor_ratio = racing_current_per_motor / motor_safe

    motor_stress = (
        0.7 * motor_ratio +
        0.3 * (kv_factor * prop_factor)
    )

    motor_stress = clamp01(motor_stress)

    # =========================================================
    # DESYNC STRESS
    # =========================================================

    demag_factor = {"high": 0.7, "med": 1.0, "low": 1.3}.get(esc_demag, 1.0)
    timing_desync_factor = {"low": 1.2, "med": 1.0, "high": 0.8}.get(esc_timing, 1.0)

    desync_stress = (
        0.3 * (motor.kv_rpm_per_v / 3000.0 if motor else 0.5) +
        0.3 * (prop_pitch / 6.0) +
        0.2 * sag_race_pct +
        0.2 * (racing_current_per_motor / motor_safe)
    )

    desync_stress *= demag_factor * timing_desync_factor
    desync_stress = clamp01(desync_stress)

    # =========================================================
    # BATTERY STRESS
    # =========================================================

    safe_current_theoretical = battery.c_rating * (battery.capacity_mah / 1000.0)
    safe_current_real = safe_current_theoretical * 0.8

    batt_stress = racing_current / safe_current_real
    batt_stress *= (1.0 + sag_race_pct)

    health_factor = 100.0 / max(lipo_health, 1.0)
    batt_stress *= health_factor

    batt_stress = clamp01(batt_stress)

    # =========================================================
    # OVERALL STRESS (logarithmic ramp of collective stressors)
    # =========================================================

    # Base stressors (exclude desync for now)
    base_stressors = [fc_stress, esc_stress, motor_stress, batt_stress]

    # Sum of stressors
    s = sum(base_stressors)

    # Logarithmic ramp
    # k = 1.8 gives a good FPV-feeling danger curve
    log_ramp = clamp01( (math.log(1 + 1.8 * s)) / math.log(1 + 1.8 * 4) )

    # Apply desync override rule
    if desync_stress > log_ramp:
        overall_stress = desync_stress
    else:
        overall_stress = log_ramp

    overall_stress = clamp01(overall_stress)


    # =========================================================
    # RENDER
    # =========================================================

    heat_bar("FC Stress", fc_stress)
    heat_bar("ESC Stress", esc_stress)
    heat_bar("Motor Stress", motor_stress)
    heat_bar("Desync Stress", desync_stress)
    heat_bar("Battery Stress", batt_stress)
    heat_bar("Overall Stress", overall_stress)
