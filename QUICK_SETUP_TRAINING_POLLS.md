# Быстрая настройка системы опросов тренировок

## 🎯 Что нужно настроить

Для полной функциональности опросов тренировок требуется:

1. **Telegram Bot API** (уже настроен)
2. **Google Sheets API** (для сохранения данных)
3. **Telegram Client API** (для получения результатов опросов)

## 📋 Пошаговая настройка

### 1. Google Sheets API

Следуйте инструкции в `GOOGLE_SHEETS_SETUP.md`:

```bash
# Установите переменные окружения в Railway:
GOOGLE_SHEETS_CREDENTIALS={"type": "service_account", ...}
SPREADSHEET_ID=your_spreadsheet_id
```

### 2. Telegram Client API

Следуйте инструкции в `TELEGRAM_CLIENT_SETUP.md`:

```bash
# Установите переменные окружения в Railway:
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE=+79001234567
```

### 3. Дополнительные переменные

```bash
# ID топика "АНОНСЫ ТРЕНИРОВОК"
ANNOUNCEMENTS_TOPIC_ID=123
```

## 🧪 Тестирование

### Поэтапное тестирование:

```bash
# 1. Тест Google Sheets
python test_google_sheets.py

# 2. Тест Telegram Client API
python poll_results_handler.py

# 3. Тест создания опросов
python test_polls.py

# 4. Тест поиска последнего опроса
python test_latest_poll.py

# 5. Комплексный тест
python test_training_polls_complete.py
```

## ⏰ Расписание работы

### Автоматические действия:

- **Воскресенье 9:00** - Создание опроса на неделю
- **Среда 9:00** - Сбор данных о посещаемости из последнего опроса (воскресенья)
- **Суббота 9:00** - Сбор данных о посещаемости из последнего опроса (воскресенья)
- **Последний день месяца 9:00** - Генерация отчета

### Ручное тестирование:

```bash
# Создать опрос сейчас
python -c "
import asyncio
from training_polls import TrainingPollsManager
async def test():
    manager = TrainingPollsManager()
    await manager.create_weekly_training_poll()
asyncio.run(test())
"
```

## 📊 Структура данных

### Google Sheets:

| Дата | День недели | Тренировка | Участники | Количество |
|------|-------------|------------|-----------|------------|
| 2024-01-15 | Вторник | Вторник СШОР 19:00 | Игрок1, Игрок2 | 2 |
| 2024-01-17 | Среда | Среда 550 школа 19:00 | Игрок2, Игрок3 | 2 |

### Месячный отчет:

```
📊 ОТЧЕТ ПО ТРЕНИРОВКАМ ЗА ЯНВАРЬ 2024

🏀 Всего тренировок: 12
👥 Всего участников: 15

🏆 Самые активные участники:
  Игрок1: 8 тренировок
  Игрок2: 7 тренировок
  Игрок3: 6 тренировок

📉 Менее активные участники:
  Игрок4: 2 тренировки
  Игрок5: 1 тренировка
```

## 🔧 Устранение неполадок

### Частые проблемы:

1. **"GOOGLE_SHEETS_CREDENTIALS не настроен"**
   - Следуйте `GOOGLE_SHEETS_SETUP.md`

2. **"Telegram Client API не настроен"**
   - Следуйте `TELEGRAM_CLIENT_SETUP.md`

3. **"Опросы не найдены"**
   - Проверьте, что опросы созданы в правильном топике
   - Убедитесь, что вопрос содержит "Тренировки на неделе"

4. **"Ошибка авторизации Telegram"**
   - Проверьте правильность номера телефона
   - Введите код подтверждения при первом запуске

## 🚀 Развертывание на Railway

### 1. Обновите зависимости:

```bash
# requirements.txt уже содержит все необходимые библиотеки
pip install -r requirements.txt
```

### 2. Настройте переменные окружения в Railway:

```
BOT_TOKEN=your_bot_token
CHAT_ID=your_chat_id
ANNOUNCEMENTS_TOPIC_ID=your_topic_id
GOOGLE_SHEETS_CREDENTIALS=your_credentials_json
SPREADSHEET_ID=your_spreadsheet_id
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=your_phone_number
```

### 3. Настройте cron:

```
Command: python birthday_bot_simple.py
Schedule: */30 * * * *
```

## ✅ Проверка работоспособности

После настройки всех компонентов:

1. **Создайте тестовый опрос** вручную
2. **Проголосуйте** за несколько вариантов
3. **Запустите сбор данных** вручную
4. **Проверьте Google Sheets** - данные должны появиться
5. **Сгенерируйте отчет** - должен создаться месячный отчет

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи в Railway Dashboard
2. Запустите тесты: `python test_training_polls_complete.py`
3. Проверьте переменные окружения
4. Убедитесь, что все API ключи корректны

## 🎉 Готово!

После настройки система будет автоматически:

- ✅ Создавать опросы каждое воскресенье
- ✅ Собирать данные о посещаемости
- ✅ Сохранять статистику в Google Sheets
- ✅ Генерировать месячные отчеты
