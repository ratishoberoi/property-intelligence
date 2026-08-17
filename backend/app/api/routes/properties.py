from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.intelligence.property_intelligence.engine import PropertyIntelligenceEngine
from app.schemas.domain import PropertyRead
from app.services.property_service import PropertyService

router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("", response_model=list[PropertyRead])
def list_properties(
    limit: int = Query(50, ge=1, le=200),
    offset: int = 0,
    area: str | None = None,
    max_rent: int | None = None,
    bedrooms: int | None = None,
    db: Session = Depends(get_db),
):
    return PropertyService(db).list(limit=limit, offset=offset, area=area, max_rent=max_rent, bedrooms=bedrooms)


@router.get("/{property_id}", response_model=PropertyRead)
def get_property(property_id: str, db: Session = Depends(get_db)):
    prop = PropertyService(db).get(property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@router.get("/{property_id}/intelligence")
def property_intelligence(property_id: str, db: Session = Depends(get_db)):
    prop = PropertyService(db).get(property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return PropertyIntelligenceEngine(db).analyze(prop)

