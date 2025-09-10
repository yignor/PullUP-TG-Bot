# СРОЧНОЕ ИСПРАВЛЕНИЕ НА ПРОДАКШЕНЕ

## Проблема:
```
python-dotenv could not parse statement starting at line 5
python-dotenv could not parse statement starting at line 6
...
```

## Решение:

### Вариант 1: Автоматическое исправление
```bash
cd /path/to/telegram-birthday-bot
python3 fix_env_secure.py
```

### Вариант 2: Ручное исправление
1. Откройте файл `.env`
2. Найдите строку с `GOOGLE_SHEETS_CREDENTIALS=`
3. Удалите эту строку полностью
4. Сохраните файл

### Вариант 3: Полная замена .env файла
```bash
# Создайте резервную копию
cp .env .env.backup

# Создайте новый .env файл
cat > .env << 'EOF'
# Продакшн настройки
BOT_TOKEN=7772125141:AAExr_nQDdoe54VunpckDwDcwTMTQMj8-sU
CHAT_ID=-1001535261616

# Google Sheets настройки
SPREADSHEET_ID=1evCO5a8q3w4EP9ydbVfDr92u_w33Mcq1B4Wt9q-9bkA
ANNOUNCEMENTS_TOPIC_ID=26

# Google credentials теперь в отдельном файле google_credentials.json
# GOOGLE_SHEETS_CREDENTIALS удален из .env для избежания проблем с парсингом

TELEGRAM_API_ID=13972664
TELEGRAM_API_HASH=8d34f77daef000887857cc70b2e88a4d
TELEGRAM_PHONE=+79257469550
TEST_CHAT_ID=your_test_chat_id_here
EOF
```

## Проверка:
```bash
python3 training_polls_enhanced.py
```

## Ожидаемый результат:
```
✅ Google credentials загружены из google_credentials.json
✅ Google Sheets подключен успешно
```

БЕЗ ошибок:
```
python-dotenv could not parse statement starting at line X
```

## Важно:
- Файл `google_credentials.json` должен существовать
- Все токены остаются в .env файле
- Только проблемная переменная `GOOGLE_SHEETS_CREDENTIALS` удаляется
