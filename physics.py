# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 David Martinez

"""
physics.py — Multirotor Propulsion & Power Modeling Engine
==========================================================

This module implements a diameter‑aware, semi‑empirical physics engine for
multirotor UAVs. It models:

- Static thrust generation
- Induced power (momentum theory)
- Profile drag power
- Motor electrical behavior
- Battery voltage sag
- Thermal rise (steady‑state & transient)
- Diameter‑dependent CT and Figure‑of‑Merit scaling
- Nonlinear throttle → RPM mapping

The goal is not perfect CFD accuracy, but a *realistic, stable, and tunable*
model that behaves correctly across:

- Whoops (1.6–2.0")
- Toothpicks (2.5–3")
- Freestyle quads (5")
- Long‑range rigs (6–7")
- Utility platforms (8–12")

This engine is used by higher‑level simulation and sizing tools. All function
names, parameters, and return values are stable and relied upon by other
modules — **do not rename anything**.

The model is intentionally “fuzzable” via the `Fuzz` class, allowing global
multipliers to tune realism, compensate for unknowns, or match real‑world
bench data.

This file is licensed under GPL‑3.0‑or‑later. You may modify and redistribute
it under the terms of that license.
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from math import pi, sqrt, exp

# ============================================================
# Fundamental constants
# ============================================================

GRAVITY = 9.80665
AIR_DENSITY_SEA_LEVEL = 1.225


# ============================================================
# Universal Fuzz Model
# ============================================================

@dataclass
class Fuzz:
    """
    Global multipliers used to tune realism across the entire engine.

    These allow adjusting thrust, drag, thermal behavior, battery IR,
    and other subsystems without modifying core equations.

    This is essential because real‑world multirotor behavior varies
    significantly with prop brand, ESC firmware, motor design, and
    environmental conditions.
    """
    air_density_multiplier: float = 1.0
    drag_multiplier: float = 1.0
    prop_thrust_multiplier: float = 1.0

    motor_torque_multiplier: float = 1.0
    motor_efficiency_multiplier: float = 1.0

    battery_ir_multiplier: float = 1.0
    esc_loss_multiplier: float = 1.0

    thermal_resistance_multiplier: float = 1.0
    thermal_capacitance_multiplier: float = 1.0

    thrust_coefficient_multiplier: float = 1.0
    figure_of_merit_multiplier: float = 1.0
    hover_power_multiplier: float = 1.0


# ============================================================
# Battery chemistry
# ============================================================

@dataclass(frozen=True)
class BatteryChemistry:
    """
    Defines the electrical characteristics of a battery chemistry.

    Attributes:
        nominal_cell_voltage: Voltage at nominal charge.
        full_cell_voltage: Voltage at full charge.
        empty_cell_voltage: Minimum safe voltage.
        internal_resistance_per_cell_ohm: IR per cell (Ohms).
    """
    nominal_cell_voltage: float
    full_cell_voltage: float
    empty_cell_voltage: float
    internal_resistance_per_cell_ohm: float


# Default LiPo chemistry
LIPO_DEFAULT = BatteryChemistry(
    nominal_cell_voltage=3.7,
    full_cell_voltage=4.2,
    empty_cell_voltage=3.3,
    internal_resistance_per_cell_ohm=0.012,
)


# ============================================================
# Motor physics parameters
# ============================================================

@dataclass(frozen=True)
class MotorPhysicsParams:
    """
    Basic electrical parameters for a brushless motor.

    Attributes:
        kv_rpm_per_v: Motor KV constant.
        resistance_ohm: Winding resistance.
        no_load_current_a: Current at zero torque.
        efficiency: Peak motor efficiency (0–1).
    """
    kv_rpm_per_v: float
    resistance_ohm: float
    no_load_current_a: float
    efficiency: float


# ============================================================
# Thermal model
# ============================================================

@dataclass(frozen=True)
class ThermalModel:
    """
    First‑order thermal model for ESCs or motors.

    Attributes:
        thermal_resistance_c_per_w: °C rise per watt at steady state.
        thermal_capacitance_j_per_c: Thermal mass (J/°C).

    The time constant τ = R * C determines how fast temperature rises.
    """
    thermal_resistance_c_per_w: float
    thermal_capacitance_j_per_c: float

    def tau_seconds(self, fuzz: Fuzz) -> float:
        """Return thermal time constant τ (seconds)."""
        r = self.thermal_resistance_c_per_w * fuzz.thermal_resistance_multiplier
        c = self.thermal_capacitance_j_per_c * fuzz.thermal_capacitance_multiplier
        return r * c


# ============================================================
# Diameter-aware scaling helpers
# ============================================================

def _clamp_diameter_in(diameter_in: float) -> float:
    """Clamp prop diameter to a safe modeling range."""
    return max(1.0, min(12.0, diameter_in))


def _ct_base_for_diameter(diameter_in: float) -> float:
    """
    Base thrust coefficient scaling vs diameter.

    Empirically:
    - Tiny props have slightly higher CT
    - Large props have slightly lower CT
    - 5" baseline ≈ 0.078
    """
    d = _clamp_diameter_in(diameter_in)
    base_ct_5 = 0.078
    scale = (d / 5.0) ** -0.15
    return base_ct_5 * scale


def _fm_for_diameter(diameter_in: float) -> float:
    """
    Figure of Merit scaling vs diameter.

    - Tiny props are less efficient
    - 5" ≈ 0.18
    - Large props slightly more efficient
    - Clamped to realistic multirotor ranges
    """
    d = _clamp_diameter_in(diameter_in)
    fm_5 = 0.18
    scale = (d / 5.0) ** 0.10
    return max(0.16, min(0.24, fm_5 * scale))


def _motor_efficiency_for_load(load_fraction: float) -> float:
    """
    Simple motor efficiency curve vs load fraction (0–1).

    Peak efficiency occurs around 40–60% load.
    Efficiency falls off at very low or very high load.
    """
    x = max(0.0, min(1.0, load_fraction))
    return 0.75 + 0.17 * (1.0 - (2.0 * x - 1.0) ** 2)


# ============================================================
# Aerodynamics
# ============================================================

def weight_from_mass(mass_kg: float) -> float:
    """Convert mass (kg) to weight (N)."""
    return mass_kg * GRAVITY


def static_thrust_simple(
    rpm: float,
    diameter_in: float,
    pitch_in: float,
    blades: int,
    fuzz: Fuzz,
    rho: float = AIR_DENSITY_SEA_LEVEL,
) -> float:
    """
    Compute static thrust using a diameter‑aware CT model.

    Includes:
    - Pitch scaling
    - Blade count scaling
    - Tip Mach dropoff (CT reduction near Mach 0.7–0.9)
    - Fuzz multipliers

    This model is stable across 2"–12" props.
    """
    rpm = max(0.0, min(rpm, 200_000.0))  # Safety clamp

    diameter_m = diameter_in * 0.0254
    pitch_m = pitch_in * 0.0254
    n = rpm / 60.0  # rev/sec

    base_ct = _ct_base_for_diameter(diameter_in)

    # Pitch influence
    p_over_d = pitch_m / max(diameter_m, 1e-6)
    ct_pitch = base_ct * (p_over_d ** 0.65)

    # Blade influence (2-blade baseline)
    blade_factor = 1.0 + 0.10 * (blades - 2)

    ct = ct_pitch * blade_factor * fuzz.prop_thrust_multiplier

    # Tip Mach dropoff
    tip_speed = pi * diameter_m * n
    mach = tip_speed / 343.0
    ct *= 1.0 / (1.0 + 3.0 * max(mach - 0.6, 0.0))

    return ct * rho * (n ** 2) * (diameter_m ** 4)


def induced_power(thrust_n: float, disk_area_m2: float, fuzz: Fuzz,
                  rho: float = AIR_DENSITY_SEA_LEVEL) -> float:
    """
    Ideal induced power from momentum theory.

    P_i = T^(3/2) / sqrt(2 ρ A)
    """
    if thrust_n <= 0 or disk_area_m2 <= 0:
        return 0.0

    rho_adj = rho * fuzz.air_density_multiplier
    return (thrust_n ** 1.5) / sqrt(2 * rho_adj * disk_area_m2)


# ============================================================
# Throttle → RPM mapping
# ============================================================

def throttle_to_rpm(throttle: float, kv_rpm_per_v: float, voltage_v: float,
                    alpha: float = 1.32) -> float:
    """
    Nonlinear throttle → RPM mapping.

    alpha = 1.32 was tuned for 5" quads but behaves reasonably across sizes.
    """
    throttle = max(0.0, min(1.0, throttle))
    return (throttle ** alpha) * kv_rpm_per_v * voltage_v


# ============================================================
# Prop power model
# ============================================================

def prop_power_from_thrust(
    thrust_n: float,
    diameter_in: float,
    blades: int,
    fuzz: Fuzz,
    rho: float = AIR_DENSITY_SEA_LEVEL,
    figure_of_merit: float | None = None,
) -> float:
    """
    Compute mechanical power required to generate a given thrust.

    Includes:
    - Induced power (momentum theory)
    - Diameter‑dependent Figure of Merit
    - FM dropoff at high thrust
    - Profile drag term (dominant at high thrust)
    - Global non‑ideal losses
    """
    diameter_m = diameter_in * 0.0254
    area = math.pi * (diameter_m / 2.0) ** 2

    p_i = induced_power(thrust_n, area, fuzz, rho)

    fm_base = _fm_for_diameter(diameter_in) if figure_of_merit is None else figure_of_merit
    fm = max(fm_base * fuzz.figure_of_merit_multiplier, 0.1)

    thrust_ratio = thrust_n / (thrust_n + 15.0)
    fm *= 1.0 - 0.65 * (thrust_ratio ** 1.7)

    power = p_i / fm

    drag_scale = thrust_ratio ** 3
    p_profile = drag_scale * (thrust_n ** (4/3)) * diameter_in
    power += p_profile

    return power * 1.25  # Global losses


# ============================================================
# Motor electrical models
# ============================================================

def motor_back_emf_constant(kv_rpm_per_v: float) -> float:
    """Return motor back‑EMF constant (V per rad/s)."""
    return 60.0 / (2 * pi * kv_rpm_per_v) if kv_rpm_per_v > 0 else 0.0


def motor_torque_constant(kv_rpm_per_v: float, fuzz: Fuzz) -> float:
    """Return torque constant Kt (Nm/A)."""
    return motor_back_emf_constant(kv_rpm_per_v) * fuzz.motor_torque_multiplier


def motor_current_for_torque(torque_nm: float, kv_rpm_per_v: float,
                             fuzz: Fuzz, no_load_current_a: float = 0.0) -> float:
    """
    Compute motor current required to generate a given torque.
    """
    kt = motor_torque_constant(kv_rpm_per_v, fuzz)
    return torque_nm / max(kt, 1e-9) + no_load_current_a


def motor_output_power(input_power_w: float, load_fraction: float, fuzz: Fuzz) -> float:
    """
    Apply motor efficiency curve to electrical input power.
    """
    eff_curve = _motor_efficiency_for_load(load_fraction)
    eff = max(0.3, min(0.98, eff_curve * fuzz.motor_efficiency_multiplier))
    return input_power_w * eff


# ============================================================
# Battery models
# ============================================================

def pack_voltage_nominal(cells_series: int, chem: BatteryChemistry) -> float:
    """Nominal pack voltage."""
    return cells_series * chem.nominal_cell_voltage


def pack_voltage_full(cells_series: int, chem: BatteryChemistry) -> float:
    """Full‑charge pack voltage."""
    return cells_series * chem.full_cell_voltage


def pack_internal_resistance(cells_series: int, chem: BatteryChemistry, fuzz: Fuzz) -> float:
    """Total pack internal resistance."""
    return cells_series * chem.internal_resistance_per_cell_ohm * fuzz.battery_ir_multiplier


def voltage_sag_under_load(v_oc: float, current_a: float, r_internal: float) -> float:
    """Compute voltage sag under load."""
    return v_oc - current_a * r_internal


def energy_wh_from_capacity(capacity_mah: float, nominal_voltage_v: float) -> float:
    """Convert mAh + V into watt‑hours."""
    return (capacity_mah / 1000.0) * nominal_voltage_v


def ideal_flight_time_minutes(energy_wh: float, avg_power_w: float) -> float:
    """Ideal flight time in minutes."""
    return (energy_wh / avg_power_w) * 60.0 if avg_power_w > 0 else 0.0


# ============================================================
# Thermal physics
# ============================================================

def copper_loss(i: float, r: float) -> float:
    """Copper (I²R) loss."""
    return i * i * r


def esc_loss(current_a: float, r_mosfet: float, fuzz: Fuzz,
             switching_loss_w: float = 0.5) -> float:
    """
    ESC conduction + switching losses.
    """
    conduction = current_a * current_a * r_mosfet
    return (conduction + switching_loss_w) * fuzz.esc_loss_multiplier


def steady_state_temp_rise(power_loss_w: float, thermal_resistance_c_per_w: float,
                           fuzz: Fuzz) -> float:
    """Steady‑state temperature rise (°C)."""
    return power_loss_w * thermal_resistance_c_per_w * fuzz.thermal_resistance_multiplier


def transient_temp_rise(power_loss_w: float, thermal_model: ThermalModel,
                        fuzz: Fuzz, time_s: float) -> float:
    """
    First‑order thermal transient:
    ΔT(t) = ΔT_ss * (1 - e^(-t/τ))
    """
    delta_ss = steady_state_temp_rise(
        power_loss_w, thermal_model.thermal_resistance_c_per_w, fuzz
    )
    tau = thermal_model.tau_seconds(fuzz)
    return delta_ss * (1 - exp(-time_s / tau))
