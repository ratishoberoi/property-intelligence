from datetime import date, datetime
from uuid import uuid4
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Property(Base):
    __tablename__ = "properties"

    property_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    postcode: Mapped[str] = mapped_column(String(16), index=True)
    city: Mapped[str] = mapped_column(String(64), index=True)
    area: Mapped[str] = mapped_column(String(96), index=True)
    property_type: Mapped[str] = mapped_column(String(32), index=True)
    bedrooms: Mapped[int] = mapped_column(Integer, index=True)
    bathrooms: Mapped[int] = mapped_column(Integer)
    rent_pcm: Mapped[int] = mapped_column(Integer, index=True)
    sale_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_sqft: Mapped[int] = mapped_column(Integer)
    furnished: Mapped[bool] = mapped_column(Boolean, default=True)
    parking: Mapped[bool] = mapped_column(Boolean, default=False)
    garden: Mapped[bool] = mapped_column(Boolean, default=False)
    balcony: Mapped[bool] = mapped_column(Boolean, default=False)
    pets_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    available_date: Mapped[date] = mapped_column(Date, index=True)
    amenities: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    interactions: Mapped[list["Interaction"]] = relationship(back_populates="property")
    viewings: Mapped[list["Viewing"]] = relationship(back_populates="property")


class Applicant(Base):
    __tablename__ = "applicants"

    applicant_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    age_band: Mapped[str] = mapped_column(String(16))
    budget_min: Mapped[int] = mapped_column(Integer)
    budget_max: Mapped[int] = mapped_column(Integer, index=True)
    preferred_areas: Mapped[str] = mapped_column(Text)
    bedrooms_required: Mapped[int] = mapped_column(Integer, index=True)
    property_types: Mapped[str] = mapped_column(Text)
    move_in_date: Mapped[date] = mapped_column(Date)
    employment_type: Mapped[str] = mapped_column(String(64))
    pets: Mapped[bool] = mapped_column(Boolean, default=False)
    children: Mapped[bool] = mapped_column(Boolean, default=False)
    furnished_preference: Mapped[str] = mapped_column(String(32), default="any")
    parking_required: Mapped[bool] = mapped_column(Boolean, default=False)
    amenities_preferences: Mapped[str] = mapped_column(Text, default="")

    interactions: Mapped[list["Interaction"]] = relationship(back_populates="applicant")
    viewings: Mapped[list["Viewing"]] = relationship(back_populates="applicant")


class Interaction(Base):
    __tablename__ = "interactions"

    interaction_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    applicant_id: Mapped[str] = mapped_column(ForeignKey("applicants.applicant_id"), index=True)
    property_id: Mapped[str | None] = mapped_column(ForeignKey("properties.property_id"), nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    channel: Mapped[str] = mapped_column(String(32))
    event_type: Mapped[str] = mapped_column(String(48), index=True)
    message: Mapped[str] = mapped_column(Text, default="")
    sentiment: Mapped[float] = mapped_column(Float, default=0.0)
    intent: Mapped[str] = mapped_column(String(32), default="UNKNOWN")

    applicant: Mapped[Applicant] = relationship(back_populates="interactions")
    property: Mapped[Property | None] = relationship(back_populates="interactions")


class Viewing(Base):
    __tablename__ = "viewings"

    viewing_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    applicant_id: Mapped[str] = mapped_column(ForeignKey("applicants.applicant_id"), index=True)
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.property_id"), index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(32))

    applicant: Mapped[Applicant] = relationship(back_populates="viewings")
    property: Mapped[Property] = relationship(back_populates="viewings")
    feedback: Mapped["Feedback | None"] = relationship(back_populates="viewing")


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    viewing_id: Mapped[str] = mapped_column(ForeignKey("viewings.viewing_id"), index=True)
    applicant_id: Mapped[str] = mapped_column(ForeignKey("applicants.applicant_id"), index=True)
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.property_id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    rating: Mapped[int] = mapped_column(Integer)
    sentiment: Mapped[float] = mapped_column(Float)
    objections: Mapped[str] = mapped_column(Text, default="")
    comments: Mapped[str] = mapped_column(Text)

    viewing: Mapped[Viewing] = relationship(back_populates="feedback")


class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    applicant_id: Mapped[str] = mapped_column(ForeignKey("applicants.applicant_id"), index=True)
    property_id: Mapped[str | None] = mapped_column(ForeignKey("properties.property_id"), nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    direction: Mapped[str] = mapped_column(String(16))
    channel: Mapped[str] = mapped_column(String(32))
    subject: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    sentiment: Mapped[float] = mapped_column(Float, default=0.0)


class ClientPreference(Base):
    __tablename__ = "client_preferences"

    preference_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: f"PREF-{uuid4().hex[:12].upper()}")
    applicant_id: Mapped[str] = mapped_column(ForeignKey("applicants.applicant_id"), index=True)
    budget_max: Mapped[int] = mapped_column(Integer)
    preferred_areas: Mapped[str] = mapped_column(Text)
    bedrooms_required: Mapped[int] = mapped_column(Integer)
    move_in_date: Mapped[date] = mapped_column(Date)
    amenities_preferences: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class SavedProperty(Base):
    __tablename__ = "saved_properties"

    saved_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: f"SAVE-{uuid4().hex[:12].upper()}")
    applicant_id: Mapped[str] = mapped_column(ForeignKey("applicants.applicant_id"), index=True)
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.property_id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ViewingRequest(Base):
    __tablename__ = "viewing_requests"

    request_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: f"VIEWREQ-{uuid4().hex[:12].upper()}")
    applicant_id: Mapped[str] = mapped_column(ForeignKey("applicants.applicant_id"), index=True)
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.property_id"), index=True)
    status: Mapped[str] = mapped_column(String(24), default="PENDING", index=True)
    preferred_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    proposed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    client_message: Mapped[str] = mapped_column(Text, default="")
    agency_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confirmed_by: Mapped[str | None] = mapped_column(String(96), nullable=True)


class Application(Base):
    __tablename__ = "applications"

    application_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: f"APP-{uuid4().hex[:12].upper()}")
    applicant_id: Mapped[str] = mapped_column(ForeignKey("applicants.applicant_id"), index=True)
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.property_id"), index=True)
    status: Mapped[str] = mapped_column(String(24), default="STARTED", index=True)
    client_message: Mapped[str] = mapped_column(Text, default="")
    agency_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    event_id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: f"EVT-{uuid4().hex[:12].upper()}")
    applicant_id: Mapped[str] = mapped_column(ForeignKey("applicants.applicant_id"), index=True)
    property_id: Mapped[str | None] = mapped_column(ForeignKey("properties.property_id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(48), index=True)
    message: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
