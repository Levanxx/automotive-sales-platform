.PHONY: run test coverage integration n8n-validate n8n-smoke seed load50 load100 stress regression
run:
	docker compose up --build
test:
	python -m unittest discover -s tests -v
coverage:
	coverage run --branch -m unittest discover -s tests && coverage report --fail-under=80
integration:
	python scripts/integration_check.py --self-contained
n8n-validate:
	python scripts/validate_n8n.py
n8n-smoke:
	python scripts/n8n_cloud_smoke_check.py
seed:
	python scripts/seed.py
load50:
	python load-tests/sales_load.py --concurrency 50
load100:
	python load-tests/sales_load.py --concurrency 100
stress:
	python scripts/stress_check.py
regression: coverage integration n8n-validate
