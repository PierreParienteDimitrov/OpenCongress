.PHONY: run migrate makemigrations shell test install

VENV = venv/bin
PYTHON = $(VENV)/python
PIP = $(VENV)/pip

run:
	docker compose -f ../docker-compose.yml up -d db redis
	@echo "Waiting for PostgreSQL to be ready..."
	@until docker compose -f ../docker-compose.yml exec db pg_isready -U postgres > /dev/null 2>&1; do sleep 1; done
	$(PYTHON) manage.py runserver

migrate:
	$(PYTHON) manage.py migrate

makemigrations:
	$(PYTHON) manage.py makemigrations

shell:
	$(PYTHON) manage.py shell

test:
	$(PYTHON) manage.py test

install:
	$(PIP) install -r requirements/base.txt
