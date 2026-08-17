from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.agents.base import AgentContext
from app.agents.orchestrator import IntelligenceOrchestrator
from app.db.session import get_db
from app.intelligence.matching.engine import PropertyMatchingEngine
from app.schemas.domain import ApplicantRead, InteractionRead
from app.services.applicant_service import ApplicantService
from app.utils.logging import request_id_ctx

router = APIRouter(prefix="/applicants", tags=["applicants"])


@router.get("", response_model=list[ApplicantRead])
def list_applicants(limit: int = Query(50, ge=1, le=200), offset: int = 0, search: str | None = None, db: Session = Depends(get_db)):
    return ApplicantService(db).list(limit=limit, offset=offset, search=search)


@router.get("/{applicant_id}", response_model=ApplicantRead)
def get_applicant(applicant_id: str, db: Session = Depends(get_db)):
    applicant = ApplicantService(db).get(applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return applicant


@router.get("/{applicant_id}/timeline", response_model=list[InteractionRead])
def applicant_timeline(applicant_id: str, db: Session = Depends(get_db)):
    service = ApplicantService(db)
    if not service.get(applicant_id):
        raise HTTPException(status_code=404, detail="Applicant not found")
    return service.interactions(applicant_id, limit=100)


@router.get("/{applicant_id}/matches")
def applicant_matches(applicant_id: str, limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    applicant = ApplicantService(db).get(applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return PropertyMatchingEngine(db).match(applicant, limit)


@router.get("/{applicant_id}/recommendations")
async def applicant_recommendation_alias(applicant_id: str, db: Session = Depends(get_db)):
    if not ApplicantService(db).get(applicant_id):
        raise HTTPException(status_code=404, detail="Applicant not found")
    state = await IntelligenceOrchestrator(db).run(
        AgentContext(request_id=request_id_ctx.get(), applicant_id=applicant_id, query="Recommend the next best action")
    )
    return state.action_result


@router.get("/{applicant_id}/intelligence")
async def applicant_intelligence(applicant_id: str, limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    if not ApplicantService(db).get(applicant_id):
        raise HTTPException(status_code=404, detail="Applicant not found")
    state = await IntelligenceOrchestrator(db).run(
        AgentContext(
            request_id=request_id_ctx.get(),
            applicant_id=applicant_id,
            query="Why is this applicant a strong candidate and what should the agent do next?",
            limit=limit,
        )
    )
    return state.final_response
