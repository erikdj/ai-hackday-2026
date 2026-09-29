PYTHON ?= python3
VENV ?= .venv
RUN_PYTHON = $(VENV)/bin/python
FIXTURE ?= handoff_2

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

# Live is the default. BOTH mock flags explicitly select unit-test harness only.
# Mixed flags fail; a live error never falls back to local execution.
demo:
	@mode=$$($(RUN_PYTHON) -m hallway.offline_demo --mode) || exit $$?; \
	case "$$mode" in \
	  offline) $(RUN_PYTHON) -m hallway.offline_demo ;; \
	  live) $(RUN_PYTHON) -m hallway.demo --fixture $(FIXTURE) ;; \
	  *) exit 2 ;; \
	esac
