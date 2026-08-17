from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


def split_pipe(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [part.strip() for part in value.split("|") if part.strip()]


class PropertyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    property_id: str
    postcode: str
    city: str
    area: str
    property_type: str
    bedrooms: int
    bathrooms: int
    rent_pcm: int
    sale_price: int | None
    size_sqft: int
    furnished: bool
    parking: bool
    garden: bool
    balcony: bool
    pets_allowed: bool
    available_date: date
    amenities: str
    description: str
    latitude: float
    longitude: float


class ApplicantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    applicant_id: str
    name: str
    age_band: str
    budget_min: int
    budget_max: int
    preferred_areas: str
    bedrooms_required: int
    property_types: str
    move_in_date: date
    employment_type: str
    pets: bool
    children: bool
    furnished_preference: str
    parking_required: bool
    amenities_preferences: str


class InteractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interaction_id: str
    applicant_id: str
    property_id: str | None
    timestamp: datetime
    channel: str
    event_type: str
    message: str
    sentiment: float
    intent: str


class MatchRequest(BaseModel):
    applicant_id: str
    limit: int = Field(default=10, ge=1, le=50)


class ClientMatchRequest(BaseModel):
    applicant_id: str = "A-DEMO-SARAH"
    budget_max: int = Field(ge=500, le=20000)
    preferred_areas: str = Field(min_length=2, max_length=240)
    bedrooms_required: int = Field(ge=0, le=10)
    amenities_preferences: str = ""
    move_in_date: date
    limit: int = Field(default=8, ge=1, le=20)


class ClientPreferenceRequest(BaseModel):
    applicant_id: str = "A-DEMO-SARAH"
    budget_max: int = Field(ge=500, le=20000)
    preferred_areas: str = Field(min_length=2, max_length=240)
    bedrooms_required: int = Field(ge=0, le=10)
    amenities_preferences: str = ""
    move_in_date: date


class SavePropertyRequest(BaseModel):
    applicant_id: str = "A-DEMO-SARAH"
    property_id: str
    saved: bool | None = None


class ViewingRequestCreate(BaseModel):
    applicant_id: str = "A-DEMO-SARAH"
    property_id: str
    preferred_at: datetime | None = None
    client_message: str = ""


class WorkflowStatusUpdate(BaseModel):
    status: str
    note: str = ""
    proposed_at: datetime | None = None


class ApplicationCreate(BaseModel):
    applicant_id: str = "A-DEMO-SARAH"
    property_id: str
    client_message: str = ""


class ClientQuestionRequest(BaseModel):
    applicant_id: str = "A-DEMO-SARAH"
    property_id: str
    question: str = Field(min_length=3, max_length=500)


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    applicant_id: str | None = None
    property_id: str | None = None
    limit: int = Field(default=8, ge=1, le=25)


class AnalyzeRequest(BaseModel):
    applicant_id: str
    property_id: str | None = None


class AgentRunRequest(BaseModel):
    applicant_id: str
    property_id: str | None = None
    query: str | None = None
    limit: int = Field(default=5, ge=1, le=20)
