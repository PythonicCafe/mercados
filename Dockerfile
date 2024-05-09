FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED 1
ARG DEV_BUILD
WORKDIR /app

RUN apt update \
  && apt upgrade -y \
  && apt install -y aria2 build-essential python3-dev wget \
  && apt purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt clean \
  && rm -rf /var/lib/apt/lists/*

RUN addgroup --gid ${GID:-1000} python \
  && adduser --disabled-password --gecos "" --home /app --uid ${UID:-1000} --gid ${GID:-1000} python \
  && chown -R python:python /app

COPY requirements.txt /app/
COPY requirements-development.txt /app/
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -r /app/requirements-development.txt

COPY . /app/
