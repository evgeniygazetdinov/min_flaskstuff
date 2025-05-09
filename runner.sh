#!/bin/bash

ETCD_ONLY=false
while getopts "e" opt; do
    case $opt in
        e) ETCD_ONLY=true ;;
        *) echo "Usage: $0 [-e] (run etcd only)" && exit 1 ;;
    esac
done

check_port() {
    lsof -i:$1 >/dev/null 2>&1
    return $?
}

free_port() {
    local port=$1
    if check_port $port; then
        echo "Freeing port $port..."
        pid=$(lsof -t -i:$port)
        if [ ! -z "$pid" ]; then
            kill -9 $pid
            sleep 1
        fi
    fi
}

cleanup() {
    echo "Stopping services..."
    docker compose -f local-compose.yml down
    exit 0
}

trap cleanup SIGINT SIGTERM

free_port 2379  # etcd
free_port 2380  # additional etcd port

if [ "$ETCD_ONLY" = false ]; then
    free_port 8000  # FastAPI
fi

echo "Starting etcd..."
docker compose -f local-compose.yml up -d
sleep 5

if [ "$ETCD_ONLY" = false ]; then
    echo "Starting FastAPI application..."
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
else
    echo "Etcd is running. Press Ctrl+C to stop"
    docker compose -f local-compose.yml logs -f etcd

fi