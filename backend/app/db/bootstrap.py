from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Applicant, Conversation, Feedback, Interaction, Property, Viewing


SYNTHETIC_DATA_FILES = (
    "properties.csv",
    "applicants.csv",
    "interactions.csv",
    "viewings.csv",
    "feedback.csv",
    "conversations.csv",
)


def resolve_data_dir(configured_dir: Path | str | None = None) -> Path:
    """Resolve DATA_DIR for Docker absolute paths and local relative paths."""
    configured = Path(configured_dir) if configured_dir is not None else get_settings().data_dir
    if configured.is_absolute():
        return configured

    working_directory_path = (Path.cwd() / configured).resolve()
    if working_directory_path.exists():
        return working_directory_path

    # When the backend is started from the repository root, the local default
    # is relative to the backend directory rather than the current directory.
    repository_root = Path(__file__).resolve().parents[3]
    return (repository_root / "data" / "processed").resolve()


def seed_synthetic_dataset(db: Session, data_dir: Path | str | None = None) -> None:
    """Load the committed synthetic CSV dataset into an empty database."""
    data_dir = resolve_data_dir(data_dir)
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
