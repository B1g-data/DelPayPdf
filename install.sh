#!/bin/bash

# Переменные
REPO_URL="https://github.com/B1g-data/DelPayPdf.git"  # Замените на URL репозитория
TARGET_DIR="/opt/DelPayPdf"
ENV_FILE="${TARGET_DIR}/.env"
CONTAINER_NAME="DelPayPdf"
IMAGE_NAME="DelPayPdf_image"  # Имя Docker-образа

# 1. Проверка наличия каталога и его создание, если отсутствует
if [ ! -d "$TARGET_DIR" ]; then
  echo "Папка $TARGET_DIR не существует. Создаём её..."
  mkdir -p "$TARGET_DIR"
else
  echo "Папка $TARGET_DIR уже существует."
fi

# 2. Клонирование репозитория
if [ -d "$TARGET_DIR/.git" ]; then
  echo "Папка $TARGET_DIR уже содержит репозиторий. Обновление содержимого..."
  git -C "$TARGET_DIR" pull || { echo "Ошибка обновления репозитория"; exit 1; }
else
  echo "Клонируем репозиторий..."
  git clone "$REPO_URL" "$TARGET_DIR" || { echo "Ошибка клонирования репозитория"; exit 1; }
fi

# 3. Проверка наличия .env файла и сохранённых переменных
if [ -f "$ENV_FILE" ]; then
  # Чтение сохраненных данных из .env
  source "$ENV_FILE"
  echo "Найден файл .env. Используем сохраненные значения."
else
  # Запрос данных у пользователя, если .env файл не существует
  echo "Файл .env не найден. Требуются данные от пользователя."

  # Цикл запроса токена, пока он не будет правильным
  while true; do
    read -p "Введите токен Telegram-бота: " TELEGRAM_BOT_TOKEN
    if validate_token_format "$TELEGRAM_BOT_TOKEN"; then
      echo "Формат токена правильный. Проверяем его..."
      if validate_telegram_token "$TELEGRAM_BOT_TOKEN"; then
        echo "Токен действителен!"
        break  # Прерываем цикл, если токен действителен
      else
        echo "Ошибка: Токен неверный или недействителен. Попробуйте снова."
      fi
    else
      echo "Ошибка: Токен имеет неверный формат. Попробуйте снова."
    fi
  done
fi

# 5. Сохранение в .env, если данные были введены
echo "TELEGRAM_BOT_TOKEN=$BOT_TOKEN" >> "$ENV_FILE"

echo "Файл .env успешно создан."

# 5. Сборка Docker-образа
cd "$TARGET_DIR" || { echo "Ошибка при переходе в директорию $TARGET_DIR"; exit 1; }
echo "Собираем Docker-образ..."
docker build -t "$IMAGE_NAME" . || { echo "Ошибка сборки Docker-образа"; exit 1; }

# 6. Остановка и удаление старого контейнера
if docker ps -a | grep -q "$CONTAINER_NAME"; then
  echo "Останавливаем и удаляем старый контейнер..."
  docker stop "$CONTAINER_NAME" || { echo "Ошибка остановки контейнера"; exit 1; }
  docker rm "$CONTAINER_NAME" || { echo "Ошибка удаления контейнера"; exit 1; }
fi

# 7. Запуск нового контейнера
echo "Запускаем новый контейнер..."
docker run -d --name "$CONTAINER_NAME" --env-file "$ENV_FILE" "$IMAGE_NAME" || { echo "Ошибка запуска контейнера"; exit 1; }

echo "Контейнер $CONTAINER_NAME успешно запущен."