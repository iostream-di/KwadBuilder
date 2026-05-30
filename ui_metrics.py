# ui_metrics.py

import streamlit as st
import physics as phys
import engine
from ui_stressbars import render_stress_bars


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
    payload_g = cfg.get("payload", 0.0)  # default 0 if not set
    auw_kg = engine.auw_kg(kwad) + (payload_g / 1000.0)
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

    # ---------------------------------------------------------
    # Full throttle & profiles (MUST be defined early)
    # ---------------------------------------------------------

    ft_current = perf.full_throttle_current_a
    ft_power = perf.full_throttle_power_w

    racing_current = ft_current * 0.75
    racing_power = racing_current * v_nom if v_nom > 0 else 0.0

    freestyle_current = 0.5 * (hover_current + racing_current)
    freestyle_power = freestyle_current * v_nom if v_nom > 0 else 0.0

    # Battery energy
    energy_wh = phys.energy_wh_from_capacity(kwad.battery.capacity_mah, v_nom)

    # ---------------------------------------------------------
    # Expanded Performance Metrics
    # ---------------------------------------------------------

    # Max Speed (MPH)
    rpm = kwad.motors[0].kv_rpm_per_v * v_nom * 0.9
    max_speed_mph = cfg["prop_pitch"] * rpm * 0.000947

    # High Power & High Current (Racing)
    high_current = racing_current
    high_power = high_current * v_nom

    # Max Current (Full Throttle)
    max_current = ft_current

    # Max Payload (TWR = 2:1)
    max_payload_g = (max_thrust_g / 2) - auw_g

    # Max Voltage Sag (Full Throttle)
    v_sag_ft = phys.voltage_sag_under_load(v_full, ft_current, r_pack)
    sag_ft_pct = (v_full - v_sag_ft) / v_full if v_full > 0 else 0.0

    # Flight Time (Freestyle)
    flight_time_freestyle = phys.ideal_flight_time_minutes(energy_wh, freestyle_power) if freestyle_power > 0 else 0.0

    # Battery Warning Voltage (freestyle load)
    v_warn = phys.voltage_sag_under_load(v_full, freestyle_current, r_pack)

    # Battery Land Voltage
    v_land = 3.5 * kwad.battery.cells_series

    # Max Acceleration (G)
    max_accel_g = (perf.max_thrust_total_n - weight_n) / (auw_kg * phys.GRAVITY) if auw_kg > 0 else 0.0

    # ---------------------------------------------------------
    # Capacitor Recommendation
    # ---------------------------------------------------------

    # Base capacitance from full-throttle current
    base_cap_uf = 200 * (ft_current / 50.0)

    # Scale by full-throttle sag severity
    cap_required_uf = base_cap_uf * (1.0 + 2.0 * sag_ft_pct)

    # Clamp to realistic FPV ranges
    cap_required_uf = max(100, min(cap_required_uf, 2200))

    # Voltage rating (25% margin above full voltage)
    cap_voltage_required = v_full * 1.25

    # Round voltage rating to nearest standard value
    standard_voltages = [16, 25, 35, 50, 63]
    cap_voltage_rating = next((v for v in standard_voltages if v >= cap_voltage_required), 63)

    # Dry Weight
    dry_weight_g = (engine.auw_kg(kwad) * 1000.0) - kwad.battery.weight_g

    # Max Prop Load (per motor)
    motor_count = len(kwad.motors)
    max_prop_load_g = max_thrust_g / motor_count if motor_count > 0 else 0.0

    # Max RPM
    max_rpm = kwad.motors[0].kv_rpm_per_v * v_full * 0.9


    # ---------------------------------------------------------
    # Render Metrics
    # ---------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Dry Weight", f"{dry_weight_g:.0f} g")
        st.metric("Max Payload", f"{max_payload_g:.0f} g")
        st.metric("AUW", f"{auw_g:.0f} g")
        st.metric("Max Thrust", f"{max_thrust_g:.0f} g")
        st.metric("Max RPM", f"{max_rpm:.0f} RPM")
        st.metric("Max Acceleration", f"{max_accel_g:.2f} G")
        st.metric("Max Speed", f"{max_speed_mph:.0f} mph")
        st.metric("TWR", f"{twr:.2f} : 1")
        st.metric("Hover Throttle", f"{perf.hover_throttle:.2f}")
        st.metric("Max Prop Load", f"{max_prop_load_g:.0f} g/motor")
        
    with col2:
        st.metric("Hover Power", f"{hover_power:.0f} W")
        st.metric("High Power", f"{high_power:.0f} W")
        st.metric("Hover Current", f"{hover_current:.1f} A")
        st.metric("High Current", f"{high_current:.1f} A")
        st.metric("Max Current", f"{max_current:.1f} A")
        st.metric("Voltage Sag (Hover)", f"{sag_pct * 100:.1f} %")
        st.metric("Max Voltage Sag", f"{sag_ft_pct * 100:.1f} %")
        st.metric("Battery Warning Voltage", f"{v_warn:.2f} V")
        st.metric("Battery Land Voltage", f"{v_land:.2f} V")
        st.metric("Capacitor Required (Low ESR)", f"{cap_required_uf:.0f} µF @ {cap_voltage_rating} V")




    # ---------------------------------------------------------
    # Flight Time Breakdown
    # ---------------------------------------------------------

    with st.expander("Flight Time Breakdown", expanded=False):

        rows_mode = []
        rows_current = []
        rows_time = []

        # Loitering
        loiter_current = hover_current * 0.6
        loiter_power = loiter_current * v_nom if v_nom > 0 else 0.0

        # Cruise
        cruise_current = hover_current
        cruise_power = hover_power

        # Freestyle (already computed)
        # Racing (already computed)
        # Full throttle (already computed)

        modes = [
            ("Loitering", loiter_current, loiter_power),
            ("Cruise", cruise_current, cruise_power),
            ("Freestyle", freestyle_current, freestyle_power),
            ("Racing", racing_current, racing_power),
            ("Full Throttle", ft_current, ft_power),
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
    # Stress Bars
    # ---------------------------------------------------------

    render_stress_bars(cfg, kwad, perf, fuzz, v_full, r_pack, hover_current)

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
