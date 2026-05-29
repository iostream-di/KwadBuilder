"""
physics.py

Core physical constants, aerodynamic models, electrical models,
battery models, thermal models, and universal fuzz multipliers.

This file contains NO quad-specific logic.
All real-world deviation is handled through user-tunable fuzz factors.
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

    # Adjustments
    thrust_coefficient_multiplier: float = 1.0
    figure_of_merit_multiplier: float = 1.0
    hover_power_multiplier: float = 1.0


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
    internal_resistance_per_cell_ohm=0.0045,
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


def static_thrust_simple(
    rpm: float,
    diameter_in: float,
    pitch_in: float,
    blades: int,
    fuzz: Fuzz,
    rho: float = AIR_DENSITY_SEA_LEVEL,
) -> float:
    """
    Static thrust model that accounts for:
    - Diameter
    - Pitch
    - Blade count
    - Air density
    Returns thrust in Newtons.
    """

    diameter_m = diameter_in * 0.0254
    pitch_m = pitch_in * 0.0254
    n = rpm / 60.0  # rev/s

    # Pitch-to-diameter ratio
    p_over_d = pitch_m / diameter_m

    # Base thrust coefficient for a 2-blade reference prop
    base_ct = 0.08  # tuned constant, refine against real data

    # Pitch influence: higher pitch → higher CT
    ct_pitch = base_ct * (p_over_d ** 0.7)

    # Blade count influence: more blades → more thrust, more drag
    # 2 blades = 1.0, 3 blades ≈ 1.15, 4 blades ≈ 1.25, etc.
    blade_factor = 1.0 + 0.15 * (blades - 2)

    ct = ct_pitch * blade_factor

    # (Fuzz multiplier can be re-enabled later)
    # ct *= fuzz.thrust_coefficient_multiplier

    thrust_n = ct * rho * (n ** 2) * (diameter_m ** 4)
    return thrust_n


def induced_power(thrust_n: float, disk_area_m2: float,
                  fuzz: Fuzz,
                  rho: float = AIR_DENSITY_SEA_LEVEL) -> float:
    rho_adj = rho * fuzz.air_density_multiplier
    if disk_area_m2 <= 0 or thrust_n <= 0:
        return 0.0
    # Equivalent to T * v_i with v_i = sqrt(T / (2 ρ A))
    return (thrust_n ** 1.5) / sqrt(2 * rho_adj * disk_area_m2)

def rpm_under_load(
    throttle: float,
    kv_rpm_per_v: float,
    voltage_v: float,
    current_a: float,
    motor_resistance_ohm: float,
    alpha: float = 1.35,
) -> float:
    """
    Compute RPM under load considering:
    - nonlinear throttle curve
    - back-EMF
    - winding resistance voltage drop
    """
    # Ideal no-load RPM from throttle curve
    rpm_ideal = (throttle ** alpha) * kv_rpm_per_v * voltage_v

    # Back-EMF voltage at that RPM
    v_back = rpm_ideal / kv_rpm_per_v

    # Voltage lost to winding resistance
    v_drop = current_a * motor_resistance_ohm

    # Effective voltage available to spin the motor
    v_eff = max(voltage_v - v_drop, 0.0)

    # If back-EMF exceeds available voltage, motor saturates
    if v_back > v_eff:
        return v_eff * kv_rpm_per_v

    return rpm_ideal



def prop_disk_area_from_diameter_in(diameter_in: float) -> float:
    diameter_m = diameter_in * 0.0254
    return math.pi * (diameter_m / 2.0) ** 2


def throttle_to_rpm(throttle: float, kv_rpm_per_v: float, voltage_v: float, alpha: float = 1.35) -> float:
    """
    Nonlinear throttle → RPM mapping.
    alpha > 1 makes low throttle weaker and pushes hover throttle upward.
    """
    throttle = max(0.0, min(1.0, throttle))
    return (throttle ** alpha) * kv_rpm_per_v * voltage_v


def prop_power_from_thrust(
    thrust_n: float,
    diameter_in: float,
    blades: int,
    fuzz: Fuzz,
    rho: float = AIR_DENSITY_SEA_LEVEL,
    figure_of_merit: float = 0.22,
) -> float:
    """
    Induced + profile power estimate for a prop:
    - Uses induced power from momentum theory
    - Divides by figure of merit
    - Adds extra loss for higher blade count
    Returns power in Watts.
    """

    diameter_m = diameter_in * 0.0254
    area = math.pi * (diameter_m / 2.0) ** 2

    # Ideal induced power
    p_i = induced_power(thrust_n, area, fuzz, rho)

    # Effective figure of merit (clamped)
    fm = max(figure_of_merit, 0.1)

    power = p_i / fm

    # More blades → more profile drag → more power required
    # 2 blades = 1.0, 3 blades ≈ 1.1, 4 blades ≈ 1.2, etc.
    blade_loss_factor = 1.0 + 0.10 * (blades - 2)
    power *= blade_loss_factor

    # Additional non-ideal losses (tip vortices, inflow distortion, etc.)
    power *= 1.15  # 15% extra losses

    # (Fuzz multipliers can be re-enabled later)
    # power *= fuzz.hover_power_multiplier
    # power /= max(fuzz.figure_of_merit_multiplier, 0.3)

    return power


# ============================================================
# Motor electrical models
# ============================================================

def motor_back_emf_constant(kv_rpm_per_v: float) -> float:
    if kv_rpm_per_v <= 0:
        return 0.0
    return 60.0 / (2 * pi * kv_rpm_per_v)


def motor_torque_constant(kv_rpm_per_v: float, fuzz: Fuzz) -> float:
    return motor_back_emf_constant(kv_rpm_per_v) * fuzz.motor_torque_multiplier


def motor_current_for_torque(torque_nm: float, kv_rpm_per_v: float,
                             fuzz: Fuzz,
                             no_load_current_a: float = 0.0) -> float:
    kt = motor_torque_constant(kv_rpm_per_v, fuzz)
    if kt <= 0:
        return 0.0
    return torque_nm / kt + no_load_current_a


def motor_voltage_for_rpm(rpm: float, kv_rpm_per_v: float) -> float:
    if kv_rpm_per_v <= 0:
        return 0.0
    return rpm / kv_rpm_per_v


def motor_input_power(voltage_v: float, current_a: float, fuzz: Fuzz) -> float:
    """
    Electrical input power to the motor.

    NOTE:
    - Input power is simply V * I.
    - Efficiency and fuzz are applied when going from input → output power,
      not the other way around.
    """
    return voltage_v * current_a


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
        return 0.0
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
