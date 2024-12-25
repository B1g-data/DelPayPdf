# Используем официальный Python 3.11 образ на основе Debian
FROM python:3.11-slim

# Устанавливаем необходимые библиотеки через apt
RUN apt-get update && apt-get install -y \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем директорию для приложения
WORKDIR /app

# Копируем только необходимые файлы для установки зависимостей
COPY requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только нужные файлы приложения
COPY main.py /app/
COPY images /app/images/
COPY .env /app/
COPY temp_files /app/temp_files 

# Указываем команду для запуска бота
CMD ["python", "main.py"]