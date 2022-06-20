FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED 1
ARG DEV_BUILD
WORKDIR /app

RUN apt update \
  && apt upgrade -y \
  && apt install -y aria2 build-essential python3-dev wget \
  && apt purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt clean \
  && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -U pip

COPY requirements.txt /app/
COPY requirements-development.txt /app/
RUN pip install --no-cache-dir -r /app/requirements-development.txt

COPY . /app/
