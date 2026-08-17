from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.agents.base import AgentContext
from app.agents.orchestrator import IntelligenceOrchestrator
from app.db.session import get_db
from app.schemas.domain import AgentRunRequest
from app.utils.logging import request_id_ctx

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/run")
async def run_agents(request: AgentRunRequest, db: Session = Depends(get_db)):
    state = await IntelligenceOrchestrator(db).run(
        AgentContext(
            request_id=request_id_ctx.get(),
            applicant_id=request.applicant_id,
            property_id=request.property_id,
            query=request.query,
            limit=request.limit,
        )
    )
    return state

