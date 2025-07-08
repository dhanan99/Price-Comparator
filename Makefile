# Makefile for Flask + crawl4ai app with virtual environment

VENV_NAME := comparator_venv
CRAWL4AI_SETUP := $(VENV_NAME)/bin/crawl4ai-setup

# Makefile for Flask + crawl4ai app with venv + UTF-8 fix

PYTHON := python3
PIP := $(VENV_NAME)/bin/python -m pip

.PHONY: venv install run clean

venv:
	$(PYTHON) -m venv $(VENV_NAME)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(CRAWL4AI_SETUP)

run:
	@echo "Activating virtualenv and starting Flask..."
	source $(VENV_NAME)/bin/activate && FLASK_APP=app.py FLASK_ENV=development $(VENV_NAME)/bin/flask run

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	rm -rf $(VENV_NAME)
