import streamlit as st
import requests
import pandas as pd
import base64
from PIL import Image
import io
import time
import plotly.express as px
import plotly.graph_objects as go

BACKEND_URL = "http://127.0.0.1:8000"

# ─────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dakshiya AI – Industrial Monitoring",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif;
}
.stApp {
    background: #050a0f;
    color: #e0f0ff;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1628 0%, #050a0f 100%);
    border-right: 1px solid #1a3a5c;
}
[data-testid="stSidebar"] * { color: #c0d8f0 !important; }

/* ── Header Banner ── */
.dash-header {
    background: linear-gradient(135deg, #0a1f3d 0%, #0d2b4e 50%, #071524 100%);
    border: 1px solid #1e4a7a;
    border-radius: 12px;
    padding: 28px 36px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.dash-header::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(0,180,255,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.dash-header h1 {
    font-size: 2.2rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
    letter-spacing: 1px;
    text-shadow: 0 0 30px rgba(0,180,255,0.4);
}
.dash-header p {
    color: #7ab8e0;
    font-size: 1.05rem;
    margin: 6px 0 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}
.accent-dot {
    display: inline-block;
    width: 10px; height: 10px;
    background: #00b4ff;
    border-radius: 50%;
    margin-right: 8px;
    box-shadow: 0 0 10px #00b4ff;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.3); }
}

/* ── Section Headers ── */
.section-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: #00b4ff;
    letter-spacing: 2px;
    text-transform: uppercase;
    border-left: 3px solid #00b4ff;
    padding-left: 12px;
    margin: 28px 0 16px;
    font-family: 'Rajdhani', sans-serif;
}

/* ── KPI Cards ── */
.kpi-card {
    background: linear-gradient(135deg, #0d1f35 0%, #0a1828 100%);
    border: 1px solid #1a3a5c;
    border-radius: 10px;
    padding: 20px 24px;
    text-align: center;
    transition: border-color 0.3s, box-shadow 0.3s;
}
.kpi-card:hover {
    border-color: #00b4ff;
    box-shadow: 0 0 20px rgba(0,180,255,0.15);
}
.kpi-value {
    font-size: 2.4rem;
    font-weight: 700;
    color: #00b4ff;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
}
.kpi-label {
    font-size: 0.8rem;
    color: #6a9dbf;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 6px;
}

/* ── Status Badges ── */
.badge-good    { background:#0a2e1a; color:#00e676; border:1px solid #00e676; border-radius:20px; padding:4px 14px; font-size:0.85rem; font-weight:600; }
.badge-warn    { background:#2e1f00; color:#ffab00; border:1px solid #ffab00; border-radius:20px; padding:4px 14px; font-size:0.85rem; font-weight:600; }
.badge-danger  { background:#2e0a0a; color:#ff5252; border:1px solid #ff5252; border-radius:20px; padding:4px 14px; font-size:0.85rem; font-weight:600; }

/* ── Health Cards ── */
.health-card {
    background: #0a1828;
    border: 1px solid #1a3a5c;
    border-radius: 10px;
    padding: 18px;
    text-align: center;
}
.health-ok   { border-color: #00e676; box-shadow: 0 0 12px rgba(0,230,118,0.1); }
.health-fail { border-color: #ff5252; box-shadow: 0 0 12px rgba(255,82,82,0.1); }

/* ── Metric override ── */
[data-testid="stMetric"] {
    background: #0d1f35;
    border: 1px solid #1a3a5c;
    border-radius: 10px;
    padding: 14px 18px;
}
[data-testid="stMetricValue"] {
    color: #00b4ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.8rem !important;
}
[data-testid="stMetricLabel"] { color: #7ab8e0 !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #1a3a5c;
    border-radius: 10px;
    overflow: hidden;
}

/* ── Divider ── */
hr { border-color: #1a3a5c !important; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #003d6b, #005fa3);
    color: #ffffff;
    border: 1px solid #00b4ff;
    border-radius: 8px;
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600;
    letter-spacing: 1px;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #005fa3, #0080d4);
    box-shadow: 0 0 16px rgba(0,180,255,0.3);
}

/* ── Progress bars ── */
.stProgress > div > div { background: linear-gradient(90deg, #00b4ff, #0066cc) !important; }

/* ── Info/warning boxes ── */
.stAlert { border-radius: 8px !important; border-left-width: 4px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def safe_get(endpoint):
    try:
        r = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
        return r.json()
    except:
        return None

def safe_post(endpoint, files=None):
    try:
        r = requests.post(f"{BACKEND_URL}{endpoint}", files=files, timeout=10)
        return r.json()
    except:
        return None

def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 10px 0 20px;'>
        <div style='font-size:2.5rem;'>⚙️</div>
        <div style='font-size:1.3rem; font-weight:700; color:#00b4ff; letter-spacing:2px;'>DAKSHIYA AI</div>
        <div style='font-size:0.75rem; color:#5a8aaa; letter-spacing:1px; margin-top:4px;'>INDUSTRIAL MONITORING</div>
    </div>
    <hr style='border-color:#1a3a5c; margin-bottom:20px;'>
    """, unsafe_allow_html=True)

    st.markdown("**⚡ Live Controls**")
    refresh = st.toggle("Enable Live Monitoring", value=False)
    if refresh:
        interval = st.slider("Refresh interval (sec)", 3, 30, 5)
        st.caption(f"🔄 Refreshing every {interval}s")

    st.markdown("<hr style='border-color:#1a3a5c;'>", unsafe_allow_html=True)
    st.markdown("**🔗 System Info**")
    st.code(f"Backend: {BACKEND_URL}", language=None)

    health = safe_get("/health")
    if health:
        status = health.get("server_status", "unknown")
        color = "#00e676" if status == "running" else "#ff5252"
        st.markdown(f"<span style='color:{color}; font-size:0.85rem;'>● Server: {status.upper()}</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#ff5252; font-size:0.85rem;'>● Backend Offline</span>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1a3a5c;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.7rem; color:#3a6a8a; text-align:center;'>v2.0 · Dakshiya AI Platform</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
    <h1><span class="accent-dot"></span>Dakshiya AI – Intelligent Industrial Monitoring</h1>
    <p>// AI-powered computer vision system for real-time conveyor belt & material analysis</p>
</div>
""", unsafe_allow_html=True)

# Auto refresh
if refresh:
    time.sleep(interval)
    st.rerun()

# ─────────────────────────────────────────────
# SYSTEM HEALTH (top of page)
# ─────────────────────────────────────────────
section("🩺 System Health")
health = safe_get("/health")

if health:
    c1, c2, c3, c4 = st.columns(4)
    items = [
        ("server_status",   "running",   "🖥️",  "Server"),
        ("database_status", "connected", "🗄️",  "Database"),
        ("model_loaded",    True,        "🧠",  "AI Model"),
    ]
    cols = [c1, c2, c3]
    for col, (key, ok_val, icon, label) in zip(cols, items):
        val  = health.get(key)
        ok   = (val == ok_val) if isinstance(ok_val, str) else bool(val)
        cls  = "health-ok" if ok else "health-fail"
        txt  = ("ONLINE" if ok else "OFFLINE") if label != "AI Model" else ("LOADED" if ok else "NOT LOADED")
        col.markdown(f"""
        <div class="health-card {cls}">
            <div style='font-size:1.8rem'>{icon}</div>
            <div style='font-weight:700; font-size:1rem; margin:6px 0 2px'>{label}</div>
            <div style='font-size:0.8rem; color:{"#00e676" if ok else "#ff5252"}'>{txt}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        ts = health.get("timestamp", "—")
        st.markdown(f"""
        <div class="health-card">
            <div style='font-size:1.8rem'>🕐</div>
            <div style='font-weight:700; font-size:1rem; margin:6px 0 2px'>Last Updated</div>
            <div style='font-size:0.75rem; color:#7ab8e0; font-family:monospace'>{str(ts)[:19]}</div>
        </div>""", unsafe_allow_html=True)
else:
    st.error("⚠️ Backend not responding — start your FastAPI server.")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONVEYOR FLOW KPIs
# ─────────────────────────────────────────────
section("📊 Conveyor Flow Analytics")
flow = safe_get("/flow")

if flow:
    k1, k2, k3 = st.columns(3)
    kpis = [
        ("Belt Speed", round(flow.get("belt_speed", 0), 2), "m/s"),
        ("Material Area", round(flow.get("material_area", 0), 2), "m²"),
        ("Volumetric Flow", round(flow.get("volumetric_flow_m3_hr", 0), 2), "m³/hr"),
    ]
    for col, (label, val, unit) in zip([k1, k2, k3], kpis):
        col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{val}</div>
            <div style='color:#4a8aaa; font-size:0.7rem; font-family:monospace'>{unit}</div>
            <div class="kpi-label">{label}</div>
        </div>""", unsafe_allow_html=True)
else:
    st.warning("⚠️ Flow data unavailable")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# IMAGE DETECTION
# ─────────────────────────────────────────────
section("📷 Live Image Detection")

uploaded_file = st.file_uploader("Upload Conveyor Belt Image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    files = {"file": uploaded_file.getvalue()}
    data  = safe_post("/predict", files=files)

    if data is None:
        st.error("⚠️ Detection failed — backend not responding.")
    else:
        img_bytes = base64.b64decode(data["image"])
        img = Image.open(io.BytesIO(img_bytes))

        col1, col2 = st.columns([1.3, 1])

        with col1:
            st.image(img, caption="🤖 AI Detection Result", use_container_width=True)

        with col2:
            total = data.get("total_detections", 0)
            st.markdown(f"""
            <div class="kpi-card" style='margin-bottom:16px;'>
                <div class="kpi-value">{total}</div>
                <div class="kpi-label">Objects Detected</div>
            </div>""", unsafe_allow_html=True)

            alerts = data.get("alerts", [])
            if alerts:
                st.error("🚨 Alert: " + ", ".join(alerts))
            else:
                st.success("✅ No Foreign Objects Detected")

            # Quality
            if "quality" in data:
                quality = data["quality"]
                score   = quality.get("score", 0)
                status  = quality.get("status", "")

                st.markdown("**🧠 Quality Score**")
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=score,
                    number={"suffix": "%", "font": {"color": "#00b4ff", "size": 32}},
                    gauge={
                        "axis":  {"range": [0, 100], "tickcolor": "#3a6a8a"},
                        "bar":   {"color": "#00b4ff"},
                        "bgcolor": "#0a1828",
                        "steps": [
                            {"range": [0,   50], "color": "#1a0a0a"},
                            {"range": [50,  75], "color": "#1a1a0a"},
                            {"range": [75, 100], "color": "#0a1a0a"},
                        ],
                        "threshold": {"line": {"color": "#00e676", "width": 2}, "value": 75}
                    }
                ))
                fig.update_layout(
                    paper_bgcolor="#050a0f", font_color="#c0d8f0",
                    height=180, margin=dict(t=20, b=10, l=20, r=20)
                )
                st.plotly_chart(fig, use_container_width=True)

                badge = ("badge-good" if status=="GOOD" else "badge-warn" if status=="MODERATE" else "badge-danger")
                st.markdown(f'<span class="{badge}">● {status}</span>', unsafe_allow_html=True)

            # Granulometry
            if "granulometry" in data:
                st.markdown("<br>**🪨 Granulometry**", unsafe_allow_html=True)
                g = data["granulometry"]
                labels  = ["Fine", "Medium", "Oversize"]
                values  = [g.get("fine_percentage",0), g.get("medium_percentage",0), g.get("oversize_percentage",0)]
                colors  = ["#00b4ff", "#0066cc", "#003d80"]

                fig2 = go.Figure(go.Bar(
                    x=values, y=labels, orientation="h",
                    marker_color=colors,
                    text=[f"{v}%" for v in values],
                    textposition="auto",
                ))
                fig2.update_layout(
                    paper_bgcolor="#050a0f", plot_bgcolor="#0a1828",
                    font_color="#c0d8f0", height=160,
                    margin=dict(t=10, b=10, l=10, r=10),
                    xaxis=dict(range=[0,100], showgrid=False, tickcolor="#1a3a5c"),
                    yaxis=dict(showgrid=False),
                )
                st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DETECTION HISTORY + ANALYTICS
# ─────────────────────────────────────────────
section("📁 Detection History & Analytics")

history    = safe_get("/history")
detections = (history or {}).get("history", [])

if not history:
    st.error("⚠️ Backend not connected")
    st.stop()

if detections:
    df = pd.DataFrame(detections)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    # KPI row
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Records", len(df))
    if "confidence" in df.columns:
        m2.metric("Avg Confidence", f"{round(df['confidence'].mean()*100, 1)}%")
    if "label" in df.columns:
        m3.metric("Unique Classes", df["label"].nunique())

    st.markdown("<br>", unsafe_allow_html=True)

    ch1, ch2 = st.columns(2)

    # Bar chart – detection count
    with ch1:
        st.markdown("**Detection Count by Class**")
        if "label" in df.columns:
            vc = df["label"].value_counts().reset_index()
            vc.columns = ["Class", "Count"]
            fig3 = px.bar(vc, x="Class", y="Count",
                          color_discrete_sequence=["#00b4ff"],
                          template="plotly_dark")
            fig3.update_layout(
                paper_bgcolor="#050a0f", plot_bgcolor="#0a1828",
                font_color="#c0d8f0", height=280,
                margin=dict(t=10, b=30, l=10, r=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#1a3a5c"),
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No class data available")

    # Line chart – confidence trend
    with ch2:
        st.markdown("**Confidence Trend Over Time**")
        if "timestamp" in df.columns and "confidence" in df.columns:
            df_s = df.sort_values("timestamp")
            fig4 = px.line(df_s, x="timestamp", y="confidence",
                           color_discrete_sequence=["#00b4ff"],
                           template="plotly_dark")
            fig4.update_traces(line_width=2, fill="tozeroy",
                               fillcolor="rgba(0,180,255,0.08)")
            fig4.update_layout(
                paper_bgcolor="#050a0f", plot_bgcolor="#0a1828",
                font_color="#c0d8f0", height=280,
                margin=dict(t=10, b=30, l=10, r=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#1a3a5c", range=[0, 1]),
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No confidence data available")

    # Pie / donut – material composition
    if "label" in df.columns:
        st.markdown("**📊 Material Composition**")
        vc2 = df["label"].value_counts().reset_index()
        vc2.columns = ["Class", "Count"]
        fig5 = px.pie(vc2, names="Class", values="Count", hole=0.55,
                      color_discrete_sequence=px.colors.sequential.Blues_r,
                      template="plotly_dark")
        fig5.update_layout(
            paper_bgcolor="#050a0f", font_color="#c0d8f0",
            height=300, margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(bgcolor="#0a1828", bordercolor="#1a3a5c")
        )
        st.plotly_chart(fig5, use_container_width=True)

    # Full table
    st.markdown("**Full Detection Log**")
    st.dataframe(
        df.sort_values("timestamp", ascending=False).reset_index(drop=True),
        use_container_width=True,
        height=280
    )
else:
    st.info("No detections recorded yet.")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PLC CONTROL PANEL
# ─────────────────────────────────────────────
section("🏭 Conveyor Control Panel")
plc = safe_get("/plc_status")

if plc:
    p1, p2 = st.columns(2)
    with p1:
        running = plc.get("conveyor_running", False)
        cls     = "health-ok" if running else "health-fail"
        txt     = "RUNNING" if running else "STOPPED"
        col_    = "#00e676" if running else "#ff5252"
        st.markdown(f"""
        <div class="health-card {cls}" style='padding:24px;'>
            <div style='font-size:2rem'>🏗️</div>
            <div style='font-weight:700; font-size:1.1rem; margin:8px 0 4px'>Conveyor Belt</div>
            <div style='color:{col_}; font-size:1rem; font-weight:700'>● {txt}</div>
        </div>""", unsafe_allow_html=True)
    with p2:
        emergency = plc.get("emergency_triggered", False)
        cls2      = "health-fail" if emergency else "health-ok"
        txt2      = "⚠️ EMERGENCY STOP" if emergency else "✅ NORMAL"
        col2_     = "#ff5252" if emergency else "#00e676"
        st.markdown(f"""
        <div class="health-card {cls2}" style='padding:24px;'>
            <div style='font-size:2rem'>🛑</div>
            <div style='font-weight:700; font-size:1.1rem; margin:8px 0 4px'>Emergency Status</div>
            <div style='color:{col2_}; font-size:1rem; font-weight:700'>{txt2}</div>
        </div>""", unsafe_allow_html=True)

    if plc.get("emergency_triggered"):
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Reset Conveyor System"):
            requests.post(f"{BACKEND_URL}/reset_system")
            st.success("✅ System Reset Successful")
            st.rerun()
else:
    st.warning("⚠️ Unable to connect to PLC system")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<hr style='border-color:#1a3a5c; margin-top:32px;'>
<div style='text-align:center; color:#2a5a7a; font-size:0.78rem; font-family:monospace; padding:12px 0;'>
    ⚙️ DAKSHIYA AI PLATFORM · INTELLIGENT INDUSTRIAL MONITORING · v2.0
</div>
""", unsafe_allow_html=True)
  
