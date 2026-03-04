import streamlit as st
import requests
import pandas as pd
import base64
from PIL import Image
import io
import time

BACKEND_URL = "http://127.0.0.1:8000"

# ----------------------------
# SAFE REQUEST FUNCTION
# ----------------------------
def safe_get(endpoint):
    try:
        response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
        return response.json()
    except:
        return None

def safe_post(endpoint, files=None):
    try:
        response = requests.post(f"{BACKEND_URL}{endpoint}", files=files, timeout=10)
        return response.json()
    except:
        return None


st.set_page_config(page_title="iMGS Dashboard", layout="wide")

st.title("Dakshiya.ai")
st.write("AI-based Industrial Monitoring Dashboard")
# ----------------------------
# AUTO REFRESH
# ----------------------------
refresh = st.toggle("Enable Live Monitoring")

if refresh:
    st.caption("🔄 Auto-refreshing every 5 seconds")
    time.sleep(5)
    st.rerun()

# ----------------------------
# IMAGE DETECTION
# ----------------------------
st.header("📷 Live Image Detection")

uploaded_file = st.file_uploader(
    "Upload Conveyor Belt Image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:

    files = {"file": uploaded_file.getvalue()}
    data = safe_post("/predict", files=files)

    if data is None:
        st.error("⚠ Detection failed. Backend not responding.")
    else:
        img_bytes = base64.b64decode(data["image"])
        img = Image.open(io.BytesIO(img_bytes))

        col1, col2 = st.columns([1.2, 1])

        # LEFT SIDE - IMAGE
        with col1:
            st.image(img, caption="AI Detection Result", width="stretch")

        # RIGHT SIDE - ANALYTICS
        with col2:

            st.subheader("📊 Detection Summary")

            st.metric("Total Objects", data.get("total_detections", 0))

            alerts = data.get("alerts", [])
            if alerts:
                st.error("🚨 " + ", ".join(alerts))
            else:
                st.success("✅ No Foreign Objects")

            st.divider()

            # ----------------------------
            # QUALITY SECTION
            # ----------------------------
            if "quality" in data:
                quality = data["quality"]

                st.subheader("🧠 Quality Score")
                st.metric("Score", f"{quality.get('score', 0)} %")

                status = quality.get("status", "")

                if status == "GOOD":
                    st.success("🟢 Status: GOOD")
                elif status == "MODERATE":
                    st.warning("🟡 Status: MODERATE")
                else:
                    st.error("🔴 Status: POOR")

            st.divider()

            # ----------------------------
            # GRANULOMETRY SECTION
            # ----------------------------
            if "granulometry" in data:
                st.subheader("🪨 Granulometry")

                g = data["granulometry"]

                st.write(f"Fine: {g.get('fine_percentage',0)}%")
                st.progress(g.get("fine_percentage",0) / 100)

                st.write(f"Medium: {g.get('medium_percentage',0)}%")
                st.progress(g.get("medium_percentage",0) / 100)

                st.write(f"Oversize: {g.get('oversize_percentage',0)}%")
                st.progress(g.get("oversize_percentage",0) / 100)

# ----------------------------
# HISTORY
# ----------------------------
st.header("📁 Detection History")

history = safe_get("/history")

if history is None:
    st.error("⚠ Backend not connected")
    st.stop()

detections = history.get("history", [])

if len(detections) > 0:

    df = pd.DataFrame(detections)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    st.metric("Total Records", len(df))

    col1, col2 = st.columns(2)

    # Detection Count Chart
    with col1:
        st.subheader("Detection Count by Class")
        if "label" in df.columns:
            st.bar_chart(df["label"].value_counts())
        else:
            st.info("No class data available")

    # Confidence Trend
    with col2:
        st.subheader("Confidence Trend")

        if "timestamp" in df.columns and "confidence" in df.columns:
            df_sorted = df.sort_values("timestamp")
            st.line_chart(df_sorted.set_index("timestamp")["confidence"])
        else:
            st.info("No confidence data available")

    st.subheader("Full Detection Table")
    st.dataframe(
        df.sort_values("timestamp", ascending=False),
        width="stretch"
    )

else:
    st.info("No detections yet.")

# -----------------------------------
# QUALITY TREND ANALYTICS
# -----------------------------------
st.header("📊 Quality Trend Analytics")

# Get detection history
history = safe_get("/history")

if history:

    detections = history.get("history", [])

    if len(detections) > 0:

        df_trend = pd.DataFrame(detections)

        # Convert timestamp
        if "timestamp" in df_trend.columns:
            df_trend["timestamp"] = pd.to_datetime(df_trend["timestamp"])

        # KPI Metrics
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Records", len(df_trend))

        with col2:
            if "confidence" in df_trend.columns:
                avg_conf = round(df_trend["confidence"].mean(), 2)
                st.metric("Average Confidence", avg_conf)

        # Trend Chart
        if "timestamp" in df_trend.columns and "confidence" in df_trend.columns:

            df_trend = df_trend.sort_values("timestamp")

            st.subheader("📈 Detection Confidence Over Time")

            st.line_chart(
                df_trend.set_index("timestamp")["confidence"]
            )

    else:
        st.info("No detection data available")

else:
    st.warning("⚠ Unable to fetch analytics data")

    st.subheader("📊 Material Composition")

if detections:

    df = pd.DataFrame(detections)

    if "label" in df.columns:
        st.bar_chart(df["label"].value_counts())

# -----------------------------------
# SYSTEM HEALTH
# -----------------------------------
st.header("🩺 System Health")

health = safe_get("/health")

if health is None:
    st.error("⚠ Backend not responding")

else:
    col1, col2, col3 = st.columns(3)

    # Server Status
    with col1:
        if health.get("server_status") == "running":
            st.success("🟢 Server Running")
        else:
            st.error("🔴 Server Down")

    # Database Status
    with col2:
        if health.get("database_status") == "connected":
            st.success("🟢 Database Connected")
        else:
            st.error("🔴 Database Issue")

    # AI Model Status
    with col3:
        if health.get("model_loaded"):
            st.success("🧠 AI Model Loaded")
        else:
            st.error("⚠ Model Not Loaded")

    st.caption(f"Last Updated: {health.get('timestamp')}")

# -----------------------------------
# LIVE CONVEYOR MONITORING
# -----------------------------------
st.header("🎥 Live Conveyor Monitoring")

st.info("Live camera unavailable in Docker environment. Using AI image detection feed.")

uploaded = st.file_uploader("Upload Conveyor Image", type=["jpg","png","jpeg"])

if uploaded:
    files = {"file": uploaded.getvalue()}
    response = requests.post(f"{BACKEND_URL}/predict", files=files)

    data = response.json()

    img_bytes = base64.b64decode(data["image"])
    img = Image.open(io.BytesIO(img_bytes))

    st.image(img, caption="AI Conveyor Monitoring", width="stretch")

# -----------------------------------
# LIVE FLOW ANALYTICS
# -----------------------------------
st.header("📊 Conveyor Flow Analytics")

flow = safe_get("/flow")

if flow:

    col1, col2, col3 = st.columns(3)

    col1.metric("Belt Speed (m/s)", round(flow["belt_speed"], 2))
    col2.metric("Material Area", round(flow["material_area"], 2))
    col3.metric("Volumetric Flow (m³/hr)", round(flow["volumetric_flow_m3_hr"], 2))

else:
    st.warning("Unable to fetch flow data")
# ----------------------------
# PLC CONTROL PANEL
# ----------------------------
st.header("🏭 Conveyor Control Panel")

plc = safe_get("/plc_status")

if plc:

    col1, col2 = st.columns(2)

    # Conveyor Status
    with col1:
        if plc["conveyor_running"]:
            st.success("🟢 Conveyor Status: RUNNING")
        else:
            st.error("🔴 Conveyor Status: STOPPED")

    # Emergency Status
    with col2:
        if plc["emergency_triggered"]:
            st.error("🚨 EMERGENCY STOP ACTIVATED")
        else:
            st.success("✅ System Normal")

    # Reset Button
    if plc["emergency_triggered"]:
        if st.button("🔄 Reset Conveyor System"):
            requests.post(f"{BACKEND_URL}/reset_system")
            st.success("System Reset Successful")
            st.rerun()

else:
    st.warning("⚠ Unable to connect to PLC system")

  