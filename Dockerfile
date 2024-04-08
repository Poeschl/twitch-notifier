FROM python:3.11-slim-bookworm as build

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1
WORKDIR /opt/twitch-notifier

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

FROM python:3.11-slim-bookworm

ENV VIRTUAL_ENV=/opt/twitch-notifier/.venv \
    PATH="/opt/twitch-notifier/.venv/bin:$PATH"

WORKDIR /opt/twitch-notifier
ENTRYPOINT python -u twitch-notifier/__init__.py

COPY --from=build ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY twitch-notifier ./twitch-notifier
