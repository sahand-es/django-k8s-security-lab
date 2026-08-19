FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SQLITE_PATH=/tmp/oncall.sqlite3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "rm -f \"$SQLITE_PATH\" && python manage.py migrate --noinput && python manage.py seed_challenge && python manage.py runserver --insecure 0.0.0.0:8000"]
