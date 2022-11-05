# sh docker/celery.sh
python3 manage.py migrate --settings=base.settings
uwsgi --env DJANGO_SETTINGS_MODULE=base.settings --ini uwsgi.local.ini