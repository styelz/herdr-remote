.PHONY: relay-venv relay-install relay-run relay-plugin ios-build

VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python3

relay-venv:
	python3 -m venv $(VENV)
	$(VENV_PYTHON) -m pip install -r requirements.txt

relay-install:
	$(VENV_PYTHON) -m pip install -r requirements.txt

relay-run:
	$(VENV_PYTHON) relay/herdr_relay.py

relay-plugin:
	herdr plugin link relay/

ios-build:
	cd herdi-ios && swift build
