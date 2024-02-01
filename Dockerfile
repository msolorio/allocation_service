FROM python:3.9-slim-buster

ENV DOCKER_CONTAINER=true

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /src
COPY src/ /src/
RUN pip install -e /src
COPY tests/ /tests/

WORKDIR /src
ENV FLASK_APP=allocation/entrypoints/flask_app.py FLASK_DEBUG=1 PYTHONUNBUFFERED=1
CMD flask run --host=0.0.0.0 --port=80
# CMD flask run --help

# RUN mkdir -p /code
# COPY *.py /code/
# WORKDIR /code
# ENV FLASK_APP=entrypoints/flask_app.py FLASK_DEBUG=1 PYTHONUNBUFFERED=1
# CMD flask run --host=0.0.0.0 --port=80
