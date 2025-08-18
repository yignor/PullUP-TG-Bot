# 📊 НАСТРОЙКА GOOGLE SHEETS ДЛЯ УПРАВЛЕНИЯ ИГРОКАМИ

## 🎯 Цель

Перенести данные игроков (имена, дни рождения, Telegram ID) из кода в Google Sheets для:
- ✅ **Безопасности** - данные не в открытом коде
- ✅ **Гибкости** - легко добавлять/удалять игроков
- ✅ **Централизации** - все данные в одном месте
- ✅ **Веб-интерфейса** - удобное управление через браузер

## 📋 Структура таблицы

### Лист "Игроки"

| Имя | Ник | Telegram ID | Дата рождения | Статус | Команда | Дата добавления | Примечания |
|-----|-----|-------------|---------------|--------|---------|-----------------|------------|
| Шахманов Максим | @max_shah | 123456789 | 2006-08-17 | Активный | Pull Up | 2025-08-18 | Мигрирован из кода |
| Иванов Иван | @ivan_ball | 987654321 | 1995-03-15 | Активный | Pull Up-Фарм | 2025-08-18 | - |

### Описание полей:

- **Имя** - полное имя игрока (обязательно)
- **Ник** - никнейм в Telegram (опционально)
- **Telegram ID** - ID пользователя в Telegram (опционально)
- **Дата рождения** - в формате YYYY-MM-DD или DD.MM.YYYY (обязательно)
- **Статус** - "Активный" или "Неактивный" (по умолчанию "Активный")
- **Команда** - "Pull Up" или "Pull Up-Фарм" (опционально)
- **Дата добавления** - автоматически заполняется
- **Примечания** - дополнительная информация (опционально)

## 🔧 Настройка Google Sheets API

### 1. Создание проекта в Google Cloud Console

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google Sheets API:
   - Перейдите в "APIs & Services" → "Library"
   - Найдите "Google Sheets API"
   - Нажмите "Enable"

### 2. Создание Service Account

1. Перейдите в "APIs & Services" → "Credentials"
2. Нажмите "Create Credentials" → "Service Account"
3. Заполните форму:
   - **Name**: `telegram-bot-service`
   - **Description**: `Service account for Telegram bot`
4. Нажмите "Create and Continue"
5. Пропустите шаги 2 и 3, нажмите "Done"

### 3. Создание ключа

1. В списке Service Accounts найдите созданный аккаунт
2. Нажмите на email аккаунта
3. Перейдите на вкладку "Keys"
4. Нажмите "Add Key" → "Create new key"
5. Выберите "JSON" и нажмите "Create"
6. Скачайте файл JSON

### 4. Настройка Google таблицы

1. Создайте новую Google таблицу или используйте существующую
2. Скопируйте ID таблицы из URL (часть между `/d/` и `/edit`)
3. Предоставьте доступ Service Account:
   - Нажмите "Share" в правом верхнем углу
   - Добавьте email Service Account (из JSON файла)
   - Дайте права "Editor"

## 🔑 Настройка переменных окружения

### 1. Добавьте в .env файл:

```bash
# Google Sheets
GOOGLE_SHEETS_CREDENTIALS='{"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"telegram-bot-service@your-project.iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/telegram-bot-service%40your-project.iam.gserviceaccount.com"}'
SPREADSHEET_ID=your_spreadsheet_id_here
```

### 2. Добавьте в GitHub Secrets:

- `GOOGLE_SHEETS_CREDENTIALS` - весь JSON из скачанного файла
- `SPREADSHEET_ID` - ID вашей Google таблицы

## 🚀 Использование

### 1. Тестирование подключения

```bash
python players_manager.py
```

### 2. Миграция существующих данных

```bash
python migrate_players_to_sheets.py
```

### 3. Тестирование системы дней рождения

```bash
python birthday_bot_google.py
```

## 📝 Примеры использования

### Добавление игрока через код:

```python
from players_manager import players_manager

# Добавить нового игрока
success = players_manager.add_player(
    name="Новый Игрок",
    birthday="1990-01-01",
    nickname="@new_player",
    telegram_id="123456789",
    team="Pull Up",
    notes="Новый игрок команды"
)
```

### Получение игроков:

```python
# Все игроки
all_players = players_manager.get_all_players()

# Только активные
active_players = players_manager.get_active_players()

# Именинники сегодня
birthday_players = players_manager.get_players_with_birthdays_today()

# Поиск по Telegram ID
player = players_manager.get_player_by_telegram_id("123456789")
```

## 🔄 Миграция с существующего кода

### 1. Обновите migrate_players_to_sheets.py:

```python
EXISTING_PLAYERS = [
    {"name": "Шахманов Максим", "birthday": "2006-08-17", "team": "Pull Up"},
    {"name": "Иванов Иван", "birthday": "1995-03-15", "team": "Pull Up-Фарм"},
    # Добавьте всех существующих игроков
]
```

### 2. Запустите миграцию:

```bash
python migrate_players_to_sheets.py
```

### 3. Замените birthday_bot.py на birthday_bot_google.py

### 4. Обновите github_actions_monitor.py:

```python
# Замените импорт
from birthday_bot_google import check_birthdays
```

## ✅ Преимущества нового подхода

1. **Безопасность** - данные не в коде
2. **Гибкость** - легко управлять через веб-интерфейс
3. **Масштабируемость** - можно добавить больше полей
4. **Версионность** - история изменений
5. **Доступность** - можно дать доступ команде
6. **Автоматизация** - можно добавить автоматические уведомления

## 🛠️ Дополнительные возможности

### Автоматические уведомления о новых игроках
### Статистика по командам
### Экспорт данных
### Интеграция с другими системами

---

**Статус**: 🟡 В разработке  
**Последнее обновление**: 18.08.2025
