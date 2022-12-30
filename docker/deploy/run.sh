# sh docker/celery.sh
echo yes | python3 manage.py collectstatic
python3 manage.py migrate --settings=base.settings
uvicorn base.asgi:application --port 9999 --host 0.0.0.0 --workers 4 --lifespan off