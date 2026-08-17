from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import ActivityEvent, Applicant, Application, ClientPreference, Conversation, Interaction, Property, SavedProperty, ViewingRequest
from app.db.session import get_db
from app.rag.answer import GroundedAnswerGenerator
from app.rag.retrieval import RetrievalService
from app.schemas.domain import ApplicationCreate, ClientPreferenceRequest, ClientQuestionRequest, SavePropertyRequest, ViewingRequestCreate, WorkflowStatusUpdate

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.get("/client/{applicant_id}")
def client_state(applicant_id: str, db: Session = Depends(get_db)):
    applicant = _client_applicant(db, applicant_id)
    return {"applicant": applicant, "preferences": _latest(db, ClientPreference, applicant_id, "created_at"), "saved_properties": _properties(db, SavedProperty, applicant_id), "viewing_requests": _requests(db, applicant_id), "applications": _applications(db, applicant_id, include_internal=False), "activity": _activity(db, applicant_id)}


@router.post("/preferences")
def save_preferences(request: ClientPreferenceRequest, db: Session = Depends(get_db)):
    applicant_id = request.applicant_id
    _client_applicant(db, applicant_id)
    preference = ClientPreference(applicant_id=applicant_id, budget_max=request.budget_max, preferred_areas=request.preferred_areas, bedrooms_required=request.bedrooms_required, move_in_date=request.move_in_date, amenities_preferences=request.amenities_preferences)
    db.add(preference)
    _event(db, applicant_id, None, "PREFERENCES_SUBMITTED", "Client submitted property preferences.")
    db.commit()
    return _preference(preference)


@router.post("/saved")
def save_property(request: SavePropertyRequest, db: Session = Depends(get_db)):
    _client_applicant(db, request.applicant_id)
    _property(db, request.property_id)
    existing = db.scalar(select(SavedProperty).where(SavedProperty.applicant_id == request.applicant_id, SavedProperty.property_id == request.property_id))
    should_save = request.saved if request.saved is not None else existing is None
    if existing and not should_save:
        db.delete(existing)
        action = "removed"
    elif not existing and should_save:
        db.add(SavedProperty(applicant_id=request.applicant_id, property_id=request.property_id))
        _event(db, request.applicant_id, request.property_id, "PROPERTY_SAVED", f"Client saved {request.property_id}.")
        action = "saved"
    else:
        action = "saved" if existing else "removed"
    db.commit()
    return {"status": action, "property_id": request.property_id}


@router.post("/viewings")
def create_viewing(request: ViewingRequestCreate, db: Session = Depends(get_db)):
    _client_applicant(db, request.applicant_id)
    _property(db, request.property_id)
    pending = db.scalar(select(ViewingRequest).where(ViewingRequest.applicant_id == request.applicant_id, ViewingRequest.property_id == request.property_id, ViewingRequest.status.in_(["PENDING", "TIME_PROPOSED", "CONFIRMED"])))
    if pending:
        return _viewing(pending, db)
    viewing = ViewingRequest(applicant_id=request.applicant_id, property_id=request.property_id, preferred_at=request.preferred_at, client_message=request.client_message, status="PENDING")
    db.add(viewing)
    _event(db, request.applicant_id, request.property_id, "VIEWING_REQUESTED", f"Client requested a viewing for {request.property_id}.")
    db.commit()
    db.refresh(viewing)
    return _viewing(viewing, db)


@router.get("/viewings")
def list_viewings(applicant_id: str | None = None, db: Session = Depends(get_db)):
    stmt = select(ViewingRequest).order_by(ViewingRequest.created_at.desc())
    if applicant_id:
        stmt = stmt.where(ViewingRequest.applicant_id == applicant_id)
    return [_viewing(row, db) for row in db.scalars(stmt)]


@router.patch("/viewings/{request_id}")
def update_viewing(request_id: str, request: WorkflowStatusUpdate, db: Session = Depends(get_db)):
    row = db.get(ViewingRequest, request_id)
    if not row:
        raise HTTPException(status_code=404, detail="Viewing request not found")
    allowed = {"PENDING", "CONFIRMED", "TIME_PROPOSED", "DECLINED"}
    if request.status not in allowed:
        raise HTTPException(status_code=422, detail="Unsupported viewing status")
    row.status = request.status
    row.agency_note = request.note
    row.proposed_at = request.proposed_at if request.status == "TIME_PROPOSED" else row.proposed_at
    if request.status == "CONFIRMED":
        row.confirmed_at = datetime.utcnow()
        row.confirmed_by = "Demo agency team"
    _event(db, row.applicant_id, row.property_id, f"VIEWING_{request.status}", f"Agency updated viewing request to {request.status.replace('_', ' ').lower()}.")
    db.commit()
    return _viewing(row, db)


@router.post("/applications")
def create_application(request: ApplicationCreate, db: Session = Depends(get_db)):
    _client_applicant(db, request.applicant_id)
    _property(db, request.property_id)
    existing = db.scalar(select(Application).where(Application.applicant_id == request.applicant_id, Application.property_id == request.property_id, Application.status.not_in(["DECLINED"])))
    if existing:
        return _application(existing, db)
    row = Application(applicant_id=request.applicant_id, property_id=request.property_id, status="SUBMITTED", client_message=request.client_message)
    db.add(row)
    _event(db, request.applicant_id, request.property_id, "APPLICATION_SUBMITTED", f"Application submitted for {request.property_id}.")
    db.commit()
    db.refresh(row)
    return _application(row, db)


@router.get("/applications")
def list_applications(applicant_id: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Application).order_by(Application.updated_at.desc())
    if applicant_id:
        stmt = stmt.where(Application.applicant_id == applicant_id)
    return [_application(row, db, include_internal=applicant_id is None) for row in db.scalars(stmt)]


@router.patch("/applications/{application_id}")
def update_application(application_id: str, request: WorkflowStatusUpdate, db: Session = Depends(get_db)):
    row = db.get(Application, application_id)
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    if request.status not in {"STARTED", "SUBMITTED", "UNDER_REVIEW", "APPROVED", "DECLINED"}:
        raise HTTPException(status_code=422, detail="Unsupported application status")
    row.status = request.status
    row.agency_note = request.note
    _event(db, row.applicant_id, row.property_id, f"APPLICATION_{request.status}", f"Agency updated application to {request.status.replace('_', ' ').lower()}.")
    db.commit()
    return _application(row, db)


@router.post("/questions")
def client_question(request: ClientQuestionRequest, db: Session = Depends(get_db)):
    applicant = _client_applicant(db, request.applicant_id)
    _property(db, request.property_id)
    conversation = Conversation(conversation_id=f"CLIENT-{uuid4().hex[:12].upper()}", applicant_id=request.applicant_id, property_id=request.property_id, timestamp=datetime.utcnow(), direction="inbound", channel="client_portal", subject="Client property question", body=request.question, sentiment=0.0)
    db.add(conversation)
    _event(db, request.applicant_id, request.property_id, "PROPERTY_QUESTION", f"{applicant.name} asked: {request.question}")
    db.commit()
    citations = RetrievalService(db).query(request.question, limit=5, applicant_id=request.applicant_id, property_id=request.property_id)
    grounded = GroundedAnswerGenerator().generate(request.question, "", citations, [])
    return {"answer": grounded.answer, "evidence": grounded.evidence, "inference": grounded.inference, "citations": citations, "conversation_id": conversation.conversation_id}


@router.get("/agency/inbox")
def agency_inbox(db: Session = Depends(get_db)):
    requests = list(db.scalars(select(ViewingRequest).where(ViewingRequest.status == "PENDING").order_by(ViewingRequest.created_at.desc())))
    applications = list(db.scalars(select(Application).where(Application.status.in_(["SUBMITTED", "UNDER_REVIEW"])).order_by(Application.updated_at.desc())))
    questions = list(db.scalars(select(ActivityEvent).where(ActivityEvent.event_type == "PROPERTY_QUESTION").order_by(ActivityEvent.created_at.desc()).limit(20)))
    return {"viewing_requests": [_viewing(row, db) for row in requests], "applications": [_application(row, db) for row in applications], "questions": [_activity_item(row, db) for row in questions]}


@router.post("/reset")
def reset_demo(db: Session = Depends(get_db)):
    applicant_id = "A-DEMO-SARAH"
    for model in (ClientPreference, SavedProperty, ViewingRequest, Application, ActivityEvent):
        db.execute(delete(model).where(model.applicant_id == applicant_id))
    db.execute(delete(Conversation).where(Conversation.applicant_id == applicant_id, Conversation.conversation_id.like("CLIENT-%")))
    db.execute(delete(Interaction).where(Interaction.applicant_id == applicant_id, Interaction.interaction_id.like("WF-%")))
    db.commit()
    seed_demo_workflow(db)
    return {"status": "reset", "applicant_id": applicant_id}


def seed_demo_workflow(db: Session) -> None:
    """Create a small persisted starting state for the synthetic Sarah demo."""
    applicant_id = "A-DEMO-SARAH"
    if not db.get(Applicant, applicant_id) or db.scalar(select(ActivityEvent).where(ActivityEvent.applicant_id == applicant_id)):
        return
    db.add(ClientPreference(applicant_id=applicant_id, budget_max=2800, preferred_areas="Canary Wharf|Stratford", bedrooms_required=2, move_in_date=datetime(2026, 9, 15).date(), amenities_preferences="transport|balcony|gym|concierge"))
    db.add(SavedProperty(applicant_id=applicant_id, property_id="P-DEMO-01"))
    confirmed = ViewingRequest(applicant_id=applicant_id, property_id="P-DEMO-02", status="CONFIRMED", preferred_at=datetime(2026, 8, 22, 16, 0), confirmed_at=datetime.utcnow(), confirmed_by="Demo agency team")
    db.add(confirmed)
    db.add(Application(applicant_id=applicant_id, property_id="P-DEMO-01", status="UNDER_REVIEW", client_message="Sarah is ready to progress this application."))
    _event(db, applicant_id, "P-DEMO-01", "PROPERTY_SAVED", "Sarah saved P-DEMO-01.")
    _event(db, applicant_id, "P-DEMO-02", "VIEWING_CONFIRMED", "The agency confirmed Sarah's viewing for P-DEMO-02.")
    _event(db, applicant_id, "P-DEMO-01", "APPLICATION_SUBMITTED", "Sarah submitted an application for P-DEMO-01.")
    db.commit()


def _applicant(db: Session, applicant_id: str) -> Applicant:
    row = db.get(Applicant, applicant_id)
    if not row:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return row


def _client_applicant(db: Session, applicant_id: str) -> Applicant:
    if applicant_id != "A-DEMO-SARAH":
        raise HTTPException(status_code=403, detail="The demo client workspace is scoped to Sarah Mitchell.")
    return _applicant(db, applicant_id)


def _property(db: Session, property_id: str) -> Property:
    row = db.get(Property, property_id)
    if not row:
        raise HTTPException(status_code=404, detail="Property not found")
    return row


def _event(db: Session, applicant_id: str, property_id: str | None, event_type: str, message: str) -> None:
    db.add(ActivityEvent(applicant_id=applicant_id, property_id=property_id, event_type=event_type, message=message))
    db.add(Interaction(interaction_id=f"WF-{uuid4().hex[:16].upper()}", applicant_id=applicant_id, property_id=property_id, timestamp=datetime.utcnow(), channel="client_portal", event_type=event_type, message=message, sentiment=0.5, intent="HIGH"))


def _properties(db: Session, model, applicant_id: str):
    rows = db.scalars(select(model).where(model.applicant_id == applicant_id).order_by(model.created_at.desc())).all()
    return [{"saved_id": row.saved_id, "property_id": row.property_id, "created_at": row.created_at.isoformat()} for row in rows]


def _latest(db: Session, model, applicant_id: str, field: str):
    row = db.scalars(select(model).where(model.applicant_id == applicant_id).order_by(getattr(model, field).desc()).limit(1)).first()
    return _preference(row) if row else None


def _preference(row):
    return {"preference_id": row.preference_id, "budget_max": row.budget_max, "preferred_areas": row.preferred_areas, "bedrooms_required": row.bedrooms_required, "move_in_date": row.move_in_date.isoformat(), "amenities_preferences": row.amenities_preferences}


def _requests(db: Session, applicant_id: str):
    return [_viewing(row, db, include_internal=False) for row in db.scalars(select(ViewingRequest).where(ViewingRequest.applicant_id == applicant_id).order_by(ViewingRequest.created_at.desc()))]


def _viewing(row: ViewingRequest, db: Session, include_internal: bool = True):
    applicant = db.get(Applicant, row.applicant_id)
    prop = db.get(Property, row.property_id)
    result = {"request_id": row.request_id, "applicant_id": row.applicant_id, "applicant_name": applicant.name, "property_id": row.property_id, "property_area": prop.area, "rent_pcm": prop.rent_pcm, "status": row.status, "preferred_at": row.preferred_at.isoformat() if row.preferred_at else None, "proposed_at": row.proposed_at.isoformat() if row.proposed_at else None, "client_message": row.client_message, "created_at": row.created_at.isoformat(), "confirmed_at": row.confirmed_at.isoformat() if row.confirmed_at else None}
    if include_internal:
        result["agency_note"] = row.agency_note
        result["confirmed_by"] = row.confirmed_by
    return result


def _applications(db: Session, applicant_id: str, include_internal: bool = True):
    return [_application(row, db, include_internal=include_internal) for row in db.scalars(select(Application).where(Application.applicant_id == applicant_id).order_by(Application.updated_at.desc()))]


def _application(row: Application, db: Session, include_internal: bool = True):
    applicant = db.get(Applicant, row.applicant_id)
    prop = db.get(Property, row.property_id)
    result = {"application_id": row.application_id, "applicant_id": row.applicant_id, "applicant_name": applicant.name, "property_id": row.property_id, "property_area": prop.area, "rent_pcm": prop.rent_pcm, "status": row.status, "client_message": row.client_message, "created_at": row.created_at.isoformat(), "updated_at": row.updated_at.isoformat() if row.updated_at else row.created_at.isoformat()}
    if include_internal:
        result["agency_note"] = row.agency_note
    return result


def _activity(db: Session, applicant_id: str):
    return [_activity_item(row, db) for row in db.scalars(select(ActivityEvent).where(ActivityEvent.applicant_id == applicant_id).order_by(ActivityEvent.created_at.desc()).limit(50))]


def _activity_item(row: ActivityEvent, db: Session):
    prop = db.get(Property, row.property_id) if row.property_id else None
    return {"event_id": row.event_id, "event_type": row.event_type, "message": row.message, "property_id": row.property_id, "property_area": prop.area if prop else None, "created_at": row.created_at.isoformat()}
