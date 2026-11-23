PYTHON ?= python3
VENV ?= .venv

.PHONY: setup run test audit import clean-db

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements-dev.txt

run:
	$(VENV)/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	$(VENV)/bin/pytest -q

audit:
	$(VENV)/bin/python -m scripts.audit_library

import:
	$(VENV)/bin/python -m scripts.import_questions

clean-db:
	rm -f data/study.db data/study.db-*
