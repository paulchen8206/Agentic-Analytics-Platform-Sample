"""
FastAPI backend for the Agentic Analytics Platform.
Provides REST + streaming endpoints for data ingestion and AI analysis.
"""

import asyncio
import json
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agents.analytics_agent import AnalyticsAgent
from backend.data.loader import DataLoader
from backend.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Agentic Analytics Platform",
    description="Turn your data into insights with agentic AI powered by Ollama",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

loader = DataLoader()


# ------------------------------------------------------------------
# Request / Response Models
# ------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    dataset_id: str | None = None
    history: list[dict] | None = None
    model: str = "llama3.2"


class QuickAnalyzeRequest(BaseModel):
    dataset_id: str
    model: str = "llama3.2"


# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Agentic Analytics Platform"}


# ------------------------------------------------------------------
# Datasets
# ------------------------------------------------------------------

@app.get("/api/datasets")
async def list_datasets():
    return {"datasets": loader.list_datasets()}


@app.post("/api/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    allowed = {".csv", ".json", ".parquet", ".xlsx", ".xls"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'")

    content = await file.read()
    if len(content) > 100 * 1024 * 1024:  # 100 MB cap
        raise HTTPException(status_code=413, detail="File too large (max 100 MB)")

    try:
        dataset_id, df = loader.load_from_bytes(content, file.filename)
        return {
            "dataset_id": dataset_id,
            "filename": file.filename,
            "rows": len(df),
            "columns": list(df.columns),
        }
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/datasets/{dataset_id}/preview")
async def preview_dataset(dataset_id: str, rows: int = 20):
    try:
        df = loader.load(dataset_id)
        return {
            "dataset_id": dataset_id,
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "preview": df.head(rows).to_dict(orient="records"),
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# Chat / Agentic Analysis — Streaming
# ------------------------------------------------------------------

@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    agent = AnalyticsAgent(model=req.model)

    async def event_generator() -> AsyncGenerator[str, None]:
        loop = asyncio.get_event_loop()

        def run_agent():
            return list(agent.chat(
                user_message=req.message,
                dataset_id=req.dataset_id,
                history=req.history,
            ))

        events = await loop.run_in_executor(None, run_agent)
        for event in events:
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/chat")
async def chat(req: ChatRequest):
    agent = AnalyticsAgent(model=req.model)
    events = list(agent.chat(
        user_message=req.message,
        dataset_id=req.dataset_id,
        history=req.history,
    ))
    answer_events = [e for e in events if e["type"] == "answer"]
    return {
        "answer": answer_events[-1]["content"] if answer_events else "",
        "events": events,
    }


# ------------------------------------------------------------------
# Quick Analyze
# ------------------------------------------------------------------

@app.post("/api/analyze/quick")
async def quick_analyze(req: QuickAnalyzeRequest):
    agent = AnalyticsAgent(model=req.model)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, agent.quick_analyze, req.dataset_id)
    return result


# ------------------------------------------------------------------
# Direct Analytics Endpoints (bypass LLM for speed)
# ------------------------------------------------------------------

@app.get("/api/analytics/{dataset_id}/describe")
async def describe(dataset_id: str):
    from backend.analytics.engine import AnalyticsEngine
    engine = AnalyticsEngine()
    try:
        df = loader.load(dataset_id)
        return engine.describe(df)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")


@app.get("/api/analytics/{dataset_id}/anomalies/{column}")
async def anomalies(dataset_id: str, column: str):
    from backend.analytics.engine import AnalyticsEngine
    engine = AnalyticsEngine()
    try:
        df = loader.load(dataset_id)
        return engine.detect_anomalies(df, column)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")


@app.get("/api/analytics/{dataset_id}/trend/{column}")
async def trend(dataset_id: str, column: str, time_col: str):
    from backend.analytics.engine import AnalyticsEngine
    engine = AnalyticsEngine()
    try:
        df = loader.load(dataset_id)
        return engine.trend_analysis(df, column, time_col)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")


@app.get("/api/analytics/{dataset_id}/correlate")
async def correlate(dataset_id: str, col_a: str, col_b: str):
    from backend.analytics.engine import AnalyticsEngine
    engine = AnalyticsEngine()
    try:
        df = loader.load(dataset_id)
        return engine.correlate(df, col_a, col_b)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")


@app.get("/api/analytics/{dataset_id}/segment/{column}")
async def segment(dataset_id: str, column: str):
    from backend.analytics.engine import AnalyticsEngine
    engine = AnalyticsEngine()
    try:
        df = loader.load(dataset_id)
        return engine.segment(df, column)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")


@app.get("/api/analytics/{dataset_id}/forecast/{column}")
async def forecast(dataset_id: str, column: str, time_col: str, periods: int = 7):
    from backend.analytics.engine import AnalyticsEngine
    engine = AnalyticsEngine()
    try:
        df = loader.load(dataset_id)
        return engine.forecast(df, column, time_col, periods)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
