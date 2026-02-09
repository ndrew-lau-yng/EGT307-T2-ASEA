from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .schemas import PredictionRequest, PredictionResponse, PredictionOutput
from .predict import load_model, predict, EXPECTED_COLUMNS


def create_app() -> FastAPI:
    app = FastAPI(title="Predictive Maintenance Inference API", version="1.0.0")

    model_path = Path(__file__).resolve().parents[1] / "model" / "model.joblib"
    model = {"obj": None, "error": None}

    @app.on_event("startup")
    def _startup():
        try:
            model["obj"] = load_model(model_path)
        except Exception as e:
            model["error"] = str(e)

    @app.get("/health")
    def health():
        if model["obj"] is None:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "model_loaded": False,
                    "error": model["error"] or "Model not loaded",
                    "expected_features": EXPECTED_COLUMNS,
                },
            )
        return {
            "status": "ok",
            "model_loaded": True,
            "expected_features": EXPECTED_COLUMNS,
        }

    @app.post("/predict", response_model=PredictionResponse)
    def predict_endpoint(req: PredictionRequest):
        if model["obj"] is None:
            raise HTTPException(status_code=503, detail=f"Model not loaded: {model['error']}")

        # Convert Pydantic models into dicts using the original dataset column names
        records = [r.model_dump(by_alias=True) for r in req.records]

        try:
            preds, probs = predict(model["obj"], records)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        results = []
        for i, p in enumerate(preds):
            results.append(
                PredictionOutput(
                    prediction=int(p),
                    prediction_label="failure" if int(p) == 1 else "no_failure",
                    failure_probability=(float(probs[i]) if probs is not None else None),
                )
            )

        return PredictionResponse(results=results)

    return app


app = create_app()