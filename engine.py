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
import math

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
    """Linear RPM model (kept for reference, not used for hover)."""
    return motor.kv_rpm_per_v * voltage_v


def static_thrust(motor: Motor, prop: Propeller, voltage_v: float, fuzz: phys.Fuzz) -> float:
    """
    Static max thrust per motor using the diameter-aware prop model.
    """
    rpm = phys.throttle_to_rpm(1.0, motor.kv_rpm_per_v, voltage_v)
    rpm = min(rpm, 120_000.0)

    diameter_in = prop.diameter_in
    pitch_in = prop.pitch_in
    blades = getattr(prop, "blades", 2)

    return phys.static_thrust_simple(
        rpm=rpm,
        diameter_in=diameter_in,
        pitch_in=pitch_in,
        blades=blades,
        fuzz=fuzz,
    )


# ============================================================
# Hover Throttle
# ============================================================

def hover_thrust_required(kwad: Kwad) -> float:
    return phys.weight_from_mass(auw_kg(kwad))


def hover_throttle(kwad: Kwad, voltage_v: float, fuzz: phys.Fuzz) -> float:
    """
    Solve for hover throttle by matching thrust per motor to required hover thrust,
    using the nonlinear throttle→RPM mapping and the diameter-aware prop model.
    """
    thrust_needed = hover_thrust_required(kwad)
    motor_count = len(kwad.motors)
    if motor_count <= 0:
        return 0.0

    thrust_per_motor = thrust_needed / motor_count

    motor = kwad.motors[0]
    prop = kwad.props[0]

    diameter_in = prop.diameter_in
    pitch_in = prop.pitch_in
    blades = getattr(prop, "blades", 2)

    lo, hi = 0.0, 1.0
    for _ in range(25):
        mid = 0.5 * (lo + hi)

        rpm = phys.throttle_to_rpm(mid, motor.kv_rpm_per_v, voltage_v)
        rpm = min(rpm, 120_000.0)

        thrust = phys.static_thrust_simple(
            rpm=rpm,
            diameter_in=diameter_in,
            pitch_in=pitch_in,
            blades=blades,
            fuzz=fuzz,
        )

        if thrust > thrust_per_motor:
            hi = mid
        else:
            lo = mid

    return max(0.0, min(1.0, 0.5 * (lo + hi)))


# ============================================================
# Power Model (mechanical → electrical)
# ============================================================

def hover_mech_power_total_w(kwad: Kwad, thrust_per_motor_n: float, fuzz: phys.Fuzz) -> float:
    """
    Hover mechanical power at the props using induced power
    and the diameter-aware prop power function.
    """
    total = 0.0
    for prop in kwad.props:
        diameter_in = prop.diameter_in
        blades = getattr(prop, "blades", 2)

        p = phys.prop_power_from_thrust(
            thrust_n=thrust_per_motor_n,
            diameter_in=diameter_in,
            blades=blades,
            fuzz=fuzz,
        )
        total += p
    return total


# ============================================================
# Motor Current from Thrust (mech → elec)
# ============================================================

def motor_current_from_thrust(
    motor: Motor,
    prop: Propeller,
    thrust_n: float,
    voltage_v: float,
    fuzz: phys.Fuzz,
) -> float:
    """
    Convert thrust → prop mechanical power → electrical power → motor current.
    Uses motor efficiency instead of assuming ideal torque conversion.
    """
    diameter_in = prop.diameter_in
    blades = getattr(prop, "blades", 2)

    # Mechanical power at the prop
    p_mech = phys.prop_power_from_thrust(
        thrust_n=thrust_n,
        diameter_in=diameter_in,
        blades=blades,
        fuzz=fuzz,
    )

    # Motor efficiency (use motor_physics if present, otherwise a sane default)
    if motor.motor_physics is not None:
        eff_base = motor.motor_physics.efficiency
    else:
        eff_base = 0.85

    eff = eff_base * fuzz.motor_efficiency_multiplier
    eff = max(0.3, min(0.98, eff))

    # Electrical power per motor
    p_elec = p_mech / max(eff, 1e-6)

    # Current from electrical power
    current = p_elec / max(voltage_v, 1e-3)
    return max(current, 0.0)


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
    total_power_hover_w: float  # electrical power
    flight_time_min: float
    motor_temp_rise_c: float
    esc_temp_rise_c: float


def evaluate_kwad(kwad: Kwad, fuzz: phys.Fuzz) -> KwadPerformance:
    """
    High-level evaluation of quad performance with sag-aware hover throttle.
    """

    v_full = phys.pack_voltage_full(kwad.battery.cells_series, kwad.battery.chemistry)

    thrust_needed = hover_thrust_required(kwad)
    motor_count = len(kwad.motors)
    if motor_count <= 0:
        return KwadPerformance(
            hover_throttle=0.0,
            max_thrust_total_n=0.0,
            total_power_hover_w=0.0,
            flight_time_min=0.0,
            motor_temp_rise_c=0.0,
            esc_temp_rise_c=0.0,
        )

    thrust_per_motor = thrust_needed / motor_count

    motor = kwad.motors[0]
    prop = kwad.props[0]

    r_internal = phys.pack_internal_resistance(
        kwad.battery.cells_series, kwad.battery.chemistry, fuzz
    )

    # Iterative sag + throttle loop: solve for self-consistent voltage, current, and throttle
    v_loaded = v_full
    hover_current = 0.0
    current_per_motor = 0.0
    h_throttle = 0.5  # initial guess; will be overwritten

    for _ in range(8):
        # Solve hover throttle at the current loaded voltage
        h_throttle = hover_throttle(kwad, v_loaded, fuzz)

        # Current per motor from mech→elec power at this voltage
        current_per_motor = motor_current_from_thrust(
            motor,
            prop,
            thrust_per_motor,
            v_loaded,
            fuzz,
        )
        hover_current = current_per_motor * motor_count

        new_v_loaded = phys.voltage_sag_under_load(v_full, hover_current, r_internal)

        if abs(new_v_loaded - v_loaded) < 0.02:
            v_loaded = new_v_loaded
            break

        v_loaded = new_v_loaded

    # Electrical hover power
    total_power = v_loaded * hover_current * fuzz.hover_power_multiplier

    # Flight time
    ft = flight_time_minutes(kwad, total_power)

    # Thermal (approximate)
    motor_temp = motor_temperature_rise(motor, current_per_motor, 60, fuzz)
    esc_temp = esc_temperature_rise(kwad.esc, current_per_motor, 60, fuzz)

    # Max thrust (full throttle at full voltage)
    max_thrust_per_motor = static_thrust(motor, prop, v_full, fuzz)
    max_total = max_thrust_per_motor * motor_count

    return KwadPerformance(
        hover_throttle=h_throttle,
        max_thrust_total_n=max_total,
        total_power_hover_w=total_power,
        flight_time_min=ft,
        motor_temp_rise_c=motor_temp,
        esc_temp_rise_c=esc_temp,
    )
