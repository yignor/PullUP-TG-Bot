# 🏀 Общий парсер игр (game_parser.py)

## 📋 Описание

`game_parser.py` - централизованный модуль для парсинга игр и работы с результатами. Устраняет дублирование функционала между разными модулями проекта.

## 🔧 Функциональность

### Основные методы

#### `get_fresh_page_content()`
Получает свежий контент страницы letobasket.ru с обходом кеша.

```python
html_content = await game_parser.get_fresh_page_content()
```

#### `extract_current_date(page_text)`
Извлекает текущую дату из текста страницы.

```python
current_date = game_parser.extract_current_date(page_text)
```

#### `check_finished_games(html_content, current_date)`
Проверяет завершенные игры PullUP на странице.

```python
finished_games = game_parser.check_finished_games(html_content, current_date)
```

**Возвращает**: Список словарей с информацией о завершенных играх:
```python
[
    {
        'pullup_team': 'Pull Up',
        'opponent_team': 'Garde Marine',
        'pullup_score': 92,
        'opponent_score': 46,
        'date': '17.08.2025',
        'game_link': 'http://letobasket.ru/...'
    }
]
```

#### `extract_finished_game_info(row, html_content, current_date)`
Извлекает информацию о завершенной игре из строки таблицы.

```python
game_info = game_parser.extract_finished_game_info(row, html_content, current_date)
```

#### `parse_game_info(game_url)`
Парсит информацию об игре с страницы игры.

```python
game_info = await game_parser.parse_game_info(game_url)
```

**Возвращает**: Словарь с информацией об игре:
```python
{
    'time': '20.08.2025 20:30',
    'team1': 'Pull Up',
    'team2': 'Кирпичный Завод'
}
```

## 🎯 Использование

### Импорт модуля
```python
from game_parser import game_parser
```

### Пример использования
```python
# Получаем свежий контент
html_content = await game_parser.get_fresh_page_content()

# Извлекаем дату
page_text = soup.get_text()
current_date = game_parser.extract_current_date(page_text)

# Проверяем завершенные игры
finished_games = game_parser.check_finished_games(html_content, current_date)

# Парсим информацию об игре
game_info = await game_parser.parse_game_info(game_url)
```

## 🔍 Логика определения завершенных игр

Игра считается завершенной, если:
1. **Атрибуты HTML**: `js-period='4'` и `js-timer='0:00'`
2. **Текст**: содержит "4ч" или "4 ч"
3. **Счет**: присутствует полный счет в формате "NN:NN"

## 🛡️ Обработка ошибок

Все методы включают обработку ошибок и возвращают `None` в случае проблем:
- Ошибки сети
- Ошибки парсинга HTML
- Отсутствие данных на странице

## 📊 Логирование

Модуль использует стандартное логирование Python:
```python
import logging
logger = logging.getLogger(__name__)
```

## 🔗 Интеграция с другими модулями

### Используется в:
- `game_results_monitor.py` - мониторинг результатов игр
- `pullup_notifications.py` - уведомления PullUP
- `birthday_bot.py` - основной бот
- `letobasket_monitor.py` - мониторинг letobasket.ru

### Зависимости:
- `aiohttp` - HTTP-клиент
- `beautifulsoup4` - парсинг HTML
- `re` - регулярные выражения

## 🧪 Тестирование

```bash
# Тест парсера игр
python tests/test_game_results_monitor.py

# Тест уведомлений (использует парсер)
python tests/test_notifications.py
```

## 📈 Преимущества централизации

- ✅ **Единая логика**: Все модули используют одинаковые алгоритмы парсинга
- ✅ **Легкость обновления**: Изменения в одном месте
- ✅ **Консистентность**: Одинаковое поведение во всех модулях
- ✅ **Тестируемость**: Можно тестировать парсинг отдельно
- ✅ **Поддерживаемость**: Меньше дублированного кода
