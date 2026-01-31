.PHONY: run migrate makemigrations shell test install

VENV = venv/bin
PYTHON = $(VENV)/python
PIP = $(VENV)/pip

run:
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
