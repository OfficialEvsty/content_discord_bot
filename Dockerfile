FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY . .

# Установка зависимостей
RUN python -m venv venv \
    && . venv/bin/activate \
    && pip install -r requirements.txt

# Запуск приложения
CMD ["python", "main.py"]