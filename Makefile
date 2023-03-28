install:
	python -m pip install --upgrade pip
	python -m pip install black flake8 isort
	python -m pip install -e .

check:
	python -m black prodigy-tui
	python -m pytest prodigy-tui/tests.py
	python -m isort prodigy-tui
	python -m flake8 prodigy-tui