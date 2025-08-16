#!/bin/bash

# Скрипт для запуска мониторинга игр PullUP

echo "Запуск мониторинга игр PullUP..."

# Проверяем наличие переменных окружения
if [ -z "$BOT_TOKEN" ]; then
    echo "ОШИБКА: Не установлена переменная BOT_TOKEN"
    exit 1
fi

if [ -z "$CHAT_ID" ]; then
    echo "ОШИБКА: Не установлена переменная CHAT_ID"
    exit 1
fi

# Запускаем мониторинг в фоновом режиме
nohup python pullup_monitor.py > pullup_monitor.log 2>&1 &

# Сохраняем PID процесса
echo $! > pullup_monitor.pid

echo "Мониторинг запущен с PID: $(cat pullup_monitor.pid)"
echo "Логи записываются в файл: pullup_monitor.log"
echo ""
echo "Для остановки мониторинга выполните: ./stop_monitor.sh"
