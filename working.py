def evaluate_kwad(kwad: Kwad, fuzz: phys.Fuzz) -> KwadPerformance:

    v_full = phys.pack_voltage_full(kwad.battery.cells_series, kwad.battery.chemistry)
    thrust_needed = phys.weight_from_mass(auw_kg(kwad))
    motor_count = len(kwad.motors)
    thrust_per_motor = thrust_needed / motor_count

    motor = kwad.motors[0]
    prop = kwad.props[0]

    r_internal = phys.pack_internal_resistance(
        kwad.battery.cells_series, kwad.battery.chemistry, fuzz
    )

    # -------------------------------
    # SAG-AWARE THROTTLE SOLVER LOOP
    # -------------------------------
    v_loaded = v_full
    h_throttle = 0.5
    current_per_motor = 0.0

    for _ in range(10):

        # 1. Solve throttle at current sagged voltage
        h_throttle = hover_throttle(kwad, v_loaded, fuzz)

        # 2. Compute current at this throttle + voltage
        current_per_motor = motor_current_from_thrust(
            motor, prop, thrust_per_motor, v_loaded, fuzz
        )
        total_current = current_per_motor * motor_count

        # 3. Compute new sagged voltage
        new_v_loaded = phys.voltage_sag_under_load(v_full, total_current, r_internal)

        # 4. Convergence check
        if abs(new_v_loaded - v_loaded) < 0.01:
            v_loaded = new_v_loaded
            break

        v_loaded = new_v_loaded

    # Final electrical hover power
    total_power = v_loaded * total_current * fuzz.hover_power_multiplier

    # Flight time
    ft = flight_time_minutes(kwad, total_power)

    # Thermal
    motor_temp = motor_temperature_rise(motor, current_per_motor, 60, fuzz)
    esc_temp = esc_temperature_rise(kwad.esc, current_per_motor, 60, fuzz)

    # Max thrust
    max_total = static_thrust(motor, prop, v_full, fuzz) * motor_count

    return KwadPerformance(
        hover_throttle=h_throttle,
        max_thrust_total_n=max_total,
        total_power_hover_w=total_power,
        flight_time_min=ft,
        motor_temp_rise_c=motor_temp,
        esc_temp_rise_c=esc_temp,
    )
