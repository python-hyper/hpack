.PHONY: publish test

publish:
	python setup.py sdist upload
	python setup.py bdist_wheel upload

test:
	py.test -n 4 --cov hyper test/
