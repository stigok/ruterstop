ARG PYTHON_VERSION

# Base
FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=10
WORKDIR /opt/app

# Build
FROM base as build

ARG POETRY_VERSION
ENV POETRY_VERSION=${POETRY_VERSION:-1.1.5}
RUN pip install "poetry==$POETRY_VERSION"

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.in-project true \
 && poetry install --no-interaction --no-ansi --no-root

# Runtime
FROM base
ENV PYTHONPATH=/opt/app/.venv \
    PATH="/opt/app/.venv/bin:${PATH}" \
    TZ=Europe/Oslo
COPY . .
COPY --from=build /opt/app/.venv ./.venv
ENTRYPOINT ["python", "-m"]
