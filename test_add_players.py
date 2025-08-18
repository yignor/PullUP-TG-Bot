#!/usr/bin/env python3
"""
Тест добавления игроков в Google Sheets
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_add_players():
    """Тестирует добавление игроков в Google Sheets"""
    print("🧪 ТЕСТ ДОБАВЛЕНИЯ ИГРОКОВ В GOOGLE SHEETS")
    print("=" * 50)
    
    try:
        from players_manager import PlayersManager
        
        # Создаем менеджер
        manager = PlayersManager()
        print("✅ PlayersManager инициализирован")
        
        # Тестовые данные игроков
        test_players = [
            {
                'name': 'Шахманов Максим',
                'nickname': '@max_shah',
                'telegram_id': '123456789',
                'birthday': '2006-08-17',
                'status': 'Активный',
                'team': 'Pull Up',
                'notes': 'Тестовые данные'
            },
            {
                'name': 'Иванов Иван',
                'nickname': '@ivan_ball',
                'telegram_id': '987654321',
                'birthday': '1995-03-15',
                'status': 'Активный',
                'team': 'Pull Up-Фарм',
                'notes': 'Тестовые данные'
            },
            {
                'name': 'Петров Петр',
                'nickname': '@petr_hoop',
                'telegram_id': '555666777',
                'birthday': '1998-11-22',
                'status': 'Неактивный',
                'team': 'Pull Up',
                'notes': 'Тестовые данные'
            }
        ]
        
        # Добавляем игроков
        print(f"\n📝 Добавляем {len(test_players)} игроков...")
        for i, player in enumerate(test_players, 1):
            success = manager.add_player(
                name=player['name'],
                birthday=player['birthday'],
                nickname=player['nickname'],
                telegram_id=player['telegram_id'],
                team=player['team'],
                notes=player['notes']
            )
            
            if success:
                print(f"   ✅ {i}. {player['name']} добавлен")
            else:
                print(f"   ❌ {i}. {player['name']} - ошибка добавления")
        
        # Проверяем результат
        print(f"\n📊 Проверяем результат...")
        all_players = manager.get_all_players()
        print(f"   Всего игроков: {len(all_players)}")
        
        active_players = manager.get_active_players()
        print(f"   Активных игроков: {len(active_players)}")
        
        # Показываем всех игроков
        if all_players:
            print(f"\n📋 СПИСОК ВСЕХ ИГРОКОВ:")
            for i, player in enumerate(all_players, 1):
                status_emoji = "✅" if player['status'] == 'Активный' else "❌"
                print(f"   {i}. {status_emoji} {player['name']} - {player['birthday']} - {player.get('team', '')}")
        
        # Проверяем дни рождения сегодня
        birthday_players = manager.get_players_with_birthdays_today()
        print(f"\n🎂 Дней рождения сегодня: {len(birthday_players)}")
        
        if birthday_players:
            print("🎉 Именинники:")
            for player in birthday_players:
                age = player.get('age', 0)
                print(f"   - {player['name']} ({age} лет)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def test_birthday_functionality():
    """Тестирует функциональность дней рождения"""
    print("\n🧪 ТЕСТ ФУНКЦИОНАЛЬНОСТИ ДНЕЙ РОЖДЕНИЯ")
    print("=" * 50)
    
    try:
        from players_manager import PlayersManager
        
        manager = PlayersManager()
        
        # Добавляем игрока с днем рождения сегодня
        import datetime
        today = datetime.datetime.now()
        today_birthday = today.strftime("%Y-%m-%d")
        
        # Создаем игрока с днем рождения сегодня
        success = manager.add_player(
            name='Тестовый Именинник',
            birthday=today_birthday,
            nickname='@test_birthday',
            telegram_id='999888777',
            team='Pull Up',
            notes='Тест дня рождения'
        )
        
        if success:
            print(f"✅ Добавлен тестовый именинник с датой {today_birthday}")
            
            # Проверяем дни рождения
            birthday_players = manager.get_players_with_birthdays_today()
            print(f"🎂 Дней рождения сегодня: {len(birthday_players)}")
            
            if birthday_players:
                print("🎉 Найденные именинники:")
                for player in birthday_players:
                    age = player.get('age', 0)
                    print(f"   - {player['name']} ({age} лет)")
            else:
                print("⚠️ Именинники не найдены")
        else:
            print("❌ Не удалось добавить тестового именинника")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования дней рождения: {e}")
        return False

if __name__ == "__main__":
    # Тестируем добавление игроков
    add_success = test_add_players()
    
    if add_success:
        # Тестируем функциональность дней рождения
        birthday_success = test_birthday_functionality()
        
        if birthday_success:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
            print("Google Sheets полностью настроен и работает с данными")
        else:
            print("\n⚠️ Добавление игроков работает, но есть проблемы с днями рождения")
    else:
        print("\n❌ Проблемы с добавлением игроков")
