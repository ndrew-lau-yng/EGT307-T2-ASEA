from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

#Creating FastAPI app
app = FastAPI(title="API Gateway Service")

# URLs change depending on the environment
INFERENCE_URL = os.getenv("INFERENCE_URL", "http://localhost:8000/predict")
DATABASE_URL = os.getenv("DATABASE_URL", "http://localhost:8002/store")

origins = [
    "http://localhost:8501",   # placeholder: dashboard URL
    "http://127.0.0.1:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Input data model from frontend
class SensorData(BaseModel):
    Type: str
    air_temperature: float
    process_temperature: float
    rotational_speed: float
    torque: float
    tool_wear: float

@app.get("/")
def root():
    return {"message": "API Gateway is running"}

#Predict endpoint
@app.post("/predict")
def predict(data: SensorData):

    #Converting frontend data to model input format
    inference_payload = {
        "records": [
            {
                "Type": data.Type,
                "Air temperature [K]": data.air_temperature,
                "Process temperature [K]": data.process_temperature,
                "Rotational speed [rpm]": data.rotational_speed,
                "Torque [Nm]": data.torque,
                "Tool wear [min]": data.tool_wear,
                "TWF": 0,
                "HDF": 0,
                "PWF": 0,
                "OSF": 0,
                "RNF": 0
            }
        ]
    }

    #Calling Inference Service (call in service)
    try:
        res = requests.post(INFERENCE_URL, json=inference_payload, timeout=5)
        res.raise_for_status()
        prediction_result = res.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference service error: {e}")

    #Send result to Database Service (need to call in service)
    db_payload = {
        "input_data": inference_payload["records"][0],
        "prediction": prediction_result["results"][0]
    }

    try:
        requests.post(DATABASE_URL, json=db_payload, timeout=5)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database service error: {e}")

    #Return prediction to frontend dashboard
    return {
        "prediction_result": prediction_result["results"][0]
    }
