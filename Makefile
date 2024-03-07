install:
	/bin/sh setup.sh

fmt:
	isort .
	black .

lint: fmt-check

fmt-check:
	isort --check .
	black --check .
