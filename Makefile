.PHONY: dev backend frontend test build qa clean

# Run both backend and frontend dev servers concurrently
dev:
	@echo "Starting CampusConnect backend (http://127.0.0.1:5000) and frontend (http://localhost:5173)..."
	@powershell -NoProfile -ExecutionPolicy Bypass -File dev.ps1

backend:
	"backend/venv/Scripts/python.exe" backend/run.py

frontend:
	npm --prefix frontend run dev

test:
	"backend/venv/Scripts/pytest.exe" backend/tests -v --tb=short

build:
	npm --prefix frontend run build

qa:
	"backend/venv/Scripts/python.exe" -u qa/test_complete_feature_suite.py
