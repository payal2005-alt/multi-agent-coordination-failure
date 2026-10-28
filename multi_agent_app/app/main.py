from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from . import database as db
from .orchestrator import run_task
from .fault_injection import FAULTS

app = FastAPI(title="Multi-Agent Coordination Failure Lab", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
db.init_db()


class RunRequest(BaseModel):
    task: str = Field(min_length=5, max_length=500)
    live: bool = False                       # False = mock agents (no API keys needed)
    fault: str = "none"
    fault_rounds: int = Field(1, ge=0, le=3)
    max_rounds: int = Field(3, ge=1, le=5)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/faults")
def faults():
    return FAULTS


@app.post("/runs")
def create_run(req: RunRequest):
    if req.fault not in FAULTS:
        raise HTTPException(400, f"fault must be one of {FAULTS}")
    return run_task(req.task, req.live, req.fault, req.fault_rounds, req.max_rounds)


@app.get("/runs")
def runs():
    return db.list_runs()


@app.get("/runs/{run_id}")
def run(run_id: int):
    r = db.get_run(run_id)
    if not r:
        raise HTTPException(404, "run not found")
    return r


@app.get("/stats")
def stats():
    return db.stats()
