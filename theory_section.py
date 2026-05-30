import streamlit as st

def render_theory_section():

    with st.expander("Motor Physics", expanded=False):
        st.latex(r"RPM_{no\_load} = KV \cdot V")
        st.latex(r"RPM_{loaded} \approx 0.78 \cdot KV \cdot V")
        st.latex(r"K_t = \frac{60}{2\pi \cdot KV}")
        st.latex(r"\tau = K_t \cdot (I - I_0)")
        st.latex(r"P_{out} = \tau \cdot \omega")

        st.write("""
        - KV determines RPM per volt.
        - Loaded RPM is typically ~78% of no‑load RPM.
        - Torque constant (Kt) converts current into torque.
        - Torque increases linearly with current above no‑load current.
        - Output power is torque × angular velocity.
        """)

    with st.expander("Propeller Physics", expanded=False):
        st.latex(r"A_{disk} = \pi \left(\frac{D}{2}\right)^2")
        st.latex(r"CT = f(D, Pitch, Blades, Mach)")
        st.latex(r"Thrust = CT \cdot \rho \cdot n^2 \cdot D^4")
        st.latex(r"P_{induced} = \frac{T^{3/2}}{\sqrt{2 \rho A}}")
        st.latex(r"P_{profile} \propto T^{4/3} \cdot D")

        st.write("""
        - Disk area determines thrust potential.
        - Thrust coefficient (CT) depends on diameter, pitch, blade count, and tip Mach.
        - Induced power is the ideal power needed to generate thrust.
        - Profile drag increases rapidly at high thrust.
        - Larger props are more efficient at low RPM; small props lose efficiency at high thrust.
        """)

    with st.expander("Battery Physics", expanded=False):
        st.latex(r"V_{nominal} = 3.7 \cdot S")
        st.latex(r"I_{safe} = C \cdot Capacity_{Ah}")
        st.latex(r"V_{sag} = V_{open} - I \cdot R_{internal}")
        st.latex(r"E_{Wh} = Capacity_{Ah} \cdot V_{nominal}")

        st.write("""
        - Voltage sag reduces RPM and thrust.
        - Higher C rating reduces sag.
        - Larger packs sag less but weigh more.
        - Internal resistance increases with age and damage.
        """)

    with st.expander("ESC Physics", expanded=False):
        st.latex(r"P_{esc} = I^2 R_{mosfet} + P_{switching}")

        st.write("""
        - Higher PWM frequency increases smoothness but increases switching losses.
        - Demag compensation prevents desync under high load.
        - Timing affects torque and efficiency:
            - Low timing = efficient, cooler
            - High timing = more torque, more heat
        """)

    with st.expander("Flight Controller Physics", expanded=False):
        st.latex(r"Loop\ Frequency = \frac{1}{Loop\ Time}")
        st.latex(r"CPU\ Load \propto Loop\ Rate \cdot Filter\ Load \cdot Motor\ Count")

        st.write("""
        - Higher loop frequency improves responsiveness.
        - Higher CPU load increases FC heat.
        - Frame noise increases filtering load.
        - DShot rate affects motor update speed.
        """)

    with st.expander("Aerodynamics & Drag", expanded=False):
        st.latex(r"D = \tfrac{1}{2} \rho C_d A v^2")
        st.latex(r"T_{forward} = \sqrt{T_{total}^2 - W^2}")
        st.latex(r"v_{max} = \sqrt{\frac{2 T_{forward}}{\rho C_d A}}")

        st.write("""
        - Drag increases with the square of velocity.
        - Forward thrust is limited by the need to hold the quad up.
        - Max speed occurs when forward thrust equals drag.
        """)

    with st.expander("Thrust‑to‑Weight Ratio (TWR)", expanded=False):
        st.latex(r"TWR = \frac{T_{max}}{W}")
        st.write("""
        - TWR > 1 means the quad can hover.
        - TWR > 4 is typical for freestyle.
        - TWR > 8 is typical for racing.
        """)

    with st.expander("Disk Loading", expanded=False):
        st.latex(r"DL = \frac{W}{A_{total}}")
        st.write("""
        - Lower disk loading improves efficiency and stability.
        - Higher disk loading increases responsiveness but reduces flight time.
        """)

    with st.expander("Hover Power", expanded=False):
        st.latex(r"P_{hover} \approx \frac{T^{3/2}}{\sqrt{2 \rho A}}")
        st.write("""
        - Hover power increases with weight.
        - Larger props reduce hover power.
        """)

    with st.expander("Flight Time", expanded=False):
        st.latex(r"t_{min} = \frac{E_{Wh}}{P_{avg}} \cdot 60")
        st.write("""
        - Flight time is battery energy divided by average power draw.
        - Aggressive flying increases power draw dramatically.
        """)

    with st.expander("Radio & RF Physics", expanded=False):
        st.latex(r"FSPL(dB) = 20 \log_{10}(d) + 20 \log_{10}(f) + 32.44")
        st.latex(r"LinkBudget = P_{tx} + G_{tx} + G_{rx} - FSPL - L_{misc}")
        st.latex(r"Range \propto 10^{\frac{(LinkBudget)}{20}}")
        st.latex(r"Loss_{pol} = 20 \log_{10}(\cos(\theta))")
        st.latex(r"Loss_{CP/LP} \approx 3 \text{ dB}")
        st.latex(r"FresnelRadius = \sqrt{\frac{\lambda d_1 d_2}{d_1 + d_2}}")

        st.write("""
        ### Free‑Space Path Loss (FSPL)
        - FSPL increases with both distance and frequency.
        - Higher frequency loses range faster.
        - Every 6 dB of loss halves your range.

        ### Link Budget
        - Determines maximum usable range.
        - Includes Tx power, antenna gains, FSPL, and losses.

        ### Decibels
        - +3 dB = 2× power
        - +6 dB = 4× power
        - +10 dB = 10× power

        ### Polarization Loss
        - Linear ↔ Linear misalignment = up to −∞ dB
        - Circular ↔ Linear = −3 dB
        - LHCP ↔ RHCP = −30 dB

        ### Fresnel Zone
        - RF energy occupies a 3D volume, not a line.
        - Obstructions cause fading and multipath.

        ### Multipath
        - Indoors or near metal → reflections cause RSSI swings.
        """)

    with st.expander("Frequency Comparison (Civilian & Military UAS Bands)", expanded=False):
        st.write("""
        ### 5.8 GHz
        - Short range, weak penetration, small antennas.

        ### 2.4 GHz
        - Good range, good penetration, medium antennas.

        ### 900 MHz
        - Excellent penetration, long range, large antennas.

        ### L‑Band (1–2 GHz)
        - Long range, excellent penetration.

        ### S‑Band (2–4 GHz)
        - Good compromise of range and bandwidth.

        ### C‑Band (4–8 GHz)
        - High bandwidth, moderate range.

        ### Ku‑Band (12–18 GHz)
        - Very high bandwidth, short range unless directional.
        """)

    with st.expander("Build Style Definitions", expanded=False):
        st.write("""
        - **Whoop:** 1.6–2.0" props, <80g AUW  
        - **Toothpick:** 2.5–3" props, <120g AUW  
        - **Freestyle:** 3–5" props, 200–800g AUW  
        - **Racing:** 5" props, 400–600g AUW  
        - **Long Range:** 6–7" props, TWR 2–4  
        - **Cinewhoop:** 3–3.5" props, ducts  
        - **Utility:** 7–17" props, payload‑focused  
        """)

    with st.expander("Community Reference Tables", expanded=False):
        st.write("### Typical AUW Ranges")
        st.table({
            "Build": ["Whoop", "Toothpick", "3\"", "5\" Freestyle", "5\" Racing", "7\" LR", "Utility"],
            "AUW (g)": ["20–45", "55–120", "120–200", "650–800", "430–550", "650–1100", "1500–4000+"]
        })

        st.write("### Typical TWR Ranges")
        st.table({
            "Build": ["Whoop", "Toothpick", "Freestyle", "Racing", "Long Range", "Utility"],
            "TWR": ["2–3", "4–7", "5–8", "8–12", "2–3", "1.5–3"]
        })

        st.write("### Typical RPM Ranges")
        st.table({
            "Build": ["Whoop", "Toothpick", "3\"", "5\"", "7\""],
            "Loaded RPM": ["28–45k", "32–48k", "38–48k", "28–36k", "18–26k"]
        })

        st.write("### Typical Flight Times")
        st.table({
            "Build": ["Whoop", "Toothpick", "Freestyle", "Racing", "Long Range"],
            "Flight Time": ["3–5 min", "3–6 min", "4–7 min", "1.5–3 min", "12–25 min"]
        })
