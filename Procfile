web: python manage.py migrate --noinput && gunicorn resume_builder.wsgi:application --workers 2 --timeout 120 --bind 0.0.0.0:$PORT
