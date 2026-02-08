.PHONY: setup test migrate lint

setup:
	python3 -m venv .venv
	. .venv/bin/activate && python -m pip install -r requirements.txt

test:
	. .venv/bin/activate && python -m unittest discover -v -s tests -p 'test_*.py'

migrate:
	. .venv/bin/activate && alembic upgrade head

lint:
	. .venv/bin/activate && python -m compileall app tests alembic
