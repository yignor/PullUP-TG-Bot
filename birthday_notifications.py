#!/usr/bin/env python3
"""
Модуль для уведомлений о днях рождения
Использует Google Sheets для получения данных игроков
"""

import os
import asyncio
import datetime
from dotenv import load_dotenv
from datetime_utils import get_moscow_time, log_current_time

# Загружаем переменные окружения
load_dotenv()

def get_years_word(age: int) -> str:
    """Возвращает правильное склонение слова 'год'"""
    if age % 10 == 1 and age % 100 != 11:
        return "год"
    elif age % 10 in [2, 3, 4] and age % 100 not in [12, 13, 14]:
        return "года"
    else:
        return "лет"

def should_check_birthdays() -> bool:
    """Проверяет, нужно ли проверять дни рождения (в 09:00-09:59 по Москве)"""
    # Получаем московское время
    now = get_moscow_time()
    return now.hour == 9  # Проверяем весь час с 09:00 до 09:59 по Москве

async def check_birthdays():
    """Проверяет дни рождения и отправляет уведомления"""
    try:
        # Используем централизованное логирование времени
        time_info = log_current_time()
        
        if not should_check_birthdays():
            print("📅 Не время для проверки дней рождения (только в 09:00-09:59)")
            return
        
        print("🎂 Проверяем дни рождения...")
        
        # Импортируем менеджер игроков
        from players_manager import PlayersManager
        
        # Создаем менеджер
        manager = PlayersManager()
        
        # Получаем игроков с днями рождения сегодня
        birthday_players = manager.get_players_with_birthdays_today()
        
        if not birthday_players:
            print("📅 Сегодня нет дней рождения.")
            return
        
        print(f"🎉 Найдено {len(birthday_players)} именинников!")
        
        # Формируем сообщения для каждого именинника
        birthday_messages = []
        
        for player in birthday_players:
            # Получаем данные игрока
            surname = player.get('surname', '')  # Фамилия из столбца "Фамилия"
            nickname = player.get('nickname', '')  # Ник из столбца "Ник"
            telegram_id = player.get('telegram_id', '')  # Telegram ID
            first_name = player.get('name', '')  # Имя из столбца "Имя"
            age = player.get('age', 0)  # Возраст (уже вычислен)
            
            # Формируем сообщение
            if nickname and telegram_id:
                # Если есть ник и Telegram ID
                message = f"🎉 Сегодня день рождения у {surname} \"{nickname}\" ({telegram_id}) {first_name} ({age} {get_years_word(age)})!"
            elif nickname:
                # Если есть только ник
                message = f"🎉 Сегодня день рождения у {surname} \"{nickname}\" {first_name} ({age} {get_years_word(age)})!"
            elif telegram_id:
                # Если есть только Telegram ID
                message = f"🎉 Сегодня день рождения у {surname} ({telegram_id}) {first_name} ({age} {get_years_word(age)})!"
            else:
                # Если нет ни ника, ни Telegram ID
                message = f"🎉 Сегодня день рождения у {surname} {first_name} ({age} {get_years_word(age)})!"
            
            message += "\n Поздравляем! 🎂"
            birthday_messages.append(message)
        
        # Отправляем уведомления
        if birthday_messages:
            # Импортируем бота
            from bot_wrapper import get_bot
            
            current_bot = get_bot()
            if not current_bot:
                print("❌ Не удалось отправить уведомление - бот не инициализирован")
                return
            
            chat_id = os.getenv("CHAT_ID")
            if not chat_id:
                print("❌ CHAT_ID не настроен")
                return
            
            # Отправляем каждое сообщение
            for i, message in enumerate(birthday_messages, 1):
                try:
                    await current_bot.send_message(chat_id=chat_id, text=message)
                    print(f"✅ Отправлено уведомление {i}: {message[:50]}...")
                except Exception as e:
                    print(f"❌ Ошибка отправки уведомления {i}: {e}")
        
    except Exception as e:
        print(f"❌ Ошибка проверки дней рождения: {e}")

async def test_birthday_notifications():
    """Тестирует систему уведомлений о днях рождения"""
    print("🧪 ТЕСТ СИСТЕМЫ УВЕДОМЛЕНИЙ О ДНЯХ РОЖДЕНИЯ")
    print("=" * 60)
    
    try:
        from players_manager import PlayersManager
        
        # Создаем менеджер
        manager = PlayersManager()
        print("✅ PlayersManager инициализирован")
        
        # Получаем всех игроков
        all_players = manager.get_all_players()
        print(f"📊 Всего игроков: {len(all_players)}")
        
        # Получаем игроков с днями рождения сегодня
        birthday_players = manager.get_players_with_birthdays_today()
        print(f"🎂 Дней рождения сегодня: {len(birthday_players)}")
        
        if birthday_players:
            print("\n🎉 Именинники сегодня:")
            for i, player in enumerate(birthday_players, 1):
                surname = player.get('surname', '')
                nickname = player.get('nickname', '')
                telegram_id = player.get('telegram_id', '')
                first_name = player.get('name', '')
                age = player.get('age', 0)
                
                print(f"   {i}. {surname} {first_name} ({age} лет)")
                print(f"      Ник: {nickname or 'Не указан'}")
                print(f"      Telegram ID: {telegram_id or 'Не указан'}")
                
                # Показываем пример сообщения
                if nickname and telegram_id:
                    message = f"🎉 Сегодня день рождения у {surname} \"{nickname}\" ({telegram_id}) {first_name} ({age} {get_years_word(age)})!"
                elif nickname:
                    message = f"🎉 Сегодня день рождения у {surname} \"{nickname}\" {first_name} ({age} {get_years_word(age)})!"
                elif telegram_id:
                    message = f"🎉 Сегодня день рождения у {surname} ({telegram_id}) {first_name} ({age} {get_years_word(age)})!"
                else:
                    message = f"🎉 Сегодня день рождения у {surname} {first_name} ({age} {get_years_word(age)})!"
                
                message += "\n Поздравляем! 🎂"
                print(f"      Пример сообщения: {message}")
                print()
        else:
            print("📅 Сегодня нет дней рождения")
        
        # Показываем примеры для разных случаев
        print("📝 ПРИМЕРЫ СООБЩЕНИЙ:")
        print("-" * 40)
        
        # Пример 1: Полные данные
        print("1. С никнеймом и Telegram ID:")
        print("🎉 Сегодня день рождения у Шахманов \"Каша\" (@kkkkkkkkasha) Максим (19 лет)!")
        print(" Поздравляем! 🎂")
        print()
        
        # Пример 2: Только никнейм
        print("2. Только с никнеймом:")
        print("🎉 Сегодня день рождения у Шахманов \"Каша\" Максим (19 лет)!")
        print(" Поздравляем! 🎂")
        print()
        
        # Пример 3: Только Telegram ID
        print("3. Только с Telegram ID:")
        print("🎉 Сегодня день рождения у Шахманов (@kkkkkkkkasha) Максим (19 лет)!")
        print(" Поздравляем! 🎂")
        print()
        
        # Пример 4: Без дополнительных данных
        print("4. Без никнейма и Telegram ID:")
        print("🎉 Сегодня день рождения у Шахманов Максим (19 лет)!")
        print(" Поздравляем! 🎂")
        
        print("\n✅ Тестирование завершено")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

async def main():
    """Основная функция"""
    print("🎂 СИСТЕМА УВЕДОМЛЕНИЙ О ДНЯХ РОЖДЕНИЯ")
    print("=" * 60)
    
    # Тестируем систему
    await test_birthday_notifications()
    
    # Проверяем дни рождения (если время подходящее)
    await check_birthdays()

if __name__ == "__main__":
    asyncio.run(main())
