from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import time

import psycopg2
from psycopg2.extras import Json


app = FastAPI(title="API Gateway Service", version="1.0.0")

INFERENCE_URL = os.getenv("INFERENCE_URL", "http://localhost:8000/predict")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "egtdb")
DB_USER = os.getenv("DB_USER", "egtdb")
DB_PASSWORD = os.getenv("DB_PASSWORD", "egtdb")

origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SensorData(BaseModel):
    Type: str
    air_temperature: float
    process_temperature: float
    rotational_speed: float
    torque: float
    tool_wear: float


def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def log_prediction_to_db(input_data: dict, prediction_data: dict) -> None:
    conn = get_db_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO predictions (input_json, prediction_json)
                    VALUES (%s, %s)
                    """,
                    (Json(input_data), Json(prediction_data)),
                )
    finally:
        conn.close()


def log_request_to_db(route: str, status_code: int, latency_ms: int) -> None:
    conn = get_db_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO request_log (route, status_code, latency_ms)
                    VALUES (%s, %s, %s)
                    """,
                    (route, status_code, latency_ms),
                )
    finally:
        conn.close()


@app.get("/health")
def health():
    try:
        conn = get_db_conn()
        conn.close()
        db_ok = True
        db_error = None
    except Exception as e:
        db_ok = False
        db_error = str(e)

    return {
        "status": "ok",
        "inference_url": INFERENCE_URL,
        "db_host": DB_HOST,
        "db_ok": db_ok,
        "db_error": db_error,
    }


@app.post("/predict")
def predict(data: SensorData, request: Request):
    start = time.time()

    inference_payload = {
        "records": [
            {
                "Type": data.Type,
                "Air temperature [K]": data.air_temperature,
                "Process temperature [K]": data.process_temperature,
                "Rotational speed [rpm]": data.rotational_speed,
                "Torque [Nm]": data.torque,
                "Tool wear [min]": data.tool_wear,
            }
        ]
    }

    # 1) Call Inference Service
    try:
        res = requests.post(INFERENCE_URL, json=inference_payload, timeout=8)

        if not res.ok:
            latency_ms = int((time.time() - start) * 1000)
            try:
                log_request_to_db(str(request.url.path), res.status_code, latency_ms)
            except Exception:
                pass

            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Inference returned an error",
                    "inference_status": res.status_code,
                    "inference_body": res.text,
                    "sent_payload": inference_payload,
                },
            )

        prediction_result = res.json()

    except requests.RequestException as e:
        latency_ms = int((time.time() - start) * 1000)
        try:
            log_request_to_db(str(request.url.path), 502, latency_ms)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=f"Inference service request failed: {str(e)}")

    # 2) Extract the results
    try:
        pred_out = prediction_result["results"][0]
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Inference response format invalid",
                "inference_response": prediction_result,
            },
        )

    # 3) Log into DB
    try:
        log_prediction_to_db(inference_payload["records"][0], pred_out)
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        try:
            log_request_to_db(str(request.url.path), 500, latency_ms)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Database insert failed: {str(e)}")

    # 4) Log request metadata
    latency_ms = int((time.time() - start) * 1000)
    try:
        log_request_to_db(str(request.url.path), 200, latency_ms)
    except Exception:
        pass

    return {"prediction_result": pred_out}