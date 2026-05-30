"""
physics.py — diameter-aware, tuned for realistic quad performance
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
        r = self.thermal_resistance_c_per_w * fuzz.thermal_resistance_multiplier
        c = self.thermal_capacitance_j_per_c * fuzz.thermal_capacitance_multiplier
        return r * c


# ============================================================
# Helpers for diameter-aware scaling
# ============================================================

def _clamp_diameter_in(diameter_in: float) -> float:
    # Keep within a sane multirotor range (whoop → X-class)
    return max(1.0, min(12.0, diameter_in))


def _ct_base_for_diameter(diameter_in: float) -> float:
    """
    Base CT scaling vs diameter:
    - Slightly higher CT for tiny props (low Re)
    - Slightly lower CT for very large props
    Anchored at 5" ≈ 0.048.
    """
    d = _clamp_diameter_in(diameter_in)
    base_ct_5 = 0.048
    # Small props: +10–15%, big props: −10–15%
    scale = (d / 5.0) ** -0.15
    return base_ct_5 * scale


def _fm_for_diameter(diameter_in: float) -> float:
    """
    Figure of merit vs diameter:
    - Tiny props are less efficient
    - 5" around 0.19
    - Larger props slightly more efficient
    """
    d = _clamp_diameter_in(diameter_in)
    fm_5 = 0.19
    scale = (d / 5.0) ** 0.10
    return max(0.14, min(0.24, fm_5 * scale))


# ============================================================
# Aerodynamics
# ============================================================

def weight_from_mass(mass_kg: float) -> float:
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
    Diameter-aware static thrust model.
    Behaves correctly for whoops, 5-inch, and larger props.
    """
    diameter_m = diameter_in * 0.0254
    pitch_m = pitch_in * 0.0254
    n = rpm / 60.0

    base_ct = _ct_base_for_diameter(diameter_in)

    p_over_d = pitch_m / max(diameter_m, 1e-6)
    ct_pitch = base_ct * (p_over_d ** 0.65)

    # Slightly weaker blade scaling so 3-blade whoops don't explode
    blade_factor = 1.0 + 0.10 * (blades - 2)

    ct = ct_pitch * blade_factor * fuzz.prop_thrust_multiplier

    thrust_n = ct * rho * (n ** 2) * (diameter_m ** 4)
    return thrust_n


def induced_power(thrust_n: float, disk_area_m2: float, fuzz: Fuzz,
                  rho: float = AIR_DENSITY_SEA_LEVEL) -> float:
    if thrust_n <= 0 or disk_area_m2 <= 0:
        return 0.0
    rho_adj = rho * fuzz.air_density_multiplier
    return (thrust_n ** 1.5) / sqrt(2 * rho_adj * disk_area_m2)


# ============================================================
# Throttle → RPM (nonlinear)
# ============================================================

def throttle_to_rpm(throttle: float, kv_rpm_per_v: float, voltage_v: float,
                    alpha: float = 1.32) -> float:
    """
    Nonlinear throttle → RPM mapping.
    alpha tuned for 5-inch; still reasonable for other sizes.
    """
    throttle = max(0.0, min(1.0, throttle))
    return (throttle ** alpha) * kv_rpm_per_v * voltage_v


# ============================================================
# Prop power model (mechanical)
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
    Diameter-aware induced + profile power estimate for a prop.
    Returns mechanical power in Watts.
    """
    diameter_m = diameter_in * 0.0254
    area = math.pi * (diameter_m / 2.0) ** 2

    p_i = induced_power(thrust_n, area, fuzz, rho)

    fm_base = _fm_for_diameter(diameter_in) if figure_of_merit is None else figure_of_merit
    fm = max(fm_base * fuzz.figure_of_merit_multiplier, 0.1)

    power = p_i / fm

    blade_loss_factor = 1.0 + 0.06 * (blades - 2)
    power *= blade_loss_factor

    # Slight non-ideal losses
    power *= 1.08

    return power


# ============================================================
# Motor electrical models
# ============================================================

def motor_back_emf_constant(kv_rpm_per_v: float) -> float:
    return 60.0 / (2 * pi * kv_rpm_per_v) if kv_rpm_per_v > 0 else 0.0


def motor_torque_constant(kv_rpm_per_v: float, fuzz: Fuzz) -> float:
    return motor_back_emf_constant(kv_rpm_per_v) * fuzz.motor_torque_multiplier


def motor_current_for_torque(torque_nm: float, kv_rpm_per_v: float,
                             fuzz: Fuzz, no_load_current_a: float = 0.0) -> float:
    kt = motor_torque_constant(kv_rpm_per_v, fuzz)
    return torque_nm / max(kt, 1e-9) + no_load_current_a


# ============================================================
# Battery models
# ============================================================

def pack_voltage_nominal(cells_series: int, chem: BatteryChemistry) -> float:
    return cells_series * chem.nominal_cell_voltage


def pack_voltage_full(cells_series: int, chem: BatteryChemistry) -> float:
    return cells_series * chem.full_cell_voltage


def pack_internal_resistance(cells_series: int, chem: BatteryChemistry, fuzz: Fuzz) -> float:
    return cells_series * chem.internal_resistance_per_cell_ohm * fuzz.battery_ir_multiplier


def voltage_sag_under_load(v_oc: float, current_a: float, r_internal: float) -> float:
    return v_oc - current_a * r_internal


def energy_wh_from_capacity(capacity_mah: float, nominal_voltage_v: float) -> float:
    return (capacity_mah / 1000.0) * nominal_voltage_v


def ideal_flight_time_minutes(energy_wh: float, avg_power_w: float) -> float:
    return (energy_wh / avg_power_w) * 60.0 if avg_power_w > 0 else 0.0


# ============================================================
# Thermal physics
# ============================================================

def copper_loss(i: float, r: float) -> float:
    return i * i * r


def esc_loss(current_a: float, r_mosfet: float, fuzz: Fuzz,
             switching_loss_w: float = 0.5) -> float:
    conduction = current_a * current_a * r_mosfet
    return (conduction + switching_loss_w) * fuzz.esc_loss_multiplier


def steady_state_temp_rise(power_loss_w: float, thermal_resistance_c_per_w: float,
                           fuzz: Fuzz) -> float:
    return power_loss_w * thermal_resistance_c_per_w * fuzz.thermal_resistance_multiplier


def transient_temp_rise(power_loss_w: float, thermal_model: ThermalModel,
                        fuzz: Fuzz, time_s: float) -> float:
    delta_ss = steady_state_temp_rise(
        power_loss_w, thermal_model.thermal_resistance_c_per_w, fuzz
    )
    tau = thermal_model.tau_seconds(fuzz)
    return delta_ss * (1 - exp(-time_s / tau))
