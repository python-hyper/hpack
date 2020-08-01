.PHONY: publish sample_output

publish:
	rm -rf dist/
	python setup.py sdist bdist_wheel
	twine upload -s dist/*

sample_output:
	rm -rf hpack-test-case/
	git clone https://github.com/http2jp/hpack-test-case.git
	tox -e create_test_output -- hpack-test-case
