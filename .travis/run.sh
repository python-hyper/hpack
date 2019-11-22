#!/bin/bash

set -e
set -x

if [[ $TRAVIS_PYTHON_VERSION == pypy ]] || [[ $TRAVIS_PYTHON_VERSION == pypy3 ]]; then
    py.test test/
else
    coverage run -m py.test test/
    coverage report -m --fail-under 100
fi
