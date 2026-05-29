# theory_section.py

import streamlit as st

def render_theory_section():

    st.markdown("## Motor Physics")

    st.latex(r"RPM_{no\_load} = KV \cdot V")
    st.latex(r"RPM_{loaded} \approx 0.78 \cdot RPM_{no\_load}")
    st.latex(r"\tau \propto V_{stator} = \pi \cdot \left(\frac{D}{2}\right)^2 \cdot H")

    st.write("""
    - KV determines RPM per volt.
    - Loaded RPM is typically ~78% of no‑load RPM.
    - Torque scales with stator volume (diameter × height).
    - Higher KV → more RPM, less torque.
    - Lower KV → more torque, less RPM.
    """)

    st.markdown("## Propeller Physics")

    st.latex(r"A_{disk} = \pi \left(\frac{D}{2}\right)^2")
    st.latex(r"Thrust \propto A_{disk}^{1.15} \cdot Pitch^{0.75} \cdot RPM^{1.15}")
    st.latex(r"Pitch\ Speed = Pitch \cdot \frac{RPM}{60}")

    st.write("""
    - Disk area determines thrust potential.
    - Higher pitch increases speed but also current draw.
    - More blades increase thrust but reduce efficiency.
    - Small props are inefficient at high thrust.
    """)

    st.markdown("## Battery Physics")

    st.latex(r"V_{nominal} = 3.8 \cdot S")
    st.latex(r"I_{safe} = C \cdot Capacity_{Ah}")
    st.latex(r"V_{sag} = I \cdot R_{internal}")

    st.write("""
    - Voltage sag reduces RPM and thrust.
    - Higher C rating reduces sag.
    - Larger packs sag less but weigh more.
    """)

    st.markdown("## ESC Physics")

    st.write("""
    - Higher PWM frequency increases smoothness but can increase heat.
    - Demag compensation prevents desync under high load.
    - Timing affects torque and efficiency:
        - Low timing = efficient, cooler
        - High timing = more torque, more heat
    """)

    st.markdown("## Flight Controller Physics")

    st.latex(r"Loop\ Frequency = \frac{1}{Loop\ Time}")
    st.write("""
    - Higher loop frequency improves responsiveness.
    - Higher CPU load increases FC heat.
    - Frame noise affects filtering load.
    - DShot rate affects motor update speed.
    """)

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
