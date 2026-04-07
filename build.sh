#!/bin/bash

echo "BUILD START"

if [ ! -f .env ] && [ -f .env-dist ]; then
    cp .env-dist .env
fi

# 1. Install dependencies (Critical step)
# Install into a local virtualenv because Vercel's system Python is managed.
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# 2. Run Migrations
# Use committed migrations only; deployment should not generate new migration files.
.venv/bin/python manage.py migrate --noinput

# 3. Collect Static Files
# Ensure your settings.py has STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_build')
.venv/bin/python manage.py collectstatic --noinput --clear

echo "BUILD END"
