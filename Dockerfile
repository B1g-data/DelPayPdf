# Используем более легкий образ на основе Alpine
FROM python:3.11-alpine

# Устанавливаем необходимые библиотеки и очищаем кэш apt для уменьшения объема
RUN apk add --no-cache libmupdf-dev \
    && pip install --no-cache-dir --upgrade pip

# Создаем директорию для приложения
WORKDIR /app

# Копируем только необходимые файлы для установки зависимостей
COPY requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только нужные файлы приложения
COPY main.py /app/
COPY images /app/images/
COPY BOT_TOKEN.env /app/
COPY temp_files /app/

# Указываем команду для запуска бота
CMD ["python", "main.py"]