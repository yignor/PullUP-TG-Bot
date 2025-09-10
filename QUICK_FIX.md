# Быстрое исправление .env файла на продакшене

## Команды для выполнения:

```bash
# 1. Перейти в директорию проекта
cd /path/to/telegram-birthday-bot

# 2. Запустить скрипт исправления
python3 fix_env_format.py

# 3. Проверить, что исправления работают
python3 training_polls_enhanced.py
```

## Что делает скрипт:
- ✅ Создает резервную копию .env файла
- ✅ Исправляет формат JSON в GOOGLE_SHEETS_CREDENTIALS
- ✅ Проверяет, что все переменные окружения загружаются
- ✅ Показывает результат проверки

## Ожидаемый результат:
После исправления должны исчезнуть ошибки:
```
python-dotenv could not parse statement starting at line 5
python-dotenv could not parse statement starting at line 6
...
```

И появиться:
```
✅ Google Sheets подключен успешно
✅ Бот инициализирован
```
