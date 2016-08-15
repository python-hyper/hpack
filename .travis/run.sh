#!/bin/bash

set -e
set -x

if [[ $TRAVIS_PYTHON_VERSION == pypy ]]; then
    py.test test/
else
    coverage run py.test test/
    coverage report -m --fail-under 100
fi