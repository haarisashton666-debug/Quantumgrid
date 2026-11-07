import time
from datetime import date, timedelta
import numpy as np
import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="QuantumGrid", page_icon="⚡", layout="wide")

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#050816,#0b1230);}
.card{background:#111a3a;border:1px solid #26336b;border-radius:14px;
      padding:14px;text-align:center;margin-bottom:8px}
.card h4{margin:0;color:#8aa0ff;font-size:14px;font-weight:500}
.card h2{margin:4px 0 0;font-size:28px;color:#fff}
</style>""", unsafe_allow_html=True)

# ---------- Sidebar ----------
st.sidebar.title("⚡ QuantumGrid")
place = st.sidebar.text_input("Location", "Coimbatore")
lat = st.sidebar.number_input("Latitude", value=11.0168, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=76.9558, format="%.4f")
solar_area = st.sidebar.slider("Solar panel area (m²)", 10, 2000, 200)
wind_rated = st.sidebar.slider("Wind turbine rated (kW)", 1, 500, 50)
refresh = st.sidebar.slider("Refresh every (sec)", 2, 60, 5)

# ---------- Data ----------
@st.cache_data(ttl=300)
def get_weather(lat, lon):
    r = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,shortwave_radiation,cloud_cover",
        "hourly": "temperature_2m,wind_speed_10m,shortwave_radiation",
        "past_days": 1, "forecast_days": 2,
        "timezone": "auto", "wind_speed_unit": "ms"}, timeout=15)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=300)
def get_satellite(lat, lon):
    r = requests.get("https://satellite-api.open-meteo.com/v1/archive", params={
        "latitude": lat, "longitude": lon,
        "hourly": "shortwave_radiation",
        "start_date": str(date.today() - timedelta(days=1)),
        "end_date": str(date.today()),
        "timezone": "auto"}, timeout=15)
    r.raise_for_status()
    d = pd.DataFrame(r.json()["hourly"])
    d["time"] = pd.to_datetime(d["time"])
    return d

def wind_power(v, rated):
    v = np.asarray(v, dtype=float) * 1.4
    p = rated * np.clip((v - 3) / 9, 0, 1) ** 3
    return np.where((v < 3) | (v > 25), 0, p)

def solar_power(rad, area):
    return np.asarray(rad, dtype=float) * area * 0.18 * 0.8 / 1000

DARK = "plotly_dark"

# ---------- Live section ----------
@st.fragment(run_every=refresh)
def live():
    try:
        w = get_weather(lat, lon)
    except Exception as e:
        st.error(f"Weather data error: {e}")
        return

    c = w["current"]

    try:
        sat = get_satellite(lat, lon)
        rad_now = float(sat["shortwave_radiation"].dropna().iloc[-1])
        src = "Satellite (Himawari/Meteosat) + Open-Meteo"
    except Exception:
        rad_now = float(c["shortwave_radiation"])
        src = "Open-Meteo weather model"

    s_kw = float(solar_power(rad_now, solar_area))
    w_kw = float(wind_power(c["wind_speed_10m"], wind_rated))
    total = s_kw + w_kw
    capacity = solar_area * 0.18 * 0.8 + wind_rated

    st.title(f"🌍 Renewable Energy Intelligence – {place}")
    st.caption(f"Live · updated {time.strftime('%H:%M:%S')} · source: {src}")

    cards = [("🌡 Temperature", f"{c['temperature_2m']:.1f} °C"),
             ("💨 Wind speed", f"{c['wind_speed_10m']:.1f} m/s"),
             ("☀ Irradiance", f"{rad_now:.0f} W/m²"),
             ("☀ Solar output", f"{s_kw:.1f} kW"),
             ("🌀 Wind output", f"{w_kw:.1f} kW"),
             ("⚡ Total", f"{total:.1f} kW")]
    cols = st.columns(6)
    for col, (t, v) in zip(cols, cards):
        col.markdown(f"<div class='card'><h4>{t}</h4><h2>{v}</h2></div>",
                     unsafe_allow_html=True)

    h = pd.DataFrame(w["hourly"])
    h["time"] = pd.to_datetime(h["time"])
    h["solar"] = solar_power(h["shortwave_radiation"], solar_area)
    h["wind"] = wind_power(h["wind_speed_10m"], wind_rated)

    left, right = st.columns([2, 1])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=h["time"], y=h["solar"], name="Solar",
                  fill="tozeroy", line=dict(color="#fbbf24")))
    fig.add_trace(go.Scatter(x=h["time"], y=h["wind"], name="Wind",
                  fill="tozeroy", line=dict(color="#22d3ee")))
    now = pd.to_datetime(c["time"])
    fig.add_shape(type="line", x0=now, x1=now, y0=0, y1=1, yref="paper",
                  line=dict(color="#f43f5e", dash="dash"))
    fig.update_layout(template=DARK, title="Generation: past 24h + forecast",
                      yaxis_title="kW", height=360,
                      margin=dict(l=10, r=10, t=50, b=10))
    left.plotly_chart(fig, use_container_width=True)

    g = go.Figure(go.Indicator(
        mode="gauge+number", value=total,
        number={"suffix": " kW"}, title={"text": "Output vs capacity"},
        gauge={"axis": {"range": [0, capacity]},
               "bar": {"color": "#22c55e"},
               "steps": [{"range": [0, capacity * .33], "color": "#7f1d1d"},
                         {"range": [capacity * .33, capacity * .66], "color": "#78350f"},
                         {"range": [capacity * .66, capacity], "color": "#14532d"}]}))
    g.update_layout(template=DARK, height=360, margin=dict(l=20, r=20, t=60, b=10))
    right.plotly_chart(g, use_container_width=True)

    n, fs = 800, 10000
    t = np.arange(n) / fs
    phase = (time.time() % 1) * 2 * np.pi
    v_pk = 230 * np.sqrt(2)
    i_pk = np.sqrt(2) * total * 1000 / 230
    volt = v_pk * np.sin(2*np.pi*50*t + phase)
    curr = (i_pk * np.sin(2*np.pi*50*t + phase - 0.2)
            + 0.05 * i_pk * np.sin(2*np.pi*150*t + phase))

    wf = make_subplots(specs=[[{"secondary_y": True}]])
    wf.add_trace(go.Scatter(x=t*1000, y=volt, name="Voltage (V)",
                 line=dict(color="#a78bfa")), secondary_y=False)
    wf.add_trace(go.Scatter(x=t*1000, y=curr, name="Current (A)",
                 line=dict(color="#34d399")), secondary_y=True)
    wf.update_layout(template=DARK, title="Inverter output waveform (50 Hz)",
                     xaxis_title="Time (ms)", height=340,
                     margin=dict(l=10, r=10, t=50, b=10))
    wf.update_yaxes(title_text="Voltage (V)", secondary_y=False)
    wf.update_yaxes(title_text="Current (A)", secondary_y=True)

    amp = np.abs(np.fft.rfft(curr)) / n * 2
    f = np.fft.rfftfreq(n, 1 / fs)
    m = f <= 500
    sp = go.Figure(go.Bar(x=f[m], y=amp[m], marker_color="#f472b6"))
    sp.update_layout(template=DARK, title="Current amplitude spectrum",
                     xaxis_title="Frequency (Hz)", yaxis_title="Amplitude (A)",
                     height=340, margin=dict(l=10, r=10, t=50, b=10))

    a, b = st.columns(2)
    a.plotly_chart(wf, use_container_width=True)
    b.plotly_chart(sp, use_container_width=True)

    with st.expander("Source readings"):
        st.dataframe(h, use_container_width=True)

live()
