import os
import streamlit as st
import requests

st.set_page_config(
    page_title="Predictive Maintenance Dashboard",
    layout="centered"
)

st.title("Predictive Maintenance Dashboard")
st.markdown("---")

st.subheader("Machine Inputs")

product_type = st.selectbox("Product Type", options=["L", "M", "H"])

air_temp = st.number_input("Air temperature (K)", value=300.0, step=0.1, format="%.1f")
process_temp = st.number_input("Process temperature (K)", value=310.0, step=0.1, format="%.1f")
rot_speed = st.number_input("Rotational speed (rpm)", value=1500, step=1)
torque = st.number_input("Torque (Nm)", value=40.0, step=0.1, format="%.1f")
tool_wear = st.number_input("Tool wear (min)", value=180, step=1)

st.markdown("---")

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8001/predict")

if st.button("Predict Failure Risk"):
    payload = {
        "Type": product_type,
        "air_temperature": air_temp,
        "process_temperature": process_temp,
        "rotational_speed": rot_speed,
        "torque": torque,
        "tool_wear": tool_wear,
    }

    try:
        resp = requests.post(GATEWAY_URL, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if "prediction_result" not in data:
            st.error("Unexpected response format from API gateway.")
            st.write(data)
        else:
            out = data["prediction_result"]
            pred_label = out.get("prediction_label", "unknown")
            prob = out.get("failure_probability", None)

            st.subheader("Prediction Result")

            if pred_label == "failure":
                st.metric("Prediction", "⚠️ failure")
            elif pred_label == "no_failure":
                st.metric("Prediction", "✅ no_failure")
            else:
                st.metric("Prediction", pred_label)

            if prob is not None:
                try:
                    st.write(f"**Failure probability:** {float(prob):.3f}")
                except Exception:
                    st.write(f"**Failure probability:** {prob}")

            with st.expander("Raw API Response"):
                st.json(data)

    except requests.exceptions.RequestException as e:
        st.error("Error connecting to API gateway.")
        st.code(str(e))

st.caption(f"Using gateway endpoint: {GATEWAY_URL}")