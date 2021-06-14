.PHONY: test
test:
	poetry run python -m unittest

.PHONY: matrix-unit-tests
matrix-unit-tests:
	poetry run .deploy/run_tests.py 3.6
	poetry run .deploy/run_tests.py 3.7
	poetry run .deploy/run_tests.py 3.8

.PHONY: matrix
matrix: matrix-unit-tests
