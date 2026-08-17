import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_property_intelligence.db")
os.environ.setdefault("RAG_EMBEDDING_MODE", "lexical")

import pytest
from datetime import date
from app.db.models import Applicant, Property
from app.db.session import Base, SessionLocal, engine


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    session.add(
        Property(
            property_id="P-T1",
            postcode="E14 1AA",
            city="London",
            area="Canary Wharf",
            property_type="flat",
            bedrooms=2,
            bathrooms=2,
            rent_pcm=2700,
            sale_price=None,
            size_sqft=760,
            furnished=True,
            parking=False,
            garden=False,
            balcony=True,
            pets_allowed=False,
            available_date=date(2026, 9, 1),
            amenities="transport|balcony|gym|concierge",
            description="Synthetic test property with transport and balcony.",
            latitude=51.5,
            longitude=-0.02,
        )
    )
    session.add(
        Applicant(
            applicant_id="A-T1",
            name="Sarah Mitchell",
            age_band="25-34",
            budget_min=2500,
            budget_max=2800,
            preferred_areas="Canary Wharf|Stratford",
            bedrooms_required=2,
            property_types="flat",
            move_in_date=date(2026, 9, 15),
            employment_type="permanent",
            pets=False,
            children=False,
            furnished_preference="furnished",
            parking_required=False,
            amenities_preferences="transport|balcony|gym",
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
