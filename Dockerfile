# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_DEBUG=0 \
    WEB_CONCURRENCY=3

WORKDIR /app

RUN useradd --create-home --uid 1000 app && chown app:app /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=app:app . .
USER app

# Static files are baked into the image and served by WhiteNoise.
# The placeholder key only lets settings load; it isn't used at runtime.
RUN DJANGO_SECRET_KEY=collectstatic-only python manage.py collectstatic --noinput

EXPOSE 8000

# Apply migrations, then serve. PORT is honoured for hosts that assign one;
# gunicorn reads its worker count from WEB_CONCURRENCY.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --access-logfile -"]
