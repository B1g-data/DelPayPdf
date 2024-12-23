# Используем официальный Python 3.11 образ
FROM python:3.11-slim

# Устанавливаем необходимые библиотеки
RUN apt-get update && apt-get install -y \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем директорию для приложения
WORKDIR /app

# Копируем локальные файлы в контейнер
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем папку с изображениями в контейнер
COPY images /app/images/

# Копируем токен
COPY BOT_TOKEN.env /app/

# Указываем команду для запуска бота
CMD ["python", "tkp-del-pay-0.6.py"]