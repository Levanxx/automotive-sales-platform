.PHONY: run test coverage seed load50 load100
run:
	docker compose up --build
test:
	python -m unittest discover -s tests -v
coverage:
	coverage run --branch -m unittest discover -s tests && coverage report --fail-under=80
seed:
	python scripts/seed.py
load50:
	python load-tests/sales_load.py --concurrency 50
load100:
	python load-tests/sales_load.py --concurrency 100

