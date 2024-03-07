#!/bin/sh

set -eu

# Will install python version listed in .python-version file, if not installed yet
pyenv install --skip-existing

# Create and activate a virtual environment
python -m venv venv
. ./venv/bin/activate

# Install dbt & sqlfluff, and anything other python libs
pip install -r requirements.txt
