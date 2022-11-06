FROM python:3.11-alpine as build

WORKDIR /opt/twitch-notifier
COPY requirements.txt /opt/twitch-notifier/

RUN apk add --no-cache gcc libc-dev &&\
    pip install --no-cache-dir --upgrade -r requirements.txt

FROM python:3.11-alpine

WORKDIR /opt/twitch-notifier
ENTRYPOINT python3 twitch-notifier/__init__.py

COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY twitch-notifier /opt/twitch-notifier/twitch-notifier
