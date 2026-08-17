from pydantic import BaseModel, Field
from app.schemas.domain import ApplicantRead, PropertyRead


class Citation(BaseModel):
    citation_id: str | None = None
    document_id: str | None = None
    source_record_id: str | None = None
    source_table: str | None = None
    chunk_id: str | None = None
    channel: str | None = None
    synthetic: bool = True
    indexed: bool = True
    source: str
    document_type: str
    applicant_id: str | None = None
    property_id: str | None = None
    timestamp: str | None = None
    excerpt: str
    score: float = 0.0
    semantic_score: float | None = None
    lexical_score: float | None = None
    hybrid_score: float | None = None
    rerank_score: float | None = None
    selection_reason: str | None = None


class MatchExplanation(BaseModel):
    budget_match: float
    bedroom_match: float
    location_match: float
    property_type_match: float
    amenity_match: float
    furnished_match: float
    parking_match: float
    pet_match: float
    distance_score: float
    behavioural_similarity: float
    historical_preference_match: float
    positives: list[str]
    negatives: list[str]


class PropertyMatch(BaseModel):
    property: PropertyRead
    match_score: float = Field(ge=0, le=100)
    explanation: MatchExplanation


class IntentResult(BaseModel):
    intent: str
    confidence: float
    probabilities: dict[str, float]
    features: dict[str, float]
    key_signals: list[str]


class ConversionResult(BaseModel):
    conversion_probability: float
    top_positive_factors: list[str]
    top_negative_factors: list[str]
    features: dict[str, float]


class NextBestAction(BaseModel):
    action: str
    priority: str
    confidence: float
    reason: str
    recommended_properties: list[PropertyMatch] = []


class ApplicantIntelligenceResponse(BaseModel):
    applicant: ApplicantRead
    top_matches: list[PropertyMatch]
    intent: IntentResult
    conversion: ConversionResult
    key_signals: list[str]
    recommended_action: NextBestAction
    explanation: str
    sources: list[Citation]


class PropertyIntelligenceResponse(BaseModel):
    property: PropertyRead
    demand: str
    qualified_applicants: int
    strong_matches: int
    average_match_score: float
    viewing_conversion: float
    application_conversion: float
    top_applicant_concern: str
    top_applicant_preference: str
    popular_amenities: list[str]
    applicant_segments: dict[str, int]
    recommended_action: str
    top_matching_applicants: list[dict]
    sources: list[Citation] = []


class SearchResponse(BaseModel):
    answer: str
    applicants: list[dict] = Field(default_factory=list)
    properties: list[PropertyMatch] = Field(default_factory=list)
    recommendations: list[NextBestAction] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    retrieval: dict = Field(default_factory=dict)
    generation: dict = Field(default_factory=dict)
