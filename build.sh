#!/usr/bin/env bash
# build.sh — Render Build Script
# Runs during deployment to install dependencies

set -o errexit  # Exit on error

pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build complete!"
