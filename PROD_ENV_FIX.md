# Исправление .env файла на продакшене

## Проблема
На продакшене возникают ошибки парсинга .env файла:
```
python-dotenv could not parse statement starting at line 5
python-dotenv could not parse statement starting at line 6
...
```

## Причина
JSON в переменной `GOOGLE_SHEETS_CREDENTIALS` содержит переносы строк и специальные символы, которые не правильно экранированы для файла `.env`.

## Решение

### Вариант 1: Автоматическое исправление
1. Загрузите скрипт `fix_env_format.py` на продакшен
2. Запустите: `python3 fix_env_format.py`
3. Скрипт автоматически исправит формат .env файла

### Вариант 2: Ручное исправление
1. Найдите строку с `GOOGLE_SHEETS_CREDENTIALS=`
2. Замените все переносы строк `\n` на `\\n`
3. Убедитесь, что вся строка находится на одной линии

### Пример исправления:
**Было:**
```
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account","project_id":"training-polls-bot","private_key":"-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCNTMOK3+ZJLOf3
RCaKaHOWl05YQh+10C8rF/OITzGaKhbxRYJu1HDyfeKRJFNoKilj22lm9+yesIGm
...
```

**Стало:**
```
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account","project_id":"training-polls-bot","private_key":"-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCNTMOK3+ZJLOf3\\nRCaKaHOWl05YQh+10C8rF/OITzGaKhbxRYJu1HDyfeKRJFNoKilj22lm9+yesIGm\\n...
```

## Проверка
После исправления запустите:
```bash
python3 training_polls_enhanced.py
```

Должны исчезнуть ошибки парсинга .env файла.

## Резервная копия
Скрипт автоматически создает резервную копию с именем `.env.backup.YYYYMMDD_HHMMSS`
