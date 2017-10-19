FROM python:3
 ENV PYTHONUNBUFFERED 1
 RUN mkdir /code
 WORKDIR /code
 ADD . /code/
 RUN pip install -r requirements/production.req
 RUN apt-get update
 RUN apt-get install -y postgresql-client
 RUN adduser --disabled-password --gecos '' iguana
