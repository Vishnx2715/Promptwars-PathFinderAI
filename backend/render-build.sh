#!/usr/bin/env bash
# Render build script

set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies (prefer binary wheels, no build isolation issues)
pip install --no-cache-dir --only-binary=:all: -r requirements.txt || \
pip install --no-cache-dir -r requirements.txt
