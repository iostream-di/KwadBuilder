# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 David Martinez

"""
basekwad.py — Pure Data Models for the simmulation engine.
==========================================================

This module defines the structural data models used throughout the 
simulation engine. These classes represent the physical components of a
multirotor UAV:

- Frame
- Motors
- Propellers
- Battery
- ESC
- Flight Controller
- VTX
- Camera / Action Camera
- Receiver
- Payload
- Kwad (aggregate)

This file intentionally contains **no physics, no computation, no assumptions,
and no magic numbers**. All calculations are performed in:

    - physics.py  (low‑level physics models)
    - engine.py   (system‑level performance solver)

These dataclasses serve as clean, declarative containers for component
specifications. They are designed to be stable and predictable — **do not rename
fields or classes**, as other modules depend on these exact names.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List


# ============================================================
# Frame
# ============================================================

@dataclass
class Frame:
    """
    Represents the physical frame of the quadcopter.

    Attributes:
        name: Human‑readable frame name.
        dry_weight_g: Weight of the bare frame (grams).
        arm_length_mm: Motor‑to‑center distance (millimeters).
        motor_mount_pattern: Bolt pattern (e.g., "16x16", "19x19").
        max_prop_size_in: Maximum supported prop diameter (inches).
        notes: Optional notes or metadata.
    """
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
    """
    Represents a brushless motor.

    Attributes:
        name: Motor name/model.
        kv_rpm_per_v: KV rating (RPM per volt).
        stator_size: Stator geometry (e.g., "2207").
        weight_g: Motor weight (grams).
        resistance_ohm: Winding resistance.
        no_load_current_a: Current at zero torque.
        max_current_a: Maximum safe current.
        motor_physics: Optional MotorPhysicsParams attached by engine.py.
    """
    name: str
    kv_rpm_per_v: float
    stator_size: str
    weight_g: float
    resistance_ohm: float
    no_load_current_a: float
    max_current_a: float
    motor_physics: Optional[object] = None


# ============================================================
# Propeller
# ============================================================

@dataclass
class Propeller:
    """
    Represents a propeller.

    Attributes:
        name: Prop name/model.
        diameter_in: Diameter (inches).
        pitch_in: Pitch (inches).
        blades: Number of blades (default: 2).
        notes: Optional notes.

    Provides:
        diameter_m: Diameter in meters.
        pitch_m: Pitch in meters.
    """
    name: str
    diameter_in: float
    pitch_in: float
    blades: int = 2
    notes: str = ""

    @property
    def diameter_m(self) -> float:
        """Return diameter in meters."""
        return self.diameter_in * 0.0254

    @property
    def pitch_m(self) -> float:
        """Return pitch in meters."""
        return self.pitch_in * 0.0254


# ============================================================
# Battery
# ============================================================

@dataclass
class Battery:
    """
    Represents a battery pack.

    Attributes:
        name: Battery name/model.
        cells_series: Number of cells in series (S count).
        capacity_mah: Capacity in mAh.
        weight_g: Weight in grams.
        c_rating: Discharge C‑rating.
        chemistry: Optional BatteryChemistry attached by engine.py.
    """
    name: str
    cells_series: int
    capacity_mah: float
    weight_g: float
    c_rating: float
    chemistry: Optional[object] = None


# ============================================================
# Electronics
# ============================================================

@dataclass
class ESC:
    """
    Represents an Electronic Speed Controller.

    Attributes:
        name: ESC name/model.
        continuous_current_a: Continuous current rating.
        burst_current_a: Burst current rating.
        weight_g: Weight in grams.
        mosfet_resistance_ohm: MOSFET conduction resistance.
        thermal_model: Optional ThermalModel attached by engine.py.
    """
    name: str
    continuous_current_a: float
    burst_current_a: float
    weight_g: float
    mosfet_resistance_ohm: float
    thermal_model: Optional[object] = None


@dataclass
class FlightController:
    """
    Represents a flight controller.

    Attributes:
        name: FC name/model.
        weight_g: Weight in grams.
        cpu: MCU type (e.g., F4, F7, H7).
        gyro: Gyro model (e.g., BMI270, MPU6000).
        thermal_model: Optional ThermalModel.
    """
    name: str
    weight_g: float
    cpu: str
    gyro: str
    thermal_model: Optional[object] = None


@dataclass
class VTX:
    """
    Represents a video transmitter.

    Attributes:
        name: VTX name/model.
        power_levels_mw: Supported output power levels (mW).
        weight_g: Weight in grams.
        thermal_model: Optional ThermalModel.
    """
    name: str
    power_levels_mw: List[int]
    weight_g: float
    thermal_model: Optional[object] = None


@dataclass
class Camera:
    """
    Represents an FPV camera.

    Attributes:
        name: Camera name/model.
        weight_g: Weight in grams.
        sensor: Sensor type.
        resolution: Resolution (e.g., "720p", "1080p").
        notes: Optional notes.
    """
    name: str
    weight_g: float
    sensor: str
    resolution: str
    notes: str = ""


@dataclass
class ActionCam:
    """
    Represents an HD action camera (GoPro, Insta360, etc.).

    Attributes:
        name: Camera name/model.
        weight_g: Weight in grams.
        resolution: Recording resolution.
        notes: Optional notes.
    """
    name: str
    weight_g: float
    resolution: str
    notes: str = ""


@dataclass
class Receiver:
    """
    Represents an RC receiver.

    Attributes:
        name: Receiver name/model.
        protocol: RC protocol (e.g., ELRS, Crossfire).
        weight_g: Weight in grams.
    """
    name: str
    protocol: str
    weight_g: float


@dataclass
class Payload:
    """
    Represents an arbitrary payload attached to the quad.

    Attributes:
        name: Payload name.
        weight_g: Weight in grams.
    """
    name: str
    weight_g: float


# ============================================================
# Kwad (aggregate)
# ============================================================

@dataclass
class Kwad:
    """
    Aggregate model representing a complete quadcopter.

    Contains:
        - Frame
        - Motors
        - Props
        - ESC
        - Flight Controller
        - VTX
        - FPV Camera
        - Receiver
        - Battery
        - Payload
        - Optional Action Camera

    Notes:
        This class intentionally contains **no computation**.
        All physics and performance calculations are handled in engine.py.
    """
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
