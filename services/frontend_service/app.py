import streamlit as st
import requests

# ----- Page Setup -----
st.set_page_config(
    page_title="Predictive Maintenance Dashboard",
    layout="centered"
)

st.title("Predictive Maintenance Dashboard")
st.markdown("---")

# ----- User Inputs -----
st.subheader("Machine Inputs")

product_type = st.selectbox(
    "Product Type", 
    options=["L", "M", "H"]
)

air_temp = st.number_input("Air Temp (K)", value=300.0, step=0.1)
process_temp = st.number_input("Process Temp (K)", value=310.0, step=0.1)
rot_speed = st.number_input("Rotational Speed (rpm)", value=1500, step=1)
torque = st.number_input("Torque (Nm)", value=40.0, step=0.1)
tool_wear = st.number_input("Tool Wear (min)", value=180, step=1)

# ----- API Call -----
INFERENCE_URL = "http://inference-service:8000/predict"

if st.button("Predict Failure Risk"):
    payload = {
        "product_type": product_type,
        "air_temp": air_temp,
        "process_temp": process_temp,
        "rotational_speed": rot_speed,
        "torque": torque,
        "tool_wear": tool_wear
    }

    try:
        response = requests.post(INFERENCE_URL, json=payload, timeout=5)
        response.raise_for_status()
        result = response.json()
        
        # ----- Display Results -----
        st.markdown("---")
        status = result.get("machine_status", "UNKNOWN")
        failure_mode = result.get("predicted_failure", "N/A")
        confidence = result.get("confidence", 0)

        # Use emoji for visual alert
        if status.lower() in ["at risk", "failure"]:
            emoji = "⚠️"
        else:
            emoji = "✅"

        st.metric("Machine Status", f"{emoji} {status}")
        st.write(f"**Predicted Failure:** {failure_mode}")
        st.write(f"**Confidence:** {confidence}%")
        st.markdown("---")

    except requests.exceptions.RequestException as e:
        st.error("Error connecting to inference service.")
        st.code(str(e))
