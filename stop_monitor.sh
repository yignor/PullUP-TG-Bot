#!/bin/bash

# Скрипт для остановки мониторинга игр PullUP

echo "Остановка мониторинга игр PullUP..."

# Проверяем наличие PID файла
if [ ! -f "pullup_monitor.pid" ]; then
    echo "ОШИБКА: Файл pullup_monitor.pid не найден"
    exit 1
fi

# Читаем PID процесса
PID=$(cat pullup_monitor.pid)

# Проверяем, существует ли процесс
if ! ps -p $PID > /dev/null; then
    echo "Процесс с PID $PID не найден"
    rm -f pullup_monitor.pid
    exit 1
fi

# Останавливаем процесс
echo "Останавливаем процесс с PID: $PID"
kill $PID

# Ждем завершения процесса
sleep 2

# Проверяем, остановился ли процесс
if ps -p $PID > /dev/null; then
    echo "Принудительная остановка процесса..."
    kill -9 $PID
fi

# Удаляем PID файл
rm -f pullup_monitor.pid

echo "Мониторинг остановлен"
