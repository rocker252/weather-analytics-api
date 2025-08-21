# Makefile

APP_NAME = weather-analytics-api
PORT = 8000

# ---------- Commands ----------

.PHONY: install start test lint build up down logs
.PHONY: test coverage lint start db-seed
.PHONY: clean
.PHONY: dev


install:
	poetry install

start:
	poetry run uvicorn weather_analytics_api.api:app --reload --host 0.0.0.0 --port $(PORT)

test:
	poetry run pytest --disable-warnings -v

lint:
	poetry run isort weather_analytics_api tests
	poetry run black weather_analytics_api tests
	poetry run flake8 weather_analytics_api tests

build:
	docker build -t $(APP_NAME):latest .

up:
	docker-compose up -d --build

down:
	docker-compose down

logs:
	docker-compose logs -f

coverage:
	poetry run pytest --cov=weather_analytics_api --cov-report=term-missing --cov-report=html tests

db-seed:
	poetry run python scripts/seed_db.py

clean:
	# Remove Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	# Remove coverage reports
	rm -rf htmlcov
	rm -f .coverage

format:
	poetry run black weather_analytics_api tests

dev: install
	poetry run uvicorn weather_analytics_api.api:app --reload --host 0.0.0.0 --port $(PORT)