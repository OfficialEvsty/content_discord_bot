FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY requirements.txt .

# Установка зависимостей
RUN python -m venv venv \
    && . venv/bin/activate \
    && pip install -r requirements.txt

COPY . .

# Запуск приложения
CMD ["python", "main.py"]