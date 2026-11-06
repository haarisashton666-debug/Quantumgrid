
import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime

st.set_page_config(
    page_title="QuantumGrid Control Center",
    page_icon="⚡",
    layout="wide"
)

# Session data
if "history" not in st.session_state:
    st.session_state.history = []

if "battery" not in st.session_state:
    st.session_state.battery = 85.0

# Styling
st.markdown("""
<style>
.stApp {
    background-color: #0b1220;
    color: white;
}
[data-testid="stMetric"] {
    background: #17243a;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #263c59;
}
h1, h2, h3 {
    color: #55d6be;
}
</style>
""", unsafe_allow_html=True)

# Header
st.title("⚡ QUANTUMGRID")
st.caption("INTELLIGENT EMERGENCY POWER DISTRIBUTION")
st.success("● CONTROL CENTER ONLINE")

# Sidebar
st.sidebar.title("⚡ QuantumGrid")
page = st.sidebar.radio(
    "NAVIGATION",
    ["Live Monitoring", "Power Analytics",
     "Emergency Alerts", "Quantum Optimizer"]
)

st.sidebar.info("System: Demo Mode")
st.sidebar.caption("Automatic updates every 3 seconds")

# Live monitoring
@st.fragment(run_every="3s")
def live_dashboard():

    power = round(random.uniform(40, 95), 2)
    voltage = round(random.uniform(215, 240), 2)
    current = round(power * 1000 / voltage, 2)

    st.session_state.battery = max(
        0, min(100, st.session_state.battery
               + random.uniform(-0.2, 0.1))
    )

    status = "NORMAL" if power < 85 else "HIGH LOAD"

    st.session_state.history.append({
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Power": power,
        "Voltage": voltage
    })

    st.session_state.history = (
        st.session_state.history[-30:]
    )

    a, b, c, d = st.columns(4)

    a.metric("Power Consumption", f"{power} kW")
    b.metric("Grid Voltage", f"{voltage} V")
    c.metric("Current", f"{current} A")
    d.metric("Battery Level",
             f"{st.session_state.battery:.1f}%")

    st.divider()

    st.subheader("⚡ Electricity Network")

    st.metric("Grid Status", status)

    df = pd.DataFrame(st.session_state.history)

    st.subheader("Live Power Consumption")
    st.line_chart(
        df.set_index("Time")[["Power"]]
    )

    st.subheader("Facility Monitoring")

    facilities = pd.DataFrame([
        ["Hospital", 50, "Critical", "ONLINE"],
        ["Water Pump", 30, "High", "ONLINE"],
        ["Mobile Tower", 20, "High", "ONLINE"],
        ["Residential Area", 40, "Normal", "STANDBY"]
    ], columns=[
        "Facility", "Demand (kW)",
        "Priority", "Status"
    ])

    st.dataframe(
        facilities,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Last simulated update: "
        + datetime.now().strftime("%H:%M:%S")
    )

# Navigation pages
if page == "Live Monitoring":
    live_dashboard()

elif page == "Power Analytics":
    st.header("📊 Power Analytics")

    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.line_chart(df.set_index("Time"))
    else:
        st.info("Waiting for monitoring data.")

elif page == "Emergency Alerts":
    st.header("🚨 Emergency Center")

    st.warning("DEMO ALERT: Simulated grid overload warning")
    st.info("Hospital supply: Protected")
    st.success("Water pump: Operational")
    st.info("Mobile tower: Operational")

elif page == "Quantum Optimizer":
    st.header("⚛️ Quantum Optimization Center")

    st.write(
        "QAOA-based power distribution research module"
    )

    st.info(
        "Your classical optimization result: "
        "Hospital + Water Pump + Mobile Tower"
    )

    st.write("Total priority score: 250")

    st.warning(
        "Quantum circuit integration is the next development stage. "
        "No live quantum computation is being performed here."
    )

st.divider()

st.caption(
    "QUANTUMGRID | Intelligent Energy Infrastructure | "
    "Prototype v1.0"
)
