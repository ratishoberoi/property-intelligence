from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.agents.base import AgentContext
from app.agents.orchestrator import IntelligenceOrchestrator
from app.db.session import get_db
from app.services.applicant_service import ApplicantService
from app.utils.logging import request_id_ctx

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/applicants/{applicant_id}")
async def applicant_recommendations(applicant_id: str, db: Session = Depends(get_db)):
    if not ApplicantService(db).get(applicant_id):
        raise HTTPException(status_code=404, detail="Applicant not found")
    state = await IntelligenceOrchestrator(db).run(
        AgentContext(request_id=request_id_ctx.get(), applicant_id=applicant_id, query="Recommend the next best action")
    )
    return state.action_result

