"""
physics.py

Core physical constants, aerodynamic models, electrical models,
battery models, thermal models, and universal fuzz multipliers.

This file contains NO quad-specific logic.
All real-world deviation is handled through user-tunable fuzz factors.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt, exp


# ============================================================
# Fundamental constants
# ============================================================

GRAVITY = 9.80665
AIR_DENSITY_SEA_LEVEL = 1.225
STANDARD_TEMPERATURE = 288.15
BOLTZMANN = 1.380649e-23
R_AIR = 287.058


# ============================================================
# Universal Fuzz Model
# ============================================================

@dataclass
class Fuzz:
    """
    Universal user-tunable multipliers that adjust theoretical physics
    to match real-world logged data.

    All fuzz values default to 1.0 (no change).
    """
    # Aerodynamics
    air_density_multiplier: float = 1.0
    drag_multiplier: float = 1.0
    prop_thrust_multiplier: float = 1.0

    # Motor
    motor_torque_multiplier: float = 1.0
    motor_efficiency_multiplier: float = 1.0

    # Battery
    battery_ir_multiplier: float = 1.0

    # ESC
    esc_loss_multiplier: float = 1.0

    # Thermal
    thermal_resistance_multiplier: float = 1.0
    thermal_capacitance_multiplier: float = 1.0


# ============================================================
# Battery chemistry
# ============================================================

@dataclass(frozen=True)
class BatteryChemistry:
    nominal_cell_voltage: float
    full_cell_voltage: float
    empty_cell_voltage: float
    internal_resistance_per_cell_ohm: float


LIPO_DEFAULT = BatteryChemistry(
    nominal_cell_voltage=3.7,
    full_cell_voltage=4.2,
    empty_cell_voltage=3.3,
    internal_resistance_per_cell_ohm=0.003,
)


# ============================================================
# Motor physics parameters
# ============================================================

@dataclass(frozen=True)
class MotorPhysicsParams:
    kv_rpm_per_v: float
    resistance_ohm: float
    no_load_current_a: float
    efficiency: float  # 0–1


# ============================================================
# Thermal model parameters
# ============================================================

@dataclass(frozen=True)
class ThermalModel:
    thermal_resistance_c_per_w: float
    thermal_capacitance_j_per_c: float

    def tau_seconds(self, fuzz: Fuzz) -> float:
        """Thermal time constant τ = Rθ * Cth."""
        r = self.thermal_resistance_c_per_w * fuzz.thermal_resistance_multiplier
        c = self.thermal_capacitance_j_per_c * fuzz.thermal_capacitance_multiplier
        return r * c


# ============================================================
# Aerodynamics
# ============================================================

def weight_from_mass(mass_kg: float) -> float:
    return mass_kg * GRAVITY


def drag_force(airspeed_mps: float, area_m2: float, drag_coefficient: float,
               fuzz: Fuzz, rho: float = AIR_DENSITY_SEA_LEVEL) -> float:
    rho_adj = rho * fuzz.air_density_multiplier
    return 0.5 * rho_adj * airspeed_mps**2 * drag_coefficient * area_m2 * fuzz.drag_multiplier


def disk_area_from_diameter(diameter_m: float) -> float:
    r = diameter_m / 2
    return pi * r * r


def static_thrust_simple(rpm: float, diameter_m: float, pitch_m: float,
                         fuzz: Fuzz,
                         rho: float = AIR_DENSITY_SEA_LEVEL,
                         k_t: float = 1.0) -> float:
    rev_s = rpm / 60
    rho_adj = rho * fuzz.air_density_multiplier
    t = k_t * rho_adj * (rev_s**2) * (diameter_m**4)
    return t * fuzz.prop_thrust_multiplier


def induced_power(thrust_n: float, disk_area_m2: float,
                  fuzz: Fuzz,
                  rho: float = AIR_DENSITY_SEA_LEVEL) -> float:
    rho_adj = rho * fuzz.air_density_multiplier
    if disk_area_m2 <= 0:
        return 0
    return (thrust_n ** 1.5) / sqrt(2 * rho_adj * disk_area_m2)


def prop_power_from_thrust(thrust_n: float, diameter_m: float,
                           fuzz: Fuzz,
                           rho: float = AIR_DENSITY_SEA_LEVEL,
                           figure_of_merit: float = 0.6) -> float:
    area = disk_area_from_diameter(diameter_m)
    p_i = induced_power(thrust_n, area, fuzz, rho)
    return p_i / max(figure_of_merit, 1e-6)


# ============================================================
# Motor electrical models
# ============================================================

def motor_back_emf_constant(kv_rpm_per_v: float) -> float:
    if kv_rpm_per_v <= 0:
        return 0
    return 60.0 / (2 * pi * kv_rpm_per_v)


def motor_torque_constant(kv_rpm_per_v: float, fuzz: Fuzz) -> float:
    return motor_back_emf_constant(kv_rpm_per_v) * fuzz.motor_torque_multiplier


def motor_current_for_torque(torque_nm: float, kv_rpm_per_v: float,
                             fuzz: Fuzz,
                             no_load_current_a: float = 0.0) -> float:
    kt = motor_torque_constant(kv_rpm_per_v, fuzz)
    if kt <= 0:
        return 0
    return torque_nm / kt + no_load_current_a


def motor_voltage_for_rpm(rpm: float, kv_rpm_per_v: float) -> float:
    if kv_rpm_per_v <= 0:
        return 0
    return rpm / kv_rpm_per_v


def motor_input_power(voltage_v: float, current_a: float, fuzz: Fuzz) -> float:
    return voltage_v * current_a * fuzz.motor_efficiency_multiplier


def motor_output_power(input_power_w: float, efficiency: float, fuzz: Fuzz) -> float:
    eff = max(0.0, min(efficiency, 1.0)) * fuzz.motor_efficiency_multiplier
    return input_power_w * eff


# ============================================================
# Battery models
# ============================================================

def pack_voltage_nominal(cells_series: int, chem: BatteryChemistry) -> float:
    return cells_series * chem.nominal_cell_voltage


def pack_voltage_full(cells_series: int, chem: BatteryChemistry) -> float:
    return cells_series * chem.full_cell_voltage


def pack_voltage_empty(cells_series: int, chem: BatteryChemistry) -> float:
    return cells_series * chem.empty_cell_voltage


def pack_internal_resistance(cells_series: int, chem: BatteryChemistry, fuzz: Fuzz) -> float:
    return cells_series * chem.internal_resistance_per_cell_ohm * fuzz.battery_ir_multiplier


def voltage_sag_under_load(v_oc: float, current_a: float,
                           r_internal: float) -> float:
    return v_oc - current_a * r_internal


def energy_wh_from_capacity(capacity_mah: float, nominal_voltage_v: float) -> float:
    return (capacity_mah / 1000.0) * nominal_voltage_v


def ideal_flight_time_minutes(energy_wh: float, avg_power_w: float) -> float:
    if avg_power_w <= 0:
        return 0
    return (energy_wh / avg_power_w) * 60.0


# ============================================================
# Thermal physics
# ============================================================

def copper_loss(i: float, r: float) -> float:
    return i * i * r


def iron_loss(rpm: float, k_iron: float = 1e-6) -> float:
    return k_iron * (rpm ** 2)


def esc_loss(current_a: float, r_mosfet: float,
             fuzz: Fuzz,
             switching_loss_w: float = 0.5) -> float:
    conduction = current_a * current_a * r_mosfet
    return (conduction + switching_loss_w) * fuzz.esc_loss_multiplier


def steady_state_temp_rise(power_loss_w: float, thermal_resistance_c_per_w: float,
                           fuzz: Fuzz) -> float:
    return power_loss_w * thermal_resistance_c_per_w * fuzz.thermal_resistance_multiplier


def transient_temp_rise(power_loss_w: float, thermal_model: ThermalModel,
                        fuzz: Fuzz, time_s: float) -> float:
    delta_ss = steady_state_temp_rise(
        power_loss_w,
        thermal_model.thermal_resistance_c_per_w,
        fuzz
    )
    tau = thermal_model.tau_seconds(fuzz)
    return delta_ss * (1 - exp(-time_s / tau))


def cooled_temperature(current_temp_c: float, ambient_c: float,
                       thermal_model: ThermalModel, fuzz: Fuzz, time_s: float) -> float:
    tau = thermal_model.tau_seconds(fuzz)
    return ambient_c + (current_temp_c - ambient_c) * exp(-time_s / tau)
