from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Property


class PropertyService:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        area: str | None = None,
        max_rent: int | None = None,
        bedrooms: int | None = None,
    ) -> list[Property]:
        stmt = select(Property).order_by(Property.property_id).offset(offset).limit(limit)
        if area:
            stmt = stmt.where(Property.area.ilike(f"%{area}%"))
        if max_rent:
            stmt = stmt.where(Property.rent_pcm <= max_rent)
        if bedrooms:
            stmt = stmt.where(Property.bedrooms == bedrooms)
        return list(self.db.scalars(stmt))

    def get(self, property_id: str) -> Property | None:
        return self.db.get(Property, property_id)

