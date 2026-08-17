from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Applicant, Interaction, Property
from app.schemas.domain import split_pipe
from app.schemas.intelligence import MatchExplanation, PropertyMatch


@dataclass(frozen=True)
class MatchingWeights:
    budget_match: float = 0.24
    bedroom_match: float = 0.14
    location_match: float = 0.18
    property_type_match: float = 0.1
    amenity_match: float = 0.12
    furnished_match: float = 0.05
    parking_match: float = 0.05
    pet_match: float = 0.04
    distance_score: float = 0.03
    behavioural_similarity: float = 0.03
    historical_preference_match: float = 0.02


class PropertyMatchingEngine:
    """Hybrid retrieval and transparent ranking for applicant-property matching."""

    def __init__(self, db: Session, weights: MatchingWeights | None = None):
        self.db = db
        self.weights = weights or MatchingWeights()

    def match(self, applicant: Applicant, limit: int = 10) -> list[PropertyMatch]:
        candidates = self._hard_filter(applicant)
        scored = [self._score(applicant, prop) for prop in candidates]
        scored.sort(key=lambda item: item.match_score, reverse=True)
        return scored[:limit]

    def score_property(self, applicant: Applicant, prop: Property) -> PropertyMatch:
        return self._score(applicant, prop)

    def _hard_filter(self, applicant: Applicant) -> list[Property]:
        types = split_pipe(applicant.property_types)
        budget_ceiling = int(applicant.budget_max * 1.12)
        stmt = (
            select(Property)
            .where(Property.rent_pcm <= budget_ceiling)
            .where(Property.bedrooms >= max(applicant.bedrooms_required - 1, 0))
            .where(Property.available_date <= applicant.move_in_date)
            .order_by(Property.rent_pcm.asc())
            .limit(300)
        )
        if types:
            stmt = stmt.where(Property.property_type.in_(types))
        return list(self.db.scalars(stmt))

    def _score(self, applicant: Applicant, prop: Property) -> PropertyMatch:
        features = self._features(applicant, prop)
        weighted = sum(getattr(self.weights, key) * value for key, value in features.items())
        score = round(max(0.0, min(100.0, weighted * 100)), 1)
        explanation = self._explain(applicant, prop, features)
        return PropertyMatch(property=prop, match_score=score, explanation=explanation)

    def _features(self, applicant: Applicant, prop: Property) -> dict[str, float]:
        preferred_areas = split_pipe(applicant.preferred_areas)
        applicant_amenities = set(split_pipe(applicant.amenities_preferences))
        prop_amenities = set(split_pipe(prop.amenities))
        if prop.rent_pcm <= applicant.budget_max:
            budget = 1.0 - max(applicant.budget_min - prop.rent_pcm, 0) / max(applicant.budget_min, 1) * 0.3
        else:
            budget = max(0.0, 1.0 - (prop.rent_pcm - applicant.budget_max) / max(applicant.budget_max, 1) * 3.0)
        bedroom = 1.0 if prop.bedrooms == applicant.bedrooms_required else max(0.25, 1 - abs(prop.bedrooms - applicant.bedrooms_required) * 0.35)
        location = 1.0 if prop.area in preferred_areas else 0.55 if prop.city == "London" else 0.25
        ptype = 1.0 if prop.property_type in split_pipe(applicant.property_types) else 0.25
        amenity = len(applicant_amenities & prop_amenities) / max(len(applicant_amenities), 1)
        furnished = 1.0 if applicant.furnished_preference == "any" else float((applicant.furnished_preference == "furnished") == prop.furnished)
        parking = 1.0 if not applicant.parking_required else float(prop.parking)
        pet = 1.0 if not applicant.pets else float(prop.pets_allowed)
        distance = 1.0 if prop.area in preferred_areas else 0.65
        return {
            "budget_match": round(max(0.0, min(1.0, budget)), 3),
            "bedroom_match": round(bedroom, 3),
            "location_match": round(location, 3),
            "property_type_match": round(ptype, 3),
            "amenity_match": round(amenity, 3),
            "furnished_match": round(furnished, 3),
            "parking_match": round(parking, 3),
            "pet_match": round(pet, 3),
            "distance_score": round(distance, 3),
            "behavioural_similarity": round(self._behavioural_similarity(applicant, prop), 3),
            "historical_preference_match": round(self._historical_preference(applicant, prop), 3),
        }

    def _behavioural_similarity(self, applicant: Applicant, prop: Property) -> float:
        rows = list(
            self.db.scalars(
                select(Interaction)
                .where(Interaction.applicant_id == applicant.applicant_id)
                .where(Interaction.property_id.is_not(None))
                .where(Interaction.event_type.in_(["PROPERTY_VIEW", "VIEWING_BOOKED", "FEEDBACK", "APPLICATION_STARTED"]))
                .limit(50)
            )
        )
        if not rows:
            return 0.5
        seen_ids = [row.property_id for row in rows if row.property_id]
        seen = list(self.db.scalars(select(Property).where(Property.property_id.in_(seen_ids))))
        if not seen:
            return 0.5
        area_hits = sum(1 for p in seen if p.area == prop.area)
        rent_closeness = sum(max(0, 1 - abs(p.rent_pcm - prop.rent_pcm) / max(prop.rent_pcm, 1)) for p in seen) / len(seen)
        return min(1.0, 0.35 + 0.35 * area_hits / len(seen) + 0.3 * rent_closeness)

    def _historical_preference(self, applicant: Applicant, prop: Property) -> float:
        positive = list(
            self.db.scalars(
                select(Interaction)
                .where(Interaction.applicant_id == applicant.applicant_id)
                .where(Interaction.event_type.in_(["APPLICATION_STARTED", "APPLICATION_SUBMITTED", "OFFER_MADE", "OFFER_ACCEPTED"]))
            )
        )
        if not positive:
            return 0.5
        return 1.0 if any(row.property_id == prop.property_id for row in positive) else 0.65

    def _explain(self, applicant: Applicant, prop: Property, f: dict[str, float]) -> MatchExplanation:
        positives: list[str] = []
        negatives: list[str] = []
        if f["budget_match"] >= 0.9:
            positives.append(f"Rent at £{prop.rent_pcm:,} is aligned with the applicant budget.")
        elif f["budget_match"] < 0.55:
            negatives.append(f"Rent at £{prop.rent_pcm:,} is materially above the preferred ceiling.")
        if f["bedroom_match"] >= 0.95:
            positives.append(f"{prop.bedrooms} bedrooms exactly matches the requirement.")
        if f["location_match"] >= 0.9:
            positives.append(f"{prop.area} is one of the preferred areas.")
        if f["amenity_match"] >= 0.7:
            positives.append("Most requested amenities are present.")
        if applicant.parking_required and not prop.parking:
            negatives.append("Parking is required but unavailable.")
        if applicant.pets and not prop.pets_allowed:
            negatives.append("Applicant has pets but this property does not allow pets.")
        if not positives:
            positives.append("The property passes the hard eligibility filters.")
        return MatchExplanation(**f, positives=positives, negatives=negatives)

