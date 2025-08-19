# 📁 Активные файлы системы

## 🏀 Система управления играми (основная)

### Основные модули:
- **`game_system_manager.py`** - Единый модуль управления всей системой игр
- **`run_game_system.py`** - Скрипт запуска системы игр

### Вспомогательные:
- **`game_parser.py`** - Парсер игр (используется в системе)
- **`game_results_monitor.py`** - Мониторинг результатов игр
- **`run_game_results_monitor.py`** - Скрипт запуска мониторинга результатов

## 🎯 Система опросов по тренировкам

### Основные модули:
- **`training_polls_enhanced.py`** - Улучшенная система опросов по тренировкам
- **`run_training_polls.py`** - Скрипт запуска опросов по тренировкам

### Вспомогательные:
- **`schedule_poll_results.py`** - Обработка результатов опросов
- **`run_schedule_polls.py`** - Скрипт запуска опросов по расписанию

## 🎂 Система уведомлений о днях рождения

### Основные модули:
- **`birthday_notifications.py`** - Система уведомлений о днях рождения
- **`run_birthday_notifications.py`** - Скрипт запуска уведомлений

## 📊 Система сбора данных

### Основные модули:
- **`scheduled_poll_collector.py`** - Сборщик данных опросов
- **`run_scheduled_collection.py`** - Скрипт запуска сбора данных
- **`collect_corrected_poll_results.py`** - Сбор исправленных результатов
- **`collect_detailed_poll_results.py`** - Сбор детальных результатов
- **`collect_poll_results.py`** - Основной сборщик результатов

### Вспомогательные:
- **`check_real_poll_data.py`** - Проверка реальных данных опросов
- **`collect_tuesday_data.py`** - Сбор данных по вторникам
- **`create_and_track_poll.py`** - Создание и отслеживание опросов
- **`create_and_track_simple.py`** - Упрощенное создание опросов

## 👥 Управление игроками

### Основные модули:
- **`players_manager.py`** - Управление игроками
- **`find_player_by_telegram_id.py`** - Поиск игрока по Telegram ID
- **`update_player_name_in_sheet.py`** - Обновление имен игроков

## 🔧 Вспомогательные модули

### Боты и уведомления:
- **`bot_wrapper.py`** - Обертка для бота
- **`bot_poll_results.py`** - Результаты опросов бота
- **`send_success_notification.py`** - Уведомления об успехе
- **`send_failure_notification.py`** - Уведомления об ошибках

### Тестирование и отладка:
- **`test_training_data_collection.py`** - Тест сбора данных тренировок
- **`simple_topic_send.py`** - Простая отправка в топик
- **`list_all_topics.py`** - Список всех топиков
- **`get_topic_id.py`** - Получение ID топика

## 📋 GitHub Actions Workflows

### Активные workflows:
- **`game_announcements.yml`** - Система управления играми (10:00 МСК)
- **`training_polls_enhanced.yml`** - Опросы по тренировкам
- **`training_polls.yml`** - Основные опросы по тренировкам
- **`birthday_notifications.yml`** - Уведомления о днях рождения
- **`test_birthday_system.yml`** - Тест системы дней рождения
- **`schedule_polls.yml`** - Опросы по расписанию
- **`pullup_monitor.yml`** - Мониторинг PullUP
- **`game_results_monitor.yml`** - Мониторинг результатов игр

## 📄 Документация

### Основная документация:
- **`FINAL_SYSTEM_SETUP.md`** - Полная настройка системы игр
- **`GITHUB_SECRETS_SETUP.md`** - Настройка GitHub Secrets
- **`README.md`** - Основная документация проекта

### Отчеты:
- **`ATTENDANCE_COLLECTION_SOLUTION.md`** - Решение сбора посещаемости
- **`REAL_DATA_COLLECTION_REPORT.md`** - Отчет о сборе реальных данных
- **`SCHEDULED_DATA_COLLECTION_REPORT.md`** - Отчет о запланированном сборе
- **`REAL_DATA_SOLUTION_REPORT.md`** - Решение реальных данных
- **`CORRECTED_TRAINING_SHEET_REPORT.md`** - Отчет об исправлении таблицы
- **`DETAILED_POLL_RESULTS_REPORT.md`** - Отчет о детальных результатах
- **`POLL_RESULTS_COLLECTION_REPORT.md`** - Отчет о сборе результатов
- **`TRAINING_POLLS_SETUP_REPORT.md`** - Отчет о настройке опросов
- **`WORKFLOW_FIX_REPORT.md`** - Отчет об исправлении workflows
- **`SCHEDULE_CHECK_REPORT.md`** - Отчет о проверке расписания
- **`REPOSITORY_CLEANUP_REPORT.md`** - Отчет об очистке репозитория
- **`GITHUB_SYNC_REPORT.md`** - Отчет о синхронизации GitHub

## 📊 JSON файлы (данные)

### История и результаты:
- **`game_polls_history.json`** - История опросов по играм
- **`game_day_announcements.json`** - История анонсов игр
- **`game_announcements.json`** - Анонсы игр
- **`scheduled_poll_results.json`** - Результаты запланированных опросов
- **`player_name_update_info.json`** - Информация об обновлении имен
- **`found_player_info.json`** - Информация о найденных игроках
- **`real_poll_votes.json`** - Голоса реальных опросов
- **`sunday_training_poll_info.json`** - Информация о воскресных тренировках
- **`simple_poll_info.json`** - Информация о простых опросах
- **`tracked_poll_info.json`** - Информация об отслеживаемых опросах
- **`test_poll_info.json`** - Информация о тестовых опросах

## 🗂️ Конфигурационные файлы

- **`.gitignore`** - Игнорируемые файлы Git
- **`requirements-github.txt`** - Зависимости для GitHub Actions
- **`env.example`** - Пример переменных окружения
- **`bot_session.session`** - Сессия бота

---

**Статус**: Все файлы проверены и актуальны  
**Последнее обновление**: Август 2025
