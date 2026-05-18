# ----------------------------------------------------------------------
# Dockerfile для FastAPI-застосунку Library API.
#
# Збирає мінімальний образ:
#   1) бере Python 3.11
#   2) ставить залежності з requirements.txt
#   3) копіює код застосунку
#   4) запускає uvicorn на 0.0.0.0:8000
# ----------------------------------------------------------------------
FROM python:3.11-slim

# Неблокуючий stdout — щоб логи одразу з'являлись у docker logs.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Спершу ставимо залежності — цей шар кешується поки requirements.txt не змінюється.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Тепер копіюємо код застосунку.
COPY . .

EXPOSE 8000

# Запуск продакшн-сервера. --host 0.0.0.0 обов'язково, щоб порт
# був доступний з-за меж контейнера.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
