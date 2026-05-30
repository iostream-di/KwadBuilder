"""
engine.py

High‑level quadcopter performance engine for Kwadstream.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import physics as phys
from basekwad import (
    Kwad, Motor, Propeller, Battery, ESC, FlightController, VTX
)


# ============================================================
# AUW Calculation
# ============================================================

def auw_kg(kwad: Kwad) -> float:
    total_g = (
        kwad.frame.dry_weight_g
        + kwad.esc.weight_g
        + kwad.fc.weight_g
        + kwad.vtx.weight_g
        + kwad.camera.weight_g
        + kwad.receiver.weight_g
        + kwad.battery.weight_g
    )

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

def static_thrust(motor: Motor, prop: Propeller, voltage_v: float, fuzz: phys.Fuzz) -> float:
    rpm = phys.throttle_to_rpm(1.0, motor.kv_rpm_per_v, voltage_v)
    rpm = min(rpm, 120_000.0)

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
    thrust_needed = phys.weight_from_mass(auw_kg(kwad))
    motor_count = len(kwad.motors)
    if motor_count == 0:
        return 0.0

    thrust_per_motor = thrust_needed / motor_count
    motor = kwad.motors[0]
    prop = kwad.props[0]

    lo, hi = 0.0, 1.0
    for _ in range(25):
        mid = (lo + hi) * 0.5
        rpm = phys.throttle_to_rpm(mid, motor.kv_rpm_per_v, voltage_v)
        rpm = min(rpm, 120_000.0)

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
# Motor Current (mech → elec)
# ============================================================

def motor_current_from_thrust(
    motor: Motor,
    prop: Propeller,
    thrust_n: float,
    voltage_v: float,
    fuzz: phys.Fuzz,
) -> float:

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
    v_nom = phys.pack_voltage_nominal(kwad.battery.cells_series, kwad.battery.chemistry)
    energy_wh = phys.energy_wh_from_capacity(kwad.battery.capacity_mah, v_nom)
    return phys.ideal_flight_time_minutes(energy_wh, avg_power_w)


# ============================================================
# Thermal Modeling
# ============================================================

def motor_temperature_rise(motor: Motor, current_a: float, time_s: float, fuzz: phys.Fuzz) -> float:
    if not motor.motor_physics or not motor.thermal_model:
        return 0.0
    return phys.transient_temp_rise(
        phys.copper_loss(current_a, motor.resistance_ohm),
        motor.thermal_model,
        fuzz,
        time_s,
    )


def esc_temperature_rise(esc: ESC, current_a: float, time_s: float, fuzz: phys.Fuzz) -> float:
    if not esc.thermal_model:
        return 0.0
    return phys.transient_temp_rise(
        phys.esc_loss(current_a, esc.mosfet_resistance_ohm, fuzz),
        esc.thermal_model,
        fuzz,
        time_s,
    )


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

    v_full = phys.pack_voltage_full(kwad.battery.cells_series, kwad.battery.chemistry)
    thrust_needed = phys.weight_from_mass(auw_kg(kwad))
    motor_count = len(kwad.motors)
    thrust_per_motor = thrust_needed / motor_count

    motor = kwad.motors[0]
    prop = kwad.props[0]

    r_internal = phys.pack_internal_resistance(
        kwad.battery.cells_series, kwad.battery.chemistry, fuzz
    )

    # -------------------------------
    # SAG-AWARE THROTTLE SOLVER LOOP
    # -------------------------------
    v_loaded = v_full
    h_throttle = 0.5
    current_per_motor = 0.0

    for _ in range(10):

        # 1. Solve throttle at current sagged voltage
        h_throttle = hover_throttle(kwad, v_loaded, fuzz)

        # 2. Compute current at this throttle + voltage
        current_per_motor = motor_current_from_thrust(
            motor, prop, thrust_per_motor, v_loaded, fuzz
        )
        total_current = current_per_motor * motor_count

        # 3. Compute new sagged voltage
        new_v_loaded = phys.voltage_sag_under_load(v_full, total_current, r_internal)

        # 4. Convergence check
        if abs(new_v_loaded - v_loaded) < 0.01:
            v_loaded = new_v_loaded
            break

        v_loaded = new_v_loaded

    # Final electrical hover power
    total_power = v_loaded * total_current * fuzz.hover_power_multiplier

    # Flight time
    ft = flight_time_minutes(kwad, total_power)

    # Thermal
    motor_temp = motor_temperature_rise(motor, current_per_motor, 60, fuzz)
    esc_temp = esc_temperature_rise(kwad.esc, current_per_motor, 60, fuzz)

    # Max thrust
    max_total = static_thrust(motor, prop, v_full, fuzz) * motor_count

    return KwadPerformance(
        hover_throttle=h_throttle,
        max_thrust_total_n=max_total,
        total_power_hover_w=total_power,
        flight_time_min=ft,
        motor_temp_rise_c=motor_temp,
        esc_temp_rise_c=esc_temp,
    )
