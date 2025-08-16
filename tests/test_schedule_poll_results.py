#!/usr/bin/env python3
"""
Тестовый скрипт для проверки сбора результатов голосований по расписанию
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Добавляем корневую папку в путь для импорта
sys.path.append('..')

# Загружаем переменные окружения
load_dotenv()

async def test_schedule_poll_results():
    """Тестирует сбор результатов голосований по расписанию"""
    print("🧪 ТЕСТ СБОРА РЕЗУЛЬТАТОВ ГОЛОСОВАНИЙ ПО РАСПИСАНИЮ")
    print("=" * 60)
    
    try:
        # Импортируем обработчик результатов
        from schedule_poll_results import schedule_poll_handler
        
        print("✅ Модуль schedule_poll_results импортирован")
        
        # Проверяем настройки
        telegram_api_id = os.getenv('TELEGRAM_API_ID')
        telegram_api_hash = os.getenv('TELEGRAM_API_HASH')
        telegram_phone = os.getenv('TELEGRAM_PHONE')
        
        print(f"✅ TELEGRAM_API_ID: {'*' * 10}{telegram_api_id[-4:] if telegram_api_id else 'Не настроен'}")
        print(f"✅ TELEGRAM_API_HASH: {'*' * 10}{telegram_api_hash[-4:] if telegram_api_hash else 'Не настроен'}")
        print(f"✅ TELEGRAM_PHONE: {telegram_phone if telegram_phone else 'Не настроен'}")
        print()
        
        if not all([telegram_api_id, telegram_api_hash, telegram_phone]):
            print("❌ Переменные для Telegram Client API не настроены")
            print("📝 Для сбора результатов голосований нужно настроить:")
            print("   - TELEGRAM_API_ID")
            print("   - TELEGRAM_API_HASH") 
            print("   - TELEGRAM_PHONE")
            return False
        
        # Запускаем клиент
        print("🔌 Подключение к Telegram Client API...")
        if not await schedule_poll_handler.start_client():
            print("❌ Не удалось подключиться к Telegram Client API")
            return False
        
        # Получаем голосования по расписанию
        print("\n📊 Поиск голосований по расписанию...")
        schedule_polls = await schedule_poll_handler.get_schedule_polls(days_back=7)
        
        if schedule_polls:
            print(f"\n✅ Найдено {len(schedule_polls)} голосований по расписанию:")
            
            for i, poll in enumerate(schedule_polls, 1):
                print(f"\n🏀 Голосование {i}:")
                print(f"   Вопрос: {poll['question']}")
                print(f"   Всего голосов: {poll['total_voters']}")
                print(f"   Дата создания: {poll['date']}")
                
                # Показываем варианты ответов
                print(f"   Варианты ответов:")
                for option in poll['options']:
                    print(f"     - {option['text']}: {option['voters']} голосов")
                
                # Парсим результаты
                parsed_data = schedule_poll_handler.parse_schedule_votes(poll)
                if parsed_data:
                    game_info = parsed_data.get('game_info', {})
                    votes = parsed_data.get('votes', {})
                    
                    print(f"   📅 Информация об игре:")
                    print(f"     Соперник: {game_info.get('opponent', 'Неизвестно')}")
                    print(f"     Дата: {game_info.get('date', 'Неизвестно')}")
                    print(f"     Время: {game_info.get('time', 'Неизвестно')}")
                    print(f"     Зал: {game_info.get('venue', 'Неизвестно')}")
                    print(f"     Тип команды: {game_info.get('team_type', 'Неизвестно')}")
                    
                    print(f"   📊 Результаты голосования:")
                    print(f"     ✅ Готовы: {votes.get('ready', 0)}")
                    print(f"     ❌ Не готовы: {votes.get('not_ready', 0)}")
                    print(f"     👨‍🏫 Тренер: {votes.get('coach', 0)}")
                    print(f"     📈 Всего: {votes.get('total', 0)}")
        else:
            print("📊 Голосования по расписанию не найдены")
            print("💡 Убедитесь, что:")
            print("   - Голосования были созданы в топике 1282")
            print("   - Голосования содержат 'Летняя лига' в названии")
            print("   - Голосования созданы за последние 7 дней")
        
        # Получаем сводку посещаемости
        print(f"\n📈 Получение сводки посещаемости...")
        summary = await schedule_poll_handler.get_game_attendance_summary(days_back=7)
        
        if summary:
            print(f"\n📊 СВОДКА ПОСЕЩАЕМОСТИ:")
            print(f"   Всего игр: {summary['total_games']}")
            print(f"   Всего готовы: {summary['total_ready']}")
            print(f"   Всего не готовы: {summary['total_not_ready']}")
            print(f"   Всего тренер: {summary['total_coach']}")
            
            if summary['games']:
                print(f"\n🏀 ДЕТАЛИ ПО ИГРАМ:")
                for game in summary['games']:
                    print(f"   {game['opponent']} ({game['date']} {game['time']})")
                    print(f"     Тип: {game['team_type']}")
                    print(f"     Зал: {game['venue']}")
                    print(f"     Готовы: {game['ready']}, Не готовы: {game['not_ready']}, Тренер: {game['coach']}")
                    print(f"     Всего: {game['total']}")
                    print()
        else:
            print("📊 Сводка посещаемости не получена")
        
        # Закрываем клиент
        await schedule_poll_handler.close_client()
        
        print("\n✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_schedule_poll_results())
