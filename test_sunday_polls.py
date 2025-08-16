#!/usr/bin/env python3
"""
Скрипт для тестирования функционала опросов по воскресеньям
"""

import asyncio
import datetime
import os
from dotenv import load_dotenv
from training_polls import should_create_weekly_poll, should_collect_attendance, get_target_training_day

def load_env_variables():
    """Загружает переменные из .env файла"""
    try:
        load_dotenv()
        print("✅ Переменные загружены через python-dotenv")
    except ImportError:
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            print("✅ Переменные загружены из .env файла")
        except FileNotFoundError:
            print("❌ Файл .env не найден")
            return False
    
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ BOT_TOKEN или CHAT_ID не найдены")
        return False
    
    print(f"✅ BOT_TOKEN: {bot_token[:10]}...")
    print(f"✅ CHAT_ID: {chat_id}")
    return True

async def test_sunday_polls():
    """Тестирует функционал опросов по воскресеньям"""
    print("\n=== ТЕСТИРОВАНИЕ ОПРОСОВ ПО ВОСКРЕСЕНЬЯМ ===\n")
    
    if not load_env_variables():
        return
    
    # Проверяем текущее время
    now = datetime.datetime.now()
    print(f"1. Текущее время: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   День недели: {now.strftime('%A')} ({now.weekday()})")
    
    # Проверяем, нужно ли создать опрос на неделю
    should_create = await should_create_weekly_poll()
    print(f"\n2. Нужно ли создать опрос на неделю: {'✅ Да' if should_create else '❌ Нет'}")
    
    # Проверяем, нужно ли собрать данные о посещаемости
    should_collect = await should_collect_attendance()
    print(f"3. Нужно ли собрать данные о посещаемости: {'✅ Да' if should_collect else '❌ Нет'}")
    
    # Определяем целевую тренировку
    target_day = get_target_training_day()
    print(f"4. Целевая тренировка для сбора данных: {target_day if target_day else 'Нет'}")
    
    # Проверяем файлы
    print(f"\n5. Проверка файлов:")
    import os
    
    poll_files = [
        'training_polls.py',
        'enhanced_training_polls.py',
        'poll_results_handler.py'
    ]
    
    for poll_file in poll_files:
        if os.path.exists(poll_file):
            print(f"   ✅ {poll_file} - существует")
        else:
            print(f"   ❌ {poll_file} - не найден")
    
    # Тестируем создание опроса (если время подходящее)
    if should_create:
        print(f"\n6. Тестирование создания опроса на неделю...")
        try:
            from training_polls import training_manager
            poll = await training_manager.create_weekly_training_poll()
            if poll:
                print("✅ Опрос тренировок создан успешно!")
                print(f"   Вопрос: {poll.poll.question}")
                print(f"   Варианты: {poll.poll.options}")
            else:
                print("❌ Ошибка создания опроса")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    # Показываем расписание
    print(f"\n7. Расписание опросов:")
    print(f"   📅 Воскресенье 9:00 - Создание опроса на неделю")
    print(f"   📅 Среда 9:00 - Сбор данных за Вторник")
    print(f"   📅 Суббота 9:00 - Сбор данных за Пятницу")
    print(f"   📅 Последний день месяца 9:00 - Месячный отчет")
    
    # Показываем варианты ответов
    print(f"\n8. Варианты ответов в опросе:")
    options = [
        "🏀 Вторник 19:00",
        "🏀 Пятница 20:30", 
        "👨‍🏫 Тренер",
        "❌ Нет"
    ]
    for i, option in enumerate(options, 1):
        print(f"   {i}. {option}")
    
    print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")

if __name__ == "__main__":
    asyncio.run(test_sunday_polls())
