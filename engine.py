"""
engine.py

The physics computation engine for Kwadstream.

This module:
- Imports pure data models from basekwad.py
- Imports physics constants & equations from physics.py
- Computes thrust, power, AUW, flight time, thermal rise, etc.
- Applies user-tunable fuzz multipliers to all physics calls.

No UI. No Streamlit. No magic numbers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from basekwad import (
    Kwad, Motor, Propeller, Battery, ESC, FlightController, VTX
)

import physics as phys


# ============================================================
# Utility: mass/weight conversions
# ============================================================

def auw_kg(kwad: Kwad) -> float:
    return kwad.auw_g / 1000.0


# ============================================================
# Motor + Propeller Physics
# ============================================================

def motor_rpm_from_voltage(motor: Motor, voltage_v: float) -> float:
    """RPM = Kv * V (no-load approximation)."""
    return motor.kv_rpm_per_v * voltage_v


def motor_torque_from_thrust(thrust_n: float, prop: Propeller, fuzz: phys.Fuzz) -> float:
    """
    Approximate torque required for a given thrust.
    This is a placeholder for a more advanced prop model.
    """
    disk_area = phys.disk_area_from_diameter(prop.diameter_m)
    if disk_area <= 0:
        return 0.0

    # Induced power → torque
    p = phys.prop_power_from_thrust(thrust_n, prop.diameter_m, fuzz)
    rpm = 5000  # placeholder; engine will iterate to solve this
    omega = (rpm * 2 * 3.14159) / 60
    if omega <= 0:
        return 0.0

    return p / omega


def motor_current(motor: Motor, torque_nm: float, fuzz: phys.Fuzz) -> float:
    return phys.motor_current_for_torque(
        torque_nm,
        motor.kv_rpm_per_v,
        fuzz,
        motor.no_load_current_a
    )


# ============================================================
# Thrust Model
# ============================================================

def static_thrust(motor: Motor, prop: Propeller, voltage_v: float, fuzz: phys.Fuzz) -> float:
    rpm = motor_rpm_from_voltage(motor, voltage_v)
    return phys.static_thrust_simple(
        rpm,
        prop.diameter_m,
        prop.pitch_m,
        fuzz
    )


# ============================================================
# Battery / Voltage / Sag
# ============================================================

def battery_full_voltage(battery: Battery) -> float:
    return phys.pack_voltage_full(
        battery.cells_series,
        battery.chemistry
    )


def battery_nominal_voltage(battery: Battery) -> float:
    return phys.pack_voltage_nominal(
        battery.cells_series,
        battery.chemistry
    )


def battery_sag_voltage(battery: Battery, current_a: float, fuzz: phys.Fuzz) -> float:
    r = phys.pack_internal_resistance(
        battery.cells_series,
        battery.chemistry,
        fuzz
    )
    v_oc = battery_full_voltage(battery)
    return phys.voltage_sag_under_load(v_oc, current_a, r)


# ============================================================
# Power Draw
# ============================================================

def motor_power_draw(motor: Motor, torque_nm: float, voltage_v: float, fuzz: phys.Fuzz) -> float:
    current = motor_current(motor, torque_nm, fuzz)
    return phys.motor_input_power(voltage_v, current, fuzz)


def total_power_draw(kwad: Kwad, thrust_per_motor_n: float, voltage_v: float, fuzz: phys.Fuzz) -> float:
    total = 0.0
    for motor, prop in zip(kwad.motors, kwad.props):
        torque = motor_torque_from_thrust(thrust_per_motor_n, prop, fuzz)
        total += motor_power_draw(motor, torque, voltage_v, fuzz)
    return total


# ============================================================
# Hover Throttle
# ============================================================

def hover_thrust_required(kwad: Kwad) -> float:
    return phys.weight_from_mass(auw_kg(kwad))


def hover_throttle(kwad: Kwad, voltage_v: float, fuzz: phys.Fuzz) -> float:
    thrust_needed = hover_thrust_required(kwad)
    thrust_per_motor = thrust_needed / len(kwad.motors)

    max_thrust = static_thrust(kwad.motors[0], kwad.props[0], voltage_v, fuzz)

    if max_thrust <= 0:
        return 1.0

    return thrust_per_motor / max_thrust


# ============================================================
# Flight Time
# ============================================================

def flight_time_minutes(kwad: Kwad, avg_power_w: float) -> float:
    energy_wh = phys.energy_wh_from_capacity(
        kwad.battery.capacity_mah,
        battery_nominal_voltage(kwad.battery)
    )
    return phys.ideal_flight_time_minutes(energy_wh, avg_power_w)


# ============================================================
# Thermal Modeling
# ============================================================

def motor_temperature_rise(motor: Motor, current_a: float, time_s: float, fuzz: phys.Fuzz) -> float:
    if motor.motor_physics is None or not hasattr(motor, "thermal_model") or motor.thermal_model is None:
        return 0.0

    p_loss = phys.copper_loss(current_a, motor.resistance_ohm)

    return phys.transient_temp_rise(
        p_loss,
        motor.thermal_model,
        fuzz,
        time_s
    )


def esc_temperature_rise(esc: ESC, current_a: float, time_s: float, fuzz: phys.Fuzz) -> float:
    if esc.thermal_model is None:
        return 0.0

    p_loss = phys.esc_loss(current_a, esc.mosfet_resistance_ohm, fuzz)

    return phys.transient_temp_rise(
        p_loss,
        esc.thermal_model,
        fuzz,
        time_s
    )


def fc_temperature_rise(fc: FlightController, power_w: float, time_s: float, fuzz: phys.Fuzz) -> float:
    if fc.thermal_model is None:
        return 0.0

    return phys.transient_temp_rise(power_w, fc.thermal_model, fuzz, time_s)


def vtx_temperature_rise(vtx: VTX, power_mw: float, time_s: float, fuzz: phys.Fuzz) -> float:
    if vtx.thermal_model is None:
        return 0.0

    power_w = power_mw / 1000.0
    return phys.transient_temp_rise(power_w, vtx.thermal_model, fuzz, time_s)


# ============================================================
# Forward Flight / Drag / Top Speed
# ============================================================

def drag_force(kwad: Kwad, airspeed_mps: float, area_m2: float, cd: float, fuzz: phys.Fuzz) -> float:
    return phys.drag_force(airspeed_mps, area_m2, cd, fuzz)


# ============================================================
# High-Level Evaluation
# ============================================================

@dataclass
class KwadPerformance:
    hover_throttle: float
    max_thrust_total_n: float
    total_power_hover_w: float
    flight_time_min: float
    motor_temp_rise_c: float
    esc_temp_rise_c: float


def evaluate_kwad(kwad: Kwad, fuzz: phys.Fuzz) -> KwadPerformance:
    """
    High-level evaluation of quad performance.
    """

    v_full = battery_full_voltage(kwad.battery)

    # Hover
    h_throttle = hover_throttle(kwad, v_full, fuzz)
    thrust_needed = hover_thrust_required(kwad)
    thrust_per_motor = thrust_needed / len(kwad.motors)

    # Power at hover
    total_power = total_power_draw(kwad, thrust_per_motor, v_full, fuzz)

    # Flight time
    ft = flight_time_minutes(kwad, total_power)

    # Thermal (60s hover)
    motor_current_est = motor_current(
        kwad.motors[0],
        motor_torque_from_thrust(thrust_per_motor, kwad.props[0], fuzz),
        fuzz
    )
    motor_temp = motor_temperature_rise(kwad.motors[0], motor_current_est, 60, fuzz)
    esc_temp = esc_temperature_rise(kwad.esc, motor_current_est, 60, fuzz)

    # Max thrust
    max_thrust_per_motor = static_thrust(kwad.motors[0], kwad.props[0], v_full, fuzz)
    max_total = max_thrust_per_motor * len(kwad.motors)

    return KwadPerformance(
        hover_throttle=h_throttle,
        max_thrust_total_n=max_total,
        total_power_hover_w=total_power,
        flight_time_min=ft,
        motor_temp_rise_c=motor_temp,
        esc_temp_rise_c=esc_temp,
    )
