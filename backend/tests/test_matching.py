from app.intelligence.matching.engine import PropertyMatchingEngine
from app.services.applicant_service import ApplicantService


def test_matching_scores_demo_like_property_high(db):
    applicant = ApplicantService(db).get("A-T1")
    matches = PropertyMatchingEngine(db).match(applicant, 5)
    assert matches
    assert matches[0].property.property_id == "P-T1"
    assert matches[0].match_score >= 85
    assert matches[0].explanation.budget_match >= 0.9

