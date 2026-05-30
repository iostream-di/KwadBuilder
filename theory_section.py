import streamlit as st

def render_theory_section():

    with st.expander("Marty Mayhem's Build Logic", expanded=False):
        st.markdown("## Marty's Motor KV Formula")

        st.write("""
        This formula gives you the correct motor KV for **any prop size** and **any cell count**. 
        It is based on the observation that FPV quads across all sizes tend to run their propeller
        tips at about **70% of the speed of sound**.
        """)

        st.markdown("### Step 1 — Convert prop diameter to meters")
        st.latex(r"D_m = D_{in} \cdot 0.0254")

        st.markdown("### Step 2 — Use the universal FPV tip‑speed constant")
        st.latex(r"k_{tip} = 0.70")
        st.latex(r"a = 343\ \text{m/s}")

        st.write("This represents the typical unloaded tip‑speed FPV quads operate at.")

        st.markdown("### Step 3 — Compute target unloaded RPM for that prop size")
        st.latex(r"RPM_{target} = \frac{k_{tip} \cdot a \cdot 60}{\pi \cdot D_m}")

        st.write("""
        This gives the ideal unloaded RPM for the prop size, matching real FPV builds across
        2\", 3\", 5\", 7\", and larger platforms.
        """)

        st.markdown("### Step 4 — Compute pack voltage")
        st.latex(r"V_{pack} = S \cdot V_{cell}")

        st.write("""
        Use:
        - 3.8 V per cell for nominal
        - 4.0 V per cell for design
        - 4.2 V per cell for full‑charge KV
        - 4.35 V per cell for High-Voltage full-charge KV
        """)

        st.markdown("### Step 5 — Final KV Formula")
        st.latex(r"KV_{target} = \frac{RPM_{target}}{V_{pack}}")

        st.write("""
        This produces KV values that match real‑world FPV builds. You can go higer or 
        lower than this by 10% to give you a decent change in your build character. 15% 
        deviation is my max. Normally I have seen that -15% makes it too gentile, and 
        +15% makes for one-time rockets.
        """)

        st.markdown("## Stator Diameter & Height Formula")

        st.write("""
        Once KV is known, the next step is choosing a motor size that can supply the 
        torque required for your target AUW and prop size. This formula gives a 
        recommended stator diameter and height using a simple torque-scaling model.
        I personally just buy they widest motor out there with my target KV, unless I 
        am building as light weight as possible, like a racer or toothpick. 
        """)

        st.markdown("### Step 1 — Inputs")
        st.write("""
        - **mₖg** = target AUW in kilograms  
        - **Dᵢₙ** = prop diameter in inches  
        """)

        st.markdown("### Step 2 — Stator Diameter Formula")
        st.latex(r"d_{mm} \approx 16 \cdot (m_{kg} \cdot D_{in})^{1/3}")

        st.write("""
        This formula is tuned so that typical FPV builds land in the correct stator 
        diameter ranges:
        - 5\" freestyle → ~23–25 mm  
        - 3\" toothpick → ~11–12 mm  
        - 7\" long‑range → ~28–30 mm  
        """)

        st.markdown("### Step 3 — Stator Height (Width‑Biased)")
        st.latex(r"h_{mm} \approx 0.35 \cdot d_{mm}")

        st.write("""
        This biases toward wider stators, which provide better torque response and 
        thermal handling for FPV flying styles.
        """)

        st.markdown("### Example Outputs")
        st.write("""
        - **5\" @ 750 g** → d ≈ 25 mm → h ≈ 8.7 mm → *2508 class*  
        - **3\" @ 120 g** → d ≈ 11.4 mm → h ≈ 4.0 mm → *1104/1204 class*  
        - **7\" @ 900 g** → d ≈ 29.6 mm → h ≈ 10.4 mm → *2806/3007 class*  
        """)

        st.write("""
        This gives me a clean, physics‑inspired baseline motor size that you can 
        adjust later based on flight style, efficiency goals, or weight constraints.
        """)

        st.markdown("## Marty's Prop Load Index — Pitch, KV, Cells, Blades")

        st.write("""
        This formula estimates how 'heavy' a prop feels electrically, combining:
        - prop diameter
        - prop pitch
        - motor KV
        - cell count
        - blade count

        The goal is to help choose a prop pitch that matches their intent
        (gentle vs hot) without accidentally overloading the pack or ESC.
        """)

        st.markdown("### Step 1 — Inputs")
        st.write("""
        - **Dᵢₙ** = prop diameter in inches  
        - **Pᵢₙ** = prop pitch in inches  
        - **KV** = motor KV  
        - **S** = cell count  
        - **B** = blade count (2, 3, 4, …)  
        """)

        st.markdown("### Step 2 — Reference Values")
        st.write("""
        These define a 'normal' 5\" freestyle baseline:
        - **KV_ref** = 1800  
        - **S_ref** = 6  
        - **B_ref** = 3  (tri‑blade)
        """)

        st.markdown("### Step 3 — Prop Load Index Formula")
        st.latex(
            r"PLI = \frac{P_{in}}{D_{in}}"
            r"\cdot \frac{KV}{KV_{ref}}"
            r"\cdot \frac{S}{S_{ref}}"
            r"\cdot \frac{B}{B_{ref}}"
        )

        st.write("""
        This is a dimensionless load number:
        - more pitch → higher PLI  
        - more KV → higher PLI  
        - more cells → higher PLI  
        - more blades → higher PLI  
        """)

        st.markdown("### Step 4 — How to Interpret PLI")
        st.write("""
        - **PLI ≤ 0.8** → Gentle / easy on pack & ESC  
        - **0.8 < PLI ≤ 1.0** → Normal / sporty  
        - **1.0 < PLI ≤ 1.15** → Hot / aggressive  
        - **PLI > 1.15** → High overload risk (only on purpose)  
        """)

        st.markdown("### Example — 5\" on 6S, 1800KV, tri‑blade")
        st.write("""
        Here KV/KV_ref = 1, S/S_ref = 1, B/B_ref = 1, so PLI = Pᵢₙ / Dᵢₙ:

        - 5×3.6×3 → PLI = 0.72 → Gentle  
        - 5×4.3×3 → PLI = 0.86 → Normal  
        - 5×5.1×3 → PLI = 1.02 → Hot  
        - 5×5.5×3 → PLI = 1.10 → Upper hot, near limit  
        """)

        st.markdown("### Example — 3\" on 3S, 5500KV, 1303.5")
        st.write("""
        - 3×1.6×2 → PLI ≈ 0.54 → Very gentle / super safe  
        - 3×1.8×3 → PLI ≈ 0.92 → Sporty / normal load  

        Builders can use this to sanity‑check prop pitch and blade count choices
        against their KV and cell count, before they buy props that are way too
        heavy for their pack or ESC.
        """)



    with st.expander("Motor Physics", expanded=False):
        st.markdown("## Motor Physics")

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
        st.markdown("## Propeller Physics")

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
        st.markdown("## Battery Physics")

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
        st.markdown("## ESC Physics")

        st.latex(r"P_{esc} = I^2 R_{mosfet} + P_{switching}")

        st.write("""
        - Higher PWM frequency increases smoothness but increases switching losses.
        - Demag compensation prevents desync under high load.
        - Timing affects torque and efficiency:
            - Low timing = efficient, cooler
            - High timing = more torque, more heat
        """)

    with st.expander("Flight Controller Physics", expanded=False):
        st.markdown("## Flight Controller Physics")

        st.latex(r"Loop\ Frequency = \frac{1}{Loop\ Time}")
        st.latex(r"CPU\ Load \propto Loop\ Rate \cdot Filter\ Load \cdot Motor\ Count")

        st.write("""
        - Higher loop frequency improves responsiveness.
        - Higher CPU load increases FC heat.
        - Frame noise increases filtering load.
        - DShot rate affects motor update speed.
        """)

    with st.expander("Aerodynamics & Drag", expanded=False):
        st.markdown("## Aerodynamics & Drag")

        st.latex(r"D = \tfrac{1}{2} \rho C_d A v^2")
        st.latex(r"T_{forward} = \sqrt{T_{total}^2 - W^2}")
        st.latex(r"v_{max} = \sqrt{\frac{2 T_{forward}}{\rho C_d A}}")

        st.write("""
        - Drag increases with the square of velocity.
        - Forward thrust is limited by the need to hold the quad up.
        - Max speed occurs when forward thrust equals drag.
        """)

    with st.expander("Thrust‑to‑Weight Ratio (TWR)", expanded=False):
        st.markdown("## Thrust‑to‑Weight Ratio (TWR)")

        st.latex(r"TWR = \frac{T_{max}}{W}")
        st.write("""
        - TWR > 1 means the quad can hover.
        - TWR > 4 is typical for freestyle.
        - TWR > 8 is typical for racing.
        """)

    with st.expander("Disk Loading", expanded=False):
        st.markdown("## Disk Loading")

        st.latex(r"DL = \frac{W}{A_{total}}")
        st.write("""
        - Lower disk loading improves efficiency and stability.
        - Higher disk loading increases responsiveness but reduces flight time.
        """)

    with st.expander("Hover Power", expanded=False):
        st.markdown("## Hover Power")

        st.latex(r"P_{hover} \approx \frac{T^{3/2}}{\sqrt{2 \rho A}}")
        st.write("""
        - Hover power increases with weight.
        - Larger props reduce hover power.
        """)

    with st.expander("Flight Time", expanded=False):
        st.markdown("## Flight Time")

        st.latex(r"t_{min} = \frac{E_{Wh}}{P_{avg}} \cdot 60")
        st.write("""
        - Flight time is battery energy divided by average power draw.
        - Aggressive flying increases power draw dramatically.
        """)

    with st.expander("Radio & RF Physics", expanded=False):
        st.markdown("## Radio & RF Physics")

        st.latex(r"FSPL(dB) = 20 \log_{10}(d) + 20 \log_{10}(f) + 32.44")
        st.latex(r"LinkBudget = P_{tx} + G_{tx} + G_{rx} - FSPL - L_{misc}")
        st.latex(r"Range \propto 10^{\frac{(LinkBudget)}{20}}")
        st.latex(r"Loss_{pol} = 20 \log_{10}(\cos(\theta))")
        st.latex(r"Loss_{CP/LP} \approx 3 \text{ dB}")
        st.latex(r"FresnelRadius = \sqrt{\frac{\lambda d_1 d_2}{d_1 + d_2}}")

        st.write("""
        ### Free‑Space Path Loss (FSPL)
        - FSPL increases with both **distance** and **frequency**.
        - Higher frequency (5.8 GHz) loses range faster than lower frequency (2.4 GHz).
        - Every **6 dB** of additional loss cuts your range in half.

        ### Link Budget
        - Determines maximum usable range.
        - Includes:
            - Transmit power (mW → dBm)
            - Antenna gains (Tx + Rx)
            - FSPL
            - Misc losses (polarization, connectors, body blocking)
        - Higher link budget = longer range.

        ### Decibels (dB)
        - **+3 dB = 2× power**
        - **+6 dB = 4× power**
        - **+10 dB = 10× power**
        - **−20 dB = 1/10th power**
        - Range scales with the **square root** of power.

        ### Antenna Gain
        - Higher gain antennas focus energy → more range but narrower beam.
        - Omni antennas: 0–2 dBi
        - Patch antennas: 6–14 dBi
        - Helicals: 10–16 dBi

        ### Polarization Loss
        - Linear ↔ Linear misalignment:
            - 0° = 0 dB loss
            - 45° = −3 dB
            - 90° = **−∞ dB** (no signal)
        - Circular ↔ Linear mismatch ≈ **−3 dB**
        - LHCP ↔ RHCP mismatch ≈ **−30 dB**

        ### Fresnel Zone
        - RF energy travels in a **fat rugby‑ball shaped volume**, not a straight line.
        - Obstructions inside the Fresnel zone cause:
            - multipath
            - fading
            - sudden link drops
        - Larger at lower frequencies (2.4 GHz > 5.8 GHz).

        ### Multipath & Reflections
        - Indoors or near metal structures:
            - reflections cause constructive/destructive interference
            - RSSI fluctuates rapidly
            - desync risk increases
        - Circular polarization helps reject reflections.

        ### Practical FPV Rules of Thumb
        - Every **3 dB** = ~1.4× range
        - Every **6 dB** = ~2× range
        - Every **20 dB** = ~10× range
        - Body blocking = −10 to −20 dB
        - Trees = −3 to −12 dB
        - Buildings = −20 to −40 dB
        - Wet foliage is RF death
        """)

    with st.expander("Frequency Comparison (Civilian & Military UAS Bands)", expanded=False):
        st.markdown("## Frequency Comparison (Civilian & Military UAS Bands)")

        st.write("""
        Below is a comparison of common FPV frequencies and the major bands used in 
        professional and military‑grade UAS systems. These are physics‑based characteristics, 
        not operational details.

        ### **5.8 GHz (Civilian FPV Video)**
        - Shortest range
        - Weak penetration
        - Very small antennas
        - High bandwidth → good video quality
        - Strongly affected by foliage and walls

        ### **2.4 GHz (ELRS, WiFi, Control Links)**
        - Medium range
        - Better penetration than 5.8 GHz
        - Moderate antenna size
        - Good balance of range + bandwidth

        ### **900 MHz / 868 MHz (Long‑Range Control)**
        - Long range
        - Excellent penetration
        - Large antennas
        - Lower bandwidth → not used for HD video

        ---

        ## **Military / Professional UAS Frequency Bands**

        ### **L‑Band (1–2 GHz)**
        - Good penetration through foliage and buildings
        - Long range due to low FSPL
        - Moderate antenna size
        - Used for telemetry, command links, and SATCOM uplinks
        - Physics: lower frequency → larger Fresnel zone, better NLOS performance

        ### **S‑Band (2–4 GHz)**
        - Similar to 2.4 GHz civilian but with more bandwidth
        - Good compromise between range and data rate
        - Often used for robust command & control (C2) links
        - Less attenuation than C‑band or Ku‑band

        ### **C‑Band (4–8 GHz)**
        - Higher bandwidth → supports high‑rate video/data
        - Shorter range than L/S bands
        - More LOS‑dependent
        - Smaller antennas than L/S band
        - Often used for tactical UAS video downlinks

        ### **Ku‑Band (12–18 GHz)**
        - Very high bandwidth
        - Shorter range unless using directional antennas
        - Primarily used for SATCOM on larger UAS platforms
        - Requires precise antenna pointing
        - Strongly affected by rain fade and atmospheric absorption

        ---

        ## **Propagation Characteristics by Frequency**

        ### **Range**
        - Lower frequency → longer range
        - Higher frequency → shorter range

        ### **Penetration**
        - Lower frequency → better penetration (foliage, buildings)
        - Higher frequency → poor penetration

        ### **Antenna Size**
        - Lower frequency → larger antennas
        - Higher frequency → smaller antennas

        ### **Bandwidth**
        - Higher frequency → more bandwidth (better video/data)
        - Lower frequency → less bandwidth (better control reliability)

        ---

        ## **Practical Summary**

        | Band | Frequency | Range & Penetration | Antenna Size | Bandwidth | Typical Use |
        |------|-----------|---------------------|----------------|------------|--------------|
        | 900 MHz | 0.9 GHz | Excellent | Large | Low | LR control |
        | 2.4 GHz | 2.4 GHz | Good | Medium | Medium | Control / FPV |
        | 5.8 GHz | 5.8 GHz | Short | Small | High | FPV video |
        | L‑Band | 1–2 GHz | Excellent | Medium‑Large | Low‑Med | C2 / Telemetry |
        | S‑Band | 2–4 GHz | Good | Medium | Medium | C2 / Video |
        | C‑Band | 4–8 GHz | Medium | Small | High | Video downlink |
        | Ku‑Band | 12–18 GHz | Short | Very Small | Very High | SATCOM video/data |
        """)

    with st.expander("Build Style Definitions", expanded=False):
        st.markdown("## Build Style Definitions")

        st.write("""
        - **Whoop:** 1.6–2.0" props, <80g AUW  
        - **Toothpick:** 2.5–3" props, <120g AUW, TWR > 4  
        - **Freestyle:** 3–5" props, 200–800g AUW, TWR 4–8  
        - **Racing:** 5" props, 400–600g AUW, TWR 8–12  
        - **Long Range:** 6–7" props, TWR 2–4, flight time > 10 min  
        - **Cinewhoop:** 3–3.5" props, ducts, stable flight  
        - **Kamikaze:** 7–10" props, 1–2kg AUW, 6–10 min  
        - **Utility:** 7–17" props, 1.5–4kg AUW, payload‑focused  
        """)

    with st.expander("Community Reference Tables", expanded=False):
        st.markdown("## Community Reference Tables")

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
