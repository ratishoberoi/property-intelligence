PYTHON ?= $(if $(wildcard .venv/bin/python),$(CURDIR)/.venv/bin/python,python3)

.PHONY: setup generate seed train index eval rag-provenance export-dataset backend frontend test smoke docker-up docker-down

setup: generate seed train index eval

generate:
	cd backend && $(PYTHON) scripts/generate_dataset.py

seed:
	cd backend && $(PYTHON) scripts/seed_database.py

train:
	cd backend && $(PYTHON) scripts/train_models.py

index:
	cd backend && $(PYTHON) scripts/build_index.py

eval:
	cd backend && $(PYTHON) scripts/run_evaluation.py

rag-provenance:
	cd backend && $(PYTHON) scripts/rag_provenance.py

export-dataset:
	cd backend && $(PYTHON) scripts/export_dataset.py

backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && $(PYTHON) -m pytest -q
	cd frontend && npm run lint && npm run typecheck && npm run build

smoke:
	curl -fsS http://localhost:8000/health
	curl -fsS http://localhost:8000/api/dashboard/summary
	curl -fsS http://localhost:8000/api/applicants/A-DEMO-SARAH/intelligence

docker-up:
	docker compose up --build

docker-down:
	docker compose down -v
