#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.db.bootstrap import seed_synthetic_dataset
from app.db.session import Base, SessionLocal, engine


def main() -> None:
    data_dir = ROOT.parent / "data" / "processed"
    if not (data_dir / "properties.csv").exists():
        raise SystemExit("Dataset missing. Run python backend/scripts/generate_dataset.py first.")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_synthetic_dataset(db, data_dir)
        print("Seeded database with synthetic demo data.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
