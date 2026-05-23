class Component:
    def __init__(self, manufacturer, model, partNumber, weight, cost):
        self.manufacturer = manufacturer # string
        self.model = model # string
        self.partNumber = partNumber # string 
        self.weight = weight # grams
        self.cost = cost # USD

class Motor(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost, kv, statorDiameter, statorHeight, mountingPattern, maxCurrent, propMountType = "5mm"):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.kv = kv
        self.statorDiameter = statorDiameter 
        self.statorHeight = statorHeight
        self.mountingPattern = mountingPattern
        self.maxCurrent = maxCurrent
        self.propMountType = propMountType
        self.statorVolume = self.statorDiameter * self.statorHeight

class Propeller(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost, bladeCount, diameter, pitch, propMountType = "5mm"):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.bladeCount = bladeCount
        self.diameter = diameter
        self.pitch = pitch 
        self.propMountType = propMountType

class Frame(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost, fc_mountingPattern, esc_mountingPattern, aio_mountingPattern, motor_mountingPattern, vtx_mountingPattern, cam_mountingPattern, propDiameterClearance, armThickness, frameThickness, style = "True X"):
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
    def __init__(self, manufacturer, model, partNumber, weight, cost, mountingPattern, currentPull, vin):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.mountingPattern = mountingPattern
        self.currentPull = currentPull
        self.vin = vin

class FC(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost):
        super().__init__(manufacturer, model, partNumber, weight, cost)


class ESC(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost, maxCurrent, vin, mountingPattern):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.maxCurrent = maxCurrent 
        self.vin = vin 
        self.mountingPattern = mountingPattern

class AIO(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost, maxCurrent, vin, mountingPattern):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.fc = FC(manufacturer, model, partNumber, weight, cost)
        self.esc = ESC(manufacturer, model, partNumber, weight, cost, maxCurrent, vin, mountingPattern)

class RX(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost):
        super().__init__(manufacturer, model, partNumber, weight, cost)

class GPS(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost):
        super().__init__(manufacturer, model, partNumber, weight, cost)

class CAM(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost, mountingPattern):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.mountingPattern = mountingPattern

class ANT(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost):
        super().__init__(manufacturer, model, partNumber, weight, cost)

class LIPO(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost, cells, capacity, cRating, conType = "XT60", hv = False):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.cells = cells
        self.capacity = capacity
        self.cRating = cRating 
        self.contype = conType
        if self.hv == True:
            self.s1 = 4.35
        else:
            self.s1 = 4.20
        self.voltage = self.s1 * self.cells

class CAP(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost, maxVoltage, microFarad):
        super().__init__(manufacturer, model, partNumber, weight, cost)
        self.maxVoltage = maxVoltage
        self.microFarad = microFarad

class ActionCAM(Component):
    def __init__(self, manufacturer, model, partNumber, weight, cost):
        super().__init__(manufacturer, model, partNumber, weight, cost)

class Kwad:
    def __init__(self, model, nickname, buildType, frame, motors, props, esc, cap, fc, aio, gps, rx, rx_ant, vtx, vtx_ant, cam, actionCam, lipo):
        self.model = model
        self.nickname = nickname 
        self.buildType = buildType # LR Recon, Bando Basher, Racing, Tiny Whoop, CineWhoop, Toothpick, etc.
        self.frame = frame 
        self.motors = motors # array of 4
        self.prop = props # array of 4
        self.esc = esc #esc = None if AIO
        self.cap = cap # Optional, although hopefully not None
        self.fc = fc #fc = None if AIO
        self.aio = aio 
        self.gps = gps # Optional
        self.rx = rx # None if built in FC or AIO
        self.rxAnt = rx_ant # None if ceramic chip or other built-in
        self.vtx = vtx # None if AIO has built-in
        self.vtxAnt = vtx_ant # None if AIO has built-in
        self.cam = cam 
        self.actionCam = actionCam # Optional
        self.lipo = lipo
        self.dryWeight = self.get_weight("dry")
        self.allUpWeight = self.get_weight("auw")
        self.gradeRating = self.get_grade_rating()
        self.compatibility = self.get_component_compatibility()
        self.totalCost = self.get_total_cost()
        self.twr = self.get_twr() # thrust to weight ratio
        self.thrust = self.get_thrust() # in grams
        self.maxPayloadWeight = self.get_max_payload_weight() # the amount of weight left that can be used to carry things before the drone is unflyable
        self.maxRPM = self.get_max_rpm() # if 100% throttle with no atmostpheric drag
        self.maxCurrent = self.get_max_current() # if 100% throttle
        self.expectedFlightTime = self.get_expected_flight_time() # in seconds, theorhetical average
        self.maxSpeed = self.get_max_speed() # theorhetical 
        self.expectedCooldownTime = self.get_expected_Cooldown_time() # to prevent overheating if applicable

    # returns the sum of each component's weight. "dry" will be without LIPO
    def get_weight(self, type):
        total = 0

        components = [
            self.frame,
            *self.motors,
            *self.prop,
            self.esc if self.esc else None,
            self.cap if self.cap else None,
            self.fc if self.fc else None,
            self.aio if self.aio else None,
            self.gps if self.gps else None,
            self.rx if self.rx else None,
            self.rxAnt if self.rxAnt else None,
            self.vtx if self.vtx else None,
            self.vtxAnt if self.vtxAnt else None,
            self.cam if self.cam else None,
            self.actionCam if self.actionCam else None,
        ]

        for c in components:
            if c is not None:
                total += c.weight

        if type == "auw" and self.lipo is not None:
            total += self.lipo.weight

        return total


    # returns a grade rating: A - F based on how good it is likely to perform compared to the drone's "build type"; S = Super.
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


    # returns a compatibility mismatch warning if it detects any issues across components.
    def get_component_compatibility(self):
        issues = []

        # motor mounting pattern vs frame motor pattern
        for m in self.motors:
            if m.mountingPattern != self.frame.motor_mountingPattern:
                issues.append(f"Motor {m.model} mounting pattern mismatch with frame.")

        # prop mount type vs motor prop mount type
        for p, m in zip(self.prop, self.motors):
            if p.propMountType != m.propMountType:
                issues.append(f"Prop {p.model} mount type mismatch with motor {m.model}.")

        # FC / ESC / AIO mounting patterns vs frame
        if self.fc and self.fc.mountingPattern != self.frame.fc_mountingPattern:
            issues.append("FC mounting pattern mismatch with frame.")

        if self.esc and self.esc.mountingPattern != self.frame.esc_mountingPattern:
            issues.append("ESC mounting pattern mismatch with frame.")

        if self.aio and self.aio.esc.mountingPattern != self.frame.aio_mountingPattern:
            issues.append("AIO mounting pattern mismatch with frame.")

        return issues if issues else ["OK"]


    # returns the sum of each component's cost.
    def get_total_cost(self):
        total = 0

        components = [
            self.frame,
            *self.motors,
            *self.prop,
            self.esc if self.esc else None,
            self.cap if self.cap else None,
            self.fc if self.fc else None,
            self.aio if self.aio else None,
            self.gps if self.gps else None,
            self.rx if self.rx else None,
            self.rxAnt if self.rxAnt else None,
            self.vtx if self.vtx else None,
            self.vtxAnt if self.vtxAnt else None,
            self.cam if self.cam else None,
            self.actionCam if self.actionCam else None,
            self.lipo if self.lipo else None
        ]

        for c in components:
            if c is not None:
                total += c.cost

        return total


    # returns the thrust to weight ratio of this build
    def get_twr(self):
        thrust = self.get_thrust()
        auw = self.allUpWeight if self.allUpWeight > 0 else 1
        return thrust / auw


    # simple thrust model based on KV, voltage, and prop size
    def get_thrust(self):
        if not self.motors or not self.prop:
            return 0

        motor = self.motors[0]
        prop = self.prop[0]

        voltage = self.lipo.voltage if self.lipo else 14.8

        # approximate thrust model:
        # thrust_per_motor ≈ k * KV * voltage * (diameter^2 * pitch) / 1e6
        k = 0.95
        thrust_per_motor = k * motor.kv * voltage * (prop.diameter ** 2 * prop.pitch) / 1_000_000

        return thrust_per_motor * 4


    # max payload weight = thrust - AUW
    def get_max_payload_weight(self):
        return max(0, self.get_thrust() - self.allUpWeight)


    # max RPM = KV * voltage
    def get_max_rpm(self):
        if not self.motors:
            return 0
        voltage = self.lipo.voltage if self.lipo else 14.8
        return self.motors[0].kv * voltage


    # max current = motor max current * 4
    def get_max_current(self):
        if not self.motors:
            return 0
        return self.motors[0].maxCurrent * 4


    # expected flight time (seconds)
    def get_expected_flight_time(self):
        if not self.lipo:
            return 0

        capacity_ah = self.lipo.capacity / 1000
        usable_capacity = capacity_ah * 0.8

        avg_current = self.get_max_current() * 0.35

        if avg_current <= 0:
            return 0

        return (usable_capacity / avg_current) * 3600


    # max speed (very rough)
    def get_max_speed(self):
        if not self.prop:
            return 0

        rpm = self.get_max_rpm()
        pitch_in_inches = self.prop[0].pitch
        pitch_in_meters = pitch_in_inches * 0.0254

        return (rpm * pitch_in_meters) / 60


    # cooldown time (placeholder)
    def get_expected_Cooldown_time(self):
        max_current = self.get_max_current()
        if max_current < 60:
            return 10
        elif max_current < 120:
            return 20
        else:
            return 30
