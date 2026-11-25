# syntax=docker/dockerfile:1
# Servicio: knowledge  ·  imagen: ghcr.io/help-chair/hc-knowledge
# Usa requirements.txt (generado con `make lock`) para no depender de uv al construir.

FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /build
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY . .
RUN python -m django collectstatic --settings=config.static_settings --noinput \
 && chown -R app:app /app
USER app
EXPOSE 8006
CMD ["gunicorn", "--config", "gunicorn.conf.py", "config.wsgi:application"]
