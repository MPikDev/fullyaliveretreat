release: python manage.py migrate --noinput
web: gunicorn personal_code.wsgi --workers 3 --timeout 30 --access-logfile - --error-logfile -
