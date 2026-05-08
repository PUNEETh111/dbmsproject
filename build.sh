#!/usr/bin/env bash
# build.sh — Render Build Script (MySQL Edition)
# Runs during deployment to install Python dependencies
# MySQL connection is handled via environment variables:
#   MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

set -o errexit  # Exit on error

pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build complete! MySQL driver installed."
