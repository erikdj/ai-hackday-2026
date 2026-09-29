PYTHON ?= python3
VENV ?= .venv
RUN_PYTHON = $(VENV)/bin/python
FIXTURE ?= transcript_1

.PHONY: install check smoke-models demo
install:
	$(PYTHON) -m venv $(VENV)
	$(RUN_PYTHON) -m pip install -r requirements.txt

check:
	$(RUN_PYTHON) -m compileall -q hallway scripts
	$(RUN_PYTHON) -m unittest discover -s scripts -p 'test_*.py' -v
	$(RUN_PYTHON) -m unittest discover -s hallway/tests -v

# First discover IDs: make smoke-models MODELS=--list
# Then supply exactly two: make smoke-models MODELS='catalog/id-a catalog/id-b'
smoke-models:
	$(RUN_PYTHON) scripts/smoke_models.py $(MODELS)

# Requires live Band/Crusoe configuration. The module sends through Band only.
# Room is read from BAND_LOBBY_ROOM_ID (.env supported by the product).
demo:
	$(RUN_PYTHON) -m hallway.demo --fixture $(FIXTURE)
