"""
engine.py

High‑level quadcopter performance engine for Kwadstream.

This module:
- Computes AUW from component weights
- Computes thrust, hover throttle, hover power, flight time
- Computes thermal rise
- Applies fuzz multipliers
- Returns a KwadPerformance object for the UI
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import physics as phys
from basekwad import (
    Kwad, Motor, Propeller, Battery, ESC, FlightController, VTX
)


# ============================================================
# AUW Calculation
# ============================================================

def auw_kg(kwad: Kwad) -> float:
    """Compute AUW from all component weights."""
    total_g = 0.0

    total_g += kwad.frame.dry_weight_g
    total_g += kwad.esc.weight_g
    total_g += kwad.fc.weight_g
    total_g += kwad.vtx.weight_g
    total_g += kwad.camera.weight_g
    total_g += kwad.receiver.weight_g
    total_g += kwad.battery.weight_g

    if kwad.action_cam:
        total_g += kwad.action_cam.weight_g

    for m in kwad.motors:
        total_g += m.weight_g

    for p in kwad.props:
        if hasattr(p, "weight_g"):
            total_g += p.weight_g

    return total_g / 1000.0


# ============================================================
# Thrust Model
# ============================================================

def motor_rpm_from_voltage(motor: Motor, voltage_v: float) -> float:
    return motor.kv_rpm_per_v * voltage_v


def static_thrust(motor: Motor, prop: Propeller, voltage_v: float, fuzz: phys.Fuzz) -> float:
    rpm = motor_rpm_from_voltage(motor, voltage_v)
    return phys.static_thrust_simple(
        rpm,
        prop.diameter_m,
        prop.pitch_m,
        fuzz
    )


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
# Power Model (Corrected)
# ============================================================

def hover_power_total_w(kwad: Kwad, thrust_per_motor_n: float, fuzz: phys.Fuzz) -> float:
    """
    Correct hover power model using induced power (momentum theory).
    This produces realistic values for 5"–7" quads.
    """
    total = 0.0
    for prop in kwad.props:
        p = phys.prop_power_from_thrust(
            thrust_per_motor_n,
            prop.diameter_m,
            fuzz
        )
        total += p
    return total


# ============================================================
# Flight Time
# ============================================================

def flight_time_minutes(kwad: Kwad, avg_power_w: float) -> float:
    v_nom = phys.pack_voltage_nominal(kwad.battery.cells_series, kwad.battery.chemistry)
    energy_wh = phys.energy_wh_from_capacity(kwad.battery.capacity_mah, v_nom)
    return phys.ideal_flight_time_minutes(energy_wh, avg_power_w)


# ============================================================
# Thermal Modeling
# ============================================================

def motor_temperature_rise(motor: Motor, current_a: float, time_s: float, fuzz: phys.Fuzz) -> float:
    if motor.motor_physics is None or motor.thermal_model is None:
        return 0.0

    p_loss = phys.copper_loss(current_a, motor.resistance_ohm)
    return phys.transient_temp_rise(p_loss, motor.thermal_model, fuzz, time_s)


def esc_temperature_rise(esc: ESC, current_a: float, time_s: float, fuzz: phys.Fuzz) -> float:
    if esc.thermal_model is None:
        return 0.0

    p_loss = phys.esc_loss(current_a, esc.mosfet_resistance_ohm, fuzz)
    return phys.transient_temp_rise(p_loss, esc.thermal_model, fuzz, time_s)


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

    v_full = phys.pack_voltage_full(kwad.battery.cells_series, kwad.battery.chemistry)

    # Hover
    h_throttle = hover_throttle(kwad, v_full, fuzz)
    thrust_needed = hover_thrust_required(kwad)
    thrust_per_motor = thrust_needed / len(kwad.motors)

    # Hover power (corrected)
    total_power = hover_power_total_w(kwad, thrust_per_motor, fuzz)

    # Flight time
    ft = flight_time_minutes(kwad, total_power)

    # Thermal (approximate)
    hover_current = total_power / v_full if v_full > 0 else 0.0
    current_per_motor = hover_current / len(kwad.motors)

    motor_temp = motor_temperature_rise(kwad.motors[0], current_per_motor, 60, fuzz)
    esc_temp = esc_temperature_rise(kwad.esc, current_per_motor, 60, fuzz)

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
