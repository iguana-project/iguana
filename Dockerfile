FROM python:3
 ENV PYTHONUNBUFFERED 1
 RUN mkdir /code
 WORKDIR /code
 ADD . /code/
 RUN pip install -r requirements/production.req
 RUN adduser --disabled-password --gecos '' iguana
