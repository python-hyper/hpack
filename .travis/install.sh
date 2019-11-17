#!/bin/bash

set -e
set -x

pip install .
pip install -U -r test_requirements.txt
pip install flake8

