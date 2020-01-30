.PHONY: test
test:
	python3 setup.py test

.PHONY: matrix-unit-tests
matrix-unit-tests:
	.docker/run-tests.sh 3.5 matrix-unit-tests python setup.py test
	.docker/run-tests.sh 3.6 matrix-unit-tests python setup.py test
	.docker/run-tests.sh 3.7 matrix-unit-tests python setup.py test
	.docker/run-tests.sh 3.8 matrix-unit-tests python setup.py test

.PHONY: matrix-install
matrix-install:
	.docker/run-tests.sh 3.5 matrix-install pip install .
	.docker/run-tests.sh 3.6 matrix-install pip install .
	.docker/run-tests.sh 3.7 matrix-install pip install .
	.docker/run-tests.sh 3.8 matrix-install pip install .

.PHONY: matrix
matrix: matrix-unit-tests matrix-install
