class Component:
    def __init__(self, manufacturer, model, partNumber, weight, cost):
        self.manufacturer = manufacturer
        self.model = model
        self.partNumber = partNumber
        self.weight = weight
        self.cost = cost


class Motor(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost,
                 kv, statorDiameter, statorHeight, mountingPattern,
                 maxCurrent, propMountType="5mm"):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.kv = kv
        self.statorDiameter = statorDiameter
        self.statorHeight = statorHeight
        self.mountingPattern = mountingPattern
        self.maxCurrent = maxCurrent
        self.propMountType = propMountType
        self.statorVolume = self.statorDiameter * self.statorHeight


class Propeller(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost,
                 bladeCount, diameter, pitch, propMountType="5mm"):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.bladeCount = bladeCount
        self.diameter = diameter
        self.pitch = pitch
        self.propMountType = propMountType


class Frame(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost,
                 fc_mountingPattern, esc_mountingPattern, aio_mountingPattern,
                 motor_mountingPattern, vtx_mountingPattern, cam_mountingPattern,
                 propDiameterClearance, armThickness, frameThickness,
                 style="True X"):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.fc_mountingPattern = fc_mountingPattern
        self.esc_mountingPattern = esc_mountingPattern
        self.aio_mountingPattern = aio_mountingPattern
        self.motor_mountingPattern = motor_mountingPattern
        self.vtx_mountingPattern = vtx_mountingPattern
        self.cam_mountingPattern = cam_mountingPattern
        self.propDiameterClearance = propDiameterClearance
        self.armThickness = armThickness
        self.frameThickness = frameThickness
        self.style = style


class VTX(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost,
                 mountingPattern, currentPull, vin):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.mountingPattern = mountingPattern
        self.currentPull = currentPull
        self.vin = vin


class FC(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost):
        super().__init__(manufacturer, model, partNumber, weight, cost)


class ESC(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost,
                 maxCurrent, vin, mountingPattern):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.maxCurrent = maxCurrent
        self.vin = vin
        self.mountingPattern = mountingPattern


class AIO(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost,
                 maxCurrent, vin, mountingPattern):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.fc = FC(manufacturer, model, partNumber, weight, cost)
        self.esc = ESC(manufacturer, model, partNumber, weight, cost,
                       maxCurrent, vin, mountingPattern)


class RX(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost):
        super().__init__(manufacturer, model, partNumber, weight, cost)


class GPS(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost):
        super().__init__(manufacturer, model, partNumber, weight, cost)


class CAM(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost,
                 mountingPattern):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.mountingPattern = mountingPattern


class ANT(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost):
        super().__init__(manufacturer, model, partNumber, weight, cost)


class LIPO(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost,
                 cells, capacity, cRating, conType="XT60", hv=False):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.cells = cells
        self.capacity = capacity
        self.cRating = cRating
        self.contype = conType
        self.hv = hv
        self.s1 = 4.35 if hv else 4.20
        self.voltage = self.s1 * self.cells


class CAP(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost,
                 maxVoltage, microFarad):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.maxVoltage = maxVoltage
        self.microFarad = microFarad


class ActionCAM(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost):
        super().__init__(manufacturer, model, partNumber, weight, cost)


class Kwad:
    def __init__(self, model, nickname, buildType, frame, motors, props,
                 esc, cap, fc, aio, gps, rx, rx_ant, vtx, vtx_ant,
                 cam, actionCam, lipo):

        self.model = model
        self.nickname = nickname
        self.buildType = buildType

        self.frame = frame
        self.motors = motors
        self.prop = props
        self.esc = esc
        self.cap = cap
        self.fc = fc
        self.aio = aio
        self.gps = gps
        self.rx = rx
        self.rxAnt = rx_ant
        self.vtx = vtx
        self.vtxAnt = vtx_ant
        self.cam = cam
        self.actionCam = actionCam
        self.lipo = lipo

        self.dryWeight = self.get_weight("dry")
        self.allUpWeight = self.get_weight("auw")
        self.gradeRating = self.get_grade_rating()
        self.compatibility = self.get_component_compatibility()
        self.totalCost = self.get_total_cost()
        self.thrust = self.get_thrust()
        self.twr = self.get_twr()
        self.maxPayloadWeight = self.get_max_payload_weight()
        self.maxRPM = self.get_max_rpm()
        self.maxCurrent = self.get_max_current()
        self.expectedFlightTime = self.get_expected_flight_time()
        self.maxSpeed = self.get_max_speed()
        self.expectedCooldownTime = self.get_expected_Cooldown_time()

    # -------------------------
    # WEIGHT
    # -------------------------
    def get_weight(self, type):
        total = 0

        components = [
            self.frame,
            *self.motors,
            *self.prop,
            self.esc,
            self.cap,
            self.fc,
            self.aio,
            self.gps,
            self.rx,
            self.rxAnt,
            self.vtx,
            self.vtxAnt,
            self.cam,
            self.actionCam,
        ]

        for c in components:
            if c is not None:
                total += c.weight

        if type == "auw" and self.lipo:
            total += self.lipo.weight

        return total

    # -------------------------
    # GRADE
    # -------------------------
    def get_grade_rating(self):
        twr = self.get_twr()

        if twr >= 12:
            return "S"
        elif twr >= 10:
            return "A"
        elif twr >= 8:
            return "B"
        elif twr >= 6:
            return "C"
        elif twr >= 4:
            return "D"
        else:
            return "F"

    # -------------------------
    # COMPATIBILITY
    # -------------------------
    def get_component_compatibility(self):
        issues = []

        if not self.frame:
            return ["No frame selected"]

        # Motor mounting
        for m in self.motors:
            if m and m.mountingPattern != self.frame.motor_mountingPattern:
                issues.append(f"Motor {m.model} mounting pattern mismatch with frame.")

        # Prop mount
        for p, m in zip(self.prop, self.motors):
            if p and m and p.propMountType != m.propMountType:
                issues.append(f"Prop {p.model} mount type mismatch with motor {m.model}.")

        # FC
        if self.fc and hasattr(self.fc, "mountingPattern"):
            if self.fc.mountingPattern != self.frame.fc_mountingPattern:
                issues.append("FC mounting pattern mismatch with frame.")

        # ESC
        if self.esc and hasattr(self.esc, "mountingPattern"):
            if self.esc.mountingPattern != self.frame.esc_mountingPattern:
                issues.append("ESC mounting pattern mismatch with frame.")

        # AIO
        if self.aio and hasattr(self.aio.esc, "mountingPattern"):
            if self.aio.esc.mountingPattern != self.frame.aio_mountingPattern:
                issues.append("AIO mounting pattern mismatch with frame.")

        return issues if issues else ["OK"]

    # -------------------------
    # COST
    # -------------------------
    def get_total_cost(self):
        total = 0

        components = [
            self.frame,
            *self.motors,
            *self.prop,
            self.esc,
            self.cap,
            self.fc,
            self.aio,
            self.gps,
            self.rx,
            self.rxAnt,
            self.vtx,
            self.vtxAnt,
            self.cam,
            self.actionCam,
            self.lipo,
        ]

        for c in components:
            if c:
                total += c.cost

        return total

    # -------------------------
    # THRUST MODEL (REALISTIC)
    # -------------------------
    def get_thrust(self):
        motors = [m for m in self.motors if m]
        props = [p for p in self.prop if p]

        if not motors or not props:
            return 0

        motor = motors[0]
        prop = props[0]

        voltage = self.lipo.voltage if self.lipo else 14.8

        # Empirically tuned constant:
        # 2305 1950KV + 5048 + 4S ≈ ~900g per motor
        k = 2.3e-4

        thrust_per_motor = (
            k * motor.kv * voltage * (prop.diameter ** 2 * prop.pitch)
        )

        return thrust_per_motor * 4

    def get_twr(self):
        thrust = self.get_thrust()
        auw = self.allUpWeight if self.allUpWeight > 0 else 1
        return thrust / auw

    # -------------------------
    # OTHER METRICS
    # -------------------------
    def get_max_payload_weight(self):
        return max(0, self.get_thrust() - self.allUpWeight)

    def get_max_rpm(self):
        if not self.motors:
            return 0
        voltage = self.lipo.voltage if self.lipo else 14.8
        return self.motors[0].kv * voltage

    def get_max_current(self):
        if not self.motors:
            return 0
        return self.motors[0].maxCurrent * 4

    def get_expected_flight_time(self):
        if not self.lipo:
            return 0

        capacity_ah = self.lipo.capacity / 1000
        usable_capacity = capacity_ah * 0.8
        avg_current = self.get_max_current() * 0.35

        if avg_current <= 0:
            return 0

        return (usable_capacity / avg_current) * 3600

    def get_max_speed(self):
        if not self.prop:
            return 0

        rpm = self.get_max_rpm()
        pitch_m = self.prop[0].pitch * 0.0254
        return (rpm * pitch_m) / 60

    def get_expected_Cooldown_time(self):
        max_current = self.get_max_current()
        if max_current < 60:
            return 10
        elif max_current < 120:
            return 20
        else:
            return 30
