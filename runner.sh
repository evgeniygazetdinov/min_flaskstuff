#!/bin/bash

# Функция для очистки при выходе
cleanup() {
    echo "Останавливаем сервисы..."
    docker compose -f local-compose.yml down
    exit 0
}

# Перехват сигнала прерывания
trap cleanup SIGINT SIGTERM

# Запуск etcd
echo "Запускаем etcd..."
docker compose -f local-compose.yml up -d

# Ждем, пока etcd полностью запустится
sleep 5

# Запуск FastAPI приложения
echo "Запускаем FastAPI приложение..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000
