# build_kwad.py

import physics as phys
from basekwad import (
    Frame, Motor, Propeller, Battery, ESC, FlightController,
    VTX, Camera, Receiver, ActionCam, Kwad
)


def build_kwad_and_fuzz(cfg):
    """
    Build the Kwad object and Fuzz object from the UI config.
    This keeps streamlitapp.py clean and modular.
    """

    # ---------------------------------------------------------
    # Propeller
    # ---------------------------------------------------------
    prop = Propeller(
        name="Prop",
        diameter_in=cfg["prop_diameter"],
        pitch_in=cfg["prop_pitch"],
        blades=int(cfg["prop_blades"]),
        notes=""
    )

    # ---------------------------------------------------------
    # Motors
    # ---------------------------------------------------------
    motors = [
        Motor(
            name="Motor",
            kv_rpm_per_v=cfg["motor_kv"],
            stator_size=f"{int(cfg['motor_stator_d'])}{int(cfg['motor_stator_h'])}",
            weight_g=cfg["motor_weight"],
            resistance_ohm=0.05,
            no_load_current_a=1.0,
            max_current_a=cfg["motor_current_rating"],
        )
        for _ in range(cfg["motor_count"])
    ]

    # ---------------------------------------------------------
    # Battery
    # ---------------------------------------------------------
    battery = Battery(
        name="Battery",
        cells_series=int(cfg["lipo_cells"]),
        capacity_mah=cfg["lipo_capacity"],
        weight_g=cfg["lipo_weight"],
        c_rating=cfg["lipo_c"],
        chemistry=phys.LIPO_DEFAULT,
    )

    # ---------------------------------------------------------
    # Frame
    # ---------------------------------------------------------
    frame = Frame(
        name="Frame",
        dry_weight_g=cfg["frame_weight"],
        arm_length_mm=cfg["frame_wheelbase"] / 2,
        motor_mount_pattern="16x16",
        max_prop_size_in=cfg["frame_prop_fit"],
    )

    # ---------------------------------------------------------
    # Flight Controller
    # ---------------------------------------------------------
    fc = FlightController(
        name="FC",
        weight_g=cfg["fc_weight"],
        cpu=str(cfg["fc_cpu"]),
        gyro="BMI270",
    )

    # ---------------------------------------------------------
    # ESC
    # ---------------------------------------------------------
    esc = ESC(
        name="ESC",
        continuous_current_a=cfg["esc_current_rating"],
        burst_current_a=cfg["esc_current_rating"] * 1.2,
        weight_g=cfg["esc_weight"],
        mosfet_resistance_ohm=0.002,
    )

    # ---------------------------------------------------------
    # VTX
    # ---------------------------------------------------------
    vtx = VTX(
        name="VTX",
        power_levels_mw=[25, 200, 400, int(cfg["video_power"])],
        weight_g=cfg["video_weight"],
    )

    # ---------------------------------------------------------
    # Camera
    # ---------------------------------------------------------
    camera = Camera(
        name="FPV Cam",
        weight_g=0.0,
        sensor="1/3 CMOS",
        resolution="720p",
    )

    # ---------------------------------------------------------
    # Receiver
    # ---------------------------------------------------------
    receiver = Receiver(
        name="RX",
        protocol="ELRS" if cfg["rx_elrs"] else "Other",
        weight_g=cfg["rx_weight"],
    )

    # ---------------------------------------------------------
    # Action Cam
    # ---------------------------------------------------------
    action_cam = None
    if cfg["cam_weight"] > 0:
        action_cam = ActionCam(
            name="Action Cam",
            weight_g=cfg["cam_weight"],
            resolution="4K",
        )

    # ---------------------------------------------------------
    # Build Kwad
    # ---------------------------------------------------------
    kwad = Kwad(
        name="User Kwad",
        frame=frame,
        motors=motors,
        props=[prop] * len(motors),
        esc=esc,
        fc=fc,
        vtx=vtx,
        camera=camera,
        receiver=receiver,
        battery=battery,
        action_cam=action_cam,
    )

    # ---------------------------------------------------------
    # Build Fuzz Object
    # ---------------------------------------------------------
    fuzz = phys.Fuzz(
        air_density_multiplier=cfg["fuzz_air"],
        drag_multiplier=cfg["fuzz_drag"],
        prop_thrust_multiplier=cfg["fuzz_prop"],
        motor_torque_multiplier=cfg["fuzz_motor_torque"],
        motor_efficiency_multiplier=cfg["fuzz_motor_eff"],
        battery_ir_multiplier=cfg["fuzz_batt_ir"],
        esc_loss_multiplier=cfg["fuzz_esc_loss"],
        thermal_resistance_multiplier=cfg["fuzz_thermal_r"],
        thermal_capacitance_multiplier=cfg["fuzz_thermal_c"],
    )

    return kwad, fuzz
