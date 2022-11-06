# sh docker/celery.sh
echo yes | python3 manage.py collectstatic
python3 manage.py migrate --settings=base.settings
uwsgi --env DJANGO_SETTINGS_MODULE=base.settings --ini uwsgi.local.ini