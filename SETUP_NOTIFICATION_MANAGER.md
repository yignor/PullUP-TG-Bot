# 📢 Общий менеджер уведомлений (notification_manager.py)

## 📋 Описание

`notification_manager.py` - централизованный модуль для управления уведомлениями. Устраняет дублирование логики отправки уведомлений между разными модулями проекта и обеспечивает защиту от дублирования.

## 🔧 Функциональность

### Основные методы

#### `send_game_end_notification(game_info, game_url)`
Отправляет уведомление о завершении игры.

```python
await notification_manager.send_game_end_notification(game_info, game_url)
```

**Параметры:**
- `game_info` - словарь с информацией об игре
- `game_url` - ссылка на игру

#### `send_game_start_notification(game_info, game_url)`
Отправляет уведомление о начале игры.

```python
await notification_manager.send_game_start_notification(game_info, game_url)
```

#### `send_game_result_notification(game_info, poll_results=None)`
Отправляет уведомление о результате игры с анализом голосований.

```python
await notification_manager.send_game_result_notification(game_info, poll_results)
```

**Параметры:**
- `game_info` - словарь с информацией об игре
- `poll_results` - результаты голосования (опционально)

#### `send_morning_notification(games, date)`
Отправляет утреннее уведомление о предстоящих играх.

```python
await notification_manager.send_morning_notification(games, date)
```

**Параметры:**
- `games` - список игр
- `date` - дата в формате 'YYYY-MM-DD'

## 🛡️ Защита от дублирования

Модуль автоматически отслеживает отправленные уведомления и предотвращает дублирование:

### Отслеживаемые уведомления:
- `sent_game_end_notifications` - уведомления о завершении игр
- `sent_game_start_notifications` - уведомления о начале игр  
- `sent_game_result_notifications` - уведомления о результатах
- `sent_morning_notifications` - утренние уведомления

### Уникальные идентификаторы:
- **Завершение игры**: `game_end_{date}_{opponent_team}`
- **Начало игры**: `game_start_{game_url}`
- **Результат игры**: `game_result_{date}_{opponent_team}`
- **Утреннее уведомление**: `morning_{date}`

## 📊 Форматы уведомлений

### Уведомление о завершении игры
```
🏀 Игра против Garde Marine закончилась
🏆 Счет: Pull Up 92 : 46 Garde Marine (победили)
📅 Дата: 17.08.2025
📊 Ссылка на протокол: [тут](http://letobasket.ru/...)
```

### Уведомление о результате с голосованиями
```
🏀 Игра против Кирпичный Завод закончилась
🏆 Счет: Pull Up 78 : 56 Кирпичный Завод (победили)

📊 Статистика голосования:
✅ Готовы: 8
❌ Не готовы: 2
👨‍🏫 Тренер: 1
📈 Всего проголосовало: 11
🎯 Отличная готовность! (72.7%)

📅 Дата: 20.08.2025
```

### Утреннее уведомление
```
🏀 Сегодня игра против IT Basket
⏰ Время игры: 12.30
🔗 Ссылка на игру: [тут](http://letobasket.ru/...)

🏀 Сегодня игра против Маиле Карго
⏰ Время игры: 14.00
🔗 Ссылка на игру: [тут](http://letobasket.ru/...)
```

## 🎯 Использование

### Импорт модуля
```python
from notification_manager import notification_manager
```

### Пример использования
```python
# Уведомление о завершении игры
game_info = {
    'pullup_team': 'Pull Up',
    'opponent_team': 'Garde Marine',
    'pullup_score': 92,
    'opponent_score': 46,
    'date': '17.08.2025'
}
await notification_manager.send_game_end_notification(game_info, game_url)

# Уведомление о результате с голосованиями
poll_results = {
    'votes': {
        'ready': 8,
        'not_ready': 2,
        'coach': 1,
        'total': 11
    }
}
await notification_manager.send_game_result_notification(game_info, poll_results)
```

## 🔍 Анализ готовности

При наличии результатов голосования модуль автоматически анализирует готовность команды:

- **🎯 Отличная готовность** (≥80%): Отличная готовность команды
- **👍 Хорошая готовность** (60-79%): Хорошая готовность команды
- **⚠️ Средняя готовность** (40-59%): Средняя готовность команды
- **😕 Низкая готовность** (<40%): Низкая готовность команды

## 🛠️ Управление уведомлениями

### Очистка отслеживания (для тестирования)
```python
notification_manager.clear_notifications()
```

### Проверка статуса уведомлений
```python
# Проверяем, было ли отправлено уведомление
notification_id = f"game_end_{date}_{opponent_team}"
if notification_id in notification_manager.sent_game_end_notifications:
    print("Уведомление уже отправлено")
```

## 🔗 Интеграция с другими модулями

### Используется в:
- `game_results_monitor.py` - мониторинг результатов игр
- `pullup_notifications.py` - уведомления PullUP
- `birthday_bot.py` - основной бот
- `letobasket_monitor.py` - мониторинг letobasket.ru

### Зависимости:
- `telegram` - Telegram Bot API
- `os` - переменные окружения
- `logging` - логирование

## 🧪 Тестирование

```bash
# Тест уведомлений
python tests/test_notifications.py

# Тест результатов игр
python tests/test_game_results_monitor.py

# Финальный тест
python tests/final_test.py
```

## 📈 Преимущества централизации

- ✅ **Единый формат**: Все уведомления имеют одинаковый стиль
- ✅ **Защита от дублирования**: Автоматическое отслеживание
- ✅ **Легкость обновления**: Изменения в одном месте
- ✅ **Консистентность**: Одинаковое поведение во всех модулях
- ✅ **Анализ готовности**: Автоматический анализ голосований
- ✅ **Поддерживаемость**: Меньше дублированного кода

## ⚙️ Настройка

### Переменные окружения
```bash
BOT_TOKEN=your_telegram_bot_token
CHAT_ID=your_chat_id
```

### Инициализация
Модуль автоматически инициализируется при импорте:
```python
from notification_manager import notification_manager
# notification_manager готов к использованию
```
