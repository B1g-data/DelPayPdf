#!/bin/bash

# Переменные
REPO_URL="https://github.com/B1g-data/DelPayPdf.git"  # Замените на URL репозитория
TARGET_DIR="/opt/DelPayPdf"
ENV_FILE="${TARGET_DIR}/.env"
CONTAINER_NAME="DelPayPdf"
IMAGE_NAME="DelPayPdf_image"  # Имя Docker-образа

# Функция проверки формата ID пользователя
validate_user_id() {
  local user_id=$1
  if [[ "$user_id" =~ ^[0-9]+$ ]] && [ "$user_id" -gt 0 ]; then
    return 0  # ID корректен
  else
    return 1  # Неверный ID
  fi
}

# Функция проверки существования пользователя через Telegram API
validate_user_exists() {
  local user_id=$1
  response=$(curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getChat?chat_id=$user_id")
  if [[ "$response" =~ "\"ok\":true" ]]; then
    return 0  # Пользователь существует
  else
    return 1  # Пользователь не найден или ошибка
  fi
}

# Функция проверки формата токена
validate_token_format() {
  local token=$1
  if [[ "$token" =~ ^[0-9]{9,15}:[A-Za-z0-9_-]{35,45}$ ]]; then
    return 0  # Токен соответствует формату
  else
    return 1  # Неверный формат
  fi
}

# Функция проверки действительности токена через Telegram API
validate_telegram_token() {
  local token=$1
  response=$(curl -s "https://api.telegram.org/bot$token/getMe")
  if [[ "$response" =~ "\"ok\":true" ]]; then
    return 0  # Токен действителен
  else
    return 1  # Токен неверный
  fi
}

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