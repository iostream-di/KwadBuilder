import streamlit as st

def render_theory_section():

    with st.expander("MartyMayhem's Build Logic", expanded=False):
        st.markdown("## Marty's Motor KV Formula")

        st.write("""
        This formula estimates an appropriate motor KV for **any prop size**
        and **any battery voltage**.

        It is based on the observation that many successful FPV drone designs
        tend to operate with propeller tip speeds around **70% of the speed
        of sound**. By maintaining a similar tip Mach number across different
        prop sizes, we can derive a useful scaling rule for motor KV.
        """)

        st.markdown("### Step 1 — Convert prop diameter to meters")

        st.latex(r"D_m = D_{in} \cdot 0.0254")

        st.markdown("### Step 2 — Calculate prop tip speed")

        st.write("""
        Propeller tip speed is determined by prop diameter and rotational speed:
        """)

        st.latex(r"V_{tip} = \pi D \frac{RPM}{60}")

        st.markdown("### Step 3 — Estimate Target Prop Tip Mach")

        st.write("""
        Small props and large props do not appear to operate at the same
        optimal tip Mach number.

        Community-tested builds suggest that target tip Mach increases
        gradually with prop diameter and approaches approximately 0.70
        for larger aircraft.
        """)

        st.latex(
            r"M(D)=0.45+0.25\left(1-e^{-0.4(D-2)}\right)"
        )

        st.write("""
        Where:

        - D = prop diameter in inches
        - M(D) = estimated optimal tip Mach fraction
        """)

        st.markdown("### Step 4 — Relate RPM to Motor KV")

        st.latex(
            r"RPM = KV \cdot V \cdot \eta"
        )

        st.write("""
        For this model:

        - η = 0.90
        """)

        st.markdown("### Step 5 — Solve for KV")

        st.latex(
            r"KV = \frac{60\,M(D)\,a}{\pi D V \eta}"
        )

        st.write("""
        Substituting:

        - a = 343 m/s
        - η = 0.90
        - D in inches

        yields:
        """)

        st.latex(
            r"KV \approx \frac{327555 \cdot M(D)}{D_{in}\cdot V}"
        )

        st.markdown("### Final Formula")

        st.success(
            "KV ≈ (327555 × M(D)) / (Prop Diameter × Battery Voltage)"
        )

        st.latex(
            r"KV \approx \frac{327555 \cdot M(D)}{D_{in}\cdot V}"
        )

        st.markdown("### Example Calculations")

        st.write("**2 inch prop on 1S (3.8V nominal)**")

        st.latex(
            r"M(2)=0.45"
        )

        st.latex(
            r"KV=\frac{327555\times0.45}{2\times3.8}"
        )

        st.latex(
            r"KV\approx19,392"
        )

        st.write("**5 inch prop on 6S (22.2V nominal)**")

        st.latex(
            r"M(5)\approx0.625"
        )

        st.latex(
            r"KV=\frac{327555\times0.625}{5\times22.2}"
        )

        st.latex(
            r"KV\approx1,844"
        )

        st.write("**7 inch prop on 6S (22.2V nominal)**")

        st.latex(
            r"M(7)\approx0.683"
        )

        st.latex(
            r"KV=\frac{327555\times0.683}{7\times22.2}"
        )

        st.latex(
            r"KV\approx1,437"
        )

        st.write("**10 inch prop on 6S (22.2V nominal)**")

        st.latex(
            r"M(10)\approx0.690"
        )

        st.latex(
            r"KV=\frac{327555\times0.690}{10\times22.2}"
        )

        st.latex(
            r"KV\approx1,019"
        )

        st.write("**15 inch prop on 12S (44.4V nominal)**")

        st.latex(
            r"M(15)\approx0.698"
        )

        st.latex(
            r"KV=\frac{327555\times0.698}{15\times44.4}"
        )

        st.latex(
            r"KV\approx344"
        )

        st.markdown("### Why It Works")

        st.write("""
        Rather than assuming all drones operate at the same prop tip Mach
        number, this model adjusts the target Mach based on prop size.

        Tiny whoops generally operate at lower tip Mach values, while
        larger aircraft gradually converge toward approximately 0.70 Mach.

        This produces KV recommendations that better align with successful
        community builds across a much wider range of aircraft sizes.
        """)

        st.markdown("## Marty's Stator Diameter & Height Formula")

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
        heavy for their pack or ESC. Remember, as with motor KV, you can deviate 
        to an extent. 
        
        - Going lower will run cooler and safer and longer. Top speed 
        is exchanged for higher small area resolution. Great for navigating tight 
        spaces, or smooth attitude changes, like cinematic flying or long range recon. 
        - Going higher will run hotter, bleed the pack faster, and risk motor desyncs. 
        Small throttle movements are more exaggerated. High pitch is ideal for aggressive 
        freestyle and racing since you are getting the punch you need from the props.

        These are the basic formulas I use on my own builds. They are mostly based on my own
        studies and community driven data. I am not an aerospace engineer. My strengths are 
        in embedded systems engineering. But, I am an FPV pilot and an engineer at heart. Use 
        these formulas with caution. I am not responsible for any injury or damages. Good luck, bro.
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

    with st.expander("PID Loops, Feed‑Forward & Tuning Diagnostics", expanded=False):

        st.markdown("## PID Loops — What They Actually Do")

        st.write("""
        A PID loop is the flight controller’s core control system. It constantly compares:
        - **what the quad is doing**, versus  
        - **what your sticks are commanding**,  
        and adjusts motor power to close the gap.

        PID stands for **Proportional, Integral, Derivative**. Each term contributes a
        different kind of correction and affects how the quad feels in the air.
        """)

        st.markdown("### P — Proportional (The Muscle)")
        st.write("""
        **P** reacts instantly to error.  
        - More P = stronger, tighter, more locked‑in  
        - Too much P = fast, high‑frequency oscillations  
        - Too little P = mushy, drifty feel  

        **Pilot feel:** P is the quad’s *strength*.
        """)

        st.markdown("### I — Integral (The Memory)")
        st.write("""
        **I** corrects long‑term, accumulated error.  
        - Holds angle in wind  
        - Prevents slow drifting  
        - Too much I = slow wobbles, bounce‑back  
        - Too little I = quad gets pushed around  

        **Pilot feel:** I is the quad’s *stubbornness*.
        """)

        st.markdown("### D — Derivative (The Dampener)")
        st.write("""
        **D** predicts motion and damps it.  
        - Smooths out P  
        - Controls prop‑wash  
        - Too much D = heat, twitchiness  
        - Too little D = sloppy, lots of prop‑wash  

        **Pilot feel:** D is the quad’s *smoothness*.
        """)

        st.markdown("## Feed‑Forward (FF) — The Stick Predictor")

        st.write("""
        Feed‑Forward reacts directly to **your stick inputs**, instead of waiting for the
        PID loop to detect error. It makes the quad feel more connected and responsive.
        """)

        st.markdown("### What Feed‑Forward Does")
        st.write("""
        - Sharpens stick response  
        - Reduces perceived latency  
        - Helps maintain crispness even with heavy filtering  
        - Reduces workload on P and D  
        """)

        st.markdown("### Too Much Feed‑Forward")
        st.write("""
        - Twitchy or robotic feel  
        - Overshoots when stopping rotation  
        - Harsh, unnatural transitions  
        """)

        st.markdown("### Too Little Feed‑Forward")
        st.write("""
        - Sluggish stick response  
        - Feels like input delay  
        - Quad lags behind your commands  
        """)

        st.markdown("### Pilot Feel Summary")
        st.write("""
        **Feed‑Forward is the quad’s 'stick sharpness' — it makes the quad follow your
        fingers instead of waiting for the PID loop to catch up.**
        """)

        st.markdown("---")
        st.markdown("## PID & FF Symptom → Root Cause Cheat Sheet")

        st.write("""
        This cheat sheet maps common flight symptoms to the most likely PID or Feed‑Forward
        causes. It gives builders a fast way to diagnose tune issues without needing
        blackbox logs.
        """)

        st.markdown("### Common Symptoms and Likely Causes")

        st.write("""
        **Fast, high‑frequency oscillations (buzzy)**  
        - P too high  
        - D too low  
        - Filters too light  

        **Slow wobbles or bounce‑back after flips**  
        - I too high  
        - D too low  
        - P too low  

        **Prop‑wash wobble on throttle chop**  
        - D too low  
        - Filters too heavy  
        - P too low  

        **Twitchy, robotic, over‑snappy response**  
        - Feed‑Forward too high  
        - D too high  

        **Sluggish, delayed stick response**  
        - Feed‑Forward too low  
        - P too low  

        **Motors getting hot quickly**  
        - D too high  
        - Filters too light  
        - P too high  

        **Quad won’t hold angle in wind**  
        - I too low  

        **Drifts or slowly wanders off‑axis**  
        - I too low  
        - Possible mechanical issue (loose arm, soft mount)  

        **Overshoots when stopping rotation**  
        - D too low  
        - Feed‑Forward too high  
        """)

        st.write("""
        These patterns hold across 2–7\" FPV quads and give builders a fast, intuitive way
        to diagnose tune issues by feel.
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

    with st.expander("Acronyms & Abbreviations", expanded=False):
        st.markdown("## Common FPV & Engineering Acronyms")

        st.write("""
        **AUW** — All-Up Weight (total flying weight)  
        **B_ref** — Reference blade count (tri-blade = 3)  
        **CT** — Thrust Coefficient  
        **DL** — Disk Loading  
        **DShot** — Digital Shot (digital ESC protocol)  
        **ESC** — Electronic Speed Controller  
        **FC** — Flight Controller  
        **FF** — Feed-Forward (stick prediction term in control loop)  
        **FSPL** — Free-Space Path Loss  
        **KV** — RPM per volt (motor constant)  
        **Kt** — Torque constant (Nm per amp)  
        **LPF** — Low-Pass Filter  
        **mAh** — Milliamp-Hours (battery capacity)  
        **PID** — Proportional, Integral, Derivative (control loop)  
        **PLI** — Prop Load Index  
        **PWM** — Pulse-Width Modulation  
        **RPM** — Revolutions Per Minute  
        **RSSI** — Received Signal Strength Indicator  
        **S_ref** — Reference cell count (6S baseline)  
        **TWR** — Thrust-to-Weight Ratio  
        **VTX** — Video Transmitter  
        **Wh** — Watt-Hours (battery energy)  
        """)

        st.markdown("## Battery & Power Terms")
        st.write("""
        **C Rating** — Discharge capability of a battery  
        **IR** — Internal Resistance  
        **LiPo** — Lithium Polymer battery  
        **Li-Ion** — Lithium-Ion battery  
        **V_cell** — Voltage per cell  
        **V_pack** — Total pack voltage  
        """)

        st.markdown("## Radio & RF Terms")
        st.write("""
        **dB** — Decibel (logarithmic power ratio)  
        **dBi** — Antenna gain relative to isotropic radiator  
        **ELRS** — ExpressLRS (long-range RC protocol)  
        **GHz** — Gigahertz (frequency unit)  
        **LP** — Linear Polarization  
        **CP** — Circular Polarization  
        **LHCP/RHCP** — Left/Right-Hand Circular Polarization  
        """)

        st.markdown("## Prop & Motor Terms")
        st.write("""
        **D_in** — Prop diameter in inches  
        **P_in** — Prop pitch in inches  
        **B** — Blade count  
        **d_mm** — Stator diameter in millimeters  
        **h_mm** — Stator height in millimeters  
        **ω (omega)** — Angular velocity (rad/s)  
        """)

        st.markdown("## Physics & Math Terms")
        st.write("""
        **ρ (rho)** — Air density  
        **π (pi)** — 3.14159…  
        **τ (tau)** — Torque  
        **ω (omega)** — Angular velocity  
        **A** — Area  
        **T** — Thrust  
        **P** — Power  
        """)

    with st.expander("FPV Slang & Community Terminology", expanded=False):
        st.markdown("## Common FPV Slang & What It Means")

        st.write("""
        **Bando** — An abandoned building or structure used for freestyle flying.  
        **Send / Full Send** — Flying aggressively with no hesitation.  
        **Rip / Ripping** — Flying fast, hard, or with style.  
        **Pack** — A battery (LiPo or Li-Ion).  
        **Sag** — Voltage drop under load.  
        **Desync** — When a motor loses sync with the ESC, causing a crash.  
        **Turtle Mode** — Using reversed motors to flip the quad upright after a crash.  
        **Propwash** — Turbulence from your own props causing wobble on throttle chop.  
        **Jello** — Wavy video caused by vibration.  
        **Whoop** — Tiny ducted quad (1.6–2.0”).  
        **Toothpick** — Ultra-light 2.5–3” quad with minimal frame.  
        **Cinewhoop** — Ducted quad for smooth cinematic footage.  
        **Freestyle** — Flow-based acrobatic flying.  
        **Racer** — High-speed, gate-focused quad.  
        **Long Range** — Built for endurance and distance.  
        **Failsafe** — Loss of radio link causing the quad to drop or return.  
        **Brownout** — Momentary voltage drop causing electronics to reboot.  
        **Magic Smoke** — When electronics burn out (jokingly: “the smoke that makes electronics work”).  
        **Batteries are spicy** — Battery is puffed, damaged, or dangerous.  
        **Bando Basher** — A quad built tough for crashing into concrete.  
        **Tuning** — Adjusting PID, filters, and FF for better flight performance.  
        **Dry Weight** — Weight without battery.  
        **AUW** — All-Up Weight (with battery).  
        **Punchout** — Full-throttle vertical climb.  
        **Yaw Washout** — Sudden yaw dip during hard turns or dives.  
        **Ghost Branch** — Invisible thin branch that ruins your day.  
        **Gremlin** — A tiny 2” micro quad.  
        **Prop Strike** — When props hit something (frame, wire, branch).  
        **Brap / Braaap** — The sound of a quad ripping (yes, it’s a word).  
        """)

        st.markdown("## Social & Community Terms")
        st.write("""
        **OG** — Original pilot from early FPV days.  
        **Sim** — Flight simulator (Liftoff, Velocidrone, DRL, etc.).  
        **Spotter** — Person watching your flight for safety.  
        **Failsafe Dance** — The quad twitching or spinning after failsafe.  
        **Dumpster Dive** — Searching for a lost quad in trash, bushes, or sketchy places.  
        **Walk of Shame** — Walking to retrieve your crashed quad.  
        **Tree’d** — When your quad gets stuck in a tree.  
        **Grass Ninja** — When your quad disappears into grass like it was never there.  
        """)

        st.markdown("## Build & Repair Slang")
        st.write("""
        **Blue Smoke** — Burned electronics (same as magic smoke).  
        **Soft Mount** — Rubber mounting to reduce vibration.  
        **Hard Mount** — Direct mounting (no vibration isolation).  
        **Stack** — FC + ESC assembly.  
        **Smoke Stopper** — Inline current limiter to prevent frying electronics.  
        **Conformal Coat** — Waterproofing electronics with silicone coating.  
        **Frankenbuild** — A quad made from mismatched or leftover parts.  
        **Solder Goblin** — Someone who solders like a gremlin (badly).  
        **Tuning Gremlins** — Mysterious issues that disappear when you stop looking.  
        """)

    with st.expander("FPV Trick Names & Freestyle Maneuvers", expanded=False):
        st.markdown("## Core Freestyle Tricks")

        st.write("""
        **Powerloop** — Looping over an object and exiting through the same gap.  
        **Split‑S** — Half‑roll into a half‑loop to reverse direction quickly.  
        **Immelmann** — Half‑loop into a half‑roll to gain altitude and reverse direction.  
        **Matty Flip** — Backwards inverted dive around an object (invented by MattyStuntz).  
        **Dive** — Vertical drop down a building, tower, or cliff.  
        **Orbit** — Circling an object smoothly while keeping it centered in view.  
        **Rewind** — Reversing a trick mid‑motion to retrace your path.  
        **Juicy Flick** — Snappy stick reversal creating a sharp, rhythmic motion.  
        **Juicy Roll** — Fast roll with immediate counter‑roll for a “whip” effect.  
        **Snap Roll** — Extremely fast roll with high stick input.  
        **Barrel Roll** — Smooth, continuous roll while maintaining forward motion.  
        **Corkscrew** — Spiral descent or ascent around an object.  
        **Knife‑Edge** — Flying sideways with the quad banked at 90°.  
        **Skimming / Mowing The Lawn** — Flying insanely close to the ground for a prolonged time.
        """)

        st.markdown("## Gap Tricks")

        st.write("""
        **Gap Shot** — Flying through any opening (window, doorway, branches).  
        **Micro Gap** — A stupidly small gap you shouldn’t try but will anyway.  
        **Powerloop Gap** — Powerlooping through a gap on the return.  
        **Inverted Gap** — Entering a gap upside‑down.  
        **Side Gap** — Sliding sideways through a narrow opening.  
        **Reverse Gap** — Entering a gap backwards.  
        """)

        st.markdown("## Advanced Freestyle Maneuvers")

        st.write("""
        **Wall Tap** — Lightly touching a wall or surface with a prop or arm.  
        **Ground Tap / Grass Tap** — Skimming low enough to touch the ground.  
        **Pole Tap** — Tapping a pole mid‑flight without crashing.  
        **Ladder Climb** — Ascending through multiple stacked gaps.  
        **Ladder Drop** — Descending through stacked gaps.  
        **Rubik’s Cube** — Roll → flip → roll in rapid sequence.  
        **Hurricane** — Tight, fast orbit with heavy tilt.  
        **Inverted Yaw Spin** — Spinning on yaw while upside‑down.  
        **Tornado** — Fast yaw spin while climbing or descending.  
        **Trippy Spin** — Orbiting an object while yawing in the opposite direction.  
        **Backward Dive** — Diving backwards while maintaining camera lock.  
        **Backward Powerloop** — Powerloop performed in reverse orientation.  
        """)

        st.markdown("## Cinematic Maneuvers")

        st.write("""
        **Reveal Shot** — Rising or sliding to reveal a scene or subject.  
        **Orbit Reveal** — Orbiting while revealing a subject from behind cover.  
        **Slider** — Smooth lateral movement with minimal tilt.  
        **Dolly Shot** — Forward/backward movement with stable horizon.  
        **Fly‑Through** — Smooth entry through buildings, vehicles, or structures.  
        **Cine‑Dive** — Slow, controlled dive for cinematic effect.  
        """)

        st.markdown("## Racing & Technical Maneuvers")

        st.write("""
        **Split‑S Gate** — Split‑S maneuver through a race gate.  
        **Power Loop Gate** — Powerlooping a race gate.  
        **Hairpin Turn** — Extremely tight 180° turn.  
        **Slalom** — Rapid side‑to‑side movement through obstacles.  
        **Chicane** — Quick left‑right or right‑left directional change.  
        **Dive Gate** — Vertical drop through a gate.  
        """)

        st.markdown("## Micro‑Quad / Whoop‑Style Tricks")

        st.write("""
        **Wall Ride** — Riding along a wall at an angle.  
        **Ceiling Kiss** — Lightly touching the ceiling with ducts.  
        **Table Split** — Sliding under tables or furniture.  
        **Vent Gap** — Flying through vents or tiny openings.  
        **Hallway Surf** — Riding the air cushion in narrow hallways.  
        """)

        st.markdown("## Flow & Style Terms")

        st.write("""
        **Flow** — Smooth, continuous movement with intentional lines.  
        **Juicy** — Snappy, rhythmic, high‑energy freestyle with reversals.  
        **Technical** — Precision flying with tight gaps and complex lines.  
        **Aggro** — Fast, hard, high‑throttle freestyle.  
        **Cinematic** — Smooth, stable, visually pleasing movement.  
        **Proximity** — Flying extremely close to surfaces or objects.  
        """)

