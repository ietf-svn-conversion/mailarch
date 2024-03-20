#!/bin/bash

# append path
export PYTHONPATH="$PYTHONPATH:/workspace/backend"

# set log dir for container
export LOG_DIR="/data"

# Copy temp settings
cp build/app/settings_collectstatics.py backend/mlarchive/settings/

# Install Python dependencies
pip --disable-pip-version-check --no-cache-dir install -r requirements.txt

# Collect statics
backend/manage.py collectstatic --settings=mlarchive.settings.settings_collectstatics

# Delete temp local settings
rm backend/mlarchive/settings/settings_collectstatics.py
