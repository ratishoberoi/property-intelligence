from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import Applicant, Conversation, Feedback, Interaction, Property, Viewing


DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"


def seed_synthetic_dataset(db: Session, data_dir: Path = DATA_DIR) -> None:
    """Load the committed synthetic CSV dataset into an empty database."""
    if not (data_dir / "properties.csv").exists():
        raise RuntimeError(f"Synthetic dataset is missing: {data_dir / 'properties.csv'}")

    for model in [Conversation, Feedback, Viewing, Interaction, Applicant, Property]:
        db.execute(delete(model))
    db.commit()

    _load(db, Property, data_dir / "properties.csv")
    _load(db, Applicant, data_dir / "applicants.csv")
    _load(db, Interaction, data_dir / "interactions.csv")
    _load(db, Viewing, data_dir / "viewings.csv")
    _load(db, Feedback, data_dir / "feedback.csv")
    _load(db, Conversation, data_dir / "conversations.csv")
    db.commit()


def _load(db: Session, model, path: Path) -> None:
    frame = pd.read_csv(path).replace({float("nan"): None})
    for column in ["available_date", "move_in_date"]:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column]).dt.date
    for column in ["timestamp", "scheduled_at"]:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column]).dt.to_pydatetime()
    if "sale_price" in frame.columns:
        frame["sale_price"] = frame["sale_price"].where(pd.notnull(frame["sale_price"]), None)
    if "property_id" in frame.columns:
        frame["property_id"] = frame["property_id"].replace({"": None})
    records = frame.where(pd.notnull(frame), None).to_dict(orient="records")
    db.bulk_insert_mappings(model, records)
