FROM python:3.11-slim

WORKDIR /app

# Спершу — лише requirements, щоб скористатись Docker layer cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Тепер — весь код
COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 5000

# Запуск Flask-застосунку
CMD ["python", "main.py"]
