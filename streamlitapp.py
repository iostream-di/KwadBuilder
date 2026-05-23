import streamlit as st

# -------------------------
# IMPORT YOUR CLASSES HERE
# -------------------------
from kwad import Component, Motor, Propeller, Frame, VTX, FC, ESC, AIO, RX, GPS, CAM, ANT, LIPO, CAP, ActionCAM, Kwad


st.title("FPV Kwad Builder")

# -------------------------
# SESSION STATE INIT
# -------------------------
if "components" not in st.session_state:
    st.session_state.components = {
        "frame": None,
        "motors": [],
        "props": [],
        "esc": None,
        "fc": None,
        "aio": None,
        "gps": None,
        "rx": None,
        "rx_ant": None,
        "vtx": None,
        "vtx_ant": None,
        "cam": None,
        "actionCam": None,
        "cap": None,
        "lipo": None
    }

# -------------------------
# COMPONENT EDITOR FUNCTION
# -------------------------
def edit_component(label, cls, defaults=None, extra_fields=None, list_mode=False):
    st.subheader(label)

    if list_mode:
        count = st.number_input(f"How many {label}?", 0, 8, len(st.session_state.components[label]))
        st.session_state.components[label] = st.session_state.components[label][:count]

        for i in range(count):
            with st.expander(f"{label} #{i+1}"):
                st.session_state.components[label][i] = build_component_ui(cls, f"{label}_{i}", defaults, extra_fields)

    else:
        st.session_state.components[label] = build_component_ui(cls, label, defaults, extra_fields)


def build_component_ui(cls, key_prefix, defaults, extra_fields):
    defaults = defaults or {}

    manufacturer = st.text_input(f"{key_prefix} Manufacturer", defaults.get("manufacturer", ""), key=f"{key_prefix}_man")
    model = st.text_input(f"{key_prefix} Model", defaults.get("model", ""), key=f"{key_prefix}_model")
    partNumber = st.text_input(f"{key_prefix} Part Number", defaults.get("partNumber", ""), key=f"{key_prefix}_pn")
    weight = st.number_input(f"{key_prefix} Weight (g)", 0.0, 2000.0, defaults.get("weight", 0.0), key=f"{key_prefix}_w")
    cost = st.number_input(f"{key_prefix} Cost ($)", 0.0, 1000.0, defaults.get("cost", 0.0), key=f"{key_prefix}_c")

    values = [manufacturer, model, partNumber, weight, cost]

    if extra_fields:
        for field_name, field_type, default in extra_fields:
            if field_type == int:
                val = st.number_input(f"{key_prefix} {field_name}", 0, 99999, default, key=f"{key_prefix}_{field_name}")
            elif field_type == float:
                val = st.number_input(f"{key_prefix} {field_name}", 0.0, 99999.0, default, key=f"{key_prefix}_{field_name}")
            elif field_type == str:
                val = st.text_input(f"{key_prefix} {field_name}", default, key=f"{key_prefix}_{field_name}")
            elif field_type == bool:
                val = st.checkbox(f"{key_prefix} {field_name}", default, key=f"{key_prefix}_{field_name}")

            values.append(val)

    return cls(*values)



# -------------------------
# COMPONENT EDITORS
# -------------------------

edit_component("frame", Frame, extra_fields=[
    ("fc_mountingPattern", str, ""),
    ("esc_mountingPattern", str, ""),
    ("aio_mountingPattern", str, ""),
    ("motor_mountingPattern", str, ""),
    ("vtx_mountingPattern", str, ""),
    ("cam_mountingPattern", str, ""),
    ("propDiameterClearance", float, 0.0),
    ("armThickness", float, 0.0),
    ("frameThickness", float, 0.0),
    ("style", str, "True X")
])

edit_component("motors", Motor, list_mode=True, extra_fields=[
    ("kv", int, 0),
    ("statorDiameter", float, 0.0),
    ("statorHeight", float, 0.0),
    ("mountingPattern", str, ""),
    ("maxCurrent", float, 0.0),
    ("propMountType", str, "5mm")
])

edit_component("props", Propeller, list_mode=True, extra_fields=[
    ("bladeCount", int, 2),
    ("diameter", float, 0.0),
    ("pitch", float, 0.0),
    ("propMountType", str, "5mm")
])

edit_component("esc", ESC, extra_fields=[
    ("maxCurrent", float, 0.0),
    ("vin", float, 0.0),
    ("mountingPattern", str, "")
])

edit_component("fc", FC)
edit_component("aio", AIO, extra_fields=[
    ("maxCurrent", float, 0.0),
    ("vin", float, 0.0),
    ("mountingPattern", str, "")
])

edit_component("gps", GPS)
edit_component("rx", RX)
edit_component("rx_ant", ANT)
edit_component("vtx", VTX, extra_fields=[
    ("mountingPattern", str, ""),
    ("currentPull", float, 0.0),
    ("vin", float, 0.0)
])
edit_component("vtx_ant", ANT)
edit_component("cam", CAM, extra_fields=[
    ("mountingPattern", str, "")
])
edit_component("actionCam", ActionCAM)
edit_component("cap", CAP, extra_fields=[
    ("maxVoltage", float, 0.0),
    ("microFarad", float, 0.0)
])
edit_component("lipo", LIPO, extra_fields=[
    ("cells", int, 4),
    ("capacity", int, 1000),
    ("cRating", int, 100),
    ("conType", str, "XT60"),
    ("hv", bool, False)
])

# -------------------------
# BUILD + CHECK
# -------------------------

st.header("Build & Evaluate")

model = st.text_input("Kwad Model")
nickname = st.text_input("Nickname")
buildType = st.text_input("Build Type (Freestyle, Racing, LR, etc.)")

if st.button("Check"):
    kwad = Kwad(
        model,
        nickname,
        buildType,
        st.session_state.components["frame"],
        st.session_state.components["motors"],
        st.session_state.components["props"],
        st.session_state.components["esc"],
        st.session_state.components["cap"],
        st.session_state.components["fc"],
        st.session_state.components["aio"],
        st.session_state.components["gps"],
        st.session_state.components["rx"],
        st.session_state.components["rx_ant"],
        st.session_state.components["vtx"],
        st.session_state.components["vtx_ant"],
        st.session_state.components["cam"],
        st.session_state.components["actionCam"],
        st.session_state.components["lipo"]
    )

    st.subheader("Results")
    st.write("Dry Weight:", kwad.dryWeight)
    st.write("All-Up Weight:", kwad.allUpWeight)
    st.write("Total Cost:", kwad.totalCost)
    st.write("Thrust:", kwad.thrust)
    st.write("TWR:", kwad.twr)
    st.write("Max Payload:", kwad.maxPayloadWeight)
    st.write("Max RPM:", kwad.maxRPM)
    st.write("Max Current:", kwad.maxCurrent)
    st.write("Expected Flight Time:", kwad.expectedFlightTime)
    st.write("Max Speed:", kwad.maxSpeed)
    st.write("Cooldown Time:", kwad.expectedCooldownTime)
    st.write("Grade Rating:", kwad.gradeRating)
    st.write("Compatibility:", kwad.compatibility)
