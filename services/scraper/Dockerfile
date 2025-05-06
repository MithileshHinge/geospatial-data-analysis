FROM python:3.13-slim

# Install Poetry
RUN pip install "poetry==2.0.0"

# Copy tsg-libs
COPY lib/ /lib/

WORKDIR /services/scraper

# Copy poetry files
COPY services/scraper/pyproject.toml services/scraper/poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --all-extras --all-groups

# Copy app
COPY services/scraper/app/ app/

CMD ["python", "app/main.py"]