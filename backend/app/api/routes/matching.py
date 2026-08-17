from copy import copy
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.intelligence.matching.engine import PropertyMatchingEngine
from app.schemas.domain import ClientMatchRequest, MatchRequest
from app.services.applicant_service import ApplicantService

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("")
def post_matching(request: MatchRequest, db: Session = Depends(get_db)):
    applicant = ApplicantService(db).get(request.applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return PropertyMatchingEngine(db).match(applicant, request.limit)


@router.post("/client")
def post_client_matching(request: ClientMatchRequest, db: Session = Depends(get_db)):
    applicant = ApplicantService(db).get(request.applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    preference_profile = copy(applicant)
    preference_profile.budget_max = request.budget_max
    preference_profile.preferred_areas = request.preferred_areas.replace(",", "|")
    preference_profile.bedrooms_required = request.bedrooms_required
    preference_profile.amenities_preferences = request.amenities_preferences.replace(",", "|")
    preference_profile.move_in_date = request.move_in_date
    return PropertyMatchingEngine(db).match(preference_profile, request.limit)


@router.get("/applicants/{applicant_id}/matches")
def get_applicant_matches(applicant_id: str, limit: int = 10, db: Session = Depends(get_db)):
    applicant = ApplicantService(db).get(applicant_id)
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return PropertyMatchingEngine(db).match(applicant, limit)
