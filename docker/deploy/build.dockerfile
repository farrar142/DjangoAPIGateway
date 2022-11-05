FROM python:3.10-alpine

WORKDIR /usr/src/app
ENV PYTHONUNBUFFERED=0
COPY requirements.txt requirements.txt

RUN apk update
##dependeencies
RUN apk add --virtual build-deps gcc python3-dev musl-dev libc-dev libffi-dev\
    && apk add --no-cache mariadb-dev\
    && apk add jpeg-dev zlib-dev libjpeg
RUN pip3 install -r requirements.txt
RUN apk del build-deps