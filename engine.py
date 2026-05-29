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
    Static max thrust per motor using the upgraded prop model:
    - Uses diameter, pitch, and blade count
    - Uses nonlinear throttle→RPM at full throttle
    Returns thrust in Newtons.
    """
    # Full-throttle RPM using nonlinear mapping
    rpm = phys.rpm_under_load(
        throttle=mid,
        kv_rpm_per_v=motor.kv_rpm_per_v,
        voltage_v=voltage_v,
        current_a=0.0,  # hover solver assumes low load; refined later
        motor_resistance_ohm=motor.resistance_ohm,
    )


    # Convert geometry to inches for the physics helpers
    diameter_in = prop.diameter_m / 0.0254
    pitch_in = prop.pitch_m / 0.0254
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
    using the nonlinear throttle→RPM mapping and the upgraded prop model.
    """
    thrust_needed = hover_thrust_required(kwad)
    thrust_per_motor = thrust_needed / len(kwad.motors)

    motor = kwad.motors[0]
    prop = kwad.props[0]

    diameter_in = prop.diameter_m / 0.0254
    pitch_in = prop.pitch_m / 0.0254
    blades = getattr(prop, "blades", 2)

    # Binary search on throttle in [0, 1]
    lo, hi = 0.0, 1.0
    for _ in range(20):
        mid = 0.5 * (lo + hi)

        # RPM under load (initially assume low load; refined later)
        rpm = phys.rpm_under_load(
            throttle=mid,
            kv_rpm_per_v=motor.kv_rpm_per_v,
            voltage_v=voltage_v,
            current_a=0.0,
            motor_resistance_ohm=motor.resistance_ohm,
        )

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

    ht = 0.5 * (lo + hi)
    return max(0.0, min(1.0, ht))



# ============================================================
# Power Model
# ============================================================

def hover_power_total_w(kwad: Kwad, thrust_per_motor_n: float, fuzz: phys.Fuzz) -> float:
    """
    Hover power model using induced power (momentum theory) and
    the upgraded prop power function (pitch + blade count).
    Returns total electrical power in Watts.
    """
    total = 0.0
    for prop in kwad.props:
        diameter_in = prop.diameter_m / 0.0254
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
# Motor Current from Thrust
# ============================================================

def motor_current_from_thrust(
    motor: Motor,
    prop: Propeller,
    rpm: float,
    thrust_n: float,
    fuzz: phys.Fuzz,
) -> float:
    """
    Convert thrust → prop power → torque → motor current using motor physics.
    """
    # Angular velocity
    omega = (rpm * 2.0 * math.pi) / 60.0  # rad/s

    # Mechanical power from prop model
    diameter_in = prop.diameter_m / 0.0254
    blades = getattr(prop, "blades", 2)

    p_out = phys.prop_power_from_thrust(
        thrust_n=thrust_n,
        diameter_in=diameter_in,
        blades=blades,
        fuzz=fuzz,
    )

    # Torque (Nm)
    torque = p_out / max(omega, 1e-6)

    # Motor torque constant (Nm/A)
    kt = phys.motor_torque_constant(motor.kv_rpm_per_v, fuzz)

    # Motor current (A)
    current = torque / max(kt, 1e-9) + motor.no_load_current_a
    return current


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

    # Hover power
    total_power = hover_power_total_w(kwad, thrust_per_motor, fuzz)

    # Hover current via torque/current model
    rpm_hover = rpm_hover = phys.rpm_under_load(
        throttle=h_throttle,
        kv_rpm_per_v=kwad.motors[0].kv_rpm_per_v,
        voltage_v=v_full,
        current_a=current_per_motor,
        motor_resistance_ohm=kwad.motors[0].resistance_ohm,
    )

    current_per_motor = motor_current_from_thrust(
        kwad.motors[0],
        kwad.props[0],
        rpm_hover,
        thrust_per_motor,
        fuzz,
    )
    hover_current = current_per_motor * len(kwad.motors)

    # Flight time
    ft = flight_time_minutes(kwad, total_power)

    # Thermal (approximate)
    motor_temp = motor_temperature_rise(kwad.motors[0], current_per_motor, 60, fuzz)
    esc_temp = esc_temperature_rise(kwad.esc, current_per_motor, 60, fuzz)

    # Max thrust (full throttle)
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
