FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV SQLITE_PATH=/app/db.sqlite3 DEBUG=0 ALLOWED_HOSTS=* JWT_SECRET=changeme123 HOME=/tmp
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl wget jq ca-certificates iputils-ping \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSLo /usr/local/bin/kubectl \
      https://dl.k8s.io/release/v1.31.0/bin/linux/amd64/kubectl \
    && chmod +x /usr/local/bin/kubectl

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY .env.leaked /app/.env
RUN rm -f /app/.env

COPY . .
RUN rm -f /app/.env /app/.env.leaked

RUN mkdir -p /app/reports \
 && printf 'Q3 Financial Summary - Acme Corp\nRevenue: $4.2M | EBITDA: $1.1M\n' > /app/reports/report_1.txt \
 && printf 'Internal audit notes for Globex Inc\nFY review, restricted distribution.\n' > /app/reports/report_2.txt

RUN mkdir -p /opt/.sysdiag-7e3f9a2c4b1d8e5f

RUN useradd -r app && chown -R app:app /app && chown app:app /opt/.sysdiag-7e3f9a2c4b1d8e5f
USER app

EXPOSE 8000
CMD ["sh", "-c", "printf '%s\\n' \"$FLAG_F4\" > /app/flag.txt && printf '%s\\n' \"$FLAG_F9\" > /opt/.sysdiag-7e3f9a2c4b1d8e5f/flag.txt && python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py seed && gunicorn config.wsgi:application -b 0.0.0.0:8000"]
