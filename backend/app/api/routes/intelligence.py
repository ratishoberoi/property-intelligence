from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.agents.base import AgentContext
from app.agents.orchestrator import IntelligenceOrchestrator
from app.db.session import get_db
from app.schemas.domain import AnalyzeRequest
from app.services.applicant_service import ApplicantService
from app.utils.logging import request_id_ctx

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.post("/analyze")
async def analyze(request: AnalyzeRequest, db: Session = Depends(get_db)):
    if not ApplicantService(db).get(request.applicant_id):
        raise HTTPException(status_code=404, detail="Applicant not found")
    state = await IntelligenceOrchestrator(db).run(
        AgentContext(
            request_id=request_id_ctx.get(),
            applicant_id=request.applicant_id,
            property_id=request.property_id,
            query="Explain the recommendation using applicant, property, viewing and conversation evidence.",
        )
    )
    return state.final_response

