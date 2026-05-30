"""
basekwad.py

Pure data models for Kwadstream.
No physics, no computation, no assumptions, no magic numbers.

These classes describe the components of a quadcopter.
All calculations are performed in engine.py using physics.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List


# ============================================================
# Frame
# ============================================================

@dataclass
class Frame:
    name: str
    dry_weight_g: float
    arm_length_mm: float
    motor_mount_pattern: str
    max_prop_size_in: float
    notes: str = ""


# ============================================================
# Motor
# ============================================================

@dataclass
class Motor:
    name: str
    kv_rpm_per_v: float
    stator_size: str  # e.g. "2207"
    weight_g: float
    resistance_ohm: float
    no_load_current_a: float
    max_current_a: float
    motor_physics: Optional[object] = None  # engine.py attaches MotorPhysicsParams


# ============================================================
# Propeller
# ============================================================

@dataclass
class Propeller:
    name: str
    diameter_in: float
    pitch_in: float
    blades: int = 2
    notes: str = ""

    @property
    def diameter_m(self) -> float:
        return self.diameter_in * 0.0254

    @property
    def pitch_m(self) -> float:
        return self.pitch_in * 0.0254


# ============================================================
# Battery
# ============================================================

@dataclass
class Battery:
    name: str
    cells_series: int
    capacity_mah: float
    weight_g: float
    c_rating: float
    chemistry: Optional[object] = None  # engine.py attaches BatteryChemistry


# ============================================================
# Electronics
# ============================================================

@dataclass
class ESC:
    name: str
    continuous_current_a: float
    burst_current_a: float
    weight_g: float
    mosfet_resistance_ohm: float
    thermal_model: Optional[object] = None  # engine.py attaches ThermalModel


@dataclass
class FlightController:
    name: str
    weight_g: float
    cpu: str
    gyro: str
    thermal_model: Optional[object] = None


@dataclass
class VTX:
    name: str
    power_levels_mw: List[int]
    weight_g: float
    thermal_model: Optional[object] = None


@dataclass
class Camera:
    name: str
    weight_g: float
    sensor: str
    resolution: str
    notes: str = ""


@dataclass
class ActionCam:
    name: str
    weight_g: float
    resolution: str
    notes: str = ""


@dataclass
class Receiver:
    name: str
    protocol: str
    weight_g: float


@dataclass
class Payload:
    name: str
    weight_g: float

# ============================================================
# Kwad (aggregate)
# ============================================================

@dataclass
class Kwad:
    name: str
    frame: Frame
    motors: List[Motor]
    props: List[Propeller]
    esc: ESC
    fc: FlightController
    vtx: VTX
    camera: Camera
    receiver: Receiver
    battery: Battery
    payload: Payload
    action_cam: Optional[ActionCam] = None

    # No weight calculations here — engine.py handles all computation.
