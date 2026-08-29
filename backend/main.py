import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.models.domain import AskRequest, AskResponse, Watch
from backend.repositories import MemoryRepository
from backend.services.pipeline import Pipeline

logging.basicConfig(level=logging.INFO, format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}')
app = FastAPI(title="Fynura", version="0.1.0", description="Near-real-time, traceable public-health intelligence")
repo = MemoryRepository(); pipeline = Pipeline(repo)
ROOT = Path(__file__).resolve().parents[1]
app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")

@app.get("/", include_in_schema=False)
def home(): return FileResponse(ROOT / "frontend" / "index.html")

@app.get("/health")
def health(): return {"status": "ok", "service": "fynura", "cloud_project": "fynura-public-health"}

@app.get("/api/threats")
def threats():
    return [{"id": x, "name": x.title(), "supported": True, "assessment": repo.latest_assessment(x)} for x in ("measles", "ebola", "cholera")]

@app.post("/api/threats/{threat_id}/assess")
async def assess(threat_id: str):
    if threat_id not in {"measles", "cholera"}: raise HTTPException(501, "Ebola is registered for the next live-source expansion phase.")
    try: return await (pipeline.assess_measles() if threat_id == "measles" else pipeline.assess_cholera())
    except Exception as exc: raise HTTPException(502, str(exc)) from exc

@app.get("/api/threats/{threat_id}/assessments/latest")
def latest(threat_id: str):
    item = repo.latest_assessment(threat_id)
    if not item: raise HTTPException(404, "No assessment has been generated in this process yet.")
    return item

@app.get("/api/assessments/{assessment_id}/evidence")
def evidence(assessment_id: str):
    item = repo.get_assessment(assessment_id)
    if not item: raise HTTPException(404, "Assessment not found")
    return {"observations": item.observations, "evidence_groups": item.evidence_groups, "claims": item.claims}

@app.post("/api/ask", response_model=AskResponse)
def ask(request: AskRequest):
    if not request.threat_id: return AskResponse(answer="Choose a threat so I can retrieve its structured evidence.", evidence_ids=[], declined=True)
    item = repo.latest_assessment(request.threat_id)
    if not item: return AskResponse(answer="Fynura has no stored assessment for that threat yet. Refresh its evidence first.", evidence_ids=[], declined=True)
    q = request.question.lower()
    if any(word in q for word in ("case", "changed", "latest", "source", "confidence")):
        refs = sorted({eid for claim in item.claims for eid in claim.evidence_ids})
        return AskResponse(answer=f"{item.summary} Evidence confidence is {item.evidence_confidence:.0%}. {item.claims[0].text}", evidence_ids=refs)
    return AskResponse(answer="The structured evidence currently stored does not support a reliable answer to that question.", evidence_ids=[], declined=True)

@app.post("/api/watches", response_model=Watch)
def create_watch(watch: Watch): return repo.save_watch(watch)

@app.get("/api/watches")
def watches(): return list(repo.watches.values())

@app.delete("/api/watches/{watch_id}")
def delete_watch(watch_id: str):
    if watch_id not in repo.watches: raise HTTPException(404, "Watch not found")
    repo.watches[watch_id].active = False
    return repo.watches[watch_id]
