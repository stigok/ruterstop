.PHONY: test
test:
	poetry run python -m unittest

.PHONY: matrix-unit-tests
matrix-unit-tests:
	.deploy/run-tests.sh 3.5 matrix-unit-tests python setup.py test
	.deploy/run-tests.sh 3.6 matrix-unit-tests python setup.py test
	.deploy/run-tests.sh 3.7 matrix-unit-tests python setup.py test
	.deploy/run-tests.sh 3.8 matrix-unit-tests python setup.py test

.PHONY: matrix-install
matrix-install:
	.deploy/run-tests.sh 3.5 matrix-install pip install .
	.deploy/run-tests.sh 3.6 matrix-install pip install .
	.deploy/run-tests.sh 3.7 matrix-install pip install .
	.deploy/run-tests.sh 3.8 matrix-install pip install .

.PHONY: matrix
matrix: matrix-unit-tests matrix-install
