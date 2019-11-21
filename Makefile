init:
	pip install -r requirements.txt

test:
	python setup.py test

test-e2e: init test
	python ruterstop/ --stop-id=6013 --min-eta=2 --direction=outbound

.PHONY: init test test-e2e
