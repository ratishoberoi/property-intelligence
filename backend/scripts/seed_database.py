#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import delete

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.db.models import Applicant, Conversation, Feedback, Interaction, Property, Viewing
from app.db.session import Base, SessionLocal, engine


def main() -> None:
    data_dir = ROOT.parent / "data" / "processed"
    if not (data_dir / "properties.csv").exists():
        raise SystemExit("Dataset missing. Run python backend/scripts/generate_dataset.py first.")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for model in [Conversation, Feedback, Viewing, Interaction, Applicant, Property]:
            db.execute(delete(model))
        db.commit()
        load(db, Property, data_dir / "properties.csv")
        load(db, Applicant, data_dir / "applicants.csv")
        load(db, Interaction, data_dir / "interactions.csv")
        load(db, Viewing, data_dir / "viewings.csv")
        load(db, Feedback, data_dir / "feedback.csv")
        load(db, Conversation, data_dir / "conversations.csv")
        db.commit()
        print("Seeded database with synthetic demo data.")
    finally:
        db.close()


def load(db, model, path: Path) -> None:
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
    print(f"Loaded {len(records)} rows into {model.__tablename__}")


if __name__ == "__main__":
    main()
