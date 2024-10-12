# Use an official Python image from Docker Hub
FROM python:3.11-slim

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Create a working directory for your app
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Установка локали в Docker
RUN apt-get update && apt-get install -y locales \
    && echo "ru_RU.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen ru_RU.UTF-8 \
    && update-locale LANG=ru_RU.UTF-8

# Установим переменные окружения для работы с локалью
ENV LANG=ru_RU.UTF-8 \
    LANGUAGE=ru_RU:ru \
    LC_ALL=ru_RU.UTF-8

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Создаем директорию для загрузки и хранения изображений
RUN mkdir -p /app/images

# Copy the rest of the application code
COPY . .

# Set environment variables if necessary
ENV PYTHONUNBUFFERED=1

# Start the application
CMD ["python", "main.py"]