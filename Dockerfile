FROM python:3.12-slim AS builder

ENV PIP_ROOT_USER_ACTION=ignore

RUN --mount=type=cache,target=/root/.cache \
    python -m pip install pdm

COPY pyproject.toml pdm.lock README.md src/ /app/

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache \
    pdm install --check --prod --no-editable

FROM python:3.12-slim AS runner

RUN useradd -m backend_posts_api

COPY --from=builder /app/.venv/ /app/.venv

USER backend_posts_api
EXPOSE 8000
CMD [ "/app/.venv/bin/uvicorn", "backend_posts_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
