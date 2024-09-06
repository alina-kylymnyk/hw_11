# Вибрати базовий образ
FROM python:3.9-slim

# Встановити робочу директорію
WORKDIR /app

# Скопіювати файл з залежностями
COPY requirements.txt .

# Встановити залежності
RUN pip install --no-cache-dir -r requirements.txt

# Скопіювати всі файли проєкту
COPY . .

# Вказати команду для запуску сервера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
