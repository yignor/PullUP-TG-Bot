# 🏀 Чек-лист настройки системы тренировок

## ✅ Что уже настроено:
- ✅ Логика времени (воскресенье 10:00 по Москве)
- ✅ Отправка в топик "АНОНСЫ ТРЕНИРОВОК"
- ✅ Интеграция в GitHub Actions
- ✅ Все зависимости установлены
- ✅ **ID топика "АНОНСЫ ТРЕНИРОВОК" настроен (ID: 26)**

## 🔧 Что нужно настроить:

### 1. 📱 ID топика "АНОНСЫ ТРЕНИРОВОК"
- [x] Получить `ANNOUNCEMENTS_TOPIC_ID` ✅ (ID: 26)
- [x] Добавить в GitHub Secrets ✅

### 2. 🔐 Telegram Client API
- [ ] Получить `TELEGRAM_API_ID` с https://my.telegram.org/apps
- [ ] Получить `TELEGRAM_API_HASH` с https://my.telegram.org/apps
- [ ] Настроить `TELEGRAM_PHONE` (формат: +7XXXXXXXXXX)
- [ ] Добавить все в GitHub Secrets

### 3. 📊 Google Sheets
- [ ] Создать проект в Google Cloud Console
- [ ] Включить Google Sheets API
- [ ] Создать Service Account
- [ ] Скачать JSON credentials
- [ ] Создать Google таблицу
- [ ] Настроить `GOOGLE_SHEETS_CREDENTIALS`
- [ ] Настроить `SPREADSHEET_ID`
- [ ] Добавить в GitHub Secrets

### 4. 🧪 Тестирование
- [x] Протестировать создание опроса ✅
- [ ] Протестировать сбор результатов
- [ ] Проверить работу в GitHub Actions

## 📅 Расписание работы:
- **Воскресенье 10:00** - Создание опроса на неделю
- **Среда 9:00** - Сбор данных о посещаемости
- **Суббота 9:00** - Сбор данных о посещаемости
- **Последний день месяца 9:00** - Генерация отчета

## 🚨 Критические переменные:
```
ANNOUNCEMENTS_TOPIC_ID=26 ✅
TELEGRAM_API_ID=your_telegram_api_id_here
TELEGRAM_API_HASH=your_telegram_api_hash_here
TELEGRAM_PHONE=+7XXXXXXXXXX
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account",...}
SPREADSHEET_ID=your_google_spreadsheet_id_here
```

**Прогресс: 1/3 компонентов настроено!** 🚀
