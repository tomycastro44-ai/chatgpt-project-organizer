.PHONY: setup backend frontend test validate

setup:
	./scripts/setup.sh

backend:
	.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --port 8000

frontend:
	npm --prefix frontend run dev

test:
	./scripts/test-all.sh

validate:
	PYTHONPATH=backend python scripts/validate_ot012.py
