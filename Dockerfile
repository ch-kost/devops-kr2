FROM python:3.12-slim

WORKDIR /app

ARG APP_PORT=8001
ENV APP_PORT=${APP_PORT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser

COPY --chown=10001:10001 app.py gunicorn.conf.py ./
USER 10001:10001

EXPOSE ${APP_PORT}
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
