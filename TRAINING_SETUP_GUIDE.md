# 🏀 Руководство по настройке системы тренировок

## 📋 Что нужно настроить для полноценной работы системы тренировок

### ✅ Уже настроено:
- ✅ Логика времени (воскресенье 10:00 по Москве)
- ✅ Отправка в топик "АНОНСЫ ТРЕНИРОВОК"
- ✅ Интеграция в GitHub Actions
- ✅ Все зависимости установлены

### 🔧 Что нужно настроить:

## 1. 📱 ID топика "АНОНСЫ ТРЕНИРОВОК"

**Переменная**: `ANNOUNCEMENTS_TOPIC_ID`

**Как получить**:
1. Добавьте бота в чат с топиками
2. Отправьте сообщение в топик "АНОНСЫ ТРЕНИРОВОК"
3. Перейдите по ссылке: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
4. Найдите `message_thread_id` в ответе

**Пример**: `ANNOUNCEMENTS_TOPIC_ID=123456789`

---

## 2. 🔐 Telegram Client API (для сбора результатов опросов)

### 2.1 Получение API ID и Hash
1. Перейдите на https://my.telegram.org/apps
2. Войдите в свой аккаунт Telegram
3. Создайте новое приложение или используйте существующее
4. Скопируйте `api_id` и `api_hash`

### 2.2 Настройка переменных
```bash
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+7XXXXXXXXXX
```

**Важно**: Номер телефона должен быть в международном формате

---

## 3. 📊 Google Sheets (для сохранения статистики)

### 3.1 Создание проекта в Google Cloud Console
1. Перейдите на https://console.cloud.google.com/
2. Создайте новый проект
3. Включите Google Sheets API
4. Создайте Service Account
5. Скачайте JSON файл с credentials

### 3.2 Создание Google таблицы
1. Создайте новую Google таблицу
2. Скопируйте ID из URL (часть между /d/ и /edit)
3. Предоставьте доступ Service Account email

### 3.3 Настройка переменных
```bash
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account","project_id":"..."}
SPREADSHEET_ID=your_spreadsheet_id_here
```

**Примечание**: `GOOGLE_SHEETS_CREDENTIALS` должен содержать весь JSON в одной строке

---

## 4. 🔧 Настройка в GitHub Secrets

Добавьте все переменные в GitHub Secrets:

1. Перейдите в Settings → Secrets and variables → Actions
2. Добавьте следующие секреты:

### Обязательные:
- `BOT_TOKEN`
- `CHAT_ID`
- `ANNOUNCEMENTS_TOPIC_ID`

### Для сбора результатов опросов:
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_PHONE`

### Для Google Sheets:
- `GOOGLE_SHEETS_CREDENTIALS`
- `SPREADSHEET_ID`

---

## 5. 🧪 Тестирование

### 5.1 Тест создания опроса
```bash
python test_sunday_poll_creation.py
```

### 5.2 Тест сбора результатов
```bash
python test_sunday_polls.py
```

### 5.3 Полный тест системы
```bash
python test_training_polls_complete.py
```

---

## 6. 📅 Расписание работы

| День недели | Время по Москве | Действие |
|-------------|----------------|----------|
| Воскресенье | 10:00-10:29    | ✅ Создание опроса на неделю |
| Среда       | 9:00-9:29      | ✅ Сбор данных о посещаемости |
| Суббота     | 9:00-9:29      | ✅ Сбор данных о посещаемости |
| Последний день месяца | 9:00-9:29 | ✅ Генерация месячного отчета |

---

## 7. 🔍 Проверка работоспособности

### 7.1 Проверка переменных окружения
```bash
python check_current_settings.py
```

### 7.2 Проверка подключений
- ✅ Telegram Bot API
- ✅ Telegram Client API
- ✅ Google Sheets API

### 7.3 Проверка логики времени
- ✅ Московское время (UTC+3)
- ✅ Воскресные опросы в 10:00
- ✅ Сбор данных в среду/субботу 9:00

---

## 8. 🚨 Возможные проблемы

### 8.1 Telegram Client API
- **Проблема**: Ошибка авторизации
- **Решение**: Проверьте правильность API ID, Hash и номера телефона

### 8.2 Google Sheets
- **Проблема**: Ошибка доступа к таблице
- **Решение**: Предоставьте доступ Service Account email к таблице

### 8.3 Топики
- **Проблема**: Сообщения не отправляются в топик
- **Решение**: Проверьте правильность `ANNOUNCEMENTS_TOPIC_ID`

---

## 9. 📞 Поддержка

При возникновении проблем:
1. Проверьте логи GitHub Actions
2. Запустите тесты локально
3. Проверьте настройки переменных окружения

---

## ✅ Чек-лист настройки

- [ ] Настроен `ANNOUNCEMENTS_TOPIC_ID`
- [ ] Получены `TELEGRAM_API_ID` и `TELEGRAM_API_HASH`
- [ ] Настроен `TELEGRAM_PHONE`
- [ ] Создан проект в Google Cloud Console
- [ ] Настроены `GOOGLE_SHEETS_CREDENTIALS`
- [ ] Создана Google таблица и настроен `SPREADSHEET_ID`
- [ ] Все переменные добавлены в GitHub Secrets
- [ ] Протестирована система локально
- [ ] Проверена работа в GitHub Actions

После выполнения всех пунктов система тренировок будет полностью готова к работе! 🚀
