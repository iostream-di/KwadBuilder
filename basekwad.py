# basekwad.py
import math


# ---------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def nominal_voltage(cells: int, hv: bool = False) -> float:
    return (4.35 if hv else 3.8) * cells


def pack_internal_resistance_ohm(cells: int, capacity_mah: int) -> float:
    """
    Realistic IR model:
    ~2.5 mΩ per cell at 1Ah, scaled by capacity^-0.7
    """
    capacity_ah = max(capacity_mah / 1000.0, 0.1)
    base_per_cell = 0.0025  # 2.5 mΩ
    scale = (1.0 / capacity_ah) ** 0.7
    return cells * base_per_cell * scale


def loaded_voltage(v_nom: float, current_a: float, r_pack: float) -> float:
    sag = current_a * r_pack
    return max(v_nom - sag, v_nom * 0.6)


def rpm_no_load(kv: float, voltage: float) -> float:
    return kv * voltage


def rpm_loaded(no_load_rpm: float) -> float:
    return no_load_rpm * 0.78


def prop_disk_area(diameter_in: float) -> float:
    d_m = diameter_in * 0.0254
    r_m = d_m / 2
    return math.pi * r_m * r_m


def pitch_speed_mps(pitch_in: float, rpm: float) -> float:
    return pitch_in * 0.0254 * rpm / 60.0


# ---------------------------------------------------------
# Component classes
# ---------------------------------------------------------

class Propeller:
    def __init__(self, diameter, pitch, blades, weight):
        self.diameter = diameter
        self.pitch = pitch
        self.blades = blades
        self.weight = weight


class Motor:
    def __init__(self, stator_height, stator_diameter, kv, weight, prop: Propeller, current_rating=40):
        self.stator_height = stator_height
        self.stator_width = stator_diameter
        self.kv = kv
        self.weight = weight
        self.prop = prop
        self.current_rating = current_rating  # continuous-ish rating in amps

    # -----------------------------------------------------
    # Thrust model (calibrated)
    # -----------------------------------------------------
    def compute_thrust(self, voltage):
        prop = self.prop
        area = prop_disk_area(prop.diameter)
        area_ref = prop_disk_area(5.0)

        rpm_nl = rpm_no_load(self.kv, voltage)
        rpm_ld = rpm_loaded(rpm_nl)

        base_5in_thrust = 1100.0  # realistic 5" freestyle baseline

        area_term = (area / area_ref) ** 1.15
        pitch_term = (prop.pitch / 4.5) ** 0.75
        rpm_term = (rpm_ld / 40000.0) ** 1.15
        motor_factor = ((self.stator_width * self.stator_height) / (23 * 6)) ** 1.05
        blade_factor = 1 + (prop.blades - 3) * 0.12

        thrust = base_5in_thrust * area_term * pitch_term * rpm_term * motor_factor * blade_factor
        return max(thrust, 5.0)

    # -----------------------------------------------------
    # Current model (calibrated)
    # -----------------------------------------------------
    def compute_current(self, thrust_g):
        prop = self.prop
        size_factor = 5.0 / max(prop.diameter, 1.5)
        return ((thrust_g / 120.0) ** 1.35) * size_factor / 0.8


class LiPo:
    def __init__(self, cells, capacity, c_rating, weight, hv=False, health=1.0):
        self.cells = cells
        self.capacity = capacity
        self.c_rating = c_rating
        self.weight = weight
        self.hv = hv
        self.health = clamp01(health)

    @property
    def nominal_voltage(self):
        return nominal_voltage(self.cells, self.hv)

    @property
    def safe_current(self):
        realistic_c = self.c_rating * 0.30   # 30% of printed C rating
        return (self.capacity / 1000.0) * realistic_c * self.health

    @property
    def internal_resistance(self):
        base = pack_internal_resistance_ohm(self.cells, self.capacity)
        ir_multiplier = 1.0 + (1.0 - self.health) * 1.5
        return base * ir_multiplier

    def usable_mah(self):
        return self.capacity * 0.8 * self.health


class Frame:
    def __init__(self, noise, wheelbase, prop_fit, weight):
        self.noise = noise
        self.wheelbase = wheelbase
        self.prop_fit = prop_fit
        self.weight = weight


class Flight_Controller:
    def __init__(self, pid_loop_freq, cpu_load, dshot, weight):
        self.pid_loop_freq = pid_loop_freq
        self.cpu_load = cpu_load
        self.dshot = dshot
        self.weight = weight


class Electronic_Speed_Controller:
    def __init__(self, motor_pwm, demag_comp, timing, weight, current_rating=45):
        self.motor_pwm = motor_pwm
        self.demag_comp = demag_comp
        self.timing = timing
        self.weight = weight
        self.current_rating = current_rating  # NEW


class All_In_One:
    def __init__(self, pid_loop_freq, cpu_load, dshot, motor_pwm, demag_comp, timing, weight, video=None, radio=None):
        self.pid_loop_freq = pid_loop_freq
        self.cpu_load = cpu_load
        self.dshot = dshot
        self.motor_pwm = motor_pwm
        self.demag_comp = demag_comp
        self.timing = timing
        self.weight = weight
        self.video = video
        self.radio = radio


class Video_System:
    def __init__(self, power, weight, digital=False):
        self.power = power
        self.weight = weight
        self.digital = digital


class Radio_Link:
    def __init__(self, weight, elrs=True):
        self.weight = weight
        self.elrs = elrs


class Action_Cam:
    def __init__(self, weight):
        self.weight = weight


# ---------------------------------------------------------
# Kwad Physics Engine
# ---------------------------------------------------------

class Kwad:
    def __init__(self):
        self.motors = []
        self.lipo = None
        self.frame = None
        self.fc = None
        self.esc = None
        self.aio = None
        self.video = None
        self.rx = None
        self.action_cam = None
        self.payload = 0

    # -----------------------------------------------------
    # Weight
    # -----------------------------------------------------
    def dry_weight(self):
        total = 0
        for m in self.motors:
            total += m.weight
        if self.lipo:
            total += self.lipo.weight
        if self.frame:
            total += self.frame.weight
        if self.fc:
            total += self.fc.weight
        if self.esc:
            total += self.esc.weight
        if self.aio:
            total += self.aio.weight
        if self.video:
            total += self.video.weight
        if self.rx:
            total += self.rx.weight
        if self.action_cam:
            total += self.action_cam.weight
        return total

    def auw(self):
        return self.dry_weight() + self.payload

    # -----------------------------------------------------
    # Thrust / Current
    # -----------------------------------------------------
    def max_thrust(self):
        if not self.motors or not self.lipo:
            return 0
        return sum(m.compute_thrust(self.lipo.nominal_voltage) for m in self.motors)

    def max_current(self):
        if not self.motors or not self.lipo:
            return 0
        return sum(m.compute_current(m.compute_thrust(self.lipo.nominal_voltage)) for m in self.motors)

    # -----------------------------------------------------
    # TWR
    # -----------------------------------------------------
    def max_twr(self):
        if self.auw() <= 0:
            return 0
        return self.max_thrust() / self.auw()

    # -----------------------------------------------------
    # Hover / Flight profiles
    # -----------------------------------------------------
    def hover_throttle(self):
        if self.max_thrust() <= 0:
            return 1.0
        return clamp01(self.auw() / self.max_thrust())

    def hover_current(self):
        return self.max_current() * self.hover_throttle()

    def flight_profile_currents(self):
        I_max = self.max_current()
        hover = self.hover_throttle()

        # If hover throttle is 1.0, quad is overloaded → all modes collapse
        loiter     = I_max * min(1.0, hover * 1.05)
        cruise     = I_max * min(1.0, hover * 1.6)
        freestyle  = I_max * min(1.0, hover * 2.2)
        racing     = I_max * min(1.0, hover * 3.0)
        full       = I_max

        return {
            "Loitering": loiter,
            "Cruise": cruise,
            "Freestyle": freestyle,
            "Racing": racing,
            "Full Throttle": full,
        }

    # -----------------------------------------------------
    # Flight time
    # -----------------------------------------------------
    def flight_time_profile(self, mode: str):
        if not self.lipo:
            return 0.0
        profiles = self.flight_profile_currents()
        amps = profiles.get(mode, 0.0)
        if amps <= 0:
            return 0.0
        usable_mah = self.lipo.usable_mah()
        # Slightly more optimistic than before (was 80.0)
        return (usable_mah / 1000.0) / amps * 90.0

    def flight_time(self):
        return self.flight_time_profile("Cruise")

    # -----------------------------------------------------
    # Voltage sag
    # -----------------------------------------------------
    def voltage_sag(self):
        if not self.lipo:
            return 0
        I = self.max_current()
        R = self.lipo.internal_resistance
        sag = I * R
        return sag / self.lipo.nominal_voltage

    # -----------------------------------------------------
    # Heat / Stress Models
    # -----------------------------------------------------
    def overstressed_fc(self):
        if not self.fc or not self.frame:
            return 0
        loop_norm = math.log10(self.fc.pid_loop_freq) / math.log10(8000)
        noise_norm = self.frame.noise / 100.0
        sag_norm = clamp01(self.voltage_sag() / 0.3)
        return clamp01(0.25 * loop_norm + 0.3 * noise_norm + 0.2 * sag_norm + 0.25)

    def overstressed_esc(self):
        if not self.esc or not self.lipo or not self.motors:
            return 0

        I_max = self.max_current()
        motors = len(self.motors)

        # PWM‑dependent heating factor
        pwm_heat = clamp01((48000 - self.esc.motor_pwm) / 48000)
        heat_factor = 1.0 + 0.25 * pwm_heat

        per_motor_current = (I_max / motors) * heat_factor
        esc_rating = self.esc.current_rating

        # ESC rating stress (primary, now harsh)
        ratio = per_motor_current / esc_rating
        esc_stress = clamp01(ratio ** 2)

        # Battery safe current stress (secondary)
        batt_safe = self.lipo.safe_current / motors if self.lipo.safe_current > 0 else 0
        if batt_safe > 0:
            batt_stress = clamp01(per_motor_current / batt_safe)
        else:
            batt_stress = 1.0

        # PWM / timing / demag influence (tertiary)
        pwm_norm = (self.esc.motor_pwm - 24000) / (192000 - 24000)
        timing_map = {"low": 0.2, "med-low": 0.35, "med": 0.5, "med-high": 0.7, "high": 1.0}
        timing_norm = timing_map.get(self.esc.timing, 0.5)
        demag_map = {"disabled": 1.0, "low": 0.7, "high": 0.3}
        demag_norm = demag_map.get(self.esc.demag_comp, 0.5)

        tuning_stress = clamp01(0.3 * pwm_norm + 0.4 * timing_norm + 0.3 * demag_norm)

        return clamp01(
            esc_stress * 1.0 +        # ESC rating dominates
            batt_stress * 0.3 +       # battery stress still matters
            tuning_stress * 0.2       # tuning still matters
        )

    def overstressed_motor(self):
        if not self.motors or not self.lipo or not self.esc:
            return 0

        m = self.motors[0]

        # Per‑motor thrust & current at full throttle
        thrust = m.compute_thrust(self.lipo.nominal_voltage)
        current = m.compute_current(thrust)

        # PWM‑dependent heating
        pwm_heat = clamp01((48000 - self.esc.motor_pwm) / 48000)
        heat_factor = 1.0 + 0.25 * pwm_heat
        heat_current = current * heat_factor

        # Hard over‑current: above rating → max stress
        if heat_current >= m.current_rating:
            return 1.0

        # Current‑based stress (dominant, harsh near high load)
        ratio = heat_current / m.current_rating

        if ratio >= 0.7:
            current_stress = 1.0
        elif ratio <= 0.5:
            current_stress = max(0.0, (ratio - 0.3) / 0.2) * 0.5  # up to 50% stress at 50% rating
        else:
            # 0.5–0.7 range ramps from 50% to 100% stress
            current_stress = 0.5 + (ratio - 0.5) / 0.2 * 0.5

        # RPM & cooling as secondary modifiers
        rpm = rpm_loaded(rpm_no_load(m.kv, self.lipo.nominal_voltage))
        rpm_norm = clamp01(rpm / 50000.0)
        cooling = clamp01(m.prop.diameter / 7.0)

        return clamp01(
            0.75 * current_stress +
            0.20 * rpm_norm -
            0.15 * cooling
        )

    def overstressed_desync(self):
        if not self.motors or not self.esc or not self.lipo:
            return 0

        m = self.motors[0]

        # Compute thrust & current
        thrust = m.compute_thrust(self.lipo.nominal_voltage)
        current = m.compute_current(thrust)

        # PWM‑dependent heating for desync risk
        pwm_heat = clamp01((48000 - self.esc.motor_pwm) / 48000)
        heat_factor = 1.0 + 0.25 * pwm_heat
        heat_current = current * heat_factor

        # RPM
        rpm = rpm_loaded(rpm_no_load(m.kv, self.lipo.nominal_voltage))

        # --- 1. Torque load factor (heavy props, many blades, high pitch) ---
        # Use thrust per RPM as a proxy for torque load
        torque_load = thrust / max(rpm, 1)
        torque_norm = clamp01(torque_load / 0.06)  # tuned for 5" props

        # --- 2. Low RPM + high load = desync danger ---
        low_rpm_factor = clamp01((20000 - rpm) / 20000)  # 20k RPM threshold
        low_rpm_load = clamp01(low_rpm_factor * torque_norm)

        # --- 3. ESC timing & demag ---
        timing_map = {"low": 0.1, "med-low": 0.3, "med": 0.5, "med-high": 0.7, "high": 1.0}
        timing_risk = timing_map.get(self.esc.timing, 0.5)

        demag_map = {"high": 0.1, "low": 0.7, "disabled": 1.0}
        demag_risk = demag_map.get(self.esc.demag_comp, 0.5)

        # --- 4. PWM frequency ---
        pwm_norm = clamp01((48000 - self.esc.motor_pwm) / 48000)  # lower PWM = more risk

        # --- 5. Current spikes (use heated current) ---
        current_norm = clamp01(heat_current / (m.current_rating * 1.5))

        # Final weighted risk
        return clamp01(
            0.35 * torque_norm +
            0.25 * low_rpm_load +
            0.15 * timing_risk +
            0.15 * demag_risk +
            0.10 * pwm_norm +
            0.20 * current_norm
        )

    def overstressed_battery(self):
        if not self.lipo:
            return 0

        I_max = self.max_current()
        safe = self.lipo.safe_current

        # Hard overload: battery cannot supply demanded current
        if I_max >= safe:
            return 1.0

        # Stress curve:
        # 0–60% of safe → low stress
        # 60–100% → ramps sharply
        ratio = I_max / safe

        if ratio <= 0.6:
            batt_stress = ratio / 0.6 * 0.4
        else:
            batt_stress = 0.4 + (ratio - 0.6) / 0.4 * 0.6

        return clamp01(batt_stress)


    def overstressed_overall(self):
        return clamp01((
            self.overstressed_fc() +
            self.overstressed_esc() +
            self.overstressed_motor() +
            self.overstressed_desync() +
            self.overstressed_battery()
        ) / 5.0)


    # -----------------------------------------------------
    # Build Style Classification
    # -----------------------------------------------------
    def build_style(self):
        twr = self.max_twr()
        auw = self.auw()
        prop = self.motors[0].prop.diameter if self.motors else 0
        ft = self.flight_time()

        if twr < 2:
            adjective = "Mild"
        elif twr < 4:
            adjective = "Average"
        elif twr < 7:
            adjective = "Aggressive"
        else:
            adjective = "Extreme"

        if prop <= 3.0 and auw < 120 and twr > 4:
            style = "Toothpick"
        elif prop <= 2.5 and auw < 80:
            style = "Whoop"
        elif 3.0 <= prop <= 5.1 and 200 <= auw <= 800 and 4 <= twr <= 8:
            style = "Freestyle"
        elif abs(prop - 5.0) < 0.2 and 400 <= auw <= 600 and twr >= 8:
            style = "Racing"
        elif prop >= 6.0 and 2 <= twr <= 4 and ft > 10:
            style = "Long Range"
        elif 7.0 <= prop <= 10.0 and 1000 <= auw <= 2000 and 6 <= ft <= 10:
            style = "Kamikaze"
        elif 7.0 <= prop <= 17.0 and auw >= 1200 and ft >= 12:
            style = "Utility"
        else:
            style = "General Purpose"

        return f"{adjective} {style}"
