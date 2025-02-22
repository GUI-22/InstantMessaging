#!/bin/sh
python3 manage.py makemigrations user friend message conversation
python3 manage.py migrate

# Run with uWSGI
# uwsgi --module=imBackend.wsgi:application \
#     --env DJANGO_SETTINGS_MODULE=imBackend.settings \
#     --master \
#     --http=0.0.0.0:80 \
#     --processes=5 \
#     --harakiri=20 \
#     --max-requests=5000 \
#     --vacuum

daphne imBackend.asgi:application -b 0.0.0.0 -p 80