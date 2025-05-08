# ---------- Stage 1: build env ------------------------------------
FROM mambaorg/micromamba:latest AS builder

COPY services/etl/environment.yml /tmp/env.yml
RUN micromamba install -y -n base -f /tmp/env.yml \
  && micromamba clean --all --yes

# ---------- Stage 2: runtime --------------------------------------
FROM python:3.13-slim

# copy the conda env built above
COPY --from=builder /opt/conda /opt/conda
ENV PATH=/opt/conda/bin:$PATH \
    PYTHONUNBUFFERED=1

COPY lib/ /tmp/lib/
RUN /opt/conda/bin/pip install --no-cache-dir -e "/tmp/lib[db,s3]"

COPY services/etl/app/ /app/

COPY services/etl/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
