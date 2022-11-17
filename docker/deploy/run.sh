# sh docker/celery.sh
echo yes | python3 manage.py collectstatic
python3 manage.py makemigrations --settings=base.settings
python3 manage.py migrate --settings=base.settings
uvicorn base.asgi:application --port 8000 --host 0.0.0.0