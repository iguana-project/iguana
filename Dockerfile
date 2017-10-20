FROM python:3
 ENV PYTHONUNBUFFERED 1
 RUN mkdir /code
 WORKDIR /code
 ADD . /code/
 RUN mkdir -p /var/lib/iguana/settings && cp /code/docker/settings.json /var/lib/iguana/settings/settings.json
 RUN pip install -r requirements/production.req
 RUN apt-get update
 RUN apt-get install -y postgresql-client
 RUN adduser --disabled-password --gecos '' iguana
