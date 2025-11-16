FROM python:3.12-slim AS dev

COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock /app/
RUN uv sync


FROM dev AS prod

COPY . /app/
RUN uv run python manage.py collectstatic --noinput
