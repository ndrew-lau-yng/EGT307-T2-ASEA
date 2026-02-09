from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PredictionInput(BaseModel):
    """
    Matches the columns used by training/train.py (with failure mode columns included).
    Extra keys are ignored to keep the API robust.
    """
    model_config = ConfigDict(extra="ignore")

    Type: str = Field(..., description="Product type category, e.g. 'L', 'M', 'H'")

    Air_temperature_K: float = Field(..., alias="Air temperature [K]")
    Process_temperature_K: float = Field(..., alias="Process temperature [K]")
    Rotational_speed_rpm: float = Field(..., alias="Rotational speed [rpm]")
    Torque_Nm: float = Field(..., alias="Torque [Nm]")
    Tool_wear_min: float = Field(..., alias="Tool wear [min]")

    TWF: int = 0
    HDF: int = 0
    PWF: int = 0
    OSF: int = 0
    RNF: int = 0


class PredictionRequest(BaseModel):
    """
    Allows either a single record or a batch of records.
    """
    model_config = ConfigDict(extra="ignore")
    records: List[PredictionInput]


class PredictionOutput(BaseModel):
    prediction: int
    prediction_label: str
    failure_probability: Optional[float] = None  # Probability of failure if it is applicable


class PredictionResponse(BaseModel):
    results: List[PredictionOutput]