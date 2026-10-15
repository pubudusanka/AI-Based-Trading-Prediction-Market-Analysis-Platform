from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml_service")

app = FastAPI(
    title="AI Trading ML & Inference Service",
    version="1.0.0",
    description="Probabilistic trading signal predictions, feature extraction, and model evaluation"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    service: str
    active_model_version: Optional[str] = None

class PredictionRequest(BaseModel):
    symbol: str
    timeframe: str
    candles: List[Dict[str, Any]]

class PredictionResponse(BaseModel):
    symbol: str
    timeframe: str
    candle_time: str
    model_version: str
    probability_up: float
    probability_down: float
    probability_neutral: float
    predicted_class: str

@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        service="ai-trading-ml",
        active_model_version="xgb_v1_baseline"
    )

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    if not request.candles:
        raise HTTPException(status_code=400, detail="Candle data is required for inference")
    
    # Placeholder baseline logic until models are trained in subsequent phases
    last_candle = request.candles[-1]
    return PredictionResponse(
        symbol=request.symbol,
        timeframe=request.timeframe,
        candle_time=str(last_candle.get("open_time", "")),
        model_version="baseline_rule_engine",
        probability_up=0.33,
        probability_down=0.33,
        probability_neutral=0.34,
        predicted_class="NEUTRAL"
    )
