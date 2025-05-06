# ---- base image with Poetry ----
FROM python:3.13-slim

ENV POETRY_VERSION=2.0.0 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# copy tsg-libs
COPY lib/ /lib/

WORKDIR /services/api

# copy Poetry files
COPY services/api/pyproject.toml services/api/poetry.lock* ./

# install dependencies (no dev / no local venv)
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --all-extras --all-groups

# copy the actual source
COPY services/api/app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  