# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 David Martinez

"""
engine.py — Multirotor System-Level Performance Engine
=======================================================

This module provides high‑level system modeling for multirotor UAVs by combining:

- Motor physics (via physics.py)
- Propeller thrust and power models
- Battery sag and internal resistance modeling
- Thermal rise for motors and ESCs
- Hover throttle solving
- Full‑throttle performance solving
- Flight time estimation
- AUW (All‑Up Weight) computation

This engine acts as the “glue layer” between the low‑level physics engine
(`physics.py`) and the high‑level quadcopter object model (`basekwad.py`).

All naming conventions, function signatures, and behaviors are relied upon by
other modules — **do not rename or restructure functions**.

This file is licensed under GPL‑3.0‑or‑later.
"""

from __future__ import annotations
from dataclasses import dataclass
import math

import physics as phys
from basekwad import (
    Kwad, Motor, Propeller, Battery, ESC, FlightController, VTX
)

# ============================================================
# Marty's KV Formula
# ============================================================
import math
def marty_kv(prop_diameter_in, battery_voltage):
    """
    Estimate motor KV from prop diameter and battery voltage.

    Parameters
    ----------
    prop_diameter_in : float
        Propeller diameter in inches.

    battery_voltage : float
        Battery voltage under load. For example:
        - 1S ≈ 3.8V
        - 2S ≈ 7.6V
        - 4S ≈ 15.2V
        - 6S ≈ 22.2V
        - 12S ≈ 44.4V

    Returns
    -------
    float
        Estimated motor KV (RPM/V).
    """

    # Speed of sound at sea level (m/s)
    speed_of_sound = 343.0

    # Loaded RPM factor.
    # Represents actual RPM as a fraction of unloaded KV × Voltage.
    # Example:
    #   2000KV motor on 22.2V theoretical = 44,400 RPM
    #   At 90% efficiency under load     = 39,960 RPM
    loaded_rpm_factor = 0.90

    # Inches-to-meters conversion factor.
    inches_to_meters = 0.0254

    # Diameter-dependent target tip Mach model.
    #
    # This is an empirical fit intended to better match observed
    # successful builds across multiple drone sizes.
    #
    # Small props appear to operate efficiently at lower tip Mach
    # numbers than larger props.
    target_mach = (
        0.45
        + 0.25
        * (
            1
            - math.exp(
                -0.4 * (prop_diameter_in - 2)
            )
        )
    )

    # Derived from:
    #
    #     KV = (60 * M * a) / (π * D * V * η)
    #
    # where:
    #     M = target Mach fraction
    #     a = speed of sound
    #     D = prop diameter (meters)
    #     V = battery voltage
    #     η = loaded RPM factor
    #
    # Convert inches to meters before solving.
    prop_diameter_m = prop_diameter_in * inches_to_meters

    kv = (
        60
        * target_mach
        * speed_of_sound
    ) / (
        math.pi
        * prop_diameter_m
        * battery_voltage
        * loaded_rpm_factor
    )

    return kv


def marty_load_index(
    kv,
    voltage,
    stator_width_mm,
    stator_height_mm,
    prop_diameter_in,
    prop_pitch_in,
    blade_count,
):
    """
    Relative motor load estimate.

    Higher numbers indicate a harder-working motor.

    Returns a dimensionless index intended for
    comparison between builds.
    """

    rpm_term = (kv * voltage) ** 3

    prop_term = (
        prop_diameter_in ** 4
        * prop_pitch_in
        * blade_count
    )

    motor_term = (
        stator_width_mm ** 2
        * stator_height_mm
    )

    return (
        rpm_term
        * prop_term
    ) / motor_term

REFERENCE_LOAD = marty_load_index(
    kv=1950,
    voltage=22.2,
    stator_width_mm=23,
    stator_height_mm=6,
    prop_diameter_in=5.1,
    prop_pitch_in=4.3,
    blade_count=3,
)

def marty_load_rating(load_index):
    """
    Human-readable interpretation.
    """

    if load_index < 1e12:
        return "Very Light"

    if load_index < 3e12:
        return "Efficient"

    if load_index < 6e12:
        return "Aggressive"

    if load_index < 1e13:
        return "Racing"

    return "Extremely Hot"


# ============================================================
# AUW (All-Up Weight) Calculation
# ============================================================

def dry_weight_kg(kwad: Kwad) -> float:
    """
    Compute the dry weight (no battery, no payload) of the quad in kilograms.

    Includes:
        - Frame
        - ESC
        - FC
        - VTX
        - Camera
        - Receiver
        - Motors
        - Props (if weight is defined)
        - Optional action camera

    Returns:
        float: Dry weight in kilograms.
    """
    total_g = (
        kwad.frame.dry_weight_g
        + kwad.esc.weight_g
        + kwad.fc.weight_g
        + kwad.vtx.weight_g
        + kwad.camera.weight_g
        + kwad.receiver.weight_g
    )

    if kwad.action_cam:
        total_g += kwad.action_cam.weight_g

    for m in kwad.motors:
        total_g += m.weight_g

    for p in kwad.props:
        if hasattr(p, "weight_g"):
            total_g += p.weight_g

    return total_g / 1000.0


def auw_kg(kwad: Kwad) -> float:
    """
    Compute the All‑Up Weight (AUW) including battery and payload.

    Returns:
        float: AUW in kilograms.
    """
    base = dry_weight_kg(kwad) * 1000.0
    base += kwad.battery.weight_g
    base += kwad.payload.weight_g
    return base / 1000.0


# ============================================================
# Static Thrust Model
# ============================================================

def static_thrust(motor: Motor, prop: Propeller, voltage_v: float, fuzz: phys.Fuzz) -> float:
    """
    Compute static thrust at full throttle for a given motor/prop/voltage.

    Applies:
        - Nonlinear throttle → RPM mapping
        - KV‑aware RPM limit (90% of theoretical max)
        - Diameter‑aware thrust model from physics.py

    Returns:
        float: Thrust in Newtons.
    """
    max_rpm = motor.kv_rpm_per_v * voltage_v * 0.90
    rpm = phys.throttle_to_rpm(1.0, motor.kv_rpm_per_v, voltage_v)
    rpm = min(rpm, max_rpm)

    return phys.static_thrust_simple(
        rpm=rpm,
        diameter_in=prop.diameter_in,
        pitch_in=prop.pitch_in,
        blades=getattr(prop, "blades", 2),
        fuzz=fuzz,
    )


# ============================================================
# Hover Throttle Solver
# ============================================================

def hover_throttle(kwad: Kwad, voltage_v: float, fuzz: phys.Fuzz) -> float:
    """
    Solve for the throttle percentage required to hover.

    Uses a binary search over throttle (0–1) to find the point where
    thrust_per_motor ≈ weight_per_motor.

    Returns:
        float: Hover throttle (0–1).
    """
    thrust_needed = phys.weight_from_mass(auw_kg(kwad))
    motor_count = len(kwad.motors)
    if motor_count == 0:
        return 0.0

    thrust_per_motor = thrust_needed / motor_count
    motor = kwad.motors[0]
    prop = kwad.props[0]

    max_rpm = motor.kv_rpm_per_v * voltage_v * 0.90

    lo, hi = 0.0, 1.0
    for _ in range(25):
        mid = (lo + hi) * 0.5
        rpm = phys.throttle_to_rpm(mid, motor.kv_rpm_per_v, voltage_v)
        rpm = min(rpm, max_rpm)

        thrust = phys.static_thrust_simple(
            rpm=rpm,
            diameter_in=prop.diameter_in,
            pitch_in=prop.pitch_in,
            blades=getattr(prop, "blades", 2),
            fuzz=fuzz,
        )

        if thrust > thrust_per_motor:
            hi = mid
        else:
            lo = mid

    return (lo + hi) * 0.5


# ============================================================
# Motor Current (Mechanical → Electrical)
# ============================================================

def motor_current_from_thrust(
    motor: Motor,
    prop: Propeller,
    thrust_n: float,
    voltage_v: float,
    fuzz: phys.Fuzz,
) -> float:
    """
    Convert required thrust → mechanical power → electrical power → current.

    Returns:
        float: Motor current in Amps.
    """
    p_mech = phys.prop_power_from_thrust(
        thrust_n=thrust_n,
        diameter_in=prop.diameter_in,
        blades=getattr(prop, "blades", 2),
        fuzz=fuzz,
    )

    eff_base = motor.motor_physics.efficiency if motor.motor_physics else 0.85
    eff = max(0.3, min(0.98, eff_base * fuzz.motor_efficiency_multiplier))

    p_elec = p_mech / eff
    return max(p_elec / max(voltage_v, 1e-3), 0.0)


# ============================================================
# Flight Time
# ============================================================

def flight_time_minutes(kwad: Kwad, avg_power_w: float) -> float:
    """
    Compute ideal flight time based on battery energy and average power draw.

    Returns:
        float: Flight time in minutes.
    """
    v_nom = phys.pack_voltage_nominal(kwad.battery.cells_series, kwad.battery.chemistry)
    energy_wh = phys.energy_wh_from_capacity(kwad.battery.capacity_mah, v_nom)
    return phys.ideal_flight_time_minutes(energy_wh, avg_power_w)


# ============================================================
# Thermal Modeling
# ============================================================

def motor_temperature_rise(motor: Motor, current_a: float, time_s: float, fuzz: phys.Fuzz) -> float:
    """
    Compute transient motor temperature rise over time_s seconds.

    Returns:
        float: Temperature rise in °C.
    """
    if not motor.motor_physics or not motor.thermal_model:
        return 0.0

    return phys.transient_temp_rise(
        phys.copper_loss(current_a, motor.resistance_ohm),
        motor.thermal_model,
        fuzz,
        time_s,
    )


def esc_temperature_rise(esc: ESC, current_a: float, time_s: float, fuzz: phys.Fuzz) -> float:
    """
    Compute transient ESC temperature rise over time_s seconds.

    Returns:
        float: Temperature rise in °C.
    """
    if not esc.thermal_model:
        return 0.0

    return phys.transient_temp_rise(
        phys.esc_loss(current_a, esc.mosfet_resistance_ohm, fuzz),
        esc.thermal_model,
        fuzz,
        time_s,
    )


# ============================================================
# Full-Throttle Performance Solver
# ============================================================

def full_throttle_performance(kwad: Kwad, fuzz: phys.Fuzz) -> tuple[float, float]:
    """
    Solve for self‑consistent full‑throttle voltage sag, current, and power.

    Iteratively:
        1. Compute thrust at current loaded voltage.
        2. Compute current required for that thrust.
        3. Compute new loaded voltage from sag.
        4. Repeat until convergence.

    Returns:
        (full_power_w, full_current_a)
    """
    motor_count = len(kwad.motors)
    if motor_count <= 0:
        return 0.0, 0.0

    motor = kwad.motors[0]
    prop = kwad.props[0]

    v_full = phys.pack_voltage_full(kwad.battery.cells_series, kwad.battery.chemistry)
    r_internal = phys.pack_internal_resistance(
        kwad.battery.cells_series, kwad.battery.chemistry, fuzz
    )

    v_loaded = v_full
    total_current = 0.0

    max_rpm_full = motor.kv_rpm_per_v * v_full * 0.90

    for _ in range(12):
        rpm = phys.throttle_to_rpm(1.0, motor.kv_rpm_per_v, v_loaded)
        rpm = min(rpm, max_rpm_full)

        thrust_per_motor = phys.static_thrust_simple(
            rpm=rpm,
            diameter_in=prop.diameter_in,
            pitch_in=prop.pitch_in,
            blades=getattr(prop, "blades", 2),
            fuzz=fuzz,
        )

        current_per_motor = motor_current_from_thrust(
            motor, prop, thrust_per_motor, v_loaded, fuzz
        )
        total_current = current_per_motor * motor_count

        new_v_loaded = phys.voltage_sag_under_load(v_full, total_current, r_internal)

        if abs(new_v_loaded - v_loaded) < 0.05:
            v_loaded = new_v_loaded
            break

        v_loaded = new_v_loaded

    full_power = v_loaded * total_current
    return full_power, total_current


# ============================================================
# High-Level Evaluation
# ============================================================

@dataclass
class KwadPerformance:
    """
    Container for all high‑level performance metrics of a quad.
    """
    hover_throttle: float
    max_thrust_total_n: float
    total_power_hover_w: float
    flight_time_min: float
    motor_temp_rise_c: float
    esc_temp_rise_c: float
    full_throttle_power_w: float
    full_throttle_current_a: float


def evaluate_kwad(kwad: Kwad, fuzz: phys.Fuzz) -> KwadPerformance:
    """
    Evaluate a quadcopter’s performance across:

        - Hover throttle
        - Hover power
        - Flight time
        - Thermal rise (motor & ESC)
        - Maximum static thrust
        - Full‑throttle sagged power & current

    Returns:
        KwadPerformance: Structured performance metrics.
    """
    v_full = phys.pack_voltage_full(kwad.battery.cells_series, kwad.battery.chemistry)

    # Initial hover throttle guess
    h_throttle = hover_throttle(kwad, v_full, fuzz)

    thrust_needed = phys.weight_from_mass(auw_kg(kwad))
    motor_count = len(kwad.motors)

    if motor_count <= 0:
        return KwadPerformance(
            hover_throttle=0.0,
            max_thrust_total_n=0.0,
            total_power_hover_w=0.0,
            flight_time_min=0.0,
            motor_temp_rise_c=0.0,
            esc_temp_rise_c=0.0,
            full_throttle_power_w=0.0,
            full_throttle_current_a=0.0,
        )

    thrust_per_motor = thrust_needed / motor_count
    motor = kwad.motors[0]
    prop = kwad.props[0]

    r_internal = phys.pack_internal_resistance(
        kwad.battery.cells_series, kwad.battery.chemistry, fuzz
    )

    # Hover sag loop
    v_loaded = v_full
    hover_current = 0.0
    current_per_motor = 0.0

    for _ in range(8):
        current_per_motor = motor_current_from_thrust(
            motor, prop, thrust_per_motor, v_loaded, fuzz
        )
        hover_current = current_per_motor * motor_count

        new_v_loaded = phys.voltage_sag_under_load(v_full, hover_current, r_internal)

        if abs(new_v_loaded - v_loaded) < 0.02:
            v_loaded = new_v_loaded
            break

        v_loaded = new_v_loaded

    # Recompute hover throttle at sagged voltage
    h_throttle = hover_throttle(kwad, v_loaded, fuzz)

    # Hover power
    total_power = v_loaded * hover_current * fuzz.hover_power_multiplier

    # Flight time
    ft = flight_time_minutes(kwad, total_power)

    # Thermal rise (approximate 60s hover)
    motor_temp = motor_temperature_rise(motor, current_per_motor, 60, fuzz)
    esc_temp = esc_temperature_rise(kwad.esc, current_per_motor, 60, fuzz)

    # Max thrust (no sag)
    max_thrust_per_motor = static_thrust(motor, prop, v_full, fuzz)
    max_total = max_thrust_per_motor * motor_count

    # Full-throttle sagged performance
    full_power, full_current = full_throttle_performance(kwad, fuzz)

    return KwadPerformance(
        hover_throttle=h_throttle,
        max_thrust_total_n=max_total,
        total_power_hover_w=total_power,
        flight_time_min=ft,
        motor_temp_rise_c=motor_temp,
        esc_temp_rise_c=esc_temp,
        full_throttle_power_w=full_power,
        full_throttle_current_a=full_current,
    )
