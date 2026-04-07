#!/bin/bash

echo "BUILD START"

if [ ! -f .env ] && [ -f .env-dist ]; then
    cp .env-dist .env
fi

# 1. Install dependencies (Critical step)
# Use python3 or python3.9 depending on your Vercel Python runtime
python3 -m pip install -r requirements.txt

# 2. Run Migrations
# We use 'python3 manage.py' to ensure it uses the environment where we just installed Django
python3 manage.py makemigrations --noinput
python3 manage.py migrate --noinput

# 3. Collect Static Files
# Ensure your settings.py has STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_build')
python3 manage.py collectstatic --noinput --clear

echo "BUILD END"
