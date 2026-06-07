"""Ingestion service router."""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
from utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()
_status = {"running": False, "last_result": None}


class IngestRequest(BaseModel):
    data_path: Optional[str] = None


@router.post("/trigger")
async def trigger_ingestion(request: IngestRequest, background_tasks: BackgroundTasks):
    if _status["running"]:
        raise HTTPException(status_code=409, detail="Ingestion already running")
    def run():
        _status["running"] = True
        try:
            from services.ingestion.ingest import run_ingestion
            _status["last_result"] = run_ingestion(request.data_path)
        except Exception as e:
            _status["last_result"] = {"status": "error", "error": str(e)}
        finally:
            _status["running"] = False
    background_tasks.add_task(run)
    return {"status": "started", "message": "Ingestion running in background"}


@router.get("/status")
async def get_status():
    return _status
